"""
模块名称: batch_processor
功能描述: 批量文档处理工具，支持多线程并发处理和进度监控
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path
import time
from dataclasses import dataclass
import json

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)

from ..parsers.document_processor import DocumentProcessor, UnifiedParseResult
from .performance_monitor import get_performance_monitor, ProcessingContext


@dataclass
class BatchProcessingResult:
    """批量处理结果"""
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    skipped_files: int
    processing_time: float
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class ProgressCallback:
    """进度回调接口"""
    
    def on_start(self, total_files: int):
        """处理开始"""
        pass
    
    def on_file_start(self, file_path: str, current: int, total: int):
        """文件处理开始"""
        pass
    
    def on_file_complete(self, file_path: str, success: bool, current: int, total: int):
        """文件处理完成"""
        pass
    
    def on_complete(self, result: BatchProcessingResult):
        """处理完成"""
        pass


class ConsoleProgressCallback(ProgressCallback):
    """控制台进度回调"""
    
    def __init__(self, show_details: bool = True):
        self.show_details = show_details
        self.start_time = None
    
    def on_start(self, total_files: int):
        self.start_time = time.time()
        print(f"开始批量处理 {total_files} 个文件...")
    
    def on_file_start(self, file_path: str, current: int, total: int):
        if self.show_details:
            print(f"[{current}/{total}] 处理: {Path(file_path).name}")
    
    def on_file_complete(self, file_path: str, success: bool, current: int, total: int):
        if self.show_details:
            status = "✓" if success else "✗"
            print(f"[{current}/{total}] {status} {Path(file_path).name}")
        else:
            # 简单进度条
            progress = current / total * 100
            print(f"\r进度: {progress:.1f}% ({current}/{total})", end="", flush=True)
    
    def on_complete(self, result: BatchProcessingResult):
        if not self.show_details:
            print()  # 换行
        
        elapsed = time.time() - self.start_time
        print(f"\n批量处理完成!")
        print(f"总文件数: {result.total_files}")
        print(f"成功处理: {result.successful_files}")
        print(f"处理失败: {result.failed_files}")
        print(f"跳过文件: {result.skipped_files}")
        print(f"总耗时: {elapsed:.2f}秒")
        print(f"平均耗时: {elapsed/result.processed_files:.2f}秒/文件" if result.processed_files > 0 else "")


class BatchProcessor:
    """批量文档处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化批量处理器
        
        Args:
            config (dict, optional): 配置参数
        """
        self.config = config or {}
        self.logger = logger
        
        # 处理器配置
        self.max_workers = self.config.get('max_workers', 4)
        self.continue_on_error = self.config.get('continue_on_error', True)
        self.skip_existing = self.config.get('skip_existing', False)
        self.output_format = self.config.get('output_format', 'markdown')
        
        # 文件过滤配置
        self.include_patterns = self.config.get('include_patterns', ['*'])
        self.exclude_patterns = self.config.get('exclude_patterns', [])
        self.max_file_size = self.config.get('max_file_size', None)
        self.min_file_size = self.config.get('min_file_size', 0)
        
        # 初始化文档处理器
        processor_config = self.config.get('processor_config', {})
        self.document_processor = DocumentProcessor(processor_config)
        
        # 性能监控
        self.performance_monitor = get_performance_monitor()
        
        # 线程锁
        self._lock = threading.Lock()
        self._processed_count = 0
    
    def process_files(self, 
                     file_paths: List[str], 
                     output_dir: Optional[str] = None,
                     progress_callback: Optional[ProgressCallback] = None) -> BatchProcessingResult:
        """
        批量处理文件
        
        Args:
            file_paths (list): 文件路径列表
            output_dir (str, optional): 输出目录
            progress_callback (ProgressCallback, optional): 进度回调
            
        Returns:
            BatchProcessingResult: 处理结果
        """
        start_time = time.time()
        
        # 过滤文件
        filtered_files = self._filter_files(file_paths)
        total_files = len(filtered_files)
        
        if total_files == 0:
            self.logger.warning("没有找到需要处理的文件")
            return BatchProcessingResult(
                total_files=0, processed_files=0, successful_files=0,
                failed_files=0, skipped_files=0, processing_time=0.0,
                results=[], errors=[]
            )
        
        # 创建输出目录
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 初始化结果
        results = []
        errors = []
        successful_count = 0
        failed_count = 0
        skipped_count = 0
        
        # 重置计数器
        self._processed_count = 0
        
        # 进度回调
        if progress_callback:
            progress_callback.on_start(total_files)
        
        # 多线程处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_file = {
                executor.submit(self._process_single_file, file_path, output_dir): file_path
                for file_path in filtered_files
            }
            
            # 处理结果
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                
                with self._lock:
                    self._processed_count += 1
                    current_count = self._processed_count
                
                try:
                    result = future.result()
                    
                    if result['status'] == 'success':
                        successful_count += 1
                        results.append(result)
                    elif result['status'] == 'skipped':
                        skipped_count += 1
                    else:
                        failed_count += 1
                        errors.append(result)
                    
                    # 进度回调
                    if progress_callback:
                        progress_callback.on_file_complete(
                            file_path, result['status'] == 'success', 
                            current_count, total_files
                        )
                
                except Exception as e:
                    failed_count += 1
                    error_result = {
                        'file_path': file_path,
                        'status': 'error',
                        'error': str(e),
                        'timestamp': time.time()
                    }
                    errors.append(error_result)
                    
                    self.logger.error(f"处理文件失败: {file_path}, 错误: {e}")
                    
                    # 进度回调
                    if progress_callback:
                        progress_callback.on_file_complete(
                            file_path, False, current_count, total_files
                        )
                    
                    if not self.continue_on_error:
                        self.logger.error("遇到错误，停止批量处理")
                        break
        
        # 创建结果
        processing_time = time.time() - start_time
        batch_result = BatchProcessingResult(
            total_files=total_files,
            processed_files=successful_count + failed_count,
            successful_files=successful_count,
            failed_files=failed_count,
            skipped_files=skipped_count,
            processing_time=processing_time,
            results=results,
            errors=errors
        )
        
        # 进度回调
        if progress_callback:
            progress_callback.on_complete(batch_result)
        
        return batch_result
    
    def process_directory(self, 
                         input_dir: str, 
                         output_dir: Optional[str] = None,
                         recursive: bool = True,
                         progress_callback: Optional[ProgressCallback] = None) -> BatchProcessingResult:
        """
        批量处理目录中的文件
        
        Args:
            input_dir (str): 输入目录
            output_dir (str, optional): 输出目录
            recursive (bool): 是否递归处理子目录
            progress_callback (ProgressCallback, optional): 进度回调
            
        Returns:
            BatchProcessingResult: 处理结果
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        # 收集文件
        file_paths = []
        if recursive:
            file_paths = [str(p) for p in input_path.rglob('*') if p.is_file()]
        else:
            file_paths = [str(p) for p in input_path.iterdir() if p.is_file()]
        
        return self.process_files(file_paths, output_dir, progress_callback)
    
    def _process_single_file(self, file_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """处理单个文件"""
        try:
            file_path_obj = Path(file_path)
            
            # 检查文件是否存在
            if not file_path_obj.exists():
                return {
                    'file_path': file_path,
                    'status': 'error',
                    'error': 'File not found',
                    'timestamp': time.time()
                }
            
            # 检查是否跳过已存在的输出文件
            if output_dir and self.skip_existing:
                output_file = Path(output_dir) / f"{file_path_obj.stem}.md"
                if output_file.exists():
                    return {
                        'file_path': file_path,
                        'status': 'skipped',
                        'reason': 'Output file already exists',
                        'timestamp': time.time()
                    }
            
            # 获取文件信息
            file_size = file_path_obj.stat().st_size
            file_type = file_path_obj.suffix.lower()
            
            # 性能监控
            with ProcessingContext(file_path, file_size, file_type, 'batch_processor'):
                # 处理文件
                result = self.document_processor.parse(file_path)
                
                # 保存结果
                output_file_path = None
                if output_dir:
                    output_file_path = self._save_result(result, file_path_obj, output_dir)
                
                return {
                    'file_path': file_path,
                    'status': 'success',
                    'output_file': output_file_path,
                    'file_size': file_size,
                    'file_type': file_type,
                    'parser_type': result.document_type.value,
                    'text_length': len(result.text_content),
                    'metadata': result.metadata,
                    'timestamp': time.time()
                }
        
        except Exception as e:
            return {
                'file_path': file_path,
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _save_result(self, result: UnifiedParseResult, input_file: Path, output_dir: str) -> str:
        """保存处理结果"""
        output_dir_path = Path(output_dir)
        
        if self.output_format == 'markdown':
            output_file = output_dir_path / f"{input_file.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.text_content)
        
        elif self.output_format == 'json':
            output_file = output_dir_path / f"{input_file.stem}.json"
            data = {
                'text_content': result.text_content,
                'metadata': result.metadata,
                'structured_data': result.structured_data,
                'structure_info': result.structure_info
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        else:
            raise ValueError(f"不支持的输出格式: {self.output_format}")
        
        return str(output_file)
    
    def _filter_files(self, file_paths: List[str]) -> List[str]:
        """过滤文件列表"""
        filtered = []
        
        for file_path in file_paths:
            file_path_obj = Path(file_path)
            
            # 检查文件是否存在
            if not file_path_obj.exists():
                continue
            
            # 检查是否为文件
            if not file_path_obj.is_file():
                continue
            
            # 检查文件大小
            file_size = file_path_obj.stat().st_size
            if self.max_file_size and file_size > self.max_file_size:
                self.logger.debug(f"跳过大文件: {file_path} ({file_size} bytes)")
                continue
            
            if file_size < self.min_file_size:
                self.logger.debug(f"跳过小文件: {file_path} ({file_size} bytes)")
                continue
            
            # 检查文件格式支持
            if not self.document_processor.is_supported_format(file_path):
                self.logger.debug(f"跳过不支持的格式: {file_path}")
                continue
            
            # 检查包含模式
            if self.include_patterns:
                included = any(file_path_obj.match(pattern) for pattern in self.include_patterns)
                if not included:
                    continue
            
            # 检查排除模式
            if self.exclude_patterns:
                excluded = any(file_path_obj.match(pattern) for pattern in self.exclude_patterns)
                if excluded:
                    continue
            
            filtered.append(file_path)
        
        return filtered
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.performance_monitor.get_current_stats()
    
    def export_results(self, results: List[Dict[str, Any]], output_path: str):
        """导出处理结果"""
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.endswith('.json'):
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        elif output_path.endswith('.csv'):
            import csv
            
            if results:
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
        
        else:
            raise ValueError(f"不支持的导出格式: {output_path}")
        
        self.logger.info(f"处理结果已导出到: {output_path}")


def create_batch_processor(config: Optional[Dict[str, Any]] = None) -> BatchProcessor:
    """创建批量处理器实例"""
    return BatchProcessor(config)
