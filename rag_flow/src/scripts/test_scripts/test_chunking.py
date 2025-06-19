#!/usr/bin/env python3
"""
模块名称: test_chunking
功能描述: RAG Flow文档分块功能专用测试脚本，重点测试recursive_chunker的分块效果
创建日期: 2025-06-19
作者: Sniperz
版本: v1.0.0

使用说明:
    python test_chunking.py --demo                    # 运行演示模式
    python test_chunking.py -i document.txt          # 测试文件
    python test_chunking.py -t "测试文本"             # 测试直接输入的文本
    python test_chunking.py --performance             # 性能测试模式
    python test_chunking.py -s recursive --chunk-size 500  # 自定义参数

支持的分块策略:
    - recursive: 递归字符分块器（默认，重点测试）
    - semantic: 语义分块器
    - structure: 结构分块器
    - aviation_maintenance: 航空维修文档分块器
    - aviation_regulation: 航空规章分块器
    - aviation_standard: 航空标准分块器
    - aviation_training: 航空培训分块器
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    # 直接导入需要的模块，避免复杂依赖
    from core.document_processor.chunking.recursive_chunker import RecursiveCharacterChunker
    from core.document_processor.chunking.chunking_engine import ChunkType, ChunkMetadata, TextChunk

    # 尝试导入日志管理器，如果失败则使用标准logging
    try:
        from utils.logger import SZ_LoggerManager
        USE_CUSTOM_LOGGER = True
    except ImportError:
        USE_CUSTOM_LOGGER = False

except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在RAG Flow项目的src目录下运行此脚本")
    print(f"当前路径: {os.getcwd()}")
    print(f"项目根路径: {project_root}")
    print("\n可能的解决方案:")
    print("1. 确保在 rag_flow/src 目录下运行脚本")
    print("2. 检查chunking模块是否完整")
    print("3. 安装缺失的依赖包")
    sys.exit(1)


class ChunkingTester:
    """
    文档分块测试器

    专门测试RecursiveCharacterChunker的分块效果，包括：
    - 递归分块策略测试
    - 分块效果可视化
    - 性能统计分析
    - 参数调优建议
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化测试器

        Args:
            config: 分块器配置参数
        """
        self.config = config or {}

        # 设置日志记录器
        if USE_CUSTOM_LOGGER:
            self.logger = SZ_LoggerManager.setup_logger(
                logger_name="chunking_tester",
                log_file="chunking_test.log",
                level=logging.INFO
            )
        else:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("chunking_tester")

        try:
            # 直接创建RecursiveCharacterChunker实例
            self.chunker = RecursiveCharacterChunker(self.config)
            self.logger.info("递归分块器初始化成功")
        except Exception as e:
            self.logger.error(f"递归分块器初始化失败: {e}")
            raise
    
    def test_chunking(self, text: str, metadata: Dict[str, Any],
                     strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """
        执行分块测试

        Args:
            text: 待分块的文本
            metadata: 文档元数据
            strategy_name: 指定的分块策略名称（此版本只支持recursive）

        Returns:
            dict: 测试结果，包含分块结果和统计信息
        """
        try:
            start_time = time.time()

            # 使用RecursiveCharacterChunker执行分块
            chunks = self.chunker.chunk_text(text, metadata)

            processing_time = time.time() - start_time

            # 计算统计信息
            stats = self._calculate_statistics(chunks, processing_time, len(text))

            return {
                'chunks': chunks,
                'statistics': stats,
                'processing_time': processing_time,
                'strategy_used': 'recursive'
            }

        except Exception as e:
            self.logger.error(f"分块测试失败: {e}")
            raise
    
    def _calculate_statistics(self, chunks: List, processing_time: float, 
                            original_length: int) -> Dict[str, Any]:
        """
        计算分块统计信息
        
        Args:
            chunks: 分块结果列表
            processing_time: 处理时间
            original_length: 原文长度
            
        Returns:
            dict: 统计信息
        """
        if not chunks:
            return {
                'chunk_count': 0,
                'total_characters': 0,
                'average_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'processing_speed': 0,
                'coverage_rate': 0
            }
        
        chunk_sizes = [chunk.character_count for chunk in chunks]
        total_chars = sum(chunk_sizes)
        
        return {
            'chunk_count': len(chunks),
            'total_characters': total_chars,
            'average_chunk_size': total_chars / len(chunks),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'processing_speed': original_length / processing_time if processing_time > 0 else 0,
            'coverage_rate': (total_chars / original_length) * 100 if original_length > 0 else 0,
            'quality_scores': [chunk.quality_score for chunk in chunks if hasattr(chunk, 'quality_score')]
        }
    
    def visualize_chunks(self, result: Dict[str, Any], output_format: str = 'detailed') -> None:
        """
        可视化分块结果
        
        Args:
            result: 测试结果
            output_format: 输出格式 ('detailed', 'simple', 'json')
        """
        chunks = result['chunks']
        stats = result['statistics']
        
        if output_format == 'json':
            self._output_json(result)
            return
        
        # 输出标题
        print("\n" + "="*80)
        print(f"🔍 RAG Flow 文档分块测试结果")
        print(f"📊 策略: {result['strategy_used']}")
        print(f"⏱️  处理时间: {result['processing_time']:.3f}秒")
        print("="*80)
        
        # 输出统计信息
        self._print_statistics(stats)
        
        if output_format == 'detailed':
            self._print_detailed_chunks(chunks)
        else:
            self._print_simple_chunks(chunks)
    
    def _print_statistics(self, stats: Dict[str, Any]) -> None:
        """打印统计信息"""
        print(f"\n📈 统计信息:")
        print(f"   分块数量: {stats['chunk_count']}")
        print(f"   总字符数: {stats['total_characters']}")
        print(f"   平均分块大小: {stats['average_chunk_size']:.1f} 字符")
        print(f"   最小分块: {stats['min_chunk_size']} 字符")
        print(f"   最大分块: {stats['max_chunk_size']} 字符")
        print(f"   处理速度: {stats['processing_speed']:.0f} 字符/秒")
        print(f"   覆盖率: {stats['coverage_rate']:.1f}%")
        
        if stats['quality_scores']:
            avg_quality = sum(stats['quality_scores']) / len(stats['quality_scores'])
            print(f"   平均质量评分: {avg_quality:.3f}")
    
    def _print_detailed_chunks(self, chunks: List) -> None:
        """打印详细分块信息"""
        print(f"\n📝 详细分块结果:")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- 分块 {i} ---")
            print(f"大小: {chunk.character_count} 字符 | 词数: {chunk.word_count}")
            
            if hasattr(chunk, 'quality_score'):
                print(f"质量评分: {chunk.quality_score:.3f}")
            
            if hasattr(chunk.metadata, 'start_position') and chunk.metadata.start_position is not None:
                print(f"位置: {chunk.metadata.start_position}-{chunk.metadata.end_position}")
            
            # 显示内容预览
            content_preview = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
            print(f"内容: {content_preview}")
            
            # 显示重叠内容
            if chunk.overlap_content:
                overlap_preview = chunk.overlap_content[:100] + "..." if len(chunk.overlap_content) > 100 else chunk.overlap_content
                print(f"重叠: {overlap_preview}")
    
    def _print_simple_chunks(self, chunks: List) -> None:
        """打印简洁分块信息"""
        print(f"\n📋 分块概览:")
        
        for i, chunk in enumerate(chunks, 1):
            content_preview = chunk.content[:50] + "..." if len(chunk.content) > 50 else chunk.content
            quality_info = f" (质量: {chunk.quality_score:.2f})" if hasattr(chunk, 'quality_score') else ""
            print(f"  {i:2d}. [{chunk.character_count:4d}字符] {content_preview}{quality_info}")
    
    def _output_json(self, result: Dict[str, Any]) -> None:
        """输出JSON格式结果"""
        # 转换chunks为可序列化的格式
        serializable_chunks = []
        for chunk in result['chunks']:
            chunk_data = {
                'content': chunk.content,
                'character_count': chunk.character_count,
                'word_count': chunk.word_count,
                'quality_score': getattr(chunk, 'quality_score', 0.0),
                'overlap_content': chunk.overlap_content,
                'metadata': {
                    'chunk_id': chunk.metadata.chunk_id,
                    'chunk_type': chunk.metadata.chunk_type.value if hasattr(chunk.metadata.chunk_type, 'value') else str(chunk.metadata.chunk_type),
                    'start_position': chunk.metadata.start_position,
                    'end_position': chunk.metadata.end_position
                }
            }
            serializable_chunks.append(chunk_data)
        
        output = {
            'strategy_used': result['strategy_used'],
            'processing_time': result['processing_time'],
            'statistics': result['statistics'],
            'chunks': serializable_chunks
        }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
    
    def run_performance_test(self, text_sizes: List[int] = None) -> None:
        """
        运行性能测试
        
        Args:
            text_sizes: 测试文本大小列表（字符数）
        """
        if text_sizes is None:
            text_sizes = [1000, 5000, 10000, 50000, 100000]
        
        print("\n" + "="*80)
        print("🚀 性能测试模式")
        print("="*80)
        
        # 生成测试文本
        base_text = self._get_sample_text('performance')
        
        results = []
        
        for size in text_sizes:
            # 生成指定大小的文本
            test_text = (base_text * (size // len(base_text) + 1))[:size]
            
            metadata = {
                'file_name': f'performance_test_{size}.txt',
                'document_type': 'performance_test',
                'title': f'性能测试文档 ({size}字符)'
            }
            
            print(f"\n测试文本大小: {size:,} 字符")
            
            try:
                result = self.test_chunking(test_text, metadata)
                results.append({
                    'size': size,
                    'time': result['processing_time'],
                    'chunks': result['statistics']['chunk_count'],
                    'speed': result['statistics']['processing_speed']
                })

                print(f"  处理时间: {result['processing_time']:.3f}秒")
                print(f"  分块数量: {result['statistics']['chunk_count']}")
                print(f"  处理速度: {result['statistics']['processing_speed']:.0f} 字符/秒")

            except Exception as e:
                print(f"  测试失败: {e}")
        
        # 输出性能总结
        if results:
            print(f"\n📊 性能测试总结:")
            print(f"{'文本大小':>10} {'处理时间':>10} {'分块数':>8} {'速度':>12}")
            print("-" * 45)
            for r in results:
                print(f"{r['size']:>10,} {r['time']:>9.3f}s {r['chunks']:>7} {r['speed']:>10.0f}/s")
    
    def run_demo(self) -> None:
        """运行演示模式"""
        print("\n" + "="*80)
        print("🎯 RAG Flow 递归分块器功能演示")
        print("="*80)

        demo_scenarios = [
            ('通用技术文档', 'general'),
            ('航空维修手册', 'aviation'),
            ('代码文档', 'code'),
            ('结构化文档', 'structured')
        ]

        for name, text_type in demo_scenarios:
            print(f"\n🔸 演示场景: {name}")
            print("-" * 40)

            text = self._get_sample_text(text_type)
            metadata = {
                'file_name': f'{text_type}_demo.txt',
                'document_type': text_type,
                'title': name
            }

            try:
                result = self.test_chunking(text, metadata)
                self.visualize_chunks(result, 'simple')
            except Exception as e:
                print(f"演示失败: {e}")
    
    def _get_sample_text(self, text_type: str) -> str:
        """获取示例文本"""
        samples = {
            'general': """
第一章 系统架构设计

1.1 概述
本系统采用微服务架构设计，具有高可用性、可扩展性和可维护性的特点。系统主要由以下几个核心模块组成：用户管理模块、数据处理模块、接口服务模块和监控模块。

1.2 技术选型
在技术选型方面，我们选择了以下技术栈：
- 后端框架：Spring Boot 2.7
- 数据库：MySQL 8.0 + Redis 6.2
- 消息队列：RabbitMQ 3.9
- 容器化：Docker + Kubernetes
- 监控：Prometheus + Grafana

1.3 系统特性
系统具备以下核心特性：
1. 高并发处理能力，支持每秒10万次请求
2. 数据一致性保证，采用分布式事务管理
3. 自动故障恢复，具备完善的容错机制
4. 实时监控告警，确保系统稳定运行
""",
            
            'aviation': """
任务1：发动机日常检查程序

警告：在进行任何发动机检查前，必须确保发动机完全冷却，并断开所有电源。

步骤1：外观检查
检查发动机外壳是否有裂纹、腐蚀或异常磨损。特别注意以下部位：
- 进气道和排气口
- 燃油管路连接处
- 电气线束固定点
- 冷却系统管路

步骤2：液位检查
检查各种液体的液位是否在正常范围内：
- 发动机机油液位
- 冷却液液位
- 液压油液位

注意：所有液位检查必须在发动机水平状态下进行。

步骤3：功能测试
启动发动机进行功能测试，监控以下参数：
- 发动机转速
- 油压指示
- 温度指示
- 振动水平

任务2：螺旋桨检查程序

警告：螺旋桨检查时必须确保螺旋桨完全静止，并设置安全警示标志。
""",
            
            'code': """
# 用户认证模块

## 概述
本模块提供完整的用户认证功能，包括登录、注册、密码重置等核心功能。

## 主要类和方法

### UserAuthenticator类
```python
class UserAuthenticator:
    def __init__(self, config):
        self.config = config
        self.session_manager = SessionManager()
    
    def authenticate(self, username, password):
        \"\"\"
        用户认证方法
        
        Args:
            username (str): 用户名
            password (str): 密码
            
        Returns:
            bool: 认证结果
        \"\"\"
        user = self.get_user(username)
        if user and self.verify_password(password, user.password_hash):
            return self.create_session(user)
        return False
    
    def register_user(self, user_data):
        \"\"\"注册新用户\"\"\"
        # 验证用户数据
        if not self.validate_user_data(user_data):
            raise ValidationError("用户数据验证失败")
        
        # 创建用户账户
        user = User.create(user_data)
        return user.id
```

### 配置说明
系统支持以下配置参数：
- SESSION_TIMEOUT: 会话超时时间（默认30分钟）
- PASSWORD_MIN_LENGTH: 密码最小长度（默认8位）
- MAX_LOGIN_ATTEMPTS: 最大登录尝试次数（默认5次）
""",
            
            'structured': """
# 项目管理规范文档

## 1. 项目生命周期管理

### 1.1 项目启动阶段
#### 1.1.1 需求分析
- 业务需求收集
- 技术需求分析
- 可行性研究

#### 1.1.2 项目规划
- 项目范围定义
- 时间计划制定
- 资源分配计划

### 1.2 项目执行阶段
#### 1.2.1 开发管理
- 代码开发规范
- 版本控制管理
- 代码审查流程

#### 1.2.2 质量控制
- 单元测试要求
- 集成测试流程
- 性能测试标准

## 2. 团队协作规范

### 2.1 沟通机制
- 日常站会制度
- 周报汇报机制
- 月度总结会议

### 2.2 文档管理
- 技术文档编写规范
- 文档版本控制
- 知识库维护

## 3. 风险管理

### 3.1 风险识别
- 技术风险评估
- 进度风险监控
- 质量风险预警

### 3.2 应急预案
- 故障处理流程
- 数据备份策略
- 业务连续性计划
""",
            
            'performance': """
系统性能优化是一个持续的过程，需要从多个维度进行考虑和实施。首先，我们需要建立完善的性能监控体系，实时收集系统运行数据，包括CPU使用率、内存占用、磁盘I/O、网络带宽等关键指标。通过这些数据，我们可以及时发现性能瓶颈，并采取相应的优化措施。在数据库层面，我们需要优化查询语句，建立合适的索引，合理设计表结构，并考虑读写分离、分库分表等策略。在应用层面，我们可以通过缓存机制、异步处理、连接池优化等方式提升性能。同时，代码层面的优化也不容忽视，包括算法优化、内存管理、并发控制等。此外，系统架构的合理设计也是性能优化的重要因素，微服务架构、负载均衡、CDN加速等都能有效提升系统性能。最后，我们还需要建立性能测试体系，定期进行压力测试和性能基准测试，确保系统在各种负载条件下都能稳定运行。
"""
        }
        
        return samples.get(text_type, samples['general'])


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RAG Flow文档分块功能测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --demo                           # 运行演示模式
  %(prog)s -i document.txt                  # 测试文件
  %(prog)s -t "测试文本内容"                 # 测试直接输入
  %(prog)s --performance                    # 性能测试
  %(prog)s -s recursive --chunk-size 500   # 自定义参数
        """
    )
    
    # 输入参数
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('--input', '-i', help='输入文件路径')
    input_group.add_argument('--text', '-t', help='直接输入文本内容')
    input_group.add_argument('--demo', action='store_true', help='运行演示模式')
    input_group.add_argument('--performance', action='store_true', help='性能测试模式')
    
    # 分块参数
    parser.add_argument('--strategy', '-s', default='recursive',
                       help='分块策略 (此版本只支持recursive)')
    parser.add_argument('--chunk-size', type=int, default=1000, help='分块大小 (默认: 1000)')
    parser.add_argument('--chunk-overlap', type=int, default=200, help='重叠大小 (默认: 200)')
    parser.add_argument('--min-chunk-size', type=int, default=100, help='最小分块大小 (默认: 100)')
    parser.add_argument('--max-chunk-size', type=int, default=2000, help='最大分块大小 (默认: 2000)')

    # 递归分块器特有参数
    parser.add_argument('--separators', nargs='*', help='自定义分隔符列表')
    parser.add_argument('--keep-separator', action='store_true', help='保留分隔符')
    
    # 输出参数
    parser.add_argument('--output-format', choices=['detailed', 'simple', 'json'],
                       default='detailed', help='输出格式 (默认: detailed)')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只输出结果')
    
    args = parser.parse_args()
    
    # 构建配置
    config = {
        'chunk_size': args.chunk_size,
        'chunk_overlap': args.chunk_overlap,
        'min_chunk_size': args.min_chunk_size,
        'max_chunk_size': args.max_chunk_size,
        'add_start_index': True
    }

    # 添加递归分块器特有配置
    if args.separators:
        config['separators'] = args.separators
    if args.keep_separator:
        config['keep_separator'] = True
    
    try:
        # 创建测试器
        tester = ChunkingTester(config)
        
        if not args.quiet:
            print("🚀 RAG Flow 递归分块器测试脚本启动")
            print(f"📋 当前配置: 分块大小={args.chunk_size}, 重叠={args.chunk_overlap}")

        # 根据参数执行不同的测试模式
        if args.demo:
            tester.run_demo()
        elif args.performance:
            tester.run_performance_test()
        elif args.input:
            # 文件输入模式
            if not os.path.exists(args.input):
                print(f"❌ 文件不存在: {args.input}")
                sys.exit(1)

            with open(args.input, 'r', encoding='utf-8') as f:
                text = f.read()

            metadata = {
                'file_name': os.path.basename(args.input),
                'file_path': args.input,
                'document_type': 'user_document',
                'title': f'用户文档: {os.path.basename(args.input)}'
            }

            result = tester.test_chunking(text, metadata)
            tester.visualize_chunks(result, args.output_format)

        elif args.text:
            # 直接文本输入模式
            metadata = {
                'file_name': 'direct_input.txt',
                'document_type': 'direct_input',
                'title': '直接输入文本'
            }

            result = tester.test_chunking(args.text, metadata)
            tester.visualize_chunks(result, args.output_format)
            
        else:
            # 默认显示帮助信息
            parser.print_help()
            print("\n💡 提示: 使用 --demo 参数运行演示模式，或使用 --help 查看详细帮助")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
