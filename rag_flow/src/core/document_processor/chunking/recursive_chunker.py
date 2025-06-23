"""
模块名称: recursive_chunker
功能描述: 递归字符分块器，基于多层级分隔符进行递归分割，类似LangChain的RecursiveCharacterTextSplitter
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)

from .chunking_engine import ChunkingStrategy, TextChunk, ChunkMetadata, ChunkType
from ..config.config_manager import get_config_manager


class RecursiveCharacterChunker(ChunkingStrategy):
    """
    递归字符分块器
    
    基于多层级分隔符进行递归分割，包括：
    - 多层级分隔符匹配（段落 -> 句子 -> 单词 -> 字符）
    - 正则表达式匹配模式支持
    - 可配置的分割优先级和回退机制
    - 智能重叠内容处理
    - 分块大小自适应调整
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化递归字符分块器

        Args:
            config (dict, optional): 配置参数
                - chunk_size (int): 目标分块大小，默认从配置文件读取
                - chunk_overlap (int): 分块重叠大小，默认从配置文件读取
                - separators (list): 分隔符列表，默认从配置文件读取
                - is_separator_regex (bool): 分隔符是否为正则表达式，默认从配置文件读取
                - keep_separator (bool): 是否保留分隔符，默认从配置文件读取
                - add_start_index (bool): 是否添加起始索引，默认从配置文件读取
                - strip_whitespace (bool): 是否去除空白字符，默认从配置文件读取
        """
        self.logger = logger

        # 获取配置管理器和默认配置
        try:
            config_manager = get_config_manager()
            default_config = config_manager.get_chunking_config('recursive')
        except Exception as e:
            self.logger.warning(f"无法加载配置文件，使用硬编码默认配置: {e}")
            default_config = self._get_fallback_config()

        # 合并用户配置和默认配置
        self.config = default_config.copy()
        if config:
            self.config.update(config)

        # 配置参数
        self.chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)
        self.is_separator_regex = self.config.get('is_separator_regex', False)
        self.keep_separator = self.config.get('keep_separator', True)
        self.add_start_index = self.config.get('add_start_index', False)
        self.strip_whitespace = self.config.get('strip_whitespace', True)

        # 分隔符列表（优先使用配置文件，然后是用户配置，最后是硬编码默认值）
        self.separators = self.config.get('separators', self._get_default_separators())

        # 验证配置
        self._validate_config()
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "recursive"

    def _get_fallback_config(self) -> Dict[str, Any]:
        """
        获取回退配置（当配置文件不可用时使用）

        Returns:
            dict: 回退配置
        """
        return {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'is_separator_regex': False,
            'keep_separator': True,
            'add_start_index': False,
            'strip_whitespace': True,
            'separators': self._get_default_separators()
        }
    
    def _get_default_separators(self) -> List[str]:
        """
        获取默认分隔符列表（回退方案）

        注意：此方法主要用作配置文件不可用时的回退方案。
        正常情况下应该从配置文件中读取分隔符列表。

        Returns:
            list: 分隔符列表，按优先级从高到低排序
        """
        return [
            # 段落分隔符
            "\n\n",
            "\n\n\n",
            
            # 中文段落标记
            "\n第",
            "\n章",
            "\n节",
            "\n条",
            
            # 英文段落标记
            "\nChapter",
            "\nSection",
            "\nArticle",
            
            # 列表和编号
            "\n\n•",
            "\n\n-",
            "\n\n*",
            "\n\n1.",
            "\n\n2.",
            "\n\n3.",
            
            # 单行分隔符
            "\n",
            
            # 句子分隔符
            "。",
            "！",
            "？",
            ".",
            "!",
            "?",
            
            # 子句分隔符
            "；",
            ";",
            "，",
            ",",
            
            # 词语分隔符
            " ",
            "\t",
            
            # 中文标点
            "、",
            "：",
            ":",
            
            # 零宽字符（用于无明显分词边界的语言）
            "\u200b",  # 零宽空格
            "\uff0c",  # 全角逗号
            "\u3001",  # 中文顿号
            "\uff0e",  # 全角句号
            "\u3002",  # 中文句号
            
            # 最后的回退选项
            ""
        ]
    
    def _validate_config(self) -> None:
        """验证配置参数"""
        try:
            if self.chunk_size <= 0:
                raise ValueError("chunk_size必须大于0")
            
            if self.chunk_overlap < 0:
                raise ValueError("chunk_overlap不能为负数")
            
            if self.chunk_overlap >= self.chunk_size:
                self.logger.warning("chunk_overlap大于等于chunk_size，将调整为chunk_size的一半")
                self.chunk_overlap = self.chunk_size // 2
            
            if not isinstance(self.separators, list) or not self.separators:
                raise ValueError("separators必须是非空列表")
                
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            raise
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        递归分块文本内容
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
            
        Returns:
            list: 分块结果列表
        """
        try:
            if not text or not text.strip():
                return []
            
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 执行递归分块
            chunks = self._recursive_split(processed_text)
            
            # 创建TextChunk对象
            text_chunks = self._create_text_chunks(chunks, metadata, processed_text)
            
            return text_chunks
            
        except Exception as e:
            self.logger.error(f"递归分块失败: {e}")
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
            if self.strip_whitespace:
                # 标准化换行符
                text = re.sub(r'\r\n|\r', '\n', text)
                
                # 移除行尾空格
                text = re.sub(r'[ \t]+\n', '\n', text)
                
                # 标准化多个空行
                text = re.sub(r'\n{3,}', '\n\n', text)
                
                # 移除首尾空白
                text = text.strip()
            
            return text
            
        except Exception as e:
            self.logger.warning(f"文本预处理失败: {e}")
            return text
    
    def _recursive_split(self, text: str) -> List[str]:
        """
        递归分割文本
        
        Args:
            text: 待分割的文本
            
        Returns:
            list: 分割后的文本块列表
        """
        try:
            return self._split_text_with_separators(text, self.separators)
            
        except Exception as e:
            self.logger.error(f"递归分割失败: {e}")
            return [text]
    
    def _split_text_with_separators(self, text: str, separators: List[str]) -> List[str]:
        """
        使用分隔符列表分割文本
        
        Args:
            text: 待分割的文本
            separators: 分隔符列表
            
        Returns:
            list: 分割后的文本块列表
        """
        try:
            final_chunks = []
            
            # 如果没有分隔符，直接返回
            if not separators:
                return [text]
            
            # 使用第一个分隔符分割
            separator = separators[0]
            remaining_separators = separators[1:]
            
            # 分割文本
            if separator == "":
                # 空分隔符表示按字符分割
                splits = list(text)
            else:
                splits = self._split_by_separator(text, separator)
            
            # 处理每个分割片段
            good_splits = []
            for split in splits:
                if self._length_function(split) < self.chunk_size:
                    good_splits.append(split)
                else:
                    # 如果片段太大，继续递归分割
                    if remaining_separators:
                        sub_splits = self._split_text_with_separators(split, remaining_separators)
                        good_splits.extend(sub_splits)
                    else:
                        # 没有更多分隔符，强制分割
                        good_splits.extend(self._force_split_text(split))
            
            # 合并小片段
            final_chunks = self._merge_splits(good_splits, separator)
            
            return final_chunks
            
        except Exception as e:
            self.logger.error(f"分隔符分割失败: {e}")
            return [text]
    
    def _split_by_separator(self, text: str, separator: str) -> List[str]:
        """
        使用指定分隔符分割文本
        
        Args:
            text: 待分割的文本
            separator: 分隔符
            
        Returns:
            list: 分割后的文本片段列表
        """
        try:
            if self.is_separator_regex:
                # 使用正则表达式分割
                if self.keep_separator:
                    # 保留分隔符
                    splits = re.split(f'({separator})', text)
                    # 重新组合，保留分隔符
                    result = []
                    for i in range(0, len(splits), 2):
                        if i + 1 < len(splits):
                            result.append(splits[i] + splits[i + 1])
                        else:
                            result.append(splits[i])
                    return [s for s in result if s.strip()]
                else:
                    return [s for s in re.split(separator, text) if s.strip()]
            else:
                # 普通字符串分割
                if self.keep_separator:
                    splits = text.split(separator)
                    if len(splits) > 1:
                        # 将分隔符添加回去（除了最后一个）
                        result = []
                        for i, split in enumerate(splits[:-1]):
                            result.append(split + separator)
                        result.append(splits[-1])
                        return [s for s in result if s.strip()]
                    else:
                        return splits
                else:
                    return [s for s in text.split(separator) if s.strip()]
                    
        except Exception as e:
            self.logger.warning(f"分隔符分割失败: {e}")
            return [text]
    
    def _force_split_text(self, text: str) -> List[str]:
        """
        强制分割过长的文本
        
        Args:
            text: 待分割的文本
            
        Returns:
            list: 分割后的文本片段列表
        """
        try:
            chunks = []
            start = 0
            text_length = len(text)
            
            while start < text_length:
                end = start + self.chunk_size
                if end >= text_length:
                    chunks.append(text[start:])
                    break
                else:
                    chunks.append(text[start:end])
                    start = end - self.chunk_overlap
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"强制分割失败: {e}")
            return [text]
    
    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """
        合并小的分割片段
        
        Args:
            splits: 分割片段列表
            separator: 使用的分隔符
            
        Returns:
            list: 合并后的分块列表
        """
        try:
            if not splits:
                return []
            
            merged_chunks = []
            current_chunk = ""
            
            for split in splits:
                split = split.strip()
                if not split:
                    continue
                
                # 计算合并后的长度
                potential_chunk = current_chunk
                if potential_chunk:
                    if separator and separator != "":
                        potential_chunk += separator + split
                    else:
                        potential_chunk += split
                else:
                    potential_chunk = split
                
                # 检查是否超过大小限制
                if self._length_function(potential_chunk) <= self.chunk_size:
                    current_chunk = potential_chunk
                else:
                    # 保存当前分块，开始新分块
                    if current_chunk:
                        merged_chunks.append(current_chunk)
                    current_chunk = split
            
            # 添加最后一个分块
            if current_chunk:
                merged_chunks.append(current_chunk)
            
            return merged_chunks
            
        except Exception as e:
            self.logger.error(f"分块合并失败: {e}")
            return splits
    
    def _length_function(self, text: str) -> int:
        """
        计算文本长度
        
        Args:
            text: 文本内容
            
        Returns:
            int: 文本长度
        """
        return len(text)
    
    def _create_text_chunks(self, chunks: List[str], metadata: Dict[str, Any], 
                           original_text: str) -> List[TextChunk]:
        """
        创建TextChunk对象列表
        
        Args:
            chunks: 文本分块列表
            metadata: 文档元数据
            original_text: 原始文本
            
        Returns:
            list: TextChunk对象列表
        """
        try:
            text_chunks = []
            current_position = 0
            
            for i, chunk_content in enumerate(chunks):
                if not chunk_content.strip():
                    continue
                
                # 计算在原文中的位置
                start_index = 0
                if self.add_start_index:
                    start_index = original_text.find(chunk_content, current_position)
                    if start_index == -1:
                        start_index = current_position
                    current_position = start_index + len(chunk_content)
                
                # 创建分块元数据
                chunk_metadata = ChunkMetadata(
                    chunk_id=f"recursive_{i:04d}",
                    chunk_type=ChunkType.PARAGRAPH,
                    source_document=metadata.get('file_path', ''),
                    start_position=start_index if self.add_start_index else None,
                    end_position=start_index + len(chunk_content) if self.add_start_index else None,
                    processing_timestamp=datetime.now().isoformat()
                )
                
                # 创建TextChunk对象
                text_chunk = TextChunk(
                    content=chunk_content,
                    metadata=chunk_metadata,
                    word_count=len(chunk_content.split()),
                    character_count=len(chunk_content)
                )
                
                # 添加重叠内容
                if i > 0 and self.chunk_overlap > 0:
                    text_chunk.overlap_content = self._generate_overlap_content(
                        text_chunks, chunk_content
                    )
                
                text_chunks.append(text_chunk)
            
            return text_chunks
            
        except Exception as e:
            self.logger.error(f"TextChunk对象创建失败: {e}")
            return []
    
    def _generate_overlap_content(self, previous_chunks: List[TextChunk], 
                                current_content: str) -> str:
        """
        生成重叠内容
        
        Args:
            previous_chunks: 之前的分块列表
            current_content: 当前分块内容
            
        Returns:
            str: 重叠内容
        """
        try:
            if not previous_chunks:
                return ""
            
            prev_chunk = previous_chunks[-1]
            prev_content = prev_chunk.content
            
            # 取前一个分块的末尾部分作为重叠
            overlap_length = min(self.chunk_overlap, len(prev_content))
            overlap_content = prev_content[-overlap_length:]
            
            return overlap_content
            
        except Exception as e:
            self.logger.warning(f"重叠内容生成失败: {e}")
            return ""
