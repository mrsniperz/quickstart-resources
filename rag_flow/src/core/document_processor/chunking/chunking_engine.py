"""
模块名称: chunking_engine
功能描述: 智能分块引擎，提供文档内容的智能分块处理和策略管理
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from ..config.config_manager import get_config_manager


class ChunkType(Enum):
    """分块类型枚举"""
    PARAGRAPH = "paragraph"
    SECTION = "section"
    CHAPTER = "chapter"
    TABLE = "table"
    IMAGE = "image"
    HEADER = "header"
    FOOTER = "footer"
    CUSTOM = "custom"


@dataclass
class ChunkMetadata:
    """分块元数据"""
    chunk_id: str
    chunk_type: ChunkType
    source_document: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = None
    confidence_score: float = 1.0
    processing_timestamp: Optional[str] = None


@dataclass
class TextChunk:
    """文本分块数据类"""
    content: str
    metadata: ChunkMetadata
    word_count: int = 0
    character_count: int = 0
    overlap_content: Optional[str] = None
    quality_score: float = 0.0


class ChunkingStrategy(ABC):
    """分块策略抽象基类"""
    
    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        分块文本内容
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
            
        Returns:
            list: 分块结果列表
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        pass


class ChunkingEngine:
    """
    智能分块引擎
    
    提供文档内容的智能分块处理，包括：
    - 多种分块策略管理
    - 自适应分块参数调整
    - 分块质量控制
    - 重叠策略处理
    - 上下文保持机制
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化分块引擎

        Args:
            config (dict, optional): 配置参数
                - default_strategy (str): 默认分块策略，默认从配置文件读取
                - chunk_size (int): 默认分块大小，默认从配置文件读取
                - chunk_overlap (int): 分块重叠大小，默认从配置文件读取
                - min_chunk_size (int): 最小分块大小，默认从配置文件读取
                - max_chunk_size (int): 最大分块大小，默认从配置文件读取
                - preserve_context (bool): 是否保持上下文，默认从配置文件读取
        """
        # 导入统一日志管理器
        try:
            from src.utils.logger import SZ_LoggerManager
            self.logger = SZ_LoggerManager.setup_logger(__name__)
        except ImportError:
            # 回退到标准logging
            import logging
            self.logger = logging.getLogger(__name__)

        # 获取配置管理器和默认配置
        try:
            config_manager = get_config_manager()
            default_config = config_manager.get_chunking_config('global')
        except Exception as e:
            self.logger.warning(f"无法加载配置文件，使用硬编码默认配置: {e}")
            default_config = self._get_fallback_config()

        # 合并用户配置和默认配置
        self.config = default_config.copy()
        if config:
            self.config.update(config)

        # 配置参数
        self.default_strategy = self.config.get('default_strategy', 'recursive')
        self.chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)
        self.min_chunk_size = self.config.get('min_chunk_size', 100)
        self.max_chunk_size = self.config.get('max_chunk_size', 2000)
        self.preserve_context = self.config.get('preserve_context', True)

        # 质量评估配置
        self.enable_quality_assessment = self.config.get('enable_quality_assessment', True)
        self.quality_strategy = self.config.get('quality_strategy', 'aviation')

        # 策略注册表
        self.strategies: Dict[str, ChunkingStrategy] = {}

        # 初始化质量评估管理器
        self._init_quality_assessment_manager()

        # 注册内置策略
        self._register_builtin_strategies()

    def _get_fallback_config(self) -> Dict[str, Any]:
        """
        获取回退配置（当配置文件不可用时使用）

        Returns:
            dict: 回退配置
        """
        return {
            'default_strategy': 'recursive',
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'min_chunk_size': 100,
            'max_chunk_size': 2000,
            'preserve_context': True,
            'enable_quality_assessment': True,
            'quality_strategy': 'aviation'
        }

    def _init_quality_assessment_manager(self) -> None:
        """
        初始化质量评估管理器（简化版）
        """
        try:
            # 尝试导入简化的质量评估管理器
            try:
                from .quality.manager import QualityAssessmentManager
            except ImportError as e:
                self.logger.warning(f"质量评估管理器导入失败，将使用基础评估: {e}")
                self.quality_manager = None
                return
            except Exception as e:
                self.logger.warning(f"质量评估管理器导入异常，将使用基础评估: {e}")
                self.quality_manager = None
                return

            # 简化的质量评估配置
            quality_config = self.config.get('quality_assessment', {})

            # 映射旧版配置到新版配置
            simplified_config = {
                'min_length': quality_config.get('min_chunk_size', self.min_chunk_size),
                'max_length': quality_config.get('max_chunk_size', self.max_chunk_size),
                'optimal_length': quality_config.get('chunk_size', self.chunk_size),
                'enable_quality_check': quality_config.get('enable_assessment', True)
            }

            try:
                # 根据质量策略选择预设配置
                strategy = self.quality_strategy.lower()
                if strategy in ['disabled', 'none']:
                    preset = 'disabled'
                elif strategy in ['strict', 'high']:
                    preset = 'strict'
                else:
                    preset = 'basic'

                self.quality_manager = QualityAssessmentManager(preset)
                # 应用自定义配置覆盖
                if simplified_config:
                    self.quality_manager.config.update_config(**simplified_config)

                self.logger.info(f"简化质量评估管理器初始化完成，使用预设: {preset}")
            except Exception as e:
                self.logger.warning(f"质量评估管理器创建失败，将使用基础评估: {e}")
                self.quality_manager = None

        except Exception as e:
            self.logger.warning(f"质量评估管理器初始化异常，将使用基础评估: {e}")
            self.quality_manager = None

    def register_strategy(self, name: str, strategy: ChunkingStrategy) -> None:
        """
        注册分块策略
        
        Args:
            name: 策略名称
            strategy: 策略实例
        """
        self.strategies[name] = strategy
        self.logger.info(f"注册分块策略: {name}")
    
    def chunk_document(self, text_content: str,
                      document_metadata: Dict[str, Any],
                      preset_name: Optional[str] = None) -> List[TextChunk]:
        """
        对文档进行分块处理（简化版：基于配置预设）

        Args:
            text_content: 文档文本内容
            document_metadata: 文档元数据
            preset_name: 指定的配置预设名称

        Returns:
            list: 分块结果列表

        Raises:
            ValueError: 预设不存在或文本为空
        """
        try:
            if not text_content or not text_content.strip():
                raise ValueError("文本内容为空")

            # 选择配置预设
            preset_name = preset_name or self._select_strategy(document_metadata)

            # 获取预设配置
            preset_config = self._load_preset_config(preset_name)

            # 使用唯一的recursive策略，但应用预设配置
            if 'recursive' not in self.strategies:
                raise ValueError("核心分块策略未初始化")

            strategy = self.strategies['recursive']

            self.logger.info(f"使用配置预设: {preset_name}")

            # 临时更新策略配置
            original_config = strategy.config.copy()
            strategy.config.update(preset_config)

            try:
                # 执行分块
                chunks = strategy.chunk_text(text_content, document_metadata)

                # 后处理分块结果
                processed_chunks = self._post_process_chunks(chunks, document_metadata)

                self.logger.info(f"分块完成: {len(processed_chunks)}个分块，使用预设: {preset_name}")

                return processed_chunks

            finally:
                # 恢复原始配置
                strategy.config = original_config

        except Exception as e:
            self.logger.error(f"文档分块失败: {e}")
            raise
    
    def _select_strategy(self, document_metadata: Dict[str, Any]) -> str:
        """
        根据文档元数据选择合适的配置预设

        Args:
            document_metadata: 文档元数据

        Returns:
            str: 选择的预设名称
        """
        try:
            # 根据文档类型选择预设
            doc_type = document_metadata.get('document_type', '').lower()
            file_extension = document_metadata.get('file_extension', '').lower()

            # 航空文档特殊处理
            title = document_metadata.get('title', '').lower()
            subject = document_metadata.get('subject', '').lower()

            # 维修手册
            if any(keyword in title or keyword in subject
                   for keyword in ['维修', '手册', 'maintenance', 'manual']):
                return 'aviation_maintenance'

            # 规章制度
            elif any(keyword in title or keyword in subject
                     for keyword in ['规章', '制度', 'regulation', 'policy']):
                return 'aviation_regulation'

            # 技术标准
            elif any(keyword in title or keyword in subject
                     for keyword in ['标准', '规范', 'standard', 'specification']):
                return 'aviation_standard'

            # 培训资料
            elif any(keyword in title or keyword in subject
                     for keyword in ['培训', '教学', 'training', 'education']):
                return 'aviation_training'

            # 根据文档格式选择预设
            elif doc_type == 'pdf' or file_extension == '.pdf':
                return 'structure'  # 使用结构化预设
            elif doc_type in ['word', 'docx'] or file_extension in ['.docx', '.doc']:
                return 'standard'   # Word文档使用标准预设
            elif doc_type in ['text', 'txt'] or file_extension in ['.txt', '.md']:
                return 'semantic'   # 纯文本使用语义预设

            # 默认预设
            return 'standard'

        except Exception as e:
            self.logger.warning(f"预设选择失败，使用标准预设: {e}")
            return 'standard'

    def _load_preset_config(self, preset_name: str) -> Dict[str, Any]:
        """
        加载预设配置

        Args:
            preset_name: 预设名称

        Returns:
            dict: 预设配置
        """
        try:
            config_manager = get_config_manager()
            presets = config_manager.get_chunking_config('presets')

            if not presets or preset_name not in presets:
                self.logger.warning(f"预设 {preset_name} 不存在，使用标准预设")
                preset_name = 'standard'

            if preset_name not in presets:
                # 如果连标准预设都不存在，返回默认配置
                self.logger.warning("标准预设不存在，使用默认配置")
                return self._get_fallback_config()

            preset_config = presets[preset_name].copy()

            # 移除非分块器配置项
            preset_config.pop('strategy', None)
            preset_config.pop('description', None)

            self.logger.debug(f"加载预设配置: {preset_name}")
            return preset_config

        except Exception as e:
            self.logger.error(f"加载预设配置失败: {e}")
            return self._get_fallback_config()

    def get_available_presets(self) -> List[str]:
        """
        获取可用的配置预设列表

        Returns:
            list: 预设名称列表
        """
        try:
            config_manager = get_config_manager()
            presets = config_manager.get_chunking_config('presets')
            return list(presets.keys()) if presets else ['standard']
        except Exception as e:
            self.logger.error(f"获取预设列表失败: {e}")
            return ['standard']

    def get_preset_info(self, preset_name: str) -> Dict[str, Any]:
        """
        获取预设配置信息

        Args:
            preset_name: 预设名称

        Returns:
            dict: 预设信息
        """
        try:
            config_manager = get_config_manager()
            presets = config_manager.get_chunking_config('presets')

            if not presets or preset_name not in presets:
                return {'error': f'预设不存在: {preset_name}'}

            preset_config = presets[preset_name]

            return {
                'name': preset_name,
                'description': preset_config.get('description', '无描述'),
                'chunk_size': preset_config.get('chunk_size', 1000),
                'chunk_overlap': preset_config.get('chunk_overlap', 200),
                'separators_count': len(preset_config.get('separators', [])),
                'config': preset_config
            }

        except Exception as e:
            self.logger.error(f"获取预设信息失败: {e}")
            return {'error': str(e)}
    
    def _post_process_chunks(self, chunks: List[TextChunk], 
                           document_metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        后处理分块结果
        
        Args:
            chunks: 原始分块列表
            document_metadata: 文档元数据
            
        Returns:
            list: 处理后的分块列表
        """
        try:
            processed_chunks = []
            
            for i, chunk in enumerate(chunks):
                # 更新分块ID
                chunk.metadata.chunk_id = f"{document_metadata.get('file_name', 'doc')}_{i:04d}"
                
                # 计算统计信息
                chunk.word_count = len(chunk.content.split())
                chunk.character_count = len(chunk.content)
                
                # 添加重叠内容
                if self.preserve_context and i > 0:
                    chunk.overlap_content = self._generate_overlap_content(chunks, i)
                
                # 计算质量评分（可选）
                if self.enable_quality_assessment:
                    chunk.quality_score = self._calculate_chunk_quality(chunk)
                else:
                    chunk.quality_score = 1.0  # 默认满分，不进行质量评估
                
                # 过滤过小的分块
                if chunk.character_count >= self.min_chunk_size:
                    processed_chunks.append(chunk)
                else:
                    self.logger.debug(f"过滤过小分块: {chunk.character_count}字符")
            
            return processed_chunks
            
        except Exception as e:
            self.logger.error(f"分块后处理失败: {e}")
            return chunks
    
    def _generate_overlap_content(self, chunks: List[TextChunk], current_index: int) -> str:
        """
        生成重叠内容
        
        Args:
            chunks: 分块列表
            current_index: 当前分块索引
            
        Returns:
            str: 重叠内容
        """
        try:
            if current_index <= 0:
                return ""
            
            prev_chunk = chunks[current_index - 1]
            prev_content = prev_chunk.content
            
            # 取前一个分块的后部分作为重叠
            words = prev_content.split()
            overlap_words = words[-self.chunk_overlap//10:] if len(words) > self.chunk_overlap//10 else words
            
            return " ".join(overlap_words)
            
        except Exception as e:
            self.logger.warning(f"重叠内容生成失败: {e}")
            return ""
    
    def _calculate_chunk_quality(self, chunk: TextChunk) -> float:
        """
        计算分块质量评分（使用新的质量评估管理器）

        Args:
            chunk: 文本分块

        Returns:
            float: 质量评分（0-1）
        """
        try:
            # 如果质量评估管理器可用，使用简化的评估系统
            if hasattr(self, 'quality_manager') and self.quality_manager:
                # 构建评估上下文（简化版本中基本不使用）
                context = {
                    'document_metadata': getattr(chunk.metadata, '__dict__', {}),
                    'chunk_size_config': {
                        'min_size': self.min_chunk_size,
                        'max_size': self.max_chunk_size,
                        'target_size': self.chunk_size
                    }
                }

                # 执行简化的质量评估（不需要strategy_name参数）
                quality_metrics = self.quality_manager.assess_chunk_quality(chunk, context)

                return quality_metrics.overall_score

            # 如果质量评估管理器不可用，返回基础评分
            return self._get_basic_quality_score(chunk)

        except Exception as e:
            self.logger.warning(f"分块质量评分计算失败: {e}")
            return self._get_basic_quality_score(chunk)

    def _get_basic_quality_score(self, chunk: TextChunk) -> float:
        """
        获取基础质量评分（当质量评估管理器不可用时使用）

        Args:
            chunk: 文本分块

        Returns:
            float: 基础质量评分（0-1）
        """
        try:
            # 特殊情况处理
            if not chunk.content.strip():
                return 0.0

            if chunk.character_count < 10:
                return 0.1

            # 基于长度的简单评分
            char_count = chunk.character_count

            # 定义最优大小区间
            optimal_min = self.chunk_size * 0.8
            optimal_max = self.chunk_size * 1.2

            if optimal_min <= char_count <= optimal_max:
                base_score = 0.8  # 长度合适
            elif self.min_chunk_size <= char_count <= self.max_chunk_size:
                # 在可接受范围内，根据偏离程度评分
                if char_count < optimal_min:
                    ratio = char_count / optimal_min
                    base_score = 0.5 + ratio * 0.3
                else:
                    ratio = optimal_max / char_count
                    base_score = 0.5 + ratio * 0.3
            else:
                # 超出可接受范围
                if char_count < self.min_chunk_size:
                    base_score = 0.2
                else:
                    base_score = 0.3

            # 基于内容密度的调整
            non_space_ratio = len(chunk.content.replace(' ', '').replace('\n', '').replace('\t', '')) / len(chunk.content)
            if non_space_ratio < 0.3:
                base_score *= 0.5  # 内容密度过低
            elif non_space_ratio > 0.8:
                base_score *= 1.1  # 内容密度高

            return round(min(1.0, max(0.1, base_score)), 3)

        except Exception as e:
            self.logger.warning(f"基础质量评分计算失败: {e}")
            return 0.5

    # 质量评估相关方法已移至独立的quality模块
    # 以下方法保留用于向后兼容，但建议使用新的质量评估系统

    # 以下方法已废弃，请使用新的质量评估系统
    # 保留这些方法仅为向后兼容，不建议直接调用

    def set_quality_assessment_enabled(self, enabled: bool = True) -> None:
        """
        启用或禁用质量评估

        Args:
            enabled: 是否启用质量评估
        """
        self.enable_quality_assessment = enabled
        self.logger.info(f"质量评估已{'启用' if enabled else '禁用'}")

    def is_quality_assessment_enabled(self) -> bool:
        """
        检查质量评估是否启用

        Returns:
            bool: 是否启用质量评估
        """
        return getattr(self, 'enable_quality_assessment', True)

    def set_quality_assessment_strategy(self, strategy_name: str) -> bool:
        """
        设置质量评估策略（简化版本中支持的策略：basic, strict, disabled）

        Args:
            strategy_name: 策略名称

        Returns:
            bool: 是否设置成功
        """
        try:
            if hasattr(self, 'quality_manager') and self.quality_manager:
                # 简化版本支持的策略
                supported_strategies = ['basic', 'strict', 'disabled']
                if strategy_name.lower() in supported_strategies:
                    self.quality_strategy = strategy_name.lower()
                    # 更新质量管理器配置
                    self.quality_manager.update_config(strategy_name.lower())
                    self.logger.info(f"质量评估策略设置为: {strategy_name}")
                    return True
                else:
                    self.logger.error(f"策略 {strategy_name} 不支持。支持的策略: {supported_strategies}")
                    return False
            else:
                self.logger.error("质量评估管理器未初始化")
                return False
        except Exception as e:
            self.logger.error(f"设置质量评估策略失败: {e}")
            return False

    def get_quality_assessment_strategy(self) -> str:
        """
        获取当前质量评估策略

        Returns:
            str: 当前策略名称
        """
        return getattr(self, 'quality_strategy', 'aviation')








    def _register_builtin_strategies(self) -> None:
        """注册内置分块策略（简化版：仅注册recursive_chunker）"""
        try:
            from .recursive_chunker import RecursiveCharacterChunker

            # 注册唯一的分块策略实现
            self.register_strategy('recursive', RecursiveCharacterChunker(self.config))

            self.logger.info("简化分块引擎初始化完成，使用统一的recursive_chunker + 配置预设系统")

        except Exception as e:
            self.logger.error(f"分块策略注册失败: {e}")
            raise RuntimeError(f"无法初始化分块引擎: {e}")
    
    def get_available_strategies(self) -> List[str]:
        """
        获取可用的分块策略列表（简化版：仅返回recursive）

        Returns:
            list: 策略名称列表
        """
        return list(self.strategies.keys())
    
    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """
        获取策略信息
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            dict: 策略信息
        """
        try:
            if strategy_name not in self.strategies:
                return {'error': f'策略不存在: {strategy_name}'}
            
            strategy = self.strategies[strategy_name]
            
            return {
                'name': strategy_name,
                'class_name': strategy.__class__.__name__,
                'strategy_name': strategy.get_strategy_name(),
                'description': strategy.__doc__ or '无描述'
            }
            
        except Exception as e:
            self.logger.error(f"获取策略信息失败: {e}")
            return {'error': str(e)}

    def get_quality_assessment_info(self) -> Dict[str, Any]:
        """
        获取质量评估系统信息（简化版）

        Returns:
            dict: 质量评估系统信息
        """
        try:
            if not hasattr(self, 'quality_manager') or not self.quality_manager:
                return {'error': '质量评估管理器未初始化'}

            # 获取简化版本的信息
            strategy_info = self.quality_manager.get_strategy_info()
            stats = self.quality_manager.get_statistics()

            return {
                'available_strategies': ['basic', 'strict', 'disabled'],
                'current_strategy': strategy_info.get('preset', 'basic'),
                'enabled': self.quality_manager.is_enabled(),
                'strategy_info': strategy_info,
                'statistics': stats
            }

        except Exception as e:
            self.logger.error(f"获取质量评估信息失败: {e}")
            return {'error': str(e)}

    def set_quality_strategy(self, strategy_name: str) -> bool:
        """
        设置默认质量评估策略（简化版）

        Args:
            strategy_name: 策略名称 ('basic', 'strict', 'disabled')

        Returns:
            bool: 是否设置成功
        """
        try:
            if not hasattr(self, 'quality_manager') or not self.quality_manager:
                self.logger.error("质量评估管理器未初始化")
                return False

            # 使用简化版本的配置更新方法
            self.quality_manager.update_config(strategy_name)
            self.quality_strategy = strategy_name
            self.logger.info(f"质量评估策略设置为: {strategy_name}")
            return True

        except Exception as e:
            self.logger.error(f"设置质量策略失败: {e}")
            return False

    def assess_chunks_quality(self, chunks: List[TextChunk], preset_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        批量评估分块质量

        Args:
            chunks: 分块列表
            preset_name: 指定的配置预设名称（暂未使用，保留用于未来扩展）

        Returns:
            list: 质量评估结果列表
        """
        try:
            if not hasattr(self, 'quality_manager') or not self.quality_manager:
                self.logger.warning("质量评估管理器未初始化，使用基础评估逻辑")
                return [{'overall_score': self._get_basic_quality_score(chunk)} for chunk in chunks]

            # 使用简化的质量管理器进行批量评估
            quality_results = self.quality_manager.assess_chunks_batch(chunks)

            # 转换为字典格式
            return [
                {
                    'overall_score': result.overall_score,
                    'dimension_scores': result.dimension_scores,
                    'confidence': result.confidence,
                    'strategy_name': result.strategy_name,
                    'processing_time': result.processing_time,
                    'details': result.details
                }
                for result in quality_results
            ]

        except Exception as e:
            self.logger.error(f"批量质量评估失败: {e}")
            return [{'overall_score': 0.5, 'error': str(e)} for _ in chunks]
    

