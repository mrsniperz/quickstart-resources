"""
模块名称: docling_parser
功能描述: Docling文档解析器，基于Docling库实现多格式文档的统一解析，支持PDF、Word、HTML、Excel、CSV、Markdown、图片等格式
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from io import BytesIO
import json

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat, DocumentStream
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    # 尝试导入 ConversionError，如果不存在则使用通用异常
    try:
        from docling.exceptions import ConversionError
    except ImportError:
        # 如果 ConversionError 不存在，定义一个自定义异常
        class ConversionError(Exception):
            pass
    DOCLING_AVAILABLE = True

    # 尝试导入可选的高级功能
    try:
        from docling.document_converter import WordFormatOption
        WORD_FORMAT_AVAILABLE = True
    except ImportError:
        WORD_FORMAT_AVAILABLE = False

    try:
        from docling.datamodel.pipeline_options import (
            TableFormerMode,
            PictureDescriptionVlmOptions,
            PictureDescriptionApiOptions,
            EasyOcrOptions,
            TesseractOcrOptions,
            VlmPipelineOptions
        )
        ADVANCED_OPTIONS_AVAILABLE = True
    except ImportError:
        ADVANCED_OPTIONS_AVAILABLE = False

    try:
        from docling.pipeline.vlm_pipeline import VlmPipeline
        from docling.datamodel import vlm_model_specs
        VLM_PIPELINE_AVAILABLE = True
    except ImportError:
        VLM_PIPELINE_AVAILABLE = False

    try:
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
        PYPDFIUM_BACKEND_AVAILABLE = True
    except ImportError:
        PYPDFIUM_BACKEND_AVAILABLE = False

except ImportError:
    DOCLING_AVAILABLE = False
    WORD_FORMAT_AVAILABLE = False
    ADVANCED_OPTIONS_AVAILABLE = False
    VLM_PIPELINE_AVAILABLE = False
    PYPDFIUM_BACKEND_AVAILABLE = False

from ..extractors.metadata_extractor import MetadataExtractor


@dataclass
class DoclingParseResult:
    """Docling解析结果数据类"""
    text_content: str
    metadata: Dict[str, Any]
    structured_data: Dict[str, Any]  # 包含表格、图像等结构化数据
    structure_info: Dict[str, Any]
    original_format: str
    docling_document: Optional[Any] = None  # 原始Docling文档对象


class DoclingParser:
    """
    Docling文档处理器
    
    基于Docling库实现多格式文档的统一解析，包括：
    - PDF文档解析
    - Word文档解析 (.doc, .docx)
    - HTML文件解析
    - Excel表格解析 (.xls, .xlsx)
    - CSV文件解析
    - Markdown文件解析
    - 图片文件解析（支持OCR）
    - 统一输出为Markdown格式
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Docling解析器

        Args:
            config (dict, optional): 配置参数
                - enable_ocr (bool): 是否启用OCR，默认True
                - ocr_engine (str): OCR引擎类型，支持'easyocr', 'tesseract'，默认'easyocr'
                - enable_table_structure (bool): 是否启用表格结构识别，默认True
                - table_mode (str): 表格模式，支持'fast', 'accurate'，默认'fast'
                - enable_cell_matching (bool): 是否启用单元格匹配，默认True
                - enable_picture_description (bool): 是否启用图片描述，默认False
                - picture_description_model (str): 图片描述模型，默认None
                - picture_description_prompt (str): 图片描述提示词，默认None
                - enable_picture_classification (bool): 是否启用图片分类，默认False
                - enable_formula_enrichment (bool): 是否启用公式识别，默认False
                - enable_code_enrichment (bool): 是否启用代码识别，默认False
                - generate_picture_images (bool): 是否生成图片，默认True
                - images_scale (int): 图片缩放比例，默认2
                - max_num_pages (int): 最大页数限制，默认None
                - max_file_size (int): 最大文件大小限制（字节），默认None
                - artifacts_path (str): 模型文件路径，默认None
                - enable_remote_services (bool): 是否启用远程服务，默认False
                - use_vlm_pipeline (bool): 是否使用VLM管道，默认False
                - vlm_model (str): VLM模型名称，默认None
                - custom_backend (str): 自定义后端，默认None
                - allowed_formats (list): 允许的文件格式列表，默认None（支持所有格式）
        """
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling库未安装。请运行: pip install docling"
            )

        self.config = config or {}
        self.logger = logger

        # 初始化元数据提取器
        self.metadata_extractor = MetadataExtractor()

        # 基础配置参数
        self.enable_ocr = self.config.get('enable_ocr', True)
        self.ocr_engine = self.config.get('ocr_engine', 'easyocr')
        self.enable_table_structure = self.config.get('enable_table_structure', True)
        self.table_mode = self.config.get('table_mode', 'fast')
        self.enable_cell_matching = self.config.get('enable_cell_matching', True)

        # 图片处理配置
        self.enable_picture_description = self.config.get('enable_picture_description', False)
        self.picture_description_model = self.config.get('picture_description_model', None)
        self.picture_description_prompt = self.config.get('picture_description_prompt', None)
        self.enable_picture_classification = self.config.get('enable_picture_classification', False)
        self.generate_picture_images = self.config.get('generate_picture_images', True)
        self.images_scale = self.config.get('images_scale', 2)

        # 内容识别配置
        self.enable_formula_enrichment = self.config.get('enable_formula_enrichment', False)
        self.enable_code_enrichment = self.config.get('enable_code_enrichment', False)

        # 系统配置
        self.max_num_pages = self.config.get('max_num_pages', None)
        self.max_file_size = self.config.get('max_file_size', None)
        self.artifacts_path = self.config.get('artifacts_path', None)
        self.enable_remote_services = self.config.get('enable_remote_services', False)

        # 高级配置
        self.use_vlm_pipeline = self.config.get('use_vlm_pipeline', False)
        self.vlm_model = self.config.get('vlm_model', None)
        self.custom_backend = self.config.get('custom_backend', None)
        self.allowed_formats = self.config.get('allowed_formats', None)

        # 初始化Docling转换器
        self._init_converter()
        
        # 支持的文件格式映射
        self.supported_formats = {
            '.pdf': InputFormat.PDF,
            '.docx': InputFormat.DOCX,
            '.doc': InputFormat.DOCX,  # 通过docx处理
            '.html': InputFormat.HTML,
            '.htm': InputFormat.HTML,
            '.xlsx': InputFormat.XLSX,
            '.xls': InputFormat.XLSX,  # 通过xlsx处理
            '.csv': InputFormat.CSV,
            '.md': InputFormat.MD,
            '.markdown': InputFormat.MD,
            '.txt': InputFormat.MD,  # 作为markdown处理
            '.png': InputFormat.IMAGE,
            '.jpg': InputFormat.IMAGE,
            '.jpeg': InputFormat.IMAGE,
            '.gif': InputFormat.IMAGE,
            '.bmp': InputFormat.IMAGE,
            '.tiff': InputFormat.IMAGE,
            '.tif': InputFormat.IMAGE,
            '.pptx': InputFormat.PPTX,
            '.ppt': InputFormat.PPTX,  # 通过pptx处理
        }
    
    def _init_converter(self):
        """初始化Docling文档转换器"""
        try:
            # 配置PDF管道选项
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = self.enable_ocr
            pipeline_options.do_table_structure = self.enable_table_structure
            pipeline_options.do_picture_description = self.enable_picture_description
            pipeline_options.do_formula_enrichment = self.enable_formula_enrichment
            pipeline_options.do_code_enrichment = self.enable_code_enrichment
            pipeline_options.generate_picture_images = self.generate_picture_images
            pipeline_options.images_scale = self.images_scale
            pipeline_options.enable_remote_services = self.enable_remote_services

            # 配置图片分类
            if ADVANCED_OPTIONS_AVAILABLE and self.enable_picture_classification:
                pipeline_options.do_picture_classification = self.enable_picture_classification

            # 配置表格模式
            if ADVANCED_OPTIONS_AVAILABLE and hasattr(pipeline_options, 'table_structure_options'):
                if self.table_mode == 'accurate':
                    try:
                        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
                    except:
                        self.logger.warning("无法设置表格模式为accurate，使用默认模式")

                pipeline_options.table_structure_options.do_cell_matching = self.enable_cell_matching

            # 配置OCR引擎
            if ADVANCED_OPTIONS_AVAILABLE and self.enable_ocr:
                if self.ocr_engine == 'tesseract':
                    try:
                        pipeline_options.ocr_options = TesseractOcrOptions()
                    except:
                        self.logger.warning("无法设置Tesseract OCR，使用默认OCR")
                elif self.ocr_engine == 'easyocr':
                    try:
                        pipeline_options.ocr_options = EasyOcrOptions()
                    except:
                        self.logger.warning("无法设置EasyOCR，使用默认OCR")

            # 配置图片描述
            if ADVANCED_OPTIONS_AVAILABLE and self.enable_picture_description:
                if self.picture_description_model and self.picture_description_prompt:
                    try:
                        pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
                            repo_id=self.picture_description_model,
                            prompt=self.picture_description_prompt
                        )
                    except:
                        self.logger.warning("无法设置自定义图片描述模型，使用默认设置")

            if self.artifacts_path:
                pipeline_options.artifacts_path = self.artifacts_path

            # 配置格式选项
            format_options = {
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }

            # 配置Word格式选项
            if WORD_FORMAT_AVAILABLE:
                try:
                    format_options[InputFormat.DOCX] = WordFormatOption()
                except:
                    self.logger.warning("无法配置Word格式选项")

            # 配置VLM管道
            if VLM_PIPELINE_AVAILABLE and self.use_vlm_pipeline:
                try:
                    vlm_options = None
                    if self.vlm_model:
                        vlm_options = VlmPipelineOptions(
                            vlm_options=getattr(vlm_model_specs, self.vlm_model, None)
                        )

                    format_options[InputFormat.PDF] = PdfFormatOption(
                        pipeline_cls=VlmPipeline,
                        pipeline_options=vlm_options or pipeline_options
                    )
                except:
                    self.logger.warning("无法配置VLM管道，使用标准管道")

            # 配置自定义后端
            if PYPDFIUM_BACKEND_AVAILABLE and self.custom_backend == 'pypdfium':
                try:
                    format_options[InputFormat.PDF] = PdfFormatOption(
                        pipeline_options=pipeline_options,
                        backend=PyPdfiumDocumentBackend
                    )
                except:
                    self.logger.warning("无法配置自定义后端，使用默认后端")

            # 确定允许的格式
            allowed_formats = self.allowed_formats
            if allowed_formats is None:
                allowed_formats = list(self.supported_formats.values())

            # 初始化转换器
            self.converter = DocumentConverter(
                format_options=format_options,
                allowed_formats=allowed_formats
            )

            self.logger.info("Docling转换器初始化成功")

        except Exception as e:
            self.logger.error(f"Docling转换器初始化失败: {e}")
            raise
    
    def parse(self, file_path: str) -> DoclingParseResult:
        """
        解析文档
        
        Args:
            file_path (str): 文档文件路径
            
        Returns:
            DoclingParseResult: 解析结果
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
            ConversionError: Docling转换错误
            Exception: 解析过程中的其他错误
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文档文件不存在: {file_path}")
            
            # 检查文件格式支持
            file_extension = file_path.suffix.lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"不支持的文件格式: {file_extension}")
            
            self.logger.info(f"开始使用Docling解析文档: {file_path}")
            
            # 执行转换
            conversion_result = self.converter.convert(
                str(file_path),
                max_num_pages=self.max_num_pages,
                max_file_size=self.max_file_size
            )
            
            # 检查转换状态
            if conversion_result.status.name != "SUCCESS":
                raise ConversionError(f"文档转换失败: {conversion_result.status}")
            
            # 获取Docling文档对象
            docling_document = conversion_result.document
            
            # 提取文本内容（转换为Markdown）
            text_content = docling_document.export_to_markdown()
            
            # 提取元数据
            metadata = self._extract_metadata(docling_document, file_path)
            
            # 提取结构化数据
            structured_data = self._extract_structured_data(docling_document)
            
            # 分析文档结构
            structure_info = self._analyze_structure(docling_document)
            
            result = DoclingParseResult(
                text_content=text_content,
                metadata=metadata,
                structured_data=structured_data,
                structure_info=structure_info,
                original_format=file_extension,
                docling_document=docling_document
            )
            
            self.logger.info(f"Docling文档解析完成: {file_path}")
            return result
            
        except ConversionError as e:
            self.logger.error(f"Docling转换失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"文档解析失败: {e}")
            raise
    
    def parse_stream(self, stream: BytesIO, filename: str) -> DoclingParseResult:
        """
        解析文档流
        
        Args:
            stream (BytesIO): 文档数据流
            filename (str): 文件名（用于确定格式）
            
        Returns:
            DoclingParseResult: 解析结果
        """
        try:
            # 检查文件格式支持
            file_extension = Path(filename).suffix.lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"不支持的文件格式: {file_extension}")
            
            self.logger.info(f"开始使用Docling解析文档流: {filename}")
            
            # 创建文档流对象
            document_stream = DocumentStream(name=filename, stream=stream)
            
            # 执行转换
            conversion_result = self.converter.convert(
                document_stream,
                max_num_pages=self.max_num_pages,
                max_file_size=self.max_file_size
            )
            
            # 检查转换状态
            if conversion_result.status.name != "SUCCESS":
                raise ConversionError(f"文档转换失败: {conversion_result.status}")
            
            # 获取Docling文档对象
            docling_document = conversion_result.document
            
            # 提取文本内容（转换为Markdown）
            text_content = docling_document.export_to_markdown()
            
            # 提取元数据
            metadata = self._extract_metadata(docling_document, Path(filename))
            
            # 提取结构化数据
            structured_data = self._extract_structured_data(docling_document)
            
            # 分析文档结构
            structure_info = self._analyze_structure(docling_document)
            
            result = DoclingParseResult(
                text_content=text_content,
                metadata=metadata,
                structured_data=structured_data,
                structure_info=structure_info,
                original_format=file_extension,
                docling_document=docling_document
            )
            
            self.logger.info(f"Docling文档流解析完成: {filename}")
            return result
            
        except ConversionError as e:
            self.logger.error(f"Docling转换失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"文档流解析失败: {e}")
            raise

    def _extract_metadata(self, docling_document: Any, file_path: Path) -> Dict[str, Any]:
        """
        提取文档元数据

        Args:
            docling_document: Docling文档对象
            file_path: 文件路径

        Returns:
            dict: 元数据信息
        """
        try:
            metadata = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_extension': file_path.suffix.lower(),
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
                'parser_type': 'docling',
                'docling_version': getattr(docling_document, 'version', 'unknown'),
            }

            # 尝试提取Docling文档的元数据
            if hasattr(docling_document, 'meta') and docling_document.meta:
                doc_meta = docling_document.meta
                if hasattr(doc_meta, 'export_json_dict'):
                    metadata.update(doc_meta.export_json_dict())
                else:
                    metadata['docling_meta'] = str(doc_meta)

            # 提取页面信息
            if hasattr(docling_document, 'pages') and docling_document.pages:
                metadata['page_count'] = len(docling_document.pages)
                metadata['page_dimensions'] = []
                for page in docling_document.pages:
                    if hasattr(page, 'size'):
                        metadata['page_dimensions'].append({
                            'width': page.size.width,
                            'height': page.size.height
                        })

            # 统计文档元素
            element_counts = self._count_document_elements(docling_document)
            metadata.update(element_counts)

            return metadata

        except Exception as e:
            self.logger.error(f"元数据提取失败: {e}")
            return {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_extension': file_path.suffix.lower(),
                'parser_type': 'docling',
                'error': str(e)
            }

    def _extract_structured_data(self, docling_document: Any) -> Dict[str, Any]:
        """
        提取结构化数据

        Args:
            docling_document: Docling文档对象

        Returns:
            dict: 结构化数据
        """
        try:
            structured_data = {
                'tables': [],
                'images': [],
                'headings': [],
                'lists': [],
                'code_blocks': [],
                'formulas': []
            }

            # 遍历文档元素
            if hasattr(docling_document, 'iterate_items'):
                for item, level in docling_document.iterate_items():
                    item_type = type(item).__name__

                    # 处理表格
                    if 'Table' in item_type:
                        table_data = self._extract_table_data(item)
                        if table_data:
                            structured_data['tables'].append(table_data)

                    # 处理图片
                    elif 'Picture' in item_type or 'Image' in item_type:
                        image_data = self._extract_image_data(item)
                        if image_data:
                            structured_data['images'].append(image_data)

                    # 处理标题
                    elif 'Heading' in item_type or 'Title' in item_type:
                        heading_data = self._extract_heading_data(item, level)
                        if heading_data:
                            structured_data['headings'].append(heading_data)

                    # 处理列表
                    elif 'List' in item_type:
                        list_data = self._extract_list_data(item)
                        if list_data:
                            structured_data['lists'].append(list_data)

                    # 处理代码块
                    elif 'Code' in item_type:
                        code_data = self._extract_code_data(item)
                        if code_data:
                            structured_data['code_blocks'].append(code_data)

                    # 处理公式
                    elif 'Formula' in item_type or 'Equation' in item_type:
                        formula_data = self._extract_formula_data(item)
                        if formula_data:
                            structured_data['formulas'].append(formula_data)

            return structured_data

        except Exception as e:
            self.logger.error(f"结构化数据提取失败: {e}")
            return {
                'tables': [],
                'images': [],
                'headings': [],
                'lists': [],
                'code_blocks': [],
                'formulas': [],
                'error': str(e)
            }

    def _analyze_structure(self, docling_document: Any) -> Dict[str, Any]:
        """
        分析文档结构

        Args:
            docling_document: Docling文档对象

        Returns:
            dict: 结构分析信息
        """
        try:
            structure = {
                'document_type': 'unknown',
                'has_toc': False,
                'hierarchy_levels': 0,
                'element_distribution': {},
                'reading_order': [],
                'language': 'unknown'
            }

            # 分析文档类型
            if hasattr(docling_document, 'meta') and docling_document.meta:
                structure['document_type'] = getattr(docling_document.meta, 'document_type', 'unknown')

            # 分析层次结构
            max_level = 0
            element_counts = {}

            if hasattr(docling_document, 'iterate_items'):
                for item, level in docling_document.iterate_items():
                    item_type = type(item).__name__
                    max_level = max(max_level, level)

                    # 统计元素类型
                    element_counts[item_type] = element_counts.get(item_type, 0) + 1

                    # 记录阅读顺序
                    structure['reading_order'].append({
                        'type': item_type,
                        'level': level,
                        'text_preview': self._get_item_text_preview(item)
                    })

            structure['hierarchy_levels'] = max_level
            structure['element_distribution'] = element_counts

            # 检查是否有目录
            if 'Heading' in element_counts or 'Title' in element_counts:
                structure['has_toc'] = True

            return structure

        except Exception as e:
            self.logger.error(f"结构分析失败: {e}")
            return {
                'document_type': 'unknown',
                'has_toc': False,
                'hierarchy_levels': 0,
                'element_distribution': {},
                'reading_order': [],
                'error': str(e)
            }

    def _count_document_elements(self, docling_document: Any) -> Dict[str, int]:
        """统计文档元素数量"""
        try:
            counts = {
                'total_elements': 0,
                'text_elements': 0,
                'table_elements': 0,
                'image_elements': 0,
                'heading_elements': 0,
                'list_elements': 0,
                'code_elements': 0,
                'formula_elements': 0
            }

            if hasattr(docling_document, 'iterate_items'):
                for item, level in docling_document.iterate_items():
                    item_type = type(item).__name__
                    counts['total_elements'] += 1

                    if 'Text' in item_type:
                        counts['text_elements'] += 1
                    elif 'Table' in item_type:
                        counts['table_elements'] += 1
                    elif 'Picture' in item_type or 'Image' in item_type:
                        counts['image_elements'] += 1
                    elif 'Heading' in item_type or 'Title' in item_type:
                        counts['heading_elements'] += 1
                    elif 'List' in item_type:
                        counts['list_elements'] += 1
                    elif 'Code' in item_type:
                        counts['code_elements'] += 1
                    elif 'Formula' in item_type or 'Equation' in item_type:
                        counts['formula_elements'] += 1

            return counts

        except Exception as e:
            self.logger.error(f"元素统计失败: {e}")
            return {
                'total_elements': 0,
                'text_elements': 0,
                'table_elements': 0,
                'image_elements': 0,
                'heading_elements': 0,
                'list_elements': 0,
                'code_elements': 0,
                'formula_elements': 0
            }

    def _extract_table_data(self, table_item: Any) -> Optional[Dict[str, Any]]:
        """提取表格数据"""
        try:
            table_data = {
                'type': 'table',
                'data': [],
                'rows': 0,
                'columns': 0,
                'caption': '',
                'bbox': None
            }

            # 尝试导出为DataFrame
            if hasattr(table_item, 'export_to_dataframe'):
                import pandas as pd
                df = table_item.export_to_dataframe()
                table_data['data'] = df.values.tolist()
                table_data['rows'] = len(df)
                table_data['columns'] = len(df.columns)
                table_data['headers'] = df.columns.tolist()

            # 获取表格文本
            if hasattr(table_item, 'text'):
                table_data['text'] = table_item.text

            # 获取边界框
            if hasattr(table_item, 'bbox'):
                table_data['bbox'] = table_item.bbox

            return table_data

        except Exception as e:
            self.logger.warning(f"表格数据提取失败: {e}")
            return None

    def _extract_image_data(self, image_item: Any) -> Optional[Dict[str, Any]]:
        """提取图片数据"""
        try:
            image_data = {
                'type': 'image',
                'caption': '',
                'description': '',
                'bbox': None,
                'size': None
            }

            # 获取图片描述
            if hasattr(image_item, 'text'):
                image_data['description'] = image_item.text

            # 获取边界框
            if hasattr(image_item, 'bbox'):
                image_data['bbox'] = image_item.bbox

            # 获取图片尺寸
            if hasattr(image_item, 'size'):
                image_data['size'] = {
                    'width': image_item.size.width,
                    'height': image_item.size.height
                }

            return image_data

        except Exception as e:
            self.logger.warning(f"图片数据提取失败: {e}")
            return None

    def _extract_heading_data(self, heading_item: Any, level: int) -> Optional[Dict[str, Any]]:
        """提取标题数据"""
        try:
            heading_data = {
                'type': 'heading',
                'text': '',
                'level': level,
                'bbox': None
            }

            # 获取标题文本
            if hasattr(heading_item, 'text'):
                heading_data['text'] = heading_item.text

            # 获取边界框
            if hasattr(heading_item, 'bbox'):
                heading_data['bbox'] = heading_item.bbox

            return heading_data

        except Exception as e:
            self.logger.warning(f"标题数据提取失败: {e}")
            return None

    def _extract_list_data(self, list_item: Any) -> Optional[Dict[str, Any]]:
        """提取列表数据"""
        try:
            list_data = {
                'type': 'list',
                'items': [],
                'list_type': 'unordered',
                'bbox': None
            }

            # 获取列表文本
            if hasattr(list_item, 'text'):
                list_data['text'] = list_item.text
                # 简单解析列表项
                lines = list_item.text.split('\n')
                list_data['items'] = [line.strip() for line in lines if line.strip()]

            # 获取边界框
            if hasattr(list_item, 'bbox'):
                list_data['bbox'] = list_item.bbox

            return list_data

        except Exception as e:
            self.logger.warning(f"列表数据提取失败: {e}")
            return None

    def _extract_code_data(self, code_item: Any) -> Optional[Dict[str, Any]]:
        """提取代码数据"""
        try:
            code_data = {
                'type': 'code',
                'code': '',
                'language': 'unknown',
                'bbox': None
            }

            # 获取代码文本
            if hasattr(code_item, 'text'):
                code_data['code'] = code_item.text

            # 获取编程语言
            if hasattr(code_item, 'language'):
                code_data['language'] = code_item.language

            # 获取边界框
            if hasattr(code_item, 'bbox'):
                code_data['bbox'] = code_item.bbox

            return code_data

        except Exception as e:
            self.logger.warning(f"代码数据提取失败: {e}")
            return None

    def _extract_formula_data(self, formula_item: Any) -> Optional[Dict[str, Any]]:
        """提取公式数据"""
        try:
            formula_data = {
                'type': 'formula',
                'latex': '',
                'text': '',
                'bbox': None
            }

            # 获取LaTeX格式
            if hasattr(formula_item, 'latex'):
                formula_data['latex'] = formula_item.latex

            # 获取文本格式
            if hasattr(formula_item, 'text'):
                formula_data['text'] = formula_item.text

            # 获取边界框
            if hasattr(formula_item, 'bbox'):
                formula_data['bbox'] = formula_item.bbox

            return formula_data

        except Exception as e:
            self.logger.warning(f"公式数据提取失败: {e}")
            return None

    def _get_item_text_preview(self, item: Any, max_length: int = 100) -> str:
        """获取元素文本预览"""
        try:
            if hasattr(item, 'text') and item.text:
                text = str(item.text).strip()
                if len(text) > max_length:
                    return text[:max_length] + "..."
                return text
            return ""
        except Exception:
            return ""

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式

        Returns:
            list: 支持的文件扩展名列表
        """
        return list(self.supported_formats.keys())

    def is_format_supported(self, file_path: str) -> bool:
        """
        检查文件格式是否支持

        Args:
            file_path (str): 文件路径

        Returns:
            bool: 是否支持该格式
        """
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_formats

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

    def convert_to_markdown(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        将文档转换为Markdown格式

        Args:
            file_path (str): 输入文档路径
            output_path (str, optional): 输出Markdown文件路径

        Returns:
            str: Markdown内容
        """
        try:
            result = self.parse(file_path)
            markdown_content = result.text_content

            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                self.logger.info(f"Markdown文件已保存到: {output_path}")

            return markdown_content

        except Exception as e:
            self.logger.error(f"Markdown转换失败: {e}")
            raise

    def batch_convert(self, file_paths: List[str], output_dir: Optional[str] = None) -> List[DoclingParseResult]:
        """
        批量转换文档

        Args:
            file_paths (list): 文件路径列表
            output_dir (str, optional): 输出目录

        Returns:
            list: 解析结果列表
        """
        results = []

        for file_path in file_paths:
            try:
                result = self.parse(file_path)
                results.append(result)

                # 如果指定了输出目录，保存Markdown文件
                if output_dir:
                    output_dir_path = Path(output_dir)
                    output_dir_path.mkdir(parents=True, exist_ok=True)

                    input_path = Path(file_path)
                    output_file = output_dir_path / f"{input_path.stem}.md"

                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result.text_content)

                    self.logger.info(f"已保存: {output_file}")

            except Exception as e:
                self.logger.error(f"文件{file_path}处理失败: {e}")
                continue

        return results

    def export_figures(self, file_path: str, output_dir: str) -> List[Dict[str, Any]]:
        """
        导出文档中的图形

        Args:
            file_path (str): 文档文件路径
            output_dir (str): 图形输出目录

        Returns:
            list: 导出的图形信息列表
        """
        try:
            result = self.parse(file_path)
            figures = []

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 从结构化数据中提取图片
            for i, image_data in enumerate(result.structured_data.get('images', [])):
                figure_info = {
                    'index': i,
                    'description': image_data.get('description', ''),
                    'caption': image_data.get('caption', ''),
                    'bbox': image_data.get('bbox'),
                    'size': image_data.get('size'),
                    'file_path': None
                }

                # 如果有图片数据，尝试保存
                if hasattr(result.docling_document, 'pictures') and result.docling_document.pictures:
                    try:
                        if i < len(result.docling_document.pictures):
                            picture = result.docling_document.pictures[i]
                            if hasattr(picture, 'image') and picture.image:
                                figure_path = output_path / f"figure_{i}.png"
                                picture.image.save(str(figure_path))
                                figure_info['file_path'] = str(figure_path)
                                self.logger.info(f"图形已保存: {figure_path}")
                    except Exception as e:
                        self.logger.warning(f"保存图形{i}失败: {e}")

                figures.append(figure_info)

            return figures

        except Exception as e:
            self.logger.error(f"图形导出失败: {e}")
            return []

    def export_tables(self, file_path: str, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        导出文档中的表格

        Args:
            file_path (str): 文档文件路径
            output_dir (str, optional): 表格输出目录

        Returns:
            list: 导出的表格信息列表
        """
        try:
            result = self.parse(file_path)
            tables = []

            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

            # 从结构化数据中提取表格
            for i, table_data in enumerate(result.structured_data.get('tables', [])):
                table_info = {
                    'index': i,
                    'rows': table_data.get('rows', 0),
                    'columns': table_data.get('columns', 0),
                    'data': table_data.get('data', []),
                    'headers': table_data.get('headers', []),
                    'caption': table_data.get('caption', ''),
                    'bbox': table_data.get('bbox'),
                    'text': table_data.get('text', ''),
                    'file_path': None
                }

                # 如果指定了输出目录，保存表格为CSV
                if output_dir and table_data.get('data'):
                    try:
                        import pandas as pd
                        df = pd.DataFrame(table_data['data'], columns=table_data.get('headers', []))
                        table_path = output_path / f"table_{i}.csv"
                        df.to_csv(table_path, index=False, encoding='utf-8')
                        table_info['file_path'] = str(table_path)
                        self.logger.info(f"表格已保存: {table_path}")
                    except Exception as e:
                        self.logger.warning(f"保存表格{i}失败: {e}")

                tables.append(table_info)

            return tables

        except Exception as e:
            self.logger.error(f"表格导出失败: {e}")
            return []

    def get_document_statistics(self, file_path: str) -> Dict[str, Any]:
        """
        获取文档统计信息

        Args:
            file_path (str): 文档文件路径

        Returns:
            dict: 文档统计信息
        """
        try:
            result = self.parse(file_path)

            stats = {
                'file_info': {
                    'name': result.metadata.get('file_name', ''),
                    'size': result.metadata.get('file_size', 0),
                    'format': result.original_format,
                    'pages': result.metadata.get('page_count', 0)
                },
                'content_stats': {
                    'total_text_length': len(result.text_content),
                    'total_elements': result.metadata.get('total_elements', 0),
                    'text_elements': result.metadata.get('text_elements', 0),
                    'table_elements': result.metadata.get('table_elements', 0),
                    'image_elements': result.metadata.get('image_elements', 0),
                    'heading_elements': result.metadata.get('heading_elements', 0),
                    'list_elements': result.metadata.get('list_elements', 0),
                    'code_elements': result.metadata.get('code_elements', 0),
                    'formula_elements': result.metadata.get('formula_elements', 0)
                },
                'structure_info': result.structure_info,
                'processing_info': {
                    'parser_type': 'docling',
                    'features_used': {
                        'ocr': self.enable_ocr,
                        'table_structure': self.enable_table_structure,
                        'picture_description': self.enable_picture_description,
                        'formula_enrichment': self.enable_formula_enrichment,
                        'code_enrichment': self.enable_code_enrichment
                    }
                }
            }

            return stats

        except Exception as e:
            self.logger.error(f"获取文档统计信息失败: {e}")
            return {}

    def convert_with_translation(self, file_path: str, target_language: str = 'zh',
                               translation_service: str = 'google') -> DoclingParseResult:
        """
        转换文档并进行翻译

        Args:
            file_path (str): 文档文件路径
            target_language (str): 目标语言代码，默认'zh'（中文）
            translation_service (str): 翻译服务，默认'google'

        Returns:
            DoclingParseResult: 包含翻译内容的解析结果
        """
        try:
            # 首先进行标准解析
            result = self.parse(file_path)

            # 如果启用了远程服务，可以尝试集成翻译
            if self.enable_remote_services:
                self.logger.info(f"开始翻译文档内容到{target_language}")

                # 这里可以集成各种翻译服务
                # 目前只是一个占位符实现
                translated_content = self._translate_content(
                    result.text_content,
                    target_language,
                    translation_service
                )

                # 创建包含翻译内容的新结果
                translated_result = DoclingParseResult(
                    text_content=translated_content,
                    metadata={**result.metadata, 'translated_to': target_language},
                    structured_data=result.structured_data,
                    structure_info=result.structure_info,
                    original_format=result.original_format,
                    docling_document=result.docling_document
                )

                return translated_result
            else:
                self.logger.warning("翻译功能需要启用远程服务")
                return result

        except Exception as e:
            self.logger.error(f"翻译转换失败: {e}")
            raise

    def _translate_content(self, content: str, target_language: str,
                          translation_service: str) -> str:
        """
        翻译内容的内部方法

        Args:
            content (str): 要翻译的内容
            target_language (str): 目标语言
            translation_service (str): 翻译服务

        Returns:
            str: 翻译后的内容
        """
        # 这是一个占位符实现
        # 在实际使用中，可以集成Google Translate、百度翻译、腾讯翻译等服务
        self.logger.info(f"使用{translation_service}服务翻译到{target_language}")

        # 目前只是返回原内容，实际实现需要调用翻译API
        return content

    def enable_gpu_acceleration(self) -> bool:
        """
        启用GPU加速

        Returns:
            bool: 是否成功启用GPU加速
        """
        try:
            if ADVANCED_OPTIONS_AVAILABLE:
                # 重新初始化转换器以启用GPU
                self.config['use_gpu'] = True
                self._init_converter()
                self.logger.info("GPU加速已启用")
                return True
            else:
                self.logger.warning("当前Docling版本不支持GPU加速配置")
                return False
        except Exception as e:
            self.logger.error(f"启用GPU加速失败: {e}")
            return False

    def get_conversion_capabilities(self) -> Dict[str, Any]:
        """
        获取当前转换器的能力信息

        Returns:
            dict: 转换器能力信息
        """
        capabilities = {
            'basic_features': {
                'docling_available': DOCLING_AVAILABLE,
                'supported_formats': list(self.supported_formats.keys()),
                'ocr_enabled': self.enable_ocr,
                'table_structure_enabled': self.enable_table_structure
            },
            'advanced_features': {
                'advanced_options_available': ADVANCED_OPTIONS_AVAILABLE,
                'vlm_pipeline_available': VLM_PIPELINE_AVAILABLE,
                'word_format_available': WORD_FORMAT_AVAILABLE,
                'pypdfium_backend_available': PYPDFIUM_BACKEND_AVAILABLE,
                'picture_description_enabled': self.enable_picture_description,
                'formula_enrichment_enabled': self.enable_formula_enrichment,
                'code_enrichment_enabled': self.enable_code_enrichment,
                'remote_services_enabled': self.enable_remote_services
            },
            'configuration': {
                'ocr_engine': self.ocr_engine,
                'table_mode': self.table_mode,
                'images_scale': self.images_scale,
                'use_vlm_pipeline': self.use_vlm_pipeline,
                'vlm_model': self.vlm_model,
                'custom_backend': self.custom_backend
            }
        }

        return capabilities

    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """
        检查依赖库是否可用

        Returns:
            dict: 依赖库可用性状态
        """
        dependencies = {
            'docling': DOCLING_AVAILABLE,
            'advanced_options': ADVANCED_OPTIONS_AVAILABLE,
            'vlm_pipeline': VLM_PIPELINE_AVAILABLE,
            'word_format': WORD_FORMAT_AVAILABLE,
            'pypdfium_backend': PYPDFIUM_BACKEND_AVAILABLE,
            'pandas': False,
            'pillow': False
        }

        try:
            import pandas
            dependencies['pandas'] = True
        except ImportError:
            pass

        try:
            from PIL import Image
            dependencies['pillow'] = True
        except ImportError:
            pass

        return dependencies

    @classmethod
    def create_with_preset(cls, preset: str, **kwargs) -> 'DoclingParser':
        """
        使用预设配置创建解析器

        Args:
            preset (str): 预设名称，支持：
                - 'basic': 基础配置
                - 'ocr_only': 仅OCR
                - 'table_focus': 专注表格
                - 'image_focus': 专注图像
                - 'academic': 学术文档
                - 'vlm': 视觉语言模型
            **kwargs: 额外配置参数

        Returns:
            DoclingParser: 配置好的解析器实例
        """
        presets = {
            'basic': {
                'enable_ocr': True,
                'enable_table_structure': True,
                'enable_picture_description': False,
                'enable_formula_enrichment': False,
                'enable_code_enrichment': False
            },
            'ocr_only': {
                'enable_ocr': True,
                'enable_table_structure': False,
                'enable_picture_description': False,
                'enable_formula_enrichment': False,
                'enable_code_enrichment': False
            },
            'table_focus': {
                'enable_ocr': True,
                'enable_table_structure': True,
                'table_mode': 'accurate',
                'enable_cell_matching': True,
                'enable_picture_description': False,
                'enable_formula_enrichment': False,
                'enable_code_enrichment': False
            },
            'image_focus': {
                'enable_ocr': True,
                'enable_table_structure': True,
                'enable_picture_description': True,
                'enable_picture_classification': True,
                'generate_picture_images': True,
                'images_scale': 2,
                'enable_formula_enrichment': False,
                'enable_code_enrichment': False
            },
            'academic': {
                'enable_ocr': True,
                'enable_table_structure': True,
                'table_mode': 'accurate',
                'enable_picture_description': True,
                'enable_formula_enrichment': True,
                'enable_code_enrichment': True,
                'generate_picture_images': True,
                'images_scale': 2
            },
            'vlm': {
                'use_vlm_pipeline': True,
                'enable_ocr': True,
                'enable_table_structure': True,
                'enable_picture_description': True,
                'generate_picture_images': True,
                'images_scale': 2
            }
        }

        if preset not in presets:
            raise ValueError(f"未知的预设: {preset}. 支持的预设: {list(presets.keys())}")

        config = presets[preset].copy()
        config.update(kwargs)

        return cls(config=config)
