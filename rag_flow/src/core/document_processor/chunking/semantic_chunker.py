"""
模块名称: semantic_chunker
功能描述: 语义分块器，基于语义相似度和内容连贯性进行智能分块
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .chunking_engine import ChunkingStrategy, TextChunk, ChunkMetadata, ChunkType


class SemanticChunker(ChunkingStrategy):
    """
    语义分块器
    
    基于语义相似度和内容连贯性进行智能分块，包括：
    - 句子边界检测
    - 语义相似度计算
    - 主题转换检测
    - 段落完整性保持
    - 上下文连贯性分析
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化语义分块器
        
        Args:
            config (dict, optional): 配置参数
                - target_chunk_size (int): 目标分块大小，默认800
                - min_chunk_size (int): 最小分块大小，默认200
                - max_chunk_size (int): 最大分块大小，默认1500
                - similarity_threshold (float): 语义相似度阈值，默认0.7
                - sentence_overlap (int): 句子重叠数量，默认1
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.target_chunk_size = self.config.get('target_chunk_size', 800)
        self.min_chunk_size = self.config.get('min_chunk_size', 200)
        self.max_chunk_size = self.config.get('max_chunk_size', 1500)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        self.sentence_overlap = self.config.get('sentence_overlap', 1)
        
        # 句子分割模式
        self.sentence_patterns = [
            r'[.!?。！？]+\s+',  # 英文和中文句号、感叹号、问号
            r'[.!?。！？]+$',     # 行末的标点
            r'[.!?。！？]+\n',    # 换行前的标点
        ]
        
        # 段落分割模式
        self.paragraph_patterns = [
            r'\n\s*\n',          # 空行分割
            r'\n\s*[0-9]+\.',    # 编号段落
            r'\n\s*[一二三四五六七八九十]+[、.]',  # 中文编号
            r'\n\s*[A-Z]\.',     # 字母编号
        ]
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "semantic"
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        基于语义进行文本分块
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
            
        Returns:
            list: 分块结果列表
        """
        try:
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 分割句子
            sentences = self._split_sentences(processed_text)
            
            if not sentences:
                return []
            
            # 分析句子语义
            sentence_features = self._analyze_sentences(sentences)
            
            # 基于语义相似度分块
            chunks = self._semantic_chunking(sentences, sentence_features, metadata)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"语义分块失败: {e}")
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
            
            # 处理特殊字符
            text = re.sub(r'[""\'\'""\'\'„"‚"]', '"', text)
            text = re.sub(r'[–—]', '-', text)
            
            # 标准化空格
            text = re.sub(r'[ \t]+', ' ', text)
            
            # 移除过多的空行，但保留段落分隔
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            
            return text.strip()
            
        except Exception as e:
            self.logger.warning(f"文本预处理失败: {e}")
            return text
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        分割句子
        
        Args:
            text: 文本内容
            
        Returns:
            list: 句子列表
        """
        try:
            sentences = []
            
            # 首先按段落分割
            paragraphs = re.split(r'\n\s*\n', text)
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # 在段落内分割句子
                para_sentences = self._split_paragraph_sentences(paragraph)
                sentences.extend(para_sentences)
            
            # 过滤空句子和过短句子
            filtered_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:  # 过滤过短的句子
                    filtered_sentences.append(sentence)
            
            return filtered_sentences
            
        except Exception as e:
            self.logger.error(f"句子分割失败: {e}")
            return [text]
    
    def _split_paragraph_sentences(self, paragraph: str) -> List[str]:
        """
        分割段落中的句子
        
        Args:
            paragraph: 段落文本
            
        Returns:
            list: 句子列表
        """
        try:
            sentences = []
            current_sentence = ""
            
            # 使用正则表达式分割句子
            for pattern in self.sentence_patterns:
                parts = re.split(pattern, paragraph)
                if len(parts) > 1:
                    # 找到了句子分割点
                    for i, part in enumerate(parts[:-1]):
                        if part.strip():
                            sentences.append(part.strip())
                    
                    # 处理最后一部分
                    if parts[-1].strip():
                        sentences.append(parts[-1].strip())
                    
                    return sentences
            
            # 如果没有找到明确的句子分割点，尝试其他方法
            # 按长度分割
            if len(paragraph) > self.max_chunk_size:
                words = paragraph.split()
                chunk_words = []
                
                for word in words:
                    chunk_words.append(word)
                    current_length = len(' '.join(chunk_words))
                    
                    if current_length >= self.target_chunk_size:
                        sentences.append(' '.join(chunk_words))
                        chunk_words = []
                
                if chunk_words:
                    sentences.append(' '.join(chunk_words))
            else:
                sentences.append(paragraph)
            
            return sentences
            
        except Exception as e:
            self.logger.warning(f"段落句子分割失败: {e}")
            return [paragraph]
    
    def _analyze_sentences(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """
        分析句子特征
        
        Args:
            sentences: 句子列表
            
        Returns:
            list: 句子特征列表
        """
        try:
            features = []
            
            for i, sentence in enumerate(sentences):
                feature = {
                    'index': i,
                    'length': len(sentence),
                    'word_count': len(sentence.split()),
                    'has_numbers': bool(re.search(r'\d+', sentence)),
                    'has_punctuation': bool(re.search(r'[.!?。！？]', sentence)),
                    'starts_with_capital': sentence[0].isupper() if sentence else False,
                    'contains_keywords': self._extract_keywords(sentence),
                    'sentence_type': self._classify_sentence_type(sentence),
                    'topic_indicators': self._extract_topic_indicators(sentence)
                }
                
                features.append(feature)
            
            return features
            
        except Exception as e:
            self.logger.error(f"句子特征分析失败: {e}")
            return [{'index': i, 'length': len(s)} for i, s in enumerate(sentences)]
    
    def _extract_keywords(self, sentence: str) -> List[str]:
        """
        提取句子关键词
        
        Args:
            sentence: 句子文本
            
        Returns:
            list: 关键词列表
        """
        try:
            # 简单的关键词提取（可以后续优化为更复杂的NLP方法）
            keywords = []
            
            # 航空相关关键词
            aviation_keywords = [
                '飞机', '航空', '发动机', '机翼', '起飞', '降落', '维修', '检查',
                'aircraft', 'aviation', 'engine', 'wing', 'takeoff', 'landing', 'maintenance'
            ]
            
            sentence_lower = sentence.lower()
            for keyword in aviation_keywords:
                if keyword in sentence_lower:
                    keywords.append(keyword)
            
            # 提取数字和专业术语
            numbers = re.findall(r'\d+(?:\.\d+)?', sentence)
            keywords.extend(numbers)
            
            # 提取大写词汇（可能是专业术语）
            uppercase_words = re.findall(r'\b[A-Z]{2,}\b', sentence)
            keywords.extend(uppercase_words)
            
            return keywords
            
        except Exception as e:
            self.logger.warning(f"关键词提取失败: {e}")
            return []
    
    def _classify_sentence_type(self, sentence: str) -> str:
        """
        分类句子类型
        
        Args:
            sentence: 句子文本
            
        Returns:
            str: 句子类型
        """
        try:
            sentence_lower = sentence.lower().strip()
            
            # 标题类型
            if re.match(r'^[第\d]+[章节条]', sentence) or re.match(r'^chapter\s+\d+', sentence_lower):
                return 'title'
            
            # 列表项
            if re.match(r'^\d+[.)]\s+', sentence) or re.match(r'^[a-z][.)]\s+', sentence_lower):
                return 'list_item'
            
            # 问句
            if sentence.endswith('?') or sentence.endswith('？'):
                return 'question'
            
            # 定义句
            if '定义' in sentence or 'definition' in sentence_lower or '是指' in sentence:
                return 'definition'
            
            # 步骤说明
            if re.search(r'步骤|step|首先|然后|最后|finally', sentence_lower):
                return 'procedure'
            
            # 普通陈述句
            return 'statement'
            
        except Exception as e:
            self.logger.warning(f"句子类型分类失败: {e}")
            return 'statement'
    
    def _extract_topic_indicators(self, sentence: str) -> List[str]:
        """
        提取主题指示词
        
        Args:
            sentence: 句子文本
            
        Returns:
            list: 主题指示词列表
        """
        try:
            indicators = []
            
            # 转换指示词
            transition_words = [
                '然而', '但是', '因此', '所以', '另外', '此外', '总之', '综上',
                'however', 'therefore', 'moreover', 'furthermore', 'in conclusion'
            ]
            
            sentence_lower = sentence.lower()
            for word in transition_words:
                if word in sentence_lower:
                    indicators.append(word)
            
            return indicators
            
        except Exception as e:
            self.logger.warning(f"主题指示词提取失败: {e}")
            return []
    
    def _semantic_chunking(self, sentences: List[str], 
                         sentence_features: List[Dict[str, Any]], 
                         metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        基于语义相似度进行分块
        
        Args:
            sentences: 句子列表
            sentence_features: 句子特征列表
            metadata: 文档元数据
            
        Returns:
            list: 分块结果
        """
        try:
            chunks = []
            current_chunk_sentences = []
            current_chunk_length = 0
            
            for i, sentence in enumerate(sentences):
                sentence_length = len(sentence)
                
                # 检查是否应该开始新的分块
                should_start_new_chunk = self._should_start_new_chunk(
                    current_chunk_sentences, 
                    current_chunk_length, 
                    sentence, 
                    sentence_features[i] if i < len(sentence_features) else {}
                )
                
                if should_start_new_chunk and current_chunk_sentences:
                    # 创建当前分块
                    chunk = self._create_semantic_chunk(
                        current_chunk_sentences, 
                        metadata, 
                        len(chunks)
                    )
                    chunks.append(chunk)
                    
                    # 添加重叠句子
                    overlap_sentences = current_chunk_sentences[-self.sentence_overlap:] if self.sentence_overlap > 0 else []
                    current_chunk_sentences = overlap_sentences
                    current_chunk_length = sum(len(s) for s in overlap_sentences)
                
                # 添加当前句子到分块
                current_chunk_sentences.append(sentence)
                current_chunk_length += sentence_length
            
            # 处理最后一个分块
            if current_chunk_sentences:
                chunk = self._create_semantic_chunk(
                    current_chunk_sentences, 
                    metadata, 
                    len(chunks)
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"语义分块处理失败: {e}")
            return []
    
    def _should_start_new_chunk(self, current_sentences: List[str], 
                              current_length: int, 
                              new_sentence: str, 
                              sentence_feature: Dict[str, Any]) -> bool:
        """
        判断是否应该开始新的分块
        
        Args:
            current_sentences: 当前分块的句子列表
            current_length: 当前分块长度
            new_sentence: 新句子
            sentence_feature: 新句子的特征
            
        Returns:
            bool: 是否开始新分块
        """
        try:
            # 如果当前分块为空，不开始新分块
            if not current_sentences:
                return False
            
            new_sentence_length = len(new_sentence)
            
            # 检查长度限制
            if current_length + new_sentence_length > self.max_chunk_size:
                return True
            
            # 如果当前分块已达到目标大小，检查语义边界
            if current_length >= self.target_chunk_size:
                # 检查句子类型
                sentence_type = sentence_feature.get('sentence_type', 'statement')
                
                # 如果是标题或新的主题开始，开始新分块
                if sentence_type in ['title', 'definition']:
                    return True
                
                # 检查主题转换指示词
                topic_indicators = sentence_feature.get('topic_indicators', [])
                if topic_indicators:
                    return True
                
                # 如果句子以大写字母开始且包含关键词，可能是新主题
                if (sentence_feature.get('starts_with_capital', False) and 
                    sentence_feature.get('contains_keywords', [])):
                    return True
            
            # 检查最小长度限制
            if current_length < self.min_chunk_size:
                return False
            
            return False
            
        except Exception as e:
            self.logger.warning(f"分块判断失败: {e}")
            return current_length >= self.target_chunk_size
    
    def _create_semantic_chunk(self, sentences: List[str], 
                             metadata: Dict[str, Any], 
                             chunk_index: int) -> TextChunk:
        """
        创建语义分块
        
        Args:
            sentences: 句子列表
            metadata: 文档元数据
            chunk_index: 分块索引
            
        Returns:
            TextChunk: 分块对象
        """
        try:
            content = ' '.join(sentences)
            
            # 创建分块元数据
            chunk_metadata = ChunkMetadata(
                chunk_id=f"semantic_{chunk_index:04d}",
                chunk_type=ChunkType.PARAGRAPH,
                source_document=metadata.get('file_path', ''),
                processing_timestamp=datetime.now().isoformat()
            )
            
            return TextChunk(
                content=content,
                metadata=chunk_metadata
            )
            
        except Exception as e:
            self.logger.error(f"语义分块创建失败: {e}")
            return TextChunk(
                content=' '.join(sentences),
                metadata=ChunkMetadata(
                    chunk_id=f"semantic_{chunk_index:04d}",
                    chunk_type=ChunkType.PARAGRAPH,
                    source_document=""
                )
            )
