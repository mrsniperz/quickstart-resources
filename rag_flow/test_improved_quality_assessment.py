#!/usr/bin/env python3
"""
航空RAG系统分块质量评估改进效果测试

功能描述: 测试改进后的分块质量评估方法在航空文档上的表现
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.document_processor.chunking.chunking_engine import ChunkingEngine, TextChunk, ChunkMetadata, ChunkType


def create_test_chunks():
    """创建测试用的分块数据"""
    
    test_cases = [
        {
            'name': '完整的维修步骤',
            'content': '''第3章 发动机维修程序
3.1 日常检查步骤
警告：检查前必须关闭发动机并等待冷却。
步骤1：检查发动机外观，查看是否有泄漏或损坏。
步骤2：检查机油液位，确保在正常范围内（2.5-3.0升）。
步骤3：检查冷却液温度，正常工作温度应为85-95°C。
检查完成后，记录所有参数并签字确认。''',
            'chunk_type': ChunkType.MAINTENANCE_MANUAL,
            'expected_score_range': (0.8, 1.0)
        },
        
        {
            'name': '不完整的安全警告',
            'content': '''警告：在进行液压系统维修时，必须注意
压力释放程序包括：
1. 关闭主电源
2. 释放系统压力''',
            'chunk_type': ChunkType.MAINTENANCE_MANUAL,
            'expected_score_range': (0.4, 0.7)
        },
        
        {
            'name': '技术参数列表',
            'content': '''液压系统技术规格：
工作压力：3000 PSI
最大压力：3500 PSI
工作温度：-40°C 到 +85°C
液压油类型：MIL-H-5606
油箱容量：15升
过滤器规格：25微米''',
            'chunk_type': ChunkType.TECHNICAL_STANDARD,
            'expected_score_range': (0.7, 0.9)
        },
        
        {
            'name': '航空法规条款',
            'content': '''第147条 航空器维修人员资质要求
147.1 基本要求
持证维修人员必须具备以下条件：
(a) 年满18周岁；
(b) 具有相应的技术培训经历；
(c) 通过理论和实践考试；
(d) 身体健康，能够胜任维修工作。''',
            'chunk_type': ChunkType.REGULATION,
            'expected_score_range': (0.8, 1.0)
        },
        
        {
            'name': '截断的航空术语',
            'content': '''液压系统检查程序
检查液压泵的工作状态，确保压力稳定。如果发现液压
油泄漏，应立即停止操作并进行维修。检查完成后更新维修记录。''',
            'chunk_type': ChunkType.MAINTENANCE_MANUAL,
            'expected_score_range': (0.3, 0.6)
        },
        
        {
            'name': '空白内容过多',
            'content': '''


检查     项目：     发动机


状态：     正常



''',
            'chunk_type': ChunkType.MAINTENANCE_MANUAL,
            'expected_score_range': (0.1, 0.4)
        },
        
        {
            'name': '培训材料示例',
            'content': '''航空维修基础知识
第一节：工具使用
在航空维修中，正确使用工具是确保安全的基础。
常用工具包括：
• 扭力扳手：用于精确控制螺栓扭矩
• 压力表：监测系统压力
• 万用表：检测电气系统
使用工具前，必须检查工具状态并校准。''',
            'chunk_type': ChunkType.TRAINING_MATERIAL,
            'expected_score_range': (0.7, 0.9)
        }
    ]
    
    chunks = []
    for i, case in enumerate(test_cases):
        metadata = ChunkMetadata(
            chunk_id=f"test_chunk_{i}",
            chunk_type=case['chunk_type'],
            source_document=f"test_doc_{case['name']}"
        )
        
        chunk = TextChunk(
            content=case['content'],
            metadata=metadata,
            word_count=len(case['content'].split()),
            character_count=len(case['content'])
        )
        
        chunks.append({
            'chunk': chunk,
            'name': case['name'],
            'expected_range': case['expected_score_range']
        })
    
    return chunks


def test_quality_assessment():
    """测试质量评估方法"""
    
    print("🚀 航空RAG系统分块质量评估改进效果测试")
    print("=" * 60)
    
    # 创建分块引擎
    config = {
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'min_chunk_size': 100,
        'max_chunk_size': 2000
    }
    
    engine = ChunkingEngine(config)
    
    # 获取测试数据
    test_chunks = create_test_chunks()
    
    print(f"\n📊 测试用例总数: {len(test_chunks)}")
    print("-" * 60)
    
    results = []
    
    for test_case in test_chunks:
        chunk = test_case['chunk']
        name = test_case['name']
        expected_range = test_case['expected_range']
        
        # 计算质量评分
        quality_score = engine._calculate_chunk_quality(chunk)
        
        # 检查是否在预期范围内
        in_range = expected_range[0] <= quality_score <= expected_range[1]
        status = "✅ 通过" if in_range else "❌ 未通过"
        
        print(f"\n📝 测试用例: {name}")
        print(f"   内容长度: {chunk.character_count} 字符")
        print(f"   文档类型: {chunk.metadata.chunk_type}")
        print(f"   质量评分: {quality_score:.3f}")
        print(f"   预期范围: {expected_range[0]:.1f} - {expected_range[1]:.1f}")
        print(f"   测试结果: {status}")
        
        # 显示内容预览
        preview = chunk.content[:100].replace('\n', ' ')
        if len(chunk.content) > 100:
            preview += "..."
        print(f"   内容预览: {preview}")
        
        results.append({
            'name': name,
            'score': quality_score,
            'expected': expected_range,
            'passed': in_range
        })
    
    # 统计结果
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    pass_rate = passed_count / total_count * 100
    
    print("\n" + "=" * 60)
    print("📈 测试结果统计")
    print("-" * 60)
    print(f"通过测试: {passed_count}/{total_count} ({pass_rate:.1f}%)")
    
    if pass_rate >= 80:
        print("🎉 质量评估改进效果良好！")
    elif pass_rate >= 60:
        print("⚠️  质量评估有所改进，但仍需优化")
    else:
        print("❌ 质量评估需要进一步改进")
    
    # 详细分析
    print("\n📋 详细分析:")
    avg_score = sum(r['score'] for r in results) / len(results)
    print(f"   平均质量评分: {avg_score:.3f}")
    
    high_quality = [r for r in results if r['score'] >= 0.8]
    medium_quality = [r for r in results if 0.5 <= r['score'] < 0.8]
    low_quality = [r for r in results if r['score'] < 0.5]
    
    print(f"   高质量分块 (≥0.8): {len(high_quality)} 个")
    print(f"   中等质量分块 (0.5-0.8): {len(medium_quality)} 个")
    print(f"   低质量分块 (<0.5): {len(low_quality)} 个")
    
    return results


def test_weight_configuration():
    """测试权重配置功能"""
    
    print("\n🔧 权重配置测试")
    print("-" * 40)
    
    engine = ChunkingEngine()
    
    # 测试不同文档类型的权重配置
    test_metadata = [
        ChunkMetadata("test1", ChunkType.MAINTENANCE_MANUAL, "doc1"),
        ChunkMetadata("test2", ChunkType.REGULATION, "doc2"),
        ChunkMetadata("test3", ChunkType.TECHNICAL_STANDARD, "doc3"),
        ChunkMetadata("test4", ChunkType.TRAINING_MATERIAL, "doc4")
    ]
    
    for metadata in test_metadata:
        weights = engine._get_quality_weights(metadata)
        print(f"\n📋 {metadata.chunk_type}:")
        for dimension, weight in weights.items():
            print(f"   {dimension}: {weight:.2f}")


if __name__ == "__main__":
    try:
        # 运行质量评估测试
        results = test_quality_assessment()
        
        # 运行权重配置测试
        test_weight_configuration()
        
        print("\n✨ 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
