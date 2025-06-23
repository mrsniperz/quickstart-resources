#!/usr/bin/env python3
"""
模块名称: docling_cli
功能描述: Docling文档处理器命令行工具
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.docling_parser import DoclingParser, DOCLING_AVAILABLE
from parsers.document_processor import DocumentProcessor
from utils.batch_processor import BatchProcessor, ConsoleProgressCallback
from config.config_manager import get_config_manager
from utils.performance_monitor import get_performance_monitor

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__, "docling_cli.log")
except ImportError:
    # 回退到标准logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


def cmd_parse_single(args):
    """解析单个文件"""
    if not DOCLING_AVAILABLE:
        logger.error("Docling库未安装，请运行: pip install docling")
        return 1

    try:
        # 初始化解析器
        config = {}
        if args.config:
            config_manager = get_config_manager()
            config = config_manager.get_docling_config()

        parser = DoclingParser(config)

        # 检查文件格式支持
        if not parser.is_format_supported(args.input):
            logger.error(f"不支持的文件格式: {Path(args.input).suffix}")
            return 1

        logger.info(f"正在处理文件: {args.input}")

        # 解析文件
        result = parser.parse(args.input)
        
        # 输出结果
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if args.format == 'markdown':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.text_content)
            elif args.format == 'json':
                data = {
                    'text_content': result.text_content,
                    'metadata': result.metadata,
                    'structured_data': result.structured_data,
                    'structure_info': result.structure_info
                }
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"结果已保存到: {output_path}")
        else:
            # 输出到控制台
            if args.format == 'markdown':
                print("\n=== 解析结果 ===")
                print(result.text_content)
            elif args.format == 'json':
                data = {
                    'text_content': result.text_content,
                    'metadata': result.metadata,
                    'structured_data': result.structured_data,
                    'structure_info': result.structure_info
                }
                print(json.dumps(data, indent=2, ensure_ascii=False))

        # 显示统计信息
        if args.stats:
            print(f"\n=== 统计信息 ===")
            print(f"文件大小: {result.metadata.get('file_size', 0)} 字节")
            print(f"文本长度: {len(result.text_content)} 字符")
            print(f"表格数量: {len(result.structured_data.get('tables', []))}")
            print(f"图片数量: {len(result.structured_data.get('images', []))}")
            print(f"标题数量: {len(result.structured_data.get('headings', []))}")

        return 0

    except Exception as e:
        logger.error(f"文件解析失败: {e}")
        return 1


def cmd_batch_process(args):
    """批量处理文件"""
    try:
        # 准备配置
        config = {
            'max_workers': args.workers,
            'continue_on_error': not args.stop_on_error,
            'output_format': args.format,
            'max_file_size': args.max_size * 1024 * 1024 if args.max_size else None
        }
        
        if args.config:
            config_manager = get_config_manager()
            config['processor_config'] = config_manager.get_document_processor_config()
        
        # 初始化批量处理器
        batch_processor = BatchProcessor(config)
        
        # 准备进度回调
        progress_callback = ConsoleProgressCallback(show_details=args.verbose)
        
        # 收集文件
        if args.directory:
            # 处理目录
            result = batch_processor.process_directory(
                args.input, args.output, 
                recursive=args.recursive,
                progress_callback=progress_callback
            )
        else:
            # 处理文件列表
            if args.input.endswith('.txt'):
                # 从文件读取文件列表
                with open(args.input, 'r', encoding='utf-8') as f:
                    file_paths = [line.strip() for line in f if line.strip()]
            else:
                file_paths = [args.input]
            
            result = batch_processor.process_files(
                file_paths, args.output,
                progress_callback=progress_callback
            )
        
        # 保存处理结果
        if args.report:
            report_data = {
                'summary': {
                    'total_files': result.total_files,
                    'successful_files': result.successful_files,
                    'failed_files': result.failed_files,
                    'processing_time': result.processing_time
                },
                'results': result.results,
                'errors': result.errors
            }
            
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            logger.info(f"处理报告已保存到: {args.report}")

        return 0 if result.failed_files == 0 else 1

    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        return 1


def cmd_check_dependencies(args):
    """检查依赖"""
    logger.info("检查Docling依赖...")

    if DOCLING_AVAILABLE:
        dependencies = DoclingParser.check_dependencies()

        print("依赖状态:")
        for dep, available in dependencies.items():
            status = "✓" if available else "✗"
            print(f"  {status} {dep}")

        if all(dependencies.values()):
            print("\n✓ 所有依赖都可用")
            logger.info("所有依赖都可用")
            return 0
        else:
            print("\n⚠️  部分依赖缺失")
            logger.warning("部分依赖缺失")
            return 1
    else:
        print("✗ Docling库未安装")
        print("请运行: pip install docling")
        logger.error("Docling库未安装")
        return 1


def cmd_show_formats(args):
    """显示支持的格式"""
    if not DOCLING_AVAILABLE:
        logger.error("Docling库未安装")
        return 1

    try:
        parser = DoclingParser()
        formats = parser.get_supported_formats()

        print("支持的文件格式:")
        for fmt in sorted(formats):
            print(f"  {fmt}")

        print(f"\n总计: {len(formats)} 种格式")
        logger.info(f"显示了 {len(formats)} 种支持的文件格式")
        return 0

    except Exception as e:
        logger.error(f"获取支持格式失败: {e}")
        return 1


def cmd_show_stats(args):
    """显示性能统计"""
    try:
        monitor = get_performance_monitor()
        stats = monitor.get_current_stats()

        print("性能统计信息:")
        print(f"  总处理文件数: {stats.get('total_processed', 0)}")
        print(f"  成功处理: {stats.get('total_success', 0)}")
        print(f"  处理失败: {stats.get('total_failed', 0)}")
        print(f"  成功率: {stats.get('success_rate', 0):.2%}")
        print(f"  平均处理时间: {stats.get('average_processing_time', 0):.2f}秒")

        if args.detailed:
            print("\n解析器统计:")
            for parser_type, parser_stats in stats.get('parser_stats', {}).items():
                print(f"  {parser_type}:")
                print(f"    处理数量: {parser_stats.get('count', 0)}")
                print(f"    成功率: {parser_stats.get('success_rate', 0):.2%}")
                print(f"    平均时间: {parser_stats.get('average_time', 0):.2f}秒")

        logger.info("显示性能统计信息完成")
        return 0

    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Docling文档处理器命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 解析单个文件
  %(prog)s parse document.pdf -o output.md
  
  # 批量处理目录
  %(prog)s batch /path/to/docs -o /path/to/output --directory
  
  # 检查依赖
  %(prog)s check
  
  # 显示支持的格式
  %(prog)s formats
        """
    )
    
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='日志级别')
    parser.add_argument('--config', action='store_true', help='使用配置文件')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 解析单个文件
    parse_parser = subparsers.add_parser('parse', help='解析单个文件')
    parse_parser.add_argument('input', help='输入文件路径')
    parse_parser.add_argument('-o', '--output', help='输出文件路径')
    parse_parser.add_argument('-f', '--format', choices=['markdown', 'json'], 
                             default='markdown', help='输出格式')
    parse_parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parse_parser.set_defaults(func=cmd_parse_single)
    
    # 批量处理
    batch_parser = subparsers.add_parser('batch', help='批量处理文件')
    batch_parser.add_argument('input', help='输入文件/目录路径或文件列表')
    batch_parser.add_argument('-o', '--output', help='输出目录')
    batch_parser.add_argument('-f', '--format', choices=['markdown', 'json'], 
                             default='markdown', help='输出格式')
    batch_parser.add_argument('--directory', action='store_true', help='处理目录')
    batch_parser.add_argument('--recursive', action='store_true', help='递归处理子目录')
    batch_parser.add_argument('--workers', type=int, default=4, help='并发工作线程数')
    batch_parser.add_argument('--stop-on-error', action='store_true', help='遇到错误时停止')
    batch_parser.add_argument('--max-size', type=int, help='最大文件大小(MB)')
    batch_parser.add_argument('--report', help='保存处理报告的文件路径')
    batch_parser.add_argument('--verbose', action='store_true', help='显示详细进度')
    batch_parser.set_defaults(func=cmd_batch_process)
    
    # 检查依赖
    check_parser = subparsers.add_parser('check', help='检查依赖')
    check_parser.set_defaults(func=cmd_check_dependencies)
    
    # 显示格式
    formats_parser = subparsers.add_parser('formats', help='显示支持的格式')
    formats_parser.set_defaults(func=cmd_show_formats)
    
    # 显示统计
    stats_parser = subparsers.add_parser('stats', help='显示性能统计')
    stats_parser.add_argument('--detailed', action='store_true', help='显示详细统计')
    stats_parser.set_defaults(func=cmd_show_stats)
    
    # 解析参数
    args = parser.parse_args()

    # 设置日志级别
    try:
        from src.utils.logger import SZ_LoggerManager
        import logging
        level = getattr(logging, args.log_level.upper())
        SZ_LoggerManager.set_log_level(__name__, level)
        logger.info(f"日志级别设置为: {args.log_level}")
    except Exception as e:
        logger.warning(f"设置日志级别失败: {e}")

    # 执行命令
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
