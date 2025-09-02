#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统

提供统一的日志管理功能:
- 多级别日志记录
- 文件和控制台输出
- 日志轮转和压缩
- 结构化日志格式
- 性能监控日志
- 异步日志写入
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty
import time

from loguru import logger as loguru_logger
import structlog


class LogLevel(Enum):
    """日志级别枚举"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """日志格式枚举"""
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    STRUCTURED = "structured"


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    format_type: str = "detailed"
    console_output: bool = True
    file_output: bool = True
    log_dir: str = "logs"
    max_file_size: str = "10 MB"
    retention_days: int = 30
    compression: str = "gz"
    async_logging: bool = True
    structured_logging: bool = True
    performance_logging: bool = True
    error_tracking: bool = True


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    level: str
    message: str
    module: str
    function: str
    line: int
    thread_id: int
    process_id: int
    extra: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class LoggerManager:
    """日志管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[LogConfig] = None):
        if hasattr(self, '_initialized'):
            return
        
        self.config = config or LogConfig()
        self.loggers = {}
        self.log_queue = Queue(maxsize=10000) if getattr(self.config, 'async_logging', False) else None
        self.thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Logger")
        self.async_writer_running = False
        
        # 创建日志目录
        self.log_dir = Path(getattr(self.config, 'log_dir', 'logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化结构化日志
        if self.config.structured_logging:
            self._setup_structured_logging()
        
        # 设置默认日志器
        self._setup_default_logger()
        
        # 启动异步写入器
        if self.config.async_logging:
            self._start_async_writer()
        
        self._initialized = True
    
    def _setup_structured_logging(self):
        """设置结构化日志"""
        try:
            # 配置structlog
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
            
        except Exception as e:
            print(f"设置结构化日志失败: {e}")
    
    def _setup_default_logger(self):
        """设置默认日志器"""
        try:
            # 移除默认处理器
            loguru_logger.remove()
            
            # 控制台输出
            if self.config.console_output:
                console_format = self._get_log_format("console")
                loguru_logger.add(
                    sys.stderr,
                    format=console_format,
                    level=self.config.level,
                    colorize=True,
                    backtrace=True,
                    diagnose=True
                )
            
            # 文件输出
            if self.config.file_output:
                # 主日志文件
                main_log_file = self.log_dir / "stock_data.log"
                file_format = self._get_log_format("file")
                
                loguru_logger.add(
                    str(main_log_file),
                    format=file_format,
                    level=self.config.level,
                    rotation=self.config.max_file_size,
                    retention=f"{self.config.retention_days} days",
                    compression=self.config.compression,
                    backtrace=True,
                    diagnose=True,
                    enqueue=self.config.async_logging
                )
                
                # 错误日志文件
                error_log_file = self.log_dir / "errors.log"
                loguru_logger.add(
                    str(error_log_file),
                    format=file_format,
                    level="ERROR",
                    rotation=self.config.max_file_size,
                    retention=f"{self.config.retention_days} days",
                    compression=self.config.compression,
                    backtrace=True,
                    diagnose=True,
                    enqueue=self.config.async_logging
                )
                
                # 性能日志文件
                if self.config.performance_logging:
                    perf_log_file = self.log_dir / "performance.log"
                    loguru_logger.add(
                        str(perf_log_file),
                        format=file_format,
                        level="INFO",
                        rotation=self.config.max_file_size,
                        retention=f"{self.config.retention_days} days",
                        compression=self.config.compression,
                        filter=lambda record: "PERF" in record["extra"],
                        enqueue=self.config.async_logging
                    )
            
        except Exception as e:
            print(f"设置默认日志器失败: {e}")
    
    def _get_log_format(self, output_type: str) -> str:
        """获取日志格式"""
        formats = {
            "simple": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            "detailed": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            "console": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            "file": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process.id}:{thread.id} | {name}:{function}:{line} | {message} | {extra}",
            "json": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message} | {extra}"
        }
        
        if output_type == "console":
            return formats.get("console", formats["detailed"])
        else:
            return formats.get(self.config.format_type, formats["detailed"])
    
    def _start_async_writer(self):
        """启动异步日志写入器"""
        if self.async_writer_running:
            return
        
        self.async_writer_running = True
        self.thread_pool.submit(self._async_log_writer)
    
    def _async_log_writer(self):
        """异步日志写入器"""
        while self.async_writer_running:
            try:
                # 从队列获取日志条目
                try:
                    log_entry = self.log_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # 写入日志
                self._write_log_entry(log_entry)
                self.log_queue.task_done()
                
            except Exception as e:
                print(f"异步日志写入错误: {e}")
    
    def _write_log_entry(self, log_entry: LogEntry):
        """写入日志条目"""
        try:
            # 根据级别选择合适的日志方法
            level = log_entry.level.upper()
            message = log_entry.message
            extra = log_entry.extra or {}
            
            if level == "TRACE":
                loguru_logger.trace(message, **extra)
            elif level == "DEBUG":
                loguru_logger.debug(message, **extra)
            elif level == "INFO":
                loguru_logger.info(message, **extra)
            elif level == "SUCCESS":
                loguru_logger.success(message, **extra)
            elif level == "WARNING":
                loguru_logger.warning(message, **extra)
            elif level == "ERROR":
                loguru_logger.error(message, **extra)
            elif level == "CRITICAL":
                loguru_logger.critical(message, **extra)
            
        except Exception as e:
            print(f"写入日志条目失败: {e}")
    
    def get_logger(self, name: str) -> 'Logger':
        """获取日志器"""
        if name not in self.loggers:
            self.loggers[name] = Logger(name, self)
        return self.loggers[name]
    
    def log(self, level: str, message: str, **kwargs):
        """记录日志"""
        try:
            # 获取调用信息
            import inspect
            frame = inspect.currentframe().f_back
            
            log_entry = LogEntry(
                timestamp=datetime.now().isoformat(),
                level=level.upper(),
                message=message,
                module=frame.f_globals.get('__name__', 'unknown'),
                function=frame.f_code.co_name,
                line=frame.f_lineno,
                thread_id=threading.get_ident(),
                process_id=os.getpid(),
                extra=kwargs
            )
            
            if self.config.async_logging and self.log_queue:
                try:
                    self.log_queue.put_nowait(log_entry)
                except:
                    # 队列满时直接写入
                    self._write_log_entry(log_entry)
            else:
                self._write_log_entry(log_entry)
                
        except Exception as e:
            print(f"记录日志失败: {e}")
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """记录性能日志"""
        if not self.config.performance_logging:
            return
        
        perf_data = {
            'PERF': True,
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        self.log("INFO", f"Performance: {operation} took {duration:.3f}s", **perf_data)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """记录错误日志"""
        if not self.config.error_tracking:
            return
        
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.log("ERROR", f"Error occurred: {error}", **error_data)
    
    def shutdown(self):
        """关闭日志管理器"""
        try:
            # 停止异步写入器
            if self.async_writer_running:
                self.async_writer_running = False
                
                # 等待队列清空
                if self.log_queue:
                    self.log_queue.join()
            
            # 关闭线程池
            self.thread_pool.shutdown(wait=True)
            
            # 关闭loguru
            loguru_logger.remove()
            
        except Exception as e:
            print(f"关闭日志管理器失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            stats = {
                'config': asdict(self.config),
                'loggers_count': len(self.loggers),
                'queue_size': self.log_queue.qsize() if self.log_queue else 0,
                'async_writer_running': self.async_writer_running,
                'log_files': []
            }
            
            # 获取日志文件信息
            if self.log_dir.exists():
                for log_file in self.log_dir.glob('*.log*'):
                    file_stats = log_file.stat()
                    stats['log_files'].append({
                        'name': log_file.name,
                        'size': file_stats.st_size,
                        'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    })
            
            return stats
            
        except Exception as e:
            print(f"获取日志统计信息失败: {e}")
            return {}


class Logger:
    """日志器包装类"""
    
    def __init__(self, name: str, manager: LoggerManager):
        self.name = name
        self.manager = manager
        self._context = {}
    
    def bind(self, **kwargs) -> 'Logger':
        """绑定上下文"""
        new_logger = Logger(self.name, self.manager)
        new_logger._context = {**self._context, **kwargs}
        return new_logger
    
    def trace(self, message: str, **kwargs):
        """记录TRACE级别日志"""
        self._log("TRACE", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self._log("INFO", message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """记录SUCCESS级别日志"""
        self._log("SUCCESS", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        self._log("CRITICAL", message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """记录异常日志"""
        import traceback
        kwargs['traceback'] = traceback.format_exc()
        self._log("ERROR", message, **kwargs)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """记录性能日志"""
        self.manager.log_performance(operation, duration, logger=self.name, **kwargs)
    
    def _log(self, level: str, message: str, **kwargs):
        """内部日志记录方法"""
        # 合并上下文和参数
        log_kwargs = {**self._context, **kwargs, 'logger': self.name}
        self.manager.log(level, message, **log_kwargs)


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, logger: Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
        self.context = {}
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.performance(self.operation, duration, **self.context)
    
    def add_context(self, **kwargs):
        """添加上下文信息"""
        self.context.update(kwargs)
        return self


# 全局日志管理器实例
_logger_manager = None


def setup_logger(config: Union[LogConfig, Dict[str, Any]]) -> Logger:
    """
    设置日志系统
    
    Args:
        config: 日志配置
        
    Returns:
        配置好的日志器
    """
    global _logger_manager
    
    # 如果传入的是字典，创建一个简单的配置对象
    if isinstance(config, dict):
        # 创建一个简单的配置对象
        class SimpleLogConfig:
            def __init__(self, config_dict):
                self.level = config_dict.get('level', 'INFO')
                self.log_dir = config_dict.get('log_dir', 'logs')
                self.async_logging = config_dict.get('async_logging', False)
                self.structured_logging = config_dict.get('structured_logging', False)
                self.console_output = config_dict.get('console_output', True)
                self.file_output = config_dict.get('file_output', True)
                self.max_file_size = config_dict.get('max_file_size', '10MB')
                self.retention_days = config_dict.get('retention_days', 30)
                self.compression = config_dict.get('compression', 'zip')
                self.format_type = config_dict.get('format_type', 'detailed')
                self.performance_logging = config_dict.get('performance_logging', False)
                self.error_tracking = config_dict.get('error_tracking', True)
        
        config = SimpleLogConfig(config)
    
    _logger_manager = LoggerManager(config)
    return _logger_manager.get_logger("stock_data")


def get_logger(name: str = "stock_data") -> Logger:
    """获取日志器"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager.get_logger(name)


def performance_log(operation: str):
    """性能日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            with PerformanceLogger(logger, operation) as perf:
                perf.add_context(
                    function=func.__name__,
                    args_count=len(args),
                    kwargs_count=len(kwargs)
                )
                return func(*args, **kwargs)
        return wrapper
    return decorator


# 便捷函数
def trace(message: str, **kwargs):
    """记录TRACE日志"""
    get_logger().trace(message, **kwargs)


def debug(message: str, **kwargs):
    """记录DEBUG日志"""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs):
    """记录INFO日志"""
    get_logger().info(message, **kwargs)


def success(message: str, **kwargs):
    """记录SUCCESS日志"""
    get_logger().success(message, **kwargs)


def warning(message: str, **kwargs):
    """记录WARNING日志"""
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs):
    """记录ERROR日志"""
    get_logger().error(message, **kwargs)


def critical(message: str, **kwargs):
    """记录CRITICAL日志"""
    get_logger().critical(message, **kwargs)