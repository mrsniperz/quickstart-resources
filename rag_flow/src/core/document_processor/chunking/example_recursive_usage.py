#!/usr/bin/env python3
"""
模块名称: example_recursive_usage
功能描述: 递归分块器使用示例，展示如何使用RecursiveCharacterChunker进行文本分块
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from chunking_engine import ChunkingEngine
from recursive_chunker import RecursiveCharacterChunker


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 示例文本
    text_content = """
第一章 航空安全管理

1.1 安全管理体系
航空安全管理体系是确保航空运输安全的重要保障。它包括安全政策、安全目标、安全程序和安全文化等多个方面。

1.2 风险评估
定期进行风险评估是安全管理的核心环节。风险评估应该包括：
- 识别潜在危险源
- 评估风险等级
- 制定控制措施
- 监控实施效果

第二章 维修管理

2.1 预防性维修
预防性维修是指在设备发生故障之前，按照预定的计划和标准进行的维修活动。

2.2 故障维修
当设备发生故障时，应立即进行故障维修。故障维修的步骤包括：
1. 故障诊断
2. 制定维修方案
3. 实施维修作业
4. 验证维修效果
"""
    
    # 基本配置
    config = {
        'chunk_size': 300,
        'chunk_overlap': 50,
        'add_start_index': True
    }
    
    # 创建递归分块器
    chunker = RecursiveCharacterChunker(config)
    
    # 文档元数据
    metadata = {
        'file_path': 'example_document.txt',
        'document_type': 'maintenance_manual'
    }
    
    # 执行分块
    chunks = chunker.chunk_text(text_content, metadata)
    
    # 显示结果
    print(f"总共生成 {len(chunks)} 个分块:")
    for i, chunk in enumerate(chunks):
        print(f"\n分块 {i+1}:")
        print(f"  大小: {chunk.character_count} 字符")
        print(f"  起始位置: {chunk.metadata.start_position}")
        print(f"  内容: {chunk.content[:100]}...")
        if chunk.overlap_content:
            print(f"  重叠内容: {chunk.overlap_content[:30]}...")


def example_custom_separators():
    """自定义分隔符示例"""
    print("\n=== 自定义分隔符示例 ===")
    
    text_content = """
任务1：发动机检查

步骤1：外观检查
检查发动机外观是否有损伤、裂纹或异常磨损。

步骤2：油液检查
检查机油液位和质量。注意：机油应清澈无杂质。

步骤3：连接检查
检查各种连接是否牢固。警告：检查前必须断开电源。

任务2：起落架检查

步骤1：轮胎检查
检查轮胎磨损情况和气压。

步骤2：刹车系统检查
检查刹车片厚度和刹车液液位。
"""
    
    # 航空维修专用配置
    config = {
        'chunk_size': 200,
        'chunk_overlap': 30,
        'separators': [
            "\n任务",         # 任务分隔
            "\n步骤",         # 步骤分隔
            "\n警告",         # 警告信息
            "\n注意",         # 注意事项
            "\n\n",           # 段落分隔
            "。",             # 句子结束
            ".",              # 英文句号
            " ",              # 词语分隔
            ""                # 字符级回退
        ],
        'keep_separator': True,
        'add_start_index': True
    }
    
    chunker = RecursiveCharacterChunker(config)
    
    metadata = {
        'file_path': 'maintenance_procedure.txt',
        'document_type': 'maintenance_manual'
    }
    
    chunks = chunker.chunk_text(text_content, metadata)
    
    print(f"总共生成 {len(chunks)} 个分块:")
    for i, chunk in enumerate(chunks):
        print(f"\n分块 {i+1}:")
        print(f"  大小: {chunk.character_count} 字符")
        print(f"  内容: {chunk.content}")


def example_regex_separators():
    """正则表达式分隔符示例"""
    print("\n=== 正则表达式分隔符示例 ===")
    
    text_content = """
第1章 概述

本章介绍航空维修的基本概念。航空维修是确保飞机安全运行的重要环节。

第2章 维修分类

2.1 定期维修
定期维修按照预定的时间间隔进行。

2.2 非定期维修
非定期维修根据实际需要进行。

第3章 维修程序

维修程序包括以下步骤：
1) 准备工作
2) 实施维修
3) 质量检查
4) 记录归档
"""
    
    # 使用正则表达式分隔符
    config = {
        'chunk_size': 150,
        'chunk_overlap': 20,
        'separators': [
            r'\n第\d+章',      # 章节开始
            r'\n\d+\.\d+',     # 小节开始
            r'\n\d+\)',        # 编号列表
            r'[.。]\s+',       # 句子结束
            r'[,，]\s+',       # 逗号分隔
            r'\s+',            # 空白字符
            r''                # 字符级回退
        ],
        'is_separator_regex': True,
        'keep_separator': True,
        'add_start_index': True
    }
    
    chunker = RecursiveCharacterChunker(config)
    
    metadata = {
        'file_path': 'maintenance_guide.txt',
        'document_type': 'technical_manual'
    }
    
    chunks = chunker.chunk_text(text_content, metadata)
    
    print(f"总共生成 {len(chunks)} 个分块:")
    for i, chunk in enumerate(chunks):
        print(f"\n分块 {i+1}:")
        print(f"  大小: {chunk.character_count} 字符")
        print(f"  内容: {repr(chunk.content)}")


def example_chunking_engine_integration():
    """与分块引擎集成示例"""
    print("\n=== 分块引擎集成示例 ===")
    
    # 创建分块引擎
    engine_config = {
        'default_strategy': 'recursive',
        'chunk_size': 250,
        'chunk_overlap': 40
    }
    
    engine = ChunkingEngine(engine_config)
    
    text_content = """
航空器维修手册

第一部分：安全须知

在进行任何维修作业前，必须确保：
1. 断开电源
2. 释放压力
3. 佩戴防护设备

第二部分：工具准备

所需工具清单：
- 扳手套装
- 螺丝刀套装
- 测量工具
- 安全设备

第三部分：维修程序

按照以下步骤进行维修：
1. 检查工作环境
2. 准备必要工具
3. 执行维修作业
4. 进行质量检查
5. 清理工作现场
"""
    
    metadata = {
        'file_path': 'aircraft_maintenance_manual.txt',
        'document_type': 'maintenance_manual',
        'title': '航空器维修手册'
    }
    
    # 使用分块引擎进行分块
    chunks = engine.chunk_document(text_content, metadata, 'recursive')
    
    print(f"总共生成 {len(chunks)} 个分块:")
    for i, chunk in enumerate(chunks):
        print(f"\n分块 {i+1}:")
        print(f"  ID: {chunk.metadata.chunk_id}")
        print(f"  大小: {chunk.character_count} 字符")
        print(f"  质量评分: {chunk.quality_score}")
        print(f"  内容: {chunk.content[:80]}...")


def main():
    """主函数"""
    print("递归分块器使用示例")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_custom_separators()
        example_regex_separators()
        example_chunking_engine_integration()
        
        print("\n" + "=" * 50)
        print("所有示例执行完成！")
        
    except Exception as e:
        print(f"示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
