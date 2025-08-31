#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
支持文件日志、控制台日志、日志轮转等功能
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..config.settings import get_log_config, LogConfig


class LoggerManager:
    """日志管理器"""
    
    def __init__(self, name: str = "StockData", config: Optional[LogConfig] = None):
        """
        初始化日志管理器
        
        Args:
            name: 日志器名称
            config: 日志配置，如果为None则使用全局配置
        """
        self.name = name
        self.config = config or get_log_config()
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器"""
        # 创建日志器
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 添加控制台处理器
        if self.config.console_output:
            self._add_console_handler()
        
        # 添加文件处理器
        if self.config.file_path:
            self._add_file_handler()
        
        # 设置日志格式
        self._set_formatter()
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.level.upper()))
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """添加文件处理器"""
        file_path = Path(self.config.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用RotatingFileHandler支持日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.config.level.upper()))
        self.logger.addHandler(file_handler)
    
    def _set_formatter(self):
        """设置日志格式"""
        formatter = logging.Formatter(self.config.format)
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
    
    def get_logger(self) -> logging.Logger:
        """获取日志器"""
        return self.logger
    
    def set_level(self, level: str):
        """设置日志级别"""
        self.config.level = level.upper()
        self.logger.setLevel(getattr(logging, self.config.level.upper()))
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, self.config.level.upper()))
    
    def add_file_handler(self, file_path: str, level: Optional[str] = None):
        """添加文件处理器"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        
        if level:
            file_handler.setLevel(getattr(logging, level.upper()))
        else:
            file_handler.setLevel(getattr(logging, self.config.level.upper()))
        
        formatter = logging.Formatter(self.config.format)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def remove_file_handler(self, file_path: str):
        """移除指定的文件处理器"""
        file_path = Path(file_path).resolve()
        handlers_to_remove = []
        
        for handler in self.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                if Path(handler.baseFilename).resolve() == file_path:
                    handlers_to_remove.append(handler)
        
        for handler in handlers_to_remove:
            self.logger.removeHandler(handler)
            handler.close()


class TaskLogger:
    """任务专用日志器"""
    
    def __init__(self, task_name: str, config: Optional[LogConfig] = None):
        """
        初始化任务日志器
        
        Args:
            task_name: 任务名称
            config: 日志配置
        """
        self.task_name = task_name
        self.logger_manager = LoggerManager(f"Task.{task_name}", config)
        self.logger = self.logger_manager.get_logger()
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(f"[{self.task_name}] {message}", **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(f"[{self.task_name}] {message}", **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(f"[{self.task_name}] {message}", **kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(f"[{self.task_name}] {message}", **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self.logger.critical(f"[{self.task_name}] {message}", **kwargs)
    
    def exception(self, message: str, **kwargs):
        """记录异常日志"""
        self.logger.exception(f"[{self.task_name}] {message}", **kwargs)


class PerformanceLogger:
    """性能监控日志器"""
    
    def __init__(self, name: str = "Performance", config: Optional[LogConfig] = None):
        """
        初始化性能日志器
        
        Args:
            name: 日志器名称
            config: 日志配置
        """
        self.name = name
        self.logger_manager = LoggerManager(name, config)
        self.logger = self.logger_manager.get_logger()
        self.start_times: Dict[str, datetime] = {}
    
    def start_timer(self, task_name: str):
        """开始计时"""
        self.start_times[task_name] = datetime.now()
        self.logger.info(f"开始执行任务: {task_name}")
    
    def end_timer(self, task_name: str, extra_info: Optional[Dict[str, Any]] = None):
        """结束计时并记录执行时间"""
        if task_name not in self.start_times:
            self.logger.warning(f"任务 {task_name} 未找到开始时间")
            return
        
        end_time = datetime.now()
        duration = (end_time - self.start_times[task_name]).total_seconds()
        
        log_message = f"任务 {task_name} 执行完成，耗时: {duration:.3f}秒"
        if extra_info:
            log_message += f"，额外信息: {extra_info}"
        
        self.logger.info(log_message)
        del self.start_times[task_name]
    
    def log_performance(self, task_name: str, duration: float, **kwargs):
        """记录性能数据"""
        log_message = f"任务 {task_name} 性能数据: 耗时 {duration:.3f}秒"
        if kwargs:
            log_message += f"，其他指标: {kwargs}"
        self.logger.info(log_message)


# 全局日志管理器实例
logger_manager = LoggerManager()


def get_logger(name: str = "StockData") -> logging.Logger:
    """获取日志器"""
    if name == "StockData":
        return logger_manager.get_logger()
    else:
        return LoggerManager(name).get_logger()


def get_task_logger(task_name: str) -> TaskLogger:
    """获取任务日志器"""
    return TaskLogger(task_name)


def get_performance_logger(name: str = "Performance") -> PerformanceLogger:
    """获取性能日志器"""
    return PerformanceLogger(name)


def set_log_level(level: str):
    """设置全局日志级别"""
    logger_manager.set_level(level)


def add_file_handler(file_path: str, level: Optional[str] = None):
    """添加文件处理器"""
    logger_manager.add_file_handler(file_path, level)


def remove_file_handler(file_path: str):
    """移除文件处理器"""
    logger_manager.remove_file_handler(file_path)
