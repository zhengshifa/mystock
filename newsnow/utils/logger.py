"""日志配置模块"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from .config import get_config


def setup_logger(log_file: Optional[str] = None) -> None:
    """设置日志配置"""
    config = get_config()
    
    # 移除默认处理器
    logger.remove()
    
    # 获取日志配置
    log_level = config.get("LOG_LEVEL", "INFO")
    log_file_path = log_file or config.get("LOG_FILE", "logs/newsnow.log")
    log_rotation = config.get("LOG_ROTATION", "1 day")
    log_retention = config.get("LOG_RETENTION", "30 days")
    
    # 控制台日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # 文件日志格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 添加文件处理器
    if log_file_path:
        # 确保日志目录存在
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file_path,
            format=file_format,
            level=log_level,
            rotation=log_rotation,
            retention=log_retention,
            compression="zip",
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
    
    # 设置第三方库的日志级别
    import logging
    
    # 设置httpx日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # 设置pymongo日志级别
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    
    # 设置apscheduler日志级别
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    
    logger.info(f"日志系统初始化完成，级别: {log_level}")
    if log_file_path:
        logger.info(f"日志文件: {Path(log_file_path).absolute()}")


def get_logger(name: str = None):
    """获取日志器"""
    if name:
        return logger.bind(name=name)
    return logger


# 便捷函数
def debug(message: str, **kwargs) -> None:
    """调试日志"""
    logger.debug(message, **kwargs)


def info(message: str, **kwargs) -> None:
    """信息日志"""
    logger.info(message, **kwargs)


def success(message: str, **kwargs) -> None:
    """成功日志"""
    logger.success(message, **kwargs)


def warning(message: str, **kwargs) -> None:
    """警告日志"""
    logger.warning(message, **kwargs)


def error(message: str, **kwargs) -> None:
    """错误日志"""
    logger.error(message, **kwargs)


def critical(message: str, **kwargs) -> None:
    """严重错误日志"""
    logger.critical(message, **kwargs)


def exception(message: str, **kwargs) -> None:
    """异常日志"""
    logger.exception(message, **kwargs)