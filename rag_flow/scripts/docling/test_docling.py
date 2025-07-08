#!/usr/bin/env python3
"""
模块名称: test_docling
功能描述: Docling文档解析器命令行测试脚本，支持全面的配置测试和性能评估
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import argparse
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import traceback
from datetime import datetime
import csv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.document_processor.parsers.docling_parser import DoclingParser, DoclingParseResult
    print("✓ DoclingParser导入成功")
except ImportError as e:
    print(f"✗ DoclingParser导入失败: {e}")
    print("请确保:")
    print("1. 在项目根目录(rag_flow)下运行此脚本")
    print("2. 已激活uv虚拟环境: source .venv/bin/activate")
    print("3. 已安装docling库: uv add docling")
    sys.exit(1)

try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
    print("✓ 日志管理器导入成功")
except ImportError as e:
    print(f"⚠ 日志管理器导入失败，使用标准logging: {e}")
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


@dataclass
class TestResult:
    """测试结果数据类"""
    file_path: str
    file_name: str
    file_size: int
    file_format: str
    success: bool
    processing_time: float
    text_length: int
    element_counts: Dict[str, int]
    error_message: str = ""
    error_type: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def create_parser_config(args) -> Dict[str, Any]:
        """根据命令行参数创建DoclingParser配置"""
        config = {}
        
        # 基础配置
        if hasattr(args, 'enable_ocr') and args.enable_ocr is not None:
            config['enable_ocr'] = args.enable_ocr
        if hasattr(args, 'ocr_engine') and args.ocr_engine:
            config['ocr_engine'] = args.ocr_engine
        if hasattr(args, 'enable_table_structure') and args.enable_table_structure is not None:
            config['enable_table_structure'] = args.enable_table_structure
        if hasattr(args, 'table_mode') and args.table_mode:
            config['table_mode'] = args.table_mode
        if hasattr(args, 'enable_cell_matching') and args.enable_cell_matching is not None:
            config['enable_cell_matching'] = args.enable_cell_matching
            
        # 图片处理配置
        if hasattr(args, 'enable_picture_description') and args.enable_picture_description is not None:
            config['enable_picture_description'] = args.enable_picture_description
        if hasattr(args, 'picture_description_model') and args.picture_description_model:
            config['picture_description_model'] = args.picture_description_model
        if hasattr(args, 'picture_description_prompt') and args.picture_description_prompt:
            config['picture_description_prompt'] = args.picture_description_prompt
        if hasattr(args, 'enable_picture_classification') and args.enable_picture_classification is not None:
            config['enable_picture_classification'] = args.enable_picture_classification
        if hasattr(args, 'generate_picture_images') and args.generate_picture_images is not None:
            config['generate_picture_images'] = args.generate_picture_images
        if hasattr(args, 'images_scale') and args.images_scale:
            config['images_scale'] = args.images_scale
            
        # 内容识别配置
        if hasattr(args, 'enable_formula_enrichment') and args.enable_formula_enrichment is not None:
            config['enable_formula_enrichment'] = args.enable_formula_enrichment
        if hasattr(args, 'enable_code_enrichment') and args.enable_code_enrichment is not None:
            config['enable_code_enrichment'] = args.enable_code_enrichment
            
        # 系统配置
        if hasattr(args, 'max_num_pages') and args.max_num_pages:
            config['max_num_pages'] = args.max_num_pages
        if hasattr(args, 'max_file_size') and args.max_file_size:
            config['max_file_size'] = args.max_file_size
        if hasattr(args, 'artifacts_path') and args.artifacts_path:
            config['artifacts_path'] = args.artifacts_path
        if hasattr(args, 'enable_remote_services') and args.enable_remote_services is not None:
            config['enable_remote_services'] = args.enable_remote_services
            
        # 高级配置
        if hasattr(args, 'use_vlm_pipeline') and args.use_vlm_pipeline is not None:
            config['use_vlm_pipeline'] = args.use_vlm_pipeline
        if hasattr(args, 'vlm_model') and args.vlm_model:
            config['vlm_model'] = args.vlm_model
        if hasattr(args, 'custom_backend') and args.custom_backend:
            config['custom_backend'] = args.custom_backend
        if hasattr(args, 'allowed_formats') and args.allowed_formats:
            config['allowed_formats'] = args.allowed_formats
            
        return config


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        
    def start(self):
        """开始监控"""
        self.start_time = time.time()
        
    def stop(self):
        """停止监控"""
        self.end_time = time.time()
        
    def get_duration(self) -> float:
        """获取持续时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


class DoclingTester:
    """Docling测试器主类"""
    
    def __init__(self, config: Dict[str, Any], output_dir: str = "test_output"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TestResult] = []
        
    def test_single_file(self, file_path: str) -> TestResult:
        """测试单个文件"""
        file_path = Path(file_path)
        monitor = PerformanceMonitor()

        try:
            # 检查文件存在性
            if not file_path.exists():
                return TestResult(
                    file_path=str(file_path),
                    file_name=file_path.name,
                    file_size=0,
                    file_format="",
                    success=False,
                    processing_time=0.0,
                    text_length=0,
                    element_counts={},
                    error_message="文件不存在",
                    error_type="FileNotFoundError"
                )

            # 获取文件信息
            file_size = file_path.stat().st_size
            file_format = file_path.suffix.lower()

            # 创建解析器
            try:
                if self.config:
                    parser = DoclingParser(self.config)
                else:
                    parser = DoclingParser()
            except Exception as init_error:
                return TestResult(
                    file_path=str(file_path),
                    file_name=file_path.name,
                    file_size=file_size,
                    file_format=file_format,
                    success=False,
                    processing_time=0.0,
                    text_length=0,
                    element_counts={},
                    error_message=f"解析器初始化失败: {init_error}",
                    error_type="ParserInitError"
                )

            # 检查格式支持
            try:
                format_supported = parser.is_format_supported(str(file_path))
            except Exception:
                # 如果检查格式支持失败，使用默认列表
                supported_formats = ['.pdf', '.docx', '.doc', '.html', '.htm', '.xlsx', '.xls',
                                   '.csv', '.md', '.markdown', '.txt', '.png', '.jpg', '.jpeg',
                                   '.gif', '.bmp', '.tiff', '.tif', '.pptx', '.ppt']
                format_supported = file_format in supported_formats

            if not format_supported:
                return TestResult(
                    file_path=str(file_path),
                    file_name=file_path.name,
                    file_size=file_size,
                    file_format=file_format,
                    success=False,
                    processing_time=0.0,
                    text_length=0,
                    element_counts={},
                    error_message=f"不支持的文件格式: {file_format}",
                    error_type="UnsupportedFormat"
                )
            
            # 开始解析
            monitor.start()
            result = parser.parse(str(file_path))
            monitor.stop()
            
            # 提取元素统计
            element_counts = {
                'total_elements': result.metadata.get('total_elements', 0),
                'text_elements': result.metadata.get('text_elements', 0),
                'table_elements': result.metadata.get('table_elements', 0),
                'image_elements': result.metadata.get('image_elements', 0),
                'heading_elements': result.metadata.get('heading_elements', 0),
                'list_elements': result.metadata.get('list_elements', 0),
                'code_elements': result.metadata.get('code_elements', 0),
                'formula_elements': result.metadata.get('formula_elements', 0)
            }
            
            return TestResult(
                file_path=str(file_path),
                file_name=file_path.name,
                file_size=file_size,
                file_format=file_format,
                success=True,
                processing_time=monitor.get_duration(),
                text_length=len(result.text_content),
                element_counts=element_counts,
                metadata=result.metadata
            )
            
        except Exception as e:
            monitor.stop()
            return TestResult(
                file_path=str(file_path),
                file_name=file_path.name,
                file_size=file_path.stat().st_size if file_path.exists() else 0,
                file_format=file_path.suffix.lower() if file_path.exists() else "",
                success=False,
                processing_time=monitor.get_duration(),
                text_length=0,
                element_counts={},
                error_message=str(e),
                error_type=type(e).__name__
            )
    
    def test_batch_files(self, file_paths: List[str], verbose: bool = False) -> List[TestResult]:
        """批量测试文件"""
        results = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths, 1):
            if verbose:
                print(f"处理文件 {i}/{total_files}: {Path(file_path).name}")
            
            result = self.test_single_file(file_path)
            results.append(result)
            self.results.append(result)
            
            if verbose:
                status = "✓" if result.success else "✗"
                print(f"  {status} {result.processing_time:.2f}s - {result.error_message if not result.success else 'OK'}")
        
        return results

    def test_preset_comparison(self, file_path: str) -> Dict[str, TestResult]:
        """测试不同预设配置的效果对比"""
        presets = ['basic', 'ocr_only', 'table_focus', 'image_focus', 'academic']
        results = {}

        for preset in presets:
            try:
                parser = DoclingParser.create_with_preset(preset)
                monitor = PerformanceMonitor()

                monitor.start()
                result = parser.parse(file_path)
                monitor.stop()

                file_path_obj = Path(file_path)
                element_counts = {
                    'total_elements': result.metadata.get('total_elements', 0),
                    'text_elements': result.metadata.get('text_elements', 0),
                    'table_elements': result.metadata.get('table_elements', 0),
                    'image_elements': result.metadata.get('image_elements', 0),
                    'heading_elements': result.metadata.get('heading_elements', 0),
                    'list_elements': result.metadata.get('list_elements', 0),
                    'code_elements': result.metadata.get('code_elements', 0),
                    'formula_elements': result.metadata.get('formula_elements', 0)
                }

                results[preset] = TestResult(
                    file_path=file_path,
                    file_name=file_path_obj.name,
                    file_size=file_path_obj.stat().st_size,
                    file_format=file_path_obj.suffix.lower(),
                    success=True,
                    processing_time=monitor.get_duration(),
                    text_length=len(result.text_content),
                    element_counts=element_counts,
                    metadata=result.metadata
                )

            except Exception as e:
                file_path_obj = Path(file_path)
                results[preset] = TestResult(
                    file_path=file_path,
                    file_name=file_path_obj.name,
                    file_size=file_path_obj.stat().st_size if file_path_obj.exists() else 0,
                    file_format=file_path_obj.suffix.lower() if file_path_obj.exists() else "",
                    success=False,
                    processing_time=0.0,
                    text_length=0,
                    element_counts={},
                    error_message=str(e),
                    error_type=type(e).__name__
                )

        return results

    def check_dependencies(self) -> Dict[str, bool]:
        """检查依赖库状态"""
        return DoclingParser.check_dependencies()

    def get_format_support(self) -> List[str]:
        """获取支持的格式列表"""
        try:
            parser = DoclingParser()
            return parser.get_supported_formats()
        except Exception:
            return []

    def run_performance_benchmark(self, file_paths: List[str], iterations: int = 3) -> Dict[str, Any]:
        """运行性能基准测试"""
        benchmark_results = {
            'iterations': iterations,
            'total_files': len(file_paths),
            'file_results': [],
            'summary': {}
        }

        print(f"运行性能基准测试: {len(file_paths)} 个文件, {iterations} 次迭代")

        for file_path in file_paths:
            file_path_obj = Path(file_path)
            file_results = {
                'file_path': file_path,
                'file_name': file_path_obj.name,
                'file_size': file_path_obj.stat().st_size if file_path_obj.exists() else 0,
                'file_format': file_path_obj.suffix.lower(),
                'iterations': [],
                'avg_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'success_rate': 0.0
            }

            successful_runs = 0
            total_time = 0.0

            print(f"  测试文件: {file_path_obj.name}")

            for i in range(iterations):
                print(f"    迭代 {i+1}/{iterations}...", end=' ')

                try:
                    result = self.test_single_file(file_path)
                    if result.success:
                        successful_runs += 1
                        total_time += result.processing_time
                        file_results['iterations'].append({
                            'iteration': i+1,
                            'success': True,
                            'time': result.processing_time,
                            'text_length': result.text_length
                        })
                        file_results['min_time'] = min(file_results['min_time'], result.processing_time)
                        file_results['max_time'] = max(file_results['max_time'], result.processing_time)
                        print(f"✓ {result.processing_time:.3f}s")
                    else:
                        file_results['iterations'].append({
                            'iteration': i+1,
                            'success': False,
                            'error': result.error_message
                        })
                        print(f"✗ {result.error_message}")
                except Exception as e:
                    file_results['iterations'].append({
                        'iteration': i+1,
                        'success': False,
                        'error': str(e)
                    })
                    print(f"✗ {str(e)}")

            if successful_runs > 0:
                file_results['avg_time'] = total_time / successful_runs
                file_results['success_rate'] = successful_runs / iterations
            else:
                file_results['min_time'] = 0.0

            benchmark_results['file_results'].append(file_results)

        # 计算总体统计
        all_times = []
        total_success = 0
        total_attempts = 0

        for file_result in benchmark_results['file_results']:
            for iteration in file_result['iterations']:
                total_attempts += 1
                if iteration['success']:
                    total_success += 1
                    all_times.append(iteration['time'])

        if all_times:
            benchmark_results['summary'] = {
                'overall_success_rate': total_success / total_attempts,
                'avg_processing_time': sum(all_times) / len(all_times),
                'min_processing_time': min(all_times),
                'max_processing_time': max(all_times),
                'total_successful_runs': total_success,
                'total_attempts': total_attempts
            }

        return benchmark_results


class ResultReporter:
    """结果报告器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def print_summary(self, results: List[TestResult]):
        """打印测试摘要"""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        print(f"\n{'='*60}")
        print(f"测试摘要")
        print(f"{'='*60}")
        print(f"总文件数: {total}")
        print(f"成功: {successful} ({successful/total*100:.1f}%)" if total > 0 else "成功: 0")
        print(f"失败: {failed} ({failed/total*100:.1f}%)" if total > 0 else "失败: 0")

        if successful > 0:
            avg_time = sum(r.processing_time for r in results if r.success) / successful
            avg_text_length = sum(r.text_length for r in results if r.success) / successful
            print(f"平均处理时间: {avg_time:.2f}秒")
            print(f"平均文本长度: {avg_text_length:.0f}字符")

        # 错误统计
        if failed > 0:
            error_types = {}
            for r in results:
                if not r.success:
                    error_types[r.error_type] = error_types.get(r.error_type, 0) + 1

            print(f"\n错误类型统计:")
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count}")

    def save_json_report(self, results: List[TestResult], filename: str = "test_results.json"):
        """保存JSON格式的详细报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(results),
            'successful': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'results': [asdict(result) for result in results]
        }

        output_file = self.output_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"详细报告已保存到: {output_file}")

    def save_csv_summary(self, results: List[TestResult], filename: str = "test_summary.csv"):
        """保存CSV格式的摘要报告"""
        output_file = self.output_dir / filename

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 写入标题行
            writer.writerow([
                '文件名', '文件大小(字节)', '格式', '成功', '处理时间(秒)',
                '文本长度', '总元素数', '表格数', '图片数', '标题数', '错误信息'
            ])

            # 写入数据行
            for result in results:
                writer.writerow([
                    result.file_name,
                    result.file_size,
                    result.file_format,
                    '是' if result.success else '否',
                    f"{result.processing_time:.2f}",
                    result.text_length,
                    result.element_counts.get('total_elements', 0),
                    result.element_counts.get('table_elements', 0),
                    result.element_counts.get('image_elements', 0),
                    result.element_counts.get('heading_elements', 0),
                    result.error_message
                ])

        print(f"CSV摘要已保存到: {output_file}")

    def save_markdown_report(self, results: List[TestResult], filename: str = "test_report.md"):
        """保存Markdown格式的报告"""
        output_file = self.output_dir / filename

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Docling解析器测试报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 统计信息
            total = len(results)
            successful = sum(1 for r in results if r.success)
            failed = total - successful

            f.write("## 测试统计\n\n")
            f.write(f"- 总文件数: {total}\n")
            f.write(f"- 成功: {successful} ({successful/total*100:.1f}%)\n" if total > 0 else "- 成功: 0\n")
            f.write(f"- 失败: {failed} ({failed/total*100:.1f}%)\n\n" if total > 0 else "- 失败: 0\n\n")

            # 详细结果
            f.write("## 详细结果\n\n")
            f.write("| 文件名 | 格式 | 状态 | 处理时间 | 文本长度 | 元素数 | 错误信息 |\n")
            f.write("|--------|------|------|----------|----------|--------|----------|\n")

            for result in results:
                status = "✓" if result.success else "✗"
                error_msg = result.error_message[:50] + "..." if len(result.error_message) > 50 else result.error_message
                f.write(f"| {result.file_name} | {result.file_format} | {status} | {result.processing_time:.2f}s | {result.text_length} | {result.element_counts.get('total_elements', 0)} | {error_msg} |\n")

        print(f"Markdown报告已保存到: {output_file}")

    def save_benchmark_report(self, benchmark_results: Dict[str, Any], filename: str = "benchmark_results.json"):
        """保存性能基准测试报告"""
        output_file = self.output_dir / filename

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, ensure_ascii=False, indent=2)

        print(f"性能基准测试报告已保存到: {output_file}")

    def save_error_analysis(self, error_analysis: Dict[str, Any], filename: str = "error_analysis.json"):
        """保存错误分析报告"""
        output_file = self.output_dir / filename

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(error_analysis, f, ensure_ascii=False, indent=2)

        print(f"错误分析报告已保存到: {output_file}")

    def print_preset_comparison(self, comparison_results: Dict[str, TestResult]):
        """打印预设配置对比结果"""
        print(f"\n{'='*80}")
        print(f"预设配置对比结果")
        print(f"{'='*80}")

        print(f"{'预设':<15} {'状态':<6} {'时间(s)':<10} {'文本长度':<10} {'元素数':<8} {'表格':<6} {'图片':<6}")
        print("-" * 80)

        for preset, result in comparison_results.items():
            status = "✓" if result.success else "✗"
            time_str = f"{result.processing_time:.2f}" if result.success else "N/A"
            text_len = result.text_length if result.success else 0
            total_elements = result.element_counts.get('total_elements', 0) if result.success else 0
            table_elements = result.element_counts.get('table_elements', 0) if result.success else 0
            image_elements = result.element_counts.get('image_elements', 0) if result.success else 0

            print(f"{preset:<15} {status:<6} {time_str:<10} {text_len:<10} {total_elements:<8} {table_elements:<6} {image_elements:<6}")

            if not result.success:
                print(f"  错误: {result.error_message}")

    def print_performance_benchmark(self, benchmark_results: Dict[str, Any]):
        """打印性能基准测试结果"""
        print(f"\n{'='*80}")
        print(f"性能基准测试结果")
        print(f"{'='*80}")

        summary = benchmark_results.get('summary', {})
        if summary:
            print(f"总体统计:")
            print(f"  成功率: {summary['overall_success_rate']*100:.1f}%")
            print(f"  平均处理时间: {summary['avg_processing_time']:.3f}秒")
            print(f"  最快处理时间: {summary['min_processing_time']:.3f}秒")
            print(f"  最慢处理时间: {summary['max_processing_time']:.3f}秒")
            print(f"  成功运行次数: {summary['total_successful_runs']}/{summary['total_attempts']}")

        print(f"\n文件详细结果:")
        print(f"{'文件名':<20} {'成功率':<8} {'平均时间':<10} {'最小时间':<10} {'最大时间':<10}")
        print("-" * 80)

        for file_result in benchmark_results['file_results']:
            success_rate = f"{file_result['success_rate']*100:.1f}%"
            avg_time = f"{file_result['avg_time']:.3f}s" if file_result['avg_time'] > 0 else "N/A"
            min_time = f"{file_result['min_time']:.3f}s" if file_result['min_time'] != float('inf') else "N/A"
            max_time = f"{file_result['max_time']:.3f}s" if file_result['max_time'] > 0 else "N/A"

            print(f"{file_result['file_name']:<20} {success_rate:<8} {avg_time:<10} {min_time:<10} {max_time:<10}")

    def analyze_errors(self, results: List[TestResult]) -> Dict[str, Any]:
        """分析错误模式"""
        error_analysis = {
            'total_errors': 0,
            'error_types': {},
            'error_patterns': {},
            'file_format_errors': {},
            'recommendations': []
        }

        failed_results = [r for r in results if not r.success]
        error_analysis['total_errors'] = len(failed_results)

        if not failed_results:
            return error_analysis

        # 分析错误类型
        for result in failed_results:
            error_type = result.error_type
            error_analysis['error_types'][error_type] = error_analysis['error_types'].get(error_type, 0) + 1

            # 分析文件格式相关错误
            file_format = result.file_format
            if file_format not in error_analysis['file_format_errors']:
                error_analysis['file_format_errors'][file_format] = []
            error_analysis['file_format_errors'][file_format].append(result.error_message)

            # 分析错误模式
            error_msg = result.error_message.lower()
            if 'format not allowed' in error_msg or 'not supported' in error_msg:
                error_analysis['error_patterns']['format_issues'] = error_analysis['error_patterns'].get('format_issues', 0) + 1
            elif 'file not found' in error_msg or 'not exist' in error_msg:
                error_analysis['error_patterns']['file_not_found'] = error_analysis['error_patterns'].get('file_not_found', 0) + 1
            elif 'memory' in error_msg or 'size' in error_msg:
                error_analysis['error_patterns']['memory_issues'] = error_analysis['error_patterns'].get('memory_issues', 0) + 1
            elif 'timeout' in error_msg:
                error_analysis['error_patterns']['timeout_issues'] = error_analysis['error_patterns'].get('timeout_issues', 0) + 1
            else:
                error_analysis['error_patterns']['other'] = error_analysis['error_patterns'].get('other', 0) + 1

        # 生成建议
        if error_analysis['error_patterns'].get('format_issues', 0) > 0:
            error_analysis['recommendations'].append("检查文件格式支持，考虑转换不支持的格式")
        if error_analysis['error_patterns'].get('memory_issues', 0) > 0:
            error_analysis['recommendations'].append("使用--max-file-size限制文件大小，或增加系统内存")
        if error_analysis['error_patterns'].get('timeout_issues', 0) > 0:
            error_analysis['recommendations'].append("对大文件使用--max-num-pages限制页数")
        if error_analysis['error_patterns'].get('file_not_found', 0) > 0:
            error_analysis['recommendations'].append("检查文件路径和权限")

        return error_analysis

    def print_error_analysis(self, error_analysis: Dict[str, Any]):
        """打印错误分析结果"""
        if error_analysis['total_errors'] == 0:
            print(f"\n✓ 没有发现错误")
            return

        print(f"\n{'='*60}")
        print(f"错误分析报告")
        print(f"{'='*60}")
        print(f"总错误数: {error_analysis['total_errors']}")

        # 错误类型统计
        if error_analysis['error_types']:
            print(f"\n错误类型分布:")
            for error_type, count in error_analysis['error_types'].items():
                print(f"  {error_type}: {count}")

        # 错误模式分析
        if error_analysis['error_patterns']:
            print(f"\n错误模式分析:")
            for pattern, count in error_analysis['error_patterns'].items():
                print(f"  {pattern}: {count}")

        # 文件格式错误
        if error_analysis['file_format_errors']:
            print(f"\n按文件格式分组的错误:")
            for file_format, errors in error_analysis['file_format_errors'].items():
                print(f"  {file_format}: {len(errors)} 个错误")
                for error in set(errors):  # 去重
                    print(f"    - {error}")

        # 建议
        if error_analysis['recommendations']:
            print(f"\n建议:")
            for i, recommendation in enumerate(error_analysis['recommendations'], 1):
                print(f"  {i}. {recommendation}")


def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Docling文档解析器测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 测试单个文件
  python test_docling.py --input-file document.pdf

  # 批量测试目录中的文件
  python test_docling.py --input-dir /path/to/documents --verbose

  # 使用预设配置测试
  python test_docling.py --input-file document.pdf --preset academic

  # 预设配置对比测试
  python test_docling.py --input-file document.pdf --test-mode preset-comparison

  # 性能测试
  python test_docling.py --input-dir /path/to/documents --test-mode performance
        """
    )

    # 输入参数
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--input-file', '-f', type=str, help='输入文件路径')
    input_group.add_argument('--input-dir', '-d', type=str, help='输入目录路径')

    # 输出参数
    parser.add_argument('--output-dir', '-o', type=str, default='test_output', help='输出目录路径 (默认: test_output)')

    # 测试模式
    parser.add_argument('--test-mode', '-m', type=str,
                       choices=['single', 'batch', 'performance', 'preset-comparison', 'dependency-check'],
                       default='single', help='测试模式 (默认: single)')

    # 预设配置
    parser.add_argument('--preset', '-p', type=str,
                       choices=['basic', 'ocr_only', 'table_focus', 'image_focus', 'academic', 'vlm'],
                       help='使用预设配置')

    # 基础配置参数
    ocr_group = parser.add_argument_group('OCR配置')
    ocr_group.add_argument('--enable-ocr', type=bool, help='启用OCR (默认: True)')
    ocr_group.add_argument('--disable-ocr', action='store_true', help='禁用OCR')
    ocr_group.add_argument('--ocr-engine', type=str, choices=['easyocr', 'tesseract'], help='OCR引擎类型')

    # 表格配置参数
    table_group = parser.add_argument_group('表格配置')
    table_group.add_argument('--enable-table-structure', type=bool, help='启用表格结构识别')
    table_group.add_argument('--table-mode', type=str, choices=['fast', 'accurate'], help='表格模式')
    table_group.add_argument('--enable-cell-matching', type=bool, help='启用单元格匹配')

    # 图片配置参数
    image_group = parser.add_argument_group('图片配置')
    image_group.add_argument('--enable-picture-description', type=bool, help='启用图片描述')
    image_group.add_argument('--picture-description-model', type=str, help='图片描述模型')
    image_group.add_argument('--picture-description-prompt', type=str, help='图片描述提示词')
    image_group.add_argument('--enable-picture-classification', type=bool, help='启用图片分类')
    image_group.add_argument('--generate-picture-images', type=bool, help='生成图片')
    image_group.add_argument('--images-scale', type=int, help='图片缩放比例')

    # 内容识别配置
    content_group = parser.add_argument_group('内容识别配置')
    content_group.add_argument('--enable-formula-enrichment', type=bool, help='启用公式识别')
    content_group.add_argument('--enable-code-enrichment', type=bool, help='启用代码识别')

    # 系统配置
    system_group = parser.add_argument_group('系统配置')
    system_group.add_argument('--max-num-pages', type=int, help='最大页数限制')
    system_group.add_argument('--max-file-size', type=int, help='最大文件大小限制(字节)')
    system_group.add_argument('--artifacts-path', type=str, help='模型文件路径')
    system_group.add_argument('--enable-remote-services', type=bool, help='启用远程服务')

    # 高级配置
    advanced_group = parser.add_argument_group('高级配置')
    advanced_group.add_argument('--use-vlm-pipeline', type=bool, help='使用VLM管道')
    advanced_group.add_argument('--vlm-model', type=str, help='VLM模型名称')
    advanced_group.add_argument('--custom-backend', type=str, help='自定义后端')
    advanced_group.add_argument('--allowed-formats', type=str, nargs='+', help='允许的文件格式列表')

    # 其他选项
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--save-results', action='store_true', help='保存测试结果到文件')
    parser.add_argument('--benchmark-iterations', type=int, default=3, help='性能基准测试迭代次数 (默认: 3)')
    parser.add_argument('--include-error-analysis', action='store_true', help='包含详细的错误分析')

    return parser


def collect_files(input_path: str, supported_formats: List[str]) -> List[str]:
    """收集要测试的文件"""
    input_path = Path(input_path)
    files = []

    if input_path.is_file():
        files.append(str(input_path))
    elif input_path.is_dir():
        for file_path in input_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                files.append(str(file_path))

    return files


def main():
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # 处理禁用OCR选项
    if args.disable_ocr:
        args.enable_ocr = False

    # 检查输入参数（dependency-check模式除外）
    if args.test_mode != 'dependency-check' and not args.input_file and not args.input_dir:
        parser.error("除dependency-check模式外，必须指定 --input-file 或 --input-dir")

    # 检查依赖
    print("检查依赖库...")
    dependencies = DoclingParser.check_dependencies()

    if not dependencies.get('docling', False):
        print("错误: Docling库未安装或不可用")
        print("请运行: pip install docling")
        sys.exit(1)

    print("依赖检查:")
    for dep, available in dependencies.items():
        status = "✓" if available else "✗"
        print(f"  {dep}: {status}")

    # 获取支持的格式
    try:
        temp_parser = DoclingParser()
        supported_formats = temp_parser.get_supported_formats()
        print(f"\n支持的格式: {', '.join(supported_formats)}")
    except Exception as e:
        print(f"⚠ 无法获取支持的格式: {e}")
        # 使用默认的支持格式列表
        supported_formats = ['.pdf', '.docx', '.doc', '.html', '.htm', '.xlsx', '.xls',
                           '.csv', '.md', '.markdown', '.txt', '.png', '.jpg', '.jpeg',
                           '.gif', '.bmp', '.tiff', '.tif', '.pptx', '.ppt']
        print(f"使用默认支持格式: {', '.join(supported_formats)}")

        # 如果是dependency-check模式，继续执行
        if args.test_mode != 'dependency-check':
            sys.exit(1)

    # 创建配置
    if args.preset:
        print(f"\n使用预设配置: {args.preset}")
        config = {}  # 预设配置将在创建解析器时应用
    else:
        config = ConfigManager.create_parser_config(args)
        if config:
            print(f"\n自定义配置: {config}")
        else:
            print("\n使用默认配置")

    # 收集文件（dependency-check模式除外）
    if args.test_mode != 'dependency-check':
        if args.input_file:
            files = [args.input_file]
        else:
            files = collect_files(args.input_dir, supported_formats)
            if not files:
                print(f"在目录 {args.input_dir} 中未找到支持的文件")
                sys.exit(1)
            print(f"\n找到 {len(files)} 个文件待测试")
    else:
        files = []

    # 创建测试器和报告器
    tester = DoclingTester(config, args.output_dir)
    reporter = ResultReporter(Path(args.output_dir))

    # 执行测试
    print(f"\n开始测试...")
    start_time = time.time()

    if args.test_mode == 'dependency-check':
        print("\n依赖检查模式")
        deps = tester.check_dependencies()
        formats = tester.get_format_support()

        print(f"\n依赖状态:")
        for dep, available in deps.items():
            status = "✓" if available else "✗"
            print(f"  {dep}: {status}")

        print(f"\n支持的格式 ({len(formats)}):")
        for fmt in formats:
            print(f"  {fmt}")

        return

    elif args.test_mode == 'preset-comparison':
        if len(files) != 1:
            print("预设对比模式只支持单个文件")
            sys.exit(1)

        print(f"\n预设配置对比测试: {files[0]}")
        comparison_results = tester.test_preset_comparison(files[0])
        reporter.print_preset_comparison(comparison_results)

        if args.save_results:
            # 保存对比结果
            comparison_data = {
                'timestamp': datetime.now().isoformat(),
                'file_path': files[0],
                'results': {preset: asdict(result) for preset, result in comparison_results.items()}
            }

            output_file = Path(args.output_dir) / "preset_comparison.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(comparison_data, f, ensure_ascii=False, indent=2)
            print(f"\n对比结果已保存到: {output_file}")

        return

    elif args.test_mode in ['single', 'batch', 'performance']:
        if args.test_mode == 'performance':
            iterations = args.benchmark_iterations
            print(f"\n性能基准测试: {len(files)} 个文件, {iterations} 次迭代")
            benchmark_results = tester.run_performance_benchmark(files, iterations=iterations)
            reporter.print_performance_benchmark(benchmark_results)

            if args.save_results:
                reporter.save_benchmark_report(benchmark_results)

            return
        elif args.test_mode == 'single' and len(files) == 1:
            print(f"\n单文件测试: {files[0]}")
            results = [tester.test_single_file(files[0])]
        else:
            print(f"\n批量测试: {len(files)} 个文件")
            results = tester.test_batch_files(files, args.verbose)

    end_time = time.time()
    total_time = end_time - start_time

    # 显示结果
    reporter.print_summary(results)
    print(f"\n总测试时间: {total_time:.2f}秒")

    # 错误分析
    error_analysis = reporter.analyze_errors(results)
    reporter.print_error_analysis(error_analysis)

    # 保存结果
    if args.save_results:
        print(f"\n保存测试结果...")
        reporter.save_json_report(results)
        reporter.save_csv_summary(results)
        reporter.save_markdown_report(results)

        if error_analysis['total_errors'] > 0:
            reporter.save_error_analysis(error_analysis)

    # 显示失败的文件详情
    failed_results = [r for r in results if not r.success]
    if failed_results and args.verbose:
        print(f"\n失败文件详情:")
        for result in failed_results:
            print(f"  {result.file_name}: {result.error_type} - {result.error_message}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n程序执行出错: {e}")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            traceback.print_exc()
        sys.exit(1)
