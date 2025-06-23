#!/usr/bin/env python3
"""
配置管理验证脚本
用于验证统一配置管理系统是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_config_manager():
    """测试配置管理器"""
    print("🔧 测试配置管理器...")
    
    try:
        from core.document_processor.config.config_manager import get_config_manager
        
        # 获取配置管理器
        config_manager = get_config_manager()
        print("✅ 配置管理器初始化成功")
        
        # 测试获取全局配置
        global_config = config_manager.get_chunking_config('global')
        print(f"✅ 全局配置: {global_config}")
        
        # 测试获取递归分块器配置
        recursive_config = config_manager.get_chunking_config('recursive')
        print(f"✅ 递归分块器配置: chunk_size={recursive_config.get('chunk_size')}, chunk_overlap={recursive_config.get('chunk_overlap')}")
        
        # 测试获取分隔符
        separators = config_manager.get_chunking_separators('recursive')
        print(f"✅ 递归分块器分隔符数量: {len(separators)}")
        print(f"   前5个分隔符: {separators[:5]}")
        
        # 测试获取语义分块器配置
        semantic_config = config_manager.get_chunking_config('semantic')
        print(f"✅ 语义分块器配置: target_chunk_size={semantic_config.get('target_chunk_size')}")
        
        # 测试获取结构分块器配置
        structure_config = config_manager.get_chunking_config('structure')
        print(f"✅ 结构分块器配置: min_section_size={structure_config.get('min_section_size')}")
        
        # 测试预设配置
        aviation_preset = config_manager.get_chunking_preset('aviation_standard')
        print(f"✅ 航空标准预设: {aviation_preset}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        return False

def test_chunker_initialization():
    """测试分块器初始化"""
    print("\n🔧 测试分块器初始化...")
    
    try:
        # 测试递归分块器
        from core.document_processor.chunking.recursive_chunker import RecursiveCharacterChunker
        recursive_chunker = RecursiveCharacterChunker()
        print(f"✅ 递归分块器: chunk_size={recursive_chunker.chunk_size}, separators数量={len(recursive_chunker.separators)}")
        
        # 测试语义分块器
        from core.document_processor.chunking.semantic_chunker import SemanticChunker
        semantic_chunker = SemanticChunker()
        print(f"✅ 语义分块器: target_chunk_size={semantic_chunker.target_chunk_size}")
        
        # 测试结构分块器
        from core.document_processor.chunking.structure_chunker import StructureChunker
        structure_chunker = StructureChunker()
        print(f"✅ 结构分块器: min_section_size={structure_chunker.min_section_size}")
        
        # 测试分块引擎
        from core.document_processor.chunking.chunking_engine import ChunkingEngine
        engine = ChunkingEngine()
        print(f"✅ 分块引擎: default_strategy={engine.default_strategy}, 可用策略={engine.get_available_strategies()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分块器初始化测试失败: {e}")
        return False

def test_config_override():
    """测试配置覆盖"""
    print("\n🔧 测试配置覆盖...")
    
    try:
        from core.document_processor.chunking.recursive_chunker import RecursiveCharacterChunker
        
        # 使用默认配置
        default_chunker = RecursiveCharacterChunker()
        print(f"✅ 默认配置: chunk_size={default_chunker.chunk_size}")
        
        # 使用自定义配置
        custom_config = {'chunk_size': 1500, 'chunk_overlap': 300}
        custom_chunker = RecursiveCharacterChunker(custom_config)
        print(f"✅ 自定义配置: chunk_size={custom_chunker.chunk_size}, chunk_overlap={custom_chunker.chunk_overlap}")
        
        # 验证配置覆盖生效
        assert custom_chunker.chunk_size == 1500
        assert custom_chunker.chunk_overlap == 300
        print("✅ 配置覆盖功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置覆盖测试失败: {e}")
        return False

def test_fallback_config():
    """测试回退配置"""
    print("\n🔧 测试回退配置...")
    
    try:
        # 临时重命名配置文件来测试回退
        config_path = project_root / "src/core/document_processor/config/chunking_config.yaml"
        backup_path = config_path.with_suffix('.yaml.backup')
        
        config_exists = config_path.exists()
        if config_exists:
            config_path.rename(backup_path)
        
        try:
            from core.document_processor.chunking.recursive_chunker import RecursiveCharacterChunker
            
            # 重新导入以触发配置重新加载
            import importlib
            import core.document_processor.config.config_manager
            importlib.reload(core.document_processor.config.config_manager)
            
            chunker = RecursiveCharacterChunker()
            print(f"✅ 回退配置: chunk_size={chunker.chunk_size}, separators数量={len(chunker.separators)}")
            
        finally:
            # 恢复配置文件
            if config_exists and backup_path.exists():
                backup_path.rename(config_path)
        
        return True
        
    except Exception as e:
        print(f"❌ 回退配置测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始配置管理验证测试")
    print("=" * 60)
    
    tests = [
        test_config_manager,
        test_chunker_initialization,
        test_config_override,
        test_fallback_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！配置管理系统工作正常")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置管理系统")
        return 1

if __name__ == "__main__":
    sys.exit(main())
