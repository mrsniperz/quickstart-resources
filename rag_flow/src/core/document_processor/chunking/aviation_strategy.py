"""
模块名称: aviation_strategy
功能描述: 航空文档分块策略，针对航空行业文档特点提供专门的分块处理
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from .chunking_engine import ChunkingStrategy, TextChunk, ChunkMetadata, ChunkType
from ..config.config_manager import get_config_manager


class AviationChunkingStrategy(ChunkingStrategy):
    """
    航空文档分块策略基类
    
    提供航空行业文档的通用分块处理逻辑
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化航空分块策略

        Args:
            config (dict, optional): 配置参数
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
            default_config = config_manager.get_chunking_config('aviation')
            # 如果没有aviation配置，回退到recursive配置
            if not default_config or default_config == config_manager.get_chunking_config('global'):
                default_config = config_manager.get_chunking_config('recursive')
        except Exception as e:
            self.logger.warning(f"无法加载配置文件，使用硬编码默认配置: {e}")
            default_config = self._get_fallback_config()

        # 合并用户配置和默认配置
        self.config = default_config.copy()
        if config:
            self.config.update(config)
        
        # 航空文档常见的结构标记
        self.structure_patterns = {
            'chapter': [
                r'第[一二三四五六七八九十\d]+章',
                r'Chapter\s+\d+',
                r'CHAPTER\s+\d+'
            ],
            'section': [
                r'第[一二三四五六七八九十\d]+节',
                r'Section\s+\d+',
                r'\d+\.\d+\s+',
                r'§\s*\d+'
            ],
            'subsection': [
                r'\d+\.\d+\.\d+\s+',
                r'[A-Z]\.\s+',
                r'\([a-z]\)\s+'
            ],
            'procedure_step': [
                r'步骤\s*\d+',
                r'Step\s+\d+',
                r'\d+\)\s+',
                r'[①②③④⑤⑥⑦⑧⑨⑩]\s*'
            ]
        }
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "aviation_base"

    def _get_fallback_config(self) -> Dict[str, Any]:
        """
        获取回退配置（当配置文件不可用时使用）

        Returns:
            dict: 回退配置
        """
        return {
            'chunk_size': 1200,
            'chunk_overlap': 150,
            'is_separator_regex': False,
            'keep_separator': True,
            'add_start_index': False,
            'strip_whitespace': True,
            'separators': [
                "\n\n", "\n\n\n",
                "\n第", "\n章", "\n节", "\n条", "\n款", "\n项",
                "\nChapter", "\nSection", "\nArticle",
                "\n\n•", "\n\n-", "\n\n*", "\n\n1.", "\n\n2.", "\n\n3.",
                "\n", "。", "！", "？", ".", "!", "?",
                "；", ";", "，", ",", " ", "\t",
                "、", "：", ":", ""
            ]
        }
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        分块文本内容
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
            
        Returns:
            list: 分块结果列表
        """
        try:
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 识别文档结构
            structure_info = self._analyze_document_structure(processed_text)
            
            # 根据结构进行分块
            chunks = self._chunk_by_structure(processed_text, structure_info, metadata)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"航空文档分块失败: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 处理后的文本
        """
        try:
            # 标准化换行符
            text = re.sub(r'\r\n|\r', '\n', text)
            
            # 移除多余的空行
            text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
            
            # 标准化空格
            text = re.sub(r'[ \t]+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            self.logger.warning(f"文本预处理失败: {e}")
            return text
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """
        分析文档结构
        
        Args:
            text: 文本内容
            
        Returns:
            dict: 结构分析结果
        """
        try:
            structure_info = {
                'chapters': [],
                'sections': [],
                'subsections': [],
                'procedure_steps': [],
                'tables': [],
                'figures': []
            }
            
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # 检测章节
                for pattern in self.structure_patterns['chapter']:
                    if re.match(pattern, line_stripped):
                        structure_info['chapters'].append({
                            'line_number': i,
                            'title': line_stripped,
                            'pattern': pattern
                        })
                        break
                
                # 检测节
                for pattern in self.structure_patterns['section']:
                    if re.match(pattern, line_stripped):
                        structure_info['sections'].append({
                            'line_number': i,
                            'title': line_stripped,
                            'pattern': pattern
                        })
                        break
                
                # 检测子节
                for pattern in self.structure_patterns['subsection']:
                    if re.match(pattern, line_stripped):
                        structure_info['subsections'].append({
                            'line_number': i,
                            'title': line_stripped,
                            'pattern': pattern
                        })
                        break
                
                # 检测步骤
                for pattern in self.structure_patterns['procedure_step']:
                    if re.match(pattern, line_stripped):
                        structure_info['procedure_steps'].append({
                            'line_number': i,
                            'title': line_stripped,
                            'pattern': pattern
                        })
                        break
                
                # 检测表格
                if re.search(r'表\s*\d+|Table\s+\d+|TABLE\s+\d+', line_stripped):
                    structure_info['tables'].append({
                        'line_number': i,
                        'title': line_stripped
                    })
                
                # 检测图片
                if re.search(r'图\s*\d+|Figure\s+\d+|FIGURE\s+\d+', line_stripped):
                    structure_info['figures'].append({
                        'line_number': i,
                        'title': line_stripped
                    })
            
            return structure_info
            
        except Exception as e:
            self.logger.error(f"文档结构分析失败: {e}")
            return {}
    
    def _chunk_by_structure(self, text: str, structure_info: Dict[str, Any], 
                          metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        根据结构进行分块
        
        Args:
            text: 文本内容
            structure_info: 结构信息
            metadata: 文档元数据
            
        Returns:
            list: 分块结果
        """
        try:
            chunks = []
            lines = text.split('\n')
            
            # 获取所有结构标记点
            structure_points = []
            
            for chapter in structure_info.get('chapters', []):
                structure_points.append({
                    'line_number': chapter['line_number'],
                    'type': 'chapter',
                    'title': chapter['title']
                })
            
            for section in structure_info.get('sections', []):
                structure_points.append({
                    'line_number': section['line_number'],
                    'type': 'section',
                    'title': section['title']
                })
            
            # 按行号排序
            structure_points.sort(key=lambda x: x['line_number'])
            
            # 根据结构点分块
            for i, point in enumerate(structure_points):
                start_line = point['line_number']
                end_line = structure_points[i + 1]['line_number'] if i + 1 < len(structure_points) else len(lines)
                
                # 提取分块内容
                chunk_lines = lines[start_line:end_line]
                chunk_content = '\n'.join(chunk_lines).strip()
                
                if chunk_content:
                    chunk = self._create_chunk(
                        content=chunk_content,
                        chunk_type=ChunkType.SECTION if point['type'] == 'section' else ChunkType.CHAPTER,
                        section_title=point['title'],
                        metadata=metadata,
                        start_position=start_line,
                        end_position=end_line
                    )
                    chunks.append(chunk)
            
            # 如果没有找到结构标记，使用固定大小分块
            if not chunks:
                chunks = self._chunk_by_size(text, metadata)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"结构化分块失败: {e}")
            return []
    
    def _chunk_by_size(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        按固定大小分块
        
        Args:
            text: 文本内容
            metadata: 文档元数据
            
        Returns:
            list: 分块结果
        """
        try:
            chunks = []
            chunk_size = self.config.get('chunk_size', 1000)
            overlap_size = self.config.get('overlap_size', 200)
            
            words = text.split()
            
            for i in range(0, len(words), chunk_size - overlap_size):
                chunk_words = words[i:i + chunk_size]
                chunk_content = ' '.join(chunk_words)
                
                if chunk_content.strip():
                    chunk = self._create_chunk(
                        content=chunk_content,
                        chunk_type=ChunkType.PARAGRAPH,
                        metadata=metadata,
                        start_position=i,
                        end_position=i + len(chunk_words)
                    )
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"固定大小分块失败: {e}")
            return []
    
    def _create_chunk(self, content: str, chunk_type: ChunkType, 
                     metadata: Dict[str, Any], **kwargs) -> TextChunk:
        """
        创建分块对象
        
        Args:
            content: 分块内容
            chunk_type: 分块类型
            metadata: 文档元数据
            **kwargs: 其他参数
            
        Returns:
            TextChunk: 分块对象
        """
        try:
            chunk_metadata = ChunkMetadata(
                chunk_id="",  # 将在后处理中设置
                chunk_type=chunk_type,
                source_document=metadata.get('file_path', ''),
                page_number=kwargs.get('page_number'),
                section_title=kwargs.get('section_title'),
                start_position=kwargs.get('start_position'),
                end_position=kwargs.get('end_position'),
                processing_timestamp=datetime.now().isoformat()
            )
            
            return TextChunk(
                content=content,
                metadata=chunk_metadata
            )
            
        except Exception as e:
            self.logger.error(f"分块对象创建失败: {e}")
            return TextChunk(content=content, metadata=ChunkMetadata(chunk_id="", chunk_type=chunk_type, source_document=""))


class AviationMaintenanceStrategy(AviationChunkingStrategy):
    """维修手册分块策略"""
    
    def get_strategy_name(self) -> str:
        return "aviation_maintenance"
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """分析维修手册结构"""
        structure_info = super()._analyze_document_structure(text)
        
        # 维修手册特有的结构模式
        maintenance_patterns = {
            'task': [
                r'任务\s*\d+',
                r'Task\s+\d+',
                r'TASK\s+\d+'
            ],
            'warning': [
                r'警告[:：]',
                r'WARNING[:：]',
                r'注意[:：]',
                r'CAUTION[:：]'
            ],
            'tool_requirement': [
                r'所需工具[:：]',
                r'Required Tools[:：]',
                r'工具清单[:：]'
            ]
        }
        
        lines = text.split('\n')
        structure_info['tasks'] = []
        structure_info['warnings'] = []
        structure_info['tool_requirements'] = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 检测任务
            for pattern in maintenance_patterns['task']:
                if re.match(pattern, line_stripped):
                    structure_info['tasks'].append({
                        'line_number': i,
                        'title': line_stripped
                    })
                    break
            
            # 检测警告
            for pattern in maintenance_patterns['warning']:
                if re.search(pattern, line_stripped):
                    structure_info['warnings'].append({
                        'line_number': i,
                        'content': line_stripped
                    })
                    break
            
            # 检测工具需求
            for pattern in maintenance_patterns['tool_requirement']:
                if re.search(pattern, line_stripped):
                    structure_info['tool_requirements'].append({
                        'line_number': i,
                        'content': line_stripped
                    })
                    break
        
        return structure_info


class AviationRegulationStrategy(AviationChunkingStrategy):
    """规章制度分块策略"""
    
    def get_strategy_name(self) -> str:
        return "aviation_regulation"
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """分析规章制度结构"""
        structure_info = super()._analyze_document_structure(text)
        
        # 规章制度特有的结构模式
        regulation_patterns = {
            'article': [
                r'第[一二三四五六七八九十\d]+条',
                r'Article\s+\d+',
                r'条款\s*\d+'
            ],
            'clause': [
                r'\([一二三四五六七八九十\d]+\)',
                r'\(\d+\)',
                r'[一二三四五六七八九十]\、'
            ],
            'definition': [
                r'定义[:：]',
                r'术语[:：]',
                r'Definition[:：]'
            ]
        }
        
        lines = text.split('\n')
        structure_info['articles'] = []
        structure_info['clauses'] = []
        structure_info['definitions'] = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 检测条款
            for pattern in regulation_patterns['article']:
                if re.match(pattern, line_stripped):
                    structure_info['articles'].append({
                        'line_number': i,
                        'title': line_stripped
                    })
                    break
            
            # 检测子条款
            for pattern in regulation_patterns['clause']:
                if re.match(pattern, line_stripped):
                    structure_info['clauses'].append({
                        'line_number': i,
                        'title': line_stripped
                    })
                    break
            
            # 检测定义
            for pattern in regulation_patterns['definition']:
                if re.search(pattern, line_stripped):
                    structure_info['definitions'].append({
                        'line_number': i,
                        'content': line_stripped
                    })
                    break
        
        return structure_info


class AviationStandardStrategy(AviationChunkingStrategy):
    """技术标准分块策略"""
    
    def get_strategy_name(self) -> str:
        return "aviation_standard"
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """分析技术标准结构"""
        structure_info = super()._analyze_document_structure(text)
        
        # 技术标准特有的结构模式
        standard_patterns = {
            'requirement': [
                r'要求\s*\d+',
                r'Requirement\s+\d+',
                r'REQ\s+\d+'
            ],
            'specification': [
                r'规格[:：]',
                r'Specification[:：]',
                r'技术规格[:：]'
            ],
            'test_method': [
                r'试验方法[:：]',
                r'Test Method[:：]',
                r'测试程序[:：]'
            ]
        }
        
        lines = text.split('\n')
        structure_info['requirements'] = []
        structure_info['specifications'] = []
        structure_info['test_methods'] = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 检测要求
            for pattern in standard_patterns['requirement']:
                if re.match(pattern, line_stripped):
                    structure_info['requirements'].append({
                        'line_number': i,
                        'title': line_stripped
                    })
                    break
            
            # 检测规格
            for pattern in standard_patterns['specification']:
                if re.search(pattern, line_stripped):
                    structure_info['specifications'].append({
                        'line_number': i,
                        'content': line_stripped
                    })
                    break
            
            # 检测测试方法
            for pattern in standard_patterns['test_method']:
                if re.search(pattern, line_stripped):
                    structure_info['test_methods'].append({
                        'line_number': i,
                        'content': line_stripped
                    })
                    break
        
        return structure_info


class AviationTrainingStrategy(AviationChunkingStrategy):
    """培训资料分块策略"""
    
    def get_strategy_name(self) -> str:
        return "aviation_training"
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """分析培训资料结构"""
        structure_info = super()._analyze_document_structure(text)
        
        # 培训资料特有的结构模式
        training_patterns = {
            'learning_objective': [
                r'学习目标[:：]',
                r'Learning Objective[:：]',
                r'教学目标[:：]'
            ],
            'knowledge_point': [
                r'知识点\s*\d+',
                r'Knowledge Point\s+\d+',
                r'要点\s*\d+'
            ],
            'exercise': [
                r'练习\s*\d+',
                r'Exercise\s+\d+',
                r'习题\s*\d+'
            ]
        }
        
        lines = text.split('\n')
        structure_info['learning_objectives'] = []
        structure_info['knowledge_points'] = []
        structure_info['exercises'] = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 检测学习目标
            for pattern in training_patterns['learning_objective']:
                if re.search(pattern, line_stripped):
                    structure_info['learning_objectives'].append({
                        'line_number': i,
                        'content': line_stripped
                    })
                    break
            
            # 检测知识点
            for pattern in training_patterns['knowledge_point']:
                if re.match(pattern, line_stripped):
                    structure_info['knowledge_points'].append({
                        'line_number': i,
                        'title': line_stripped
                    })
                    break
            
            # 检测练习
            for pattern in training_patterns['exercise']:
                if re.match(pattern, line_stripped):
                    structure_info['exercises'].append({
                        'line_number': i,
                        'title': line_stripped
                    })
                    break
        
        return structure_info
