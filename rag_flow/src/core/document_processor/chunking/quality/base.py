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
        """计算语义完整性评分"""
        # 这里实现基础的语义完整性评估逻辑
        # 简化版本，后续可以扩展
        return 0.7
    
    def _calculate_information_density(self, chunk: TextChunk) -> float:
        """计算信息密度评分"""
        # 这里实现基础的信息密度评估逻辑
        return 0.6
    
    def _calculate_structure_quality(self, chunk: TextChunk) -> float:
        """计算结构质量评分"""
        # 这里实现基础的结构质量评估逻辑
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
