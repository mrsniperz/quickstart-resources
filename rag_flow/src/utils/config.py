"""
配置加载工具

此模块提供配置文件的加载和访问功能。
"""

import os
import yaml
from typing import Dict, Any, Optional


class Config:
    """
    配置管理类
    
    用于加载和访问配置文件中的配置项
    """
    
    _instance = None
    _config_data = {}
    
    def __new__(cls, *args, **kwargs):
        """
        单例模式实现
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path (str, optional): 配置文件路径，默认为None，会使用默认路径
        """
        if not self._config_data:
            if config_path is None:
                # 默认配置文件路径
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                config_path = os.path.join(base_dir, 'config', 'config.yaml')
            
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> None:
        """
        加载配置文件
        
        Args:
            config_path (str): 配置文件路径
        
        Raises:
            FileNotFoundError: 配置文件不存在时抛出
            yaml.YAMLError: YAML解析错误时抛出
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"配置文件不存在: {config_path}")
            self._config_data = {}
        except yaml.YAMLError as e:
            print(f"配置文件解析错误: {e}")
            self._config_data = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key (str): 配置项键，支持点号分隔的多级键，如 "app.debug"
            default (Any, optional): 默认值，当配置项不存在时返回，默认为None
        
        Returns:
            Any: 配置项值
        """
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key (str): 配置项键，支持点号分隔的多级键，如 "app.debug"
            value (Any): 配置项值
        """
        keys = key.split('.')
        config = self._config_data
        
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置项
        
        Returns:
            Dict[str, Any]: 所有配置项
        """
        return self._config_data


# 创建全局配置实例
config = Config()


def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置项的便捷函数
    
    Args:
        key (str): 配置项键，支持点号分隔的多级键，如 "app.debug"
        default (Any, optional): 默认值，当配置项不存在时返回，默认为None
    
    Returns:
        Any: 配置项值
    """
    return config.get(key, default) 