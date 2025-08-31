#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
负责配置的加载、验证和管理
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from .settings import AppConfig
from .env_loader import EnvLoader
from .validator import ConfigValidator


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，可选
        """
        self.config_file = config_file
        self._config: Optional[AppConfig] = None
        self._env_loaded = False
        
    def get_config(self) -> AppConfig:
        """
        获取配置实例
        
        Returns:
            配置实例
        """
        if self._config is None:
            self._config = self._create_config()
        return self._config
    
    def reload_config(self) -> AppConfig:
        """
        重新加载配置
        
        Returns:
            重新加载后的配置实例
        """
        self._config = None
        self._env_loaded = False
        return self.get_config()
    
    def _create_config(self) -> AppConfig:
        """
        创建配置实例
        
        Returns:
            配置实例
        """
        # 加载环境变量
        self._load_environment()
        
        # 创建配置实例
        config = AppConfig()
        
        # 从环境变量加载配置
        EnvLoader.load_config_from_env(config)
        
        # 从配置文件加载（如果提供）
        if self.config_file:
            self._load_from_file(config)
        
        # 验证配置
        is_valid, errors = ConfigValidator.validate_config(config)
        if not is_valid:
            print("警告: 配置验证失败，请检查配置:")
            for error in errors:
                print(f"  - {error}")
        
        return config
    
    def _load_environment(self):
        """加载环境变量"""
        if self._env_loaded:
            return
            
        # 加载.env文件
        project_root = Path(__file__).parent.parent
        env_file = project_root / "config" / ".env"
        
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                print(f"已加载环境变量文件: {env_file}")
            except ImportError:
                print("警告: python-dotenv未安装，无法加载.env文件")
        
        self._env_loaded = True
    
    def _load_from_file(self, config: AppConfig):
        """
        从配置文件加载配置
        
        Args:
            config: 配置实例
        """
        # TODO: 实现从YAML或JSON文件加载配置
        pass
    
    def get_env_value(self, key: str, default: Any = None) -> Any:
        """
        获取环境变量值
        
        Args:
            key: 环境变量键
            default: 默认值
            
        Returns:
            环境变量值或默认值
        """
        return os.getenv(key, default)
    
    def set_env_value(self, key: str, value: str):
        """
        设置环境变量值
        
        Args:
            key: 环境变量键
            value: 环境变量值
        """
        os.environ[key] = value
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要信息
        
        Returns:
            配置摘要字典
        """
        config = self.get_config()
        return ConfigValidator.get_config_summary(config)
