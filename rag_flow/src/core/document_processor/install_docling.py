#!/usr/bin/env python3
"""
模块名称: install_docling
功能描述: Docling依赖安装脚本，自动检查和安装Docling相关依赖
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import subprocess
import sys
import importlib
from typing import List, Dict, Tuple


def check_package(package_name: str) -> bool:
    """检查包是否已安装"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


def install_package(package_name: str) -> bool:
    """安装包"""
    try:
        print(f"正在安装 {package_name}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {package_name} 安装失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def check_and_install_dependencies() -> Dict[str, bool]:
    """检查并安装依赖"""
    
    # 定义依赖包
    dependencies = {
        # 核心依赖
        'docling': 'docling',
        'pandas': 'pandas',
        'pillow': 'PIL',
        
        # 可选依赖
        'transformers': 'transformers',
        'torch': 'torch',
        'pytesseract': 'pytesseract',
    }
    
    results = {}
    
    print("检查Docling依赖...")
    print("=" * 50)
    
    for package_name, import_name in dependencies.items():
        print(f"检查 {package_name}...", end=" ")
        
        if check_package(import_name):
            print("✓ 已安装")
            results[package_name] = True
        else:
            print("✗ 未安装")
            
            # 询问是否安装
            if package_name in ['docling', 'pandas', 'pillow']:
                # 核心依赖自动安装
                install_choice = 'y'
                print(f"  {package_name} 是核心依赖，将自动安装")
            else:
                # 可选依赖询问用户
                install_choice = input(f"  是否安装 {package_name}? (y/n): ").lower().strip()
            
            if install_choice == 'y':
                success = install_package(package_name)
                results[package_name] = success
            else:
                print(f"  跳过安装 {package_name}")
                results[package_name] = False
    
    return results


def download_docling_models():
    """下载Docling模型"""
    print("\n下载Docling预训练模型...")
    print("=" * 50)
    
    try:
        # 检查docling-tools是否可用
        result = subprocess.run(
            ["docling-tools", "--help"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("正在下载Docling模型...")
            result = subprocess.run(
                ["docling-tools", "models", "download"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ Docling模型下载成功")
                return True
            else:
                print(f"✗ Docling模型下载失败: {result.stderr}")
                return False
        else:
            print("✗ docling-tools命令不可用，请确保Docling正确安装")
            return False
            
    except FileNotFoundError:
        print("✗ docling-tools命令未找到，请确保Docling正确安装")
        return False
    except Exception as e:
        print(f"✗ 下载模型时出错: {e}")
        return False


def test_docling_installation():
    """测试Docling安装"""
    print("\n测试Docling安装...")
    print("=" * 50)
    
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        
        print("✓ Docling核心模块导入成功")
        
        # 测试创建转换器
        converter = DocumentConverter()
        print("✓ DocumentConverter创建成功")
        
        # 检查支持的格式
        supported_formats = [fmt.value for fmt in InputFormat]
        print(f"✓ 支持的格式: {', '.join(supported_formats)}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Docling导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ Docling测试失败: {e}")
        return False


def generate_installation_report(results: Dict[str, bool]):
    """生成安装报告"""
    print("\n安装报告")
    print("=" * 50)
    
    core_deps = ['docling', 'pandas', 'pillow']
    optional_deps = ['transformers', 'torch', 'pytesseract']
    
    print("核心依赖:")
    for dep in core_deps:
        status = "✓ 已安装" if results.get(dep, False) else "✗ 未安装"
        print(f"  {dep}: {status}")
    
    print("\n可选依赖:")
    for dep in optional_deps:
        status = "✓ 已安装" if results.get(dep, False) else "✗ 未安装"
        print(f"  {dep}: {status}")
    
    # 检查核心功能是否可用
    core_available = all(results.get(dep, False) for dep in core_deps)
    
    print(f"\n核心功能可用: {'✓ 是' if core_available else '✗ 否'}")
    
    if core_available:
        print("\n✓ Docling解析器可以正常使用！")
        print("\n使用示例:")
        print("```python")
        print("from rag_flow.src.core.document_processor.parsers import DoclingParser")
        print("parser = DoclingParser()")
        print("result = parser.parse('document.pdf')")
        print("```")
    else:
        print("\n✗ 核心依赖缺失，请安装必需的依赖包")
        missing_deps = [dep for dep in core_deps if not results.get(dep, False)]
        print(f"缺失的依赖: {', '.join(missing_deps)}")


def main():
    """主函数"""
    print("Docling依赖安装脚本")
    print("=" * 50)
    print("此脚本将检查并安装Docling文档处理器所需的依赖包")
    print()
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("✗ 错误: Docling需要Python 3.8或更高版本")
        print(f"当前Python版本: {sys.version}")
        sys.exit(1)
    
    print(f"✓ Python版本: {sys.version}")
    print()
    
    # 检查并安装依赖
    results = check_and_install_dependencies()
    
    # 如果Docling安装成功，下载模型
    if results.get('docling', False):
        download_choice = input("\n是否下载Docling预训练模型? (推荐) (y/n): ").lower().strip()
        if download_choice == 'y':
            download_docling_models()
    
    # 测试安装
    if results.get('docling', False):
        test_docling_installation()
    
    # 生成报告
    generate_installation_report(results)
    
    print("\n安装脚本执行完成！")


if __name__ == "__main__":
    main()
