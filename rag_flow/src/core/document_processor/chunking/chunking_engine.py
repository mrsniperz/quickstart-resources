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
        
        # 策略注册表
        self.strategies: Dict[str, ChunkingStrategy] = {}
        
        # 注册内置策略
        self._register_builtin_strategies()
    
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
                
                # 计算质量评分
                chunk.quality_score = self._calculate_chunk_quality(chunk)
                
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
        计算分块质量评分（航空RAG系统优化版）

        Args:
            chunk: 文本分块

        Returns:
            float: 质量评分（0-1）
        """
        try:
            # 特殊情况处理
            if not chunk.content.strip():
                return 0.0

            if chunk.character_count < 10:
                return 0.1

            content = chunk.content.strip()

            # 根据文档类型获取权重配置
            weights = self._get_quality_weights(chunk.metadata)

            # 计算各维度评分
            aviation_score = self._calculate_aviation_specific_score(chunk)
            semantic_score = self._calculate_semantic_completeness_score(chunk)
            density_score = self._calculate_information_density_score(chunk)
            structure_score = self._calculate_structure_quality_score(chunk)
            size_score = self._calculate_size_appropriateness_score(chunk)

            # 加权计算总分
            total_score = (
                aviation_score * weights['aviation_specific'] +
                semantic_score * weights['semantic_completeness'] +
                density_score * weights['information_density'] +
                structure_score * weights['structure_quality'] +
                size_score * weights['size_appropriateness']
            )

            # 对于明显有问题的内容，应用惩罚机制
            penalty = 0.0

            # 内容过短惩罚
            if chunk.character_count < 30:
                penalty += 0.4
            elif chunk.character_count < 50:
                penalty += 0.2

            # 空白字符过多惩罚
            non_space_ratio = len(chunk.content.replace(' ', '').replace('\n', '').replace('\t', '')) / len(chunk.content)
            if non_space_ratio < 0.3:
                penalty += 0.5
            elif non_space_ratio < 0.5:
                penalty += 0.3
            elif non_space_ratio < 0.6:
                penalty += 0.1

            # 应用惩罚，但保留最低分数
            final_score = max(0.1, total_score - penalty)

            return round(min(1.0, final_score), 3)

        except Exception as e:
            self.logger.warning(f"分块质量评分计算失败: {e}")
            return self._get_fallback_score(chunk, e)

    def _get_quality_weights(self, metadata: ChunkMetadata) -> Dict[str, float]:
        """
        根据文档类型获取质量评估权重配置

        Args:
            metadata: 分块元数据

        Returns:
            dict: 权重配置
        """
        try:
            # 获取文档类型
            doc_type = getattr(metadata, 'chunk_type', None)
            if hasattr(doc_type, 'value'):
                doc_type = doc_type.value

            # 根据文档类型返回不同权重
            weight_configs = {
                'maintenance_manual': {
                    'aviation_specific': 0.30,
                    'semantic_completeness': 0.25,
                    'information_density': 0.20,
                    'structure_quality': 0.20,
                    'size_appropriateness': 0.05
                },
                'regulation': {
                    'aviation_specific': 0.20,
                    'semantic_completeness': 0.30,
                    'information_density': 0.25,
                    'structure_quality': 0.20,
                    'size_appropriateness': 0.05
                },
                'technical_standard': {
                    'aviation_specific': 0.25,
                    'semantic_completeness': 0.25,
                    'information_density': 0.25,
                    'structure_quality': 0.20,
                    'size_appropriateness': 0.05
                },
                'training_material': {
                    'aviation_specific': 0.20,
                    'semantic_completeness': 0.30,
                    'information_density': 0.20,
                    'structure_quality': 0.25,
                    'size_appropriateness': 0.05
                }
            }

            # 默认权重配置
            default_weights = {
                'aviation_specific': 0.25,
                'semantic_completeness': 0.25,
                'information_density': 0.25,
                'structure_quality': 0.20,
                'size_appropriateness': 0.05
            }

            return weight_configs.get(str(doc_type), default_weights)

        except Exception as e:
            self.logger.warning(f"获取权重配置失败: {e}")
            return {
                'aviation_specific': 0.25,
                'semantic_completeness': 0.25,
                'information_density': 0.25,
                'structure_quality': 0.20,
                'size_appropriateness': 0.05
            }

    def _get_fallback_score(self, chunk: TextChunk, error: Exception) -> float:
        """
        根据错误类型返回回退评分

        Args:
            chunk: 文本分块
            error: 异常对象

        Returns:
            float: 回退评分
        """
        try:
            # 根据内容长度给出基础评分
            if chunk.character_count < self.min_chunk_size:
                return 0.3
            elif chunk.character_count > self.max_chunk_size:
                return 0.4
            else:
                return 0.5
        except:
            return 0.3

    def _calculate_aviation_specific_score(self, chunk: TextChunk) -> float:
        """
        计算航空领域特定性评分

        Args:
            chunk: 文本分块

        Returns:
            float: 航空特定性评分（0-1）
        """
        try:
            score = 0.5  # 从较低的基础分开始
            content = chunk.content.lower()

            # 航空术语密度检查
            aviation_terms = [
                '发动机', '液压系统', '燃油系统', '电气系统', '起落架',
                '飞行控制', '导航系统', '通信系统', '客舱', '货舱',
                'engine', 'hydraulic', 'fuel system', 'electrical', 'landing gear',
                'flight control', 'navigation', 'communication', 'cabin', 'cargo'
            ]

            # 计算航空术语密度
            aviation_term_count = sum(1 for term in aviation_terms if term in content)
            if aviation_term_count > 0:
                score += min(0.3, aviation_term_count * 0.1)  # 每个术语加0.1分，最多0.3分

            # 检查航空术语是否被截断
            for term in aviation_terms:
                if term in content:
                    if content.startswith(term[1:]) or content.endswith(term[:-1]):
                        score -= 0.3  # 术语截断严重扣分
                        break

            # 安全信息完整性检查
            safety_keywords = [
                '警告', '注意', '危险', '禁止', '必须',
                'warning', 'caution', 'danger', 'prohibited', 'must'
            ]

            safety_found = any(keyword in content for keyword in safety_keywords)
            if safety_found:
                score += 0.2  # 包含安全信息加分
                if not self._is_safety_info_complete(chunk.content):
                    score -= 0.4  # 安全信息不完整严重扣分

            # 操作步骤连贯性检查
            step_patterns = [
                r'步骤\s*\d+', r'第\s*\d+\s*步', r'step\s+\d+',
                r'\d+\.\s', r'\(\d+\)', r'[a-z]\)'
            ]

            import re
            has_steps = any(re.search(pattern, content, re.IGNORECASE) for pattern in step_patterns)
            if has_steps:
                score += 0.2  # 包含步骤加分
                if self._has_incomplete_procedures(chunk.content):
                    score -= 0.3  # 步骤不完整扣分

            # 技术参数检查
            param_patterns = [
                r'\d+\s*(rpm|psi|°c|°f|kg|lb|ft|m|v|a|bar|mpa)',
                r'压力[:：]\s*\d+', r'温度[:：]\s*\d+', r'转速[:：]\s*\d+'
            ]

            has_params = any(re.search(pattern, content, re.IGNORECASE) for pattern in param_patterns)
            if has_params:
                score += 0.2  # 包含技术参数加分

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"航空特定性评分计算失败: {e}")
            return 0.5

    def _is_safety_info_complete(self, content: str) -> bool:
        """
        检查安全信息是否完整

        Args:
            content: 文本内容

        Returns:
            bool: 是否完整
        """
        try:
            safety_start_patterns = ['警告:', '注意:', '危险:', 'WARNING:', 'CAUTION:', 'DANGER:']

            for pattern in safety_start_patterns:
                if pattern in content:
                    start_idx = content.find(pattern)
                    after_warning = content[start_idx + len(pattern):].strip()

                    # 更严格的完整性检查
                    if len(after_warning) < 20:  # 提高最小长度要求
                        return False

                    # 检查是否有完整的句子结构
                    if not any(after_warning.endswith(end) for end in ['.', '。', '!', '！']):
                        return False

                    # 检查是否包含具体的安全措施描述
                    safety_action_keywords = ['必须', '禁止', '应该', '不得', 'must', 'should', 'do not', 'never']
                    if not any(keyword in after_warning for keyword in safety_action_keywords):
                        return False

            return True

        except Exception:
            return True

    def _has_incomplete_procedures(self, content: str) -> bool:
        """
        检查是否有不完整的操作步骤

        Args:
            content: 文本内容

        Returns:
            bool: 是否有不完整步骤
        """
        try:
            import re

            # 查找步骤编号
            step_numbers = re.findall(r'步骤\s*(\d+)|第\s*(\d+)\s*步|step\s+(\d+)|^(\d+)\.', content, re.IGNORECASE | re.MULTILINE)

            if not step_numbers:
                return False

            # 提取数字
            numbers = []
            for match in step_numbers:
                for group in match:
                    if group:
                        numbers.append(int(group))
                        break

            if not numbers:
                return False

            # 检查步骤是否连续
            numbers.sort()
            for i in range(len(numbers) - 1):
                if numbers[i + 1] - numbers[i] > 1:
                    return True  # 有跳跃，可能不完整

            # 检查是否以步骤开始但没有结束
            if numbers and not content.strip().endswith(('.', '。', '完成', 'complete', 'done')):
                return True

            return False

        except Exception:
            return False

    def _calculate_semantic_completeness_score(self, chunk: TextChunk) -> float:
        """
        计算语义完整性评分

        Args:
            chunk: 文本分块

        Returns:
            float: 语义完整性评分（0-1）
        """
        try:
            score = 0.6  # 从较低的基础分开始
            content = chunk.content.strip()

            # 检查内容结束的完整性
            proper_endings = ['.', '。', '!', '！', '?', '？', '：', ':', '完成', 'complete', '结束', 'end']
            has_proper_ending = any(content.endswith(ending) for ending in proper_endings)

            # 对于列表、参数等特殊格式，不要求句号结尾
            import re
            list_patterns = [
                r'^\s*[-•]\s',
                r'^\s*\d+\.\s',
                r'^\s*[a-zA-Z]\)\s',
                r':\s*$',
                r'\d+\s*(rpm|psi|°c|°f|kg|lb|ft|m|v|a)\s*$'
            ]

            is_special_format = any(re.search(pattern, content, re.IGNORECASE | re.MULTILINE) for pattern in list_patterns)

            if has_proper_ending or is_special_format:
                score += 0.3  # 有适当结尾加分
            else:
                score -= 0.2  # 没有适当结尾扣分

            # 检查句子完整性
            sentences = re.split(r'[.。!！?？]', content)
            complete_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]

            if len(complete_sentences) > 0:
                score += 0.2  # 有完整句子加分
            elif not is_special_format:
                score -= 0.3  # 没有完整句子且不是特殊格式扣分

            # 检查内容的连贯性
            if len(content) > 50:  # 对较长内容进行连贯性检查
                # 检查是否有突然的主题转换
                topic_keywords = {
                    'maintenance': ['维修', '检查', '更换', '安装'],
                    'operation': ['操作', '启动', '关闭', '运行'],
                    'safety': ['安全', '警告', '注意', '危险'],
                    'technical': ['参数', '规格', '标准', '技术']
                }

                topic_counts = {}
                content_lower = content.lower()

                for topic, keywords in topic_keywords.items():
                    count = sum(1 for keyword in keywords if keyword in content_lower)
                    if count > 0:
                        topic_counts[topic] = count

                # 如果主题过于分散，扣分
                if len(topic_counts) > 2:
                    score -= 0.1
                elif len(topic_counts) == 1:
                    score += 0.1  # 主题集中加分

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"语义完整性评分计算失败: {e}")
            return 0.5

    def _calculate_information_density_score(self, chunk: TextChunk) -> float:
        """
        计算信息密度评分

        Args:
            chunk: 文本分块

        Returns:
            float: 信息密度评分（0-1）
        """
        try:
            score = 0.5  # 从中等基础分开始
            content = chunk.content

            total_chars = len(content)
            if total_chars == 0:
                return 0.0

            # 计算有效字符比例
            non_space_chars = len(content.replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', ''))
            content_ratio = non_space_chars / total_chars

            if content_ratio >= 0.8:
                score += 0.3  # 高密度内容加分
            elif content_ratio >= 0.7:
                score += 0.2
            elif content_ratio >= 0.6:
                score += 0.1
            elif content_ratio < 0.5:
                score -= 0.4  # 低密度内容严重扣分
            elif content_ratio < 0.6:
                score -= 0.2

            # 计算信息关键词密度
            info_keywords = [
                '参数', '数值', '规格', '标准', '要求', '步骤', '方法', '程序',
                '检查', '测试', '维修', '更换', '安装', '调整', '校准',
                'parameter', 'value', 'specification', 'standard', 'requirement',
                'step', 'method', 'procedure', 'check', 'test', 'maintenance'
            ]

            content_lower = content.lower()
            keyword_count = sum(1 for keyword in info_keywords if keyword in content_lower)
            keyword_density = keyword_count / max(1, len(content.split()))

            if keyword_density >= 0.2:
                score += 0.3  # 高关键词密度加分
            elif keyword_density >= 0.1:
                score += 0.2
            elif keyword_density >= 0.05:
                score += 0.1
            else:
                score -= 0.2  # 低关键词密度扣分

            # 检查数字和技术数据的密度
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', content)
            units = re.findall(r'\d+\s*(rpm|psi|°c|°f|kg|lb|ft|m|v|a|bar|mpa)', content, re.IGNORECASE)

            if len(numbers) > 0:
                number_density = len(numbers) / max(1, len(content.split()))
                if number_density > 0.2:
                    score += 0.2  # 高数值密度加分
                elif number_density > 0.1:
                    score += 0.1

            if len(units) > 0:
                score += 0.1  # 包含技术单位加分

            # 检查是否包含无意义的重复内容
            words = content.split()
            if len(words) > 5:
                unique_words = set(words)
                repetition_ratio = len(words) / len(unique_words)
                if repetition_ratio > 3:
                    score -= 0.3  # 重复度太高扣分
                elif repetition_ratio < 1.5:
                    score += 0.1  # 词汇丰富度高加分

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"信息密度评分计算失败: {e}")
            return 0.5

    def _calculate_structure_quality_score(self, chunk: TextChunk) -> float:
        """
        计算结构质量评分

        Args:
            chunk: 文本分块

        Returns:
            float: 结构质量评分（0-1）
        """
        try:
            score = 0.4  # 从较低的基础分开始
            content = chunk.content

            # 检查标题和章节结构
            import re
            structure_markers = [
                r'^第\s*[一二三四五六七八九十\d]+\s*[章节条]',
                r'^Chapter\s+\d+',
                r'^Section\s+\d+',
                r'^#{1,6}\s',
                r'^\d+\.\d+',
                r'^[A-Z][A-Z\s]+:$'
            ]

            has_structure = any(re.search(pattern, content, re.IGNORECASE | re.MULTILINE) for pattern in structure_markers)

            if has_structure:
                score += 0.4  # 有明确结构标记大幅加分

            # 检查列表结构
            list_patterns = [
                r'^\s*[-•]\s',
                r'^\s*\d+\.\s',
                r'^\s*[a-zA-Z]\)\s',
                r'^\s*\([a-zA-Z0-9]+\)\s'
            ]

            list_items = []
            for pattern in list_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                list_items.extend(matches)

            if len(list_items) > 1:
                score += 0.3  # 有列表结构加分

                # 检查列表的一致性
                if len(set(list_items)) == len(list_items):
                    score += 0.1  # 列表标记一致加分
            elif len(list_items) == 1:
                score += 0.1  # 有单个列表项小幅加分

            # 检查段落结构
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if len(paragraphs) > 1:
                score += 0.2  # 有多段落结构加分

            # 检查特殊结构（表格、代码块等）
            special_structures = [
                r'\|.*\|',  # 表格
                r'```.*```',  # 代码块
                r'^\s*\w+[:：]\s*\w+',  # 键值对
                r'\d+\s*[x×]\s*\d+',  # 尺寸规格
            ]

            for pattern in special_structures:
                if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                    score += 0.2  # 有特殊结构加分
                    break

            # 检查结构的完整性
            incomplete_patterns = [
                (r'^\s*步骤\s*\d+', r'完成|结束|end|complete'),
                (r'^\s*注意[:：]', r'[.。!！]$'),
                (r'^\s*警告[:：]', r'[.。!！]$'),
            ]

            for start_pattern, end_pattern in incomplete_patterns:
                if re.search(start_pattern, content, re.IGNORECASE | re.MULTILINE):
                    if not re.search(end_pattern, content, re.IGNORECASE | re.MULTILINE):
                        score -= 0.3  # 结构不完整扣分
                        break

            # 检查特殊结构（表格、代码块等）
            special_structures = [
                r'\|.*\|',  # 表格
                r'```.*```',  # 代码块
                r'^\s*\w+[:：]\s*\w+',  # 键值对
                r'\d+\s*[x×]\s*\d+',  # 尺寸规格
            ]

            for pattern in special_structures:
                if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                    score += 0.1
                    break

            # 检查结构的完整性
            # 如果有开始标记但没有结束，可能结构不完整
            incomplete_patterns = [
                (r'^\s*步骤\s*\d+', r'完成|结束|end|complete'),  # 步骤开始但没结束
                (r'^\s*注意[:：]', r'[.。!！]$'),  # 注意事项没有结束标点
                (r'^\s*警告[:：]', r'[.。!！]$'),  # 警告没有结束标点
            ]

            for start_pattern, end_pattern in incomplete_patterns:
                if re.search(start_pattern, content, re.IGNORECASE | re.MULTILINE):
                    if not re.search(end_pattern, content, re.IGNORECASE | re.MULTILINE):
                        score -= 0.2
                        break

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"结构质量评分计算失败: {e}")
            return 0.7

    def _calculate_size_appropriateness_score(self, chunk: TextChunk) -> float:
        """
        计算大小适当性评分

        Args:
            chunk: 文本分块

        Returns:
            float: 大小适当性评分（0-1）
        """
        try:
            char_count = chunk.character_count

            # 定义最优大小区间
            optimal_min = self.chunk_size * 0.8
            optimal_max = self.chunk_size * 1.2

            if optimal_min <= char_count <= optimal_max:
                return 1.0

            # 计算偏离最优区间的程度
            if char_count < optimal_min:
                if char_count < self.min_chunk_size:
                    # 对过小的分块更严格评分
                    ratio = char_count / self.min_chunk_size
                    return max(0.0, ratio * 0.3)  # 降低基础分数
                else:
                    # 小于最优但在可接受范围内
                    ratio = char_count / optimal_min
                    return 0.3 + ratio * 0.4  # 调整评分范围
            else:
                if char_count > self.max_chunk_size:
                    ratio = self.max_chunk_size / char_count
                    return max(0.0, ratio * 0.5)
                else:
                    ratio = optimal_max / char_count
                    return 0.5 + ratio * 0.5

        except Exception as e:
            self.logger.warning(f"大小适当性评分计算失败: {e}")
            return 0.5

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
