# RAG Flow 文档分块测试脚本使用指南

## 概述

本目录包含两个专门为RAG Flow项目设计的文档分块功能测试脚本：

1. **`test_chunking.py`** - 简化版本，专门测试 `recursive_chunker` 的分块效果
2. **`test_chunking_complete.py`** - 完整版本，支持所有可用的分块策略，具有智能依赖处理

两个脚本都提供了全面的测试功能，包括可视化分块结果、性能统计分析和多种使用场景演示。

## 主要功能

## 脚本特性对比

| 特性 | test_chunking.py | test_chunking_complete.py |
|------|------------------|---------------------------|
| 分块策略 | 仅 recursive | 所有可用策略 |
| 依赖处理 | 需要完整环境 | 智能降级处理 |
| 策略对比 | ❌ | ✅ |
| 策略列表 | ❌ | ✅ |
| 适用场景 | 专门测试递归分块 | 全面功能测试 |

### 🎯 核心功能
- **多策略测试**: 支持所有内置分块策略的测试（完整版）
- **智能降级**: 当依赖缺失时自动切换到简化模式（完整版）
- **可视化展示**: 直观展示分块结果和统计信息
- **性能分析**: 提供详细的性能统计和基准测试
- **灵活输入**: 支持文件输入、直接文本输入和预设示例
- **多种输出**: 支持详细、简洁和JSON三种输出格式
- **策略对比**: 同时测试多种策略并对比效果（完整版）

### 🔧 支持的分块策略
- `recursive`: 递归字符分块器（两个版本都支持）
- `semantic`: 语义分块器（仅完整版）
- `structure`: 结构分块器（仅完整版）
- `aviation_maintenance`: 航空维修文档分块器（仅完整版）
- `aviation_regulation`: 航空规章分块器（仅完整版）
- `aviation_standard`: 航空标准分块器（仅完整版）
- `aviation_training`: 航空培训分块器（仅完整版）
- `simple`: 简化分块器（完整版降级模式）

## 安装和环境要求

### 环境要求
- Python 3.8+
- RAG Flow项目环境
- 所需依赖包已安装

### 运行前准备
确保在RAG Flow项目根目录下运行脚本，或者正确设置Python路径。

## 使用方法

### 基础用法

#### 1. 演示模式（推荐新手使用）

**简化版本**：
```bash
python src/scripts/test_scripts/test_chunking.py --demo
```

**完整版本**：
```bash
python src/scripts/test_scripts/test_chunking_complete.py --demo
```

运行预设的多种场景演示，包括：
- 通用技术文档分块
- 航空维修手册分块
- 代码文档分块
- 结构化文档分块

#### 2. 查看可用策略（仅完整版）
```bash
python src/scripts/test_scripts/test_chunking_complete.py --list-strategies
```
列出当前环境下所有可用的分块策略。

#### 3. 文件输入测试
```bash
# 简化版本
python src/scripts/test_scripts/test_chunking.py -i /path/to/your/document.txt

# 完整版本
python src/scripts/test_scripts/test_chunking_complete.py -i /path/to/your/document.txt
```
测试指定文件的分块效果。

#### 4. 直接文本测试
```bash
# 简化版本
python src/scripts/test_scripts/test_chunking.py -t "这是要测试的文本内容"

# 完整版本
python src/scripts/test_scripts/test_chunking_complete.py -t "这是要测试的文本内容"
```
直接测试输入的文本内容。

#### 5. 性能测试
```bash
# 简化版本
python src/scripts/test_scripts/test_chunking.py --performance

# 完整版本
python src/scripts/test_scripts/test_chunking_complete.py --performance
```
运行性能基准测试，测试不同大小文档的处理性能。

#### 6. 策略对比（仅完整版）
```bash
python src/scripts/test_scripts/test_chunking_complete.py --compare -t "测试文本"
```
同时使用多种策略处理同一文档，并对比效果。

### 高级用法

#### 自定义分块参数
```bash
# 使用递归分块器，设置分块大小为500，重叠为100
python src/scripts/test_scripts/test_chunking.py -t "测试文本" -s recursive --chunk-size 500 --chunk-overlap 100

# 测试航空维修文档（仅完整版）
python src/scripts/test_scripts/test_chunking_complete.py -i manual.txt -s aviation_maintenance

# 设置最小和最大分块大小
python src/scripts/test_scripts/test_chunking.py -t "测试文本" --min-chunk-size 50 --max-chunk-size 1500
```

#### RecursiveCharacterChunker 高级功能（完整版）

**自定义分隔符列表**：
```bash
# 只使用中文标点作为分隔符
python src/scripts/test_scripts/test_chunking_complete.py -t "第一段。第二段！第三段？" --separators "。" "！" "？"

# 使用段落级分隔符
python src/scripts/test_scripts/test_chunking_complete.py -t "第一章内容第二章内容" --separators "第" "章"

# 使用空格和逗号分隔
python src/scripts/test_scripts/test_chunking_complete.py -t "word1, word2, word3" --separators "," " "
```

**正则表达式分隔符**：
```bash
# 使用正则表达式匹配数字编号
python src/scripts/test_scripts/test_chunking_complete.py -t "1.内容 2.内容 3.内容" --separators "\d+\." --is-separator-regex

# 匹配章节标题
python src/scripts/test_scripts/test_chunking_complete.py -t "第一章 内容 第二章 内容" --separators "第.+?章" --is-separator-regex
```

**分隔符处理选项**：
```bash
# 不保留分隔符
python src/scripts/test_scripts/test_chunking_complete.py -t "句子1。句子2。句子3。" --separators "。" --no-keep-separator

# 添加起始位置索引
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --add-start-index

# 不去除空白字符
python src/scripts/test_scripts/test_chunking_complete.py -t "  文本1  。  文本2  。" --no-strip-whitespace
```

**查看默认分隔符**：
```bash
# 显示RecursiveCharacterChunker的默认分隔符列表
python src/scripts/test_scripts/test_chunking_complete.py --show-separators
```

#### 不同输出格式
```bash
# 简洁输出
python src/scripts/test_scripts/test_chunking.py --demo --output-format simple

# JSON格式输出（便于程序处理）
python src/scripts/test_scripts/test_chunking.py -t "测试文本" --output-format json

# 静默模式（只输出结果）
python src/scripts/test_scripts/test_chunking.py -t "测试文本" --quiet
```

## 命令行参数完整参考表

### 输入参数（互斥组）

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 | 支持版本 |
|------|------|------|--------|------|------|----------|
| `--input` | `-i` | str | - | 指定输入文件路径 | `-i document.txt` | 两个版本 |
| `--text` | `-t` | str | - | 直接输入文本内容 | `-t "测试文本"` | 两个版本 |
| `--demo` | - | flag | False | 运行演示模式 | `--demo` | 两个版本 |
| `--performance` | - | flag | False | 运行性能测试模式 | `--performance` | 两个版本 |
| `--list-strategies` | - | flag | False | 列出可用策略 | `--list-strategies` | 仅完整版 |
| `--show-separators` | - | flag | False | 显示默认分隔符列表 | `--show-separators` | 仅完整版 |

### 分块配置参数

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 | 支持版本 |
|------|------|------|--------|------|------|----------|
| `--strategy` | `-s` | str | auto | 分块策略名称 | `-s recursive` | 完整版全部/简化版仅recursive |
| `--chunk-size` | - | int | 1000 | 分块大小（字符数） | `--chunk-size 500` | 两个版本 |
| `--chunk-overlap` | - | int | 200 | 重叠大小（字符数） | `--chunk-overlap 100` | 两个版本 |
| `--min-chunk-size` | - | int | 100 | 最小分块大小 | `--min-chunk-size 50` | 两个版本 |
| `--max-chunk-size` | - | int | 2000 | 最大分块大小 | `--max-chunk-size 1500` | 两个版本 |

### RecursiveCharacterChunker 特有参数

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 | 支持版本 |
|------|------|------|--------|------|------|----------|
| `--separators` | - | list | 内置列表 | 自定义分隔符列表 | `--separators "。" "！" "？"` | 仅完整版 |
| `--is-separator-regex` | - | flag | False | 分隔符是否为正则表达式 | `--is-separator-regex` | 仅完整版 |
| `--keep-separator` | - | flag | True | 是否保留分隔符 | `--keep-separator` | 仅完整版 |
| `--no-keep-separator` | - | flag | False | 不保留分隔符 | `--no-keep-separator` | 仅完整版 |
| `--add-start-index` | - | flag | False | 添加起始索引信息 | `--add-start-index` | 仅完整版 |
| `--no-strip-whitespace` | - | flag | False | 不去除空白字符 | `--no-strip-whitespace` | 仅完整版 |

### 功能控制参数

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 | 支持版本 |
|------|------|------|--------|------|------|----------|
| `--compare` | - | flag | False | 对比不同策略 | `--compare` | 仅完整版 |
| `--validate` | - | flag | False | 详细验证分块结果 | `--validate` | 仅完整版 |

### 输出控制参数

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 | 支持版本 |
|------|------|------|--------|------|------|----------|
| `--output-format` | - | choice | detailed | 输出格式 | `--output-format json` | 两个版本 |
| `--quiet` | `-q` | flag | False | 静默模式，只输出结果 | `--quiet` | 两个版本 |

### 输出格式选项

| 格式 | 说明 | 适用场景 |
|------|------|----------|
| `detailed` | 详细模式，显示完整分块信息 | 开发调试、详细分析 |
| `simple` | 简洁模式，只显示关键信息 | 快速预览、批量处理 |
| `json` | JSON格式输出 | 程序处理、API集成 |

### 默认分隔符列表（RecursiveCharacterChunker）

| 优先级 | 分类 | 分隔符 | 说明 |
|--------|------|--------|------|
| 1 | 段落级 | `\n\n`, `\n\n\n` | 双换行、三换行 |
| 2 | 中文段落 | `\n第`, `\n章`, `\n节`, `\n条` | 中文章节标记 |
| 3 | 英文段落 | `\nChapter`, `\nSection`, `\nArticle` | 英文章节标记 |
| 4 | 列表标记 | `\n\n•`, `\n\n-`, `\n\n*`, `\n\n1.` | 列表和编号 |
| 5 | 单行 | `\n` | 单换行 |
| 6 | 中文句子 | `。`, `！`, `？` | 中文句号、感叹号、问号 |
| 7 | 英文句子 | `.`, `!`, `?` | 英文句号、感叹号、问号 |
| 8 | 子句 | `；`, `;`, `，`, `,` | 分号、逗号 |
| 9 | 词语 | ` `, `\t` | 空格、制表符 |
| 10 | 特殊字符 | `、`, `：`, `:`, `\u200b` | 中文标点、零宽字符 |

## 输出说明

### 详细模式输出（默认）
```
================================================================================
🔍 RAG Flow 文档分块测试结果
📊 策略: recursive
⏱️  处理时间: 0.045秒
================================================================================

📈 统计信息:
   分块数量: 5
   总字符数: 1234
   平均分块大小: 246.8 字符
   最小分块: 180 字符
   最大分块: 320 字符
   处理速度: 27422 字符/秒
   覆盖率: 100.0%
   平均质量评分: 0.856

📝 详细分块结果:

--- 分块 1 ---
大小: 245 字符 | 词数: 42
质量评分: 0.890
位置: 0-245
内容: 第一章 系统架构设计...
重叠: 系统主要由以下几个核心模块组成...
```

### 简洁模式输出
```
📋 分块概览:
   1. [ 245字符] 第一章 系统架构设计... (质量: 0.89)
   2. [ 312字符] 1.2 技术选型... (质量: 0.85)
   3. [ 198字符] 在技术选型方面... (质量: 0.82)
```

### JSON模式输出
```json
{
  "strategy_used": "recursive",
  "processing_time": 0.045,
  "statistics": {
    "chunk_count": 5,
    "total_characters": 1234,
    "average_chunk_size": 246.8
  },
  "chunks": [
    {
      "content": "第一章 系统架构设计...",
      "character_count": 245,
      "quality_score": 0.890,
      "metadata": {
        "chunk_id": "doc_0001",
        "start_position": 0,
        "end_position": 245
      }
    }
  ]
}
```

## 使用场景示例

### 1. 开发调试场景
```bash
# 测试新的分块参数配置
python src/scripts/test_scripts/test_chunking.py -i test_doc.txt --chunk-size 800 --chunk-overlap 150

# 对比不同策略的效果（完整版）
python src/scripts/test_scripts/test_chunking_complete.py --compare -i doc.txt

# 测试自定义分隔符效果
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --separators "。" "！" --chunk-size 50
```

### 2. 性能优化场景
```bash
# 运行性能基准测试
python src/scripts/test_scripts/test_chunking.py --performance

# 测试大文档处理能力
python src/scripts/test_scripts/test_chunking.py -i large_document.txt --quiet
```

### 3. 文档预处理场景
```bash
# 生成JSON格式的分块结果用于后续处理
python src/scripts/test_scripts/test_chunking.py -i document.txt --output-format json > chunks.json

# 批量测试多个文档
for file in docs/*.txt; do
    echo "Processing $file"
    python src/scripts/test_scripts/test_chunking.py -i "$file" --output-format simple
done
```

### 4. 教学演示场景
```bash
# 运行完整演示
python src/scripts/test_scripts/test_chunking_complete.py --demo

# 查看可用策略
python src/scripts/test_scripts/test_chunking_complete.py --list-strategies

# 查看默认分隔符
python src/scripts/test_scripts/test_chunking_complete.py --show-separators

# 展示RecursiveCharacterChunker高级功能
python src/scripts/test_scripts/test_chunking_complete.py -t "第一段。第二段！第三段？" --separators "。" "！" "？" --chunk-size 15
```

## 故障排除

### 常见问题

1. **导入错误**
   ```
   ImportError: No module named 'rag_flow.src.core.document_processor.chunking'
   ```
   **解决方案**: 确保在RAG Flow项目根目录下运行脚本

2. **文件不存在错误**
   ```
   ❌ 文件不存在: /path/to/file.txt
   ```
   **解决方案**: 检查文件路径是否正确，确保文件存在且可读

3. **分块引擎初始化失败**
   ```
   分块引擎初始化失败: ...
   ```
   **解决方案**: 检查RAG Flow环境是否正确安装，相关依赖是否完整

### 调试技巧

1. **启用详细日志**
   脚本会自动生成日志文件 `logs/chunking_test.log`，可以查看详细的执行信息。

2. **使用简洁模式快速测试**
   ```bash
   python src/scripts/test_scripts/test_chunking.py -t "测试文本" --output-format simple
   ```

3. **JSON输出便于程序处理**
   ```bash
   python src/scripts/test_scripts/test_chunking.py -t "测试文本" --output-format json | jq .
   ```

## RecursiveCharacterChunker 深度解析

### 分隔符优先级系统

RecursiveCharacterChunker 使用分层的分隔符系统，按优先级从高到低尝试分割：

1. **段落级分隔符**：`\n\n`, `\n第`, `\n章`, `\n节` 等
2. **句子级分隔符**：`。`, `！`, `？`, `.`, `!`, `?` 等
3. **子句级分隔符**：`；`, `;`, `，`, `,` 等
4. **词语级分隔符**：空格, 制表符等
5. **特殊字符**：Unicode标点符号等

### 工作原理

1. **递归分割**：如果使用当前分隔符分割后的片段仍然太大，会尝试下一个分隔符
2. **智能边界**：优先在语义边界处分割，保持内容的完整性
3. **重叠处理**：支持分块间的内容重叠，保持上下文连续性
4. **分隔符保留**：可选择保留或移除分隔符

### 高级配置示例

#### 处理中文文档
```bash
# 中文段落分块
python test_chunking_complete.py -t "第一段内容。第二段内容。" --separators "第" "。" --chunk-size 50

# 中文列表分块
python test_chunking_complete.py -t "1、第一项 2、第二项 3、第三项" --separators "、" --chunk-size 20
```

#### 处理代码文档
```bash
# 按函数分块
python test_chunking_complete.py -i code.py --separators "def " "class " --chunk-size 500

# 按注释分块
python test_chunking_complete.py -i code.py --separators "# " "## " --chunk-size 300
```

#### 处理结构化文档
```bash
# 按标题分块
python test_chunking_complete.py -i doc.md --separators "# " "## " "### " --chunk-size 800

# 按章节分块
python test_chunking_complete.py -i manual.txt --separators "Chapter" "Section" --chunk-size 1000
```

### 性能优化建议

1. **合理设置分块大小**：根据下游任务需求调整 `chunk_size`
2. **优化分隔符列表**：针对特定文档类型自定义分隔符
3. **控制重叠大小**：平衡上下文保持和存储效率
4. **使用正则表达式**：处理复杂的分割模式

## 接口开发指南

### 🚀 直接复用现有代码

现有的测试脚本代码可以直接用于开发Web API或其他接口，主要复用以下组件：

#### 核心组件复用

1. **SafeChunkingEngine 类**
   - 位置：`test_chunking_complete.py` 中的 `SafeChunkingEngine`
   - 功能：智能依赖处理、自动降级、完整参数支持
   - 复用方式：直接提取类定义，作为API的核心处理引擎

2. **ChunkingTester 类**
   - 位置：`test_chunking_complete.py` 中的 `ChunkingTester`
   - 功能：分块测试、统计计算、结果验证
   - 复用方式：提取核心方法，封装为API服务函数

#### 接口开发方案

**方案一：FastAPI RESTful 接口**
```python
# 基于现有代码的API接口示例
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# 直接复用现有的 SafeChunkingEngine 和相关类
from your_module import SafeChunkingEngine, ChunkingTester

class ChunkingRequest(BaseModel):
    text: str
    chunk_size: int = 1000
    chunk_overlap: int = 200
    strategy: Optional[str] = None
    separators: Optional[List[str]] = None
    is_separator_regex: bool = False
    keep_separator: bool = True
    # ... 其他参数

class ChunkingResponse(BaseModel):
    chunks: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    processing_time: float
    strategy_used: str

app = FastAPI()

@app.post("/chunk", response_model=ChunkingResponse)
async def chunk_text(request: ChunkingRequest):
    # 直接使用现有的配置构建逻辑
    config = {
        'chunk_size': request.chunk_size,
        'chunk_overlap': request.chunk_overlap,
        # ... 其他配置
    }

    # 复用现有的测试器
    tester = ChunkingTester(config)
    result = tester.test_chunking(request.text, {'file_name': 'api_input.txt'})

    return ChunkingResponse(**result)
```

**方案二：Flask 简单接口**
```python
from flask import Flask, request, jsonify
# 复用现有组件
from your_module import SafeChunkingEngine

app = Flask(__name__)

@app.route('/chunk', methods=['POST'])
def chunk_text():
    data = request.json

    # 直接使用现有的配置处理逻辑
    config = {k: v for k, v in data.items() if k != 'text'}

    engine = SafeChunkingEngine(config)
    chunks = engine.chunk_document(data['text'], {'source': 'api'})

    return jsonify({
        'chunks': chunks,
        'chunk_count': len(chunks)
    })
```

**方案三：gRPC 高性能接口**
```python
# 基于现有代码的gRPC服务
import grpc
from concurrent import futures
# 复用现有的核心处理逻辑

class ChunkingService:
    def __init__(self):
        # 复用现有的引擎初始化逻辑
        self.engine = SafeChunkingEngine()

    def ChunkText(self, request, context):
        # 直接使用现有的处理流程
        result = self.engine.chunk_document(request.text, request.metadata)
        return result
```

#### 复用优势

1. **零重构成本**：现有代码已经处理了所有边界情况和错误处理
2. **功能完整**：支持所有RecursiveCharacterChunker参数
3. **智能降级**：自动处理依赖缺失情况
4. **测试充分**：现有代码已经过完整测试验证
5. **文档完整**：参数说明和使用示例都已准备好

#### 建议的接口架构

```
API Layer (FastAPI/Flask/gRPC)
    ↓
Parameter Validation (Pydantic/自定义)
    ↓
SafeChunkingEngine (直接复用)
    ↓
ChunkingTester (复用核心方法)
    ↓
Response Formatting (JSON/Protobuf)
```

#### 部署建议

1. **容器化部署**：使用Docker封装，包含所有依赖
2. **配置外部化**：将默认参数配置化
3. **监控集成**：复用现有的日志记录逻辑
4. **缓存优化**：对相同输入进行结果缓存

### 传统扩展方式

#### 添加新的测试场景
可以修改脚本中的 `_get_sample_text` 方法，添加新的示例文本类型。

#### 自定义输出格式
可以扩展 `visualize_chunks` 方法，添加新的输出格式。

#### 集成到CI/CD
脚本支持静默模式和JSON输出，可以轻松集成到自动化测试流程中。

## 技术支持

如果在使用过程中遇到问题，请：
1. 查看日志文件 `logs/chunking_test.log`
2. 确认RAG Flow环境配置正确
3. 检查输入文件格式和编码
4. 尝试使用演示模式验证基础功能

---

**版本**: v1.0.0  
**作者**: Sniperz  
**更新日期**: 2025-06-19
