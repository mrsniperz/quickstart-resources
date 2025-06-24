"""
模块名称: quality
功能描述: 简化的分块质量评估模块，专注于基本的长度和完整性检查
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0 (简化版)

重构说明：
- 移除复杂的多策略架构
- 简化为基本的长度和完整性检查
- 提供3个预设配置：'basic'、'strict'、'disabled'
- 大幅减少代码复杂度，提升性能

使用示例：
    from chunking.quality import QualityAssessmentManager

    # 使用预设配置创建管理器
    manager = QualityAssessmentManager('basic')  # 或 'strict', 'disabled'

    # 评估分块质量
    metrics = manager.assess_chunk_quality(chunk)
"""

from .base import QualityMetrics, QualityAssessmentStrategy, BaseQualityAssessment
from .manager import QualityAssessmentManager
from .config_simplified import (
    SimplifiedQualityConfig,
    QualityPreset,
    get_default_config,
    get_all_presets
)

# 向后兼容的别名
QualityConfigBuilder = SimplifiedQualityConfig

__all__ = [
    'QualityMetrics',
    'QualityAssessmentStrategy',
    'BaseQualityAssessment',
    'QualityAssessmentManager',
    'SimplifiedQualityConfig',
    'QualityPreset',
    'get_default_config',
    'get_all_presets',
    'QualityConfigBuilder'  # 向后兼容
]

__version__ = "2.0.0"
