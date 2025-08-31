"""配置管理模块"""

import os
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


class Config:
    """配置管理类"""
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._loaded = False
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置"""
        if self._loaded:
            return
        
        # 加载.env文件
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"已加载环境配置文件: {env_file.absolute()}")
        else:
            logger.info("未找到.env文件，使用系统环境变量")
        
        # 设置默认配置
        self._set_defaults()
        
        # 从环境变量加载配置
        self._load_from_env()
        
        self._loaded = True
        logger.success("配置加载完成")
    
    def _set_defaults(self) -> None:
        """设置默认配置"""
        self._config.update({
            # MongoDB配置
            "MONGODB_HOST": "localhost",
            "MONGODB_PORT": "27017",
            "MONGODB_DATABASE": "newsnow",
            "MONGODB_AUTH_SOURCE": "admin",
            
            # 调度器配置
            "FETCH_INTERVAL": 300,  # 5分钟
            "MAX_NEWS_PER_SOURCE": 50,
            "MAX_CONCURRENT_SOURCES": 10,  # 增加默认并发数
            "BATCH_SIZE": 5,  # 批处理大小
            "BATCH_DELAY": 1,  # 批次间延迟(秒)
            "FETCH_ON_START": True,
            
            # 数据清理配置
            "CLEANUP_ENABLED": True,
            "CLEANUP_TIME": "02:00",
            "DATA_RETENTION_DAYS": 30,
            
            # 网络配置
            "REQUEST_TIMEOUT": 5,
            "MAX_RETRIES": 3,
            "RETRY_DELAY": 1,
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            
            # 代理配置
            "PROXY_ENABLED": False,
            "PROXY_ROTATION": False,
            
            # 日志配置
            "LOG_LEVEL": "INFO",
            "LOG_FILE": "logs/newsnow.log",
            "LOG_ROTATION": "1 day",
            "LOG_RETENTION": "30 days",
            
            # 运行模式
            "DEBUG": False,
            "ENVIRONMENT": "production",
        })
    
    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # 字符串类型的配置
        string_configs = [
            "MONGODB_URI", "MONGODB_HOST", "MONGODB_PORT", "MONGODB_DATABASE",
            "MONGODB_USERNAME", "MONGODB_PASSWORD", "MONGODB_AUTH_SOURCE",
            "CLEANUP_TIME", "USER_AGENT", "PROXY_LIST", "LOG_LEVEL",
            "LOG_FILE", "LOG_ROTATION", "LOG_RETENTION", "ENVIRONMENT",
            "ENABLED_SOURCES"
        ]
        
        # 整数类型的配置
        int_configs = [
            "FETCH_INTERVAL", "MAX_NEWS_PER_SOURCE", "MAX_CONCURRENT_SOURCES",
            "BATCH_SIZE", "BATCH_DELAY", "DATA_RETENTION_DAYS", 
            "REQUEST_TIMEOUT", "MAX_RETRIES", "RETRY_DELAY"
        ]
        
        # 布尔类型的配置
        bool_configs = [
            "FETCH_ON_START", "CLEANUP_ENABLED", "PROXY_ENABLED",
            "PROXY_ROTATION", "DEBUG"
        ]
        
        # 加载字符串配置
        for key in string_configs:
            value = os.getenv(key)
            if value is not None:
                self._config[key] = value
        
        # 加载整数配置
        for key in int_configs:
            value = os.getenv(key)
            if value is not None:
                try:
                    self._config[key] = int(value)
                except ValueError:
                    logger.warning(f"配置项 {key} 的值 '{value}' 不是有效的整数，使用默认值")
        
        # 加载布尔配置
        for key in bool_configs:
            value = os.getenv(key)
            if value is not None:
                self._config[key] = value.lower() in ('true', '1', 'yes', 'on')
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config[key] = value
    
    def get_mongodb_config(self) -> Dict[str, Any]:
        """获取MongoDB配置"""
        return {
            "uri": self.get("MONGODB_URI"),
            "host": self.get("MONGODB_HOST"),
            "port": self.get("MONGODB_PORT"),
            "database": self.get("MONGODB_DATABASE"),
            "username": self.get("MONGODB_USERNAME"),
            "password": self.get("MONGODB_PASSWORD"),
            "auth_source": self.get("MONGODB_AUTH_SOURCE")
        }
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """获取调度器配置"""
        return {
            "fetch_interval": self.get("FETCH_INTERVAL"),
            "max_news_per_source": self.get("MAX_NEWS_PER_SOURCE"),
            "max_concurrent_sources": self.get("MAX_CONCURRENT_SOURCES"),
            "fetch_on_start": self.get("FETCH_ON_START"),
            "cleanup_enabled": self.get("CLEANUP_ENABLED"),
            "cleanup_time": self.get("CLEANUP_TIME"),
            "data_retention_days": self.get("DATA_RETENTION_DAYS")
        }
    
    def get_network_config(self) -> Dict[str, Any]:
        """获取网络配置"""
        return {
            "timeout": self.get("REQUEST_TIMEOUT"),
            "max_retries": self.get("MAX_RETRIES"),
            "retry_delay": self.get("RETRY_DELAY"),
            "user_agent": self.get("USER_AGENT"),
            "proxy_enabled": self.get("PROXY_ENABLED"),
            "proxy_rotation": self.get("PROXY_ROTATION"),
            "proxy_list": self.get("PROXY_LIST")
        }
    
    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "level": self.get("LOG_LEVEL"),
            "file": self.get("LOG_FILE"),
            "rotation": self.get("LOG_ROTATION"),
            "retention": self.get("LOG_RETENTION")
        }
    
    def is_debug(self) -> bool:
        """是否为调试模式"""
        return self.get("DEBUG", False)
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.get("ENVIRONMENT", "production") == "production"
    
    def reload(self) -> None:
        """重新加载配置"""
        self._loaded = False
        self._config.clear()
        self.load_config()
        logger.info("配置已重新加载")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self._config[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """支持字典式设置"""
        self._config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """支持in操作符"""
        return key in self._config


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reload_config() -> Config:
    """重新加载配置"""
    global _config_instance
    if _config_instance:
        _config_instance.reload()
    else:
        _config_instance = Config()
    return _config_instance


# 便捷函数
def get_env(key: str, default: Any = None) -> Any:
    """获取环境变量"""
    return get_config().get(key, default)


def set_env(key: str, value: Any) -> None:
    """设置环境变量"""
    get_config().set(key, value)


def is_debug() -> bool:
    """是否为调试模式"""
    return get_config().is_debug()


def is_production() -> bool:
    """是否为生产环境"""
    return get_config().is_production()