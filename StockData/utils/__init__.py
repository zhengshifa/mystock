#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
提供各种工具函数和类
"""

from .database import DatabaseManager
from .gm_client import GMClient
from .mongodb_client import MongoDBClient
from .log_manager import LogManager

# 导出主要工具类
__all__ = [
    'DatabaseManager',
    'GMClient', 
    'MongoDBClient',
    'LogManager'
]

# 创建全局实例
db_manager = DatabaseManager()
gm_client = GMClient()
mongodb_client = MongoDBClient()
log_manager = LogManager()

# 向后兼容的别名
def get_logger(name: str):
    """获取logger的便捷函数"""
    return log_manager.get_logger(name)