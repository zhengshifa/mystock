#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器模块

提供多种配置格式和来源的加载功能:
- 支持JSON、YAML、TOML、INI等格式
- 支持文件、环境变量、远程配置等来源
- 配置合并和覆盖
- 配置缓存和热重载
"""

import os
import json
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
from urllib.parse import urlparse
import threading
import time

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import toml
    HAS_TOML = True
except ImportError:
    HAS_TOML = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ..utils import get_logger, ValidationError


class ConfigFormat(Enum):
    """配置格式枚举"""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"
    TOML = "toml"
    INI = "ini"
    ENV = "env"
    AUTO = "auto"  # 自动检测


class ConfigSource(Enum):
    """配置来源枚举"""
    FILE = "file"
    ENV = "env"
    REMOTE = "remote"
    DICT = "dict"
    STRING = "string"


@dataclass
class ConfigLoadOptions:
    """配置加载选项"""
    format: ConfigFormat = ConfigFormat.AUTO
    encoding: str = "utf-8"
    merge_env: bool = True  # 是否合并环境变量
    env_prefix: str = ""  # 环境变量前缀
    case_sensitive: bool = False  # 是否区分大小写
    allow_missing: bool = False  # 是否允许文件不存在
    cache_enabled: bool = True  # 是否启用缓存
    cache_ttl: int = 300  # 缓存TTL（秒）
    
    # 远程配置选项
    timeout: int = 30
    headers: Optional[Dict[str, str]] = None
    auth: Optional[tuple] = None


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, logger_name: str = "ConfigLoader"):
        self.logger = get_logger(logger_name)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # 格式解析器映射
        self._parsers = {
            ConfigFormat.JSON: self._parse_json,
            ConfigFormat.YAML: self._parse_yaml,
            ConfigFormat.YML: self._parse_yaml,
            ConfigFormat.TOML: self._parse_toml,
            ConfigFormat.INI: self._parse_ini,
            ConfigFormat.ENV: self._parse_env
        }
    
    def load(self, source: Union[str, Dict[str, Any]], 
             source_type: ConfigSource = ConfigSource.FILE,
             options: Optional[ConfigLoadOptions] = None) -> Dict[str, Any]:
        """加载配置
        
        Args:
            source: 配置源（文件路径、URL、字典等）
            source_type: 配置源类型
            options: 加载选项
            
        Returns:
            配置字典
        """
        if options is None:
            options = ConfigLoadOptions()
        
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(source, source_type, options)
            
            # 检查缓存
            if options.cache_enabled and self._is_cache_valid(cache_key, options.cache_ttl):
                self.logger.debug(f"Using cached config: {cache_key}")
                return self._cache[cache_key].copy()
            
            # 加载配置数据
            config_data = self._load_from_source(source, source_type, options)
            
            # 检测格式
            if options.format == ConfigFormat.AUTO:
                options.format = self._detect_format(source, source_type)
            
            # 解析配置
            config = self._parse_config(config_data, options.format)
            
            # 合并环境变量
            if options.merge_env:
                env_config = self._load_env_config(options.env_prefix, options.case_sensitive)
                config = self._merge_configs(config, env_config)
            
            # 缓存结果
            if options.cache_enabled:
                with self._lock:
                    self._cache[cache_key] = config.copy()
                    self._cache_timestamps[cache_key] = time.time()
            
            self.logger.info(f"Config loaded successfully from {source_type.value}: {source}")
            return config
            
        except Exception as e:
            if options.allow_missing and isinstance(e, FileNotFoundError):
                self.logger.warning(f"Config file not found, using empty config: {source}")
                return {}
            
            self.logger.error(f"Failed to load config from {source}: {e}")
            raise ValidationError(f"Config loading failed: {e}") from e
    
    def load_multiple(self, sources: List[tuple], 
                     merge_strategy: str = "deep") -> Dict[str, Any]:
        """加载多个配置源并合并
        
        Args:
            sources: 配置源列表，每个元素为(source, source_type, options)元组
            merge_strategy: 合并策略（"shallow", "deep", "override"）
            
        Returns:
            合并后的配置字典
        """
        merged_config = {}
        
        for source_info in sources:
            if len(source_info) == 2:
                source, source_type = source_info
                options = ConfigLoadOptions()
            elif len(source_info) == 3:
                source, source_type, options = source_info
            else:
                raise ValueError("Invalid source info format")
            
            try:
                config = self.load(source, source_type, options)
                
                if merge_strategy == "deep":
                    merged_config = self._deep_merge(merged_config, config)
                elif merge_strategy == "shallow":
                    merged_config.update(config)
                elif merge_strategy == "override":
                    merged_config = config
                else:
                    raise ValueError(f"Unknown merge strategy: {merge_strategy}")
                    
            except Exception as e:
                self.logger.error(f"Failed to load config from {source}: {e}")
                if not options or not options.allow_missing:
                    raise
        
        return merged_config
    
    def reload(self, source: Union[str, Dict[str, Any]], 
              source_type: ConfigSource = ConfigSource.FILE,
              options: Optional[ConfigLoadOptions] = None) -> Dict[str, Any]:
        """重新加载配置（清除缓存）"""
        if options is None:
            options = ConfigLoadOptions()
        
        cache_key = self._generate_cache_key(source, source_type, options)
        
        # 清除缓存
        with self._lock:
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
        
        return self.load(source, source_type, options)
    
    def clear_cache(self):
        """清除所有缓存"""
        with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()
        self.logger.info("Config cache cleared")
    
    def _load_from_source(self, source: Union[str, Dict[str, Any]], 
                         source_type: ConfigSource,
                         options: ConfigLoadOptions) -> Union[str, bytes, Dict[str, Any]]:
        """从配置源加载数据"""
        if source_type == ConfigSource.FILE:
            return self._load_from_file(source, options)
        elif source_type == ConfigSource.REMOTE:
            return self._load_from_remote(source, options)
        elif source_type == ConfigSource.DICT:
            return source
        elif source_type == ConfigSource.STRING:
            return source
        elif source_type == ConfigSource.ENV:
            return self._load_env_config(options.env_prefix, options.case_sensitive)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    def _load_from_file(self, file_path: str, options: ConfigLoadOptions) -> str:
        """从文件加载配置"""
        path = Path(file_path)
        
        if not path.exists():
            if options.allow_missing:
                return "{}"
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        try:
            with open(path, 'r', encoding=options.encoding) as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read config file {file_path}: {e}") from e
    
    def _load_from_remote(self, url: str, options: ConfigLoadOptions) -> str:
        """从远程URL加载配置"""
        if not HAS_REQUESTS:
            raise ImportError("requests library is required for remote config loading")
        
        try:
            response = requests.get(
                url,
                timeout=options.timeout,
                headers=options.headers or {},
                auth=options.auth
            )
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            raise IOError(f"Failed to load remote config from {url}: {e}") from e
    
    def _load_env_config(self, prefix: str = "", case_sensitive: bool = False) -> Dict[str, Any]:
        """加载环境变量配置"""
        env_config = {}
        
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            
            # 移除前缀
            config_key = key[len(prefix):] if prefix else key
            
            if not case_sensitive:
                config_key = config_key.lower()
            
            # 尝试转换值类型
            env_config[config_key] = self._convert_env_value(value)
        
        return env_config
    
    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值类型"""
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # JSON
        if value.startswith(('{', '[', '"')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 逗号分隔的列表
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        return value
    
    def _detect_format(self, source: Union[str, Dict[str, Any]], 
                      source_type: ConfigSource) -> ConfigFormat:
        """检测配置格式"""
        if source_type == ConfigSource.DICT:
            return ConfigFormat.JSON  # 字典当作JSON处理
        elif source_type == ConfigSource.ENV:
            return ConfigFormat.ENV
        
        if isinstance(source, str):
            # 根据文件扩展名检测
            if source_type == ConfigSource.FILE:
                ext = Path(source).suffix.lower()
                if ext == '.json':
                    return ConfigFormat.JSON
                elif ext in ('.yaml', '.yml'):
                    return ConfigFormat.YAML
                elif ext == '.toml':
                    return ConfigFormat.TOML
                elif ext in ('.ini', '.cfg'):
                    return ConfigFormat.INI
            
            # 根据内容检测
            content = source if source_type == ConfigSource.STRING else ""
            if content.strip().startswith(('{', '[')):
                return ConfigFormat.JSON
            elif content.strip().startswith(('[', 'title')):
                return ConfigFormat.INI
        
        # 默认JSON
        return ConfigFormat.JSON
    
    def _parse_config(self, data: Union[str, Dict[str, Any]], 
                     format: ConfigFormat) -> Dict[str, Any]:
        """解析配置数据"""
        if isinstance(data, dict):
            return data
        
        parser = self._parsers.get(format)
        if not parser:
            raise ValueError(f"Unsupported config format: {format}")
        
        return parser(data)
    
    def _parse_json(self, data: str) -> Dict[str, Any]:
        """解析JSON配置"""
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e
    
    def _parse_yaml(self, data: str) -> Dict[str, Any]:
        """解析YAML配置"""
        if not HAS_YAML:
            raise ImportError("PyYAML is required for YAML config loading")
        
        try:
            return yaml.safe_load(data) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}") from e
    
    def _parse_toml(self, data: str) -> Dict[str, Any]:
        """解析TOML配置"""
        if not HAS_TOML:
            raise ImportError("toml is required for TOML config loading")
        
        try:
            return toml.loads(data)
        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML format: {e}") from e
    
    def _parse_ini(self, data: str) -> Dict[str, Any]:
        """解析INI配置"""
        try:
            parser = configparser.ConfigParser()
            parser.read_string(data)
            
            config = {}
            for section_name in parser.sections():
                section = {}
                for key, value in parser.items(section_name):
                    section[key] = self._convert_env_value(value)
                config[section_name] = section
            
            # 如果只有一个DEFAULT section，直接返回其内容
            if len(config) == 0 and parser.defaults():
                return dict(parser.defaults())
            
            return config
            
        except configparser.Error as e:
            raise ValueError(f"Invalid INI format: {e}") from e
    
    def _parse_env(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量配置"""
        return data
    
    def _merge_configs(self, base: Dict[str, Any], 
                      override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置（深度合并）"""
        return self._deep_merge(base, override)
    
    def _deep_merge(self, base: Dict[str, Any], 
                   override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _generate_cache_key(self, source: Union[str, Dict[str, Any]], 
                           source_type: ConfigSource,
                           options: ConfigLoadOptions) -> str:
        """生成缓存键"""
        import hashlib
        
        key_parts = [
            str(source),
            source_type.value,
            options.format.value,
            options.encoding,
            str(options.merge_env),
            options.env_prefix,
            str(options.case_sensitive)
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str, ttl: int) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache:
            return False
        
        if cache_key not in self._cache_timestamps:
            return False
        
        age = time.time() - self._cache_timestamps[cache_key]
        return age < ttl


# 便利函数
def load_config(source: Union[str, Dict[str, Any]], 
               source_type: ConfigSource = ConfigSource.FILE,
               **kwargs) -> Dict[str, Any]:
    """加载配置的便利函数"""
    loader = ConfigLoader()
    options = ConfigLoadOptions(**kwargs)
    return loader.load(source, source_type, options)


def load_json_config(file_path: str, **kwargs) -> Dict[str, Any]:
    """加载JSON配置文件"""
    return load_config(file_path, ConfigSource.FILE, format=ConfigFormat.JSON, **kwargs)


def load_yaml_config(file_path: str, **kwargs) -> Dict[str, Any]:
    """加载YAML配置文件"""
    return load_config(file_path, ConfigSource.FILE, format=ConfigFormat.YAML, **kwargs)


def load_env_config(prefix: str = "", **kwargs) -> Dict[str, Any]:
    """加载环境变量配置"""
    return load_config({}, ConfigSource.ENV, env_prefix=prefix, **kwargs)