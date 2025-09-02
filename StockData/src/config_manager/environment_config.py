#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置模块

提供环境变量管理功能:
- 环境变量读取和设置
- 类型转换和默认值
- 环境配置验证
- 配置文件与环境变量合并
- 敏感信息处理
"""

import os
import sys
from typing import Dict, Any, Optional, Union, Type, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import json
from urllib.parse import urlparse

from ..utils import get_logger, ConfigurationError


class EnvironmentType(Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class EnvVarConfig:
    """环境变量配置"""
    name: str  # 环境变量名
    default: Any = None  # 默认值
    var_type: Type = str  # 变量类型
    required: bool = False  # 是否必需
    description: str = ""  # 描述
    sensitive: bool = False  # 是否敏感信息
    validator: Optional[Callable[[Any], bool]] = None  # 验证函数
    transformer: Optional[Callable[[str], Any]] = None  # 转换函数
    choices: Optional[List[Any]] = None  # 可选值列表
    
    def __post_init__(self):
        """初始化后处理"""
        if self.transformer is None:
            self.transformer = self._get_default_transformer()
    
    def _get_default_transformer(self) -> Callable[[str], Any]:
        """获取默认转换函数"""
        if self.var_type == bool:
            return lambda x: x.lower() in ('true', '1', 'yes', 'on')
        elif self.var_type == int:
            return int
        elif self.var_type == float:
            return float
        elif self.var_type == list:
            return lambda x: [item.strip() for item in x.split(',') if item.strip()]
        elif self.var_type == dict:
            return json.loads
        else:
            return str


class EnvironmentConfig:
    """环境配置管理器"""
    
    def __init__(self, env_prefix: str = "", logger_name: str = "EnvironmentConfig"):
        """
        初始化环境配置管理器
        
        Args:
            env_prefix: 环境变量前缀
            logger_name: 日志器名称
        """
        self.env_prefix = env_prefix
        self.logger = get_logger(logger_name)
        self.env_vars: Dict[str, EnvVarConfig] = {}
        self.loaded_config: Dict[str, Any] = {}
        
        # 自动检测环境类型
        self.environment = self._detect_environment()
        self.logger.info(f"Detected environment: {self.environment.value}")
    
    def register_env_var(self, config: EnvVarConfig):
        """注册环境变量配置
        
        Args:
            config: 环境变量配置
        """
        self.env_vars[config.name] = config
        self.logger.debug(f"Registered environment variable: {config.name}")
    
    def register_env_vars(self, configs: List[EnvVarConfig]):
        """批量注册环境变量配置
        
        Args:
            configs: 环境变量配置列表
        """
        for config in configs:
            self.register_env_var(config)
    
    def load_config(self, validate: bool = True) -> Dict[str, Any]:
        """加载环境配置
        
        Args:
            validate: 是否验证配置
            
        Returns:
            加载的配置字典
        """
        config = {}
        missing_required = []
        
        for var_name, var_config in self.env_vars.items():
            try:
                # 构建完整的环境变量名
                full_var_name = f"{self.env_prefix}{var_name}" if self.env_prefix else var_name
                
                # 获取环境变量值
                raw_value = os.getenv(full_var_name)
                
                if raw_value is None:
                    if var_config.required:
                        missing_required.append(full_var_name)
                        continue
                    else:
                        config[var_name] = var_config.default
                        continue
                
                # 转换值
                try:
                    converted_value = var_config.transformer(raw_value)
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    self.logger.error(f"Failed to convert {full_var_name}={raw_value}: {e}")
                    raise ConfigurationError(f"Invalid value for {full_var_name}: {e}")
                
                # 验证值
                if validate:
                    if var_config.choices and converted_value not in var_config.choices:
                        raise ConfigurationError(
                            f"{full_var_name} must be one of {var_config.choices}, got {converted_value}"
                        )
                    
                    if var_config.validator and not var_config.validator(converted_value):
                        raise ConfigurationError(f"Validation failed for {full_var_name}={converted_value}")
                
                config[var_name] = converted_value
                
                # 记录日志（敏感信息脱敏）
                log_value = "***" if var_config.sensitive else converted_value
                self.logger.debug(f"Loaded {full_var_name}={log_value}")
                
            except Exception as e:
                self.logger.error(f"Error loading environment variable {var_name}: {e}")
                raise
        
        # 检查必需的环境变量
        if missing_required:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing_required)}"
            )
        
        self.loaded_config = config
        self.logger.info(f"Loaded {len(config)} environment variables")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        if not self.loaded_config:
            self.load_config()
        
        return self.loaded_config.get(key, default)
    
    def set_env_var(self, name: str, value: str, override: bool = True):
        """设置环境变量
        
        Args:
            name: 变量名
            value: 变量值
            override: 是否覆盖已存在的变量
        """
        full_name = f"{self.env_prefix}{name}" if self.env_prefix else name
        
        if not override and full_name in os.environ:
            self.logger.debug(f"Environment variable {full_name} already exists, skipping")
            return
        
        os.environ[full_name] = str(value)
        self.logger.debug(f"Set environment variable {full_name}")
    
    def unset_env_var(self, name: str):
        """删除环境变量
        
        Args:
            name: 变量名
        """
        full_name = f"{self.env_prefix}{name}" if self.env_prefix else name
        
        if full_name in os.environ:
            del os.environ[full_name]
            self.logger.debug(f"Unset environment variable {full_name}")
    
    def load_from_file(self, file_path: Union[str, Path], 
                      override: bool = False, encoding: str = 'utf-8'):
        """从文件加载环境变量
        
        Args:
            file_path: 文件路径
            override: 是否覆盖已存在的变量
            encoding: 文件编码
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.warning(f"Environment file not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析键值对
                    if '=' not in line:
                        self.logger.warning(f"Invalid line {line_num} in {file_path}: {line}")
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 移除引号
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # 设置环境变量
                    if override or key not in os.environ:
                        os.environ[key] = value
                        self.logger.debug(f"Loaded from file: {key}")
            
            self.logger.info(f"Loaded environment variables from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading environment file {file_path}: {e}")
            raise ConfigurationError(f"Failed to load environment file: {e}")
    
    def save_to_file(self, file_path: Union[str, Path], 
                    include_sensitive: bool = False, encoding: str = 'utf-8'):
        """保存环境变量到文件
        
        Args:
            file_path: 文件路径
            include_sensitive: 是否包含敏感信息
            encoding: 文件编码
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(f"# Environment configuration\n")
                f.write(f"# Generated automatically\n\n")
                
                for var_name, var_config in self.env_vars.items():
                    if var_config.sensitive and not include_sensitive:
                        continue
                    
                    full_name = f"{self.env_prefix}{var_name}" if self.env_prefix else var_name
                    value = os.getenv(full_name, var_config.default or "")
                    
                    # 添加描述
                    if var_config.description:
                        f.write(f"# {var_config.description}\n")
                    
                    # 写入键值对
                    f.write(f"{full_name}={value}\n\n")
            
            self.logger.info(f"Saved environment variables to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving environment file {file_path}: {e}")
            raise ConfigurationError(f"Failed to save environment file: {e}")
    
    def merge_with_config(self, config: Dict[str, Any], 
                         env_override: bool = True) -> Dict[str, Any]:
        """合并环境配置与普通配置
        
        Args:
            config: 普通配置字典
            env_override: 环境变量是否覆盖配置文件
            
        Returns:
            合并后的配置
        """
        if not self.loaded_config:
            self.load_config()
        
        merged = config.copy()
        
        if env_override:
            merged.update(self.loaded_config)
        else:
            for key, value in self.loaded_config.items():
                if key not in merged:
                    merged[key] = value
        
        self.logger.debug(f"Merged configuration with {len(self.loaded_config)} environment variables")
        return merged
    
    def validate_environment(self) -> List[str]:
        """验证环境配置
        
        Returns:
            验证错误列表
        """
        errors = []
        
        for var_name, var_config in self.env_vars.items():
            full_name = f"{self.env_prefix}{var_name}" if self.env_prefix else var_name
            value = os.getenv(full_name)
            
            # 检查必需变量
            if var_config.required and value is None:
                errors.append(f"Missing required environment variable: {full_name}")
                continue
            
            if value is not None:
                try:
                    # 转换和验证
                    converted_value = var_config.transformer(value)
                    
                    if var_config.choices and converted_value not in var_config.choices:
                        errors.append(
                            f"{full_name} must be one of {var_config.choices}, got {converted_value}"
                        )
                    
                    if var_config.validator and not var_config.validator(converted_value):
                        errors.append(f"Validation failed for {full_name}={converted_value}")
                        
                except Exception as e:
                    errors.append(f"Invalid value for {full_name}: {e}")
        
        return errors
    
    def get_environment_info(self) -> Dict[str, Any]:
        """获取环境信息
        
        Returns:
            环境信息字典
        """
        return {
            'environment': self.environment.value,
            'python_version': sys.version,
            'platform': sys.platform,
            'env_prefix': self.env_prefix,
            'registered_vars': len(self.env_vars),
            'loaded_vars': len(self.loaded_config),
            'required_vars': sum(1 for config in self.env_vars.values() if config.required),
            'sensitive_vars': sum(1 for config in self.env_vars.values() if config.sensitive)
        }
    
    def _detect_environment(self) -> EnvironmentType:
        """自动检测环境类型"""
        # 检查常见的环境变量
        env_indicators = {
            'NODE_ENV': {
                'development': EnvironmentType.DEVELOPMENT,
                'dev': EnvironmentType.DEVELOPMENT,
                'test': EnvironmentType.TESTING,
                'testing': EnvironmentType.TESTING,
                'staging': EnvironmentType.STAGING,
                'stage': EnvironmentType.STAGING,
                'production': EnvironmentType.PRODUCTION,
                'prod': EnvironmentType.PRODUCTION
            },
            'ENVIRONMENT': {
                'development': EnvironmentType.DEVELOPMENT,
                'testing': EnvironmentType.TESTING,
                'staging': EnvironmentType.STAGING,
                'production': EnvironmentType.PRODUCTION,
                'local': EnvironmentType.LOCAL
            },
            'ENV': {
                'dev': EnvironmentType.DEVELOPMENT,
                'test': EnvironmentType.TESTING,
                'stage': EnvironmentType.STAGING,
                'prod': EnvironmentType.PRODUCTION
            }
        }
        
        for env_var, mappings in env_indicators.items():
            value = os.getenv(env_var, '').lower()
            if value in mappings:
                return mappings[value]
        
        # 检查是否在CI环境
        ci_vars = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL']
        if any(os.getenv(var) for var in ci_vars):
            return EnvironmentType.TESTING
        
        # 默认为开发环境
        return EnvironmentType.DEVELOPMENT
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == EnvironmentType.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment == EnvironmentType.TESTING
    
    def is_staging(self) -> bool:
        """是否为预发布环境"""
        return self.environment == EnvironmentType.STAGING
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == EnvironmentType.PRODUCTION


# 便利函数
def create_env_config(name: str, default: Any = None, var_type: Type = str,
                     required: bool = False, description: str = "",
                     sensitive: bool = False, choices: Optional[List[Any]] = None) -> EnvVarConfig:
    """创建环境变量配置
    
    Args:
        name: 变量名
        default: 默认值
        var_type: 变量类型
        required: 是否必需
        description: 描述
        sensitive: 是否敏感
        choices: 可选值列表
        
    Returns:
        环境变量配置
    """
    return EnvVarConfig(
        name=name,
        default=default,
        var_type=var_type,
        required=required,
        description=description,
        sensitive=sensitive,
        choices=choices
    )


def load_dotenv(file_path: Union[str, Path] = '.env', override: bool = False):
    """加载.env文件
    
    Args:
        file_path: .env文件路径
        override: 是否覆盖已存在的变量
    """
    env_config = EnvironmentConfig()
    env_config.load_from_file(file_path, override=override)


# 常用环境变量配置
COMMON_ENV_CONFIGS = [
    # 应用配置
    create_env_config('APP_NAME', 'MyStockApp', str, description='应用名称'),
    create_env_config('APP_VERSION', '1.0.0', str, description='应用版本'),
    create_env_config('DEBUG', False, bool, description='调试模式'),
    create_env_config('LOG_LEVEL', 'INFO', str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], description='日志级别'),
    
    # 服务器配置
    create_env_config('HOST', '0.0.0.0', str, description='服务器主机'),
    create_env_config('PORT', 8000, int, description='服务器端口'),
    
    # 数据库配置
    create_env_config('DB_HOST', 'localhost', str, description='数据库主机'),
    create_env_config('DB_PORT', 27017, int, description='数据库端口'),
    create_env_config('DB_NAME', 'mystock', str, description='数据库名称'),
    create_env_config('DB_USER', '', str, description='数据库用户名'),
    create_env_config('DB_PASSWORD', '', str, sensitive=True, description='数据库密码'),
    
    # API配置
    create_env_config('API_KEY', '', str, required=True, sensitive=True, description='API密钥'),
    create_env_config('API_SECRET', '', str, required=True, sensitive=True, description='API密钥'),
    create_env_config('API_TIMEOUT', 30, int, description='API超时时间(秒)'),
    
    # 缓存配置
    create_env_config('REDIS_HOST', 'localhost', str, description='Redis主机'),
    create_env_config('REDIS_PORT', 6379, int, description='Redis端口'),
    create_env_config('REDIS_PASSWORD', '', str, sensitive=True, description='Redis密码'),
]