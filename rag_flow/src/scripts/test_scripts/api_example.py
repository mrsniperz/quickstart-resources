#!/usr/bin/env python3
"""
基于现有测试脚本的API接口示例

展示如何直接复用 test_chunking_complete.py 中的代码来构建Web API

依赖安装:
    pip install fastapi uvicorn pydantic

运行方式:
    uvicorn api_example:app --reload --port 8000

测试接口:
    curl -X POST "http://localhost:8000/chunk" \
         -H "Content-Type: application/json" \
         -d '{"text": "第一段。第二段！第三段？", "chunk_size": 20}'
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import sys
import os
from pathlib import Path

# 添加项目路径，直接导入现有的测试脚本组件
sys.path.insert(0, str(Path(__file__).parent))

try:
    # 直接复用现有的核心组件
    from test_chunking_complete import SafeChunkingEngine, ChunkingTester
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保 test_chunking_complete.py 在同一目录下")
    sys.exit(1)

# FastAPI 应用实例
app = FastAPI(
    title="RAG Flow 文档分块 API",
    description="基于 RecursiveCharacterChunker 的文档分块服务",
    version="1.0.0"
)

# 请求模型 - 直接对应命令行参数
class ChunkingRequest(BaseModel):
    """分块请求模型"""
    text: str = Field(..., description="待分块的文本内容", example="第一段内容。第二段内容！第三段内容？")
    
    # 基础分块参数
    chunk_size: int = Field(1000, ge=1, le=10000, description="分块大小（字符数）")
    chunk_overlap: int = Field(200, ge=0, description="重叠大小（字符数）")
    min_chunk_size: int = Field(100, ge=1, description="最小分块大小")
    max_chunk_size: int = Field(2000, ge=1, description="最大分块大小")
    
    # RecursiveCharacterChunker 特有参数
    separators: Optional[List[str]] = Field(None, description="自定义分隔符列表", example=["。", "！", "？"])
    is_separator_regex: bool = Field(False, description="分隔符是否为正则表达式")
    keep_separator: bool = Field(True, description="是否保留分隔符")
    add_start_index: bool = Field(False, description="是否添加起始索引")
    strip_whitespace: bool = Field(True, description="是否去除空白字符")
    
    # 输出控制
    include_statistics: bool = Field(True, description="是否包含统计信息")

# 响应模型
class ChunkInfo(BaseModel):
    """单个分块信息"""
    content: str = Field(..., description="分块内容")
    character_count: int = Field(..., description="字符数")
    word_count: int = Field(..., description="词数")
    quality_score: float = Field(..., description="质量评分")
    overlap_content: Optional[str] = Field(None, description="重叠内容")
    metadata: Dict[str, Any] = Field(..., description="元数据")

class Statistics(BaseModel):
    """统计信息"""
    chunk_count: int = Field(..., description="分块数量")
    total_characters: int = Field(..., description="总字符数")
    average_chunk_size: float = Field(..., description="平均分块大小")
    min_chunk_size: int = Field(..., description="最小分块大小")
    max_chunk_size: int = Field(..., description="最大分块大小")
    processing_speed: float = Field(..., description="处理速度（字符/秒）")
    coverage_rate: float = Field(..., description="覆盖率（%）")

class ChunkingResponse(BaseModel):
    """分块响应模型"""
    success: bool = Field(..., description="处理是否成功")
    chunks: List[ChunkInfo] = Field(..., description="分块结果列表")
    statistics: Optional[Statistics] = Field(None, description="统计信息")
    processing_time: float = Field(..., description="处理时间（秒）")
    strategy_used: str = Field(..., description="使用的分块策略")
    message: Optional[str] = Field(None, description="处理消息")

# 错误响应模型
class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="处理是否成功")
    error: str = Field(..., description="错误信息")
    error_type: str = Field(..., description="错误类型")

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": "RAG Flow 文档分块 API",
        "version": "1.0.0",
        "description": "基于 RecursiveCharacterChunker 的文档分块服务",
        "endpoints": {
            "POST /chunk": "执行文档分块",
            "GET /strategies": "获取可用策略列表",
            "GET /separators": "获取默认分隔符列表",
            "GET /health": "健康检查"
        }
    }

@app.post("/chunk", response_model=ChunkingResponse, responses={400: {"model": ErrorResponse}})
async def chunk_text(request: ChunkingRequest):
    """
    执行文档分块
    
    直接复用 test_chunking_complete.py 中的核心逻辑
    """
    try:
        # 构建配置 - 直接对应命令行参数处理逻辑
        config = {
            'chunk_size': request.chunk_size,
            'chunk_overlap': request.chunk_overlap,
            'min_chunk_size': request.min_chunk_size,
            'max_chunk_size': request.max_chunk_size,
            'preserve_context': True
        }
        
        # 添加 RecursiveCharacterChunker 特有配置
        if request.separators:
            config['separators'] = request.separators
        if request.is_separator_regex:
            config['is_separator_regex'] = True
        if not request.keep_separator:
            config['keep_separator'] = False
        if request.add_start_index:
            config['add_start_index'] = True
        if not request.strip_whitespace:
            config['strip_whitespace'] = False
        
        # 直接复用现有的测试器
        tester = ChunkingTester(config)
        
        # 构建元数据
        metadata = {
            'file_name': 'api_input.txt',
            'document_type': 'api_input',
            'title': 'API输入文档'
        }
        
        # 执行分块 - 直接使用现有方法
        result = tester.test_chunking(request.text, metadata)
        
        # 转换分块结果为API响应格式
        chunks = []
        for chunk in result['chunks']:
            if isinstance(chunk, dict):
                chunk_info = ChunkInfo(
                    content=chunk.get('content', ''),
                    character_count=chunk.get('character_count', 0),
                    word_count=chunk.get('word_count', 0),
                    quality_score=chunk.get('quality_score', 0.0),
                    overlap_content=chunk.get('overlap_content'),
                    metadata=chunk.get('metadata', {})
                )
            else:
                chunk_info = ChunkInfo(
                    content=getattr(chunk, 'content', ''),
                    character_count=getattr(chunk, 'character_count', 0),
                    word_count=getattr(chunk, 'word_count', 0),
                    quality_score=getattr(chunk, 'quality_score', 0.0),
                    overlap_content=getattr(chunk, 'overlap_content', None),
                    metadata=getattr(chunk, 'metadata', {})
                )
            chunks.append(chunk_info)
        
        # 构建响应
        response = ChunkingResponse(
            success=True,
            chunks=chunks,
            processing_time=result['processing_time'],
            strategy_used=result['strategy_used']
        )
        
        # 添加可选信息
        if request.include_statistics:
            response.statistics = Statistics(**result['statistics'])

        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=str(e),
                error_type=type(e).__name__
            ).dict()
        )

@app.get("/strategies")
async def get_strategies():
    """获取可用的分块策略列表"""
    try:
        # 直接复用现有的策略获取逻辑
        engine = SafeChunkingEngine()
        strategies = engine.get_available_strategies()
        
        strategy_info = {}
        for strategy in strategies:
            info = engine.get_strategy_info(strategy)
            strategy_info[strategy] = info
        
        return {
            "available_strategies": strategies,
            "strategy_details": strategy_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/separators")
async def get_default_separators():
    """获取默认分隔符列表"""
    # 直接复用现有的分隔符列表
    default_separators = [
        "\\n\\n", "\\n\\n\\n",
        "\\n第", "\\n章", "\\n节", "\\n条",
        "\\nChapter", "\\nSection", "\\nArticle",
        "\\n\\n•", "\\n\\n-", "\\n\\n*", "\\n\\n1.", "\\n\\n2.", "\\n\\n3.",
        "\\n",
        "。", "！", "？", ".", "!", "?",
        "；", ";", "，", ",",
        " ", "\\t",
        "、", "：", ":",
        "\\u200b", "\\uff0c", "\\u3001", "\\uff0e", "\\u3002",
        '""'
    ]
    
    return {
        "default_separators": default_separators,
        "categories": {
            "paragraph": ["\\n\\n", "\\n\\n\\n"],
            "chinese_section": ["\\n第", "\\n章", "\\n节", "\\n条"],
            "english_section": ["\\nChapter", "\\nSection", "\\nArticle"],
            "list": ["\\n\\n•", "\\n\\n-", "\\n\\n*"],
            "sentence": ["。", "！", "？", ".", "!", "?"],
            "clause": ["；", ";", "，", ","],
            "word": [" ", "\\t"],
            "special": ["、", "：", ":", "\\u200b"]
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 简单测试核心组件是否正常
        engine = SafeChunkingEngine()
        test_result = engine.chunk_document("测试", {"file_name": "health_check.txt"})
        
        return {
            "status": "healthy",
            "components": {
                "chunking_engine": "ok",
                "test_result": f"generated {len(test_result)} chunks"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动 RAG Flow 文档分块 API 服务")
    print("📖 API 文档: http://localhost:8000/docs")
    print("🔍 交互式文档: http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000)
