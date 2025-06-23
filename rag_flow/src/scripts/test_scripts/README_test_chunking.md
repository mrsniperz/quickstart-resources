# RAG Flow 文档分块测试脚本使用指南

## 概述

本目录包含专门为RAG Flow项目设计的文档分块功能测试脚本：

**`test_chunking_complete.py`** - 完整功能测试脚本，支持所有可用的分块策略和质量评估功能，具有智能依赖处理

该脚本提供了全面的测试功能，包括可视化分块结果、性能统计分析、多种质量评估策略和各种使用场景演示。

## 主要功能

### 🎯 核心功能
- **多策略测试**: 支持所有内置分块策略的测试
- **智能降级**: 当依赖缺失时自动切换到简化模式
- **质量评估**: 支持多种质量评估策略，包括动态评分算法
- **策略别名映射**: 支持general和technical策略别名，提供针对性的质量评估
- **可视化展示**: 直观展示分块结果和统计信息
- **性能分析**: 提供详细的性能统计和基准测试
- **灵活输入**: 支持文件输入、直接文本输入和预设示例
- **多种输出**: 支持详细、简洁和JSON三种输出格式
- **策略对比**: 同时测试多种策略并对比效果

### 🔧 支持的分块策略
- `recursive`: 递归字符分块器
- `semantic`: 语义分块器
- `structure`: 结构分块器
- `aviation_maintenance`: 航空维修文档分块器
- `aviation_regulation`: 航空规章分块器
- `aviation_standard`: 航空标准分块器
- `aviation_training`: 航空培训分块器
- `simple`: 简化分块器（降级模式）

### 🎯 质量评估策略
系统提供七种质量评估策略：

1. **aviation**（默认）：针对航空领域文档优化的评估策略
   - 航空特定性评估(30%) + 语义完整性(25%) + 信息密度(25%) + 结构质量(15%) + 大小适当性(5%)
   - 适用场景：航空维修手册、法规文档、技术标准

2. **basic**：通用文档的基础评估策略
   - 语义完整性(40%) + 信息密度(30%) + 结构质量(20%) + 大小适当性(10%)
   - 适用场景：一般性文档、说明书、报告

3. **semantic**：专注于语义连贯性的评估策略
   - 语义边界(30%) + 主题一致性(25%) + 上下文连贯性(25%) + 语义完整性(20%)
   - 适用场景：学术论文、技术文档、需要高语义连贯性的内容

4. **length_uniformity**：专注于分块长度均匀性的评估策略
   - 大小适当性(40%) + 长度均匀性(30%) + 相对一致性(20%) + 变异系数(10%)
   - 适用场景：需要统一分块大小的应用

5. **content_completeness**：专注于内容完整性的评估策略
   - 信息单元完整性(40%) + 逻辑结构完整性(30%) + 引用完整性(20%) + 上下文依赖完整性(10%)
   - 适用场景：结构化文档、技术手册、需要保证信息完整性的内容

6. **general**：通用策略（策略别名映射）
   - 基于BaseQualityAssessment，配置更平衡的权重参数
   - 语义完整性(35%) + 信息密度(30%) + 结构质量(25%) + 大小适当性(10%)
   - 适用场景：日常办公文档、一般性文章、混合类型文档

7. **technical**：技术文档策略（策略别名映射）
   - 基于SemanticQualityAssessment，针对技术文档优化
   - 主题一致性(30%) + 上下文连贯性(30%) + 语义边界(25%) + 语义完整性(15%)
   - 适用场景：API文档、技术手册、代码文档、配置说明

### ✨ 策略别名映射
- **general策略**：实际使用优化的BaseQualityAssessment实现，权重更平衡
- **technical策略**：实际使用优化的SemanticQualityAssessment实现，专门针对技术文档
- **动态评分**：所有策略都支持基于内容的动态质量评分，不再返回固定值

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
```bash
python src/scripts/test_scripts/test_chunking_complete.py --demo
```

运行预设的多种场景演示，包括：
- 通用技术文档分块
- 航空维修手册分块
- 代码文档分块
- 结构化文档分块

#### 2. 查看可用策略
```bash
python src/scripts/test_scripts/test_chunking_complete.py --list-strategies
```
列出当前环境下所有可用的分块策略。

#### 3. 文件输入测试
```bash
python src/scripts/test_scripts/test_chunking_complete.py -i /path/to/your/document.txt
```
测试指定文件的分块效果。

#### 4. 直接文本测试
```bash
python src/scripts/test_scripts/test_chunking_complete.py -t "这是要测试的文本内容"
```
直接测试输入的文本内容。

#### 5. 性能测试
```bash
python src/scripts/test_scripts/test_chunking_complete.py --performance
```
运行性能基准测试，测试不同大小文档的处理性能。

#### 6. 策略对比
```bash
python src/scripts/test_scripts/test_chunking_complete.py --compare -t "测试文本"
```
同时使用多种策略处理同一文档，并对比效果。

#### 7. 质量评分控制
```bash
# 使用特定质量评估策略
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy technical

# 使用general策略（通用文档）
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy general

# 禁用质量评分功能
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --disable-quality-assessment

# 详细验证质量评分结果
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --validate
```
控制质量评分功能和查看详细的质量评分结果。

### 高级用法

#### 自定义分块参数
```bash
# 使用递归分块器，设置分块大小为500，重叠为100
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" -s recursive --chunk-size 500 --chunk-overlap 100

# 测试航空维修文档
python src/scripts/test_scripts/test_chunking_complete.py -i manual.txt -s aviation_maintenance

# 设置最小和最大分块大小
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --min-chunk-size 50 --max-chunk-size 1500
```

#### RecursiveCharacterChunker 高级功能

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
python src/scripts/test_scripts/test_chunking_complete.py --demo --output-format simple

# JSON格式输出（便于程序处理）
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --output-format json

# 静默模式（只输出结果）
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quiet
```

## 命令行参数完整参考表

### 输入参数（互斥组）

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `--input` | `-i` | str | - | 指定输入文件路径 | `-i document.txt` |
| `--text` | `-t` | str | - | 直接输入文本内容 | `-t "测试文本"` |
| `--demo` | - | flag | False | 运行演示模式 | `--demo` |
| `--performance` | - | flag | False | 运行性能测试模式 | `--performance` |
| `--list-strategies` | - | flag | False | 列出可用策略 | `--list-strategies` |
| `--show-separators` | - | flag | False | 显示默认分隔符列表 | `--show-separators` |

### 分块配置参数

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `--strategy` | `-s` | str | auto | 分块策略名称 | `-s recursive` |
| `--chunk-size` | - | int | 1000 | 分块大小（字符数） | `--chunk-size 500` |
| `--chunk-overlap` | - | int | 200 | 重叠大小（字符数） | `--chunk-overlap 100` |
| `--min-chunk-size` | - | int | 100 | 最小分块大小 | `--min-chunk-size 50` |
| `--max-chunk-size` | - | int | 2000 | 最大分块大小 | `--max-chunk-size 1500` |
| `--disable-quality-assessment` | - | flag | False | 禁用质量评分 | `--disable-quality-assessment` |
| `--quality-strategy` | - | choice | aviation | 质量评估策略 | `--quality-strategy general` |

### 质量评估策略选项

| 策略名称 | 说明 | 适用场景 |
|---------|------|----------|
| `aviation` | 航空领域专用策略（默认） | 航空维修手册、法规文档 |
| `basic` | 基础通用策略 | 一般性文档、说明书 |
| `semantic` | 语义连贯性策略 | 学术论文、技术文档 |
| `length_uniformity` | 长度均匀性策略 | 需要统一分块大小的应用 |
| `content_completeness` | 内容完整性策略 | 结构化文档、技术手册 |
| `general` | 通用策略（别名映射） | 日常办公文档、混合类型文档 |
| `technical` | 技术文档策略（别名映射） | API文档、代码文档、配置说明 |

### RecursiveCharacterChunker 特有参数

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `--separators` | - | list | 内置列表 | 自定义分隔符列表 | `--separators "。" "！" "？"` |
| `--is-separator-regex` | - | flag | False | 分隔符是否为正则表达式 | `--is-separator-regex` |
| `--keep-separator` | - | flag | True | 是否保留分隔符 | `--keep-separator` |
| `--no-keep-separator` | - | flag | False | 不保留分隔符 | `--no-keep-separator` |
| `--add-start-index` | - | flag | False | 添加起始索引信息 | `--add-start-index` |
| `--no-strip-whitespace` | - | flag | False | 不去除空白字符 | `--no-strip-whitespace` |

### 功能控制参数

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `--compare` | - | flag | False | 对比不同策略 | `--compare` |
| `--validate` | - | flag | False | 详细验证分块结果 | `--validate` |

### 输出控制参数

| 参数 | 简写 | 类型 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `--output-format` | - | choice | detailed | 输出格式 | `--output-format json` |
| `--quiet` | `-q` | flag | False | 静默模式，只输出结果 | `--quiet` |

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
python src/scripts/test_scripts/test_chunking_complete.py -i test_doc.txt --chunk-size 800 --chunk-overlap 150

# 对比不同策略的效果
python src/scripts/test_scripts/test_chunking_complete.py --compare -i doc.txt

# 测试自定义分隔符效果
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --separators "。" "！" --chunk-size 50

# 测试不同质量评估策略
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy general
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy technical

# 禁用质量评分功能
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --disable-quality-assessment
```

### 2. 性能优化场景
```bash
# 运行性能基准测试
python src/scripts/test_scripts/test_chunking_complete.py --performance

# 测试大文档处理能力
python src/scripts/test_scripts/test_chunking_complete.py -i large_document.txt --quiet
```

### 3. 文档预处理场景
```bash
# 生成JSON格式的分块结果用于后续处理
python src/scripts/test_scripts/test_chunking_complete.py -i document.txt --output-format json > chunks.json

# 批量测试多个文档
for file in docs/*.txt; do
    echo "Processing $file"
    python src/scripts/test_scripts/test_chunking_complete.py -i "$file" --output-format simple
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

# 展示不同质量评估策略的效果
python src/scripts/test_scripts/test_chunking_complete.py -t "技术文档示例" --quality-strategy technical --validate
python src/scripts/test_scripts/test_chunking_complete.py -t "日常文档示例" --quality-strategy general --validate

# 对比不同质量评估策略
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy aviation
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy technical
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy general
```

## 注意事项

### 环境依赖
- **test_chunking_complete.py**: 具有智能降级功能，在依赖缺失时自动切换到简化模式
- 完整功能需要RAG Flow环境，简化模式只需要基本Python环境

### 推荐使用
- **新手用户**: 建议使用 `test_chunking_complete.py --demo` 开始
- **开发调试**: 建议使用完整功能进行策略对比和质量评估
- **性能测试**: 支持多种策略的性能基准测试
- **生产环境**: 具有良好的错误处理和降级机制

### 性能考虑
- 大文档（>10MB）建议使用 `--quiet` 模式减少输出
- 性能测试模式会生成大量测试数据，请确保有足够的磁盘空间
- 质量评分功能现在支持动态评分，处理时间合理，如不需要可使用 `--disable-quality-assessment` 禁用

### 质量评估特性
- **动态评分**: 所有质量评估策略都基于内容进行动态计算，不再返回固定值
- **策略别名**: general和technical策略通过别名映射实现，提供针对性的评估
- **真实评估**: 语义完整性、信息密度、结构质量等维度都有实际的评估算法

### 输出文件
- 测试结果会保存在 `test_results/` 目录下
- JSON格式输出便于程序处理和后续分析
- 性能报告包含详细的基准测试数据

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
   python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --output-format simple
   ```

3. **JSON输出便于程序处理**
   ```bash
   python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --output-format json | jq .
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

## 质量评分功能

### 质量评分概述

RAG Flow 的分块引擎内置了先进的质量评分功能，用于评估每个分块的质量。质量评分是一个0到1之间的浮点数，值越高表示质量越好。

### 🎯 核心特性

1. **动态评分算法**：基于文本内容进行实时计算，不再返回固定值
2. **多维度评估**：从语义完整性、信息密度、结构质量等多个维度综合评估
3. **策略别名映射**：支持general和technical策略别名，提供针对性评估
4. **智能权重配置**：不同策略采用不同的评估权重，适应各种文档类型

### 🔧 评估维度详解

#### 语义完整性评估
- **句子完整性**：检查句子结构和结束标点
- **段落完整性**：评估段落结构的合理性
- **语义单元完整性**：检测定义、列举等语义单元
- **截断检测**：识别明显的内容截断标志

#### 信息密度评估
- **有效字符比例**：非空白字符占比
- **关键词密度**：技术词汇和重要概念的分布
- **数值信息密度**：数字、参数等技术信息的密度
- **冗余度检测**：重复内容的识别和评估

#### 结构质量评估
- **标题结构**：标题层次和格式规范性
- **段落结构**：段落组织的合理性
- **列表结构**：列表格式的规范性
- **格式一致性**：整体格式的统一性

### 📊 质量评估策略对比

| 策略 | 语义完整性 | 信息密度 | 结构质量 | 其他维度 | 适用场景 |
|------|-----------|----------|----------|----------|----------|
| **aviation** | 25% | 25% | 15% | 航空特定性30% + 大小适当性5% | 航空文档 |
| **basic** | 40% | 30% | 20% | 大小适当性10% | 通用文档 |
| **semantic** | 20% | - | - | 语义边界30% + 主题一致性25% + 上下文连贯性25% | 学术技术文档 |
| **general** | 35% | 30% | 25% | 大小适当性10% | 日常办公文档 |
| **technical** | 15% | - | - | 主题一致性30% + 上下文连贯性30% + 语义边界25% | 技术文档 |

### 使用示例

```bash
# 使用默认质量评估策略（aviation）
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本"

# 使用general质量评估策略（通用文档）
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy general

# 使用technical质量评估策略（技术文档）
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --quality-strategy technical

# 对比不同策略的评分效果
python src/scripts/test_scripts/test_chunking_complete.py -t "技术文档示例" --quality-strategy aviation
python src/scripts/test_scripts/test_chunking_complete.py -t "技术文档示例" --quality-strategy technical
python src/scripts/test_scripts/test_chunking_complete.py -t "技术文档示例" --quality-strategy general

# 禁用质量评分功能
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --disable-quality-assessment

# 查看质量评分详细结果
python src/scripts/test_scripts/test_chunking_complete.py -t "测试文本" --validate
```

### 🎯 策略选择建议

- **航空文档**：使用 `aviation` 策略，专门优化航空术语和安全信息
- **技术文档**：使用 `technical` 策略，注重逻辑连贯性和主题一致性
- **日常文档**：使用 `general` 策略，平衡各个评估维度
- **学术论文**：使用 `semantic` 策略，强调语义完整性
- **混合文档**：使用 `basic` 策略，提供基础的通用评估

---

## 更新日志

### v2.0.0 (2024-01-15)
- ✨ **新增**: 实现general和technical策略别名映射
- 🚀 **优化**: 完善BaseQualityAssessment核心方法，支持真实的动态质量评分
- 🔧 **修复**: 解决简化模式下固定返回0.8评分的问题
- 📝 **更新**: 移除test_chunking.py，统一使用test_chunking_complete.py
- 🎯 **增强**: 质量评估策略现在支持7种选择：aviation, basic, semantic, length_uniformity, content_completeness, general, technical
- 💡 **改进**: 策略别名映射提供更针对性的文档类型评估

### v1.0.0 (2025-06-19)
- 🎉 初始版本发布
- 📦 支持多种分块策略
- 🔍 基础质量评估功能
- 📊 性能测试和策略对比

---

**版本**: v2.0.0
**作者**: Sniperz
**更新日期**: 2024-01-15
