#!/usr/bin/env python3
"""
模块名称: examples
功能描述: 简化分块系统使用示例脚本
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0

使用说明:
    python examples.py                    # 运行所有示例
    python examples.py --example basic   # 运行特定示例
    python examples.py --list            # 列出所有可用示例
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.document_processor.chunking.chunking_engine import ChunkingEngine
    CHUNKING_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"导入ChunkingEngine失败: {e}")
    CHUNKING_ENGINE_AVAILABLE = False


class ChunkingExamples:
    """分块系统使用示例"""
    
    def __init__(self):
        """初始化示例"""
        self.engine = None
        if CHUNKING_ENGINE_AVAILABLE:
            try:
                self.engine = ChunkingEngine()
                print("✅ 分块引擎初始化成功")
            except Exception as e:
                print(f"❌ 分块引擎初始化失败: {e}")
        else:
            print("❌ 分块引擎不可用")
    
    def example_basic_usage(self):
        """示例1: 基本使用方法"""
        print("\n" + "="*60)
        print("📖 示例1: 基本使用方法")
        print("="*60)
        
        if not self.engine:
            print("❌ 分块引擎不可用")
            return
        
        # 示例文本
        text = """
第一章 人工智能概述

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

1.1 发展历史
人工智能的概念最早可以追溯到古希腊的神话传说。现代人工智能研究始于1950年代，艾伦·图灵提出了著名的图灵测试。

1.2 主要技术
目前人工智能的主要技术包括：
- 机器学习
- 深度学习
- 自然语言处理
- 计算机视觉
- 专家系统

第二章 应用领域

人工智能在各个领域都有广泛的应用前景。
"""
        
        metadata = {
            'file_name': 'ai_introduction.txt',
            'document_type': 'educational',
            'title': '人工智能概述'
        }
        
        print("📝 输入文本:")
        print(text[:200] + "...")
        
        print("\n🔧 使用标准预设进行分块:")
        try:
            chunks = self.engine.chunk_document(text, metadata, 'standard')
            
            print(f"✅ 分块完成，共生成 {len(chunks)} 个分块")
            
            for i, chunk in enumerate(chunks[:3], 1):  # 只显示前3个
                content = chunk.content if hasattr(chunk, 'content') else chunk.get('content', '')
                char_count = chunk.character_count if hasattr(chunk, 'character_count') else chunk.get('character_count', 0)
                print(f"\n分块 {i} ({char_count} 字符):")
                print(f"  {content[:100]}...")
            
            if len(chunks) > 3:
                print(f"\n  ... 还有 {len(chunks) - 3} 个分块")
                
        except Exception as e:
            print(f"❌ 分块失败: {e}")
    
    def example_preset_comparison(self):
        """示例2: 预设配置对比"""
        print("\n" + "="*60)
        print("📖 示例2: 预设配置对比")
        print("="*60)
        
        if not self.engine:
            print("❌ 分块引擎不可用")
            return
        
        # 航空文档示例
        text = """
任务1：发动机检查程序

警告：在进行任何发动机检查前，必须确保发动机完全冷却。

步骤1：外观检查
检查发动机外壳是否有裂纹、腐蚀或异常磨损。

步骤2：液位检查
检查发动机机油液位是否在正常范围内。

步骤3：功能测试
启动发动机进行功能测试，监控转速和温度。

任务2：螺旋桨检查程序

警告：螺旋桨检查时必须确保螺旋桨完全静止。
"""
        
        metadata = {
            'file_name': 'maintenance_manual.txt',
            'document_type': 'manual',
            'title': '发动机维修手册'
        }
        
        # 测试不同预设
        presets = ['standard', 'aviation_maintenance', 'structure']
        
        print("📝 输入文本:")
        print(text[:150] + "...")
        
        for preset in presets:
            print(f"\n🔧 使用预设: {preset}")
            try:
                chunks = self.engine.chunk_document(text, metadata, preset)
                print(f"  分块数量: {len(chunks)}")
                
                # 显示第一个分块
                if chunks:
                    first_chunk = chunks[0]
                    content = first_chunk.content if hasattr(first_chunk, 'content') else first_chunk.get('content', '')
                    char_count = first_chunk.character_count if hasattr(first_chunk, 'character_count') else first_chunk.get('character_count', 0)
                    print(f"  第一个分块 ({char_count} 字符): {content[:80]}...")
                    
            except Exception as e:
                print(f"  ❌ 失败: {e}")
    
    def example_automatic_selection(self):
        """示例3: 自动预设选择"""
        print("\n" + "="*60)
        print("📖 示例3: 自动预设选择")
        print("="*60)
        
        if not self.engine:
            print("❌ 分块引擎不可用")
            return
        
        test_cases = [
            {
                'text': '第一条 安全规定\n第二条 操作规范\n第三条 责任条款',
                'metadata': {'title': '安全规章', 'document_type': 'regulation'},
                'description': '规章制度文档'
            },
            {
                'text': '学习目标：掌握基本概念\n知识点1：理论基础\n练习1：实践操作',
                'metadata': {'title': '培训教材', 'document_type': 'training'},
                'description': '培训资料文档'
            },
            {
                'text': '# 技术文档\n\n## 概述\n这是一个技术文档示例。',
                'metadata': {'file_extension': '.md'},
                'description': 'Markdown文档'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n🔍 测试用例 {i}: {case['description']}")
            print(f"  元数据: {case['metadata']}")
            
            try:
                # 不指定预设，让引擎自动选择
                chunks = self.engine.chunk_document(case['text'], case['metadata'])
                
                print(f"  ✅ 自动选择完成，生成 {len(chunks)} 个分块")
                
                # 尝试获取使用的预设信息（如果可能）
                if hasattr(self.engine, '_last_used_preset'):
                    print(f"  📋 使用的预设: {self.engine._last_used_preset}")
                    
            except Exception as e:
                print(f"  ❌ 失败: {e}")
    
    def example_custom_parameters(self):
        """示例4: 自定义参数"""
        print("\n" + "="*60)
        print("📖 示例4: 自定义参数使用")
        print("="*60)
        
        if not self.engine:
            print("❌ 分块引擎不可用")
            return
        
        text = "这是第一句。这是第二句！这是第三句？这是第四句。这是第五句！"
        
        metadata = {
            'file_name': 'custom_test.txt',
            'document_type': 'test',
            'title': '自定义参数测试'
        }
        
        print("📝 输入文本:")
        print(f"  {text}")
        
        # 创建自定义配置的引擎
        custom_config = {
            'chunk_size': 20,  # 小分块便于演示
            'chunk_overlap': 5,
            'separators': ['。', '！', '？', ' ']  # 自定义分隔符
        }
        
        print(f"\n🔧 自定义配置:")
        print(f"  分块大小: {custom_config['chunk_size']}")
        print(f"  重叠大小: {custom_config['chunk_overlap']}")
        print(f"  分隔符: {custom_config['separators']}")
        
        try:
            # 创建带自定义配置的引擎
            custom_engine = ChunkingEngine(custom_config)
            chunks = custom_engine.chunk_document(text, metadata, 'standard')
            
            print(f"\n✅ 分块完成，共生成 {len(chunks)} 个分块:")
            
            for i, chunk in enumerate(chunks, 1):
                content = chunk.content if hasattr(chunk, 'content') else chunk.get('content', '')
                char_count = chunk.character_count if hasattr(chunk, 'character_count') else chunk.get('character_count', 0)
                print(f"  分块 {i} ({char_count} 字符): '{content}'")
                
        except Exception as e:
            print(f"❌ 自定义配置测试失败: {e}")
    
    def example_performance_tips(self):
        """示例5: 性能优化建议"""
        print("\n" + "="*60)
        print("📖 示例5: 性能优化建议")
        print("="*60)
        
        print("🚀 性能优化建议:")
        print("\n1. 选择合适的预设:")
        print("   - 通用文档: 使用 'standard' 预设")
        print("   - 航空文档: 使用对应的航空预设")
        print("   - 快速处理: 使用 'quick' 预设")
        
        print("\n2. 调整分块大小:")
        print("   - 小文档: chunk_size = 500-800")
        print("   - 大文档: chunk_size = 1000-1500")
        print("   - 超大文档: chunk_size = 2000+")
        
        print("\n3. 优化重叠设置:")
        print("   - 一般情况: chunk_overlap = chunk_size * 0.1-0.2")
        print("   - 需要更多上下文: chunk_overlap = chunk_size * 0.3")
        print("   - 性能优先: chunk_overlap = 0")
        
        print("\n4. 批量处理:")
        print("   - 复用同一个引擎实例")
        print("   - 避免频繁创建新引擎")
        print("   - 使用相同预设处理相似文档")
        
        if self.engine:
            print("\n📊 当前可用预设:")
            try:
                presets = self.engine.get_available_presets()
                for preset in presets:
                    info = self.engine.get_preset_info(preset)
                    chunk_size = info.get('chunk_size', '未知')
                    description = info.get('description', '无描述')
                    print(f"   - {preset}: {chunk_size}字符 - {description}")
            except Exception as e:
                print(f"   ❌ 获取预设信息失败: {e}")
    
    def list_examples(self):
        """列出所有可用示例"""
        examples = {
            'basic': '基本使用方法',
            'comparison': '预设配置对比',
            'auto_selection': '自动预设选择',
            'custom': '自定义参数使用',
            'performance': '性能优化建议'
        }
        
        print("\n📋 可用示例:")
        for key, description in examples.items():
            print(f"  {key}: {description}")
    
    def run_example(self, example_name: str):
        """运行指定示例"""
        examples = {
            'basic': self.example_basic_usage,
            'comparison': self.example_preset_comparison,
            'auto_selection': self.example_automatic_selection,
            'custom': self.example_custom_parameters,
            'performance': self.example_performance_tips
        }
        
        if example_name in examples:
            examples[example_name]()
        else:
            print(f"❌ 示例 '{example_name}' 不存在")
            self.list_examples()
    
    def run_all_examples(self):
        """运行所有示例"""
        print("🎯 简化分块系统使用示例")
        print("="*60)
        
        examples = [
            self.example_basic_usage,
            self.example_preset_comparison,
            self.example_automatic_selection,
            self.example_custom_parameters,
            self.example_performance_tips
        ]
        
        for example in examples:
            try:
                example()
            except Exception as e:
                print(f"❌ 示例执行失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="简化分块系统使用示例",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--example', '-e', help='运行特定示例')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用示例')
    
    args = parser.parse_args()
    
    try:
        examples = ChunkingExamples()
        
        if args.list:
            examples.list_examples()
        elif args.example:
            examples.run_example(args.example)
        else:
            examples.run_all_examples()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  示例被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
