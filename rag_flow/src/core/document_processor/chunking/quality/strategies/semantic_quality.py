"""
模块名称: semantic_quality
功能描述: 基于语义相似度的质量评估策略
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import re
import time
from typing import Dict, List, Optional, Any
from ..base import QualityAssessmentStrategy, QualityMetrics

# 为了避免循环导入，我们在这里处理TextChunk的导入
try:
    from ...chunking_engine import TextChunk
except ImportError:
    # 如果无法导入，使用base中的简化版本
    from ..base import TextChunk


class SemanticQualityAssessment(QualityAssessmentStrategy):
    """
    语义质量评估策略
    
    专注于评估分块的语义完整性和连贯性，包括：
    - 语义边界检测
    - 主题一致性评估
    - 上下文连贯性检查
    - 语义完整性验证
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化语义质量评估策略
        
        Args:
            config: 配置参数
                - weights: 各维度权重配置
                - semantic_threshold: 语义相似度阈值
                - coherence_window: 连贯性检查窗口大小
        """
        super().__init__(config)
        
        # 默认权重配置
        default_weights = {
            'semantic_boundary': 0.30,
            'topic_consistency': 0.25,
            'context_coherence': 0.25,
            'semantic_completeness': 0.20
        }
        
        self.weights = self.config.get('weights', default_weights)
        self.semantic_threshold = self.config.get('semantic_threshold', 0.7)
        self.coherence_window = self.config.get('coherence_window', 3)
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "semantic"
    
    def get_supported_dimensions(self) -> List[str]:
        """获取支持的评估维度"""
        return [
            'semantic_boundary',
            'topic_consistency',
            'context_coherence',
            'semantic_completeness'
        ]
    
    def assess_quality(self, chunk: TextChunk, context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        评估分块质量
        
        Args:
            chunk: 待评估的文本分块
            context: 评估上下文信息，包括相邻分块等
            
        Returns:
            QualityMetrics: 质量评估结果
        """
        try:
            start_time = time.time()
            
            if not self.validate_chunk(chunk):
                return QualityMetrics(
                    overall_score=0.0,
                    dimension_scores={},
                    confidence=0.0,
                    details={'error': 'Invalid chunk'},
                    strategy_name=self.get_strategy_name()
                )
            
            # 计算各维度评分
            dimension_scores = {}
            
            dimension_scores['semantic_boundary'] = self._calculate_semantic_boundary_score(chunk, context)
            dimension_scores['topic_consistency'] = self._calculate_topic_consistency_score(chunk)
            dimension_scores['context_coherence'] = self._calculate_context_coherence_score(chunk, context)
            dimension_scores['semantic_completeness'] = self._calculate_semantic_completeness_score(chunk)
            
            # 计算加权总分
            overall_score = sum(
                score * self.weights.get(dimension, 0.0)
                for dimension, score in dimension_scores.items()
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return QualityMetrics(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                confidence=0.8,
                details={
                    'weights_used': self.weights,
                    'chunk_length': len(chunk.content),
                    'sentence_count': len(self._split_sentences(chunk.content))
                },
                strategy_name=self.get_strategy_name(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"语义质量评估失败: {e}")
            return self.get_fallback_metrics(chunk, e)
    
    def _calculate_semantic_boundary_score(self, chunk: TextChunk, context: Optional[Dict[str, Any]]) -> float:
        """
        计算语义边界评分
        
        Args:
            chunk: 文本分块
            context: 上下文信息
            
        Returns:
            float: 语义边界评分（0-1）
        """
        try:
            score = 0.7  # 基础分
            content = chunk.content.strip()
            
            # 检查开始边界
            start_indicators = [
                r'^第\s*[一二三四五六七八九十\d]+\s*[章节条]',  # 章节开始
                r'^[A-Z][A-Z\s]*[:：]',  # 标题开始
                r'^\d+\.\s',  # 编号开始
                r'^[-•]\s',  # 列表开始
            ]
            
            has_clear_start = any(re.search(pattern, content, re.IGNORECASE) for pattern in start_indicators)
            if has_clear_start:
                score += 0.2
            
            # 检查结束边界
            end_indicators = [
                r'[.。!！?？]$',  # 句号结尾
                r'完成$|结束$|end$|done$',  # 明确结束词
                r':\s*$',  # 冒号结尾（列表等）
            ]
            
            has_clear_end = any(re.search(pattern, content, re.IGNORECASE) for pattern in end_indicators)
            if has_clear_end:
                score += 0.2
            
            # 检查是否在句子中间截断
            if content and not has_clear_end:
                # 简单检查：如果不以标点结尾且不是特殊格式，可能是截断
                if not re.search(r'[:：]\s*$|\d+\s*(rpm|psi|°c|°f|kg|lb|ft|m|v|a)\s*$', content, re.IGNORECASE):
                    score -= 0.3
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"语义边界评分计算失败: {e}")
            return 0.7
    
    def _calculate_topic_consistency_score(self, chunk: TextChunk) -> float:
        """
        计算主题一致性评分
        
        Args:
            chunk: 文本分块
            
        Returns:
            float: 主题一致性评分（0-1）
        """
        try:
            score = 0.6  # 基础分
            content = chunk.content.lower()
            
            # 定义主题关键词组
            topic_groups = {
                'maintenance': ['维修', '检查', '更换', '安装', '拆卸', '清洁', 'maintenance', 'repair', 'replace', 'install'],
                'operation': ['操作', '启动', '关闭', '运行', '控制', 'operation', 'start', 'stop', 'run', 'control'],
                'safety': ['安全', '警告', '注意', '危险', '防护', 'safety', 'warning', 'caution', 'danger', 'protection'],
                'technical': ['参数', '规格', '标准', '技术', '性能', 'parameter', 'specification', 'standard', 'technical'],
                'procedure': ['步骤', '程序', '流程', '方法', '过程', 'procedure', 'process', 'method', 'step'],
                'system': ['系统', '设备', '装置', '组件', '部件', 'system', 'equipment', 'device', 'component']
            }
            
            # 计算每个主题的关键词出现次数
            topic_scores = {}
            for topic, keywords in topic_groups.items():
                count = sum(1 for keyword in keywords if keyword in content)
                if count > 0:
                    topic_scores[topic] = count
            
            if not topic_scores:
                return 0.5  # 没有明确主题
            
            # 计算主题集中度
            total_keywords = sum(topic_scores.values())
            max_topic_count = max(topic_scores.values())
            
            # 主题集中度越高，评分越高
            concentration = max_topic_count / total_keywords
            if concentration >= 0.8:
                score += 0.3  # 高度集中
            elif concentration >= 0.6:
                score += 0.2  # 较为集中
            elif concentration >= 0.4:
                score += 0.1  # 一般集中
            else:
                score -= 0.2  # 主题分散
            
            # 检查主题转换的合理性
            sentences = self._split_sentences(chunk.content)
            if len(sentences) > 2:
                # 简单检查：相邻句子的主题一致性
                topic_changes = 0
                prev_topics = set()
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    current_topics = set()
                    
                    for topic, keywords in topic_groups.items():
                        if any(keyword in sentence_lower for keyword in keywords):
                            current_topics.add(topic)
                    
                    if prev_topics and current_topics and not current_topics.intersection(prev_topics):
                        topic_changes += 1
                    
                    prev_topics = current_topics
                
                # 主题变化过多扣分
                if topic_changes > len(sentences) * 0.3:
                    score -= 0.2
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"主题一致性评分计算失败: {e}")
            return 0.6
    
    def _calculate_context_coherence_score(self, chunk: TextChunk, context: Optional[Dict[str, Any]]) -> float:
        """
        计算上下文连贯性评分
        
        Args:
            chunk: 文本分块
            context: 上下文信息
            
        Returns:
            float: 上下文连贯性评分（0-1）
        """
        try:
            score = 0.7  # 基础分
            
            # 如果没有上下文信息，只能基于内部连贯性评估
            if not context:
                return self._calculate_internal_coherence(chunk)
            
            # 检查与前后分块的连贯性
            prev_chunk = context.get('previous_chunk')
            next_chunk = context.get('next_chunk')
            
            if prev_chunk:
                coherence_with_prev = self._calculate_chunk_coherence(prev_chunk, chunk)
                score += (coherence_with_prev - 0.5) * 0.3  # 调整权重
            
            if next_chunk:
                coherence_with_next = self._calculate_chunk_coherence(chunk, next_chunk)
                score += (coherence_with_next - 0.5) * 0.3  # 调整权重
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"上下文连贯性评分计算失败: {e}")
            return 0.7
    
    def _calculate_semantic_completeness_score(self, chunk: TextChunk) -> float:
        """
        计算语义完整性评分
        
        Args:
            chunk: 文本分块
            
        Returns:
            float: 语义完整性评分（0-1）
        """
        try:
            score = 0.6  # 基础分
            content = chunk.content.strip()
            
            # 检查句子完整性
            sentences = self._split_sentences(content)
            complete_sentences = [s for s in sentences if self._is_complete_sentence(s)]
            
            if sentences:
                completeness_ratio = len(complete_sentences) / len(sentences)
                score += completeness_ratio * 0.3
            
            # 检查语义单元完整性
            if self._has_complete_semantic_units(content):
                score += 0.2
            
            # 检查是否有明显的截断
            if self._has_obvious_truncation(content):
                score -= 0.3
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"语义完整性评分计算失败: {e}")
            return 0.6
    
    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        try:
            # 简单的句子分割
            sentences = re.split(r'[.。!！?？;；]', text)
            return [s.strip() for s in sentences if s.strip()]
        except Exception:
            return [text]
    
    def _is_complete_sentence(self, sentence: str) -> bool:
        """检查是否为完整句子"""
        try:
            sentence = sentence.strip()
            if len(sentence) < 3:
                return False
            
            # 简单的完整性检查
            has_subject = bool(re.search(r'[\u4e00-\u9fff]+|[a-zA-Z]+', sentence))
            has_predicate = bool(re.search(r'是|为|有|在|的|了|过|着|[a-zA-Z]+', sentence))
            
            return has_subject and has_predicate
        except Exception:
            return False
    
    def _has_complete_semantic_units(self, content: str) -> bool:
        """检查是否有完整的语义单元"""
        try:
            # 检查是否有完整的描述、说明或指令
            complete_patterns = [
                r'.*[:：].*[.。!！]',  # 描述模式
                r'步骤\s*\d+.*[.。!！]',  # 步骤模式
                r'注意.*[.。!！]',  # 注意事项模式
                r'警告.*[.。!！]',  # 警告模式
            ]
            
            return any(re.search(pattern, content, re.DOTALL) for pattern in complete_patterns)
        except Exception:
            return False
    
    def _has_obvious_truncation(self, content: str) -> bool:
        """检查是否有明显截断"""
        try:
            # 检查常见的截断模式
            truncation_patterns = [
                r'，$|,$',  # 以逗号结尾
                r'和$|与$|及$|or$|and$',  # 以连接词结尾
                r'的$|之$|for$|to$',  # 以介词结尾
                r'如下$|包括$|include$|such as$',  # 以引导词结尾但没有内容
            ]
            
            return any(re.search(pattern, content, re.IGNORECASE) for pattern in truncation_patterns)
        except Exception:
            return False
    
    def _calculate_internal_coherence(self, chunk: TextChunk) -> float:
        """计算内部连贯性"""
        try:
            score = 0.7
            sentences = self._split_sentences(chunk.content)
            
            if len(sentences) <= 1:
                return score
            
            # 简单的连贯性检查：相邻句子的词汇重叠
            coherence_scores = []
            for i in range(len(sentences) - 1):
                overlap = self._calculate_sentence_overlap(sentences[i], sentences[i + 1])
                coherence_scores.append(overlap)
            
            if coherence_scores:
                avg_coherence = sum(coherence_scores) / len(coherence_scores)
                score += (avg_coherence - 0.3) * 0.5  # 调整基于重叠度的评分
            
            return max(0.0, min(1.0, score))
        except Exception:
            return 0.7
    
    def _calculate_chunk_coherence(self, chunk1: TextChunk, chunk2: TextChunk) -> float:
        """计算两个分块之间的连贯性"""
        try:
            # 简单的连贯性计算：词汇重叠度
            words1 = set(chunk1.content.lower().split())
            words2 = set(chunk2.content.lower().split())
            
            if not words1 or not words2:
                return 0.5
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        except Exception:
            return 0.5
    
    def _calculate_sentence_overlap(self, sent1: str, sent2: str) -> float:
        """计算两个句子的词汇重叠度"""
        try:
            words1 = set(sent1.lower().split())
            words2 = set(sent2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        except Exception:
            return 0.0
