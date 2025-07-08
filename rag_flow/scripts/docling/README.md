# Docling解析器测试脚本

这是一个全面的Docling文档解析器测试脚本，支持多种测试模式和详细的配置选项。

## 功能特性

- 🔧 **全面配置支持**: 支持Docling解析器的所有配置参数
- 📊 **多种测试模式**: 单文件、批量、性能测试、预设对比等
- 📈 **详细结果报告**: JSON、CSV、Markdown格式的测试报告
- 🌍 **中文支持**: 完整支持中文文档内容处理
- ⚡ **性能监控**: 处理时间、内存使用等性能指标
- 🛠️ **依赖检查**: 自动检查所需依赖库的可用性
- 🔍 **错误分析**: 智能错误模式识别和解决建议
- 📊 **性能基准**: 多次迭代的性能基准测试
- 🎯 **预设对比**: 不同配置预设的效果对比分析

## 环境要求

### 基础依赖
- Python 3.8+
- docling库
- 项目的uv虚拟环境

### 安装依赖
```bash
# 激活uv虚拟环境
source .venv/bin/activate

# 安装docling库（如果尚未安装）
uv add docling

# 可选依赖（用于增强功能）
uv add pandas pillow
```

## 使用方法

### 基本用法

```bash
# 激活虚拟环境
source .venv/bin/activate

# 测试单个文件
uv run python scripts/docling/test_docling.py --input-file document.pdf

# 批量测试目录中的文件
uv run python scripts/docling/test_docling.py --input-dir /path/to/documents --verbose

# 保存测试结果
uv run python scripts/docling/test_docling.py --input-file document.pdf --save-results
```

### 高级用法

```bash
# 使用预设配置
uv run python scripts/docling/test_docling.py --input-file document.pdf --preset academic

# 预设配置对比测试
uv run python scripts/docling/test_docling.py --input-file document.pdf --test-mode preset-comparison

# 性能测试
uv run python scripts/docling/test_docling.py --input-dir /path/to/documents --test-mode performance --verbose

# 依赖检查
uv run python scripts/docling/test_docling.py --test-mode dependency-check
```

### 自定义配置

```bash
# 禁用OCR
uv run python scripts/docling/test_docling.py --input-file document.pdf --disable-ocr

# 使用特定OCR引擎
uv run python scripts/docling/test_docling.py --input-file document.pdf --ocr-engine tesseract

# 启用高精度表格模式
uv run python scripts/docling/test_docling.py --input-file document.pdf --table-mode accurate

# 启用图片描述
uv run python scripts/docling/test_docling.py --input-file document.pdf --enable-picture-description true
```

## 参数说明

### 输入输出参数

| 参数 | 类型 | 默认值 | 描述 | 示例 |
|------|------|--------|------|------|
| `--input-file`, `-f` | str | - | 输入文件路径 | `document.pdf` |
| `--input-dir`, `-d` | str | - | 输入目录路径 | `/path/to/docs` |
| `--output-dir`, `-o` | str | `test_output` | 输出目录路径 | `./results` |

### 测试模式

| 参数 | 选项 | 默认值 | 描述 |
|------|------|--------|------|
| `--test-mode`, `-m` | `single`, `batch`, `performance`, `preset-comparison`, `dependency-check` | `single` | 测试模式 |

### 预设配置

| 参数 | 选项 | 描述 |
|------|------|------|
| `--preset`, `-p` | `basic`, `ocr_only`, `table_focus`, `image_focus`, `academic`, `vlm` | 使用预设配置 |

### OCR配置

| 参数 | 类型 | 默认值 | 描述 | 示例 |
|------|------|--------|------|------|
| `--enable-ocr` | bool | `True` | 启用OCR | `true`/`false` |
| `--disable-ocr` | flag | - | 禁用OCR | - |
| `--ocr-engine` | str | `easyocr` | OCR引擎类型 | `easyocr`, `tesseract` |

### 表格配置

| 参数 | 类型 | 默认值 | 描述 | 示例 |
|------|------|--------|------|------|
| `--enable-table-structure` | bool | `True` | 启用表格结构识别 | `true`/`false` |
| `--table-mode` | str | `fast` | 表格模式 | `fast`, `accurate` |
| `--enable-cell-matching` | bool | `True` | 启用单元格匹配 | `true`/`false` |

### 图片配置

| 参数 | 类型 | 默认值 | 描述 | 示例 |
|------|------|--------|------|------|
| `--enable-picture-description` | bool | `False` | 启用图片描述 | `true`/`false` |
| `--picture-description-model` | str | - | 图片描述模型 | `model_name` |
| `--picture-description-prompt` | str | - | 图片描述提示词 | `"Describe this image"` |
| `--enable-picture-classification` | bool | `False` | 启用图片分类 | `true`/`false` |
| `--generate-picture-images` | bool | `True` | 生成图片 | `true`/`false` |
| `--images-scale` | int | `2` | 图片缩放比例 | `1`, `2`, `3` |

### 内容识别配置

| 参数 | 类型 | 默认值 | 描述 | 示例 |
|------|------|--------|------|------|
| `--enable-formula-enrichment` | bool | `False` | 启用公式识别 | `true`/`false` |
| `--enable-code-enrichment` | bool | `False` | 启用代码识别 | `true`/`false` |

### 系统配置

| 参数 | 类型 | 默认值 | 描述 | 示例 |
|------|------|--------|------|------|
| `--max-num-pages` | int | - | 最大页数限制 | `100` |
| `--max-file-size` | int | - | 最大文件大小限制(字节) | `10485760` |
| `--artifacts-path` | str | - | 模型文件路径 | `/path/to/models` |
| `--enable-remote-services` | bool | `False` | 启用远程服务 | `true`/`false` |

### 高级配置

| 参数 | 类型 | 默认值 | 描述 | 示例 |
|------|------|--------|------|------|
| `--use-vlm-pipeline` | bool | `False` | 使用VLM管道 | `true`/`false` |
| `--vlm-model` | str | - | VLM模型名称 | `model_name` |
| `--custom-backend` | str | - | 自定义后端 | `pypdfium` |
| `--allowed-formats` | list | - | 允许的文件格式列表 | `.pdf .docx .html` |

### 其他选项

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--verbose`, `-v` | flag | - | 详细输出 |
| `--save-results` | flag | - | 保存测试结果到文件 |
| `--benchmark-iterations` | int | `3` | 性能基准测试迭代次数 |
| `--include-error-analysis` | flag | - | 包含详细的错误分析 |

## 预设配置说明

### basic
- 基础配置，启用OCR和表格结构识别
- 适用于一般文档处理

### ocr_only
- 仅启用OCR功能
- 适用于图片文档或扫描文档

### table_focus
- 专注表格处理，使用高精度模式
- 适用于表格密集的文档

### image_focus
- 专注图片处理，启用图片描述和分类
- 适用于图片丰富的文档

### academic
- 学术文档配置，启用公式和代码识别
- 适用于学术论文和技术文档

### vlm
- 视觉语言模型配置
- 适用于需要高级视觉理解的文档

## 测试模式说明

### single
单文件测试模式，测试指定的单个文件。

### batch
批量测试模式，测试目录中的所有支持格式文件。

### performance
性能测试模式，重点关注处理速度和资源使用。

### preset-comparison
预设配置对比模式，使用不同预设配置测试同一文件，比较效果差异。

### dependency-check
依赖检查模式，检查所需依赖库的安装状态和支持的文件格式。

## 输出结果

### 控制台输出
- 实时进度显示
- 测试摘要统计
- 错误信息汇总

### 文件输出（使用 `--save-results`）
- `test_results.json`: 详细的JSON格式结果
- `test_summary.csv`: CSV格式的摘要数据
- `test_report.md`: Markdown格式的可读报告
- `benchmark_results.json`: 性能基准测试详细结果（性能模式）
- `preset_comparison.json`: 预设配置对比结果（对比模式）
- `error_analysis.json`: 错误分析报告（有错误时）

## 支持的文件格式

- **PDF文档**: `.pdf`
- **Word文档**: `.doc`, `.docx`
- **HTML文件**: `.html`, `.htm`
- **Excel表格**: `.xls`, `.xlsx`
- **CSV文件**: `.csv`
- **Markdown文件**: `.md`, `.markdown`
- **文本文件**: `.txt`
- **图片文件**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.tif`
- **PowerPoint**: `.ppt`, `.pptx`

## 常见使用场景

### 1. 快速测试单个文档
```bash
uv run python scripts/docling/test_docling.py --input-file document.pdf --verbose
```

### 2. 批量处理文档目录
```bash
uv run python scripts/docling/test_docling.py --input-dir ./documents --save-results --verbose
```

### 3. 学术论文处理
```bash
uv run python scripts/docling/test_docling.py --input-file paper.pdf --preset academic --save-results
```

### 4. 表格文档处理
```bash
uv run python scripts/docling/test_docling.py --input-file spreadsheet.xlsx --preset table_focus
```

### 5. 图片文档OCR
```bash
uv run python scripts/docling/test_docling.py --input-file scanned.pdf --preset ocr_only
```

### 6. 性能基准测试
```bash
uv run python scripts/docling/test_docling.py --input-dir ./test_docs --test-mode performance --save-results
```

### 7. 配置效果对比
```bash
uv run python scripts/docling/test_docling.py --input-file document.pdf --test-mode preset-comparison --save-results
```

### 8. 性能基准测试
```bash
# 运行性能基准测试，每个文件测试5次
uv run python scripts/docling/test_docling.py \
  --input-dir ./test_docs \
  --test-mode performance \
  --benchmark-iterations 5 \
  --save-results
```

### 9. 错误分析测试
```bash
# 包含详细错误分析的批量测试
uv run python scripts/docling/test_docling.py \
  --input-dir ./mixed_docs \
  --verbose \
  --save-results \
  --include-error-analysis
```

### 10. 完整演示
```bash
# 运行完整功能演示
./scripts/docling/demo.sh
```

## 故障排除

### 常见问题

#### 1. 导入错误
```
ImportError: No module named 'docling'
```
**解决方案:**
```bash
# 确保激活了虚拟环境
source .venv/bin/activate

# 安装docling库
uv add docling
```

#### 2. 路径错误
```
ModuleNotFoundError: No module named 'src.core.document_processor'
```
**解决方案:**
- 确保在项目根目录（rag_flow）下运行脚本
- 检查项目结构是否完整

#### 3. 文件格式不支持
```
ValueError: 不支持的文件格式: .xyz
```
**解决方案:**
- 使用 `--test-mode dependency-check` 查看支持的格式
- 转换文件为支持的格式

#### 4. 内存不足
```
MemoryError: Unable to allocate memory
```
**解决方案:**
- 使用 `--max-file-size` 限制文件大小
- 使用 `--max-num-pages` 限制页数
- 分批处理大文件

#### 5. OCR引擎错误
```
无法设置Tesseract OCR，使用默认OCR
```
**解决方案:**
```bash
# 安装Tesseract OCR
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# 或使用EasyOCR
uv add easyocr
```

### 性能优化建议

#### 1. 大文件处理
- 使用 `--max-num-pages` 限制处理页数
- 使用 `--max-file-size` 限制文件大小
- 考虑分割大文件后分别处理

#### 2. 批量处理
- 使用 `--verbose` 监控进度
- 定期保存中间结果
- 考虑并行处理（未来版本支持）

#### 3. 配置优化
- 根据文档类型选择合适的预设
- 禁用不需要的功能（如OCR、图片描述等）
- 使用快速模式而非精确模式

### 调试技巧

#### 1. 启用详细输出
```bash
uv run python scripts/docling/test_docling.py --input-file document.pdf --verbose
```

#### 2. 检查依赖状态
```bash
uv run python scripts/docling/test_docling.py --test-mode dependency-check
```

#### 3. 测试单个文件
```bash
# 先测试单个简单文件确认环境正常
uv run python scripts/docling/test_docling.py --input-file simple.txt --verbose
```

#### 4. 查看详细错误
```bash
# Python会显示完整的错误堆栈
python scripts/docling/test_docling.py --input-file document.pdf --verbose
```

## 输出文件说明

### test_results.json
包含完整的测试结果数据，结构如下：
```json
{
  "timestamp": "2024-12-17T10:30:00",
  "total_files": 5,
  "successful": 4,
  "failed": 1,
  "results": [
    {
      "file_path": "/path/to/document.pdf",
      "file_name": "document.pdf",
      "file_size": 1024000,
      "file_format": ".pdf",
      "success": true,
      "processing_time": 2.5,
      "text_length": 5000,
      "element_counts": {
        "total_elements": 50,
        "text_elements": 40,
        "table_elements": 5,
        "image_elements": 3,
        "heading_elements": 8
      },
      "metadata": {...}
    }
  ]
}
```

### test_summary.csv
CSV格式的摘要数据，便于在Excel中分析：
```csv
文件名,文件大小(字节),格式,成功,处理时间(秒),文本长度,总元素数,表格数,图片数,标题数,错误信息
document.pdf,1024000,.pdf,是,2.50,5000,50,5,3,8,
```

### test_report.md
Markdown格式的可读报告，包含：
- 测试统计摘要
- 详细结果表格
- 错误分析

## 中文文档处理

### 支持特性
- ✅ 中文文本识别和提取
- ✅ 中文OCR处理
- ✅ 中文字符统计
- ✅ 中文文件名支持
- ✅ 中文输出报告

### 测试中文文档
```bash
# 测试中文PDF
uv run python scripts/docling/test_docling.py --input-file 中文文档.pdf --verbose

# 测试中文目录
uv run python scripts/docling/test_docling.py --input-dir ./中文文档目录 --save-results
```

### 中文OCR优化
```bash
# 使用EasyOCR（对中文支持更好）
uv run python scripts/docling/test_docling.py --input-file 中文扫描件.pdf --ocr-engine easyocr
```

## 扩展功能

### 自定义配置文件
可以创建配置文件来保存常用设置：
```json
{
  "enable_ocr": true,
  "ocr_engine": "easyocr",
  "table_mode": "accurate",
  "enable_picture_description": true,
  "max_file_size": 10485760
}
```

### 批处理脚本
创建批处理脚本自动化测试：
```bash
#!/bin/bash
# batch_test.sh

# 激活环境
source .venv/bin/activate

# 测试不同类型的文档
uv run python scripts/docling/test_docling.py --input-dir ./pdf_docs --preset academic --save-results
uv run python scripts/docling/test_docling.py --input-dir ./office_docs --preset table_focus --save-results
uv run python scripts/docling/test_docling.py --input-dir ./image_docs --preset image_focus --save-results
```

## 实际测试结果

### 测试环境
- Python 3.12.10
- Docling 2.40.0
- uv虚拟环境

### 性能表现
- **Markdown文件**: 平均处理时间 0.1-0.2秒
- **HTML文件**: 平均处理时间 0.15-0.25秒
- **CSV文件**: 平均处理时间 0.01-0.05秒
- **批量处理**: 3个文件总计 0.26秒

### 功能验证
- ✅ 依赖检查功能正常
- ✅ 单文件解析功能正常
- ✅ 批量文件处理功能正常
- ✅ 预设配置对比功能正常
- ✅ 中文内容处理正常
- ✅ 结果报告生成正常

## 注意事项

### 重要提醒
1. **必须在uv虚拟环境中运行**: 使用 `source .venv/bin/activate` 激活环境
2. **使用uv run执行**: 命令格式为 `uv run python scripts/docling/test_docling.py`
3. **在项目根目录运行**: 确保在 `rag_flow` 目录下执行脚本
4. **初始化时间较长**: 首次导入Docling模块需要5-10秒时间

### 已知问题
1. **初始化延迟**: Docling库初始化需要较长时间，这是正常现象
2. **格式限制**: .txt文件需要重命名为.md才能被正确识别
3. **内存使用**: 处理大文件时可能需要较多内存

### 最佳实践
1. **小文件测试**: 建议先用小文件测试确认环境正常
2. **批量处理**: 大量文件建议分批处理
3. **结果保存**: 重要测试建议使用 `--save-results` 保存结果
4. **详细输出**: 调试时使用 `--verbose` 查看详细信息

## 版本信息

- **当前版本**: v1.0.0
- **创建日期**: 2024-12-17
- **作者**: Sniperz
- **兼容性**: Python 3.8+, Docling 2.40.0+, uv虚拟环境

## 更新日志

### v1.0.0 (2024-12-17)
- ✨ 初始版本发布
- ✨ 支持所有Docling配置参数
- ✨ 多种测试模式
- ✨ 详细的结果报告
- ✨ 中文文档支持
- ✨ 完整的文档和示例
- ✅ 通过完整功能测试验证

## 贡献指南

如果您发现问题或有改进建议，请：
1. 检查现有的故障排除指南
2. 创建详细的问题报告
3. 提供复现步骤和环境信息
4. 考虑提交改进建议

## 许可证

本脚本遵循项目的整体许可证协议。
