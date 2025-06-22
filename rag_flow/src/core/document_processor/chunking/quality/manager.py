"""
模块名称: manager
功能描述: 质量评估管理器，负责策略注册、选择和执行
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
import time
from typing import Dict, List, Optional, Any
from .base import QualityAssessmentStrategy, QualityMetrics, BaseQualityAssessment

# 为了避免循环导入，我们在这里处理TextChunk的导入
try:
    from ..chunking_engine import TextChunk
except ImportError:
    # 如果无法导入，使用base中的简化版本
    from .base import TextChunk


class QualityAssessmentManager:
    """
    质量评估管理器
    
    负责管理不同的质量评估策略，提供统一的评估接口
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化质量评估管理器
        
        Args:
            config: 配置参数
                - default_strategy: 默认评估策略名称
                - strategies: 策略配置字典
                - enable_caching: 是否启用结果缓存
                - cache_size: 缓存大小限制
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 策略注册表
        self.strategies: Dict[str, QualityAssessmentStrategy] = {}
        
        # 配置参数
        self.default_strategy = self.config.get('default_strategy', 'basic')
        self.enable_caching = self.config.get('enable_caching', False)
        self.cache_size = self.config.get('cache_size', 1000)
        
        # 结果缓存
        self._cache: Dict[str, QualityMetrics] = {}
        self._cache_access_order: List[str] = []
        
        # 注册内置策略
        self._register_builtin_strategies()
    
    def register_strategy(self, name: str, strategy: QualityAssessmentStrategy) -> None:
        """
        注册质量评估策略
        
        Args:
            name: 策略名称
            strategy: 策略实例
            
        Raises:
            ValueError: 当策略名称已存在时
        """
        try:
            if name in self.strategies:
                self.logger.warning(f"策略 {name} 已存在，将被覆盖")
            
            self.strategies[name] = strategy
            self.logger.info(f"注册质量评估策略: {name}")
            
        except Exception as e:
            self.logger.error(f"注册策略失败: {e}")
            raise ValueError(f"注册策略 {name} 失败: {e}")
    
    def unregister_strategy(self, name: str) -> bool:
        """
        注销质量评估策略
        
        Args:
            name: 策略名称
            
        Returns:
            bool: 是否成功注销
        """
        try:
            if name not in self.strategies:
                self.logger.warning(f"策略 {name} 不存在")
                return False
            
            if name == self.default_strategy:
                self.logger.warning(f"不能注销默认策略 {name}")
                return False
            
            del self.strategies[name]
            self.logger.info(f"注销质量评估策略: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注销策略失败: {e}")
            return False
    
    def assess_chunk_quality(self, 
                           chunk: TextChunk, 
                           strategy_name: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        评估分块质量
        
        Args:
            chunk: 待评估的文本分块
            strategy_name: 指定的评估策略名称，为None时使用默认策略
            context: 评估上下文信息
            
        Returns:
            QualityMetrics: 质量评估结果
            
        Raises:
            ValueError: 当策略不存在时
        """
        try:
            # 选择评估策略
            strategy_name = strategy_name or self.default_strategy
            
            if strategy_name not in self.strategies:
                available_strategies = list(self.strategies.keys())
                raise ValueError(f"策略 {strategy_name} 不存在。可用策略: {available_strategies}")
            
            # 检查缓存
            if self.enable_caching:
                cache_key = self._generate_cache_key(chunk, strategy_name, context)
                if cache_key in self._cache:
                    self._update_cache_access(cache_key)
                    cached_result = self._cache[cache_key]
                    self.logger.debug(f"使用缓存结果: {cache_key}")
                    return cached_result
            
            # 执行评估
            strategy = self.strategies[strategy_name]
            
            self.logger.debug(f"使用策略 {strategy_name} 评估分块质量")
            
            start_time = time.time()
            result = strategy.assess_quality(chunk, context)
            processing_time = (time.time() - start_time) * 1000
            
            # 更新处理时间
            result.processing_time = processing_time
            result.strategy_name = strategy_name
            
            # 缓存结果
            if self.enable_caching:
                self._cache_result(cache_key, result)
            
            self.logger.debug(f"质量评估完成: 总分={result.overall_score:.3f}, 耗时={processing_time:.2f}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"质量评估失败: {e}")
            # 返回回退结果
            return QualityMetrics(
                overall_score=0.3,
                dimension_scores={'error': 0.3},
                confidence=0.1,
                details={'error': str(e), 'strategy_name': strategy_name or 'unknown'},
                strategy_name=strategy_name or 'unknown'
            )
    
    def assess_chunks_batch(self, 
                          chunks: List[TextChunk],
                          strategy_name: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None) -> List[QualityMetrics]:
        """
        批量评估分块质量
        
        Args:
            chunks: 待评估的分块列表
            strategy_name: 指定的评估策略名称
            context: 评估上下文信息
            
        Returns:
            list: 质量评估结果列表
        """
        try:
            results = []
            
            for i, chunk in enumerate(chunks):
                try:
                    # 为每个分块添加索引信息到上下文
                    chunk_context = context.copy() if context else {}
                    chunk_context['chunk_index'] = i
                    chunk_context['total_chunks'] = len(chunks)
                    
                    result = self.assess_chunk_quality(chunk, strategy_name, chunk_context)
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"评估第{i}个分块失败: {e}")
                    # 添加错误结果
                    error_result = QualityMetrics(
                        overall_score=0.3,
                        dimension_scores={'error': 0.3},
                        confidence=0.1,
                        details={'error': str(e), 'chunk_index': i},
                        strategy_name=strategy_name or 'unknown'
                    )
                    results.append(error_result)
            
            self.logger.info(f"批量评估完成: {len(results)}/{len(chunks)} 个分块")
            return results
            
        except Exception as e:
            self.logger.error(f"批量评估失败: {e}")
            return []
    
    def get_available_strategies(self) -> List[str]:
        """
        获取可用的评估策略列表
        
        Returns:
            list: 策略名称列表
        """
        return list(self.strategies.keys())
    
    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """
        获取策略详细信息
        
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
                'description': strategy.get_strategy_description(),
                'supported_dimensions': strategy.get_supported_dimensions(),
                'config': getattr(strategy, 'config', {})
            }
            
        except Exception as e:
            self.logger.error(f"获取策略信息失败: {e}")
            return {'error': str(e)}
    
    def get_all_strategies_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有策略的信息
        
        Returns:
            dict: 所有策略信息的字典
        """
        return {name: self.get_strategy_info(name) for name in self.strategies.keys()}
    
    def set_default_strategy(self, strategy_name: str) -> bool:
        """
        设置默认评估策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if strategy_name not in self.strategies:
                self.logger.error(f"策略 {strategy_name} 不存在")
                return False
            
            self.default_strategy = strategy_name
            self.logger.info(f"设置默认策略为: {strategy_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置默认策略失败: {e}")
            return False
    
    def clear_cache(self) -> None:
        """清空评估结果缓存"""
        self._cache.clear()
        self._cache_access_order.clear()
        self.logger.info("清空质量评估缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            dict: 缓存统计信息
        """
        return {
            'enabled': self.enable_caching,
            'size': len(self._cache),
            'max_size': self.cache_size,
            'hit_rate': getattr(self, '_cache_hits', 0) / max(1, getattr(self, '_cache_requests', 1))
        }
    
    def _register_builtin_strategies(self) -> None:
        """注册内置评估策略"""
        try:
            # 导入策略类
            from .strategies.aviation_quality import AviationQualityAssessment
            from .strategies.semantic_quality import SemanticQualityAssessment
            from .strategies.length_quality import LengthUniformityAssessment
            from .strategies.completeness_quality import ContentCompletenessAssessment

            # 获取策略配置
            strategies_config = self.config.get('strategies', {})

            # 注册基础策略
            basic_config = strategies_config.get('basic', {})
            self.register_strategy('basic', BaseQualityAssessment(basic_config))

            # 注册航空质量评估策略
            aviation_config = strategies_config.get('aviation', {})
            self.register_strategy('aviation', AviationQualityAssessment(aviation_config))

            # 注册语义质量评估策略
            semantic_config = strategies_config.get('semantic', {})
            self.register_strategy('semantic', SemanticQualityAssessment(semantic_config))

            # 注册长度均匀性评估策略
            length_config = strategies_config.get('length_uniformity', {})
            self.register_strategy('length_uniformity', LengthUniformityAssessment(length_config))

            # 注册内容完整性评估策略
            completeness_config = strategies_config.get('content_completeness', {})
            self.register_strategy('content_completeness', ContentCompletenessAssessment(completeness_config))

            self.logger.info("内置策略注册完成")

        except Exception as e:
            self.logger.error(f"内置策略注册失败: {e}")
    
    def _generate_cache_key(self, chunk: TextChunk, strategy_name: str, context: Optional[Dict[str, Any]]) -> str:
        """生成缓存键"""
        try:
            import hashlib
            
            # 使用分块内容、策略名称和关键上下文信息生成键
            content_hash = hashlib.md5(chunk.content.encode('utf-8')).hexdigest()[:16]
            context_str = str(sorted(context.items())) if context else ""
            context_hash = hashlib.md5(context_str.encode('utf-8')).hexdigest()[:8]
            
            return f"{strategy_name}_{content_hash}_{context_hash}"
            
        except Exception:
            # 如果生成失败，返回一个基于时间的键（不会命中缓存）
            return f"nocache_{time.time()}"
    
    def _cache_result(self, cache_key: str, result: QualityMetrics) -> None:
        """缓存评估结果"""
        try:
            # 如果缓存已满，移除最旧的条目
            if len(self._cache) >= self.cache_size:
                oldest_key = self._cache_access_order.pop(0)
                del self._cache[oldest_key]
            
            self._cache[cache_key] = result
            self._cache_access_order.append(cache_key)
            
        except Exception as e:
            self.logger.warning(f"缓存结果失败: {e}")
    
    def _update_cache_access(self, cache_key: str) -> None:
        """更新缓存访问顺序"""
        try:
            if cache_key in self._cache_access_order:
                self._cache_access_order.remove(cache_key)
                self._cache_access_order.append(cache_key)
            
            # 更新缓存统计
            self._cache_hits = getattr(self, '_cache_hits', 0) + 1
            self._cache_requests = getattr(self, '_cache_requests', 0) + 1
            
        except Exception as e:
            self.logger.warning(f"更新缓存访问失败: {e}")
