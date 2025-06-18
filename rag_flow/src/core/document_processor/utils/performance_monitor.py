"""
模块名称: performance_monitor
功能描述: 性能监控工具，用于监控文档处理性能和统计信息
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import logging
from pathlib import Path


@dataclass
class ProcessingMetrics:
    """处理指标数据类"""
    file_path: str
    file_size: int
    file_type: str
    parser_type: str
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        """
        初始化性能监控器
        
        Args:
            max_history (int): 最大历史记录数量
        """
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history
        
        # 指标存储
        self.metrics_history: deque = deque(maxlen=max_history)
        self.current_metrics: Dict[str, Any] = {}
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'total_success': 0,
            'total_failed': 0,
            'total_processing_time': 0.0,
            'total_file_size': 0,
            'parser_stats': defaultdict(lambda: {'count': 0, 'success': 0, 'total_time': 0.0}),
            'file_type_stats': defaultdict(lambda: {'count': 0, 'success': 0, 'total_time': 0.0})
        }
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 系统监控
        self.system_monitor_enabled = True
        self.system_metrics = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_used': 0,
            'disk_usage': 0.0
        }
    
    def start_processing(self, file_path: str, file_size: int, file_type: str, parser_type: str) -> str:
        """
        开始处理监控
        
        Args:
            file_path (str): 文件路径
            file_size (int): 文件大小
            file_type (str): 文件类型
            parser_type (str): 解析器类型
            
        Returns:
            str: 处理ID
        """
        processing_id = f"{int(time.time() * 1000)}_{threading.get_ident()}"
        
        with self._lock:
            self.current_metrics[processing_id] = {
                'file_path': file_path,
                'file_size': file_size,
                'file_type': file_type,
                'parser_type': parser_type,
                'start_time': time.time(),
                'start_memory': self._get_memory_usage(),
                'start_cpu': self._get_cpu_usage()
            }
        
        self.logger.debug(f"开始监控处理: {processing_id}")
        return processing_id
    
    def end_processing(self, processing_id: str, success: bool, error_message: Optional[str] = None):
        """
        结束处理监控
        
        Args:
            processing_id (str): 处理ID
            success (bool): 是否成功
            error_message (str, optional): 错误信息
        """
        with self._lock:
            if processing_id not in self.current_metrics:
                self.logger.warning(f"未找到处理记录: {processing_id}")
                return
            
            current = self.current_metrics[processing_id]
            end_time = time.time()
            processing_time = end_time - current['start_time']
            
            # 创建指标记录
            metrics = ProcessingMetrics(
                file_path=current['file_path'],
                file_size=current['file_size'],
                file_type=current['file_type'],
                parser_type=current['parser_type'],
                processing_time=processing_time,
                success=success,
                error_message=error_message,
                memory_usage=self._get_memory_usage() - current['start_memory'],
                cpu_usage=self._get_cpu_usage(),
                timestamp=end_time
            )
            
            # 添加到历史记录
            self.metrics_history.append(metrics)
            
            # 更新统计信息
            self._update_stats(metrics)
            
            # 清理当前指标
            del self.current_metrics[processing_id]
        
        self.logger.debug(f"结束监控处理: {processing_id}, 成功: {success}, 耗时: {processing_time:.2f}s")
    
    def _update_stats(self, metrics: ProcessingMetrics):
        """更新统计信息"""
        self.stats['total_processed'] += 1
        self.stats['total_processing_time'] += metrics.processing_time
        self.stats['total_file_size'] += metrics.file_size
        
        if metrics.success:
            self.stats['total_success'] += 1
        else:
            self.stats['total_failed'] += 1
        
        # 解析器统计
        parser_stats = self.stats['parser_stats'][metrics.parser_type]
        parser_stats['count'] += 1
        parser_stats['total_time'] += metrics.processing_time
        if metrics.success:
            parser_stats['success'] += 1
        
        # 文件类型统计
        file_type_stats = self.stats['file_type_stats'][metrics.file_type]
        file_type_stats['count'] += 1
        file_type_stats['total_time'] += metrics.processing_time
        if metrics.success:
            file_type_stats['success'] += 1
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            return psutil.cpu_percent(interval=None)
        except Exception:
            return 0.0
    
    def update_system_metrics(self):
        """更新系统指标"""
        if not self.system_monitor_enabled:
            return
        
        try:
            self.system_metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            memory = psutil.virtual_memory()
            self.system_metrics['memory_percent'] = memory.percent
            self.system_metrics['memory_used'] = memory.used // 1024 // 1024  # MB
            
            disk = psutil.disk_usage('.')
            self.system_metrics['disk_usage'] = disk.percent
            
        except Exception as e:
            self.logger.error(f"系统指标更新失败: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        with self._lock:
            stats = dict(self.stats)
            
            # 计算平均值和成功率
            if stats['total_processed'] > 0:
                stats['average_processing_time'] = stats['total_processing_time'] / stats['total_processed']
                stats['success_rate'] = stats['total_success'] / stats['total_processed']
                stats['error_rate'] = stats['total_failed'] / stats['total_processed']
                stats['average_file_size'] = stats['total_file_size'] / stats['total_processed']
            else:
                stats['average_processing_time'] = 0.0
                stats['success_rate'] = 0.0
                stats['error_rate'] = 0.0
                stats['average_file_size'] = 0.0
            
            # 添加解析器统计的平均值
            for parser_type, parser_stats in stats['parser_stats'].items():
                if parser_stats['count'] > 0:
                    parser_stats['average_time'] = parser_stats['total_time'] / parser_stats['count']
                    parser_stats['success_rate'] = parser_stats['success'] / parser_stats['count']
                else:
                    parser_stats['average_time'] = 0.0
                    parser_stats['success_rate'] = 0.0
            
            # 添加文件类型统计的平均值
            for file_type, type_stats in stats['file_type_stats'].items():
                if type_stats['count'] > 0:
                    type_stats['average_time'] = type_stats['total_time'] / type_stats['count']
                    type_stats['success_rate'] = type_stats['success'] / type_stats['count']
                else:
                    type_stats['average_time'] = 0.0
                    type_stats['success_rate'] = 0.0
            
            # 添加系统指标
            stats['system_metrics'] = dict(self.system_metrics)
            
            # 添加当前处理数量
            stats['current_processing'] = len(self.current_metrics)
            
            return stats
    
    def get_recent_metrics(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的指标记录
        
        Args:
            count (int): 记录数量
            
        Returns:
            list: 指标记录列表
        """
        with self._lock:
            recent = list(self.metrics_history)[-count:]
            return [asdict(metric) for metric in recent]
    
    def get_metrics_by_time_range(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """
        获取指定时间范围的指标记录
        
        Args:
            start_time (float): 开始时间戳
            end_time (float): 结束时间戳
            
        Returns:
            list: 指标记录列表
        """
        with self._lock:
            filtered = [
                metric for metric in self.metrics_history
                if start_time <= metric.timestamp <= end_time
            ]
            return [asdict(metric) for metric in filtered]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        with self._lock:
            error_metrics = [metric for metric in self.metrics_history if not metric.success]
            
            error_summary = {
                'total_errors': len(error_metrics),
                'error_types': defaultdict(int),
                'error_by_parser': defaultdict(int),
                'error_by_file_type': defaultdict(int),
                'recent_errors': []
            }
            
            for metric in error_metrics:
                if metric.error_message:
                    error_summary['error_types'][metric.error_message] += 1
                error_summary['error_by_parser'][metric.parser_type] += 1
                error_summary['error_by_file_type'][metric.file_type] += 1
            
            # 最近的错误（最多10个）
            recent_errors = sorted(error_metrics, key=lambda x: x.timestamp, reverse=True)[:10]
            error_summary['recent_errors'] = [asdict(metric) for metric in recent_errors]
            
            return dict(error_summary)
    
    def export_metrics(self, output_path: str, format: str = 'json'):
        """
        导出指标数据
        
        Args:
            output_path (str): 输出文件路径
            format (str): 输出格式 ('json' 或 'csv')
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                data = {
                    'stats': self.get_current_stats(),
                    'metrics': self.get_recent_metrics(len(self.metrics_history)),
                    'export_time': time.time()
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                import csv
                
                metrics = self.get_recent_metrics(len(self.metrics_history))
                
                if metrics:
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
                        writer.writeheader()
                        writer.writerows(metrics)
            
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            self.logger.info(f"指标数据已导出到: {output_path}")
            
        except Exception as e:
            self.logger.error(f"指标数据导出失败: {e}")
            raise
    
    def reset_stats(self):
        """重置统计信息"""
        with self._lock:
            self.stats = {
                'total_processed': 0,
                'total_success': 0,
                'total_failed': 0,
                'total_processing_time': 0.0,
                'total_file_size': 0,
                'parser_stats': defaultdict(lambda: {'count': 0, 'success': 0, 'total_time': 0.0}),
                'file_type_stats': defaultdict(lambda: {'count': 0, 'success': 0, 'total_time': 0.0})
            }
            self.metrics_history.clear()
        
        self.logger.info("统计信息已重置")
    
    def enable_system_monitoring(self, enabled: bool = True):
        """启用/禁用系统监控"""
        self.system_monitor_enabled = enabled
        self.logger.info(f"系统监控已{'启用' if enabled else '禁用'}")


# 全局性能监控器实例
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


class ProcessingContext:
    """处理上下文管理器"""
    
    def __init__(self, file_path: str, file_size: int, file_type: str, parser_type: str):
        self.file_path = file_path
        self.file_size = file_size
        self.file_type = file_type
        self.parser_type = parser_type
        self.processing_id = None
        self.monitor = get_performance_monitor()
    
    def __enter__(self):
        self.processing_id = self.monitor.start_processing(
            self.file_path, self.file_size, self.file_type, self.parser_type
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None
        self.monitor.end_processing(self.processing_id, success, error_message)
