# Docling测试脚本快速入门

## 环境准备

```bash
# 1. 进入项目目录
cd rag_flow

# 2. 激活uv虚拟环境
source .venv/bin/activate

# 3. 验证环境
uv run python scripts/docling/test_docling.py --test-mode dependency-check
```

## 基础测试

### 1. 测试单个文件
```bash
# 测试Markdown文件
uv run python scripts/docling/test_docling.py \
  --input-file scripts/docling/test_output/sample_test.md \
  --verbose

# 测试HTML文件
uv run python scripts/docling/test_docling.py \
  --input-file scripts/docling/test_output/batch_test/doc2.html \
  --verbose
```

### 2. 批量测试
```bash
# 批量测试目录中的所有文件
uv run python scripts/docling/test_docling.py \
  --input-dir scripts/docling/test_output/batch_test \
  --verbose \
  --save-results
```

### 3. 预设配置对比
```bash
# 对比不同预设配置的效果
uv run python scripts/docling/test_docling.py \
  --input-file scripts/docling/test_output/sample_test.md \
  --test-mode preset-comparison \
  --save-results
```

## 高级用法

### 1. 自定义配置
```bash
# 禁用OCR，使用快速表格模式
uv run python scripts/docling/test_docling.py \
  --input-file document.pdf \
  --disable-ocr \
  --table-mode fast \
  --verbose
```

### 2. 学术文档处理
```bash
# 使用学术预设，启用公式和代码识别
uv run python scripts/docling/test_docling.py \
  --input-file academic_paper.pdf \
  --preset academic \
  --save-results
```

### 3. 表格专用处理
```bash
# 专注表格处理，使用高精度模式
uv run python scripts/docling/test_docling.py \
  --input-file spreadsheet.xlsx \
  --preset table_focus \
  --verbose
```

## 结果查看

### 1. 控制台输出
脚本会实时显示处理进度和结果摘要。

### 2. 保存的文件（使用 --save-results）
- `test_output/test_results.json` - 详细JSON报告
- `test_output/test_summary.csv` - CSV摘要数据
- `test_output/test_report.md` - Markdown可读报告

### 3. 查看报告
```bash
# 查看Markdown报告
cat test_output/test_report.md

# 查看JSON详细结果
cat test_output/test_results.json | jq .

# 在Excel中打开CSV摘要
open test_output/test_summary.csv
```

## 常见问题

### Q: 脚本运行很慢？
A: Docling初始化需要5-10秒，这是正常现象。后续处理会很快。

### Q: 提示文件格式不支持？
A: 检查文件扩展名，.txt文件需要重命名为.md。

### Q: 导入错误？
A: 确保在项目根目录(rag_flow)下运行，并激活了uv虚拟环境。

### Q: 内存不足？
A: 使用 `--max-file-size` 限制文件大小，或分批处理大文件。

## 性能参考

基于测试环境(Python 3.12, Docling 2.40.0)的性能参考：

| 文件类型 | 文件大小 | 处理时间 | 备注 |
|----------|----------|----------|------|
| Markdown | 1KB | 0.1s | 最快 |
| CSV | 200B | 0.01s | 极快 |
| HTML | 800B | 0.2s | 较快 |
| PDF | 1MB | 2-5s | 取决于复杂度 |

## 下一步

1. 阅读完整的 [README.md](README.md) 了解所有功能
2. 查看 [参数说明表格](README.md#参数说明) 了解配置选项
3. 尝试不同的预设配置和测试模式
4. 根据需要调整配置参数优化性能
