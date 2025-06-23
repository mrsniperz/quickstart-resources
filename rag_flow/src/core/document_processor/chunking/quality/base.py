"""
模块名称: base
功能描述: 质量评估基础类和数据结构定义
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# 为了避免循环导入，我们在这里定义一个简化的TextChunk类型
# 在实际使用中，会使用chunking_engine中的完整TextChunk类
try:
    from ..chunking_engine import TextChunk
except ImportError:
    # 如果无法导入，定义一个简化版本用于类型提示
    class TextChunk:
        def __init__(self, content: str, metadata=None):
            self.content = content
            self.metadata = metadata
            self.character_count = len(content)
            self.word_count = len(content.split())


@dataclass
class QualityMetrics:
    """
    质量评估指标数据类
    
    Attributes:
        overall_score: 总体质量评分（0-1）
        dimension_scores: 各维度评分字典
        confidence: 评估置信度（0-1）
        details: 详细评估信息
        strategy_name: 使用的评估策略名称
        processing_time: 评估处理时间（毫秒）
    """
    overall_score: float
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    strategy_name: str = ""
    processing_time: float = 0.0
    
    def __post_init__(self):
        """后处理验证"""
        # 确保评分在有效范围内
        self.overall_score = max(0.0, min(1.0, self.overall_score))
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        # 验证维度评分
        for dimension, score in self.dimension_scores.items():
            self.dimension_scores[dimension] = max(0.0, min(1.0, score))


class QualityAssessmentStrategy(ABC):
    """
    质量评估策略抽象基类
    
    定义了质量评估策略的统一接口，所有具体的评估策略都应该继承此类
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化评估策略
        
        Args:
            config: 策略配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def assess_quality(self, chunk: TextChunk, context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        评估分块质量
        
        Args:
            chunk: 待评估的文本分块
            context: 评估上下文信息，如文档元数据、相邻分块等
            
        Returns:
            QualityMetrics: 质量评估结果
            
        Raises:
            ValueError: 当输入参数无效时
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        获取策略名称
        
        Returns:
            str: 策略的唯一标识名称
        """
        pass
    
    @abstractmethod
    def get_supported_dimensions(self) -> List[str]:
        """
        获取支持的评估维度
        
        Returns:
            list: 支持的评估维度列表
        """
        pass
    
    def get_strategy_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            str: 策略的详细描述
        """
        return self.__doc__ or f"{self.get_strategy_name()} 质量评估策略"
    
    def validate_chunk(self, chunk: TextChunk) -> bool:
        """
        验证分块是否有效
        
        Args:
            chunk: 待验证的分块
            
        Returns:
            bool: 是否有效
        """
        try:
            if not chunk or not chunk.content:
                return False
            
            if not chunk.content.strip():
                return False
                
            return True
            
        except Exception as e:
            self.logger.warning(f"分块验证失败: {e}")
            return False
    
    def get_fallback_metrics(self, chunk: TextChunk, error: Exception) -> QualityMetrics:
        """
        获取回退评估结果
        
        Args:
            chunk: 分块对象
            error: 发生的异常
            
        Returns:
            QualityMetrics: 回退评估结果
        """
        try:
            # 基于分块长度给出基础评分
            if hasattr(chunk, 'character_count') and chunk.character_count:
                char_count = chunk.character_count
            else:
                char_count = len(chunk.content) if chunk.content else 0
            
            if char_count < 50:
                score = 0.3
            elif char_count > 2000:
                score = 0.4
            else:
                score = 0.5
            
            return QualityMetrics(
                overall_score=score,
                dimension_scores={'fallback': score},
                confidence=0.3,
                details={
                    'error': str(error),
                    'fallback_reason': 'Strategy execution failed',
                    'char_count': char_count
                },
                strategy_name=self.get_strategy_name()
            )
            
        except Exception:
            return QualityMetrics(
                overall_score=0.3,
                dimension_scores={'fallback': 0.3},
                confidence=0.1,
                details={'error': 'Complete evaluation failure'},
                strategy_name=self.get_strategy_name()
            )


class BaseQualityAssessment(QualityAssessmentStrategy):
    """
    基础质量评估策略
    
    提供通用的质量评估功能，适用于大多数文档类型
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化基础质量评估策略
        
        Args:
            config: 配置参数
                - weights: 各维度权重配置
                - min_chunk_size: 最小分块大小
                - max_chunk_size: 最大分块大小
                - optimal_chunk_size: 最优分块大小
        """
        super().__init__(config)
        
        # 默认权重配置
        default_weights = {
            'semantic_completeness': 0.40,
            'information_density': 0.30,
            'structure_quality': 0.20,
            'size_appropriateness': 0.10
        }
        
        self.weights = self.config.get('weights', default_weights)
        self.min_chunk_size = self.config.get('min_chunk_size', 100)
        self.max_chunk_size = self.config.get('max_chunk_size', 2000)
        self.optimal_chunk_size = self.config.get('optimal_chunk_size', 1000)
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "basic"
    
    def get_supported_dimensions(self) -> List[str]:
        """获取支持的评估维度"""
        return [
            'semantic_completeness',
            'information_density', 
            'structure_quality',
            'size_appropriateness'
        ]
    
    def assess_quality(self, chunk: TextChunk, context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        评估分块质量
        
        Args:
            chunk: 待评估的文本分块
            context: 评估上下文信息
            
        Returns:
            QualityMetrics: 质量评估结果
        """
        try:
            import time
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
            
            dimension_scores['semantic_completeness'] = self._calculate_semantic_completeness(chunk)
            dimension_scores['information_density'] = self._calculate_information_density(chunk)
            dimension_scores['structure_quality'] = self._calculate_structure_quality(chunk)
            dimension_scores['size_appropriateness'] = self._calculate_size_appropriateness(chunk)
            
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
                    'word_count': len(chunk.content.split())
                },
                strategy_name=self.get_strategy_name(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"基础质量评估失败: {e}")
            return self.get_fallback_metrics(chunk, e)
    
    def _calculate_semantic_completeness(self, chunk: TextChunk) -> float:
        """
        计算语义完整性评分

        评估文本分块的语义完整性，包括：
        - 句子完整性（是否有完整的句子结构）
        - 段落完整性（是否有完整的段落结构）
        - 语义单元完整性（概念、定义、描述等是否完整）
        - 截断检测（是否有明显的截断痕迹）

        Returns:
            float: 语义完整性评分（0-1）
        """
        try:
            import re

            content = chunk.content.strip()
            if not content:
                return 0.0

            score = 0.6  # 基础分

            # 1. 句子完整性检查 (权重: 0.3)
            sentence_score = self._evaluate_sentence_completeness(content)

            # 2. 段落完整性检查 (权重: 0.25)
            paragraph_score = self._evaluate_paragraph_completeness(content)

            # 3. 语义单元完整性检查 (权重: 0.25)
            semantic_unit_score = self._evaluate_semantic_unit_completeness(content)

            # 4. 截断检测 (权重: 0.2)
            truncation_score = self._evaluate_truncation_indicators(content)

            # 加权计算总分
            total_score = (
                sentence_score * 0.30 +
                paragraph_score * 0.25 +
                semantic_unit_score * 0.25 +
                truncation_score * 0.20
            )

            return max(0.0, min(1.0, total_score))

        except Exception as e:
            self.logger.warning(f"语义完整性评估失败: {e}")
            return 0.5  # 返回中等评分作为回退

    def _evaluate_sentence_completeness(self, content: str) -> float:
        """评估句子完整性"""
        try:
            import re

            # 检查句子结束标点
            sentences = re.split(r'[.!?。！？]', content)
            if not sentences:
                return 0.3

            # 过滤空句子
            valid_sentences = [s.strip() for s in sentences if s.strip()]
            if not valid_sentences:
                return 0.3

            # 检查最后一个句子是否完整（有结束标点）
            has_ending_punctuation = bool(re.search(r'[.!?。！？]\s*$', content))

            # 检查句子平均长度（太短可能不完整）
            avg_sentence_length = sum(len(s) for s in valid_sentences) / len(valid_sentences)

            score = 0.5
            if has_ending_punctuation:
                score += 0.3
            if avg_sentence_length >= 10:  # 合理的句子长度
                score += 0.2

            return min(1.0, score)

        except Exception:
            return 0.5

    def _evaluate_paragraph_completeness(self, content: str) -> float:
        """评估段落完整性"""
        try:
            # 检查段落结构
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

            if not paragraphs:
                # 单段落文本
                return 0.7 if len(content) > 50 else 0.4

            score = 0.6

            # 多段落文本的完整性检查
            if len(paragraphs) > 1:
                # 检查段落长度分布
                lengths = [len(p) for p in paragraphs]
                avg_length = sum(lengths) / len(lengths)

                # 避免过短的段落（可能是截断）
                short_paragraphs = sum(1 for length in lengths if length < avg_length * 0.3)
                if short_paragraphs / len(paragraphs) < 0.3:  # 少于30%的短段落
                    score += 0.3
                else:
                    score += 0.1
            else:
                score += 0.2

            return min(1.0, score)

        except Exception:
            return 0.6

    def _evaluate_semantic_unit_completeness(self, content: str) -> float:
        """评估语义单元完整性"""
        try:
            import re

            score = 0.6

            # 检查定义类语义单元
            definition_patterns = [
                r'是指|定义为|表示|意思是|refers to|means|defined as',
                r'包括|包含|consists of|includes',
                r'例如|比如|such as|for example'
            ]

            has_definitions = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in definition_patterns
            )

            if has_definitions:
                # 检查定义是否完整（有主语和谓语）
                if re.search(r'.+是.+|.+为.+|.+means.+|.+is.+', content, re.IGNORECASE):
                    score += 0.2
                else:
                    score += 0.1

            # 检查列举类语义单元
            enumeration_patterns = [
                r'第一|首先|1\.|①',
                r'第二|其次|2\.|②',
                r'最后|最终|finally|lastly'
            ]

            enumeration_count = sum(
                1 for pattern in enumeration_patterns
                if re.search(pattern, content, re.IGNORECASE)
            )

            if enumeration_count >= 2:
                score += 0.2
            elif enumeration_count == 1:
                score -= 0.1  # 可能是不完整的列举

            return min(1.0, score)

        except Exception:
            return 0.6

    def _evaluate_truncation_indicators(self, content: str) -> float:
        """评估截断指示器"""
        try:
            import re

            score = 0.8  # 默认认为没有截断

            # 检查明显的截断标志
            truncation_indicators = [
                r'\.\.\.+$',           # 结尾的省略号
                r'[^.!?。！？]\s*$',    # 没有结束标点的结尾
                r'^[^A-Z\u4e00-\u9fff]',  # 不是以大写字母或中文开头
                r'等等$|etc\.$',       # 以"等等"结尾
                r'如下$|如图$|见表$'    # 引用但没有内容
            ]

            for pattern in truncation_indicators:
                if re.search(pattern, content, re.IGNORECASE):
                    score -= 0.2

            # 检查句子是否突然中断
            if len(content) > 20:
                last_sentence = content.split('.')[-1].strip()
                if last_sentence and len(last_sentence) < 5:
                    score -= 0.1  # 最后一句太短，可能被截断

            return max(0.0, score)

        except Exception:
            return 0.7

    def _calculate_information_density(self, chunk: TextChunk) -> float:
        """
        计算信息密度评分

        评估文本分块的信息密度，包括：
        - 有效字符比例（非空白字符占比）
        - 关键词密度（重要词汇的分布）
        - 数值信息密度（数字、参数等技术信息）
        - 冗余度检测（重复内容的比例）

        Returns:
            float: 信息密度评分（0-1）
        """
        try:
            import re

            content = chunk.content.strip()
            if not content:
                return 0.0

            # 1. 有效字符比例 (权重: 0.25)
            effective_char_score = self._calculate_effective_char_ratio(content)

            # 2. 关键词密度 (权重: 0.30)
            keyword_density_score = self._calculate_keyword_density(content)

            # 3. 数值信息密度 (权重: 0.25)
            numerical_density_score = self._calculate_numerical_density(content)

            # 4. 冗余度评估 (权重: 0.20)
            redundancy_score = self._calculate_redundancy_score(content)

            # 加权计算总分
            total_score = (
                effective_char_score * 0.25 +
                keyword_density_score * 0.30 +
                numerical_density_score * 0.25 +
                redundancy_score * 0.20
            )

            return max(0.0, min(1.0, total_score))

        except Exception as e:
            self.logger.warning(f"信息密度评估失败: {e}")
            return 0.5  # 返回中等评分作为回退

    def _calculate_effective_char_ratio(self, content: str) -> float:
        """计算有效字符比例"""
        try:
            import re

            total_chars = len(content)
            if total_chars == 0:
                return 0.0

            # 计算非空白字符数量
            non_whitespace_chars = len(re.sub(r'\s', '', content))

            # 计算有效字符比例
            effective_ratio = non_whitespace_chars / total_chars

            # 转换为评分（0.7-1.0为优秀，0.5-0.7为良好，<0.5为较差）
            if effective_ratio >= 0.7:
                return 1.0
            elif effective_ratio >= 0.5:
                return 0.5 + (effective_ratio - 0.5) * 2.5  # 线性映射到0.5-1.0
            else:
                return effective_ratio * 1.0  # 线性映射到0-0.5

        except Exception:
            return 0.6

    def _calculate_keyword_density(self, content: str) -> float:
        """计算关键词密度"""
        try:
            import re

            # 分词（简单的基于空格和标点的分词）
            words = re.findall(r'\b\w+\b', content.lower())
            if not words:
                return 0.3

            total_words = len(words)

            # 定义关键词类别（可以根据需要扩展）
            important_word_patterns = [
                # 技术词汇
                r'系统|方法|技术|设备|功能|性能|参数|配置|操作|管理',
                r'system|method|technology|equipment|function|performance|parameter|configuration|operation|management',
                # 动作词汇
                r'实现|执行|处理|分析|计算|检测|控制|监控|优化|改进',
                r'implement|execute|process|analyze|calculate|detect|control|monitor|optimize|improve',
                # 描述词汇
                r'重要|关键|主要|核心|基础|高级|复杂|简单|有效|可靠',
                r'important|key|main|core|basic|advanced|complex|simple|effective|reliable'
            ]

            keyword_count = 0
            for pattern in important_word_patterns:
                keyword_count += len(re.findall(pattern, content, re.IGNORECASE))

            # 计算关键词密度
            keyword_density = keyword_count / total_words if total_words > 0 else 0

            # 转换为评分（5%-15%为理想密度）
            if 0.05 <= keyword_density <= 0.15:
                return 1.0
            elif 0.02 <= keyword_density < 0.05:
                return 0.6 + (keyword_density - 0.02) * 13.33  # 线性映射
            elif 0.15 < keyword_density <= 0.25:
                return 1.0 - (keyword_density - 0.15) * 4  # 密度过高扣分
            else:
                return max(0.2, min(0.6, keyword_density * 10))

        except Exception:
            return 0.5

    def _calculate_numerical_density(self, content: str) -> float:
        """计算数值信息密度"""
        try:
            import re

            # 检测数值信息
            numerical_patterns = [
                r'\d+\.?\d*%',          # 百分比
                r'\d+\.?\d*[A-Za-z]+',  # 带单位的数字
                r'\$\d+\.?\d*',         # 货币
                r'\d{4}-\d{2}-\d{2}',   # 日期
                r'\d+:\d+',             # 时间
                r'\d+\.?\d*',           # 普通数字
            ]

            numerical_matches = 0
            for pattern in numerical_patterns:
                numerical_matches += len(re.findall(pattern, content))

            # 计算数值密度（每100字符中的数值信息数量）
            char_count = len(content)
            if char_count == 0:
                return 0.0

            numerical_density = (numerical_matches / char_count) * 100

            # 转换为评分（1-5个数值信息/100字符为理想）
            if 1 <= numerical_density <= 5:
                return 1.0
            elif 0.5 <= numerical_density < 1:
                return 0.6 + (numerical_density - 0.5) * 0.8
            elif 5 < numerical_density <= 10:
                return 1.0 - (numerical_density - 5) * 0.08
            else:
                return max(0.2, min(0.6, numerical_density * 0.2))

        except Exception:
            return 0.5

    def _calculate_redundancy_score(self, content: str) -> float:
        """计算冗余度评分（冗余度越低，评分越高）"""
        try:
            import re

            # 分句
            sentences = re.split(r'[.!?。！？]', content)
            sentences = [s.strip() for s in sentences if s.strip()]

            if len(sentences) <= 1:
                return 0.8  # 单句或无句子，冗余度较低

            # 计算句子间的重复度
            total_comparisons = 0
            similar_pairs = 0

            for i in range(len(sentences)):
                for j in range(i + 1, len(sentences)):
                    total_comparisons += 1
                    similarity = self._calculate_sentence_similarity(sentences[i], sentences[j])
                    if similarity > 0.7:  # 相似度阈值
                        similar_pairs += 1

            if total_comparisons == 0:
                return 0.8

            redundancy_ratio = similar_pairs / total_comparisons

            # 冗余度越低，评分越高
            return max(0.2, 1.0 - redundancy_ratio)

        except Exception:
            return 0.7

    def _calculate_sentence_similarity(self, sent1: str, sent2: str) -> float:
        """计算两个句子的相似度（简单的词汇重叠度）"""
        try:
            import re

            words1 = set(re.findall(r'\b\w+\b', sent1.lower()))
            words2 = set(re.findall(r'\b\w+\b', sent2.lower()))

            if not words1 or not words2:
                return 0.0

            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))

            return intersection / union if union > 0 else 0.0

        except Exception:
            return 0.0

    def _calculate_structure_quality(self, chunk: TextChunk) -> float:
        """
        计算结构质量评分

        评估文本分块的结构质量，包括：
        - 标题结构（是否有清晰的标题层次）
        - 段落结构（段落组织是否合理）
        - 列表结构（列表格式是否规范）
        - 格式一致性（格式是否统一）

        Returns:
            float: 结构质量评分（0-1）
        """
        try:
            import re

            content = chunk.content.strip()
            if not content:
                return 0.0

            # 1. 标题结构评估 (权重: 0.30)
            title_score = self._evaluate_title_structure(content)

            # 2. 段落结构评估 (权重: 0.30)
            paragraph_score = self._evaluate_paragraph_structure(content)

            # 3. 列表结构评估 (权重: 0.25)
            list_score = self._evaluate_list_structure(content)

            # 4. 格式一致性评估 (权重: 0.15)
            format_score = self._evaluate_format_consistency(content)

            # 加权计算总分
            total_score = (
                title_score * 0.30 +
                paragraph_score * 0.30 +
                list_score * 0.25 +
                format_score * 0.15
            )

            return max(0.0, min(1.0, total_score))

        except Exception as e:
            self.logger.warning(f"结构质量评估失败: {e}")
            return 0.6  # 返回中等评分作为回退

    def _evaluate_title_structure(self, content: str) -> float:
        """评估标题结构"""
        try:
            import re

            # 检测各种标题格式
            title_patterns = [
                r'^#{1,6}\s+.+$',           # Markdown标题
                r'^\d+\.?\s+.+$',           # 数字标题
                r'^[一二三四五六七八九十]+[、\.]\s*.+$',  # 中文数字标题
                r'^[A-Z][A-Z\s]*:',         # 大写字母标题
                r'^\s*[【\[].*[】\]]\s*$',   # 括号标题
            ]

            lines = content.split('\n')
            title_lines = 0

            for line in lines:
                line = line.strip()
                if any(re.match(pattern, line, re.MULTILINE) for pattern in title_patterns):
                    title_lines += 1

            total_lines = len([line for line in lines if line.strip()])

            if total_lines == 0:
                return 0.5

            title_ratio = title_lines / total_lines

            # 标题比例在5%-20%之间为理想
            if 0.05 <= title_ratio <= 0.20:
                return 1.0
            elif 0.02 <= title_ratio < 0.05:
                return 0.6 + (title_ratio - 0.02) * 13.33
            elif 0.20 < title_ratio <= 0.35:
                return 1.0 - (title_ratio - 0.20) * 2.67
            else:
                return 0.5

        except Exception:
            return 0.6

    def _evaluate_paragraph_structure(self, content: str) -> float:
        """评估段落结构"""
        try:
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

            if not paragraphs:
                # 没有明显段落分隔，检查是否是单段落
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                if len(lines) <= 3:
                    return 0.7  # 短文本，段落结构可接受
                else:
                    return 0.4  # 长文本但没有段落分隔

            # 多段落文本
            if len(paragraphs) == 1:
                return 0.6  # 单段落

            # 检查段落长度分布
            lengths = [len(p) for p in paragraphs]
            avg_length = sum(lengths) / len(lengths)

            # 计算长度变异系数
            if avg_length > 0:
                variance = sum((length - avg_length) ** 2 for length in lengths) / len(lengths)
                std_dev = variance ** 0.5
                cv = std_dev / avg_length

                # 变异系数越小，段落长度越均匀
                if cv <= 0.5:
                    return 1.0
                elif cv <= 1.0:
                    return 0.8
                else:
                    return 0.6

            return 0.7

        except Exception:
            return 0.6

    def _evaluate_list_structure(self, content: str) -> float:
        """评估列表结构"""
        try:
            import re

            # 检测各种列表格式
            list_patterns = [
                r'^\s*[-*+]\s+.+$',         # 无序列表
                r'^\s*\d+[.)]\s+.+$',       # 有序列表
                r'^\s*[a-zA-Z][.)]\s+.+$',  # 字母列表
                r'^\s*[①②③④⑤⑥⑦⑧⑨⑩]\s*.+$', # 圆圈数字
            ]

            lines = content.split('\n')
            list_lines = 0
            consecutive_list_groups = 0
            in_list = False

            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                is_list_item = any(re.match(pattern, line, re.MULTILINE) for pattern in list_patterns)

                if is_list_item:
                    list_lines += 1
                    if not in_list:
                        consecutive_list_groups += 1
                        in_list = True
                else:
                    in_list = False

            if list_lines == 0:
                return 0.8  # 没有列表也是可以的

            # 检查列表的规范性
            if consecutive_list_groups > 0:
                avg_items_per_list = list_lines / consecutive_list_groups
                if avg_items_per_list >= 2:  # 每个列表至少2项
                    return 1.0
                else:
                    return 0.6

            return 0.7

        except Exception:
            return 0.7

    def _evaluate_format_consistency(self, content: str) -> float:
        """评估格式一致性"""
        try:
            import re

            score = 0.8  # 基础分

            # 检查标点符号一致性
            chinese_punctuation = len(re.findall(r'[，。！？；：]', content))
            english_punctuation = len(re.findall(r'[,.!?;:]', content))

            if chinese_punctuation > 0 and english_punctuation > 0:
                # 混用中英文标点，扣分
                total_punct = chinese_punctuation + english_punctuation
                consistency_ratio = max(chinese_punctuation, english_punctuation) / total_punct
                if consistency_ratio < 0.8:
                    score -= 0.2

            # 检查空行使用一致性
            lines = content.split('\n')
            empty_lines = sum(1 for line in lines if not line.strip())
            total_lines = len(lines)

            if total_lines > 0:
                empty_ratio = empty_lines / total_lines
                if 0.1 <= empty_ratio <= 0.3:  # 合理的空行比例
                    score += 0.1
                elif empty_ratio > 0.5:  # 空行过多
                    score -= 0.1

            return max(0.3, min(1.0, score))

        except Exception:
            return 0.7

    def _calculate_size_appropriateness(self, chunk: TextChunk) -> float:
        """计算大小适当性评分"""
        try:
            char_count = len(chunk.content)
            
            # 定义最优大小区间
            optimal_min = self.optimal_chunk_size * 0.8
            optimal_max = self.optimal_chunk_size * 1.2
            
            if optimal_min <= char_count <= optimal_max:
                return 1.0
            
            # 计算偏离最优区间的程度
            if char_count < optimal_min:
                if char_count < self.min_chunk_size:
                    ratio = char_count / self.min_chunk_size
                    return max(0.0, ratio * 0.3)
                else:
                    ratio = char_count / optimal_min
                    return 0.3 + ratio * 0.4
            else:
                if char_count > self.max_chunk_size:
                    ratio = self.max_chunk_size / char_count
                    return max(0.0, ratio * 0.5)
                else:
                    ratio = optimal_max / char_count
                    return 0.5 + ratio * 0.5
                    
        except Exception:
            return 0.5
