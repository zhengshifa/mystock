#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态配置模块

提供动态配置管理功能:
- 配置热更新
- 配置变更监控
- 配置回调机制
- 配置版本管理
- 配置同步机制
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import json
import copy
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import hashlib

from ..utils import get_logger, ConfigurationError


class ConfigChangeType(Enum):
    """配置变更类型"""
    ADDED = "added"          # 新增
    MODIFIED = "modified"    # 修改
    DELETED = "deleted"      # 删除
    RELOADED = "reloaded"    # 重新加载


class ConfigSource(Enum):
    """配置源类型"""
    FILE = "file"            # 文件
    DATABASE = "database"    # 数据库
    REMOTE = "remote"        # 远程服务
    MEMORY = "memory"        # 内存
    ENVIRONMENT = "environment"  # 环境变量


@dataclass
class ConfigChange:
    """配置变更记录"""
    key: str                           # 配置键
    old_value: Any                     # 旧值
    new_value: Any                     # 新值
    change_type: ConfigChangeType      # 变更类型
    timestamp: datetime                # 变更时间
    source: ConfigSource               # 配置源
    version: str                       # 版本号
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ConfigVersion:
    """配置版本信息"""
    version: str                       # 版本号
    config: Dict[str, Any]            # 配置内容
    timestamp: datetime               # 创建时间
    checksum: str                     # 校验和
    changes: List[ConfigChange] = field(default_factory=list)  # 变更记录
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """计算配置校验和"""
        config_str = json.dumps(self.config, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()


class ConfigWatcher:
    """配置监控器"""
    
    def __init__(self, source_path: Union[str, Path], 
                 check_interval: float = 1.0, logger_name: str = "ConfigWatcher"):
        """
        初始化配置监控器
        
        Args:
            source_path: 配置源路径
            check_interval: 检查间隔(秒)
            logger_name: 日志器名称
        """
        self.source_path = Path(source_path)
        self.check_interval = check_interval
        self.logger = get_logger(logger_name)
        
        self._last_modified = None
        self._last_checksum = None
        self._running = False
        self._thread = None
        self._callbacks: List[Callable[[Path], None]] = []
    
    def add_callback(self, callback: Callable[[Path], None]):
        """添加变更回调
        
        Args:
            callback: 回调函数，接收文件路径参数
        """
        self._callbacks.append(callback)
        self.logger.debug(f"Added config change callback: {callback.__name__}")
    
    def start(self):
        """开始监控"""
        if self._running:
            self.logger.warning("Config watcher is already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        self.logger.info(f"Started watching config file: {self.source_path}")
    
    def stop(self):
        """停止监控"""
        if not self._running:
            return
        
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        
        self.logger.info("Stopped config watcher")
    
    def _watch_loop(self):
        """监控循环"""
        while self._running:
            try:
                if self._check_changes():
                    self._notify_callbacks()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in config watch loop: {e}")
                time.sleep(self.check_interval)
    
    def _check_changes(self) -> bool:
        """检查配置变更
        
        Returns:
            是否有变更
        """
        if not self.source_path.exists():
            return False
        
        try:
            # 检查文件修改时间
            current_modified = self.source_path.stat().st_mtime
            if self._last_modified is None:
                self._last_modified = current_modified
                return False
            
            if current_modified != self._last_modified:
                self._last_modified = current_modified
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking file changes: {e}")
            return False
    
    def _notify_callbacks(self):
        """通知回调函数"""
        for callback in self._callbacks:
            try:
                callback(self.source_path)
            except Exception as e:
                self.logger.error(f"Error in config change callback {callback.__name__}: {e}")


class DynamicConfig:
    """动态配置管理器"""
    
    def __init__(self, logger_name: str = "DynamicConfig"):
        """
        初始化动态配置管理器
        
        Args:
            logger_name: 日志器名称
        """
        self.logger = get_logger(logger_name)
        
        # 配置存储
        self._config: Dict[str, Any] = {}
        self._config_lock = threading.RLock()
        
        # 版本管理
        self._versions: List[ConfigVersion] = []
        self._current_version = "1.0.0"
        self._max_versions = 10
        
        # 变更监控
        self._watchers: Dict[str, ConfigWatcher] = {}
        self._change_callbacks: Dict[str, List[Callable[[ConfigChange], None]]] = {}
        self._global_callbacks: List[Callable[[ConfigChange], None]] = []
        
        # 同步机制
        self._sync_enabled = False
        self._sync_interval = 30.0
        self._sync_thread = None
        self._sync_sources: List[Callable[[], Dict[str, Any]]] = []
        
        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="DynamicConfig")
    
    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.MEMORY,
           notify: bool = True, create_version: bool = True):
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            source: 配置源
            notify: 是否通知变更
            create_version: 是否创建新版本
        """
        with self._config_lock:
            old_value = self._config.get(key)
            
            # 检查是否有变更
            if old_value == value:
                return
            
            # 更新配置
            self._config[key] = value
            
            # 创建变更记录
            change_type = ConfigChangeType.MODIFIED if key in self._config else ConfigChangeType.ADDED
            change = ConfigChange(
                key=key,
                old_value=old_value,
                new_value=value,
                change_type=change_type,
                timestamp=datetime.now(),
                source=source,
                version=self._current_version
            )
            
            # 创建新版本
            if create_version:
                self._create_version([change])
            
            # 通知变更
            if notify:
                self._notify_change(change)
            
            self.logger.debug(f"Set config {key}={value} (source: {source.value})")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        with self._config_lock:
            return self._config.get(key, default)
    
    def delete(self, key: str, notify: bool = True, create_version: bool = True):
        """删除配置
        
        Args:
            key: 配置键
            notify: 是否通知变更
            create_version: 是否创建新版本
        """
        with self._config_lock:
            if key not in self._config:
                return
            
            old_value = self._config.pop(key)
            
            # 创建变更记录
            change = ConfigChange(
                key=key,
                old_value=old_value,
                new_value=None,
                change_type=ConfigChangeType.DELETED,
                timestamp=datetime.now(),
                source=ConfigSource.MEMORY,
                version=self._current_version
            )
            
            # 创建新版本
            if create_version:
                self._create_version([change])
            
            # 通知变更
            if notify:
                self._notify_change(change)
            
            self.logger.debug(f"Deleted config key: {key}")
    
    def update(self, config: Dict[str, Any], source: ConfigSource = ConfigSource.MEMORY,
              notify: bool = True, create_version: bool = True):
        """批量更新配置
        
        Args:
            config: 配置字典
            source: 配置源
            notify: 是否通知变更
            create_version: 是否创建新版本
        """
        changes = []
        
        with self._config_lock:
            for key, value in config.items():
                old_value = self._config.get(key)
                
                if old_value != value:
                    self._config[key] = value
                    
                    change_type = ConfigChangeType.MODIFIED if key in self._config else ConfigChangeType.ADDED
                    change = ConfigChange(
                        key=key,
                        old_value=old_value,
                        new_value=value,
                        change_type=change_type,
                        timestamp=datetime.now(),
                        source=source,
                        version=self._current_version
                    )
                    changes.append(change)
            
            # 创建新版本
            if create_version and changes:
                self._create_version(changes)
            
            # 通知变更
            if notify:
                for change in changes:
                    self._notify_change(change)
            
            self.logger.info(f"Updated {len(changes)} config items (source: {source.value})")
    
    def reload_from_source(self, source_func: Callable[[], Dict[str, Any]], 
                          source: ConfigSource = ConfigSource.FILE):
        """从源重新加载配置
        
        Args:
            source_func: 配置源函数
            source: 配置源类型
        """
        try:
            new_config = source_func()
            
            # 创建重新加载变更记录
            change = ConfigChange(
                key="*",
                old_value=copy.deepcopy(self._config),
                new_value=new_config,
                change_type=ConfigChangeType.RELOADED,
                timestamp=datetime.now(),
                source=source,
                version=self._current_version
            )
            
            # 更新配置
            with self._config_lock:
                self._config.clear()
                self._config.update(new_config)
            
            # 创建新版本
            self._create_version([change])
            
            # 通知变更
            self._notify_change(change)
            
            self.logger.info(f"Reloaded config from source: {source.value}")
            
        except Exception as e:
            self.logger.error(f"Error reloading config from source: {e}")
            raise ConfigurationError(f"Failed to reload config: {e}")
    
    def watch_file(self, file_path: Union[str, Path], 
                  loader_func: Callable[[Path], Dict[str, Any]],
                  check_interval: float = 1.0):
        """监控配置文件
        
        Args:
            file_path: 文件路径
            loader_func: 加载函数
            check_interval: 检查间隔
        """
        file_path = Path(file_path)
        watcher_key = str(file_path)
        
        if watcher_key in self._watchers:
            self.logger.warning(f"File {file_path} is already being watched")
            return
        
        # 创建监控器
        watcher = ConfigWatcher(file_path, check_interval)
        
        # 添加回调
        def on_file_change(path: Path):
            try:
                self.reload_from_source(lambda: loader_func(path), ConfigSource.FILE)
            except Exception as e:
                self.logger.error(f"Error reloading config from {path}: {e}")
        
        watcher.add_callback(on_file_change)
        
        # 启动监控
        watcher.start()
        self._watchers[watcher_key] = watcher
        
        self.logger.info(f"Started watching config file: {file_path}")
    
    def stop_watching(self, file_path: Union[str, Path]):
        """停止监控文件
        
        Args:
            file_path: 文件路径
        """
        watcher_key = str(Path(file_path))
        
        if watcher_key in self._watchers:
            self._watchers[watcher_key].stop()
            del self._watchers[watcher_key]
            self.logger.info(f"Stopped watching config file: {file_path}")
    
    def add_change_callback(self, callback: Callable[[ConfigChange], None], 
                           key_pattern: Optional[str] = None):
        """添加配置变更回调
        
        Args:
            callback: 回调函数
            key_pattern: 键模式，None表示全局回调
        """
        if key_pattern is None:
            self._global_callbacks.append(callback)
            self.logger.debug(f"Added global config change callback: {callback.__name__}")
        else:
            if key_pattern not in self._change_callbacks:
                self._change_callbacks[key_pattern] = []
            self._change_callbacks[key_pattern].append(callback)
            self.logger.debug(f"Added config change callback for pattern '{key_pattern}': {callback.__name__}")
    
    def remove_change_callback(self, callback: Callable[[ConfigChange], None], 
                              key_pattern: Optional[str] = None):
        """移除配置变更回调
        
        Args:
            callback: 回调函数
            key_pattern: 键模式
        """
        if key_pattern is None:
            if callback in self._global_callbacks:
                self._global_callbacks.remove(callback)
        else:
            if key_pattern in self._change_callbacks:
                if callback in self._change_callbacks[key_pattern]:
                    self._change_callbacks[key_pattern].remove(callback)
    
    def enable_sync(self, interval: float = 30.0):
        """启用配置同步
        
        Args:
            interval: 同步间隔(秒)
        """
        if self._sync_enabled:
            return
        
        self._sync_enabled = True
        self._sync_interval = interval
        
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        
        self.logger.info(f"Enabled config sync with interval: {interval}s")
    
    def disable_sync(self):
        """禁用配置同步"""
        self._sync_enabled = False
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5.0)
        
        self.logger.info("Disabled config sync")
    
    def add_sync_source(self, source_func: Callable[[], Dict[str, Any]]):
        """添加同步源
        
        Args:
            source_func: 同步源函数
        """
        self._sync_sources.append(source_func)
        self.logger.debug(f"Added sync source: {source_func.__name__}")
    
    def get_version(self, version: Optional[str] = None) -> Optional[ConfigVersion]:
        """获取配置版本
        
        Args:
            version: 版本号，None表示当前版本
            
        Returns:
            配置版本
        """
        if version is None:
            return self._versions[-1] if self._versions else None
        
        for v in self._versions:
            if v.version == version:
                return v
        
        return None
    
    def get_versions(self) -> List[ConfigVersion]:
        """获取所有版本
        
        Returns:
            版本列表
        """
        return self._versions.copy()
    
    def rollback_to_version(self, version: str):
        """回滚到指定版本
        
        Args:
            version: 版本号
        """
        target_version = self.get_version(version)
        if not target_version:
            raise ConfigurationError(f"Version {version} not found")
        
        with self._config_lock:
            old_config = copy.deepcopy(self._config)
            self._config.clear()
            self._config.update(target_version.config)
            
            # 创建回滚变更记录
            change = ConfigChange(
                key="*",
                old_value=old_config,
                new_value=target_version.config,
                change_type=ConfigChangeType.RELOADED,
                timestamp=datetime.now(),
                source=ConfigSource.MEMORY,
                version=version
            )
            
            # 通知变更
            self._notify_change(change)
            
            self.logger.info(f"Rolled back to version: {version}")
    
    def get_config_copy(self) -> Dict[str, Any]:
        """获取配置副本
        
        Returns:
            配置字典副本
        """
        with self._config_lock:
            return copy.deepcopy(self._config)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._config_lock:
            return {
                'config_items': len(self._config),
                'versions': len(self._versions),
                'current_version': self._current_version,
                'watchers': len(self._watchers),
                'global_callbacks': len(self._global_callbacks),
                'pattern_callbacks': sum(len(callbacks) for callbacks in self._change_callbacks.values()),
                'sync_enabled': self._sync_enabled,
                'sync_sources': len(self._sync_sources)
            }
    
    def _create_version(self, changes: List[ConfigChange]):
        """创建新版本
        
        Args:
            changes: 变更列表
        """
        # 生成新版本号
        version_parts = self._current_version.split('.')
        patch_version = int(version_parts[-1]) + 1
        new_version = '.'.join(version_parts[:-1] + [str(patch_version)])
        
        # 创建版本对象
        version = ConfigVersion(
            version=new_version,
            config=copy.deepcopy(self._config),
            timestamp=datetime.now(),
            checksum="",
            changes=changes
        )
        
        # 添加到版本列表
        self._versions.append(version)
        self._current_version = new_version
        
        # 限制版本数量
        if len(self._versions) > self._max_versions:
            self._versions.pop(0)
        
        self.logger.debug(f"Created config version: {new_version}")
    
    def _notify_change(self, change: ConfigChange):
        """通知配置变更
        
        Args:
            change: 变更记录
        """
        # 异步通知回调
        self._executor.submit(self._execute_callbacks, change)
    
    def _execute_callbacks(self, change: ConfigChange):
        """执行回调函数
        
        Args:
            change: 变更记录
        """
        # 全局回调
        for callback in self._global_callbacks:
            try:
                callback(change)
            except Exception as e:
                self.logger.error(f"Error in global config callback {callback.__name__}: {e}")
        
        # 模式匹配回调
        for pattern, callbacks in self._change_callbacks.items():
            if self._match_pattern(change.key, pattern):
                for callback in callbacks:
                    try:
                        callback(change)
                    except Exception as e:
                        self.logger.error(f"Error in config callback {callback.__name__}: {e}")
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """匹配键模式
        
        Args:
            key: 配置键
            pattern: 模式
            
        Returns:
            是否匹配
        """
        # 简单的通配符匹配
        if pattern == "*":
            return True
        
        if pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        
        if pattern.startswith("*"):
            return key.endswith(pattern[1:])
        
        return key == pattern
    
    def _sync_loop(self):
        """同步循环"""
        while self._sync_enabled:
            try:
                for source_func in self._sync_sources:
                    try:
                        remote_config = source_func()
                        self.update(remote_config, ConfigSource.REMOTE, notify=False, create_version=False)
                    except Exception as e:
                        self.logger.error(f"Error syncing from source {source_func.__name__}: {e}")
                
                time.sleep(self._sync_interval)
                
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                time.sleep(self._sync_interval)
    
    def __del__(self):
        """析构函数"""
        # 停止所有监控器
        for watcher in self._watchers.values():
            watcher.stop()
        
        # 停止同步
        self.disable_sync()
        
        # 关闭线程池
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)