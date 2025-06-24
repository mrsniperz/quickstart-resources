"""
模块名称: document_processor
功能描述: 航空RAG系统文档预处理模块，提供多格式文档解析、智能分块、内容提取等功能
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)

# 动态构建__all__列表
__all__ = []

# 尝试导入分块模块（通常不依赖外部库）
try:
    from .chunking import *
    CHUNKING_AVAILABLE = True
    logger.info("分块模块导入成功")
    __all__.extend([
        'ChunkingEngine',
        'AviationChunkingStrategy',
        'SemanticChunker',
        'StructureChunker',
    ])
except ImportError as e:
    CHUNKING_AVAILABLE = False
    logger.warning(f"分块模块导入失败: {e}")
except Exception as e:
    CHUNKING_AVAILABLE = False
    logger.warning(f"分块模块导入异常: {e}")

# 尝试导入解析器模块（可能依赖外部库）
try:
    from .parsers import *
    PARSERS_AVAILABLE = True
    logger.info("解析器模块导入成功")
    __all__.extend([
        'PDFParser',
        'WordParser',
        'ExcelParser',
        'PowerPointParser',
        'DocumentProcessor',
    ])
except ImportError as e:
    PARSERS_AVAILABLE = False
    logger.warning(f"解析器模块导入失败，部分文档格式将不支持: {e}")
except Exception as e:
    PARSERS_AVAILABLE = False
    logger.warning(f"解析器模块导入异常: {e}")

# 尝试导入提取器模块
try:
    from .extractors import *
    EXTRACTORS_AVAILABLE = True
    logger.info("提取器模块导入成功")
    __all__.extend([
        'MetadataExtractor',
        'TableExtractor',
        'ImageExtractor',
    ])
except ImportError as e:
    EXTRACTORS_AVAILABLE = False
    logger.warning(f"提取器模块导入失败: {e}")
except Exception as e:
    EXTRACTORS_AVAILABLE = False
    logger.warning(f"提取器模块导入异常: {e}")

# 验证器模块已移除
VALIDATORS_AVAILABLE = False

# 提供可用性检查函数
def is_chunking_available() -> bool:
    """检查分块模块是否可用"""
    return CHUNKING_AVAILABLE

def is_parsers_available() -> bool:
    """检查解析器模块是否可用"""
    return PARSERS_AVAILABLE

def is_extractors_available() -> bool:
    """检查提取器模块是否可用"""
    return EXTRACTORS_AVAILABLE



def get_available_modules() -> dict:
    """获取可用模块信息"""
    return {
        'chunking': CHUNKING_AVAILABLE,
        'parsers': PARSERS_AVAILABLE,
        'extractors': EXTRACTORS_AVAILABLE
    }
