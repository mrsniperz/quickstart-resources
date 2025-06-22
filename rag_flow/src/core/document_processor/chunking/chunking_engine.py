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
                - default_strategy (str): 默认分块策略
                - chunk_size (int): 默认分块大小
                - chunk_overlap (int): 分块重叠大小
                - min_chunk_size (int): 最小分块大小
                - max_chunk_size (int): 最大分块大小
                - preserve_context (bool): 是否保持上下文
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

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

    def _init_quality_assessment_manager(self) -> None:
        """
        初始化质量评估管理器
        """
        try:
            # 尝试导入质量评估管理器
            try:
                from .quality.manager import QualityAssessmentManager
            except ImportError:
                # 如果相对导入失败，尝试绝对导入
                import sys
                import os
                quality_path = os.path.join(os.path.dirname(__file__), 'quality')
                if quality_path not in sys.path:
                    sys.path.insert(0, quality_path)
                from manager import QualityAssessmentManager

            # 质量评估配置
            quality_config = self.config.get('quality_assessment', {})
            quality_config.update({
                'min_chunk_size': self.min_chunk_size,
                'max_chunk_size': self.max_chunk_size,
                'chunk_size': self.chunk_size
            })

            self.quality_manager = QualityAssessmentManager(quality_config)
            self.logger.info("质量评估管理器初始化完成")

        except Exception as e:
            self.logger.error(f"质量评估管理器初始化失败: {e}")
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
                      strategy_name: Optional[str] = None) -> List[TextChunk]:
        """
        对文档进行分块处理
        
        Args:
            text_content: 文档文本内容
            document_metadata: 文档元数据
            strategy_name: 指定的分块策略名称
            
        Returns:
            list: 分块结果列表
            
        Raises:
            ValueError: 策略不存在或文本为空
        """
        try:
            if not text_content or not text_content.strip():
                raise ValueError("文本内容为空")
            
            # 选择分块策略
            strategy_name = strategy_name or self._select_strategy(document_metadata)
            
            if strategy_name not in self.strategies:
                raise ValueError(f"分块策略不存在: {strategy_name}")
            
            strategy = self.strategies[strategy_name]
            
            self.logger.info(f"使用分块策略: {strategy_name}")
            
            # 执行分块
            chunks = strategy.chunk_text(text_content, document_metadata)
            
            # 后处理分块结果
            processed_chunks = self._post_process_chunks(chunks, document_metadata)
            
            self.logger.info(f"分块完成: {len(processed_chunks)}个分块")
            
            return processed_chunks
            
        except Exception as e:
            self.logger.error(f"文档分块失败: {e}")
            raise
    
    def _select_strategy(self, document_metadata: Dict[str, Any]) -> str:
        """
        根据文档元数据选择合适的分块策略
        
        Args:
            document_metadata: 文档元数据
            
        Returns:
            str: 选择的策略名称
        """
        try:
            # 根据文档类型选择策略
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
            
            # 根据文档格式选择
            elif doc_type == 'pdf' or file_extension == '.pdf':
                return 'structure'
            elif doc_type in ['word', 'docx'] or file_extension in ['.docx', '.doc']:
                return 'recursive'  # Word文档使用递归分块器
            elif doc_type in ['text', 'txt'] or file_extension in ['.txt', '.md']:
                return 'recursive'  # 纯文本使用递归分块器
            elif doc_type in ['excel', 'xlsx'] or file_extension in ['.xlsx', '.xls']:
                return 'table'
            elif doc_type in ['powerpoint', 'pptx'] or file_extension in ['.pptx', '.ppt']:
                return 'slide'

            # 默认策略
            return self.default_strategy
            
        except Exception as e:
            self.logger.warning(f"策略选择失败，使用默认策略: {e}")
            return self.default_strategy
    
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
            # 如果质量评估管理器可用，使用新的评估系统
            if hasattr(self, 'quality_manager') and self.quality_manager:
                # 选择评估策略
                strategy_name = self.quality_strategy

                # 构建评估上下文
                context = {
                    'document_metadata': getattr(chunk.metadata, '__dict__', {}),
                    'chunk_size_config': {
                        'min_size': self.min_chunk_size,
                        'max_size': self.max_chunk_size,
                        'target_size': self.chunk_size
                    }
                }

                # 执行质量评估
                quality_metrics = self.quality_manager.assess_chunk_quality(
                    chunk, strategy_name, context
                )

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
        设置质量评估策略

        Args:
            strategy_name: 策略名称

        Returns:
            bool: 是否设置成功
        """
        try:
            if hasattr(self, 'quality_manager') and self.quality_manager:
                available_strategies = self.quality_manager.get_available_strategies()
                if strategy_name in available_strategies:
                    self.quality_strategy = strategy_name
                    self.logger.info(f"质量评估策略设置为: {strategy_name}")
                    return True
                else:
                    self.logger.error(f"策略 {strategy_name} 不存在。可用策略: {available_strategies}")
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
        """注册内置分块策略"""
        try:
            from .semantic_chunker import SemanticChunker
            from .structure_chunker import StructureChunker
            from .recursive_chunker import RecursiveCharacterChunker
            from .aviation_strategy import (
                AviationMaintenanceStrategy,
                AviationRegulationStrategy,
                AviationStandardStrategy,
                AviationTrainingStrategy
            )

            # 注册基础策略
            self.register_strategy('semantic', SemanticChunker(self.config))
            self.register_strategy('structure', StructureChunker(self.config))
            self.register_strategy('recursive', RecursiveCharacterChunker(self.config))

            # 注册航空专用策略
            self.register_strategy('aviation_maintenance', AviationMaintenanceStrategy(self.config))
            self.register_strategy('aviation_regulation', AviationRegulationStrategy(self.config))
            self.register_strategy('aviation_standard', AviationStandardStrategy(self.config))
            self.register_strategy('aviation_training', AviationTrainingStrategy(self.config))

        except Exception as e:
            self.logger.error(f"内置策略注册失败: {e}")
    
    def get_available_strategies(self) -> List[str]:
        """
        获取可用的分块策略列表
        
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
        获取质量评估系统信息

        Returns:
            dict: 质量评估系统信息
        """
        try:
            if not hasattr(self, 'quality_manager') or not self.quality_manager:
                return {'error': '质量评估管理器未初始化'}

            return {
                'available_strategies': self.quality_manager.get_available_strategies(),
                'default_strategy': self.quality_manager.default_strategy,
                'cache_enabled': self.quality_manager.enable_caching,
                'cache_stats': self.quality_manager.get_cache_stats(),
                'strategies_info': self.quality_manager.get_all_strategies_info()
            }

        except Exception as e:
            self.logger.error(f"获取质量评估信息失败: {e}")
            return {'error': str(e)}

    def set_quality_strategy(self, strategy_name: str) -> bool:
        """
        设置默认质量评估策略

        Args:
            strategy_name: 策略名称

        Returns:
            bool: 是否设置成功
        """
        try:
            if not hasattr(self, 'quality_manager') or not self.quality_manager:
                self.logger.error("质量评估管理器未初始化")
                return False

            return self.quality_manager.set_default_strategy(strategy_name)

        except Exception as e:
            self.logger.error(f"设置质量策略失败: {e}")
            return False

    def assess_chunks_quality(self, chunks: List[TextChunk], strategy_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        批量评估分块质量

        Args:
            chunks: 分块列表
            strategy_name: 指定的评估策略名称

        Returns:
            list: 质量评估结果列表
        """
        try:
            if not hasattr(self, 'quality_manager') or not self.quality_manager:
                self.logger.warning("质量评估管理器未初始化，使用基础评估逻辑")
                return [{'overall_score': self._get_basic_quality_score(chunk)} for chunk in chunks]

            # 使用质量管理器进行批量评估
            quality_results = self.quality_manager.assess_chunks_batch(chunks, strategy_name)

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
    
    def validate_chunks(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        验证分块结果
        
        Args:
            chunks: 分块列表
            
        Returns:
            dict: 验证结果
        """
        try:
            validation_result = {
                'total_chunks': len(chunks),
                'valid_chunks': 0,
                'invalid_chunks': 0,
                'quality_scores': [],
                'size_distribution': {
                    'min_size': float('inf'),
                    'max_size': 0,
                    'avg_size': 0
                },
                'issues': []
            }
            
            total_chars = 0
            
            for i, chunk in enumerate(chunks):
                is_valid = True
                
                # 检查分块大小
                if chunk.character_count < self.min_chunk_size:
                    validation_result['issues'].append(f"分块{i}过小: {chunk.character_count}字符")
                    is_valid = False
                elif chunk.character_count > self.max_chunk_size:
                    validation_result['issues'].append(f"分块{i}过大: {chunk.character_count}字符")
                    is_valid = False
                
                # 检查内容质量
                if chunk.quality_score < 0.3:
                    validation_result['issues'].append(f"分块{i}质量过低: {chunk.quality_score}")
                    is_valid = False
                
                if is_valid:
                    validation_result['valid_chunks'] += 1
                else:
                    validation_result['invalid_chunks'] += 1
                
                # 统计信息
                validation_result['quality_scores'].append(chunk.quality_score)
                total_chars += chunk.character_count
                
                validation_result['size_distribution']['min_size'] = min(
                    validation_result['size_distribution']['min_size'], 
                    chunk.character_count
                )
                validation_result['size_distribution']['max_size'] = max(
                    validation_result['size_distribution']['max_size'], 
                    chunk.character_count
                )
            
            # 计算平均值
            if chunks:
                validation_result['size_distribution']['avg_size'] = total_chars / len(chunks)
                validation_result['avg_quality_score'] = sum(validation_result['quality_scores']) / len(validation_result['quality_scores'])
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"分块验证失败: {e}")
            return {'error': str(e)}
