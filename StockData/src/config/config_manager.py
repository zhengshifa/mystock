#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器

负责加载和管理系统配置，支持:
- YAML配置文件
- 环境变量覆盖
- 配置验证
- 动态配置更新
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .config_validator import ConfigValidator


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None, env_file: Optional[str] = None):
        self.config_file = config_file or "config.yaml"
        self.env_file = env_file or ".env"
        self.config: Dict[str, Any] = {}
        self.validator = ConfigValidator()
        self._project_root = Path(__file__).parent.parent.parent
    
    async def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            # 加载环境变量
            self._load_env_variables()
            
            # 加载YAML配置文件
            self._load_yaml_config()
            
            # 环境变量覆盖配置
            self._override_with_env_vars()
            
            # 验证配置
            self.validator.validate(self.config)
            
            return self.config
            
        except Exception as e:
            raise Exception(f"配置加载失败: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config
    
    def _load_env_variables(self):
        """加载环境变量文件"""
        env_path = self._project_root / self.env_file
        if env_path.exists():
            load_dotenv(env_path)
    
    def _load_yaml_config(self):
        """加载YAML配置文件"""
        config_path = self._project_root / self.config_file
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f) or {}
        
        # 调试日志（可选）
        # print(f"配置文件路径: {config_path}")
        # print(f"加载的配置: {self.config}")
        # if 'sync' in self.config and 'realtime_sync' in self.config['sync']:
        #     print(f"实时同步配置: {self.config['sync']['realtime_sync']}")
    
    def _override_with_env_vars(self):
        """使用环境变量覆盖配置"""
        # 掘金量化配置
        if 'gm' not in self.config:
            self.config['gm'] = {}
        
        self.config['gm']['username'] = os.getenv('GM_USERNAME', self.config['gm'].get('username', ''))
        self.config['gm']['password'] = os.getenv('GM_PASSWORD', self.config['gm'].get('password', ''))
        self.config['gm']['token'] = os.getenv('GM_TOKEN', self.config['gm'].get('token', ''))
        self.config['gm']['auth_type'] = os.getenv('GM_AUTH_TYPE', self.config['gm'].get('auth_type', 'username_password'))
        
        # MongoDB配置
        if 'mongodb' not in self.config:
            self.config['mongodb'] = {}
        
        self.config['mongodb']['host'] = os.getenv('MONGO_HOST', self.config['mongodb'].get('host', 'localhost'))
        self.config['mongodb']['port'] = int(os.getenv('MONGO_PORT', self.config['mongodb'].get('port', 27017)))
        self.config['mongodb']['username'] = os.getenv('MONGO_USERNAME', self.config['mongodb'].get('username', 'admin'))
        self.config['mongodb']['password'] = os.getenv('MONGO_PASSWORD', self.config['mongodb'].get('password', 'password'))
        self.config['mongodb']['database'] = os.getenv('MONGO_DATABASE', self.config['mongodb'].get('database', 'stock_data'))
        self.config['mongodb']['auth_source'] = os.getenv('MONGO_AUTH_SOURCE', self.config['mongodb'].get('auth_source', 'admin'))
        
        # 系统配置
        if 'system' not in self.config:
            self.config['system'] = {}
        
        self.config['system']['environment'] = os.getenv('ENVIRONMENT', 'development')
        self.config['system']['debug'] = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # 日志配置
        if 'logging' not in self.config:
            self.config['logging'] = {}
        
        self.config['logging']['level'] = os.getenv('LOG_LEVEL', self.config['logging'].get('level', 'INFO'))
        
        # 同步配置
        if 'sync' not in self.config:
            self.config['sync'] = {}
        
        self.config['sync']['realtime_interval'] = int(os.getenv('REALTIME_SYNC_INTERVAL', 
                                                                self.config['sync'].get('realtime_interval', 30)))
        
        if 'history' not in self.config['sync']:
            self.config['sync']['history'] = {}
        
        self.config['sync']['history']['batch_size'] = int(os.getenv('HISTORY_BATCH_SIZE', 
                                                                    self.config['sync']['history'].get('batch_size', 1000)))
    
    def get_config(self, key: Optional[str] = None) -> Any:
        """获取配置值"""
        if key is None:
            return self.config
        
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def set_config(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_gm_config(self) -> Dict[str, Any]:
        """获取掘金量化配置"""
        return self.get_config('gm') or {}
    
    def get_mongodb_config(self) -> Dict[str, Any]:
        """获取MongoDB配置"""
        return self.get_config('mongodb') or {}
    
    def get_sync_config(self) -> Dict[str, Any]:
        """获取同步配置"""
        return self.get_config('sync') or {}
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get_config('logging') or {}
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """获取调度器配置"""
        return self.get_config('scheduler') or {}
    
    def get_stock_data_types(self) -> Dict[str, Any]:
        """获取股票数据类型配置"""
        return self.get_config('stock_data_types') or {}
    
    def is_debug_mode(self) -> bool:
        """是否为调试模式"""
        return self.get_config('system.debug') or False
    
    def get_environment(self) -> str:
        """获取运行环境"""
        return self.get_config('system.environment') or 'development'
    
    def reload_config(self):
        """重新加载配置"""
        self.config.clear()
        return self.load_config()