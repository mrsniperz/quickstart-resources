# API 开发参数映射表

## 概述

本文档提供了将现有测试脚本转换为API接口时的完整参数映射关系，方便直接复用现有代码。

## 核心组件复用映射

### 1. 命令行参数 → API 请求参数

| 命令行参数 | API字段名 | 数据类型 | 默认值 | 验证规则 | 说明 |
|------------|-----------|----------|--------|----------|------|
| `--text` | `text` | string | - | required | 待分块文本 |
| `--chunk-size` | `chunk_size` | integer | 1000 | 1-10000 | 分块大小 |
| `--chunk-overlap` | `chunk_overlap` | integer | 200 | ≥0 | 重叠大小 |
| `--min-chunk-size` | `min_chunk_size` | integer | 100 | ≥1 | 最小分块 |
| `--max-chunk-size` | `max_chunk_size` | integer | 2000 | ≥1 | 最大分块 |
| `--separators` | `separators` | array[string] | null | - | 分隔符列表 |
| `--is-separator-regex` | `is_separator_regex` | boolean | false | - | 正则模式 |
| `--keep-separator` | `keep_separator` | boolean | true | - | 保留分隔符 |
| `--no-keep-separator` | `keep_separator` | boolean | false | - | 不保留分隔符 |
| `--add-start-index` | `add_start_index` | boolean | false | - | 添加索引 |
| `--no-strip-whitespace` | `strip_whitespace` | boolean | false | - | 空白处理 |

### 2. 配置对象构建映射

```python
# 命令行参数处理逻辑 → API配置构建
def build_config_from_api_request(request):
    config = {
        'chunk_size': request.chunk_size,
        'chunk_overlap': request.chunk_overlap,
        'min_chunk_size': request.min_chunk_size,
        'max_chunk_size': request.max_chunk_size,
        'preserve_context': True
    }
    
    # RecursiveCharacterChunker 特有配置
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
    
    return config
```

### 3. 响应数据映射

| 测试脚本输出 | API响应字段 | 数据类型 | 说明 |
|-------------|-------------|----------|------|
| `result['chunks']` | `chunks` | array[object] | 分块结果列表 |
| `result['statistics']` | `statistics` | object | 统计信息 |
| `result['validation']` | `validation` | object | 验证信息 |
| `result['processing_time']` | `processing_time` | float | 处理时间 |
| `result['strategy_used']` | `strategy_used` | string | 使用策略 |

## 直接复用的代码组件

### 1. SafeChunkingEngine 类

```python
# 位置: test_chunking_complete.py 第 52-180 行
# 功能: 智能依赖处理、自动降级、完整参数支持
# 复用方式: 直接导入使用

from test_chunking_complete import SafeChunkingEngine

# API中的使用
engine = SafeChunkingEngine(config)
chunks = engine.chunk_document(text, metadata)
```

### 2. ChunkingTester 类

```python
# 位置: test_chunking_complete.py 第 182-300 行
# 功能: 分块测试、统计计算、结果验证
# 复用方式: 提取核心方法

from test_chunking_complete import ChunkingTester

# API中的使用
tester = ChunkingTester(config)
result = tester.test_chunking(text, metadata)
```

### 3. 配置处理逻辑

```python
# 位置: test_chunking_complete.py 第 887-905 行
# 功能: 命令行参数到配置对象的转换
# 复用方式: 直接复制逻辑

# 原始代码
config = {
    'chunk_size': args.chunk_size,
    'chunk_overlap': args.chunk_overlap,
    # ... 其他配置
}

# API适配
config = {
    'chunk_size': request.chunk_size,
    'chunk_overlap': request.chunk_overlap,
    # ... 其他配置
}
```

## API 接口设计模板

### 1. FastAPI 接口模板

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from test_chunking_complete import ChunkingTester

class ChunkingRequest(BaseModel):
    text: str
    chunk_size: int = 1000
    chunk_overlap: int = 200
    # ... 其他参数

@app.post("/chunk")
async def chunk_text(request: ChunkingRequest):
    config = build_config_from_request(request)
    tester = ChunkingTester(config)
    result = tester.test_chunking(request.text, metadata)
    return format_response(result)
```

### 2. Flask 接口模板

```python
from flask import Flask, request, jsonify
from test_chunking_complete import SafeChunkingEngine

@app.route('/chunk', methods=['POST'])
def chunk_text():
    data = request.json
    config = {k: v for k, v in data.items() if k != 'text'}
    
    engine = SafeChunkingEngine(config)
    chunks = engine.chunk_document(data['text'], metadata)
    
    return jsonify({'chunks': chunks})
```

## 错误处理映射

### 1. 异常类型映射

| 测试脚本异常 | HTTP状态码 | API错误类型 | 处理方式 |
|-------------|------------|-------------|----------|
| `ImportError` | 500 | `DEPENDENCY_ERROR` | 服务不可用 |
| `ValueError` | 400 | `INVALID_PARAMETER` | 参数验证失败 |
| `Exception` | 500 | `PROCESSING_ERROR` | 处理异常 |

### 2. 错误响应格式

```python
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_type: str
    details: Optional[Dict] = None

# 使用示例
try:
    result = tester.test_chunking(text, metadata)
except ValueError as e:
    raise HTTPException(
        status_code=400,
        detail=ErrorResponse(
            error=str(e),
            error_type="INVALID_PARAMETER"
        ).dict()
    )
```

## 性能优化建议

### 1. 缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_chunks(text_hash, config_hash):
    # 缓存相同输入的分块结果
    pass
```

### 2. 异步处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def chunk_text_async(text, config):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor, 
            lambda: tester.test_chunking(text, metadata)
        )
    return result
```

### 3. 批量处理

```python
@app.post("/chunk/batch")
async def chunk_batch(requests: List[ChunkingRequest]):
    results = []
    for req in requests:
        result = await chunk_text_async(req.text, build_config(req))
        results.append(result)
    return results
```

## 部署配置

### 1. Docker 配置

```dockerfile
FROM python:3.9-slim

COPY test_chunking_complete.py /app/
COPY api_example.py /app/
COPY requirements.txt /app/

RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "api_example:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 环境变量配置

```python
import os

DEFAULT_CHUNK_SIZE = int(os.getenv('DEFAULT_CHUNK_SIZE', 1000))
DEFAULT_CHUNK_OVERLAP = int(os.getenv('DEFAULT_CHUNK_OVERLAP', 200))
MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 100000))
```

## 监控和日志

### 1. 日志配置

```python
# 复用现有的日志配置
from test_chunking_complete import USE_CUSTOM_LOGGER, SZ_LoggerManager

if USE_CUSTOM_LOGGER:
    logger = SZ_LoggerManager.setup_logger("api_service")
else:
    import logging
    logger = logging.getLogger("api_service")
```

### 2. 性能监控

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        processing_time = time.time() - start_time
        
        logger.info(f"API call completed in {processing_time:.3f}s")
        return result
    return wrapper
```

## 总结

通过以上映射表和模板，您可以：

1. **零重构复用**：直接使用现有的 `SafeChunkingEngine` 和 `ChunkingTester` 类
2. **参数映射**：按照表格直接映射命令行参数到API参数
3. **配置构建**：复用现有的配置处理逻辑
4. **错误处理**：使用现有的异常处理机制
5. **快速部署**：基于提供的模板快速构建API服务

现有代码的设计已经考虑了接口化的需求，可以直接用于生产环境的API开发。
