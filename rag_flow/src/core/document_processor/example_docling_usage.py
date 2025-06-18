"""
模块名称: example_docling_usage
功能描述: Docling文档处理器使用示例，展示如何使用Docling解析器处理各种格式的文档
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from parsers.docling_parser import DoclingParser, DoclingParseResult
from parsers.document_processor import DocumentProcessor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """基本使用示例"""
    print("=== Docling基本使用示例 ===")
    
    # 检查依赖
    dependencies = DoclingParser.check_dependencies()
    print(f"依赖库状态: {dependencies}")
    
    if not dependencies['docling']:
        print("错误: Docling库未安装，请运行: pip install docling")
        return
    
    # 初始化Docling解析器
    config = {
        'enable_ocr': True,
        'enable_table_structure': True,
        'enable_picture_description': False,  # 需要额外的模型
        'generate_picture_images': True,
        'images_scale': 2
    }
    
    try:
        parser = DoclingParser(config)
        print("Docling解析器初始化成功")
        print(f"支持的格式: {parser.get_supported_formats()}")
    except Exception as e:
        print(f"Docling解析器初始化失败: {e}")
        return
    
    # 示例文档路径（请根据实际情况修改）
    test_files = [
        "test_document.pdf",
        "test_document.docx", 
        "test_document.html",
        "test_data.csv",
        "test_readme.md",
        "test_image.png"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            try:
                print(f"\n处理文件: {file_path}")
                result = parser.parse(file_path)
                
                print(f"文档类型: {result.original_format}")
                print(f"文本长度: {len(result.text_content)}")
                print(f"表格数量: {len(result.structured_data.get('tables', []))}")
                print(f"图片数量: {len(result.structured_data.get('images', []))}")
                print(f"标题数量: {len(result.structured_data.get('headings', []))}")
                
                # 显示文本预览
                preview = result.text_content[:200] + "..." if len(result.text_content) > 200 else result.text_content
                print(f"文本预览: {preview}")
                
            except Exception as e:
                print(f"处理文件 {file_path} 失败: {e}")
        else:
            print(f"文件不存在: {file_path}")


def example_unified_processor():
    """统一文档处理器示例"""
    print("\n=== 统一文档处理器示例 ===")
    
    # 配置统一处理器，启用Docling
    config = {
        'use_docling': True,
        'prefer_docling_for_common_formats': False,  # 对于PDF等格式仍使用传统解析器
        'docling_config': {
            'enable_ocr': True,
            'enable_table_structure': True,
            'generate_picture_images': True
        }
    }
    
    try:
        processor = DocumentProcessor(config)
        print("统一文档处理器初始化成功")
        
        # 获取Docling信息
        docling_info = processor.get_docling_info()
        print(f"Docling状态: {docling_info}")
        
        # 测试文件
        test_files = [
            "test.html",      # 将使用Docling
            "test.csv",       # 将使用Docling
            "test.md",        # 将使用Docling
            "test.pdf",       # 将使用传统PDF解析器
            "test.docx"       # 将使用传统Word解析器
        ]
        
        for file_path in test_files:
            if Path(file_path).exists():
                try:
                    print(f"\n处理文件: {file_path}")
                    
                    # 检查将使用哪个解析器
                    use_docling = processor.should_use_docling(file_path)
                    print(f"使用Docling: {use_docling}")
                    
                    result = processor.parse(file_path)
                    print(f"文档类型: {result.document_type.value}")
                    print(f"文本长度: {len(result.text_content)}")
                    
                except Exception as e:
                    print(f"处理文件 {file_path} 失败: {e}")
            else:
                print(f"文件不存在: {file_path}")
                
    except Exception as e:
        print(f"统一文档处理器初始化失败: {e}")


def example_batch_conversion():
    """批量转换示例"""
    print("\n=== 批量转换示例 ===")
    
    config = {
        'enable_ocr': True,
        'enable_table_structure': True
    }
    
    try:
        parser = DoclingParser(config)
        
        # 批量处理文件
        input_files = [
            "doc1.pdf",
            "doc2.html", 
            "doc3.csv",
            "doc4.md"
        ]
        
        # 过滤存在的文件
        existing_files = [f for f in input_files if Path(f).exists()]
        
        if existing_files:
            print(f"批量处理 {len(existing_files)} 个文件...")
            
            # 批量转换并保存为Markdown
            results = parser.batch_convert(existing_files, output_dir="output_markdown")
            
            print(f"成功处理 {len(results)} 个文件")
            
            for i, result in enumerate(results):
                print(f"文件 {i+1}: {result.metadata.get('file_name', 'unknown')}")
                print(f"  - 原始格式: {result.original_format}")
                print(f"  - 文本长度: {len(result.text_content)}")
                print(f"  - 表格数量: {len(result.structured_data.get('tables', []))}")
        else:
            print("没有找到可处理的文件")
            
    except Exception as e:
        print(f"批量转换失败: {e}")


def example_advanced_features():
    """高级功能示例"""
    print("\n=== 高级功能示例 ===")
    
    # 启用高级功能的配置
    advanced_config = {
        'enable_ocr': True,
        'enable_table_structure': True,
        'enable_picture_description': True,  # 需要视觉模型
        'enable_formula_enrichment': True,   # 公式识别
        'enable_code_enrichment': True,      # 代码识别
        'generate_picture_images': True,
        'images_scale': 2,
        'max_num_pages': 50,                 # 限制页数
        'max_file_size': 50 * 1024 * 1024,   # 限制文件大小50MB
        'enable_remote_services': False      # 不使用远程服务
    }
    
    try:
        parser = DoclingParser(advanced_config)
        print("高级Docling解析器初始化成功")
        
        # 测试文件（包含公式、代码、图片的PDF）
        test_file = "advanced_document.pdf"
        
        if Path(test_file).exists():
            print(f"处理高级文档: {test_file}")
            
            result = parser.parse(test_file)
            
            # 显示高级功能结果
            structured_data = result.structured_data
            
            print(f"表格数量: {len(structured_data.get('tables', []))}")
            print(f"图片数量: {len(structured_data.get('images', []))}")
            print(f"公式数量: {len(structured_data.get('formulas', []))}")
            print(f"代码块数量: {len(structured_data.get('code_blocks', []))}")
            print(f"标题数量: {len(structured_data.get('headings', []))}")
            
            # 显示公式信息
            for i, formula in enumerate(structured_data.get('formulas', [])[:3]):
                print(f"公式 {i+1}: {formula.get('latex', 'N/A')}")
            
            # 显示代码块信息
            for i, code in enumerate(structured_data.get('code_blocks', [])[:3]):
                print(f"代码块 {i+1} ({code.get('language', 'unknown')}): {code.get('code', '')[:100]}...")
                
        else:
            print(f"测试文件不存在: {test_file}")
            
    except Exception as e:
        print(f"高级功能测试失败: {e}")


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    try:
        parser = DoclingParser()
        
        # 测试不存在的文件
        try:
            result = parser.parse("nonexistent_file.pdf")
        except FileNotFoundError as e:
            print(f"预期的文件不存在错误: {e}")
        
        # 测试不支持的格式
        try:
            result = parser.parse("test.xyz")
        except ValueError as e:
            print(f"预期的格式不支持错误: {e}")
        
        # 测试格式检查
        supported = parser.is_format_supported("test.pdf")
        print(f"PDF格式支持: {supported}")
        
        unsupported = parser.is_format_supported("test.xyz")
        print(f"XYZ格式支持: {unsupported}")
        
    except Exception as e:
        print(f"错误处理测试失败: {e}")


if __name__ == "__main__":
    print("Docling文档处理器使用示例")
    print("=" * 50)
    
    # 运行所有示例
    example_basic_usage()
    example_unified_processor()
    example_batch_conversion()
    example_advanced_features()
    example_error_handling()
    
    print("\n示例运行完成！")
