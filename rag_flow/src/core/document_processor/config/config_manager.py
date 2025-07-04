"""
模块名称: config_manager
功能描述: 配置管理器，负责加载和管理Docling文档处理器的配置
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None, chunking_config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path (str, optional): 主配置文件路径
            chunking_config_path (str, optional): 分块配置文件路径
        """
        self.logger = logger
        self.config_path = config_path or self._get_default_config_path()
        self.chunking_config_path = chunking_config_path or self._get_chunking_config_path()
        self.config = {}
        self.chunking_config = {}
        self._load_config()
        self._load_chunking_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 尝试多个可能的配置文件位置
        possible_paths = [
            os.environ.get('DOCLING_CONFIG_PATH'),
            './config/docling_config.yaml',
            './docling_config.yaml',
            str(Path(__file__).parent / 'docling_config.yaml'),
        ]

        for path in possible_paths:
            if path and Path(path).exists():
                return path

        # 如果都不存在，返回默认路径
        return './config/docling_config.yaml'

    def _get_chunking_config_path(self) -> str:
        """获取chunking配置文件路径"""
        # 尝试多个可能的配置文件位置
        possible_paths = [
            os.environ.get('CHUNKING_CONFIG_PATH'),
            './config/chunking_config.yaml',
            './chunking_config.yaml',
            str(Path(__file__).parent / 'chunking_config.yaml'),
        ]

        for path in possible_paths:
            if path and Path(path).exists():
                return path

        # 如果都不存在，返回默认路径
        return str(Path(__file__).parent / 'chunking_config.yaml')
    
    def _load_config(self):
        """加载主配置文件"""
        try:
            if not Path(self.config_path).exists():
                self.logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self.config = self._get_default_config()
                return

            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    self.config = yaml.safe_load(f)
                elif self.config_path.endswith('.json'):
                    self.config = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.config_path}")

            self.logger.info(f"配置文件加载成功: {self.config_path}")

        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            self.config = self._get_default_config()

    def _load_chunking_config(self):
        """加载分块配置文件"""
        try:
            if not Path(self.chunking_config_path).exists():
                self.logger.warning(f"分块配置文件不存在: {self.chunking_config_path}，使用默认配置")
                self.chunking_config = self._get_default_chunking_config()
                return

            with open(self.chunking_config_path, 'r', encoding='utf-8') as f:
                if self.chunking_config_path.endswith('.yaml') or self.chunking_config_path.endswith('.yml'):
                    self.chunking_config = yaml.safe_load(f)
                elif self.chunking_config_path.endswith('.json'):
                    self.chunking_config = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.chunking_config_path}")

            self.logger.info(f"分块配置文件加载成功: {self.chunking_config_path}")

        except Exception as e:
            self.logger.error(f"分块配置文件加载失败: {e}")
            self.chunking_config = self._get_default_chunking_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'global': {
                'use_docling': True,
                'prefer_docling_for_common_formats': False,
                'log_level': 'INFO',
                'max_concurrent_processes': 4
            },
            'docling': {
                'ocr': {
                    'enabled': True,
                    'engine': 'easyocr',
                    'languages': ['zh', 'en']
                },
                'table_structure': {
                    'enabled': True,
                    'mode': 'accurate'
                },
                'image_processing': {
                    'generate_images': True,
                    'scale': 2,
                    'enable_description': False
                },
                'formula': {
                    'enabled': True,
                    'output_format': 'latex'
                },
                'code': {
                    'enabled': True,
                    'auto_detect_language': True
                },
                'limits': {
                    'max_pages': None,
                    'max_file_size': 104857600,  # 100MB
                    'timeout': 300
                },
                'models': {
                    'artifacts_path': None,
                    'enable_remote_services': False
                }
            },
            'output': {
                'default_format': 'markdown',
                'markdown': {
                    'table_format': 'github',
                    'code_language_detection': True,
                    'image_placeholder': '![图片]({image_path})'
                }
            },
            'error_handling': {
                'continue_on_error': True,
                'retry': {
                    'max_attempts': 3,
                    'delay_seconds': 1,
                    'backoff_factor': 2
                },
                'log_errors': True
            }
        }

    def _get_default_chunking_config(self) -> Dict[str, Any]:
        """获取默认分块配置"""
        return {
            'global': {
                'default_strategy': 'recursive',
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'min_chunk_size': 100,
                'max_chunk_size': 2000,
                'preserve_context': True,
                'enable_quality_assessment': True,
                'quality_strategy': 'aviation'
            },
            'recursive': {
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'is_separator_regex': False,
                'keep_separator': True,
                'add_start_index': False,
                'strip_whitespace': True,
                'separators': [
                    "\n\n", "\n\n\n",
                    "\n第", "\n章", "\n节", "\n条",
                    "\nChapter", "\nSection", "\nArticle",
                    "\n\n•", "\n\n-", "\n\n*", "\n\n1.", "\n\n2.", "\n\n3.",
                    "\n",
                    "。", "！", "？", ".", "!", "?",
                    "；", ";", "，", ",",
                    " ", "\t",
                    "、", "：", ":",
                    "\u200b", "\uff0c", "\u3001", "\uff0e", "\u3002",
                    ""
                ]
            },
            'semantic': {
                'target_chunk_size': 800,
                'min_chunk_size': 200,
                'max_chunk_size': 1500,
                'similarity_threshold': 0.7,
                'sentence_overlap': 1
            },
            'structure': {
                'respect_page_breaks': True,
                'merge_short_sections': True,
                'min_section_size': 300,
                'preserve_tables': True,
                'preserve_lists': True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key (str): 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key (str): 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        try:
            keys = key.split('.')
            config = self.config
            
            # 导航到最后一级的父级
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            
        except Exception as e:
            self.logger.error(f"设置配置失败: {e}")
    
    def get_docling_config(self) -> Dict[str, Any]:
        """获取Docling解析器配置"""
        docling_config = self.get('docling', {})
        
        # 转换为DoclingParser期望的格式
        return {
            'enable_ocr': docling_config.get('ocr', {}).get('enabled', True),
            'enable_table_structure': docling_config.get('table_structure', {}).get('enabled', True),
            'enable_picture_description': docling_config.get('image_processing', {}).get('enable_description', False),
            'enable_formula_enrichment': docling_config.get('formula', {}).get('enabled', True),
            'enable_code_enrichment': docling_config.get('code', {}).get('enabled', True),
            'generate_picture_images': docling_config.get('image_processing', {}).get('generate_images', True),
            'images_scale': docling_config.get('image_processing', {}).get('scale', 2),
            'max_num_pages': docling_config.get('limits', {}).get('max_pages'),
            'max_file_size': docling_config.get('limits', {}).get('max_file_size'),
            'artifacts_path': docling_config.get('models', {}).get('artifacts_path'),
            'enable_remote_services': docling_config.get('models', {}).get('enable_remote_services', False)
        }
    
    def get_document_processor_config(self) -> Dict[str, Any]:
        """获取统一文档处理器配置"""
        return {
            'use_docling': self.get('global.use_docling', True),
            'prefer_docling_for_common_formats': self.get('global.prefer_docling_for_common_formats', False),
            'docling_config': self.get_docling_config(),
            'pdf_config': self.get('traditional_parsers.pdf', {}),
            'word_config': self.get('traditional_parsers.word', {}),
            'excel_config': self.get('traditional_parsers.excel', {}),
            'powerpoint_config': self.get('traditional_parsers.powerpoint', {})
        }

    def get_chunking_config(self, strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        获取分块配置

        Args:
            strategy (str, optional): 分块策略名称，如果不指定则返回全局配置
                                     如果是'presets'，则返回预设配置部分

        Returns:
            dict: 分块配置
        """
        if strategy == 'presets':
            # 获取预设配置
            return self.chunking_config.get('presets', {})
            
        elif strategy:
            # 获取特定策略的配置
            strategy_config = self.chunking_config.get(strategy, {})
            global_config = self.chunking_config.get('global', {})

            # 合并全局配置和策略特定配置
            merged_config = global_config.copy()
            merged_config.update(strategy_config)

            return merged_config
        else:
            # 返回完整的分块配置
            return self.chunking_config.copy()

    def get_chunking_separators(self, strategy: str = 'recursive') -> List[str]:
        """
        获取指定策略的分隔符列表

        Args:
            strategy (str): 分块策略名称

        Returns:
            list: 分隔符列表
        """
        strategy_config = self.chunking_config.get(strategy, {})
        return strategy_config.get('separators', [])

    def get_chunking_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        获取预设配置

        Args:
            preset_name (str): 预设名称

        Returns:
            dict: 预设配置
        """
        presets = self.chunking_config.get('presets', {})
        return presets.get(preset_name, {})
    
    def save_config(self, output_path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            output_path (str, optional): 输出文件路径
        """
        try:
            output_path = output_path or self.config_path
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if output_path.endswith('.yaml') or output_path.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                elif output_path.endswith('.json'):
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"不支持的配置文件格式: {output_path}")
            
            self.logger.info(f"配置文件保存成功: {output_path}")
            
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
            raise
    
    def reload_config(self):
        """重新加载配置文件"""
        self._load_config()
        self._load_chunking_config()
        self.logger.info("配置文件已重新加载")
    
    def validate_config(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查必需的配置项
            required_keys = [
                'global.use_docling',
                'docling.ocr.enabled',
                'docling.table_structure.enabled'
            ]
            
            for key in required_keys:
                if self.get(key) is None:
                    self.logger.error(f"缺少必需的配置项: {key}")
                    return False
            
            # 检查数值范围
            max_file_size = self.get('docling.limits.max_file_size')
            if max_file_size is not None and max_file_size <= 0:
                self.logger.error("max_file_size必须大于0")
                return False
            
            images_scale = self.get('docling.image_processing.scale', 2)
            if not isinstance(images_scale, (int, float)) or images_scale <= 0:
                self.logger.error("images_scale必须是正数")
                return False
            
            self.logger.info("配置验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            return False
    
    def get_environment_overrides(self) -> Dict[str, Any]:
        """获取环境变量覆盖的配置"""
        overrides = {}
        
        # 定义环境变量映射
        env_mappings = {
            'DOCLING_USE_DOCLING': 'global.use_docling',
            'DOCLING_LOG_LEVEL': 'global.log_level',
            'DOCLING_ENABLE_OCR': 'docling.ocr.enabled',
            'DOCLING_ENABLE_TABLE_STRUCTURE': 'docling.table_structure.enabled',
            'DOCLING_MAX_FILE_SIZE': 'docling.limits.max_file_size',
            'DOCLING_ARTIFACTS_PATH': 'docling.models.artifacts_path',
            'DOCLING_ENABLE_REMOTE_SERVICES': 'docling.models.enable_remote_services'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # 类型转换
                if env_value.lower() in ('true', 'false'):
                    env_value = env_value.lower() == 'true'
                elif env_value.isdigit():
                    env_value = int(env_value)
                
                overrides[config_key] = env_value
        
        return overrides
    
    def apply_environment_overrides(self):
        """应用环境变量覆盖"""
        overrides = self.get_environment_overrides()
        
        for key, value in overrides.items():
            self.set(key, value)
            self.logger.info(f"环境变量覆盖配置: {key} = {value}")


# 全局配置管理器实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.apply_environment_overrides()
    return _config_manager

def get_config(key: str, default: Any = None) -> Any:
    """快捷方式：获取配置值"""
    return get_config_manager().get(key, default)

def set_config(key: str, value: Any):
    """快捷方式：设置配置值"""
    get_config_manager().set(key, value)
