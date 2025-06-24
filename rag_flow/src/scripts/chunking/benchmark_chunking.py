#!/usr/bin/env python3
"""
模块名称: benchmark_chunking
功能描述: 简化分块系统性能基准测试脚本
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0

使用说明:
    python benchmark_chunking.py                    # 运行标准基准测试
    python benchmark_chunking.py --preset semantic  # 测试特定预设
    python benchmark_chunking.py --sizes 1000 5000 10000  # 自定义测试大小
    python benchmark_chunking.py --iterations 10    # 设置测试迭代次数
    python benchmark_chunking.py --output results.json  # 保存结果到文件
"""

import argparse
import json
import time
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.document_processor.chunking.chunking_engine import ChunkingEngine
    CHUNKING_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"导入ChunkingEngine失败: {e}")
    CHUNKING_ENGINE_AVAILABLE = False


class ChunkingBenchmark:
    """分块系统性能基准测试器"""
    
    def __init__(self):
        """初始化基准测试器"""
        self.engine = None
        if CHUNKING_ENGINE_AVAILABLE:
            try:
                self.engine = ChunkingEngine()
                print("✅ 分块引擎初始化成功")
            except Exception as e:
                print(f"❌ 分块引擎初始化失败: {e}")
        else:
            print("❌ 分块引擎不可用")
    
    def generate_test_text(self, size: int) -> str:
        """
        生成指定大小的测试文本
        
        Args:
            size: 目标文本大小（字符数）
            
        Returns:
            str: 生成的测试文本
        """
        base_text = """
第一章 系统架构设计

本章介绍系统的整体架构设计理念和实现方案。系统采用微服务架构，具有高可用性、可扩展性和可维护性的特点。

1.1 架构概述
微服务架构是一种将单一应用程序开发为一组小型服务的方法，每个服务运行在自己的进程中，并使用轻量级机制（通常是HTTP资源API）进行通信。这些服务围绕业务功能构建，并且可以通过全自动部署机制独立部署。

1.2 核心组件
系统主要包含以下核心组件：
- 用户管理服务：负责用户认证、授权和用户信息管理
- 数据处理服务：处理各种数据的采集、清洗和分析
- 接口网关：统一的API入口，负责路由、限流和安全控制
- 配置中心：集中管理各服务的配置信息
- 监控中心：实时监控系统运行状态和性能指标

1.3 技术选型
在技术选型方面，我们选择了成熟稳定的技术栈：
- 后端框架：Spring Boot 2.7，提供快速开发能力
- 数据库：MySQL 8.0作为主数据库，Redis 6.2作为缓存
- 消息队列：RabbitMQ 3.9，支持异步处理和解耦
- 容器化：Docker + Kubernetes，支持弹性伸缩
- 监控：Prometheus + Grafana，提供全面的监控能力

第二章 系统实现

本章详细介绍系统的具体实现方案和关键技术点。

2.1 服务拆分策略
服务拆分遵循单一职责原则，每个服务只负责一个业务领域。同时考虑数据一致性和事务边界，避免分布式事务的复杂性。

2.2 数据存储设计
采用读写分离架构，主库负责写操作，从库负责读操作。对于高频访问的数据，使用Redis进行缓存，提升系统响应速度。

2.3 安全机制
实现多层次的安全防护：
- 网络层：使用防火墙和VPN
- 应用层：JWT令牌认证和RBAC权限控制
- 数据层：数据加密和脱敏处理
"""
        
        # 重复文本直到达到目标大小
        repeated_text = base_text * (size // len(base_text) + 1)
        return repeated_text[:size]
    
    def benchmark_preset(self, preset_name: str, text_sizes: List[int], 
                        iterations: int = 3) -> Dict[str, Any]:
        """
        对指定预设进行基准测试
        
        Args:
            preset_name: 预设名称
            text_sizes: 测试文本大小列表
            iterations: 每个大小的测试迭代次数
            
        Returns:
            dict: 基准测试结果
        """
        if not self.engine:
            raise RuntimeError("分块引擎不可用")
        
        results = {
            'preset_name': preset_name,
            'iterations': iterations,
            'test_results': []
        }
        
        for size in text_sizes:
            print(f"\n测试文本大小: {size:,} 字符")
            
            # 生成测试文本
            test_text = self.generate_test_text(size)
            metadata = {
                'file_name': f'benchmark_{size}.txt',
                'document_type': 'benchmark',
                'title': f'基准测试文档 ({size}字符)'
            }
            
            # 多次测试取平均值
            times = []
            chunk_counts = []
            
            for i in range(iterations):
                print(f"  迭代 {i+1}/{iterations}...", end=' ')
                
                start_time = time.time()
                try:
                    chunks = self.engine.chunk_document(test_text, metadata, preset_name)
                    end_time = time.time()
                    
                    processing_time = end_time - start_time
                    chunk_count = len(chunks)
                    
                    times.append(processing_time)
                    chunk_counts.append(chunk_count)
                    
                    print(f"{processing_time:.3f}s ({chunk_count}块)")
                    
                except Exception as e:
                    print(f"失败: {e}")
                    continue
            
            if times:
                # 计算统计信息
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                std_time = statistics.stdev(times) if len(times) > 1 else 0
                
                avg_chunks = statistics.mean(chunk_counts)
                speed = size / avg_time
                
                result = {
                    'text_size': size,
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'std_time': std_time,
                    'avg_chunks': avg_chunks,
                    'speed': speed,
                    'iterations_completed': len(times)
                }
                
                results['test_results'].append(result)
                
                print(f"  平均时间: {avg_time:.3f}s ± {std_time:.3f}s")
                print(f"  处理速度: {speed:.0f} 字符/秒")
                print(f"  平均分块数: {avg_chunks:.1f}")
            else:
                print(f"  ❌ 所有迭代都失败")
        
        return results
    
    def compare_presets(self, presets: List[str], text_sizes: List[int], 
                       iterations: int = 3) -> Dict[str, Any]:
        """
        比较多个预设的性能
        
        Args:
            presets: 预设名称列表
            text_sizes: 测试文本大小列表
            iterations: 每个测试的迭代次数
            
        Returns:
            dict: 比较结果
        """
        comparison_results = {
            'presets': presets,
            'text_sizes': text_sizes,
            'iterations': iterations,
            'results': {}
        }
        
        for preset in presets:
            print(f"\n{'='*60}")
            print(f"测试预设: {preset}")
            print(f"{'='*60}")
            
            try:
                result = self.benchmark_preset(preset, text_sizes, iterations)
                comparison_results['results'][preset] = result
            except Exception as e:
                print(f"❌ 预设 {preset} 测试失败: {e}")
                comparison_results['results'][preset] = {'error': str(e)}
        
        return comparison_results
    
    def print_summary(self, results: Dict[str, Any]) -> None:
        """打印测试结果摘要"""
        print(f"\n{'='*80}")
        print("📊 性能基准测试摘要")
        print(f"{'='*80}")
        
        if 'results' in results:
            # 多预设比较结果
            print(f"{'预设':>15} {'文本大小':>10} {'平均时间':>10} {'速度':>12} {'分块数':>8}")
            print("-" * 70)
            
            for preset_name, preset_result in results['results'].items():
                if 'error' in preset_result:
                    print(f"{preset_name:>15} {'ERROR':>10} {'ERROR':>10} {'ERROR':>12} {'ERROR':>8}")
                    continue
                
                for test_result in preset_result.get('test_results', []):
                    size = test_result['text_size']
                    avg_time = test_result['avg_time']
                    speed = test_result['speed']
                    avg_chunks = test_result['avg_chunks']
                    
                    print(f"{preset_name:>15} {size:>10,} {avg_time:>9.3f}s {speed:>10.0f}/s {avg_chunks:>7.1f}")
        else:
            # 单预设结果
            preset_name = results.get('preset_name', 'unknown')
            print(f"预设: {preset_name}")
            print(f"{'文本大小':>10} {'平均时间':>10} {'速度':>12} {'分块数':>8}")
            print("-" * 45)
            
            for test_result in results.get('test_results', []):
                size = test_result['text_size']
                avg_time = test_result['avg_time']
                speed = test_result['speed']
                avg_chunks = test_result['avg_chunks']
                
                print(f"{size:>10,} {avg_time:>9.3f}s {speed:>10.0f}/s {avg_chunks:>7.1f}")
    
    def save_results(self, results: Dict[str, Any], output_file: str) -> None:
        """保存测试结果到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 结果已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="简化分块系统性能基准测试",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--preset', '-p', help='指定测试的预设名称')
    parser.add_argument('--presets', nargs='+', 
                       default=['standard', 'semantic', 'structure', 'aviation_maintenance'],
                       help='比较多个预设（默认: standard semantic structure aviation_maintenance）')
    parser.add_argument('--sizes', nargs='+', type=int,
                       default=[1000, 5000, 10000, 50000, 100000],
                       help='测试文本大小列表（默认: 1000 5000 10000 50000 100000）')
    parser.add_argument('--iterations', '-i', type=int, default=3,
                       help='每个测试的迭代次数（默认: 3）')
    parser.add_argument('--output', '-o', help='保存结果的文件路径')
    
    args = parser.parse_args()
    
    try:
        benchmark = ChunkingBenchmark()
        
        if args.preset:
            # 测试单个预设
            print(f"🚀 开始基准测试预设: {args.preset}")
            results = benchmark.benchmark_preset(args.preset, args.sizes, args.iterations)
        else:
            # 比较多个预设
            print(f"🚀 开始比较预设: {', '.join(args.presets)}")
            results = benchmark.compare_presets(args.presets, args.sizes, args.iterations)
        
        # 打印摘要
        benchmark.print_summary(results)
        
        # 保存结果
        if args.output:
            benchmark.save_results(results, args.output)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 基准测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
