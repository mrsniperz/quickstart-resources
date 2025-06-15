"""
模块名称: pdf_parser
功能描述: PDF文档解析器，基于PyMuPDF实现PDF文档的文本提取、表格识别、图像提取和元数据解析
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import pymupdf
from dataclasses import dataclass

from ..extractors.metadata_extractor import MetadataExtractor
from ..extractors.table_extractor import TableExtractor
from ..extractors.image_extractor import ImageExtractor


@dataclass
class PDFParseResult:
    """PDF解析结果数据类"""
    text_content: str
    metadata: Dict[str, Any]
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    page_count: int
    structure_info: Dict[str, Any]


class PDFParser:
    """
    PDF文档处理器
    
    基于PyMuPDF实现PDF文档的全面解析，包括：
    - 文本内容提取
    - 表格结构识别
    - 图像内容提取
    - 文档结构分析
    - 元数据自动提取
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化PDF解析器
        
        Args:
            config (dict, optional): 配置参数
                - extract_images (bool): 是否提取图像，默认True
                - extract_tables (bool): 是否提取表格，默认True
                - preserve_layout (bool): 是否保持布局，默认True
                - ocr_enabled (bool): 是否启用OCR，默认False
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化提取器
        self.metadata_extractor = MetadataExtractor()
        self.table_extractor = TableExtractor()
        self.image_extractor = ImageExtractor()
        
        # 配置参数
        self.extract_images = self.config.get('extract_images', True)
        self.extract_tables = self.config.get('extract_tables', True)
        self.preserve_layout = self.config.get('preserve_layout', True)
        self.ocr_enabled = self.config.get('ocr_enabled', False)
        
    def parse(self, file_path: str) -> PDFParseResult:
        """
        解析PDF文档
        
        Args:
            file_path (str): PDF文件路径
            
        Returns:
            PDFParseResult: 解析结果
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
            Exception: 解析过程中的其他错误
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"PDF文件不存在: {file_path}")
                
            if file_path.suffix.lower() != '.pdf':
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
                
            self.logger.info(f"开始解析PDF文档: {file_path}")
            
            with pymupdf.open(str(file_path)) as doc:
                # 提取基本信息
                page_count = len(doc)
                metadata = self._extract_metadata(doc)
                
                # 提取文本内容
                text_content = self._extract_text(doc)
                
                # 提取表格
                tables = []
                if self.extract_tables:
                    tables = self._extract_tables(doc)
                
                # 提取图像
                images = []
                if self.extract_images:
                    images = self._extract_images(doc)
                
                # 分析文档结构
                structure_info = self._analyze_structure(doc)
                
                result = PDFParseResult(
                    text_content=text_content,
                    metadata=metadata,
                    tables=tables,
                    images=images,
                    page_count=page_count,
                    structure_info=structure_info
                )
                
                self.logger.info(f"PDF解析完成: {page_count}页, {len(tables)}个表格, {len(images)}个图像")
                return result
                
        except Exception as e:
            self.logger.error(f"PDF解析失败: {e}")
            raise
    
    def _extract_text(self, doc: pymupdf.Document) -> str:
        """
        提取文档文本内容
        
        Args:
            doc: PyMuPDF文档对象
            
        Returns:
            str: 提取的文本内容
        """
        try:
            text_parts = []
            
            for page_num, page in enumerate(doc):
                if self.ocr_enabled:
                    # 使用OCR提取文本
                    tp = page.get_textpage_ocr()
                    page_text = page.get_text(textpage=tp)
                else:
                    # 直接提取文本
                    if self.preserve_layout:
                        page_text = page.get_text("text")
                    else:
                        page_text = page.get_text("text", flags=pymupdf.TEXT_INHIBIT_SPACES)
                
                if page_text.strip():
                    text_parts.append(f"=== 第{page_num + 1}页 ===\n{page_text}")
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            self.logger.error(f"文本提取失败: {e}")
            return ""
    
    def _extract_metadata(self, doc: pymupdf.Document) -> Dict[str, Any]:
        """
        提取文档元数据
        
        Args:
            doc: PyMuPDF文档对象
            
        Returns:
            dict: 元数据信息
        """
        try:
            metadata = doc.metadata or {}
            
            # 添加文档基本信息
            metadata.update({
                'page_count': len(doc),
                'is_encrypted': doc.needs_pass,
                'is_pdf': True,
                'file_size': None,  # 需要从文件路径获取
                'creation_date': metadata.get('creationDate'),
                'modification_date': metadata.get('modDate'),
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'keywords': metadata.get('keywords', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
            })
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"元数据提取失败: {e}")
            return {}
    
    def _extract_tables(self, doc: pymupdf.Document) -> List[Dict[str, Any]]:
        """
        提取文档中的表格
        
        Args:
            doc: PyMuPDF文档对象
            
        Returns:
            list: 表格数据列表
        """
        try:
            all_tables = []
            
            for page_num, page in enumerate(doc):
                # 查找页面中的表格
                tabs = page.find_tables()
                
                for table_idx, table in enumerate(tabs.tables):
                    try:
                        # 提取表格数据
                        table_data = table.extract()
                        
                        if table_data:
                            table_info = {
                                'page_number': page_num + 1,
                                'table_index': table_idx,
                                'data': table_data,
                                'bbox': table.bbox,  # 表格边界框
                                'rows': len(table_data),
                                'columns': len(table_data[0]) if table_data else 0
                            }
                            all_tables.append(table_info)
                            
                    except Exception as e:
                        self.logger.warning(f"第{page_num + 1}页表格{table_idx}提取失败: {e}")
                        continue
            
            return all_tables
            
        except Exception as e:
            self.logger.error(f"表格提取失败: {e}")
            return []
    
    def _extract_images(self, doc: pymupdf.Document) -> List[Dict[str, Any]]:
        """
        提取文档中的图像
        
        Args:
            doc: PyMuPDF文档对象
            
        Returns:
            list: 图像信息列表
        """
        try:
            all_images = []
            
            for page_num, page in enumerate(doc):
                # 获取页面中的图像块
                image_blocks = page.get_text("dict", flags=pymupdf.TEXTFLAGS_DICT)["blocks"]
                
                for block in image_blocks:
                    if block.get("type") == 1:  # 图像块
                        try:
                            image_info = {
                                'page_number': page_num + 1,
                                'bbox': block.get("bbox"),
                                'width': block.get("width"),
                                'height': block.get("height"),
                                'ext': block.get("ext"),
                                'size': block.get("size"),
                                'image_data': block.get("image")  # 二进制图像数据
                            }
                            all_images.append(image_info)
                            
                        except Exception as e:
                            self.logger.warning(f"第{page_num + 1}页图像提取失败: {e}")
                            continue
            
            return all_images
            
        except Exception as e:
            self.logger.error(f"图像提取失败: {e}")
            return []
    
    def _analyze_structure(self, doc: pymupdf.Document) -> Dict[str, Any]:
        """
        分析文档结构
        
        Args:
            doc: PyMuPDF文档对象
            
        Returns:
            dict: 结构分析信息
        """
        try:
            structure = {
                'has_toc': False,
                'toc_items': [],
                'page_sizes': [],
                'text_blocks_per_page': [],
                'font_info': {}
            }
            
            # 检查目录
            toc = doc.get_toc()
            if toc:
                structure['has_toc'] = True
                structure['toc_items'] = toc
            
            # 分析每页结构
            for page in doc:
                # 页面尺寸
                structure['page_sizes'].append({
                    'width': page.rect.width,
                    'height': page.rect.height
                })
                
                # 文本块数量
                blocks = page.get_text("dict")["blocks"]
                text_blocks = [b for b in blocks if b.get("type") == 0]
                structure['text_blocks_per_page'].append(len(text_blocks))
            
            return structure
            
        except Exception as e:
            self.logger.error(f"结构分析失败: {e}")
            return {}
    
    def extract_page_text(self, file_path: str, page_num: int) -> str:
        """
        提取指定页面的文本
        
        Args:
            file_path (str): PDF文件路径
            page_num (int): 页面编号（从0开始）
            
        Returns:
            str: 页面文本内容
            
        Raises:
            IndexError: 页面编号超出范围
        """
        try:
            with pymupdf.open(file_path) as doc:
                if page_num >= len(doc):
                    raise IndexError(f"页面编号超出范围: {page_num} >= {len(doc)}")
                
                page = doc[page_num]
                return page.get_text()
                
        except Exception as e:
            self.logger.error(f"页面文本提取失败: {e}")
            raise
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式
        
        Returns:
            list: 支持的文件扩展名列表
        """
        return ['.pdf']
