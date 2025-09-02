#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

提供配置管理功能:
- 配置加载器 (ConfigLoader)
- 配置验证器 (ConfigValidator)
- 环境配置管理 (EnvironmentConfig)
- 动态配置更新 (DynamicConfig)
"""

from .config_loader import (
    ConfigLoader,
    ConfigFormat,
    ConfigSource
)

from .config_validator import (
    ConfigValidator,
    ValidationRule,
    ValidationError as ConfigValidationError
)

from .environment_config import (
    EnvironmentConfig,
    Environment,
    get_environment,
    is_development,
    is_production,
    is_testing
)

from .dynamic_config import (
    DynamicConfig,
    ConfigWatcher,
    ConfigChangeEvent,
    ConfigChangeHandler
)

from .config_manager import (
    ConfigManager,
    get_config,
    set_config,
    reload_config,
    watch_config
)

__all__ = [
    # 配置加载器
    'ConfigLoader',
    'ConfigFormat',
    'ConfigSource',
    
    # 配置验证器
    'ConfigValidator',
    'ValidationRule',
    'ConfigValidationError',
    
    # 环境配置
    'EnvironmentConfig',
    'Environment',
    'get_environment',
    'is_development',
    'is_production',
    'is_testing',
    
    # 动态配置
    'DynamicConfig',
    'ConfigWatcher',
    'ConfigChangeEvent',
    'ConfigChangeHandler',
    
    # 配置管理器
    'ConfigManager',
    'get_config',
    'set_config',
    'reload_config',
    'watch_config'
]