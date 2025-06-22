"""
模块名称: test_quality_refactor
功能描述: 质量评估重构验证脚本
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from typing import List
from ..chunking_engine import TextChunk, ChunkMetadata, ChunkType
from .manager import QualityAssessmentManager
from .utils import QualityConfigBuilder, QualityAnalyzer, create_aviation_config


def create_test_chunks() -> List[TextChunk]:
    """创建测试分块"""
    test_chunks = []
    
    # 测试分块1：航空维修手册内容
    chunk1 = TextChunk(
        content="""
        发动机液压系统检查程序：
        步骤1：关闭发动机并等待冷却至室温。
        步骤2：检查液压油液位，确保在正常范围内。
        步骤3：检查液压管路是否有泄漏现象。
        警告：在进行液压系统检查时，必须佩戴防护设备，避免液压油接触皮肤。
        注意：检查完成后，记录检查结果并签名确认。
        """,
        metadata=ChunkMetadata(
            chunk_id="test_001",
            chunk_type=ChunkType.PARAGRAPH,
            source_document="maintenance_manual.pdf"
        )
    )
    chunk1.character_count = len(chunk1.content)
    chunk1.word_count = len(chunk1.content.split())
    test_chunks.append(chunk1)
    
    # 测试分块2：技术规格内容
    chunk2 = TextChunk(
        content="""
        发动机技术参数：
        - 最大功率：2000 HP
        - 工作转速：1500-3000 RPM
        - 燃油消耗：45 L/h
        - 工作温度：-40°C 至 +85°C
        - 液压压力：3000 PSI
        """,
        metadata=ChunkMetadata(
            chunk_id="test_002",
            chunk_type=ChunkType.PARAGRAPH,
            source_document="technical_spec.pdf"
        )
    )
    chunk2.character_count = len(chunk2.content)
    chunk2.word_count = len(chunk2.content.split())
    test_chunks.append(chunk2)
    
    # 测试分块3：不完整内容
    chunk3 = TextChunk(
        content="这是一个不完整的",
        metadata=ChunkMetadata(
            chunk_id="test_003",
            chunk_type=ChunkType.PARAGRAPH,
            source_document="incomplete.pdf"
        )
    )
    chunk3.character_count = len(chunk3.content)
    chunk3.word_count = len(chunk3.content.split())
    test_chunks.append(chunk3)
    
    # 测试分块4：长文本内容
    chunk4 = TextChunk(
        content="""
        航空安全管理体系是确保航空运输安全的重要保障。该体系包括安全政策、安全风险管理、安全保证和安全促进四个核心组件。
        安全政策是整个安全管理体系的基础，明确了组织的安全承诺和安全目标。安全风险管理通过识别、评估和控制安全风险，
        确保风险处于可接受水平。安全保证通过监控和测量安全绩效，验证安全管理体系的有效性。安全促进通过培训、
        沟通和持续改进，提升整个组织的安全文化和安全意识。这四个组件相互关联、相互支撑，共同构成了完整的安全管理体系。
        在实施过程中，需要建立相应的组织架构、制定详细的程序文件、配备必要的资源，并定期进行评审和改进。
        """,
        metadata=ChunkMetadata(
            chunk_id="test_004",
            chunk_type=ChunkType.PARAGRAPH,
            source_document="safety_manual.pdf"
        )
    )
    chunk4.character_count = len(chunk4.content)
    chunk4.word_count = len(chunk4.content.split())
    test_chunks.append(chunk4)
    
    return test_chunks


def test_quality_strategies():
    """测试不同的质量评估策略"""
    print("=" * 60)
    print("质量评估策略测试")
    print("=" * 60)
    
    # 创建测试分块
    test_chunks = create_test_chunks()
    
    # 创建质量评估管理器
    config = create_aviation_config()
    manager = QualityAssessmentManager(config)
    
    # 测试所有可用策略
    strategies = manager.get_available_strategies()
    print(f"可用策略: {strategies}")
    print()
    
    for strategy_name in strategies:
        print(f"测试策略: {strategy_name}")
        print("-" * 40)
        
        for i, chunk in enumerate(test_chunks):
            try:
                result = manager.assess_chunk_quality(chunk, strategy_name)
                print(f"分块 {i+1} ({chunk.metadata.chunk_id}):")
                print(f"  总体评分: {result.overall_score:.3f}")
                print(f"  置信度: {result.confidence:.3f}")
                print(f"  处理时间: {result.processing_time:.2f}ms")
                print(f"  维度评分: {result.dimension_scores}")
                if result.details.get('completeness_issues'):
                    print(f"  问题: {result.details['completeness_issues']}")
                print()
            except Exception as e:
                print(f"  错误: {e}")
                print()
        
        print()


def test_batch_assessment():
    """测试批量评估功能"""
    print("=" * 60)
    print("批量质量评估测试")
    print("=" * 60)
    
    # 创建测试分块
    test_chunks = create_test_chunks()
    
    # 创建质量评估管理器
    config = create_aviation_config()
    manager = QualityAssessmentManager(config)
    
    # 批量评估
    results = manager.assess_chunks_batch(test_chunks, 'aviation')
    
    print(f"批量评估完成，共 {len(results)} 个结果")
    print()
    
    # 分析结果
    analysis = QualityAnalyzer.analyze_quality_distribution(results)
    print("质量分布分析:")
    print(f"  平均评分: {analysis['mean_score']:.3f}")
    print(f"  最高评分: {analysis['max_score']:.3f}")
    print(f"  最低评分: {analysis['min_score']:.3f}")
    print(f"  标准差: {analysis['std_deviation']:.3f}")
    print()
    
    # 质量分布
    dist = analysis['score_distribution']
    print("评分分布:")
    print(f"  优秀 (≥0.8): {dist['excellent']}")
    print(f"  良好 (0.6-0.8): {dist['good']}")
    print(f"  一般 (0.4-0.6): {dist['fair']}")
    print(f"  较差 (<0.4): {dist['poor']}")
    print()
    
    # 识别问题
    issues = QualityAnalyzer.identify_quality_issues(results, 0.6)
    if issues:
        print(f"发现 {len(issues)} 个质量问题:")
        for issue in issues:
            print(f"  分块 {issue['chunk_index']+1}: {issue['overall_score']:.3f}")
            for problem in issue['issues']:
                print(f"    - {problem}")
        print()


def test_configuration_builder():
    """测试配置构建器"""
    print("=" * 60)
    print("配置构建器测试")
    print("=" * 60)
    
    # 使用配置构建器创建自定义配置
    config = (QualityConfigBuilder()
              .set_default_strategy('semantic')
              .enable_caching(True, 500)
              .configure_aviation_strategy(
                  aviation_weight=0.35,
                  semantic_weight=0.30,
                  density_weight=0.20,
                  structure_weight=0.15
              )
              .configure_semantic_strategy(
                  boundary_weight=0.35,
                  topic_weight=0.30,
                  coherence_weight=0.25,
                  completeness_weight=0.10
              )
              .build())
    
    print("自定义配置:")
    print(f"  默认策略: {config['default_strategy']}")
    print(f"  缓存启用: {config['enable_caching']}")
    print(f"  缓存大小: {config['cache_size']}")
    print(f"  策略配置: {list(config['strategies'].keys())}")
    print()
    
    # 使用自定义配置创建管理器
    manager = QualityAssessmentManager(config)
    
    # 测试策略信息
    strategies_info = manager.get_all_strategies_info()
    for name, info in strategies_info.items():
        print(f"策略 {name}:")
        print(f"  类名: {info['class_name']}")
        print(f"  描述: {info['description']}")
        print(f"  支持维度: {info['supported_dimensions']}")
        print()


def test_quality_report():
    """测试质量报告生成"""
    print("=" * 60)
    print("质量报告生成测试")
    print("=" * 60)
    
    # 创建测试分块
    test_chunks = create_test_chunks()
    
    # 创建质量评估管理器
    config = create_aviation_config()
    manager = QualityAssessmentManager(config)
    
    # 批量评估
    results = manager.assess_chunks_batch(test_chunks, 'aviation')
    
    # 生成报告
    report = QualityAnalyzer.generate_quality_report(results)
    print(report)


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("开始质量评估重构验证测试...")
        print()
        
        # 运行各项测试
        test_quality_strategies()
        test_batch_assessment()
        test_configuration_builder()
        test_quality_report()
        
        print("=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
