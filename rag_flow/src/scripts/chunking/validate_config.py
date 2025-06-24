#!/usr/bin/env python3
"""
模块名称: validate_config
功能描述: 简化分块系统配置验证脚本
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0

使用说明:
    python validate_config.py                    # 验证所有预设配置
    python validate_config.py --preset semantic  # 验证特定预设
    python validate_config.py --detailed         # 详细验证报告
    python validate_config.py --fix-issues       # 尝试修复发现的问题
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.document_processor.chunking.chunking_engine import ChunkingEngine
    from core.document_processor.config.config_manager import get_config_manager
    CHUNKING_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"导入模块失败: {e}")
    CHUNKING_ENGINE_AVAILABLE = False


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.engine = None
        self.config_manager = None
        self.issues = []
        
        if CHUNKING_ENGINE_AVAILABLE:
            try:
                self.engine = ChunkingEngine()
                self.config_manager = get_config_manager()
                print("✅ 配置验证器初始化成功")
            except Exception as e:
                print(f"❌ 配置验证器初始化失败: {e}")
        else:
            print("❌ 分块引擎不可用")
    
    def validate_config_file(self) -> Tuple[bool, List[str]]:
        """
        验证配置文件的基本结构
        
        Returns:
            tuple: (是否有效, 问题列表)
        """
        issues = []
        
        try:
            config_path = project_root / "src/core/document_processor/config/chunking_config.yaml"
            
            if not config_path.exists():
                issues.append(f"配置文件不存在: {config_path}")
                return False, issues
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查基本结构
            if not isinstance(config, dict):
                issues.append("配置文件根节点必须是字典")
                return False, issues
            
            # 检查预设配置
            if 'presets' not in config:
                issues.append("配置文件缺少 'presets' 节点")
            else:
                presets = config['presets']
                if not isinstance(presets, dict):
                    issues.append("'presets' 必须是字典类型")
                elif len(presets) == 0:
                    issues.append("'presets' 不能为空")
                else:
                    print(f"✅ 找到 {len(presets)} 个预设配置")
            
            return len(issues) == 0, issues
            
        except yaml.YAMLError as e:
            issues.append(f"YAML格式错误: {e}")
            return False, issues
        except Exception as e:
            issues.append(f"配置文件验证失败: {e}")
            return False, issues
    
    def validate_preset(self, preset_name: str) -> Tuple[bool, List[str]]:
        """
        验证单个预设配置
        
        Args:
            preset_name: 预设名称
            
        Returns:
            tuple: (是否有效, 问题列表)
        """
        issues = []
        
        if not self.engine:
            issues.append("分块引擎不可用，无法验证预设")
            return False, issues
        
        try:
            # 获取预设信息
            preset_info = self.engine.get_preset_info(preset_name)
            
            if 'error' in preset_info:
                issues.append(f"预设 '{preset_name}' 不存在或无法加载")
                return False, issues
            
            # 验证必需字段
            required_fields = ['chunk_size', 'separators']
            for field in required_fields:
                if field not in preset_info.get('config', {}):
                    issues.append(f"预设 '{preset_name}' 缺少必需字段: {field}")
            
            # 验证字段值
            config = preset_info.get('config', {})
            
            # 验证chunk_size
            chunk_size = config.get('chunk_size')
            if chunk_size is not None:
                if not isinstance(chunk_size, int) or chunk_size <= 0:
                    issues.append(f"预设 '{preset_name}' 的 chunk_size 必须是正整数")
                elif chunk_size > 10000:
                    issues.append(f"预设 '{preset_name}' 的 chunk_size ({chunk_size}) 可能过大")
            
            # 验证chunk_overlap
            chunk_overlap = config.get('chunk_overlap')
            if chunk_overlap is not None:
                if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
                    issues.append(f"预设 '{preset_name}' 的 chunk_overlap 必须是非负整数")
                elif chunk_size and chunk_overlap >= chunk_size:
                    issues.append(f"预设 '{preset_name}' 的 chunk_overlap 不应大于等于 chunk_size")
            
            # 验证separators
            separators = config.get('separators')
            if separators is not None:
                if not isinstance(separators, list):
                    issues.append(f"预设 '{preset_name}' 的 separators 必须是列表")
                elif len(separators) == 0:
                    issues.append(f"预设 '{preset_name}' 的 separators 不能为空")
                else:
                    # 检查分隔符类型
                    for i, sep in enumerate(separators):
                        if not isinstance(sep, str):
                            issues.append(f"预设 '{preset_name}' 的 separators[{i}] 必须是字符串")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"验证预设 '{preset_name}' 时发生错误: {e}")
            return False, issues
    
    def validate_all_presets(self) -> Dict[str, Tuple[bool, List[str]]]:
        """
        验证所有预设配置
        
        Returns:
            dict: 预设名称 -> (是否有效, 问题列表)
        """
        results = {}
        
        if not self.engine:
            return results
        
        try:
            presets = self.engine.get_available_presets()
            
            for preset in presets:
                print(f"验证预设: {preset}")
                is_valid, issues = self.validate_preset(preset)
                results[preset] = (is_valid, issues)
                
                if is_valid:
                    print(f"  ✅ 预设 '{preset}' 验证通过")
                else:
                    print(f"  ❌ 预设 '{preset}' 验证失败:")
                    for issue in issues:
                        print(f"    - {issue}")
            
            return results
            
        except Exception as e:
            print(f"❌ 验证所有预设时发生错误: {e}")
            return results
    
    def test_preset_functionality(self, preset_name: str) -> Tuple[bool, List[str]]:
        """
        测试预设的实际功能
        
        Args:
            preset_name: 预设名称
            
        Returns:
            tuple: (是否正常工作, 问题列表)
        """
        issues = []
        
        if not self.engine:
            issues.append("分块引擎不可用，无法测试功能")
            return False, issues
        
        try:
            # 测试文本
            test_text = """
第一章 测试文档

这是一个用于测试分块功能的示例文档。它包含多个段落和句子，用来验证分块器是否能正常工作。

第二章 功能验证

本章节用于验证分块器的各种功能，包括：
1. 段落分割
2. 句子分割
3. 重叠处理
4. 质量评估

结论：如果能看到这个分块，说明功能正常。
"""
            
            metadata = {
                'file_name': f'test_{preset_name}.txt',
                'document_type': 'test',
                'title': f'预设功能测试: {preset_name}'
            }
            
            # 执行分块
            chunks = self.engine.chunk_document(test_text, metadata, preset_name)
            
            # 验证结果
            if not chunks:
                issues.append(f"预设 '{preset_name}' 没有产生任何分块")
            elif len(chunks) == 1 and len(test_text) > 1000:
                issues.append(f"预设 '{preset_name}' 可能没有正确分割文本")
            else:
                # 检查分块质量
                total_chars = sum(len(chunk.content) if hasattr(chunk, 'content') 
                                else chunk.get('content', '') for chunk in chunks)
                if total_chars < len(test_text) * 0.8:
                    issues.append(f"预设 '{preset_name}' 可能丢失了部分文本内容")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"测试预设 '{preset_name}' 功能时发生错误: {e}")
            return False, issues
    
    def generate_report(self, detailed: bool = False) -> None:
        """
        生成验证报告
        
        Args:
            detailed: 是否生成详细报告
        """
        print("\n" + "="*80)
        print("📋 简化分块系统配置验证报告")
        print("="*80)
        
        # 验证配置文件
        print("\n🔍 配置文件验证:")
        config_valid, config_issues = self.validate_config_file()
        if config_valid:
            print("  ✅ 配置文件结构正确")
        else:
            print("  ❌ 配置文件存在问题:")
            for issue in config_issues:
                print(f"    - {issue}")
            return
        
        # 验证所有预设
        print("\n🔍 预设配置验证:")
        preset_results = self.validate_all_presets()
        
        valid_presets = []
        invalid_presets = []
        
        for preset, (is_valid, issues) in preset_results.items():
            if is_valid:
                valid_presets.append(preset)
            else:
                invalid_presets.append((preset, issues))
        
        print(f"  ✅ 有效预设: {len(valid_presets)}")
        print(f"  ❌ 无效预设: {len(invalid_presets)}")
        
        if detailed and invalid_presets:
            print("\n📝 详细问题列表:")
            for preset, issues in invalid_presets:
                print(f"\n  预设 '{preset}':")
                for issue in issues:
                    print(f"    - {issue}")
        
        # 功能测试
        if valid_presets:
            print("\n🔍 功能测试:")
            for preset in valid_presets[:3]:  # 只测试前3个有效预设
                print(f"  测试预设: {preset}")
                func_valid, func_issues = self.test_preset_functionality(preset)
                if func_valid:
                    print(f"    ✅ 功能正常")
                else:
                    print(f"    ❌ 功能异常:")
                    for issue in func_issues:
                        print(f"      - {issue}")
        
        # 总结
        print(f"\n📊 验证总结:")
        print(f"  配置文件: {'✅ 正常' if config_valid else '❌ 异常'}")
        print(f"  有效预设: {len(valid_presets)}")
        print(f"  无效预设: {len(invalid_presets)}")
        
        if len(invalid_presets) == 0 and config_valid:
            print("\n🎉 所有配置验证通过！")
        else:
            print("\n⚠️  发现配置问题，请检查并修复。")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="简化分块系统配置验证",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--preset', '-p', help='验证特定预设配置')
    parser.add_argument('--detailed', '-d', action='store_true', help='生成详细验证报告')
    parser.add_argument('--test-functionality', '-t', action='store_true', help='测试预设功能')
    
    args = parser.parse_args()
    
    try:
        validator = ConfigValidator()
        
        if args.preset:
            # 验证特定预设
            print(f"🔍 验证预设: {args.preset}")
            is_valid, issues = validator.validate_preset(args.preset)
            
            if is_valid:
                print(f"✅ 预设 '{args.preset}' 验证通过")
                
                if args.test_functionality:
                    print(f"🧪 测试预设功能...")
                    func_valid, func_issues = validator.test_preset_functionality(args.preset)
                    if func_valid:
                        print(f"✅ 预设 '{args.preset}' 功能正常")
                    else:
                        print(f"❌ 预设 '{args.preset}' 功能异常:")
                        for issue in func_issues:
                            print(f"  - {issue}")
            else:
                print(f"❌ 预设 '{args.preset}' 验证失败:")
                for issue in issues:
                    print(f"  - {issue}")
        else:
            # 生成完整报告
            validator.generate_report(args.detailed)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  验证被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 配置验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
