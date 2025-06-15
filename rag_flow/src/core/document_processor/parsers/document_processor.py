"""
模块名称: document_processor
功能描述: 统一文档处理器，提供多格式文档解析的统一接口和路由功能
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .pdf_parser import PDFParser, PDFParseResult
from .word_parser import WordParser, WordParseResult
from .excel_parser import ExcelParser, ExcelParseResult
from .powerpoint_parser import PowerPointParser, PowerPointParseResult


class DocumentType(Enum):
    """文档类型枚举"""
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    UNKNOWN = "unknown"


@dataclass
class UnifiedParseResult:
    """统一解析结果数据类"""
    document_type: DocumentType
    text_content: str
    metadata: Dict[str, Any]
    structured_data: Dict[str, Any]  # 包含表格、图像等结构化数据
    structure_info: Dict[str, Any]
    original_result: Union[PDFParseResult, WordParseResult, ExcelParseResult, PowerPointParseResult]


class DocumentProcessor:
    """
    统一文档处理器
    
    提供多格式文档解析的统一接口，支持：
    - PDF文档解析
    - Word文档解析
    - Excel文档解析
    - PowerPoint文档解析
    - 自动格式检测和路由
    - 统一的结果格式
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文档处理器
        
        Args:
            config (dict, optional): 配置参数
                - pdf_config (dict): PDF解析器配置
                - word_config (dict): Word解析器配置
                - excel_config (dict): Excel解析器配置
                - powerpoint_config (dict): PowerPoint解析器配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化各类型解析器
        self.pdf_parser = PDFParser(self.config.get('pdf_config', {}))
        self.word_parser = WordParser(self.config.get('word_config', {}))
        self.excel_parser = ExcelParser(self.config.get('excel_config', {}))
        self.powerpoint_parser = PowerPointParser(self.config.get('powerpoint_config', {}))
        
        # 文件扩展名到文档类型的映射
        self.extension_mapping = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.WORD,
            '.doc': DocumentType.WORD,
            '.xlsx': DocumentType.EXCEL,
            '.xlsm': DocumentType.EXCEL,
            '.xltx': DocumentType.EXCEL,
            '.xltm': DocumentType.EXCEL,
            '.pptx': DocumentType.POWERPOINT,
            '.ppt': DocumentType.POWERPOINT
        }
        
        # 解析器映射
        self.parser_mapping = {
            DocumentType.PDF: self.pdf_parser,
            DocumentType.WORD: self.word_parser,
            DocumentType.EXCEL: self.excel_parser,
            DocumentType.POWERPOINT: self.powerpoint_parser
        }
    
    def parse(self, file_path: str) -> UnifiedParseResult:
        """
        解析文档
        
        Args:
            file_path (str): 文档文件路径
            
        Returns:
            UnifiedParseResult: 统一解析结果
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
            Exception: 解析过程中的其他错误
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文档文件不存在: {file_path}")
            
            # 检测文档类型
            doc_type = self.detect_document_type(str(file_path))
            if doc_type == DocumentType.UNKNOWN:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
            
            self.logger.info(f"开始解析{doc_type.value}文档: {file_path}")
            
            # 获取对应的解析器
            parser = self.parser_mapping[doc_type]
            
            # 执行解析
            original_result = parser.parse(str(file_path))
            
            # 转换为统一格式
            unified_result = self._convert_to_unified_result(doc_type, original_result)
            
            self.logger.info(f"文档解析完成: {doc_type.value}")
            return unified_result
            
        except Exception as e:
            self.logger.error(f"文档解析失败: {e}")
            raise
    
    def detect_document_type(self, file_path: str) -> DocumentType:
        """
        检测文档类型
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            DocumentType: 检测到的文档类型
        """
        try:
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            return self.extension_mapping.get(extension, DocumentType.UNKNOWN)
            
        except Exception as e:
            self.logger.error(f"文档类型检测失败: {e}")
            return DocumentType.UNKNOWN
    
    def _convert_to_unified_result(self, doc_type: DocumentType, 
                                 original_result: Union[PDFParseResult, WordParseResult, 
                                                      ExcelParseResult, PowerPointParseResult]) -> UnifiedParseResult:
        """
        将原始解析结果转换为统一格式
        
        Args:
            doc_type: 文档类型
            original_result: 原始解析结果
            
        Returns:
            UnifiedParseResult: 统一解析结果
        """
        try:
            # 提取通用字段
            text_content = original_result.text_content
            metadata = original_result.metadata
            structure_info = original_result.structure_info
            
            # 构建结构化数据
            structured_data = {}
            
            if doc_type == DocumentType.PDF:
                structured_data = {
                    'tables': original_result.tables,
                    'images': original_result.images,
                    'page_count': original_result.page_count
                }
            elif doc_type == DocumentType.WORD:
                structured_data = {
                    'tables': original_result.tables,
                    'paragraphs': original_result.paragraphs
                }
            elif doc_type == DocumentType.EXCEL:
                structured_data = {
                    'worksheets': original_result.worksheets,
                    'tables': original_result.tables
                }
            elif doc_type == DocumentType.POWERPOINT:
                structured_data = {
                    'slides': original_result.slides,
                    'notes': original_result.notes
                }
            
            return UnifiedParseResult(
                document_type=doc_type,
                text_content=text_content,
                metadata=metadata,
                structured_data=structured_data,
                structure_info=structure_info,
                original_result=original_result
            )
            
        except Exception as e:
            self.logger.error(f"结果转换失败: {e}")
            raise
    
    def get_supported_formats(self) -> List[str]:
        """
        获取所有支持的文件格式
        
        Returns:
            list: 支持的文件扩展名列表
        """
        all_formats = []
        for parser in self.parser_mapping.values():
            all_formats.extend(parser.get_supported_formats())
        return list(set(all_formats))
    
    def is_supported_format(self, file_path: str) -> bool:
        """
        检查文件格式是否支持
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否支持该格式
        """
        return self.detect_document_type(file_path) != DocumentType.UNKNOWN
    
    def parse_batch(self, file_paths: List[str]) -> List[UnifiedParseResult]:
        """
        批量解析文档
        
        Args:
            file_paths (list): 文件路径列表
            
        Returns:
            list: 解析结果列表
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = self.parse(file_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"文件{file_path}解析失败: {e}")
                # 可以选择跳过失败的文件或添加错误信息
                continue
        
        return results
    
    def extract_text_only(self, file_path: str) -> str:
        """
        仅提取文档的文本内容
        
        Args:
            file_path (str): 文档文件路径
            
        Returns:
            str: 提取的文本内容
        """
        try:
            result = self.parse(file_path)
            return result.text_content
        except Exception as e:
            self.logger.error(f"文本提取失败: {e}")
            return ""
    
    def extract_metadata_only(self, file_path: str) -> Dict[str, Any]:
        """
        仅提取文档的元数据
        
        Args:
            file_path (str): 文档文件路径
            
        Returns:
            dict: 提取的元数据
        """
        try:
            result = self.parse(file_path)
            return result.metadata
        except Exception as e:
            self.logger.error(f"元数据提取失败: {e}")
            return {}
    
    def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文档基本信息
        
        Args:
            file_path (str): 文档文件路径
            
        Returns:
            dict: 文档基本信息
        """
        try:
            file_path = Path(file_path)
            doc_type = self.detect_document_type(str(file_path))
            
            info = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
                'file_extension': file_path.suffix.lower(),
                'document_type': doc_type.value,
                'is_supported': doc_type != DocumentType.UNKNOWN,
                'parser_available': doc_type in self.parser_mapping
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"文档信息获取失败: {e}")
            return {'error': str(e)}
