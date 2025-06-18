#!/usr/bin/env python3
"""
模块名称: test_docling_standalone
功能描述: Docling解析器独立测试脚本，不依赖其他解析器
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import sys
import tempfile
from pathlib import Path

# 直接导入Docling解析器，避免导入其他解析器
sys.path.insert(0, str(Path(__file__).parent))

def test_docling_availability():
    """测试Docling可用性"""
    print("=== 测试Docling可用性 ===")
    
    try:
        import docling
        print("✓ Docling库可用")
        return True
    except ImportError:
        print("✗ Docling库不可用")
        print("请运行: pip install docling")
        return False

def test_docling_parser_import():
    """测试Docling解析器导入"""
    print("\n=== 测试Docling解析器导入 ===")
    
    try:
        from parsers.docling_parser import DoclingParser, DoclingParseResult, DOCLING_AVAILABLE
        print("✓ DoclingParser导入成功")
        print(f"✓ Docling可用性: {DOCLING_AVAILABLE}")
        return True, DoclingParser
    except ImportError as e:
        print(f"✗ DoclingParser导入失败: {e}")
        return False, None

def test_docling_parser_initialization(DoclingParser):
    """测试Docling解析器初始化"""
    print("\n=== 测试Docling解析器初始化 ===")
    
    try:
        # 基本配置
        config = {
            'enable_ocr': True,
            'enable_table_structure': True,
            'enable_picture_description': False,  # 避免需要额外模型
            'generate_picture_images': True,
            'images_scale': 2
        }
        
        parser = DoclingParser(config)
        print("✓ DoclingParser初始化成功")
        
        # 检查支持的格式
        supported_formats = parser.get_supported_formats()
        print(f"✓ 支持的格式数量: {len(supported_formats)}")
        print(f"✓ 支持的格式: {', '.join(supported_formats[:10])}...")
        
        return True, parser
    except Exception as e:
        print(f"✗ DoclingParser初始化失败: {e}")
        return False, None

def test_format_support_check(parser):
    """测试格式支持检查"""
    print("\n=== 测试格式支持检查 ===")
    
    test_cases = [
        ('test.pdf', True),
        ('test.html', True),
        ('test.csv', True),
        ('test.md', True),
        ('test.png', True),
        ('test.xyz', False),
        ('test.unknown', False)
    ]
    
    all_passed = True
    for filename, expected in test_cases:
        result = parser.is_format_supported(filename)
        status = "✓" if result == expected else "✗"
        print(f"{status} {filename}: {result} (期望: {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_markdown_parsing(parser):
    """测试Markdown文件解析"""
    print("\n=== 测试Markdown文件解析 ===")
    
    # 创建测试Markdown文件
    markdown_content = """# 测试文档

这是一个测试Markdown文档。

## 第一节

这里是第一节的内容。

### 子节

- 列表项1
- 列表项2
- 列表项3

## 第二节

这里是第二节的内容。

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| 1   | 2   | 3   |

```python
def hello():
    print("Hello, World!")
```

## 结论

这是测试文档的结论。
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(markdown_content)
            temp_file = f.name
        
        print(f"✓ 创建测试文件: {temp_file}")
        
        # 解析文件
        result = parser.parse(temp_file)
        
        print("✓ 文件解析成功")
        print(f"✓ 原始格式: {result.original_format}")
        print(f"✓ 文本长度: {len(result.text_content)}")
        print(f"✓ 元数据键: {list(result.metadata.keys())}")
        print(f"✓ 结构化数据键: {list(result.structured_data.keys())}")
        
        # 显示文本预览
        preview = result.text_content[:200] + "..." if len(result.text_content) > 200 else result.text_content
        print(f"✓ 文本预览: {preview}")
        
        # 清理临时文件
        Path(temp_file).unlink()
        print("✓ 清理临时文件")
        
        return True
        
    except Exception as e:
        print(f"✗ Markdown解析失败: {e}")
        # 尝试清理临时文件
        try:
            Path(temp_file).unlink()
        except:
            pass
        return False

def test_csv_parsing(parser):
    """测试CSV文件解析"""
    print("\n=== 测试CSV文件解析 ===")
    
    csv_content = """姓名,年龄,城市
张三,25,北京
李四,30,上海
王五,28,广州
赵六,35,深圳
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_file = f.name
        
        print(f"✓ 创建测试CSV文件: {temp_file}")
        
        # 解析文件
        result = parser.parse(temp_file)
        
        print("✓ CSV文件解析成功")
        print(f"✓ 原始格式: {result.original_format}")
        print(f"✓ 文本长度: {len(result.text_content)}")
        
        # 显示文本预览
        preview = result.text_content[:200] + "..." if len(result.text_content) > 200 else result.text_content
        print(f"✓ 文本预览: {preview}")
        
        # 清理临时文件
        Path(temp_file).unlink()
        print("✓ 清理临时文件")
        
        return True
        
    except Exception as e:
        print(f"✗ CSV解析失败: {e}")
        # 尝试清理临时文件
        try:
            Path(temp_file).unlink()
        except:
            pass
        return False

def test_text_only_extraction(parser):
    """测试仅文本提取"""
    print("\n=== 测试仅文本提取 ===")
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>测试HTML</title>
</head>
<body>
    <h1>标题</h1>
    <p>这是一个段落。</p>
    <ul>
        <li>项目1</li>
        <li>项目2</li>
    </ul>
</body>
</html>"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name
        
        print(f"✓ 创建测试HTML文件: {temp_file}")
        
        # 仅提取文本
        text = parser.extract_text_only(temp_file)
        
        print("✓ 文本提取成功")
        print(f"✓ 提取的文本长度: {len(text)}")
        
        # 显示文本预览
        preview = text[:200] + "..." if len(text) > 200 else text
        print(f"✓ 文本预览: {preview}")
        
        # 清理临时文件
        Path(temp_file).unlink()
        print("✓ 清理临时文件")
        
        return True
        
    except Exception as e:
        print(f"✗ 文本提取失败: {e}")
        # 尝试清理临时文件
        try:
            Path(temp_file).unlink()
        except:
            pass
        return False

def main():
    """主测试函数"""
    print("Docling解析器独立测试")
    print("=" * 50)
    
    # 测试结果
    results = []
    
    # 1. 测试Docling可用性
    docling_available = test_docling_availability()
    results.append(("Docling可用性", docling_available))
    
    if not docling_available:
        print("\n✗ Docling不可用，跳过后续测试")
        return
    
    # 2. 测试解析器导入
    import_success, DoclingParser = test_docling_parser_import()
    results.append(("解析器导入", import_success))
    
    if not import_success:
        print("\n✗ 解析器导入失败，跳过后续测试")
        return
    
    # 3. 测试解析器初始化
    init_success, parser = test_docling_parser_initialization(DoclingParser)
    results.append(("解析器初始化", init_success))
    
    if not init_success:
        print("\n✗ 解析器初始化失败，跳过后续测试")
        return
    
    # 4. 测试格式支持检查
    format_check_success = test_format_support_check(parser)
    results.append(("格式支持检查", format_check_success))
    
    # 5. 测试Markdown解析
    markdown_success = test_markdown_parsing(parser)
    results.append(("Markdown解析", markdown_success))
    
    # 6. 测试CSV解析
    csv_success = test_csv_parsing(parser)
    results.append(("CSV解析", csv_success))
    
    # 7. 测试文本提取
    text_extract_success = test_text_only_extraction(parser)
    results.append(("文本提取", text_extract_success))
    
    # 显示测试结果汇总
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Docling解析器工作正常。")
    else:
        print("⚠️  部分测试失败，请检查相关问题。")

if __name__ == "__main__":
    main()
