# RAG Flow API 接口文档

## API 概述

RAG Flow 提供了完整的 RESTful API 接口，支持文档处理、向量检索、知识问答等核心功能。API 设计遵循 REST 规范，使用 JSON 格式进行数据交换。

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **认证方式**: Bearer Token
- **API 版本**: v1.0.0

## 认证

### 获取访问令牌

```http
POST /auth/token
Content-Type: application/json

{
    "username": "admin",
    "password": "password"
}
```

**响应示例**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### 使用令牌

在请求头中添加认证信息：
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 文档处理 API

### 1. 上传并解析文档

**接口**: `POST /documents/parse`

**描述**: 上传文档文件并进行解析处理

**请求参数**:
```http
POST /documents/parse
Content-Type: multipart/form-data

file: <文档文件>
config: {
    "use_docling": true,
    "enable_ocr": true,
    "enable_table_structure": true,
    "chunking_strategy": "aviation"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "document_id": "doc_123456",
        "document_type": "pdf",
        "metadata": {
            "title": "航空维修手册",
            "author": "航空公司",
            "page_count": 150,
            "file_size": 2048576
        },
        "processing_stats": {
            "total_chunks": 45,
            "processing_time": 12.5,
            "quality_score": 0.85
        }
    },
    "message": "文档解析成功"
}
```

### 2. 获取文档信息

**接口**: `GET /documents/{document_id}`

**描述**: 获取指定文档的详细信息

**请求示例**:
```http
GET /documents/doc_123456
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "document_id": "doc_123456",
        "title": "航空维修手册",
        "document_type": "maintenance_manual",
        "status": "processed",
        "metadata": {
            "author": "航空公司",
            "page_count": 150,
            "create_time": "2024-01-15T10:30:00Z",
            "update_time": "2024-01-15T10:45:00Z"
        },
        "chunks": [
            {
                "chunk_id": "chunk_001",
                "content": "第一章 安全检查...",
                "start_position": 0,
                "end_position": 500,
                "quality_score": 0.9
            }
        ]
    }
}
```

### 3. 批量处理文档

**接口**: `POST /documents/batch-parse`

**描述**: 批量上传和处理多个文档

**请求参数**:
```http
POST /documents/batch-parse
Content-Type: multipart/form-data

files: [<文档文件1>, <文档文件2>, ...]
config: {
    "use_docling": true,
    "parallel_processing": true,
    "max_workers": 4
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "batch_id": "batch_789",
        "total_files": 10,
        "processed_files": 8,
        "failed_files": 2,
        "results": [
            {
                "file_name": "manual1.pdf",
                "document_id": "doc_123456",
                "status": "success"
            },
            {
                "file_name": "manual2.pdf",
                "document_id": null,
                "status": "failed",
                "error": "文件格式不支持"
            }
        ]
    }
}
```

## 向量检索 API

### 1. 向量相似度检索

**接口**: `POST /search/vector`

**描述**: 基于向量相似度进行文档检索

**请求参数**:
```json
{
    "query": "航空发动机维修程序",
    "collection_name": "aviation_docs",
    "top_k": 10,
    "filter": {
        "document_type": "maintenance_manual",
        "compliance_level": "high"
    },
    "search_params": {
        "metric_type": "L2",
        "nprobe": 16
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "query": "航空发动机维修程序",
        "total_results": 10,
        "search_time": 0.15,
        "results": [
            {
                "id": "chunk_001",
                "score": 0.95,
                "content": "发动机维修程序包括以下步骤...",
                "metadata": {
                    "document_title": "发动机维修手册",
                    "document_type": "maintenance_manual",
                    "page_number": 25,
                    "compliance_level": "high"
                }
            }
        ]
    }
}
```

### 2. 混合检索

**接口**: `POST /search/hybrid`

**描述**: 结合向量检索和全文检索的混合检索

**请求参数**:
```json
{
    "query": "发动机故障诊断",
    "collection_name": "aviation_docs",
    "top_k": 10,
    "vector_weight": 0.7,
    "sparse_weight": 0.3,
    "filter": {
        "document_type": ["maintenance_manual", "technical_standard"]
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "query": "发动机故障诊断",
        "search_strategy": "hybrid",
        "total_results": 10,
        "search_time": 0.25,
        "fusion_score": 0.88,
        "results": [
            {
                "id": "chunk_005",
                "vector_score": 0.92,
                "sparse_score": 0.85,
                "final_score": 0.89,
                "content": "发动机故障诊断的基本原则...",
                "metadata": {
                    "document_title": "故障诊断手册",
                    "chapter": "第三章",
                    "section": "3.2"
                }
            }
        ]
    }
}
```

### 3. 精确匹配检索

**接口**: `POST /search/exact`

**描述**: 基于关键词的精确匹配检索

**请求参数**:
```json
{
    "keywords": ["安全检查", "日常维护"],
    "collection_name": "aviation_docs",
    "match_mode": "all",
    "top_k": 20
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "keywords": ["安全检查", "日常维护"],
        "match_mode": "all",
        "total_results": 15,
        "results": [
            {
                "id": "chunk_010",
                "content": "日常维护中的安全检查项目包括...",
                "matched_keywords": ["安全检查", "日常维护"],
                "metadata": {
                    "document_title": "维护手册",
                    "relevance_score": 0.95
                }
            }
        ]
    }
}
```

## 集合管理 API

### 1. 创建集合

**接口**: `POST /collections`

**描述**: 创建新的向量集合

**请求参数**:
```json
{
    "collection_name": "aviation_docs",
    "schema_type": "aviation",
    "dimension": 768,
    "index_config": {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "nlist": 1024
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "collection_name": "aviation_docs",
        "status": "created",
        "schema": {
            "fields": [
                {
                    "name": "id",
                    "type": "int64",
                    "is_primary": true
                },
                {
                    "name": "content_vector",
                    "type": "float_vector",
                    "dimension": 768
                }
            ]
        }
    }
}
```

### 2. 获取集合信息

**接口**: `GET /collections/{collection_name}`

**描述**: 获取指定集合的详细信息

**响应示例**:
```json
{
    "success": true,
    "data": {
        "collection_name": "aviation_docs",
        "status": "loaded",
        "entity_count": 15000,
        "partitions": [
            {
                "name": "technical_manuals",
                "entity_count": 8000
            },
            {
                "name": "regulations",
                "entity_count": 7000
            }
        ],
        "indexes": [
            {
                "field_name": "content_vector",
                "index_type": "IVF_FLAT",
                "metric_type": "L2"
            }
        ]
    }
}
```

### 3. 删除集合

**接口**: `DELETE /collections/{collection_name}`

**描述**: 删除指定的集合

**响应示例**:
```json
{
    "success": true,
    "message": "集合 aviation_docs 已成功删除"
}
```

## 数据管理 API

### 1. 插入数据

**接口**: `POST /collections/{collection_name}/data`

**描述**: 向指定集合插入数据

**请求参数**:
```json
{
    "data": [
        {
            "document_title": "维修手册第一章",
            "document_content": "本章介绍基本维修程序...",
            "document_type": "maintenance_manual",
            "compliance_level": "high"
        }
    ],
    "partition_name": "technical_manuals"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "inserted_count": 1,
        "inserted_ids": ["123456789"],
        "processing_time": 0.05
    }
}
```

### 2. 更新数据

**接口**: `PUT /collections/{collection_name}/data/{entity_id}`

**描述**: 更新指定实体的数据

**请求参数**:
```json
{
    "document_content": "更新后的文档内容...",
    "update_time": "2024-01-15T15:30:00Z"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "数据更新成功",
    "updated_id": "123456789"
}
```

### 3. 删除数据

**接口**: `DELETE /collections/{collection_name}/data`

**描述**: 删除指定条件的数据

**请求参数**:
```json
{
    "filter": "document_type == 'obsolete'",
    "partition_name": "technical_manuals"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "deleted_count": 25,
        "processing_time": 0.12
    }
}
```

## 系统管理 API

### 1. 系统健康检查

**接口**: `GET /health`

**描述**: 检查系统各组件的健康状态

**响应示例**:
```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "timestamp": "2024-01-15T16:00:00Z",
        "components": {
            "milvus": {
                "status": "healthy",
                "version": "2.4.0",
                "collections": 3
            },
            "document_processor": {
                "status": "healthy",
                "active_tasks": 2
            },
            "storage": {
                "status": "healthy",
                "disk_usage": "45%"
            }
        }
    }
}
```

### 2. 系统统计信息

**接口**: `GET /stats`

**描述**: 获取系统统计信息

**响应示例**:
```json
{
    "success": true,
    "data": {
        "documents": {
            "total_count": 1500,
            "processed_today": 25,
            "processing_queue": 3
        },
        "collections": {
            "total_count": 3,
            "total_entities": 45000,
            "storage_size": "2.5GB"
        },
        "performance": {
            "avg_search_time": 0.15,
            "avg_processing_time": 8.5,
            "success_rate": 0.98
        }
    }
}
```

## 错误处理

### 错误响应格式

```json
{
    "success": false,
    "error": {
        "code": "INVALID_PARAMETER",
        "message": "参数验证失败",
        "details": {
            "field": "collection_name",
            "reason": "集合名称不能为空"
        }
    },
    "timestamp": "2024-01-15T16:00:00Z"
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| `INVALID_PARAMETER` | 400 | 请求参数无效 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

## 限流和配额

### 请求限制

- **文档上传**: 每分钟最多 10 个文件
- **检索请求**: 每秒最多 100 次
- **批量操作**: 每次最多 1000 条记录
- **文件大小**: 单个文件最大 100MB

### 响应头

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642262400
```

## SDK 示例

### Python SDK

```python
from rag_flow_sdk import RAGFlowClient

# 初始化客户端
client = RAGFlowClient(
    base_url="http://localhost:8000/api/v1",
    token="your_access_token"
)

# 上传文档
result = client.documents.parse(
    file_path="manual.pdf",
    config={
        "use_docling": True,
        "enable_ocr": True
    }
)

# 检索文档
search_result = client.search.vector(
    query="发动机维修",
    collection_name="aviation_docs",
    top_k=10
)
```

### JavaScript SDK

```javascript
import { RAGFlowClient } from 'rag-flow-sdk';

const client = new RAGFlowClient({
    baseURL: 'http://localhost:8000/api/v1',
    token: 'your_access_token'
});

// 上传文档
const result = await client.documents.parse({
    file: fileInput.files[0],
    config: {
        use_docling: true,
        enable_ocr: true
    }
});

// 检索文档
const searchResult = await client.search.vector({
    query: '发动机维修',
    collection_name: 'aviation_docs',
    top_k: 10
});
```

## 版本历史

- **v1.0.0** (2024-01-15): 初始版本，包含基础文档处理和检索功能
- **v1.1.0** (计划): 增加实时检索和流式处理功能
- **v1.2.0** (计划): 增加多语言支持和高级分析功能
