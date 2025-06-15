# Milvus核心服务模块

## 概述

本模块提供了完整的Milvus向量数据库操作服务，专为航空RAG知识管理系统设计。模块采用分层架构，将Milvus的复杂操作封装为简单易用的服务接口。

## 模块架构

```
src/core/milvus/
├── __init__.py                 # 模块入口
├── collection_manager.py       # Collection管理服务
├── search_service.py          # 检索服务
├── metadata_service.py        # 元数据关联服务
├── data_service.py            # 数据操作服务
└── README.md                  # 本文档
```

## 核心服务组件

### 1. Collection管理服务 (MilvusCollectionManager)

**功能职责**：
- Collection的创建、删除、描述
- 分区管理（创建、删除、加载、释放）
- 索引管理和优化
- Collection状态监控和健康检查

**核心特性**：
- 支持动态Schema配置
- 航空文档专用Schema模板
- 自动BM25索引创建
- 完整的错误处理和日志记录

**使用示例**：
```python
from src.core.milvus import MilvusCollectionManager

# 初始化管理器
manager = MilvusCollectionManager(
    uri="http://localhost:19530",
    token="root:Milvus"
)

# 创建航空文档Collection
manager.create_aviation_collection("aviation_docs")

# 创建分区
manager.create_partition("aviation_docs", "technical_manuals")

# 加载Collection到内存
manager.load_collection("aviation_docs")
```

### 2. 检索服务 (MilvusSearchService)

**功能职责**：
- 向量相似度检索
- 稀疏向量检索（BM25全文检索）
- 文本精确匹配检索
- 混合检索（多种检索策略融合）
- 复杂查询和结果排序

**核心特性**：
- 多种检索策略支持
- 智能结果融合算法
- 可配置的检索参数
- 性能优化的批量检索

**使用示例**：
```python
from src.core.milvus import MilvusSearchService
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")
search_service = MilvusSearchService(client)

# 向量检索
results = search_service.vector_search(
    collection_name="aviation_docs",
    query_vectors=[[0.1, 0.2, 0.3, ...]],
    vector_field="content_vector",
    limit=10
)

# 混合检索
hybrid_results = search_service.hybrid_search(
    collection_name="aviation_docs",
    query_vectors=[[0.1, 0.2, 0.3, ...]],
    query_texts=["aircraft engine maintenance"],
    vector_field="content_vector",
    sparse_field="content_sparse_vector",
    vector_weight=0.7,
    sparse_weight=0.3
)
```

### 3. 元数据关联服务 (MilvusMetadataService)

**功能职责**：
- 检索结果元数据补全
- 复合查询支持（向量+元数据过滤）
- 聚合查询和统计分析
- 元数据缓存策略
- 批量元数据查询优化

**核心特性**：
- 智能元数据缓存
- 复合查询优化
- 聚合统计功能
- PostgreSQL集成准备

**使用示例**：
```python
from src.core.milvus import MilvusMetadataService

metadata_service = MilvusMetadataService(client)

# 为检索结果补全元数据
enriched_results = metadata_service.enrich_search_results_with_metadata(
    collection_name="aviation_docs",
    search_results=search_results,
    metadata_fields=["document_type", "compliance_level", "create_time"]
)

# 复合查询
complex_results = metadata_service.complex_query_with_metadata(
    collection_name="aviation_docs",
    vector_query={
        "vectors": [[0.1, 0.2, 0.3, ...]],
        "field": "content_vector",
        "params": {"metric_type": "L2", "params": {"nprobe": 10}}
    },
    metadata_filter="document_type == 'technical_manual' and compliance_level == 'high'"
)
```

### 4. 数据操作服务 (MilvusDataService)

**功能职责**：
- 数据插入、更新、删除操作
- 批量数据处理
- 基于内容的ID生成
- 数据格式验证
- Collection统计信息

**核心特性**：
- 智能批量处理
- 自动时间戳管理
- 内容哈希ID生成
- 完整的数据验证
- 通用化的删除操作（从原始代码优化而来）

**使用示例**：
```python
from src.core.milvus import MilvusDataService

data_service = MilvusDataService(client, chunk_size=5000)

# 插入数据
result = data_service.insert_data(
    collection_name="aviation_docs",
    data=[
        {
            "document_title": "Aircraft Maintenance Manual",
            "document_content": "This manual covers...",
            "document_type": "technical_manual",
            "compliance_level": "high"
        }
    ],
    partition_name="technical_manuals"
)

# 删除数据（通用化的删除功能）
delete_result = data_service.delete_data(
    collection_name="aviation_docs",
    filter_expr="document_type == 'obsolete'",
    partition_name="technical_manuals"
)

# 批量删除
batch_result = data_service.batch_delete_by_conditions(
    collection_name="aviation_docs",
    conditions=[
        "create_time < 1640995200",  # 2022年之前的数据
        "compliance_level == 'low'"   # 低合规等级数据
    ]
)
```

## 设计原则

### 1. 单一职责原则 (SRP)
每个服务类专注于特定的功能领域：
- `MilvusCollectionManager`: 专注Collection和分区管理
- `MilvusSearchService`: 专注各种检索操作
- `MilvusMetadataService`: 专注元数据关联和复合查询
- `MilvusDataService`: 专注数据CRUD操作

### 2. 开闭原则 (OCP)
- 通过配置参数支持扩展
- Schema配置支持自定义
- 检索策略可插拔设计

### 3. 依赖倒置原则 (DIP)
- 所有服务依赖于MilvusClient抽象
- 通过依赖注入提供灵活性

### 4. DRY原则
- 公共功能提取为工具方法
- 错误处理和日志记录统一化
- 参数验证逻辑复用

## 错误处理策略

### 1. 分层错误处理
```python
try:
    # 业务逻辑
    result = self.client.operation()
    logger.info("操作成功")
    return result
except SpecificException as e:
    logger.error(f"特定错误: {e}")
    raise
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise
```

### 2. 参数验证
```python
def method(self, param):
    if not param:
        raise ValueError("参数不能为空")
    if not self.client.has_collection(collection_name):
        raise ValueError(f"Collection {collection_name} 不存在")
```

### 3. 资源检查
- Collection存在性检查
- 分区状态验证
- 数据格式验证

## 日志记录规范

### 1. 日志级别使用
- `DEBUG`: 详细的调试信息
- `INFO`: 常规操作信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息

### 2. 日志格式
```python
logger.info(f"操作完成，耗时: {elapsed_time:.4f}秒，处理 {count} 条记录")
logger.error(f"操作失败: {error_message}")
```

## 性能优化策略

### 1. 批量处理
- 大数据集自动分块处理
- 可配置的批处理大小
- 进度跟踪和日志记录

### 2. 缓存策略
- 元数据智能缓存
- 缓存命中率统计
- 缓存清理机制

### 3. 连接管理
- 单一客户端实例复用
- 连接状态监控
- 自动重连机制

## 配置管理

### 1. 默认配置
```python
DEFAULT_MILVUS_URI = "http://124.71.148.16:19530"
DEFAULT_TOKEN = "root:Milvus"
DEFAULT_CHUNK_SIZE = 10000
```

### 2. 运行时配置
- 支持环境变量覆盖
- 配置文件支持
- 动态参数调整

## 扩展指南

### 1. 添加新的检索策略
```python
def custom_search(self, collection_name, **kwargs):
    # 实现自定义检索逻辑
    pass
```

### 2. 自定义Schema模板
```python
def get_custom_schema(self):
    return {
        "fields": [...],
        "functions": [...],
        "indexes": [...]
    }
```

### 3. 新增数据验证规则
```python
def validate_custom_data(self, data):
    # 实现自定义验证逻辑
    pass
```

## 测试建议

### 1. 单元测试
- 每个方法的独立测试
- 异常情况测试
- 边界条件测试

### 2. 集成测试
- 多服务协作测试
- 端到端流程测试
- 性能基准测试

### 3. 模拟测试
- Mock Milvus客户端
- 模拟网络异常
- 模拟数据异常

## 最佳实践

### 1. 初始化顺序
```python
# 1. 创建客户端
client = MilvusClient(uri=uri, token=token)

# 2. 初始化服务
collection_manager = MilvusCollectionManager(uri, token)
search_service = MilvusSearchService(client)
data_service = MilvusDataService(client)
metadata_service = MilvusMetadataService(client)

# 3. 创建Collection
collection_manager.create_aviation_collection("my_collection")

# 4. 加载Collection
collection_manager.load_collection("my_collection")
```

### 2. 资源清理
```python
# 释放Collection
collection_manager.release_collection("my_collection")

# 清理缓存
metadata_service.clear_metadata_cache()
```

### 3. 错误恢复
```python
try:
    # 执行操作
    result = service.operation()
except Exception as e:
    # 记录错误
    logger.error(f"操作失败: {e}")
    # 清理资源
    cleanup_resources()
    # 重新抛出异常
    raise
```

## 详细API参考

### MilvusCollectionManager API

#### 核心方法

**create_aviation_collection(collection_name, schema_config=None)**
- 创建航空文档专用Collection
- 支持自定义Schema配置
- 自动创建BM25索引

**create_partition(collection_name, partition_name)**
- 在Collection中创建分区
- 自动检查Collection存在性
- 支持分区状态验证

**load_collection(collection_name, load_fields=None)**
- 加载Collection到内存
- 支持选择性字段加载
- 提供加载状态监控

**get_health_info(collection_name=None)**
- 获取Milvus服务健康状态
- Collection级别的状态检查
- 连接状态验证

#### 默认航空Schema配置

```python
{
    "fields": [
        {"name": "id", "datatype": "INT64", "is_primary": True},
        {"name": "document_title", "datatype": "VARCHAR", "max_length": 500},
        {"name": "document_content", "datatype": "VARCHAR", "max_length": 8000},
        {"name": "content_vector", "datatype": "SPARSE_FLOAT_VECTOR"},
        {"name": "document_type", "datatype": "VARCHAR", "max_length": 100},
        {"name": "compliance_level", "datatype": "VARCHAR", "max_length": 50},
        {"name": "create_time", "datatype": "INT64"},
        {"name": "update_time", "datatype": "INT64"}
    ],
    "functions": [
        {
            "name": "bm25_content_func",
            "input_fields": ["document_content"],
            "output_fields": ["content_vector"],
            "function_type": "BM25"
        }
    ],
    "indexes": [
        {
            "field_name": "content_vector",
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "BM25"
        }
    ]
}
```

### MilvusSearchService API

#### 检索方法详解

**vector_search(collection_name, query_vectors, vector_field, ...)**
- 执行向量相似度检索
- 支持多种距离度量（L2, IP, COSINE）
- 可配置检索参数（nprobe等）

**sparse_vector_search(collection_name, query_texts, sparse_field, ...)**
- 执行BM25全文检索
- 直接传递查询文本
- 自动处理文本向量化

**hybrid_search(collection_name, query_vectors, query_texts, ...)**
- 融合向量检索和全文检索
- 可配置权重比例
- 智能结果排序算法

#### 检索参数配置

```python
# 向量检索参数
vector_search_params = {
    "metric_type": "L2",        # 距离度量类型
    "params": {"nprobe": 10}    # 检索参数
}

# 稀疏向量检索参数
sparse_search_params = {
    "params": {"drop_ratio_search": 0.2}  # BM25参数
}

# 混合检索权重
hybrid_weights = {
    "vector_weight": 0.7,      # 向量检索权重
    "sparse_weight": 0.3       # 全文检索权重
}
```

### MilvusDataService API

#### 数据操作方法

**insert_data(collection_name, data, partition_name=None, add_timestamps=True)**
- 批量插入数据
- 自动分块处理
- 时间戳自动管理

**upsert_data(collection_name, data, partition_name=None, use_content_based_id=False)**
- 更新或插入数据
- 智能ID处理
- 支持内容哈希ID生成

**delete_data(collection_name, ids=None, filter_expr=None, partition_name=None)**
- 通用化删除操作（从原始代码优化）
- 支持ID删除和条件删除
- 增强的错误处理和日志

**validate_data_format(collection_name, data)**
- 数据格式验证
- Schema兼容性检查
- 详细的验证报告

#### 删除操作详解

这个删除功能是从您提供的原始代码中提取并通用化的：

**原始代码的优势**：
1. 完善的参数验证
2. 灵活的删除方式（ID或条件）
3. 详细的日志记录
4. 完整的错误处理

**通用化改进**：
1. 移除了对特定collection_name的依赖
2. 增加了性能计时
3. 增强了返回结果信息
4. 标准化了ID格式处理
5. 添加了操作类型标识

```python
# 使用示例
# 按ID删除
result = data_service.delete_data(
    collection_name="aviation_docs",
    ids=[123, 456, 789]
)

# 按条件删除
result = data_service.delete_data(
    collection_name="aviation_docs",
    filter_expr="create_time < 1640995200"
)

# 返回结果格式
{
    "delete_count": 15,
    "collection_name": "aviation_docs",
    "elapsed_time": 0.1234,
    "operation_type": "delete_by_filter"
}
```

### MilvusMetadataService API

#### 元数据操作方法

**enrich_search_results_with_metadata(collection_name, search_results, metadata_fields=None)**
- 为检索结果补全元数据
- 智能缓存机制
- 批量查询优化

**complex_query_with_metadata(collection_name, vector_query=None, metadata_filter=None, ...)**
- 复合查询支持
- 向量检索+元数据过滤
- 灵活的查询组合

**aggregate_query_results(collection_name, filter_expr, group_by_field, ...)**
- 聚合查询功能
- 分组统计分析
- 多维度数据汇总

#### 缓存机制

```python
# 缓存键格式
cache_key = f"{collection_name}:{entity_id}"

# 缓存统计
cache_stats = metadata_service.get_cache_stats()
# 返回: {"cache_size": 1000, "cache_keys": ["aviation_docs:123", ...]}

# 清理缓存
metadata_service.clear_metadata_cache()
```

## 故障排除指南

### 常见问题

**1. Collection不存在错误**
```python
# 错误: Collection 'xxx' 不存在
# 解决: 先创建Collection
manager.create_aviation_collection("xxx")
```

**2. 内存不足错误**
```python
# 错误: 内存不足
# 解决: 释放不需要的Collection
manager.release_collection("unused_collection")
```

**3. 检索结果为空**
```python
# 检查: Collection是否已加载
load_state = manager.client.get_load_state("collection_name")
if load_state.get("state") != 3:
    manager.load_collection("collection_name")
```

**4. 数据插入失败**
```python
# 检查: 数据格式是否正确
validation_result = data_service.validate_data_format("collection_name", data)
if not validation_result["is_valid"]:
    print("数据格式错误:", validation_result["errors"])
```

### 性能调优

**1. 批处理大小调整**
```python
# 根据数据大小调整chunk_size
data_service = MilvusDataService(client, chunk_size=5000)  # 较小数据
data_service = MilvusDataService(client, chunk_size=20000) # 较大数据
```

**2. 检索参数优化**
```python
# 调整nprobe参数平衡精度和速度
search_params = {"metric_type": "L2", "params": {"nprobe": 16}}  # 高精度
search_params = {"metric_type": "L2", "params": {"nprobe": 8}}   # 高速度
```

**3. 缓存策略优化**
```python
# 定期清理缓存
if metadata_service.get_cache_stats()["cache_size"] > 10000:
    metadata_service.clear_metadata_cache()
```

## 版本历史

- **v1.0.0** (2025-06-14): 初始版本，包含四个核心服务模块
  - Collection管理服务
  - 检索服务
  - 元数据关联服务
  - 数据操作服务（包含通用化的删除功能）

## 贡献指南

1. 遵循现有的代码风格和注释规范
2. 添加完整的类型注解
3. 编写详细的docstring文档
4. 包含完整的错误处理
5. 添加相应的单元测试
6. 更新相关文档
