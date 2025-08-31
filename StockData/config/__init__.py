#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块初始化文件
提供统一的配置访问接口
"""

from .config_manager import ConfigManager

# 创建全局配置管理器实例
config_manager = ConfigManager()

# 获取配置实例
config = config_manager.get_config()

# 导出主要配置对象
__all__ = ['config', 'config_manager', 'ConfigManager']