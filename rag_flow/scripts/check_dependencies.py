#!/usr/bin/env python3
"""
模块名称: check_dependencies
功能描述: 依赖检查工具，分析requirements.txt中的版本约束和实际安装版本
创建日期: 2025-01-07
作者: Sniperz
版本: v1.0.0
"""

import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

def parse_requirements(requirements_file: str) -> List[Tuple[str, str]]:
    """解析requirements.txt文件"""
    requirements = []
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 解析包名和版本约束
                    match = re.match(r'^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)\s*([><=!,.\d\s]*)', line.split('#')[0])
                    if match:
                        package_name = match.group(1)
                        version_spec = match.group(2).strip()
                        requirements.append((package_name, version_spec))
    except FileNotFoundError:
        print(f"错误: 找不到文件 {requirements_file}")
        return []
    
    return requirements

def get_latest_version(package_name: str) -> Optional[str]:
    """获取包的最新版本"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'index', 'versions', package_name
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines and '(' in lines[0]:
                return lines[0].split('(')[1].split(')')[0]
    except Exception:
        pass
    
    return None

def get_installed_version(package_name: str) -> Optional[str]:
    """获取已安装包的版本"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'show', package_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()
    except Exception:
        pass
    
    return None

def check_version_compatibility(version_spec: str, available_version: str) -> bool:
    """检查版本是否满足约束条件"""
    if not version_spec or not available_version:
        return True
    
    try:
        # 简单的版本检查（实际应该使用packaging库）
        from packaging import specifiers, version
        spec = specifiers.SpecifierSet(version_spec)
        return available_version in spec
    except ImportError:
        # 如果没有packaging库，进行简单检查
        return True
    except Exception:
        return True

def analyze_dependencies(requirements_file: str = "requirements.txt"):
    """分析依赖关系"""
    print("🔍 依赖分析报告")
    print("=" * 80)
    
    requirements = parse_requirements(requirements_file)
    if not requirements:
        print("❌ 无法解析requirements.txt文件")
        return
    
    print(f"📋 发现 {len(requirements)} 个依赖包")
    print()
    
    results = []
    
    for package_name, version_spec in requirements:
        print(f"🔎 检查 {package_name}...")
        
        # 获取版本信息
        latest_version = get_latest_version(package_name)
        installed_version = get_installed_version(package_name)
        
        # 分析结果
        status = "✅"
        notes = []
        
        if not latest_version:
            status = "❓"
            notes.append("无法获取最新版本信息")
        
        if installed_version:
            if latest_version and installed_version != latest_version:
                notes.append(f"已安装版本 {installed_version} 不是最新版本")
        else:
            notes.append("未安装")
        
        if version_spec and latest_version:
            compatible = check_version_compatibility(version_spec, latest_version)
            if not compatible:
                status = "⚠️"
                notes.append("最新版本不满足约束条件")
        
        results.append({
            'package': package_name,
            'constraint': version_spec,
            'latest': latest_version,
            'installed': installed_version,
            'status': status,
            'notes': notes
        })
        
        print(f"  约束: {version_spec or '无'}")
        print(f"  最新: {latest_version or '未知'}")
        print(f"  已安装: {installed_version or '未安装'}")
        print(f"  状态: {status}")
        if notes:
            for note in notes:
                print(f"  📝 {note}")
        print()
    
    # 生成摘要
    print("📊 摘要")
    print("-" * 40)
    
    total = len(results)
    installed = len([r for r in results if r['installed']])
    outdated = len([r for r in results if r['installed'] and r['latest'] and r['installed'] != r['latest']])
    issues = len([r for r in results if r['status'] in ['⚠️', '❌']])
    
    print(f"总依赖数: {total}")
    print(f"已安装: {installed}")
    print(f"可更新: {outdated}")
    print(f"有问题: {issues}")
    
    if issues > 0:
        print("\n⚠️ 需要注意的依赖:")
        for result in results:
            if result['status'] in ['⚠️', '❌']:
                print(f"  - {result['package']}: {', '.join(result['notes'])}")
    
    return results

def simulate_install_plan(requirements_file: str = "requirements.txt"):
    """模拟安装计划"""
    print("\n🎯 模拟安装计划")
    print("=" * 80)
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            '--dry-run', '-r', requirements_file
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ 依赖解析成功")
            print("\n📦 将要安装的包:")
            
            # 解析输出中的包信息
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Collecting' in line or 'Downloading' in line:
                    print(f"  {line.strip()}")
        else:
            print("❌ 依赖解析失败")
            print(f"错误信息: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ 请求超时")
    except Exception as e:
        print(f"❌ 执行失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="依赖检查工具")
    parser.add_argument(
        '-f', '--file', 
        default='requirements.txt',
        help='requirements文件路径 (默认: requirements.txt)'
    )
    parser.add_argument(
        '--simulate', 
        action='store_true',
        help='模拟安装计划'
    )
    parser.add_argument(
        '--json', 
        action='store_true',
        help='输出JSON格式结果'
    )
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not Path(args.file).exists():
        print(f"❌ 错误: 文件 {args.file} 不存在")
        sys.exit(1)
    
    # 分析依赖
    results = analyze_dependencies(args.file)
    
    # 模拟安装计划
    if args.simulate:
        simulate_install_plan(args.file)
    
    # JSON输出
    if args.json:
        print("\n📄 JSON结果:")
        print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
