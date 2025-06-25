"""
模块名称: base_simplified
功能描述: 简化的质量评估基础类和数据结构定义
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0 (简化版)

重构说明:
- 移除复杂的多策略架构
- 简化为基本的长度和完整性检查
- 大幅减少代码复杂度，提升性能
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# 为了避免循环导入，我们在这里定义一个简化的TextChunk类型
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
    简化的质量评估指标数据类
    
    Attributes:
        overall_score: 总体质量评分（0-1）
        dimension_scores: 各维度评分字典（简化为2-3个维度）
        confidence: 评估置信度（0-1）
        details: 详细评估信息
        strategy_name: 使用的评估策略名称
        processing_time: 评估处理时间（毫秒）
    """
    overall_score: Optional[float]
    dimension_scores: Dict[str, Optional[float]] = field(default_factory=dict)
    confidence: Optional[float] = 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    strategy_name: str = "basic"
    processing_time: float = 0.0
    
    def __post_init__(self):
        """后处理验证"""
        # 确保评分在有效范围内（如果不为None）
        if self.overall_score is not None:
            self.overall_score = max(0.0, min(1.0, self.overall_score))
        if self.confidence is not None:
            self.confidence = max(0.0, min(1.0, self.confidence))

        # 验证维度评分
        for dimension, score in self.dimension_scores.items():
            if score is not None:
                self.dimension_scores[dimension] = max(0.0, min(1.0, score))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'overall_score': self.overall_score,
            'dimension_scores': self.dimension_scores,
            'confidence': self.confidence,
            'details': self.details,
            'strategy_name': self.strategy_name,
            'processing_time': self.processing_time
        }


class QualityAssessmentStrategy(ABC):
    """
    简化的质量评估策略抽象基类
    
    定义了质量评估策略的统一接口，简化为基本的长度和完整性检查
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化评估策略
        
        Args:
            config: 策略配置参数
                - min_length: 最小分块长度 (默认: 50)
                - max_length: 最大分块长度 (默认: 2000)
                - enable_quality_check: 是否启用质量检查 (默认: True)
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 简化的配置参数
        self.min_length = self.config.get('min_length', 50)
        self.max_length = self.config.get('max_length', 2000)
        self.enable_quality_check = self.config.get('enable_quality_check', True)
    
    @abstractmethod
    def assess_quality(self, chunk: TextChunk, context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        评估分块质量
        
        Args:
            chunk: 待评估的文本分块
            context: 评估上下文信息（简化版本中基本不使用）
            
        Returns:
            QualityMetrics: 质量评估结果
        """
        pass
    
    def get_strategy_name(self) -> str:
        """
        获取策略名称
        
        Returns:
            str: 策略的唯一标识名称
        """
        return "basic"
    
    def get_supported_dimensions(self) -> List[str]:
        """
        获取支持的评估维度（简化为2个核心维度）
        
        Returns:
            list: 支持的评估维度列表
        """
        return ['length_appropriateness', 'basic_completeness']
    
    def get_strategy_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            str: 策略的详细描述
        """
        return self.__doc__ or f"{self.get_strategy_name()} 简化质量评估策略"
    
    def validate_chunk(self, chunk: TextChunk) -> bool:
        """
        验证分块是否有效（简化版本）
        
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
        获取回退评估结果（简化版本）
        
        Args:
            chunk: 分块对象
            error: 发生的异常
            
        Returns:
            QualityMetrics: 回退评估结果
        """
        try:
            # 基于分块长度给出基础评分
            char_count = len(chunk.content) if chunk and chunk.content else 0
            
            if char_count < self.min_length:
                score = 0.3
            elif char_count > self.max_length:
                score = 0.4
            else:
                score = 0.7
            
            return QualityMetrics(
                overall_score=score,
                dimension_scores={'length_appropriateness': score, 'basic_completeness': score},
                confidence=0.5,
                details={
                    'error': str(error),
                    'fallback_reason': 'Strategy execution failed',
                    'char_count': char_count
                },
                strategy_name=self.get_strategy_name()
            )
            
        except Exception:
            return QualityMetrics(
                overall_score=0.5,
                dimension_scores={'length_appropriateness': 0.5, 'basic_completeness': 0.5},
                confidence=0.3,
                details={'error': 'Complete evaluation failure'},
                strategy_name=self.get_strategy_name()
            )


class BaseQualityAssessment(QualityAssessmentStrategy):
    """
    简化的基础质量评估策略
    
    只进行基本的长度检查和完整性验证，大幅简化评估逻辑
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化简化的基础质量评估策略
        
        Args:
            config: 配置参数
                - min_length: 最小分块长度 (默认: 50)
                - max_length: 最大分块长度 (默认: 2000)
                - optimal_length: 最优分块长度 (默认: 1000)
                - enable_quality_check: 是否启用质量检查 (默认: True)
        """
        super().__init__(config)
        
        # 简化的配置参数
        self.optimal_length = self.config.get('optimal_length', 1000)
        
        # 权重配置（简化为2个维度）
        self.length_weight = self.config.get('length_weight', 0.6)
        self.completeness_weight = self.config.get('completeness_weight', 0.4)
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "basic"
    
    def get_supported_dimensions(self) -> List[str]:
        """获取支持的评估维度（简化为2个核心维度）"""
        return ['length_appropriateness', 'basic_completeness']

    def assess_quality(self, chunk: TextChunk, context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        简化的分块质量评估

        Args:
            chunk: 待评估的文本分块
            context: 评估上下文信息（在简化版本中基本不使用）

        Returns:
            QualityMetrics: 质量评估结果
        """
        try:
            import time
            start_time = time.time()

            # 如果禁用质量检查，直接返回满分
            if not self.enable_quality_check:
                return QualityMetrics(
                    overall_score=1.0,
                    dimension_scores={'length_appropriateness': 1.0, 'basic_completeness': 1.0},
                    confidence=1.0,
                    details={'quality_check_disabled': True},
                    strategy_name=self.get_strategy_name(),
                    processing_time=0.1
                )

            if not self.validate_chunk(chunk):
                return QualityMetrics(
                    overall_score=0.0,
                    dimension_scores={'length_appropriateness': 0.0, 'basic_completeness': 0.0},
                    confidence=1.0,
                    details={'error': 'Invalid chunk'},
                    strategy_name=self.get_strategy_name()
                )

            # 简化的评估逻辑：只检查长度和基本完整性
            length_score = self._calculate_length_appropriateness(chunk)
            completeness_score = self._calculate_basic_completeness(chunk)

            # 计算加权总分
            overall_score = (length_score * self.length_weight +
                           completeness_score * self.completeness_weight)

            processing_time = (time.time() - start_time) * 1000

            return QualityMetrics(
                overall_score=overall_score,
                dimension_scores={
                    'length_appropriateness': length_score,
                    'basic_completeness': completeness_score
                },
                confidence=0.9,
                details={
                    'chunk_length': len(chunk.content),
                    'word_count': len(chunk.content.split()),
                    'simplified_evaluation': True
                },
                strategy_name=self.get_strategy_name(),
                processing_time=processing_time
            )

        except Exception as e:
            self.logger.error(f"简化质量评估失败: {e}")
            return self.get_fallback_metrics(chunk, e)

    def _calculate_length_appropriateness(self, chunk: TextChunk) -> float:
        """
        计算长度适当性评分（简化版本）

        Args:
            chunk: 文本分块

        Returns:
            float: 长度适当性评分（0-1）
        """
        try:
            char_count = len(chunk.content)

            # 定义最优长度区间
            optimal_min = self.optimal_length * 0.8
            optimal_max = self.optimal_length * 1.2

            # 在最优区间内给满分
            if optimal_min <= char_count <= optimal_max:
                return 1.0

            # 计算偏离最优区间的程度
            if char_count < optimal_min:
                if char_count < self.min_length:
                    return 0.2  # 过短严重扣分
                else:
                    ratio = char_count / optimal_min
                    return 0.5 + ratio * 0.5  # 线性映射到0.5-1.0
            else:
                if char_count > self.max_length:
                    return 0.3  # 过长严重扣分
                else:
                    ratio = optimal_max / char_count
                    return 0.5 + ratio * 0.5  # 线性映射到0.5-1.0

        except Exception as e:
            self.logger.warning(f"长度适当性评估失败: {e}")
            return 0.7  # 返回中等偏上评分作为回退

    def _calculate_basic_completeness(self, chunk: TextChunk) -> float:
        """
        计算基本完整性评分（简化版本）

        Args:
            chunk: 文本分块

        Returns:
            float: 基本完整性评分（0-1）
        """
        try:
            content = chunk.content.strip()
            if not content:
                return 0.0

            score = 0.7  # 基础分

            # 检查是否有明显的截断（简化检查）
            if content.endswith(('.', '。', '!', '！', '?', '？', ':', '：')):
                score += 0.2  # 有适当结尾加分
            elif content.endswith(('...', '…')):
                score -= 0.3  # 省略号结尾扣分

            # 检查是否过短
            if len(content) < 20:
                score -= 0.4  # 过短内容扣分

            # 检查是否有基本的词汇内容
            words = content.split()
            if len(words) < 3:
                score -= 0.3  # 词汇过少扣分

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"基本完整性评估失败: {e}")
            return 0.7  # 返回中等偏上评分作为回退
