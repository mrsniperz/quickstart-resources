"""
模块名称: length_quality
功能描述: 基于长度均匀性的质量评估策略
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import time
import statistics
from typing import Dict, List, Optional, Any
from ..base import QualityAssessmentStrategy, QualityMetrics

# 为了避免循环导入，我们在这里处理TextChunk的导入
try:
    from ...chunking_engine import TextChunk
except ImportError:
    # 如果无法导入，使用base中的简化版本
    from ..base import TextChunk


class LengthUniformityAssessment(QualityAssessmentStrategy):
    """
    长度均匀性质量评估策略
    
    专注于评估分块长度的合理性和均匀性，包括：
    - 分块大小适当性
    - 长度分布均匀性
    - 相对长度一致性
    - 长度变异系数评估
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化长度均匀性评估策略
        
        Args:
            config: 配置参数
                - target_length: 目标分块长度
                - min_length: 最小可接受长度
                - max_length: 最大可接受长度
                - tolerance_ratio: 长度容忍比例
                - weights: 各维度权重配置
        """
        super().__init__(config)
        
        # 长度配置
        self.target_length = self.config.get('target_length', 1000)
        self.min_length = self.config.get('min_length', 100)
        self.max_length = self.config.get('max_length', 2000)
        self.tolerance_ratio = self.config.get('tolerance_ratio', 0.3)  # 30%容忍度
        
        # 默认权重配置
        default_weights = {
            'size_appropriateness': 0.40,
            'length_uniformity': 0.30,
            'relative_consistency': 0.20,
            'variation_coefficient': 0.10
        }
        
        self.weights = self.config.get('weights', default_weights)
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "length_uniformity"
    
    def get_supported_dimensions(self) -> List[str]:
        """获取支持的评估维度"""
        return [
            'size_appropriateness',
            'length_uniformity',
            'relative_consistency',
            'variation_coefficient'
        ]
    
    def assess_quality(self, chunk: TextChunk, context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        评估分块质量
        
        Args:
            chunk: 待评估的文本分块
            context: 评估上下文信息，包括其他分块的长度信息
            
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
            
            # 获取分块长度
            chunk_length = len(chunk.content)
            
            # 计算各维度评分
            dimension_scores = {}
            
            dimension_scores['size_appropriateness'] = self._calculate_size_appropriateness(chunk_length)
            dimension_scores['length_uniformity'] = self._calculate_length_uniformity(chunk_length, context)
            dimension_scores['relative_consistency'] = self._calculate_relative_consistency(chunk_length, context)
            dimension_scores['variation_coefficient'] = self._calculate_variation_coefficient(chunk_length, context)
            
            # 计算加权总分
            overall_score = sum(
                score * self.weights.get(dimension, 0.0)
                for dimension, score in dimension_scores.items()
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return QualityMetrics(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                confidence=0.9,  # 长度评估置信度较高
                details={
                    'chunk_length': chunk_length,
                    'target_length': self.target_length,
                    'length_ratio': chunk_length / self.target_length,
                    'weights_used': self.weights
                },
                strategy_name=self.get_strategy_name(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"长度均匀性评估失败: {e}")
            return self.get_fallback_metrics(chunk, e)
    
    def _calculate_size_appropriateness(self, chunk_length: int) -> float:
        """
        计算大小适当性评分
        
        Args:
            chunk_length: 分块长度
            
        Returns:
            float: 大小适当性评分（0-1）
        """
        try:
            # 定义最优长度区间
            optimal_min = self.target_length * (1 - self.tolerance_ratio)
            optimal_max = self.target_length * (1 + self.tolerance_ratio)
            
            # 在最优区间内得满分
            if optimal_min <= chunk_length <= optimal_max:
                return 1.0
            
            # 在可接受范围内按距离计算评分
            if self.min_length <= chunk_length <= self.max_length:
                if chunk_length < optimal_min:
                    # 小于最优区间
                    distance_ratio = (optimal_min - chunk_length) / (optimal_min - self.min_length)
                    return max(0.3, 1.0 - distance_ratio * 0.7)
                else:
                    # 大于最优区间
                    distance_ratio = (chunk_length - optimal_max) / (self.max_length - optimal_max)
                    return max(0.3, 1.0 - distance_ratio * 0.7)
            
            # 超出可接受范围
            if chunk_length < self.min_length:
                # 过短
                ratio = chunk_length / self.min_length
                return max(0.0, ratio * 0.3)
            else:
                # 过长
                ratio = self.max_length / chunk_length
                return max(0.0, ratio * 0.3)
                
        except Exception as e:
            self.logger.warning(f"大小适当性评分计算失败: {e}")
            return 0.5
    
    def _calculate_length_uniformity(self, chunk_length: int, context: Optional[Dict[str, Any]]) -> float:
        """
        计算长度均匀性评分
        
        Args:
            chunk_length: 当前分块长度
            context: 上下文信息，包含其他分块长度
            
        Returns:
            float: 长度均匀性评分（0-1）
        """
        try:
            if not context or 'chunk_lengths' not in context:
                # 没有上下文信息，只能基于目标长度评估
                return self._calculate_target_deviation_score(chunk_length)
            
            chunk_lengths = context['chunk_lengths']
            if not chunk_lengths or len(chunk_lengths) < 2:
                return self._calculate_target_deviation_score(chunk_length)
            
            # 计算长度的标准差和平均值
            all_lengths = chunk_lengths + [chunk_length]
            mean_length = statistics.mean(all_lengths)
            std_length = statistics.stdev(all_lengths) if len(all_lengths) > 1 else 0
            
            # 计算变异系数
            cv = std_length / mean_length if mean_length > 0 else 1.0
            
            # 变异系数越小，均匀性越好
            if cv <= 0.1:
                return 1.0  # 非常均匀
            elif cv <= 0.2:
                return 0.9  # 很均匀
            elif cv <= 0.3:
                return 0.7  # 较均匀
            elif cv <= 0.5:
                return 0.5  # 一般
            else:
                return max(0.1, 1.0 - cv)  # 不均匀
                
        except Exception as e:
            self.logger.warning(f"长度均匀性评分计算失败: {e}")
            return 0.5
    
    def _calculate_relative_consistency(self, chunk_length: int, context: Optional[Dict[str, Any]]) -> float:
        """
        计算相对一致性评分
        
        Args:
            chunk_length: 当前分块长度
            context: 上下文信息
            
        Returns:
            float: 相对一致性评分（0-1）
        """
        try:
            if not context:
                return 0.7  # 默认分数
            
            # 检查与相邻分块的长度一致性
            prev_length = context.get('previous_chunk_length')
            next_length = context.get('next_chunk_length')
            
            scores = []
            
            if prev_length:
                consistency_score = self._calculate_length_consistency(chunk_length, prev_length)
                scores.append(consistency_score)
            
            if next_length:
                consistency_score = self._calculate_length_consistency(chunk_length, next_length)
                scores.append(consistency_score)
            
            if scores:
                return sum(scores) / len(scores)
            else:
                return 0.7  # 没有相邻分块信息
                
        except Exception as e:
            self.logger.warning(f"相对一致性评分计算失败: {e}")
            return 0.7
    
    def _calculate_variation_coefficient(self, chunk_length: int, context: Optional[Dict[str, Any]]) -> float:
        """
        计算变异系数评分
        
        Args:
            chunk_length: 当前分块长度
            context: 上下文信息
            
        Returns:
            float: 变异系数评分（0-1）
        """
        try:
            if not context or 'chunk_lengths' not in context:
                return 0.7  # 默认分数
            
            chunk_lengths = context['chunk_lengths']
            if not chunk_lengths:
                return 0.7
            
            # 包含当前分块计算变异系数
            all_lengths = chunk_lengths + [chunk_length]
            
            if len(all_lengths) < 2:
                return 0.7
            
            mean_length = statistics.mean(all_lengths)
            std_length = statistics.stdev(all_lengths)
            
            cv = std_length / mean_length if mean_length > 0 else 1.0
            
            # 变异系数评分：越小越好
            if cv <= 0.15:
                return 1.0
            elif cv <= 0.25:
                return 0.8
            elif cv <= 0.35:
                return 0.6
            elif cv <= 0.5:
                return 0.4
            else:
                return max(0.1, 0.5 - cv)
                
        except Exception as e:
            self.logger.warning(f"变异系数评分计算失败: {e}")
            return 0.7
    
    def _calculate_target_deviation_score(self, chunk_length: int) -> float:
        """
        计算与目标长度的偏差评分
        
        Args:
            chunk_length: 分块长度
            
        Returns:
            float: 偏差评分（0-1）
        """
        try:
            deviation = abs(chunk_length - self.target_length)
            max_acceptable_deviation = self.target_length * self.tolerance_ratio
            
            if deviation <= max_acceptable_deviation:
                return 1.0 - (deviation / max_acceptable_deviation) * 0.2
            else:
                # 超出容忍范围，评分快速下降
                excess_deviation = deviation - max_acceptable_deviation
                max_excess = self.target_length  # 最大额外偏差
                excess_ratio = min(1.0, excess_deviation / max_excess)
                return max(0.1, 0.8 - excess_ratio * 0.7)
                
        except Exception:
            return 0.5
    
    def _calculate_length_consistency(self, length1: int, length2: int) -> float:
        """
        计算两个长度之间的一致性
        
        Args:
            length1: 第一个长度
            length2: 第二个长度
            
        Returns:
            float: 一致性评分（0-1）
        """
        try:
            if length1 == 0 or length2 == 0:
                return 0.0
            
            ratio = min(length1, length2) / max(length1, length2)
            
            # 比例越接近1，一致性越好
            if ratio >= 0.9:
                return 1.0
            elif ratio >= 0.8:
                return 0.9
            elif ratio >= 0.7:
                return 0.7
            elif ratio >= 0.5:
                return 0.5
            else:
                return max(0.1, ratio)
                
        except Exception:
            return 0.5
    
    def assess_batch_quality(self, chunks: List[TextChunk]) -> List[QualityMetrics]:
        """
        批量评估分块质量（针对长度均匀性优化）
        
        Args:
            chunks: 分块列表
            
        Returns:
            list: 质量评估结果列表
        """
        try:
            if not chunks:
                return []
            
            # 提取所有分块长度
            chunk_lengths = [len(chunk.content) for chunk in chunks]
            
            results = []
            for i, chunk in enumerate(chunks):
                # 构建上下文信息
                context = {
                    'chunk_lengths': chunk_lengths[:i] + chunk_lengths[i+1:],  # 排除当前分块
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
                
                # 添加相邻分块长度信息
                if i > 0:
                    context['previous_chunk_length'] = chunk_lengths[i-1]
                if i < len(chunks) - 1:
                    context['next_chunk_length'] = chunk_lengths[i+1]
                
                result = self.assess_quality(chunk, context)
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"批量长度评估失败: {e}")
            return [self.get_fallback_metrics(chunk, e) for chunk in chunks]
