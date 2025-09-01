"""
日志配置模块
使用loguru进行日志管理
"""
import os
import sys
from pathlib import Path
from loguru import logger
from src.config.settings import get_settings


def setup_logger() -> None:
    """设置日志配置"""
    settings = get_settings()
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 创建日志目录
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 控制台日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 文件日志格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 添加控制台日志处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.log_level,
        colorize=True
    )
    
    # 添加文件日志处理器
    logger.add(
        settings.log_file,
        format=file_format,
        level=settings.log_level,
        rotation="1 day",      # 每天轮转
        retention="30 days",   # 保留30天
        compression="zip",     # 压缩旧日志
        encoding="utf-8"
    )
    
    # 设置全局日志级别
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {settings.log_level}")
    logger.info(f"日志文件: {settings.log_file}")


def get_logger(name: str = None):
    """获取日志记录器"""
    if name:
        return logger.bind(name=name)
    return logger
