#!/bin/bash
# Docling测试脚本演示
# 展示所有主要功能的使用方法

echo "Docling文档解析器测试脚本演示"
echo "================================"

# 确保在正确的目录
if [ ! -f "scripts/docling/test_docling.py" ]; then
    echo "错误: 请在项目根目录(rag_flow)下运行此脚本"
    exit 1
fi

# 激活虚拟环境
echo "1. 激活uv虚拟环境..."
source .venv/bin/activate

echo -e "\n2. 检查依赖状态..."
uv run python scripts/docling/test_docling.py --test-mode dependency-check

echo -e "\n3. 单文件测试 - 测试Markdown文档..."
uv run python scripts/docling/test_docling.py \
    --input-file scripts/docling/test_output/sample_test.md \
    --verbose

echo -e "\n4. 批量测试 - 测试多个文件..."
uv run python scripts/docling/test_docling.py \
    --input-dir scripts/docling/test_output/batch_test \
    --verbose \
    --save-results

echo -e "\n5. 预设配置对比测试..."
uv run python scripts/docling/test_docling.py \
    --input-file scripts/docling/test_output/sample_test.md \
    --test-mode preset-comparison \
    --save-results

echo -e "\n6. 性能基准测试..."
uv run python scripts/docling/test_docling.py \
    --input-dir scripts/docling/test_output/batch_test \
    --test-mode performance \
    --benchmark-iterations 2 \
    --save-results

echo -e "\n7. 错误处理测试 - 测试不支持的格式..."
uv run python scripts/docling/test_docling.py \
    --input-file scripts/docling/test_output/batch_test/unsupported.xyz \
    --verbose

echo -e "\n8. 自定义配置测试 - 禁用OCR..."
uv run python scripts/docling/test_docling.py \
    --input-file scripts/docling/test_output/sample_test.md \
    --disable-ocr \
    --table-mode fast \
    --verbose

echo -e "\n9. 学术文档预设测试..."
uv run python scripts/docling/test_docling.py \
    --input-file scripts/docling/test_output/sample_test.md \
    --preset academic \
    --verbose

echo -e "\n演示完成！"
echo "================================"
echo "生成的报告文件位于 test_output/ 目录："
echo "- test_results.json (详细JSON报告)"
echo "- test_summary.csv (CSV摘要)"
echo "- test_report.md (Markdown报告)"
echo "- benchmark_results.json (性能基准测试)"
echo "- preset_comparison.json (预设对比)"
echo "- error_analysis.json (错误分析)"

echo -e "\n查看Markdown报告:"
echo "cat test_output/test_report.md"

echo -e "\n查看性能基准测试结果:"
echo "cat test_output/benchmark_results.json | jq ."
