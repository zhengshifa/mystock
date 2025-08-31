#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
支持从环境变量、配置文件、命令行参数等加载配置
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field


@dataclass
class GMConfig:
    """掘金量化配置类"""
    token: str = ""
    account_id: Optional[str] = None
    server_addr: str = ""
    mode: str = "MODE_BACKTEST"  # MODE_BACKTEST, MODE_LIVE, MODE_UNKNOWN


@dataclass
class LogConfig:
    """日志配置类"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True


@dataclass
class SchedulerConfig:
    """调度器配置类"""
    max_workers: int = 4
    thread_name_prefix: str = "StockData"
    enable_monitoring: bool = True
    heartbeat_interval: int = 30  # 秒


@dataclass
class AppConfig:
    """应用配置类"""
    gm: GMConfig = field(default_factory=GMConfig)
    log: LogConfig = field(default_factory=LogConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    debug: bool = False
    data_dir: str = "./data"
    cache_dir: str = "./cache"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，支持 .json, .yaml, .yml 格式
        """
        self.config_file = config_file
        self.config = AppConfig()
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 1. 加载默认配置
        self._load_defaults()
        
        # 2. 加载配置文件
        if self.config_file and Path(self.config_file).exists():
            self._load_from_file()
        
        # 3. 加载环境变量
        self._load_from_env()
    
    def _load_defaults(self):
        """加载默认配置"""
        # 掘金量化默认配置
        self.config.gm.token = os.getenv("GM_TOKEN", "")
        self.config.gm.account_id = os.getenv("GM_ACCOUNT_ID")
        self.config.gm.server_addr = os.getenv("GM_SERVER_ADDR", "")
        self.config.gm.mode = os.getenv("GM_MODE", "MODE_BACKTEST")
        
        # 日志默认配置
        self.config.log.level = os.getenv("LOG_LEVEL", "INFO")
        self.config.log.file_path = os.getenv("LOG_FILE_PATH")
        self.config.log.console_output = os.getenv("LOG_CONSOLE_OUTPUT", "true").lower() == "true"
        
        # 调度器默认配置
        self.config.scheduler.max_workers = int(os.getenv("SCHEDULER_MAX_WORKERS", "4"))
        self.config.scheduler.enable_monitoring = os.getenv("SCHEDULER_ENABLE_MONITORING", "true").lower() == "true"
        
        # 应用默认配置
        self.config.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.config.data_dir = os.getenv("DATA_DIR", "./data")
        self.config.cache_dir = os.getenv("CACHE_DIR", "./cache")
    
    def _load_from_file(self):
        """从配置文件加载配置"""
        if not self.config_file:
            return
            
        file_path = Path(self.config_file)
        if not file_path.exists():
            return
            
        try:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                return
                
            self._update_config_from_dict(config_data)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 掘金量化配置
        if os.getenv("GM_TOKEN"):
            self.config.gm.token = os.getenv("GM_TOKEN")
        if os.getenv("GM_ACCOUNT_ID"):
            self.config.gm.account_id = os.getenv("GM_ACCOUNT_ID")
        if os.getenv("GM_SERVER_ADDR"):
            self.config.gm.server_addr = os.getenv("GM_SERVER_ADDR")
        if os.getenv("GM_MODE"):
            self.config.gm.mode = os.getenv("GM_MODE")
        
        # 日志配置
        if os.getenv("LOG_LEVEL"):
            self.config.log.level = os.getenv("LOG_LEVEL")
        if os.getenv("LOG_FILE_PATH"):
            self.config.log.file_path = os.getenv("LOG_FILE_PATH")
        
        # 调度器配置
        if os.getenv("SCHEDULER_MAX_WORKERS"):
            self.config.scheduler.max_workers = int(os.getenv("SCHEDULER_MAX_WORKERS"))
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """从字典更新配置"""
        if not isinstance(config_data, dict):
            return
            
        # 更新掘金量化配置
        if "gm" in config_data:
            gm_config = config_data["gm"]
            if isinstance(gm_config, dict):
                for key, value in gm_config.items():
                    if hasattr(self.config.gm, key):
                        setattr(self.config.gm, key, value)
        
        # 更新日志配置
        if "log" in config_data:
            log_config = config_data["log"]
            if isinstance(log_config, dict):
                for key, value in log_config.items():
                    if hasattr(self.config.log, key):
                        setattr(self.config.log, key, value)
        
        # 更新调度器配置
        if "scheduler" in config_data:
            scheduler_config = config_data["scheduler"]
            if isinstance(scheduler_config, dict):
                for key, value in scheduler_config.items():
                    if hasattr(self.config.scheduler, key):
                        setattr(self.config.scheduler, key, value)
        
        # 更新应用配置
        for key, value in config_data.items():
            if key not in ["gm", "log", "scheduler"] and hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def get_gm_config(self) -> GMConfig:
        """获取掘金量化配置"""
        return self.config.gm
    
    def get_log_config(self) -> LogConfig:
        """获取日志配置"""
        return self.config.log
    
    def get_scheduler_config(self) -> SchedulerConfig:
        """获取调度器配置"""
        return self.config.scheduler
    
    def get_app_config(self) -> AppConfig:
        """获取应用配置"""
        return self.config
    
    def update_gm_config(self, **kwargs):
        """更新掘金量化配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.gm, key):
                setattr(self.config.gm, key, value)
    
    def save_config(self, file_path: Optional[str] = None):
        """保存配置到文件"""
        save_path = file_path or self.config_file
        if not save_path:
            return
            
        file_path = Path(save_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            "gm": {
                "token": self.config.gm.token,
                "account_id": self.config.gm.account_id,
                "server_addr": self.config.gm.server_addr,
                "mode": self.config.gm.mode,
            },
            "log": {
                "level": self.config.log.level,
                "format": self.config.log.format,
                "file_path": self.config.log.file_path,
                "max_bytes": self.config.log.max_bytes,
                "backup_count": self.config.log.backup_count,
                "console_output": self.config.log.console_output,
            },
            "scheduler": {
                "max_workers": self.config.scheduler.max_workers,
                "thread_name_prefix": self.config.scheduler.thread_name_prefix,
                "enable_monitoring": self.config.scheduler.enable_monitoring,
                "heartbeat_interval": self.config.scheduler.heartbeat_interval,
            },
            "debug": self.config.debug,
            "data_dir": self.config.data_dir,
            "cache_dir": self.config.cache_dir,
        }
        
        try:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """获取全局配置"""
    return config_manager.get_app_config()


def get_gm_config() -> GMConfig:
    """获取掘金量化配置"""
    return config_manager.get_gm_config()


def get_log_config() -> LogConfig:
    """获取日志配置"""
    return config_manager.get_log_config()


def get_scheduler_config() -> SchedulerConfig:
    """获取调度器配置"""
    return config_manager.get_scheduler_config()
