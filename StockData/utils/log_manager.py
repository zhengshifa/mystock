#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器
整合日志配置和日志管理功能
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any

# 修复配置导入
try:
    from config import config
except ImportError:
    # 如果配置模块导入失败，使用默认配置
    class DefaultLogConfig:
        level = "INFO"
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_dir = "logs"
        max_file_size = 10 * 1024 * 1024  # 10MB
        backup_count = 5
    
    config = DefaultLogConfig()
    config.logging = DefaultLogConfig()


class LogManager:
    """日志管理器类"""
    
    def __init__(self):
        """初始化日志管理器"""
        self.log_dir = Path(config.logging.log_dir)
        self.log_format = config.logging.format
        self.max_file_size = config.logging.max_file_size
        self.backup_count = config.logging.backup_count
        
        # 确保日志目录存在
        self.log_dir.mkdir(exist_ok=True)
        
        # 已创建的logger缓存
        self._loggers: Dict[str, logging.Logger] = {}
        
        # 设置项目基础日志配置
        self._setup_project_logging()
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取logger，如果不存在则创建新的
        
        Args:
            name: logger名称
            
        Returns:
            logger对象
        """
        if name not in self._loggers:
            self._loggers[name] = self._create_logger(name)
        return self._loggers[name]
    
    def _create_logger(self, name: str) -> logging.Logger:
        """
        创建新的logger
        
        Args:
            name: logger名称
            
        Returns:
            新创建的logger对象
        """
        logger = logging.getLogger(name)
        
        # 如果logger已经有处理器，直接返回
        if logger.handlers:
            return logger
        
        # 设置日志级别
        log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # 创建格式化器
        formatter = logging.Formatter(self.log_format)
        
        # 根据logger名称决定输出方式
        if name == "root" or name == "__main__":
            # 主程序logger：控制台 + 文件 + 错误日志
            self._add_console_handler(logger, formatter, log_level)
            self._add_file_handler(logger, name, formatter, log_level)
            self._add_error_file_handler(logger, name, formatter)
        elif name.startswith("utils."):
            # 工具模块：文件 + 错误日志
            self._add_file_handler(logger, name, formatter, log_level)
            self._add_error_file_handler(logger, name, formatter)
        else:
            # 其他模块：仅文件输出
            self._add_file_handler(logger, name, formatter, log_level)
        
        return logger
    
    def _add_console_handler(self, logger: logging.Logger, formatter: logging.Formatter, level: int):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger, name: str, formatter: logging.Formatter, level: int):
        """添加文件处理器"""
        log_file = self.log_dir / f"{name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def _add_error_file_handler(self, logger: logging.Logger, name: str, formatter: logging.Formatter):
        """添加错误日志文件处理器"""
        error_log_file = self.log_dir / f"{name}_error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    def _setup_project_logging(self):
        """设置项目的基础日志配置"""
        # 设置根logger
        root_logger = self.get_logger("root")
        
        # 设置核心模块的logger
        core_modules = [
            "utils.gm_client",
            "utils.database", 
            "utils.mongodb_client",
            "src.current_data",
            "src.scheduler",
            "src.fundamentals_data"
        ]
        
        for module in core_modules:
            self.get_logger(module)
    
    def cleanup_old_logs(self, days: int = 7, remove_empty: bool = True, max_total_size_mb: int = 100):
        """
        清理日志文件
        
        Args:
            days: 保留天数
            remove_empty: 是否删除空文件
            max_total_size_mb: 日志目录最大总大小(MB)
        """
        import time
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0
        total_size = 0
        
        # 获取所有日志文件并按修改时间排序
        log_files = list(self.log_dir.glob("*.log*"))
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        for log_file in log_files:
            file_stat = log_file.stat()
            file_size = file_stat.st_size
            
            # 删除空文件
            if remove_empty and file_size == 0:
                try:
                    log_file.unlink()
                    print(f"已删除空日志文件: {log_file.name}")
                    deleted_count += 1
                    continue
                except Exception as e:
                    print(f"删除空日志文件失败 {log_file.name}: {e}")
            
            # 删除过期文件
            if file_stat.st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    print(f"已删除过期日志文件: {log_file.name} (大小: {file_size/1024:.1f}KB)")
                    deleted_count += 1
                    continue
                except Exception as e:
                    print(f"删除过期日志文件失败 {log_file.name}: {e}")
            
            total_size += file_size
        
        # 如果总大小超过限制，删除最旧的文件
        if total_size > max_total_size_mb * 1024 * 1024:
            print(f"日志目录总大小 {total_size/1024/1024:.1f}MB 超过限制 {max_total_size_mb}MB，清理最旧文件...")
            remaining_files = [f for f in log_files if f.exists()]
            remaining_files.sort(key=lambda f: f.stat().st_mtime)
            
            current_size = sum(f.stat().st_size for f in remaining_files)
            for old_file in remaining_files:
                if current_size <= max_total_size_mb * 1024 * 1024:
                    break
                try:
                    file_size = old_file.stat().st_size
                    old_file.unlink()
                    current_size -= file_size
                    print(f"已删除旧日志文件: {old_file.name} (大小: {file_size/1024:.1f}KB)")
                    deleted_count += 1
                except Exception as e:
                    print(f"删除旧日志文件失败 {old_file.name}: {e}")
        
        print(f"日志清理完成，共删除 {deleted_count} 个文件")
        return deleted_count
    
    def get_log_summary(self) -> Dict[str, Any]:
        """
        获取日志摘要信息
        
        Returns:
            日志摘要字典
        """
        log_files = list(self.log_dir.glob("*.log*"))
        total_size = sum(f.stat().st_size for f in log_files)
        
        return {
            "log_dir": str(self.log_dir),
            "total_files": len(log_files),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "max_file_size_mb": round(self.max_file_size / 1024 / 1024, 2),
            "backup_count": self.backup_count,
            "active_loggers": list(self._loggers.keys())
        }


def setup_logging(level: str = "INFO", log_dir: str = "logs") -> None:
    """设置日志系统
    
    Args:
        level: 日志级别
        log_dir: 日志目录
    """
    try:
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # 设置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 创建文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 创建错误日志处理器
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "error.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # 创建格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # 设置格式化器
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        # 添加处理器到根日志器
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        
        # 设置一些第三方库的日志级别
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        
        print(f"✅ 日志系统初始化成功，级别: {level}")
        
    except Exception as e:
        print(f"❌ 日志系统初始化失败: {e}")
        # 使用基础日志配置
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )


# 创建全局日志管理器实例
log_manager = LogManager()

# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取logger的便捷函数
    
    Args:
        name: logger名称
        
    Returns:
        logger对象
    """
    return log_manager.get_logger(name)
