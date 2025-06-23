"""
模块名称: core
功能描述: 航空RAG系统核心业务模块，包含Milvus向量数据库操作、文档处理、检索服务等核心功能
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0

使用说明:
    # 推荐的导入方式（明确且可靠）
    from core.document_processor.chunking.chunking_engine import ChunkingEngine
    from core.document_processor.chunking.recursive_chunker import RecursiveCharacterChunker

    # 可选功能的导入方式
    try:
        from core.milvus.collection_manager import MilvusCollectionManager
    except ImportError:
        print("Milvus功能需要安装pymilvus: pip install pymilvus")
"""

# 为了避免依赖问题，这里不进行任何导入
# 用户应该直接从具体模块导入所需的类和函数

# 提供便利函数来检查模块可用性
def check_milvus_availability():
    """检查Milvus模块是否可用"""
    try:
        import pymilvus
        return True
    except ImportError:
        return False

def check_document_parsers_availability():
    """检查文档解析器是否可用"""
    availability = {}

    # 检查PDF解析器
    try:
        import fitz  # PyMuPDF
        availability['pdf'] = True
    except ImportError:
        availability['pdf'] = False

    # 检查Word解析器
    try:
        import docx
        availability['word'] = True
    except ImportError:
        availability['word'] = False

    # 检查Excel解析器
    try:
        import openpyxl
        availability['excel'] = True
    except ImportError:
        availability['excel'] = False

    return availability

def get_system_status():
    """获取系统各模块状态"""
    return {
        'milvus_available': check_milvus_availability(),
        'document_parsers': check_document_parsers_availability(),
        'chunking_available': True,  # 分块功能不依赖外部库
    }