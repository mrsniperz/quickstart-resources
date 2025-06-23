"""
模块名称: document_processor
功能描述: 统一文档处理器，提供多格式文档解析的统一接口和路由功能
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)

# 尝试导入性能监控和配置管理（可选）
try:
    from ..utils.performance_monitor import get_performance_monitor, ProcessingContext
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False

try:
    from ..config.config_manager import get_config_manager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

from .pdf_parser import PDFParser, PDFParseResult
from .word_parser import WordParser, WordParseResult
from .excel_parser import ExcelParser, ExcelParseResult
from .powerpoint_parser import PowerPointParser, PowerPointParseResult
from .docling_parser import DoclingParser, DoclingParseResult


class DocumentType(Enum):
    """文档类型枚举"""
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    DOCLING = "docling"  # Docling统一处理器
    UNKNOWN = "unknown"


@dataclass
class UnifiedParseResult:
    """统一解析结果数据类"""
    document_type: DocumentType
    text_content: str
    metadata: Dict[str, Any]
    structured_data: Dict[str, Any]  # 包含表格、图像等结构化数据
    structure_info: Dict[str, Any]
    original_result: Union[PDFParseResult, WordParseResult, ExcelParseResult, PowerPointParseResult, DoclingParseResult]


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
        self.logger = logger

        # 初始化性能监控（如果可用）
        self.performance_monitor = None
        if PERFORMANCE_MONITORING_AVAILABLE:
            try:
                self.performance_monitor = get_performance_monitor()
                self.logger.info("性能监控已启用")
            except Exception as e:
                self.logger.warning(f"性能监控初始化失败: {e}")

        # 从配置管理器加载配置（如果可用）
        if CONFIG_MANAGER_AVAILABLE and not config:
            try:
                config_manager = get_config_manager()
                self.config = config_manager.get_document_processor_config()
                self.logger.info("从配置管理器加载配置")
            except Exception as e:
                self.logger.warning(f"配置管理器加载失败: {e}")
        
        # 初始化各类型解析器
        self.pdf_parser = PDFParser(self.config.get('pdf_config', {}))
        self.word_parser = WordParser(self.config.get('word_config', {}))
        self.excel_parser = ExcelParser(self.config.get('excel_config', {}))
        self.powerpoint_parser = PowerPointParser(self.config.get('powerpoint_config', {}))

        # 初始化Docling解析器（如果可用）
        self.docling_parser = None
        self.use_docling = self.config.get('use_docling', False)
        if self.use_docling:
            try:
                self.docling_parser = DoclingParser(self.config.get('docling_config', {}))
                self.logger.info("Docling解析器初始化成功")
            except ImportError:
                self.logger.warning("Docling库未安装，将使用传统解析器")
                self.use_docling = False
            except Exception as e:
                self.logger.error(f"Docling解析器初始化失败: {e}")
                self.use_docling = False
        
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

        # 如果启用Docling，添加额外支持的格式
        if self.use_docling and self.docling_parser:
            docling_formats = {
                '.html': DocumentType.DOCLING,
                '.htm': DocumentType.DOCLING,
                '.csv': DocumentType.DOCLING,
                '.md': DocumentType.DOCLING,
                '.markdown': DocumentType.DOCLING,
                '.txt': DocumentType.DOCLING,
                '.png': DocumentType.DOCLING,
                '.jpg': DocumentType.DOCLING,
                '.jpeg': DocumentType.DOCLING,
                '.gif': DocumentType.DOCLING,
                '.bmp': DocumentType.DOCLING,
                '.tiff': DocumentType.DOCLING,
                '.tif': DocumentType.DOCLING,
            }
            self.extension_mapping.update(docling_formats)
        
        # 解析器映射
        self.parser_mapping = {
            DocumentType.PDF: self.pdf_parser,
            DocumentType.WORD: self.word_parser,
            DocumentType.EXCEL: self.excel_parser,
            DocumentType.POWERPOINT: self.powerpoint_parser
        }

        # 如果启用Docling，添加到解析器映射
        if self.use_docling and self.docling_parser:
            self.parser_mapping[DocumentType.DOCLING] = self.docling_parser
    
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

            # 获取文件信息用于监控
            file_size = file_path.stat().st_size
            file_extension = file_path.suffix.lower()

            # 检测文档类型和选择解析器
            if self.should_use_docling(str(file_path)):
                doc_type = DocumentType.DOCLING
                parser = self.docling_parser
                parser_type = "docling"
                self.logger.info(f"使用Docling解析器处理文档: {file_path}")
            else:
                doc_type = self.detect_document_type(str(file_path))
                if doc_type == DocumentType.UNKNOWN:
                    raise ValueError(f"不支持的文件格式: {file_path.suffix}")
                parser = self.parser_mapping[doc_type]
                parser_type = doc_type.value
                self.logger.info(f"开始解析{doc_type.value}文档: {file_path}")

            # 使用性能监控上下文（如果可用）
            if PERFORMANCE_MONITORING_AVAILABLE and self.performance_monitor:
                with ProcessingContext(str(file_path), file_size, file_extension, parser_type):
                    # 执行解析
                    original_result = parser.parse(str(file_path))

                    # 转换为统一格式
                    unified_result = self._convert_to_unified_result(doc_type, original_result)
            else:
                # 执行解析（无监控）
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
                                                      ExcelParseResult, PowerPointParseResult, DoclingParseResult]) -> UnifiedParseResult:
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
            elif doc_type == DocumentType.DOCLING:
                # Docling已经提供了统一的结构化数据格式
                structured_data = original_result.structured_data
            
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

    def should_use_docling(self, file_path: str) -> bool:
        """
        判断是否应该使用Docling解析器

        Args:
            file_path (str): 文件路径

        Returns:
            bool: 是否使用Docling
        """
        if not self.use_docling or not self.docling_parser:
            return False

        file_extension = Path(file_path).suffix.lower()

        # Docling独有的格式
        docling_only_formats = {'.html', '.htm', '.csv', '.md', '.markdown', '.txt',
                               '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif'}

        if file_extension in docling_only_formats:
            return True

        # 对于共同支持的格式，可以通过配置选择
        prefer_docling = self.config.get('prefer_docling_for_common_formats', False)
        common_formats = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'}

        if file_extension in common_formats and prefer_docling:
            return True

        return False

    def get_docling_info(self) -> Dict[str, Any]:
        """
        获取Docling解析器信息

        Returns:
            dict: Docling信息
        """
        info = {
            'available': self.use_docling and self.docling_parser is not None,
            'enabled': self.use_docling,
            'supported_formats': [],
            'dependencies': {}
        }

        if self.docling_parser:
            info['supported_formats'] = self.docling_parser.get_supported_formats()
            info['dependencies'] = DoclingParser.check_dependencies()

        return info

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息

        Returns:
            dict: 性能统计信息
        """
        if PERFORMANCE_MONITORING_AVAILABLE and self.performance_monitor:
            return self.performance_monitor.get_current_stats()
        else:
            return {
                'performance_monitoring': False,
                'message': '性能监控不可用'
            }

    def reset_performance_stats(self):
        """重置性能统计信息"""
        if PERFORMANCE_MONITORING_AVAILABLE and self.performance_monitor:
            self.performance_monitor.reset_stats()
            self.logger.info("性能统计信息已重置")
        else:
            self.logger.warning("性能监控不可用，无法重置统计信息")
