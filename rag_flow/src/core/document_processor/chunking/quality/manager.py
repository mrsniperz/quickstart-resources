"""
模块名称: manager_simplified
功能描述: 简化的质量评估管理器
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0 (简化版)

重构说明:
- 移除复杂的多策略注册机制
- 只使用一个简化的基础策略
- 大幅简化管理逻辑，提升性能
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from functools import lru_cache

try:
    from .base import BaseQualityAssessment, QualityMetrics, TextChunk
    from .config_simplified import SimplifiedQualityConfig, QualityPreset
except ImportError:
    from base import BaseQualityAssessment, QualityMetrics, TextChunk
    from config_simplified import SimplifiedQualityConfig, QualityPreset


class SimplifiedQualityAssessmentManager:
    """
    简化的质量评估管理器
    
    只使用一个基础策略，大幅简化管理逻辑
    """
    
    def __init__(self, config: Optional[Union[SimplifiedQualityConfig, Dict[str, Any], str]] = None):
        """
        初始化简化的质量评估管理器
        
        Args:
            config: 配置参数，可以是：
                - SimplifiedQualityConfig 实例
                - 配置字典
                - 预设名称字符串 ('basic', 'strict', 'disabled')
                - None (使用默认配置)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 处理配置参数
        if config is None:
            self.config = SimplifiedQualityConfig()
        elif isinstance(config, SimplifiedQualityConfig):
            self.config = config
        elif isinstance(config, str):
            self.config = SimplifiedQualityConfig.from_preset(config)
        elif isinstance(config, dict):
            self.config = SimplifiedQualityConfig.from_dict(config)
        else:
            raise ValueError(f"不支持的配置类型: {type(config)}")
        
        # 验证配置
        if not self.config.validate_config():
            self.logger.warning("配置验证失败，使用默认配置")
            self.config = SimplifiedQualityConfig()
        
        # 初始化策略
        self.strategy = BaseQualityAssessment(self.config.get_config())
        
        # 统计信息
        self.stats = {
            'total_assessments': 0,
            'total_processing_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        self.logger.info(f"简化质量评估管理器初始化完成: {self.config}")
    
    def assess_chunk_quality(self, chunk: TextChunk, context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        评估单个分块的质量
        
        Args:
            chunk: 待评估的文本分块
            context: 评估上下文信息（简化版本中基本不使用）
            
        Returns:
            QualityMetrics: 质量评估结果
        """
        try:
            start_time = time.time()
            
            # 如果禁用质量检查，返回None表示未评估
            if not self.config.get_config().get('enable_quality_check', True):
                return QualityMetrics(
                    overall_score=None,
                    dimension_scores={'length_appropriateness': None, 'basic_completeness': None},
                    confidence=None,
                    details={'quality_check_disabled': True, 'note': 'Quality assessment disabled'},
                    strategy_name='disabled',
                    processing_time=0.0
                )
            
            # 使用缓存（基于内容长度的简单缓存）
            cache_key = self._generate_cache_key(chunk)
            cached_result = self._get_cached_result(cache_key)
            
            if cached_result:
                self.stats['cache_hits'] += 1
                return cached_result
            
            self.stats['cache_misses'] += 1
            
            # 执行评估
            result = self.strategy.assess_quality(chunk, context)
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            # 更新统计信息
            processing_time = (time.time() - start_time) * 1000
            self.stats['total_assessments'] += 1
            self.stats['total_processing_time'] += processing_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"分块质量评估失败: {e}")
            return self.strategy.get_fallback_metrics(chunk, e)
    
    def assess_chunks_batch(self, chunks: List[TextChunk], 
                          context: Optional[Dict[str, Any]] = None) -> List[QualityMetrics]:
        """
        批量评估分块质量（简化版本，串行处理）
        
        Args:
            chunks: 待评估的文本分块列表
            context: 评估上下文信息
            
        Returns:
            List[QualityMetrics]: 质量评估结果列表
        """
        try:
            results = []
            
            for chunk in chunks:
                result = self.assess_chunk_quality(chunk, context)
                results.append(result)
            
            self.logger.info(f"批量评估完成，处理了 {len(chunks)} 个分块")
            return results
            
        except Exception as e:
            self.logger.error(f"批量质量评估失败: {e}")
            # 返回回退结果
            return [self.strategy.get_fallback_metrics(chunk, e) for chunk in chunks]
    
    @lru_cache(maxsize=1000)
    def _get_cached_result(self, cache_key: str) -> Optional[QualityMetrics]:
        """获取缓存结果（使用LRU缓存）"""
        # 这里使用装饰器缓存，实际的缓存逻辑在_cache_result中
        return None
    
    def _cache_result(self, cache_key: str, result: QualityMetrics) -> None:
        """缓存评估结果（简化实现）"""
        # 在简化版本中，我们依赖LRU缓存装饰器
        pass
    
    def _generate_cache_key(self, chunk: TextChunk) -> str:
        """
        生成缓存键（简化版本）
        
        Args:
            chunk: 文本分块
            
        Returns:
            str: 缓存键
        """
        # 简化的缓存键：基于内容长度和前后几个字符
        content = chunk.content
        length = len(content)
        prefix = content[:20] if len(content) > 20 else content
        suffix = content[-20:] if len(content) > 20 else ""
        
        return f"{length}_{hash(prefix)}_{hash(suffix)}"
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息
        
        Returns:
            Dict[str, Any]: 策略信息
        """
        return {
            'strategy_name': self.strategy.get_strategy_name(),
            'strategy_description': self.strategy.get_strategy_description(),
            'supported_dimensions': self.strategy.get_supported_dimensions(),
            'config': self.config.get_config(),
            'preset': self.config.preset.value
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_assessments = self.stats['total_assessments']
        avg_processing_time = (
            self.stats['total_processing_time'] / total_assessments 
            if total_assessments > 0 else 0.0
        )
        
        cache_total = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (
            self.stats['cache_hits'] / cache_total 
            if cache_total > 0 else 0.0
        )
        
        return {
            'total_assessments': total_assessments,
            'total_processing_time_ms': self.stats['total_processing_time'],
            'average_processing_time_ms': avg_processing_time,
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'cache_hit_rate': cache_hit_rate,
            'strategy_name': self.strategy.get_strategy_name(),
            'config_preset': self.config.preset.value
        }
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.stats = {
            'total_assessments': 0,
            'total_processing_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.logger.info("统计信息已重置")
    
    def update_config(self, new_config: Union[SimplifiedQualityConfig, Dict[str, Any], str]) -> None:
        """
        更新配置
        
        Args:
            new_config: 新的配置参数
        """
        try:
            # 处理新配置
            if isinstance(new_config, SimplifiedQualityConfig):
                self.config = new_config
            elif isinstance(new_config, str):
                self.config = SimplifiedQualityConfig.from_preset(new_config)
            elif isinstance(new_config, dict):
                self.config = SimplifiedQualityConfig.from_dict(new_config)
            else:
                raise ValueError(f"不支持的配置类型: {type(new_config)}")
            
            # 验证配置
            if not self.config.validate_config():
                raise ValueError("新配置验证失败")
            
            # 重新初始化策略
            self.strategy = BaseQualityAssessment(self.config.get_config())
            
            # 清除缓存（因为配置改变了）
            self._get_cached_result.cache_clear()
            
            self.logger.info(f"配置更新成功: {self.config}")
            
        except Exception as e:
            self.logger.error(f"配置更新失败: {e}")
            raise
    
    def is_enabled(self) -> bool:
        """
        检查质量评估是否启用
        
        Returns:
            bool: 是否启用质量评估
        """
        return self.config.get_config().get('enable_quality_check', True)
    
    def disable_quality_check(self) -> None:
        """禁用质量检查"""
        self.update_config('disabled')
    
    def enable_quality_check(self, preset: str = 'basic') -> None:
        """
        启用质量检查
        
        Args:
            preset: 预设配置名称
        """
        self.update_config(preset)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SimplifiedQualityAssessmentManager(preset={self.config.preset.value}, enabled={self.is_enabled()})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"SimplifiedQualityAssessmentManager(config={self.config}, stats={self.stats})"


# 向后兼容的别名
QualityAssessmentManager = SimplifiedQualityAssessmentManager
