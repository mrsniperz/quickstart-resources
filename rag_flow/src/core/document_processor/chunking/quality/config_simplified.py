"""
模块名称: config_simplified
功能描述: 简化的质量评估配置系统
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0 (简化版)

重构说明:
- 移除复杂的QualityConfigBuilder
- 提供3个简单的预设配置：'basic'、'strict'、'disabled'
- 大幅简化配置选项
"""

from typing import Dict, Any, Optional
from enum import Enum


class QualityPreset(Enum):
    """质量评估预设配置枚举"""
    BASIC = "basic"
    STRICT = "strict"
    DISABLED = "disabled"


class SimplifiedQualityConfig:
    """
    简化的质量评估配置类
    
    提供3个预设配置，每个预设只包含必要的参数
    """
    
    # 预设配置定义
    PRESETS = {
        QualityPreset.BASIC: {
            'min_length': 50,
            'max_length': 2000,
            'optimal_length': 1000,
            'enable_quality_check': True,
            'length_weight': 0.6,
            'completeness_weight': 0.4,
            'description': '基础质量检查，适用于大多数场景'
        },
        QualityPreset.STRICT: {
            'min_length': 100,
            'max_length': 1500,
            'optimal_length': 800,
            'enable_quality_check': True,
            'length_weight': 0.5,
            'completeness_weight': 0.5,
            'description': '严格质量检查，要求更高的分块质量'
        },
        QualityPreset.DISABLED: {
            'min_length': 1,
            'max_length': 10000,
            'optimal_length': 1000,
            'enable_quality_check': False,
            'length_weight': 1.0,
            'completeness_weight': 0.0,
            'description': '禁用质量检查，所有分块都返回满分'
        }
    }
    
    def __init__(self, preset: QualityPreset = QualityPreset.BASIC):
        """
        初始化简化配置
        
        Args:
            preset: 预设配置类型
        """
        self.preset = preset
        self.config = self.PRESETS[preset].copy()
    
    @classmethod
    def from_preset(cls, preset_name: str) -> 'SimplifiedQualityConfig':
        """
        从预设名称创建配置
        
        Args:
            preset_name: 预设名称 ('basic', 'strict', 'disabled')
            
        Returns:
            SimplifiedQualityConfig: 配置实例
            
        Raises:
            ValueError: 当预设名称无效时
        """
        try:
            preset = QualityPreset(preset_name.lower())
            return cls(preset)
        except ValueError:
            raise ValueError(f"无效的预设名称: {preset_name}. 支持的预设: {list(QualityPreset)}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SimplifiedQualityConfig':
        """
        从字典创建配置（用于向后兼容）
        
        Args:
            config_dict: 配置字典
            
        Returns:
            SimplifiedQualityConfig: 配置实例
        """
        # 根据配置参数推断最接近的预设
        enable_check = config_dict.get('enable_quality_check', True)
        
        if not enable_check:
            instance = cls(QualityPreset.DISABLED)
        else:
            min_length = config_dict.get('min_length', 50)
            if min_length >= 100:
                instance = cls(QualityPreset.STRICT)
            else:
                instance = cls(QualityPreset.BASIC)
        
        # 应用自定义配置覆盖
        for key, value in config_dict.items():
            if key in instance.config:
                instance.config[key] = value
        
        return instance
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取配置字典
        
        Returns:
            Dict[str, Any]: 配置参数字典
        """
        return self.config.copy()
    
    def update_config(self, **kwargs) -> None:
        """
        更新配置参数
        
        Args:
            **kwargs: 要更新的配置参数
        """
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
            else:
                raise ValueError(f"不支持的配置参数: {key}")
    
    def validate_config(self) -> bool:
        """
        验证配置参数的有效性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查长度参数
            if self.config['min_length'] < 1:
                return False
            if self.config['max_length'] <= self.config['min_length']:
                return False
            if self.config['optimal_length'] < self.config['min_length']:
                return False
            if self.config['optimal_length'] > self.config['max_length']:
                return False
            
            # 检查权重参数
            if not (0.0 <= self.config['length_weight'] <= 1.0):
                return False
            if not (0.0 <= self.config['completeness_weight'] <= 1.0):
                return False
            
            # 检查权重总和（允许一定误差）
            total_weight = self.config['length_weight'] + self.config['completeness_weight']
            if abs(total_weight - 1.0) > 0.1:
                return False
            
            return True
            
        except (KeyError, TypeError):
            return False
    
    def get_description(self) -> str:
        """
        获取配置描述
        
        Returns:
            str: 配置描述
        """
        return self.config.get('description', f'{self.preset.value} 配置')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式（用于序列化）
        
        Returns:
            Dict[str, Any]: 包含预设和配置的字典
        """
        return {
            'preset': self.preset.value,
            'config': self.config
        }
    
    @classmethod
    def from_serialized(cls, data: Dict[str, Any]) -> 'SimplifiedQualityConfig':
        """
        从序列化数据恢复配置
        
        Args:
            data: 序列化的配置数据
            
        Returns:
            SimplifiedQualityConfig: 配置实例
        """
        preset = QualityPreset(data['preset'])
        instance = cls(preset)
        instance.config.update(data['config'])
        return instance
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SimplifiedQualityConfig(preset={self.preset.value}, enabled={self.config['enable_quality_check']})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"SimplifiedQualityConfig(preset={self.preset.value}, config={self.config})"


def get_default_config() -> SimplifiedQualityConfig:
    """
    获取默认配置
    
    Returns:
        SimplifiedQualityConfig: 默认的基础配置
    """
    return SimplifiedQualityConfig(QualityPreset.BASIC)


def get_all_presets() -> Dict[str, Dict[str, Any]]:
    """
    获取所有可用的预设配置
    
    Returns:
        Dict[str, Dict[str, Any]]: 所有预设配置的字典
    """
    return {preset.value: config for preset, config in SimplifiedQualityConfig.PRESETS.items()}

