# Embedding 模块文档

## 概述

本模块提供统一的文本嵌入服务，支持多种embedding模型的API调用和本地化部署。

## 支持的模型

### Embedding 模型

#### 1. 智谱AI Embedding-3 (API调用)
- **模型ID**: `embedding-3`
- **类型**: API调用
- **提供商**: 智谱AI
- **最大tokens**: 8,192
- **支持维度**: 64, 128, 256, 512, 768, 1024
- **默认维度**: 1024
- **价格**: 0.5元/百万tokens

#### 2. BGE-M3 (本地化模型)
- **模型ID**: `bge-m3`
- **类型**: 本地化部署
- **提供商**: BAAI
- **模型路径**: `BAAI/bge-m3`
- **最大tokens**: 8,192
- **默认维度**: 1024
- **支持模式**: dense, sparse, colbert

#### 3. Qwen3-Embedding-0.6B (本地化模型)
- **模型ID**: `qwen3-embedding-0.6b`
- **类型**: 本地化部署
- **提供商**: Qwen
- **模型路径**: `Qwen/Qwen3-Embedding-0.6B`
- **模型大小**: 0.6B参数
- **最大tokens**: 8,192
- **默认维度**: 1024

### Chat 模型

#### DeepSeek 系列
- **deepseek-chat**: DeepSeek 主力聊天模型，适合代码生成和逻辑推理

#### GLM 系列（智谱AI）
- **glm-4-plus**: GLM-4 Plus 模型，性能强劲
- **glm-4-air**: GLM-4 Air 模型，轻量级版本
- **glm-4-airx**: GLM-4 AirX 模型
- **glm-4-flash**: GLM-4 Flash 模型，快速响应
- **glm-4-flashx**: GLM-4 FlashX 模型

#### GLM 视觉模型
- **glm-4.1v-thinking-flash**: GLM-4.1V 思考版 Flash 模型
- **glm-4.1v-thinking-flashx**: GLM-4.1V 思考版 FlashX 模型
- **glm-4v-plus-0111**: GLM-4V Plus 历史版本

#### Kimi 系列（月之暗面）
- **kimi-k2-0711-preview**: Kimi K2 预览版，适合长文本处理
- **kimi-k2-turbo-preview**: Kimi K2 Turbo 预览版
- **kimi-thinking-preview**: Kimi 思考版预览
- **kimi-vision**: Kimi 视觉模型，支持图像理解

## 环境变量配置

使用本模块前，需要设置相应的API密钥环境变量：

```bash
# DeepSeek API 密钥
export DS_API_KEY="your_deepseek_api_key"

# 智谱AI API 密钥
export ZHIPU_API_KEY="your_zhipu_api_key"

# Kimi API 密钥
export KIMI_API_KEY="your_kimi_api_key"

# 或者在代码中动态设置
```

## 核心文件

- `embedding_client.py`: 主要的embedding客户端类
- `deepseek_chat.py`: DeepSeek聊天模型客户端类
- `llm_select.py`: 统一的LLM模型选择与调用客户端类
- `embedding_test.py`: 测试文件
- `README.md`: 本文档

## 快速使用

### 基本导入
```python
# Embedding 相关
from src.core.llm.embedding_client import (
    embedding_client,
    embed_text,
    embed_texts,
    calculate_similarity,
    set_api_keys
)

# DeepSeek Chat 相关
from src.core.llm.deepseek_chat import DeepSeekChat

# LLM 统一调用相关
from src.core.llm.llm_select import (
    LLMClient,
    llm_client,
    chat_completion,
    set_api_keys as set_llm_api_keys,
    try_parse_json_object
)
```

### 简单使用示例

#### Embedding 使用示例
```python
# 设置API密钥（如果使用智谱AI）
set_api_keys(zhipu_api_key="your_zhipu_api_key")

# 单文本嵌入
embedding = embed_text("这是一个测试文本", "embedding-3")

# 批量文本嵌入
texts = ["文本1", "文本2", "文本3"]
embeddings = embed_texts(texts, "bge-m3")

# 计算相似度
similarity = calculate_similarity("文本A", "文本B", "qwen3-embedding-0.6b")
print(f"文本相似度: {similarity:.4f}")
```

#### DeepSeek Chat 使用示例
```python
# 初始化 DeepSeek Chat 客户端
chat_client = DeepSeekChat(api_key="your_deepseek_api_key")

# 基本对话
response = chat_client.chat("你好，请介绍一下自己")
print(response)

# 使用系统提示词
response = chat_client.chat(
    "请翻译这句话：Hello World",
    system_prompt="你是一个专业的翻译助手"
)
print(response)

# JSON 格式输出
response = chat_client.chat(
    "请用JSON格式返回北京的天气信息",
    use_json=True
)
print(response)

# 流式输出
def stream_callback(token):
    print(token, end="", flush=True)

chat_client.chat(
    "请写一首关于春天的诗",
    stream=True,
    stream_callback=stream_callback
)

# 重置对话历史
chat_client.reset_conversation()
```

#### LLM 统一调用使用示例
```python
# 设置多个 API 密钥
set_llm_api_keys(
    deepseek_api_key="your_deepseek_api_key",
    zhipu_api_key="your_zhipu_api_key",
    kimi_api_key="your_kimi_api_key"
)

# 使用全局客户端实例进行简单调用
messages = [{"role": "user", "content": "你好"}]

# DeepSeek 模型调用
response = chat_completion(messages, model_name="deepseek-chat")
print(response)

# GLM 模型调用
response = chat_completion(messages, model_name="glm-4-flash")
print(response)

# Kimi 模型调用
response = chat_completion(messages, model_name="kimi-k2-turbo-preview")
print(response)

# 流式输出
for chunk in chat_completion(messages, model_name="deepseek-chat", stream=True):
    print(chunk, end="", flush=True)

# JSON 格式输出
response = chat_completion(
    [{"role": "user", "content": "请用JSON格式返回今天的日期"}],
    model_name="glm-4-flash",
    use_json=True
)
parsed_text, parsed_json = try_parse_json_object(response)
print(f"解析后的JSON: {parsed_json}")
```

### 高级使用示例

#### Embedding 高级使用
```python
# 初始化客户端
from src.core.llm.embedding_client import EmbeddingClient

client = EmbeddingClient()

# 列出可用模型
models = client.list_available_models()
print("可用模型:", models)

# 获取模型详细信息
for model in models:
    info = client.get_model_info(model)
    print(f"模型: {model}, 类型: {info['type']}, 提供商: {info['provider']}")

# 初始化特定模型
success = client.initialize_model("embedding-3")
if success:
    # 使用智谱AI进行嵌入，指定维度
    embedding = client.embed_text("测试文本", "embedding-3", dimensions=512)
    print(f"嵌入维度: {len(embedding)}")
    
    # 获取嵌入维度信息
    dim = client.get_embedding_dimension("embedding-3", dimensions=512)
    print(f"确认维度: {dim}")

# 批量相似度计算
query_embedding = client.embed_text("查询文本", "bge-m3")
```

#### DeepSeek Chat 高级使用
```python
# 初始化客户端
chat_client = DeepSeekChat(api_key="your_deepseek_api_key")

# 工具调用示例
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

response = chat_client.chat(
    "北京今天天气怎么样？",
    tools=tools,
    tool_choice="auto"
)
print(response)

# 控制对话历史长度
chat_client.chat("第一条消息")
chat_client.chat("第二条消息")
chat_client.chat("第三条消息")

# 只保留最近2轮对话
response = chat_client.chat(
    "第四条消息",
    max_history=2
)

# 获取当前对话历史
print("当前对话历史:", chat_client.messages)
```

#### LLM 统一调用高级使用
```python
# 初始化客户端实例
client = LLMClient()

# 视觉模型使用（GLM 和 Kimi 视觉模型）
image_urls = ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
vision_messages = client.build_vision_messages(
    "请描述这些图片的内容",
    image_urls
)

# 使用 GLM 视觉模型
response = client.chat_completion(
    vision_messages,
    model_name="glm-4.1v-thinking-flash",
    enable_vision=True
)
print(response)

# 使用 Kimi 视觉模型
response = client.chat_completion(
    vision_messages,
    model_name="kimi-vision",
    enable_vision=True
)
print(response)

# 翻译任务模板
translation_messages = client.generate_translation_template(
    system_var="你是专业的航空翻译专家",
    reference="参考术语：aircraft - 飞机, runway - 跑道",
    query="The aircraft is approaching the runway"
)

response = client.chat_completion(
    translation_messages,
    model_name="glm-4-plus",
    temperature=0.3
)
print(response)

# 工具调用示例
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

response = client.chat_completion(
    [{"role": "user", "content": "计算 25 * 4 + 10"}],
    model_name="glm-4-flash",
    tools=tools,
    tool_choice="auto"
)
print(response)

# 不同模型的参数调优
# DeepSeek 模型 - 适合代码生成和逻辑推理
response = client.chat_completion(
    [{"role": "user", "content": "写一个Python快速排序算法"}],
    model_name="deepseek-chat",
    temperature=0.1,  # 低温度保证代码准确性
    max_tokens=2000
)

# GLM 模型 - 适合中文对话和创意写作
response = client.chat_completion(
    [{"role": "user", "content": "写一首关于人工智能的现代诗"}],
    model_name="glm-4-plus",
    temperature=0.8,  # 高温度增加创造性
    top_p=0.9
)

# Kimi 模型 - 适合长文本处理和分析
response = client.chat_completion(
    [{"role": "user", "content": "请总结这篇长文档的要点..."}],
    model_name="kimi-k2-0711-preview",
    temperature=0.3,
    max_tokens=4000
)
```
candidate_embeddings = client.embed_texts(["候选1", "候选2", "候选3"], "bge-m3")
similarities = client.batch_similarity(query_embedding, candidate_embeddings)
print(f"批量相似度: {similarities}")
```

### 本地模型路径指定

#### 方法1: 环境变量指定缓存目录
```bash
# 设置模型缓存根目录
export EMBEDDING_CACHE_DIR="/your/custom/path/embedding_models"
```

#### 方法2: 修改配置文件中的本地路径
```python
from src.core.llm.embedding_client import MODEL_CONFIGS

# 在初始化前修改模型配置
MODEL_CONFIGS["bge-m3"]["local_path"] = "/path/to/your/bge-m3-model"
MODEL_CONFIGS["qwen3-embedding-0.6b"]["local_path"] = "/path/to/your/qwen3-model"

# 然后正常使用
from src.core.llm.embedding_client import embedding_client
success = embedding_client.initialize_model("bge-m3")
```

#### 方法3: 直接指定已下载的模型路径
```python
import os
from pathlib import Path
from src.core.llm.embedding_client import EmbeddingClient, LocalEmbeddingProvider

# 创建自定义配置
custom_config = {
    "type": "local",
    "provider": "baai",
    "model_id": "BAAI/bge-m3",
    "max_tokens": 8192,
    "default_dimensions": 1024,
    "local_path": "/your/existing/model/path/bge-m3"  # 指定已存在的模型路径
}

# 创建客户端并手动添加提供者
client = EmbeddingClient()
provider = LocalEmbeddingProvider("custom-bge-m3", custom_config)

# 手动设置模型路径，跳过下载检查
provider.model_cache_dir = Path("/your/existing/model/path")
provider._load_local_model(Path(custom_config["local_path"]))
provider.is_initialized = True

# 添加到客户端
client.providers["custom-bge-m3"] = provider
client.current_model = "custom-bge-m3"

# 使用自定义路径的模型
embedding = client.embed_text("测试文本", "custom-bge-m3")
```

#### 常见本地模型路径结构
```
/your/model/path/
├── bge-m3/                    # BGE-M3模型目录
│   ├── config.json
│   ├── pytorch_model.bin
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── vocab.txt
└── qwen3-embedding-0.6b/      # Qwen3模型目录
    ├── config.json
    ├── model.safetensors
    ├── tokenizer.json
    ├── tokenizer_config.json
    └── vocab.json
```

#### 验证本地模型路径
```python
from pathlib import Path

def verify_model_path(model_path, model_type="bge-m3"):
    """验证本地模型路径是否有效"""
    path = Path(model_path)
    
    if not path.exists():
        print(f"❌ 路径不存在: {model_path}")
        return False
    
    # 检查必要文件
    required_files = ["config.json"]
    if model_type == "bge-m3":
        required_files.extend(["pytorch_model.bin", "tokenizer.json"])
    elif model_type == "qwen3":
        required_files.extend(["model.safetensors", "tokenizer.json"])
    
    missing_files = []
    for file_name in required_files:
        if not (path / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    print(f"✅ 模型路径有效: {model_path}")
    return True

# 使用示例
verify_model_path("/path/to/your/bge-m3", "bge-m3")
verify_model_path("/path/to/your/qwen3-embedding", "qwen3")
```

## 环境配置

### API密钥设置
```bash
# 智谱AI API密钥
export ZHIPU_API_KEY="your_zhipu_api_key"
```

### 依赖安装
```bash
# 基础依赖
pip install numpy

# 智谱AI API支持
pip install zhipuai

# 本地模型支持
pip install torch transformers sentence-transformers

# 可选：加速库
pip install accelerate
```

## 完整使用示例

### 示例1: 智谱AI Embedding-3 使用
```python
import os
from src.core.llm.embedding_client import embedding_client, set_api_keys

# 设置API密钥
set_api_keys(zhipu_api_key="your_zhipu_api_key")
# 或使用环境变量
# os.environ["ZHIPU_API_KEY"] = "your_zhipu_api_key"

# 初始化模型
if embedding_client.initialize_model("embedding-3"):
    print("✅ 智谱AI Embedding-3 初始化成功")
    
    # 单文本嵌入
    text = "人工智能正在改变世界"
    embedding = embedding_client.embed_text(text, "embedding-3")
    print(f"文本: {text}")
    print(f"嵌入维度: {len(embedding)}")
    
    # 批量嵌入
    texts = [
        "机器学习是AI的核心技术",
        "深度学习推动了AI的发展",
        "自然语言处理让机器理解人类语言"
    ]
    embeddings = embedding_client.embed_texts(texts, "embedding-3")
    print(f"批量嵌入完成，共{len(embeddings)}个向量")
    
    # 计算相似度
    for i, text_a in enumerate(texts):
        for j, text_b in enumerate(texts[i+1:], i+1):
            sim = embedding_client.calculate_similarity(embeddings[i], embeddings[j])
            print(f"'{text_a}' vs '{text_b}': {sim:.4f}")
else:
    print("❌ 智谱AI Embedding-3 初始化失败")
```

### 示例2: BGE-M3 本地模型使用
```python
from src.core.llm.embedding_client import embedding_client

# 初始化BGE-M3模型（首次使用会自动下载）
print("正在初始化BGE-M3模型，首次使用需要下载...")
if embedding_client.initialize_model("bge-m3"):
    print("✅ BGE-M3 模型初始化成功")
    
    # 测试文本
    query = "如何学习机器学习？"
    documents = [
        "机器学习需要扎实的数学基础，包括线性代数、概率论和统计学。",
        "推荐从Python编程开始，然后学习scikit-learn等机器学习库。",
        "理论与实践结合很重要，多做项目练习。",
        "今天天气很好，适合出门散步。"  # 不相关文档
    ]
    
    # 生成嵌入
    query_embedding = embedding_client.embed_text(query, "bge-m3")
    doc_embeddings = embedding_client.embed_texts(documents, "bge-m3")
    
    # 计算相似度并排序
    similarities = embedding_client.batch_similarity(query_embedding, doc_embeddings)
    
    # 按相似度排序
    ranked_docs = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)
    
    print(f"\n查询: {query}")
    print("相关文档排序:")
    for i, (doc, sim) in enumerate(ranked_docs, 1):
        print(f"{i}. 相似度: {sim:.4f} - {doc}")
else:
    print("❌ BGE-M3 模型初始化失败")
```

### 示例3: 使用已下载的本地模型
```python
from src.core.llm.embedding_client import MODEL_CONFIGS, embedding_client

# 方法1: 修改配置指定本地路径
MODEL_CONFIGS["bge-m3"]["local_path"] = "/path/to/your/downloaded/bge-m3"

# 初始化模型
if embedding_client.initialize_model("bge-m3"):
    print("✅ 使用本地路径的BGE-M3模型初始化成功")
    
    # 正常使用
    embedding = embedding_client.embed_text("测试文本", "bge-m3")
    print(f"嵌入维度: {len(embedding)}")
```

### 示例4: 文档检索应用
```python
from src.core.llm.embedding_client import embedding_client
import numpy as np

class DocumentRetriever:
    def __init__(self, model_name="bge-m3"):
        self.model_name = model_name
        self.documents = []
        self.embeddings = []
        
        # 初始化模型
        if not embedding_client.initialize_model(model_name):
            raise RuntimeError(f"模型 {model_name} 初始化失败")
    
    def add_documents(self, docs):
        """添加文档到检索库"""
        print(f"正在为{len(docs)}个文档生成嵌入...")
        doc_embeddings = embedding_client.embed_texts(docs, self.model_name)
        
        self.documents.extend(docs)
        self.embeddings.extend(doc_embeddings)
        print(f"✅ 文档库现有{len(self.documents)}个文档")
    
    def search(self, query, top_k=5):
        """搜索相关文档"""
        if not self.documents:
            return []
        
        # 生成查询嵌入
        query_embedding = embedding_client.embed_text(query, self.model_name)
        
        # 计算相似度
        similarities = embedding_client.batch_similarity(query_embedding, self.embeddings)
        
        # 排序并返回top_k结果
        results = list(zip(self.documents, similarities))
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]

# 使用示例
retriever = DocumentRetriever("bge-m3")

# 添加文档
docs = [
    "Python是一种高级编程语言，广泛用于数据科学和机器学习。",
    "机器学习算法可以从数据中学习模式，无需显式编程。",
    "深度学习是机器学习的一个子集，使用神经网络进行学习。",
    "自然语言处理帮助计算机理解和生成人类语言。",
    "计算机视觉让机器能够理解和分析图像内容。"
]
retriever.add_documents(docs)

# 搜索
query = "什么是机器学习？"
results = retriever.search(query, top_k=3)

print(f"\n查询: {query}")
print("搜索结果:")
for i, (doc, score) in enumerate(results, 1):
    print(f"{i}. 相似度: {score:.4f}")
    print(f"   文档: {doc}\n")
```

### 示例5: 多模型对比
```python
from src.core.llm.embedding_client import embedding_client
import time

def compare_models():
    """对比不同模型的性能"""
    test_text = "人工智能技术正在快速发展，深刻影响着各个行业。"
    models_to_test = ["embedding-3", "bge-m3", "qwen3-embedding-0.6b"]
    
    results = {}
    
    for model_name in models_to_test:
        print(f"\n测试模型: {model_name}")
        
        # 初始化模型
        start_time = time.time()
        success = embedding_client.initialize_model(model_name)
        init_time = time.time() - start_time
        
        if not success:
            print(f"❌ 模型 {model_name} 初始化失败")
            continue
        
        # 测试嵌入性能
        start_time = time.time()
        embedding = embedding_client.embed_text(test_text, model_name)
        embed_time = time.time() - start_time
        
        results[model_name] = {
            "init_time": init_time,
            "embed_time": embed_time,
            "dimension": len(embedding),
            "first_5_values": embedding[:5]
        }
        
        print(f"✅ 初始化时间: {init_time:.2f}秒")
        print(f"✅ 嵌入时间: {embed_time:.2f}秒")
        print(f"✅ 向量维度: {len(embedding)}")
    
    # 输出对比结果
    print("\n" + "="*60)
    print("模型性能对比")
    print("="*60)
    for model, result in results.items():
        print(f"{model}:")
        print(f"  初始化: {result['init_time']:.2f}s")
        print(f"  嵌入速度: {result['embed_time']:.2f}s")
        print(f"  向量维度: {result['dimension']}")
        print()

# 运行对比
compare_models()
```

## 架构设计

### 类层次结构
```
EmbeddingClient (主客户端)
├── BaseEmbeddingProvider (抽象基类)
│   ├── ZhipuEmbeddingProvider (智谱AI提供者)
│   └── LocalEmbeddingProvider (本地模型提供者)
```

### 设计原则
- **统一接口**: 所有模型通过相同的接口调用
- **自动下载**: 本地模型首次使用时自动下载
- **缓存管理**: 本地模型缓存在 `~/.cache/embedding_models/`
- **错误处理**: 完善的异常处理和日志记录
- **性能优化**: 支持批量处理和GPU加速

## 部署注意事项

### 服务器环境要求
- Python 3.8+
- 足够的磁盘空间（本地模型约1-3GB）
- GPU支持（可选，用于加速本地模型）
- 网络连接（用于模型下载和API调用）

### 性能考虑
- **内存使用**: 本地模型加载需要2-4GB内存
- **GPU加速**: 支持CUDA加速本地模型推理
- **并发处理**: 支持批量文本处理
- **缓存策略**: 模型加载后保持在内存中

### 安全考虑
- API密钥通过环境变量管理
- 本地模型文件权限控制
- 输入文本长度限制
- 错误信息脱敏

## 实用功能

### JSON 解析工具
```python
from src.core.llm.llm_select import try_parse_json_object

# 解析可能包含 JSON 的字符串
text_with_json = '```json\n{"name": "张三", "age": 25}\n```'
parsed_text, parsed_json = try_parse_json_object(text_with_json)
print(f"解析结果: {parsed_json}")
```

### 模型选择建议

- **代码生成和逻辑推理**: 推荐使用 `deepseek-chat`，温度设置为 0.1-0.3
- **中文对话和创意写作**: 推荐使用 `glm-4-plus` 或 `glm-4-flash`，温度设置为 0.6-0.8
- **长文本处理和分析**: 推荐使用 `kimi-k2-0711-preview`，温度设置为 0.3-0.5
- **图像理解和多模态**: 推荐使用 `glm-4.1v-thinking-flash` 或 `kimi-vision`
- **快速响应场景**: 推荐使用 `glm-4-flash` 或 `glm-4-flashx`

### 性能优化建议

1. **流式输出**: 对于长文本生成，建议使用流式输出提升用户体验
2. **批量处理**: 对于多个文本的嵌入，使用 `embed_texts` 批量处理
3. **模型缓存**: 本地化模型首次加载较慢，后续调用会利用缓存
4. **参数调优**: 根据具体任务调整 `temperature`、`top_p` 等参数

## 故障排除

### 常见问题

1. **API密钥相关问题**
   - 确保环境变量设置正确
   - 检查API密钥是否有效且未过期
   - 验证API密钥权限是否足够

2. **智谱AI API调用失败**
   - 检查API密钥是否正确设置
   - 确认网络连接正常
   - 检查API配额是否充足

2. **本地模型下载失败**
   - 检查网络连接
   - 确认磁盘空间充足
   - 尝试手动下载模型

3. **内存不足错误**
   - 减少批量处理的文本数量
   - 使用较小的模型
   - 增加服务器内存

4. **GPU相关错误**
   - 检查CUDA安装
   - 确认GPU驱动版本
   - 回退到CPU模式

### 日志查看
```python
from src.utils.logger import SZ_LoggerManager
logger = SZ_LoggerManager.get_logger("embedding")
# 查看详细日志信息
```

## 性能基准

### 智谱AI Embedding-3
- 单文本嵌入: ~0.5秒
- 批量嵌入(10个文本): ~1.2秒
- 网络延迟影响较大

### BGE-M3 (本地)
- 模型加载: ~10秒
- 单文本嵌入: ~0.1秒 (GPU) / ~0.3秒 (CPU)
- 批量嵌入(10个文本): ~0.5秒 (GPU) / ~1.5秒 (CPU)

### Qwen3-Embedding-0.6B (本地)
- 模型加载: ~5秒
- 单文本嵌入: ~0.08秒 (GPU) / ~0.2秒 (CPU)
- 批量嵌入(10个文本): ~0.3秒 (GPU) / ~1.0秒 (CPU)

## 更新日志

### v1.0.0 (2025-08-08)
- 初始版本发布
- 支持智谱AI Embedding-3 API调用
- 支持BGE-M3和Qwen3-Embedding本地化部署
- 实现统一的嵌入接口
- 添加自动模型下载功能
- 提供相似度计算工具
