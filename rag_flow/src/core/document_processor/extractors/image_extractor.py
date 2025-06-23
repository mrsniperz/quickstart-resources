"""
模块名称: image_extractor
功能描述: 图像提取器，提供文档中图像的提取、分析和处理功能
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

from typing import Dict, List, Optional, Any, Tuple
import base64
import hashlib
from pathlib import Path
from dataclasses import dataclass

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)
import io


@dataclass
class ImageInfo:
    """图像信息数据类"""
    image_id: str
    page_number: Optional[int] = None
    bbox: Optional[Tuple[float, float, float, float]] = None  # (x, y, width, height)
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    size_bytes: Optional[int] = None
    dpi: Optional[Tuple[int, int]] = None
    color_mode: Optional[str] = None
    has_transparency: bool = False


@dataclass
class ProcessedImage:
    """处理后的图像数据类"""
    info: ImageInfo
    image_data: Optional[bytes] = None
    base64_data: Optional[str] = None
    thumbnail_data: Optional[bytes] = None
    extracted_text: Optional[str] = None
    metadata: Dict[str, Any] = None
    quality_score: float = 0.0


class ImageExtractor:
    """
    图像提取器
    
    提供文档中图像的提取、分析和处理功能，包括：
    - 图像数据提取
    - 图像信息分析
    - 图像格式转换
    - 缩略图生成
    - OCR文本提取（可选）
    - 图像质量评估
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化图像提取器
        
        Args:
            config (dict, optional): 配置参数
                - extract_image_data (bool): 是否提取图像数据，默认True
                - generate_thumbnails (bool): 是否生成缩略图，默认False
                - thumbnail_size (tuple): 缩略图尺寸，默认(150, 150)
                - extract_text_from_images (bool): 是否从图像提取文本，默认False
                - supported_formats (list): 支持的图像格式，默认['png', 'jpg', 'jpeg', 'gif', 'bmp']
        """
        self.config = config or {}
        self.logger = logger
        
        # 配置参数
        self.extract_image_data = self.config.get('extract_image_data', True)
        self.generate_thumbnails = self.config.get('generate_thumbnails', False)
        self.thumbnail_size = self.config.get('thumbnail_size', (150, 150))
        self.extract_text_from_images = self.config.get('extract_text_from_images', False)
        self.supported_formats = self.config.get('supported_formats', 
                                                ['png', 'jpg', 'jpeg', 'gif', 'bmp'])
        
        # 尝试导入可选依赖
        self.pil_available = self._check_pil_availability()
        self.ocr_available = self._check_ocr_availability()
    
    def process_image(self, image_data: bytes, 
                     image_info: Dict[str, Any],
                     page_number: Optional[int] = None) -> ProcessedImage:
        """
        处理图像数据
        
        Args:
            image_data (bytes): 图像二进制数据
            image_info (dict): 图像基本信息
            page_number (int, optional): 页面编号
            
        Returns:
            ProcessedImage: 处理后的图像对象
        """
        try:
            # 生成图像ID
            image_id = self._generate_image_id(image_data)
            
            # 创建图像信息对象
            info = ImageInfo(
                image_id=image_id,
                page_number=page_number,
                bbox=image_info.get('bbox'),
                width=image_info.get('width'),
                height=image_info.get('height'),
                format=image_info.get('ext', '').lower(),
                size_bytes=len(image_data)
            )
            
            # 分析图像详细信息
            if self.pil_available:
                self._analyze_image_with_pil(image_data, info)
            
            # 创建处理结果对象
            processed_image = ProcessedImage(
                info=info,
                metadata=self._generate_image_metadata(info, image_info)
            )
            
            # 提取图像数据
            if self.extract_image_data:
                processed_image.image_data = image_data
                processed_image.base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # 生成缩略图
            if self.generate_thumbnails and self.pil_available:
                processed_image.thumbnail_data = self._generate_thumbnail(image_data)
            
            # 提取图像中的文本
            if self.extract_text_from_images and self.ocr_available:
                processed_image.extracted_text = self._extract_text_from_image(image_data)
            
            # 计算质量评分
            processed_image.quality_score = self._calculate_image_quality(processed_image)
            
            return processed_image
            
        except Exception as e:
            self.logger.error(f"图像处理失败: {e}")
            # 返回基本的图像对象
            return ProcessedImage(
                info=ImageInfo(image_id=self._generate_image_id(image_data)),
                metadata={'error': str(e)}
            )
    
    def _generate_image_id(self, image_data: bytes) -> str:
        """
        生成图像唯一标识
        
        Args:
            image_data: 图像数据
            
        Returns:
            str: 图像ID
        """
        try:
            hash_obj = hashlib.md5(image_data)
            return f"img_{hash_obj.hexdigest()[:12]}"
        except Exception as e:
            self.logger.warning(f"图像ID生成失败: {e}")
            return f"img_unknown_{id(image_data)}"
    
    def _check_pil_availability(self) -> bool:
        """
        检查PIL/Pillow是否可用
        
        Returns:
            bool: 是否可用
        """
        try:
            from PIL import Image
            return True
        except ImportError:
            self.logger.warning("PIL/Pillow不可用，部分图像处理功能将被禁用")
            return False
    
    def _check_ocr_availability(self) -> bool:
        """
        检查OCR库是否可用
        
        Returns:
            bool: 是否可用
        """
        try:
            # 这里可以检查pytesseract或其他OCR库
            # import pytesseract
            # return True
            return False  # 暂时禁用OCR功能
        except ImportError:
            self.logger.warning("OCR库不可用，图像文本提取功能将被禁用")
            return False
    
    def _analyze_image_with_pil(self, image_data: bytes, info: ImageInfo) -> None:
        """
        使用PIL分析图像详细信息
        
        Args:
            image_data: 图像数据
            info: 图像信息对象（会被修改）
        """
        try:
            from PIL import Image
            
            with Image.open(io.BytesIO(image_data)) as img:
                # 更新基本信息
                info.width = img.width
                info.height = img.height
                info.format = img.format.lower() if img.format else None
                info.color_mode = img.mode
                info.has_transparency = img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                
                # 获取DPI信息
                if hasattr(img, 'info') and 'dpi' in img.info:
                    info.dpi = img.info['dpi']
                
        except Exception as e:
            self.logger.warning(f"PIL图像分析失败: {e}")
    
    def _generate_thumbnail(self, image_data: bytes) -> Optional[bytes]:
        """
        生成缩略图
        
        Args:
            image_data: 原始图像数据
            
        Returns:
            bytes: 缩略图数据，失败返回None
        """
        try:
            from PIL import Image
            
            with Image.open(io.BytesIO(image_data)) as img:
                # 创建缩略图
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # 转换为字节数据
                thumbnail_io = io.BytesIO()
                img.save(thumbnail_io, format='PNG')
                return thumbnail_io.getvalue()
                
        except Exception as e:
            self.logger.warning(f"缩略图生成失败: {e}")
            return None
    
    def _extract_text_from_image(self, image_data: bytes) -> Optional[str]:
        """
        从图像中提取文本（OCR）
        
        Args:
            image_data: 图像数据
            
        Returns:
            str: 提取的文本，失败返回None
        """
        try:
            # 这里应该实现OCR功能
            # 例如使用pytesseract:
            # import pytesseract
            # from PIL import Image
            # 
            # with Image.open(io.BytesIO(image_data)) as img:
            #     text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            #     return text.strip()
            
            # 暂时返回None
            return None
            
        except Exception as e:
            self.logger.warning(f"图像文本提取失败: {e}")
            return None
    
    def _generate_image_metadata(self, info: ImageInfo, 
                               original_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成图像元数据
        
        Args:
            info: 图像信息对象
            original_info: 原始图像信息
            
        Returns:
            dict: 图像元数据
        """
        try:
            metadata = {
                'image_id': info.image_id,
                'dimensions': {
                    'width': info.width,
                    'height': info.height,
                    'aspect_ratio': info.width / info.height if info.width and info.height else None
                },
                'file_info': {
                    'format': info.format,
                    'size_bytes': info.size_bytes,
                    'size_mb': round(info.size_bytes / (1024 * 1024), 3) if info.size_bytes else None
                },
                'color_info': {
                    'mode': info.color_mode,
                    'has_transparency': info.has_transparency
                },
                'location_info': {
                    'page_number': info.page_number,
                    'bbox': info.bbox
                },
                'processing_info': {
                    'extraction_method': 'document_parser',
                    'pil_analysis': self.pil_available,
                    'ocr_attempted': self.extract_text_from_images and self.ocr_available
                }
            }
            
            # 添加DPI信息
            if info.dpi:
                metadata['resolution'] = {
                    'dpi_x': info.dpi[0],
                    'dpi_y': info.dpi[1]
                }
            
            # 添加原始信息
            metadata['original_info'] = original_info
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"图像元数据生成失败: {e}")
            return {'error': str(e)}
    
    def _calculate_image_quality(self, processed_image: ProcessedImage) -> float:
        """
        计算图像质量评分
        
        Args:
            processed_image: 处理后的图像对象
            
        Returns:
            float: 质量评分（0-1）
        """
        try:
            score = 0.0
            info = processed_image.info
            
            # 分辨率评分（40%）
            if info.width and info.height:
                pixel_count = info.width * info.height
                # 基于像素数量评分，100万像素为满分
                resolution_score = min(1.0, pixel_count / 1000000)
                score += resolution_score * 0.4
            
            # 文件大小评分（20%）
            if info.size_bytes:
                # 合理的文件大小范围：10KB - 5MB
                if 10000 <= info.size_bytes <= 5000000:
                    size_score = 1.0
                elif info.size_bytes < 10000:
                    size_score = info.size_bytes / 10000
                else:
                    size_score = max(0.5, 5000000 / info.size_bytes)
                score += size_score * 0.2
            
            # 格式评分（20%）
            format_scores = {
                'png': 1.0,
                'jpg': 0.9,
                'jpeg': 0.9,
                'gif': 0.7,
                'bmp': 0.6
            }
            format_score = format_scores.get(info.format, 0.5)
            score += format_score * 0.2
            
            # 完整性评分（20%）
            completeness_score = 1.0
            if not processed_image.image_data:
                completeness_score -= 0.5
            if processed_image.metadata.get('error'):
                completeness_score -= 0.3
            score += max(0, completeness_score) * 0.2
            
            return round(score, 3)
            
        except Exception as e:
            self.logger.error(f"图像质量评分计算失败: {e}")
            return 0.0
    
    def is_supported_format(self, format_name: str) -> bool:
        """
        检查图像格式是否支持
        
        Args:
            format_name: 格式名称
            
        Returns:
            bool: 是否支持
        """
        return format_name.lower() in self.supported_formats
    
    def get_image_summary(self, processed_images: List[ProcessedImage]) -> Dict[str, Any]:
        """
        获取图像集合的摘要信息
        
        Args:
            processed_images: 处理后的图像列表
            
        Returns:
            dict: 摘要信息
        """
        try:
            if not processed_images:
                return {}
            
            total_images = len(processed_images)
            total_size = sum(img.info.size_bytes or 0 for img in processed_images)
            
            # 格式分布
            format_counts = {}
            for img in processed_images:
                fmt = img.info.format or 'unknown'
                format_counts[fmt] = format_counts.get(fmt, 0) + 1
            
            # 尺寸统计
            widths = [img.info.width for img in processed_images if img.info.width]
            heights = [img.info.height for img in processed_images if img.info.height]
            
            # 质量统计
            quality_scores = [img.quality_score for img in processed_images]
            
            summary = {
                'total_images': total_images,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'format_distribution': format_counts,
                'size_statistics': {
                    'avg_width': round(sum(widths) / len(widths), 1) if widths else None,
                    'avg_height': round(sum(heights) / len(heights), 1) if heights else None,
                    'max_width': max(widths) if widths else None,
                    'max_height': max(heights) if heights else None,
                    'min_width': min(widths) if widths else None,
                    'min_height': min(heights) if heights else None
                },
                'quality_statistics': {
                    'avg_quality': round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else 0,
                    'max_quality': max(quality_scores) if quality_scores else 0,
                    'min_quality': min(quality_scores) if quality_scores else 0
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"图像摘要生成失败: {e}")
            return {'error': str(e)}
