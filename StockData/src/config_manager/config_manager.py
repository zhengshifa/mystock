#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器主模块

整合所有配置管理功能:
- 配置加载和保存
- 配置验证
- 环境变量管理
- 动态配置更新
- 配置缓存和优化
"""

import os
import threading
from typing import Dict, Any, Optional, Union, List, Callable, Type
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import copy

from ..utils import get_logger, ConfigurationError, ValidationError
from .config_loader import ConfigLoader, ConfigFormat, ConfigSource as LoaderSource
from .config_validator import ConfigValidator, ValidationRule, ValidationResult
from .environment_config import EnvironmentConfig, EnvVarConfig, EnvironmentType
from .dynamic_config import DynamicConfig, ConfigChange, ConfigSource as DynamicSource


@dataclass
class ConfigManagerOptions:
    """配置管理器选项"""
    # 基础选项
    config_dir: Optional[Union[str, Path]] = None  # 配置目录
    env_prefix: str = ""                          # 环境变量前缀
    auto_reload: bool = True                      # 自动重载
    watch_interval: float = 1.0                   # 监控间隔
    
    # 验证选项
    validate_on_load: bool = True                 # 加载时验证
    strict_validation: bool = False               # 严格验证
    
    # 缓存选项
    enable_cache: bool = True                     # 启用缓存
    cache_ttl: int = 300                         # 缓存TTL(秒)
    
    # 环境选项
    load_env_vars: bool = True                   # 加载环境变量
    env_override: bool = True                    # 环境变量覆盖
    
    # 动态配置选项
    enable_dynamic: bool = True                  # 启用动态配置
    enable_sync: bool = False                    # 启用同步
    sync_interval: float = 30.0                  # 同步间隔
    
    # 版本管理
    enable_versioning: bool = True               # 启用版本管理
    max_versions: int = 10                       # 最大版本数
    
    # 安全选项
    mask_sensitive: bool = True                  # 脱敏敏感信息
    sensitive_keys: List[str] = field(default_factory=lambda: [
        'password', 'secret', 'key', 'token', 'api_key', 'private_key'
    ])


class ConfigManager:
    """配置管理器
    
    整合配置加载、验证、环境变量、动态更新等功能的统一管理器
    """
    
    def __init__(self, options: Optional[ConfigManagerOptions] = None, 
                 logger_name: str = "ConfigManager"):
        """
        初始化配置管理器
        
        Args:
            options: 配置选项
            logger_name: 日志器名称
        """
        self.options = options or ConfigManagerOptions()
        self.logger = get_logger(logger_name)
        
        # 初始化组件
        self.loader = ConfigLoader()
        self.validator = ConfigValidator()
        self.env_config = EnvironmentConfig(env_prefix=self.options.env_prefix)
        self.dynamic_config = DynamicConfig() if self.options.enable_dynamic else None
        
        # 配置存储
        self._config: Dict[str, Any] = {}
        self._config_lock = threading.RLock()
        self._config_files: Dict[str, Path] = {}  # 配置文件映射
        
        # 缓存
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # 回调函数
        self._change_callbacks: List[Callable[[str, Any, Any], None]] = []
        
        # 初始化配置目录
        if self.options.config_dir:
            self.config_dir = Path(self.options.config_dir)
            self.config_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.config_dir = Path.cwd() / "config"
        
        self.logger.info(f"Initialized ConfigManager with config dir: {self.config_dir}")
    
    def load_config(self, config_path: Union[str, Path, Dict[str, Union[str, Path]]], 
                   config_format: Optional[ConfigFormat] = None,
                   namespace: str = "default") -> Dict[str, Any]:
        """加载配置
        
        Args:
            config_path: 配置路径或路径字典
            config_format: 配置格式
            namespace: 命名空间
            
        Returns:
            加载的配置字典
        """
        try:
            # 处理多个配置文件
            if isinstance(config_path, dict):
                merged_config = {}
                for name, path in config_path.items():
                    config = self._load_single_config(path, config_format)
                    merged_config = self.loader.merge_configs(merged_config, config)
                    self._config_files[f"{namespace}.{name}"] = Path(path)
            else:
                merged_config = self._load_single_config(config_path, config_format)
                self._config_files[namespace] = Path(config_path)
            
            # 合并环境变量
            if self.options.load_env_vars:
                env_config = self.env_config.load_config(validate=False)
                if self.options.env_override:
                    merged_config.update(env_config)
                else:
                    for key, value in env_config.items():
                        if key not in merged_config:
                            merged_config[key] = value
            
            # 验证配置
            if self.options.validate_on_load:
                validation_result = self.validator.validate(
                    merged_config, 
                    raise_on_error=self.options.strict_validation
                )
                
                if not validation_result.is_valid:
                    self.logger.warning(f"Config validation warnings: {validation_result.warnings}")
                    if self.options.strict_validation:
                        raise ValidationError(f"Config validation failed: {validation_result.errors}")
            
            # 更新配置
            with self._config_lock:
                if namespace in self._config:
                    old_config = self._config[namespace].copy()
                else:
                    old_config = {}
                
                self._config[namespace] = merged_config
                
                # 通知变更
                self._notify_config_change(namespace, old_config, merged_config)
            
            # 更新动态配置
            if self.dynamic_config:
                self.dynamic_config.update(merged_config, DynamicSource.FILE)
            
            # 设置文件监控
            if self.options.auto_reload:
                self._setup_file_watching(namespace)
            
            self.logger.info(f"Loaded config for namespace '{namespace}' with {len(merged_config)} items")
            return merged_config
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            raise ConfigurationError(f"Failed to load config: {e}")
    
    def save_config(self, namespace: str = "default", 
                   config_path: Optional[Union[str, Path]] = None,
                   config_format: Optional[ConfigFormat] = None,
                   backup: bool = True):
        """保存配置
        
        Args:
            namespace: 命名空间
            config_path: 配置路径
            config_format: 配置格式
            backup: 是否备份
        """
        try:
            with self._config_lock:
                if namespace not in self._config:
                    raise ConfigurationError(f"Namespace '{namespace}' not found")
                
                config = self._config[namespace]
            
            # 确定保存路径
            if config_path is None:
                if namespace in self._config_files:
                    config_path = self._config_files[namespace]
                else:
                    config_path = self.config_dir / f"{namespace}.json"
            
            config_path = Path(config_path)
            
            # 备份原文件
            if backup and config_path.exists():
                backup_path = config_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
                config_path.rename(backup_path)
                self.logger.debug(f"Backed up config to: {backup_path}")
            
            # 脱敏敏感信息
            if self.options.mask_sensitive:
                config = self._mask_sensitive_data(config)
            
            # 保存配置
            self.loader.save_config(config, config_path, config_format)
            
            self.logger.info(f"Saved config for namespace '{namespace}' to: {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            raise ConfigurationError(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None, namespace: str = "default") -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值
            namespace: 命名空间
            
        Returns:
            配置值
        """
        # 检查缓存
        cache_key = f"{namespace}.{key}"
        if self.options.enable_cache and cache_key in self._cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time and (datetime.now() - cache_time).total_seconds() < self.options.cache_ttl:
                return self._cache[cache_key]
        
        # 获取配置值
        with self._config_lock:
            if namespace not in self._config:
                return default
            
            config = self._config[namespace]
            value = self._get_nested_value(config, key, default)
            
            # 更新缓存
            if self.options.enable_cache:
                self._cache[cache_key] = value
                self._cache_timestamps[cache_key] = datetime.now()
            
            return value
    
    def set(self, key: str, value: Any, namespace: str = "default", 
           persist: bool = False, notify: bool = True):
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            namespace: 命名空间
            persist: 是否持久化
            notify: 是否通知变更
        """
        with self._config_lock:
            if namespace not in self._config:
                self._config[namespace] = {}
            
            old_value = self._get_nested_value(self._config[namespace], key)
            self._set_nested_value(self._config[namespace], key, value)
            
            # 清除缓存
            cache_key = f"{namespace}.{key}"
            if cache_key in self._cache:
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
            
            # 通知变更
            if notify:
                self._notify_value_change(f"{namespace}.{key}", old_value, value)
            
            # 更新动态配置
            if self.dynamic_config:
                self.dynamic_config.set(key, value, DynamicSource.MEMORY)
        
        # 持久化
        if persist:
            self.save_config(namespace)
        
        self.logger.debug(f"Set config {namespace}.{key}={value}")
    
    def delete(self, key: str, namespace: str = "default", 
              persist: bool = False, notify: bool = True):
        """删除配置
        
        Args:
            key: 配置键
            namespace: 命名空间
            persist: 是否持久化
            notify: 是否通知变更
        """
        with self._config_lock:
            if namespace not in self._config:
                return
            
            old_value = self._get_nested_value(self._config[namespace], key)
            if old_value is not None:
                self._delete_nested_value(self._config[namespace], key)
                
                # 清除缓存
                cache_key = f"{namespace}.{key}"
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
                
                # 通知变更
                if notify:
                    self._notify_value_change(f"{namespace}.{key}", old_value, None)
                
                # 更新动态配置
                if self.dynamic_config:
                    self.dynamic_config.delete(key)
        
        # 持久化
        if persist:
            self.save_config(namespace)
        
        self.logger.debug(f"Deleted config {namespace}.{key}")
    
    def reload(self, namespace: str = "default"):
        """重新加载配置
        
        Args:
            namespace: 命名空间
        """
        if namespace not in self._config_files:
            self.logger.warning(f"No config file found for namespace '{namespace}'")
            return
        
        config_path = self._config_files[namespace]
        self.load_config(config_path, namespace=namespace)
        
        self.logger.info(f"Reloaded config for namespace '{namespace}'")
    
    def validate_config(self, namespace: str = "default") -> ValidationResult:
        """验证配置
        
        Args:
            namespace: 命名空间
            
        Returns:
            验证结果
        """
        with self._config_lock:
            if namespace not in self._config:
                raise ConfigurationError(f"Namespace '{namespace}' not found")
            
            config = self._config[namespace]
            return self.validator.validate(config)
    
    def add_validation_rule(self, rule: ValidationRule):
        """添加验证规则
        
        Args:
            rule: 验证规则
        """
        self.validator.add_rule(rule)
    
    def add_env_var(self, env_config: EnvVarConfig):
        """添加环境变量配置
        
        Args:
            env_config: 环境变量配置
        """
        self.env_config.register_env_var(env_config)
    
    def add_change_callback(self, callback: Callable[[str, Any, Any], None]):
        """添加配置变更回调
        
        Args:
            callback: 回调函数，接收(key, old_value, new_value)参数
        """
        self._change_callbacks.append(callback)
        self.logger.debug(f"Added config change callback: {callback.__name__}")
    
    def get_config_info(self, namespace: str = "default") -> Dict[str, Any]:
        """获取配置信息
        
        Args:
            namespace: 命名空间
            
        Returns:
            配置信息字典
        """
        with self._config_lock:
            if namespace not in self._config:
                return {}
            
            config = self._config[namespace]
            return {
                'namespace': namespace,
                'items': len(config),
                'file_path': str(self._config_files.get(namespace, '')),
                'last_modified': self._config_files.get(namespace, Path()).stat().st_mtime 
                                if namespace in self._config_files and self._config_files[namespace].exists() else None,
                'cache_items': len([k for k in self._cache.keys() if k.startswith(f"{namespace}.")]),
                'environment': self.env_config.environment.value,
                'validation_rules': len(self.validator.rules)
            }
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置
        
        Returns:
            所有配置字典
        """
        with self._config_lock:
            return copy.deepcopy(self._config)
    
    def clear_cache(self, namespace: Optional[str] = None):
        """清除缓存
        
        Args:
            namespace: 命名空间，None表示清除所有缓存
        """
        if namespace is None:
            self._cache.clear()
            self._cache_timestamps.clear()
            self.logger.info("Cleared all config cache")
        else:
            prefix = f"{namespace}."
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._cache[key]
                del self._cache_timestamps[key]
            self.logger.info(f"Cleared cache for namespace '{namespace}'")
    
    def export_config(self, namespace: str = "default", 
                     export_path: Union[str, Path] = None,
                     export_format: ConfigFormat = ConfigFormat.JSON,
                     include_metadata: bool = True) -> str:
        """导出配置
        
        Args:
            namespace: 命名空间
            export_path: 导出路径
            export_format: 导出格式
            include_metadata: 是否包含元数据
            
        Returns:
            导出的配置字符串
        """
        with self._config_lock:
            if namespace not in self._config:
                raise ConfigurationError(f"Namespace '{namespace}' not found")
            
            config = self._config[namespace].copy()
            
            # 添加元数据
            if include_metadata:
                config['__metadata__'] = {
                    'namespace': namespace,
                    'export_time': datetime.now().isoformat(),
                    'environment': self.env_config.environment.value,
                    'version': getattr(self.dynamic_config, '_current_version', '1.0.0') if self.dynamic_config else '1.0.0'
                }
            
            # 脱敏敏感信息
            if self.options.mask_sensitive:
                config = self._mask_sensitive_data(config)
            
            # 导出
            if export_path:
                self.loader.save_config(config, export_path, export_format)
                return str(export_path)
            else:
                return self.loader.config_to_string(config, export_format)
    
    def import_config(self, config_data: Union[str, Dict[str, Any]], 
                     namespace: str = "default",
                     config_format: Optional[ConfigFormat] = None,
                     merge: bool = True):
        """导入配置
        
        Args:
            config_data: 配置数据
            namespace: 命名空间
            config_format: 配置格式
            merge: 是否合并现有配置
        """
        try:
            # 解析配置数据
            if isinstance(config_data, str):
                if config_format is None:
                    config_format = ConfigFormat.AUTO
                config = self.loader.load_from_string(config_data, config_format)
            else:
                config = config_data
            
            # 移除元数据
            if '__metadata__' in config:
                del config['__metadata__']
            
            # 合并或替换配置
            with self._config_lock:
                if merge and namespace in self._config:
                    old_config = self._config[namespace].copy()
                    self._config[namespace] = self.loader.merge_configs(self._config[namespace], config)
                else:
                    old_config = self._config.get(namespace, {})
                    self._config[namespace] = config
                
                # 通知变更
                self._notify_config_change(namespace, old_config, self._config[namespace])
            
            # 更新动态配置
            if self.dynamic_config:
                self.dynamic_config.update(config, DynamicSource.MEMORY)
            
            self.logger.info(f"Imported config for namespace '{namespace}' with {len(config)} items")
            
        except Exception as e:
            self.logger.error(f"Error importing config: {e}")
            raise ConfigurationError(f"Failed to import config: {e}")
    
    def _load_single_config(self, config_path: Union[str, Path], 
                           config_format: Optional[ConfigFormat] = None) -> Dict[str, Any]:
        """加载单个配置文件
        
        Args:
            config_path: 配置路径
            config_format: 配置格式
            
        Returns:
            配置字典
        """
        config_path = Path(config_path)
        
        # 如果是相对路径，相对于配置目录
        if not config_path.is_absolute():
            config_path = self.config_dir / config_path
        
        return self.loader.load_config(config_path, config_format)
    
    def _setup_file_watching(self, namespace: str):
        """设置文件监控
        
        Args:
            namespace: 命名空间
        """
        if not self.dynamic_config or namespace not in self._config_files:
            return
        
        config_path = self._config_files[namespace]
        
        def reload_callback(path: Path):
            try:
                self.reload(namespace)
            except Exception as e:
                self.logger.error(f"Error reloading config from {path}: {e}")
        
        self.dynamic_config.watch_file(
            config_path, 
            lambda p: self.loader.load_config(p),
            self.options.watch_interval
        )
    
    def _get_nested_value(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """获取嵌套配置值
        
        Args:
            config: 配置字典
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """设置嵌套配置值
        
        Args:
            config: 配置字典
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _delete_nested_value(self, config: Dict[str, Any], key: str):
        """删除嵌套配置值
        
        Args:
            config: 配置字典
            key: 配置键
        """
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                return
            current = current[k]
        
        if keys[-1] in current:
            del current[keys[-1]]
    
    def _mask_sensitive_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏敏感数据
        
        Args:
            config: 配置字典
            
        Returns:
            脱敏后的配置字典
        """
        masked_config = copy.deepcopy(config)
        
        def mask_recursive(obj: Any, path: str = "") -> Any:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(sensitive_key.lower() in key.lower() for sensitive_key in self.options.sensitive_keys):
                        obj[key] = "***"
                    else:
                        obj[key] = mask_recursive(value, current_path)
            elif isinstance(obj, list):
                return [mask_recursive(item, f"{path}[{i}]") for i, item in enumerate(obj)]
            
            return obj
        
        return mask_recursive(masked_config)
    
    def _notify_config_change(self, namespace: str, old_config: Dict[str, Any], 
                             new_config: Dict[str, Any]):
        """通知配置变更
        
        Args:
            namespace: 命名空间
            old_config: 旧配置
            new_config: 新配置
        """
        # 找出变更的键
        all_keys = set(old_config.keys()) | set(new_config.keys())
        
        for key in all_keys:
            old_value = old_config.get(key)
            new_value = new_config.get(key)
            
            if old_value != new_value:
                self._notify_value_change(f"{namespace}.{key}", old_value, new_value)
    
    def _notify_value_change(self, key: str, old_value: Any, new_value: Any):
        """通知值变更
        
        Args:
            key: 配置键
            old_value: 旧值
            new_value: 新值
        """
        for callback in self._change_callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                self.logger.error(f"Error in config change callback {callback.__name__}: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        # 停止文件监控
        if self.dynamic_config:
            for namespace in self._config_files:
                if namespace in self._config_files:
                    self.dynamic_config.stop_watching(self._config_files[namespace])
        
        # 清理资源
        self.clear_cache()


# 便利函数
def create_config_manager(config_dir: Union[str, Path] = None, 
                         env_prefix: str = "",
                         auto_reload: bool = True) -> ConfigManager:
    """创建配置管理器
    
    Args:
        config_dir: 配置目录
        env_prefix: 环境变量前缀
        auto_reload: 自动重载
        
    Returns:
        配置管理器实例
    """
    options = ConfigManagerOptions(
        config_dir=config_dir,
        env_prefix=env_prefix,
        auto_reload=auto_reload
    )
    
    return ConfigManager(options)