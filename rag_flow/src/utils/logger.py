"""
模块名称: logger
功能描述: 日志管理器，提供统一的日志配置和管理功能
创建日期: 2025-06-14
作者: Sniperz
版本: v1.0.0
"""

import logging
import os
import sys
from typing import Optional


class SZ_LoggerManager:
    """
    日志管理器类
    
    提供统一的日志配置和管理功能，支持控制台和文件双重输出。
    """
    
    @staticmethod
    def setup_logger(
        logger_name: str = __name__, 
        log_file: str = "app.log", 
        level: int = logging.INFO,
        log_dir: str = "logs"
    ) -> logging.Logger:
        """
        设置并配置日志记录器
        
        Args:
            logger_name (str): 日志记录器名称
            log_file (str): 日志文件名
            level (int): 日志级别
            log_dir (str): 日志目录
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        # 创建一个日志记录器
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

        # 检查是否已经配置过处理器，避免重复添加
        if logger.hasHandlers():
            return logger

        # 创建日志目录（如果不存在）
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 创建一个控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)  # 控制台输出 DEBUG 及以上级别的日志

        # 创建一个文件处理器
        file_handler = logging.FileHandler(os.path.join(log_dir, log_file), encoding='utf-8')
        file_handler.setLevel(logging.ERROR)  # 文件输出 ERROR 及以上级别的日志

        # 定义日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 将处理器添加到日志记录器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger
    
    @staticmethod
    def get_logger(logger_name: str) -> logging.Logger:
        """
        获取已配置的日志记录器
        
        Args:
            logger_name (str): 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        return logging.getLogger(logger_name)
    
    @staticmethod
    def set_log_level(logger_name: str, level: int) -> None:
        """
        设置日志记录器的日志级别
        
        Args:
            logger_name (str): 日志记录器名称
            level (int): 日志级别
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
