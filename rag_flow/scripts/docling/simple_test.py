#!/usr/bin/env python3
"""
简化的Docling测试脚本，用于验证基本功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_basic_import():
    """测试基本导入"""
    print("1. 测试基本导入...")
    try:
        from src.core.document_processor.parsers.docling_parser import DoclingParser, DoclingParseResult
        print("   ✓ DoclingParser导入成功")
        return True
    except Exception as e:
        print(f"   ✗ 导入失败: {e}")
        return False

def test_dependency_check():
    """测试依赖检查"""
    print("2. 测试依赖检查...")
    try:
        from src.core.document_processor.parsers.docling_parser import DoclingParser
        deps = DoclingParser.check_dependencies()
        print("   依赖状态:")
        for dep, available in deps.items():
            status = "✓" if available else "✗"
            print(f"     {dep}: {status}")
        return True
    except Exception as e:
        print(f"   ✗ 依赖检查失败: {e}")
        return False

def test_parser_creation():
    """测试解析器创建"""
    print("3. 测试解析器创建...")
    try:
        from src.core.document_processor.parsers.docling_parser import DoclingParser
        
        # 尝试使用最小配置创建解析器
        config = {
            'enable_ocr': False,
            'enable_table_structure': False,
            'enable_picture_description': False,
            'enable_formula_enrichment': False,
            'enable_code_enrichment': False,
            'generate_picture_images': False
        }
        
        print("   尝试创建解析器...")
        parser = DoclingParser(config)
        print("   ✓ 解析器创建成功")
        
        # 测试格式支持检查
        try:
            supported = parser.get_supported_formats()
            print(f"   ✓ 支持的格式: {len(supported)} 种")
        except Exception as e:
            print(f"   ⚠ 格式检查失败: {e}")
        
        return True
    except Exception as e:
        print(f"   ✗ 解析器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_parsing():
    """测试简单解析"""
    print("4. 测试简单解析...")
    try:
        from src.core.document_processor.parsers.docling_parser import DoclingParser
        
        # 创建测试文件
        test_file = Path("scripts/docling/test_output/simple_test.md")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("# 测试文档\n\n这是一个简单的测试文件。\n\nThis is a simple test file.\n\n测试中文内容。")
        
        print(f"   创建测试文件: {test_file}")
        
        # 尝试解析
        config = {
            'enable_ocr': False,
            'enable_table_structure': False,
            'enable_picture_description': False,
            'enable_formula_enrichment': False,
            'enable_code_enrichment': False,
            'generate_picture_images': False
        }
        
        parser = DoclingParser(config)
        
        print("   开始解析...")
        start_time = time.time()
        result = parser.parse(str(test_file))
        end_time = time.time()
        
        print(f"   ✓ 解析成功，耗时: {end_time - start_time:.2f}秒")
        print(f"   文本长度: {len(result.text_content)} 字符")
        print(f"   文本预览: {result.text_content[:100]}...")
        
        return True
    except Exception as e:
        print(f"   ✗ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("Docling解析器简化测试")
    print("=" * 50)
    
    tests = [
        test_basic_import,
        test_dependency_check,
        test_parser_creation,
        test_simple_parsing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"   ✗ 测试异常: {e}")
            print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
