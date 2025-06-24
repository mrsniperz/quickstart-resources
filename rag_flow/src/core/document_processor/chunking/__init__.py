"""
模块名称: chunking
功能描述: 简化的智能分块引擎，基于配置预设提供统一的分块处理功能
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0 (简化重构版)
"""

from .chunking_engine import ChunkingEngine
from .recursive_chunker import RecursiveCharacterChunker

__all__ = [
    'ChunkingEngine',
    'RecursiveCharacterChunker',
]
