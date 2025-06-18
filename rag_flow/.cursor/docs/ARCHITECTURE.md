# RAG Flow 系统架构文档

## 架构概述

RAG Flow 采用模块化的分层架构设计，将文档处理和向量检索分离为两个核心模块，通过清晰的接口进行协作。系统设计遵循单一职责原则，每个模块专注于特定的功能领域。

## 整体架构

### 系统架构图

```mermaid
graph TB
    subgraph "用户层"
        A[用户接口]
        B[API接口]
        C[命令行工具]
    end
    
    subgraph "业务逻辑层"
        D[文档处理服务]
        E[检索服务]
        F[知识问答服务]
    end
    
    subgraph "核心模块层"
        G[Document Processor]
        H[Milvus Services]
    end
    
    subgraph "数据存储层"
        I[Milvus向量数据库]
        J[文件存储]
        K[元数据存储]
    end
    
    A --> D
    B --> E
    C --> F
    
    D --> G
    E --> H
    F --> H
    
    G --> J
    H --> I
    H --> K
    
    style G fill:#e1f5fe
    style H fill:#f3e5f5
```

### 模块依赖关系

```mermaid
graph LR
    subgraph "Document Processor 模块"
        A1[Parsers 解析器]
        A2[Extractors 提取器]
        A3[Chunking 分块引擎]
        A4[Validators 验证器]
        
        A1 --> A2
        A2 --> A3
        A3 --> A4
    end
    
    subgraph "Milvus Services 模块"
        B1[Collection Manager]
        B2[Data Service]
        B3[Search Service]
        B4[Metadata Service]
        
        B1 --> B2
        B2 --> B3
        B3 --> B4
    end
    
    A4 --> B1
    
    style A1 fill:#ffebee
    style A2 fill:#e8f5e8
    style A3 fill:#f3e5f5
    style A4 fill:#fff3e0
    style B1 fill:#e3f2fd
    style B2 fill:#f1f8e9
    style B3 fill:#fce4ec
    style B4 fill:#fff8e1
```

## 核心模块架构

### Document Processor 模块架构

#### 模块结构图

```mermaid
graph TD
    A[DocumentProcessor 统一入口] --> B{文档类型检测}
    
    B -->|PDF| C[PDFParser]
    B -->|Word| D[WordParser]
    B -->|Excel| E[ExcelParser]
    B -->|PowerPoint| F[PowerPointParser]
    B -->|多格式| G[DoclingParser]
    
    C --> H[MetadataExtractor]
    D --> H
    E --> H
    F --> H
    G --> H
    
    C --> I[TableExtractor]
    D --> I
    E --> I
    F --> I
    G --> I
    
    C --> J[ImageExtractor]
    D --> J
    E --> J
    F --> J
    G --> J
    
    H --> K[UnifiedParseResult]
    I --> K
    J --> K
    
    K --> L[ChunkingEngine]
    L --> M{策略选择}
    
    M -->|航空文档| N[AviationStrategy]
    M -->|语义分块| O[SemanticChunker]
    M -->|结构分块| P[StructureChunker]
    
    N --> Q[TextChunk列表]
    O --> Q
    P --> Q
    
    Q --> R[ChunkValidator]
    R --> S[QualityController]
    S --> T[最终输出]
```

#### 数据流图

```mermaid
sequenceDiagram
    participant U as 用户
    participant DP as DocumentProcessor
    participant P as Parser
    participant E as Extractor
    participant C as ChunkingEngine
    participant V as Validator
    
    U->>DP: parse(file_path)
    DP->>DP: detect_document_type()
    DP->>P: 选择解析器
    P->>P: 解析文档内容
    P->>E: 提取元数据/表格/图像
    E-->>P: 返回提取结果
    P-->>DP: UnifiedParseResult
    DP->>C: chunk_document()
    C->>C: 选择分块策略
    C-->>DP: TextChunk列表
    DP->>V: validate_chunks()
    V-->>DP: ValidationResult
    DP-->>U: 最终结果
```

### Milvus Services 模块架构

#### 模块结构图

```mermaid
graph TD
    A[MilvusClient] --> B[CollectionManager]
    A --> C[DataService]
    A --> D[SearchService]
    A --> E[MetadataService]
    
    B --> F[集合创建]
    B --> G[分区管理]
    B --> H[索引管理]
    B --> I[健康监控]
    
    C --> J[数据插入]
    C --> K[数据更新]
    C --> L[数据删除]
    C --> M[批量操作]
    
    D --> N[向量检索]
    D --> O[稀疏检索]
    D --> P[混合检索]
    D --> Q[查询优化]
    
    E --> R[元数据关联]
    E --> S[缓存管理]
    E --> T[复合查询]
    E --> U[聚合统计]
```

#### 服务交互图

```mermaid
sequenceDiagram
    participant CM as CollectionManager
    participant DS as DataService
    participant SS as SearchService
    participant MS as MetadataService
    participant M as Milvus
    
    Note over CM,M: 初始化阶段
    CM->>M: 创建Collection
    CM->>M: 创建索引
    CM->>M: 加载Collection
    
    Note over DS,M: 数据插入阶段
    DS->>DS: 数据验证
    DS->>M: 批量插入
    DS->>DS: 更新统计
    
    Note over SS,MS: 检索阶段
    SS->>M: 向量检索
    SS->>M: 稀疏检索
    SS->>SS: 结果融合
    SS->>MS: 请求元数据
    MS->>M: 查询元数据
    MS-->>SS: 返回元数据
    SS-->>SS: 结果补全
```

## 技术架构

### 技术栈架构

```mermaid
graph TB
    subgraph "应用层"
        A1[Web API]
        A2[CLI工具]
        A3[SDK接口]
    end
    
    subgraph "业务层"
        B1[文档处理服务]
        B2[检索服务]
        B3[管理服务]
    end
    
    subgraph "核心层"
        C1[Document Processor]
        C2[Milvus Services]
        C3[Utils & Config]
    end
    
    subgraph "数据层"
        D1[Milvus 2.4+]
        D2[文件系统]
        D3[配置存储]
    end
    
    subgraph "基础设施层"
        E1[Python 3.8+]
        E2[Docker]
        E3[日志系统]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    
    B1 --> C1
    B2 --> C2
    B3 --> C3
    
    C1 --> D2
    C2 --> D1
    C3 --> D3
    
    D1 --> E2
    D2 --> E1
    D3 --> E3
```

### 数据架构

#### 数据流架构

```mermaid
graph LR
    A[原始文档] --> B[文档解析]
    B --> C[内容提取]
    C --> D[智能分块]
    D --> E[质量验证]
    E --> F[向量化]
    F --> G[Milvus存储]
    G --> H[检索服务]
    H --> I[结果返回]
    
    subgraph "数据转换"
        B --> B1[文本内容]
        C --> C1[结构化数据]
        D --> D1[文本块]
        E --> E1[验证结果]
        F --> F1[向量数据]
    end
    
    subgraph "存储层"
        G --> G1[向量索引]
        G --> G2[元数据]
        G --> G3[分区数据]
    end
```

#### 数据模型

```mermaid
erDiagram
    Document ||--o{ Chunk : contains
    Document {
        string id
        string title
        string type
        string path
        datetime create_time
        datetime update_time
    }
    
    Chunk ||--o{ Vector : generates
    Chunk {
        string id
        string document_id
        string content
        int start_position
        int end_position
        float quality_score
        datetime create_time
    }
    
    Vector ||--|| Metadata : associates
    Vector {
        string id
        string chunk_id
        array dense_vector
        array sparse_vector
        string partition_name
    }
    
    Metadata {
        string id
        string document_type
        string compliance_level
        json structured_data
        datetime create_time
    }
```

## 部署架构

### 单机部署架构

```mermaid
graph TB
    subgraph "应用服务器"
        A[RAG Flow 应用]
        B[Python Runtime]
        C[依赖库]
    end
    
    subgraph "数据服务器"
        D[Milvus Standalone]
        E[etcd]
        F[MinIO]
    end
    
    subgraph "存储"
        G[文档存储]
        H[向量数据]
        I[元数据]
    end
    
    A --> D
    D --> E
    D --> F
    F --> H
    E --> I
    A --> G
```

### 分布式部署架构

```mermaid
graph TB
    subgraph "负载均衡层"
        LB[Load Balancer]
    end
    
    subgraph "应用层"
        A1[RAG Flow App 1]
        A2[RAG Flow App 2]
        A3[RAG Flow App N]
    end
    
    subgraph "Milvus集群"
        M1[Milvus Coordinator]
        M2[Query Node 1]
        M3[Query Node 2]
        M4[Data Node 1]
        M5[Data Node 2]
        M6[Index Node]
        M7[Proxy]
    end
    
    subgraph "存储集群"
        S1[MinIO Cluster]
        S2[etcd Cluster]
    end
    
    LB --> A1
    LB --> A2
    LB --> A3
    
    A1 --> M7
    A2 --> M7
    A3 --> M7
    
    M7 --> M1
    M1 --> M2
    M1 --> M3
    M1 --> M4
    M1 --> M5
    M1 --> M6
    
    M2 --> S1
    M3 --> S1
    M4 --> S1
    M5 --> S1
    M6 --> S1
    
    M1 --> S2
```

## 性能架构

### 性能优化策略

```mermaid
graph TD
    A[性能优化] --> B[文档处理优化]
    A --> C[向量检索优化]
    A --> D[系统架构优化]
    
    B --> B1[批量处理]
    B --> B2[并行解析]
    B --> B3[智能分块]
    B --> B4[质量控制]
    
    C --> C1[索引优化]
    C --> C2[分区策略]
    C --> C3[缓存机制]
    C --> C4[混合检索]
    
    D --> D1[异步处理]
    D --> D2[连接池]
    D --> D3[资源管理]
    D --> D4[监控告警]
```

### 扩展性设计

```mermaid
graph LR
    A[水平扩展] --> A1[应用层扩展]
    A --> A2[存储层扩展]
    A --> A3[计算层扩展]
    
    A1 --> A11[多实例部署]
    A1 --> A12[负载均衡]
    A1 --> A13[服务发现]
    
    A2 --> A21[Milvus集群]
    A2 --> A22[分布式存储]
    A2 --> A23[数据分片]
    
    A3 --> A31[GPU加速]
    A3 --> A32[分布式计算]
    A3 --> A33[资源调度]
```

## 安全架构

### 安全层次

```mermaid
graph TB
    A[安全架构] --> B[网络安全]
    A --> C[应用安全]
    A --> D[数据安全]
    A --> E[运维安全]
    
    B --> B1[防火墙]
    B --> B2[VPN]
    B --> B3[SSL/TLS]
    
    C --> C1[身份认证]
    C --> C2[权限控制]
    C --> C3[API安全]
    
    D --> D1[数据加密]
    D --> D2[访问控制]
    D --> D3[备份恢复]
    
    E --> E1[日志审计]
    E --> E2[监控告警]
    E --> E3[安全更新]
```

## 监控架构

### 监控体系

```mermaid
graph TD
    A[监控系统] --> B[应用监控]
    A --> C[基础设施监控]
    A --> D[业务监控]
    
    B --> B1[性能指标]
    B --> B2[错误率]
    B --> B3[响应时间]
    B --> B4[吞吐量]
    
    C --> C1[CPU/内存]
    C --> C2[磁盘I/O]
    C --> C3[网络流量]
    C --> C4[服务状态]
    
    D --> D1[文档处理量]
    D --> D2[检索成功率]
    D --> D3[用户活跃度]
    D --> D4[质量指标]
```

## 总结

RAG Flow 的架构设计具有以下特点：

1. **模块化设计**: 清晰的模块边界和职责分离
2. **可扩展性**: 支持水平和垂直扩展
3. **高性能**: 多层次的性能优化策略
4. **高可用**: 分布式部署和故障恢复机制
5. **安全性**: 全方位的安全保障措施
6. **可维护性**: 完善的监控和运维体系

这种架构设计确保了系统的稳定性、性能和可扩展性，能够满足航空行业对知识管理系统的高要求。
