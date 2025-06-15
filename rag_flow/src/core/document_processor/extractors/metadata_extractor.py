"""
模块名称: metadata_extractor
功能描述: 元数据提取器，提供文档元数据的提取、标准化和增强功能
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import hashlib
import mimetypes
from dataclasses import dataclass


@dataclass
class StandardMetadata:
    """标准化元数据结构"""
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    description: str = ""
    creator: str = ""
    producer: str = ""
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    last_modified_by: str = ""
    version: str = ""
    language: str = ""
    category: str = ""
    comments: str = ""


class MetadataExtractor:
    """
    元数据提取器
    
    提供文档元数据的提取、标准化和增强功能，包括：
    - 文档基本信息提取
    - 文件系统元数据
    - 内容特征分析
    - 元数据标准化
    - 自定义字段扩展
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化元数据提取器
        
        Args:
            config (dict, optional): 配置参数
                - include_file_hash (bool): 是否计算文件哈希，默认False
                - hash_algorithm (str): 哈希算法，默认'md5'
                - extract_content_stats (bool): 是否提取内容统计，默认True
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.include_file_hash = self.config.get('include_file_hash', False)
        self.hash_algorithm = self.config.get('hash_algorithm', 'md5')
        self.extract_content_stats = self.config.get('extract_content_stats', True)
    
    def extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取文件系统元数据
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            dict: 文件元数据
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            stat = file_path.stat()
            
            metadata = {
                'file_name': file_path.name,
                'file_stem': file_path.stem,
                'file_extension': file_path.suffix.lower(),
                'file_size': stat.st_size,
                'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'accessed_time': datetime.fromtimestamp(stat.st_atime),
                'is_file': file_path.is_file(),
                'is_directory': file_path.is_dir(),
                'absolute_path': str(file_path.absolute()),
                'parent_directory': str(file_path.parent),
                'mime_type': mimetypes.guess_type(str(file_path))[0]
            }
            
            # 计算文件哈希
            if self.include_file_hash:
                metadata['file_hash'] = self._calculate_file_hash(file_path)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"文件元数据提取失败: {e}")
            return {}
    
    def standardize_metadata(self, raw_metadata: Dict[str, Any]) -> StandardMetadata:
        """
        标准化元数据格式
        
        Args:
            raw_metadata (dict): 原始元数据
            
        Returns:
            StandardMetadata: 标准化元数据对象
        """
        try:
            # 处理日期字段
            created_date = self._parse_date(raw_metadata.get('created') or 
                                          raw_metadata.get('creation_date') or
                                          raw_metadata.get('creationDate'))
            
            modified_date = self._parse_date(raw_metadata.get('modified') or 
                                           raw_metadata.get('modification_date') or
                                           raw_metadata.get('modDate'))
            
            return StandardMetadata(
                title=str(raw_metadata.get('title', '')).strip(),
                author=str(raw_metadata.get('author', '')).strip(),
                subject=str(raw_metadata.get('subject', '')).strip(),
                keywords=str(raw_metadata.get('keywords', '')).strip(),
                description=str(raw_metadata.get('description', '') or 
                            raw_metadata.get('comments', '')).strip(),
                creator=str(raw_metadata.get('creator', '')).strip(),
                producer=str(raw_metadata.get('producer', '')).strip(),
                created_date=created_date,
                modified_date=modified_date,
                last_modified_by=str(raw_metadata.get('last_modified_by', '') or
                                   raw_metadata.get('lastModifiedBy', '')).strip(),
                version=str(raw_metadata.get('version', '')).strip(),
                language=str(raw_metadata.get('language', '')).strip(),
                category=str(raw_metadata.get('category', '')).strip(),
                comments=str(raw_metadata.get('comments', '')).strip()
            )
            
        except Exception as e:
            self.logger.error(f"元数据标准化失败: {e}")
            return StandardMetadata()
    
    def extract_content_statistics(self, text_content: str) -> Dict[str, Any]:
        """
        提取内容统计信息
        
        Args:
            text_content (str): 文本内容
            
        Returns:
            dict: 内容统计信息
        """
        try:
            if not text_content:
                return {}
            
            # 基本统计
            char_count = len(text_content)
            char_count_no_spaces = len(text_content.replace(' ', ''))
            word_count = len(text_content.split())
            line_count = len(text_content.splitlines())
            paragraph_count = len([p for p in text_content.split('\n\n') if p.strip()])
            
            # 语言特征分析
            chinese_char_count = sum(1 for char in text_content if '\u4e00' <= char <= '\u9fff')
            english_word_count = sum(1 for word in text_content.split() 
                                   if word.isascii() and word.isalpha())
            
            # 计算语言比例
            chinese_ratio = chinese_char_count / char_count if char_count > 0 else 0
            english_ratio = english_word_count / word_count if word_count > 0 else 0
            
            # 推测主要语言
            primary_language = "unknown"
            if chinese_ratio > 0.3:
                primary_language = "chinese"
            elif english_ratio > 0.5:
                primary_language = "english"
            elif chinese_ratio > 0.1 and english_ratio > 0.2:
                primary_language = "mixed"
            
            statistics = {
                'character_count': char_count,
                'character_count_no_spaces': char_count_no_spaces,
                'word_count': word_count,
                'line_count': line_count,
                'paragraph_count': paragraph_count,
                'chinese_character_count': chinese_char_count,
                'english_word_count': english_word_count,
                'chinese_ratio': round(chinese_ratio, 3),
                'english_ratio': round(english_ratio, 3),
                'primary_language': primary_language,
                'average_word_length': round(char_count_no_spaces / word_count, 2) if word_count > 0 else 0,
                'average_sentence_length': round(word_count / line_count, 2) if line_count > 0 else 0
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"内容统计提取失败: {e}")
            return {}
    
    def enhance_metadata(self, base_metadata: Dict[str, Any], 
                        file_path: str, 
                        text_content: Optional[str] = None) -> Dict[str, Any]:
        """
        增强元数据信息
        
        Args:
            base_metadata (dict): 基础元数据
            file_path (str): 文件路径
            text_content (str, optional): 文本内容
            
        Returns:
            dict: 增强后的元数据
        """
        try:
            enhanced_metadata = base_metadata.copy()
            
            # 添加文件系统元数据
            file_metadata = self.extract_file_metadata(file_path)
            enhanced_metadata.update(file_metadata)
            
            # 标准化核心元数据
            standard_metadata = self.standardize_metadata(base_metadata)
            enhanced_metadata['standard'] = {
                'title': standard_metadata.title,
                'author': standard_metadata.author,
                'subject': standard_metadata.subject,
                'keywords': standard_metadata.keywords,
                'description': standard_metadata.description,
                'creator': standard_metadata.creator,
                'producer': standard_metadata.producer,
                'created_date': standard_metadata.created_date.isoformat() if standard_metadata.created_date else None,
                'modified_date': standard_metadata.modified_date.isoformat() if standard_metadata.modified_date else None,
                'last_modified_by': standard_metadata.last_modified_by,
                'version': standard_metadata.version,
                'language': standard_metadata.language,
                'category': standard_metadata.category,
                'comments': standard_metadata.comments
            }
            
            # 添加内容统计
            if text_content and self.extract_content_stats:
                content_stats = self.extract_content_statistics(text_content)
                enhanced_metadata['content_statistics'] = content_stats
            
            # 添加处理时间戳
            enhanced_metadata['processing_timestamp'] = datetime.now().isoformat()
            
            # 添加元数据质量评分
            enhanced_metadata['metadata_quality_score'] = self._calculate_metadata_quality(enhanced_metadata)
            
            return enhanced_metadata
            
        except Exception as e:
            self.logger.error(f"元数据增强失败: {e}")
            return base_metadata
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件哈希值
        """
        try:
            hash_func = hashlib.new(self.hash_algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            self.logger.error(f"文件哈希计算失败: {e}")
            return ""
    
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """
        解析日期值
        
        Args:
            date_value: 日期值（可能是字符串、datetime对象等）
            
        Returns:
            datetime: 解析后的日期对象，失败返回None
        """
        try:
            if date_value is None:
                return None
            
            if isinstance(date_value, datetime):
                return date_value
            
            if isinstance(date_value, str):
                # 尝试多种日期格式
                date_formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%Y/%m/%d %H:%M:%S',
                    '%Y/%m/%d',
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y',
                    '%d-%m-%Y %H:%M:%S',
                    '%d-%m-%Y'
                ]
                
                for fmt in date_formats:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
            
            return None
            
        except Exception as e:
            self.logger.warning(f"日期解析失败: {e}")
            return None
    
    def _calculate_metadata_quality(self, metadata: Dict[str, Any]) -> float:
        """
        计算元数据质量评分
        
        Args:
            metadata: 元数据字典
            
        Returns:
            float: 质量评分（0-1）
        """
        try:
            score = 0.0
            max_score = 0.0
            
            # 检查标准字段的完整性
            standard = metadata.get('standard', {})
            
            fields_weights = {
                'title': 0.2,
                'author': 0.15,
                'subject': 0.1,
                'keywords': 0.1,
                'description': 0.1,
                'created_date': 0.1,
                'modified_date': 0.05,
                'language': 0.05,
                'category': 0.05
            }
            
            for field, weight in fields_weights.items():
                max_score += weight
                value = standard.get(field)
                if value and str(value).strip():
                    score += weight
            
            # 检查内容统计的存在
            if metadata.get('content_statistics'):
                score += 0.1
            max_score += 0.1
            
            return round(score / max_score if max_score > 0 else 0, 3)
            
        except Exception as e:
            self.logger.error(f"元数据质量评分计算失败: {e}")
            return 0.0
