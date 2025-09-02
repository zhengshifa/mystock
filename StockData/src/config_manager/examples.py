#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块使用示例

展示如何使用配置管理器的各种功能:
- 基础配置加载和保存
- 环境变量集成
- 动态配置更新
- 配置验证
- 配置监控和回调
"""

import os
import time
from pathlib import Path
from typing import Dict, Any

from .config_manager import ConfigManager, ConfigManagerOptions, create_config_manager
from .config_validator import ValidationRule, ValidationType
from .environment_config import EnvVarConfig, EnvironmentType


def basic_config_example():
    """基础配置管理示例"""
    print("=== 基础配置管理示例 ===")
    
    # 创建配置管理器
    config_manager = create_config_manager(
        config_dir="./config",
        env_prefix="MYSTOCK_",
        auto_reload=True
    )
    
    # 创建示例配置
    sample_config = {
        "database": {
            "host": "localhost",
            "port": 27017,
            "name": "mystock",
            "username": "admin",
            "password": "secret123"
        },
        "api": {
            "gm_token": "your_gm_token_here",
            "timeout": 30,
            "retry_count": 3
        },
        "sync": {
            "interval": 30,
            "batch_size": 1000,
            "enabled": True
        },
        "logging": {
            "level": "INFO",
            "file": "./logs/mystock.log",
            "max_size": "10MB",
            "backup_count": 5
        }
    }
    
    # 导入配置
    config_manager.import_config(sample_config, "app")
    
    # 获取配置值
    db_host = config_manager.get("database.host", namespace="app")
    api_timeout = config_manager.get("api.timeout", namespace="app")
    
    print(f"数据库主机: {db_host}")
    print(f"API超时: {api_timeout}")
    
    # 设置配置值
    config_manager.set("database.port", 27018, namespace="app", persist=True)
    
    # 获取配置信息
    config_info = config_manager.get_config_info("app")
    print(f"配置信息: {config_info}")
    
    # 导出配置
    exported_config = config_manager.export_config("app", include_metadata=True)
    print(f"导出的配置: {exported_config[:200]}...")
    
    print("基础配置管理示例完成\n")


def environment_config_example():
    """环境变量配置示例"""
    print("=== 环境变量配置示例 ===")
    
    # 设置环境变量
    os.environ["MYSTOCK_DB_HOST"] = "prod-db.example.com"
    os.environ["MYSTOCK_DB_PORT"] = "27017"
    os.environ["MYSTOCK_API_TOKEN"] = "prod_token_123"
    os.environ["MYSTOCK_DEBUG"] = "false"
    
    # 创建配置管理器
    options = ConfigManagerOptions(
        env_prefix="MYSTOCK_",
        load_env_vars=True,
        env_override=True
    )
    
    config_manager = ConfigManager(options)
    
    # 注册环境变量配置
    config_manager.add_env_var(EnvVarConfig(
        name="DB_HOST",
        config_key="database.host",
        var_type=str,
        default="localhost",
        description="数据库主机地址"
    ))
    
    config_manager.add_env_var(EnvVarConfig(
        name="DB_PORT",
        config_key="database.port",
        var_type=int,
        default=27017,
        description="数据库端口"
    ))
    
    config_manager.add_env_var(EnvVarConfig(
        name="API_TOKEN",
        config_key="api.token",
        var_type=str,
        required=True,
        sensitive=True,
        description="API访问令牌"
    ))
    
    config_manager.add_env_var(EnvVarConfig(
        name="DEBUG",
        config_key="debug",
        var_type=bool,
        default=False,
        description="调试模式"
    ))
    
    # 加载基础配置
    base_config = {
        "database": {"host": "localhost", "port": 27017},
        "api": {"timeout": 30},
        "debug": True
    }
    
    config_manager.import_config(base_config, "env_test")
    
    # 获取合并后的配置
    db_host = config_manager.get("database.host", namespace="env_test")
    db_port = config_manager.get("database.port", namespace="env_test")
    api_token = config_manager.get("api.token", namespace="env_test")
    debug_mode = config_manager.get("debug", namespace="env_test")
    
    print(f"数据库主机 (环境变量覆盖): {db_host}")
    print(f"数据库端口 (环境变量覆盖): {db_port}")
    print(f"API令牌 (环境变量): {api_token}")
    print(f"调试模式 (环境变量覆盖): {debug_mode}")
    
    print("环境变量配置示例完成\n")


def validation_example():
    """配置验证示例"""
    print("=== 配置验证示例 ===")
    
    # 创建配置管理器
    options = ConfigManagerOptions(
        validate_on_load=True,
        strict_validation=False
    )
    
    config_manager = ConfigManager(options)
    
    # 添加验证规则
    config_manager.add_validation_rule(ValidationRule(
        key="database.host",
        validation_type=ValidationType.TYPE,
        expected_type=str,
        required=True,
        description="数据库主机必须是字符串"
    ))
    
    config_manager.add_validation_rule(ValidationRule(
        key="database.port",
        validation_type=ValidationType.RANGE,
        min_value=1,
        max_value=65535,
        description="数据库端口必须在1-65535范围内"
    ))
    
    config_manager.add_validation_rule(ValidationRule(
        key="api.timeout",
        validation_type=ValidationType.RANGE,
        min_value=1,
        max_value=300,
        description="API超时必须在1-300秒范围内"
    ))
    
    config_manager.add_validation_rule(ValidationRule(
        key="logging.level",
        validation_type=ValidationType.ENUM,
        allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        description="日志级别必须是有效值"
    ))
    
    # 测试有效配置
    valid_config = {
        "database": {
            "host": "localhost",
            "port": 27017
        },
        "api": {
            "timeout": 30
        },
        "logging": {
            "level": "INFO"
        }
    }
    
    try:
        config_manager.import_config(valid_config, "valid_test")
        validation_result = config_manager.validate_config("valid_test")
        print(f"有效配置验证结果: {validation_result.is_valid}")
        if validation_result.warnings:
            print(f"警告: {validation_result.warnings}")
    except Exception as e:
        print(f"配置验证错误: {e}")
    
    # 测试无效配置
    invalid_config = {
        "database": {
            "host": 123,  # 应该是字符串
            "port": 99999  # 超出范围
        },
        "api": {
            "timeout": -5  # 负数
        },
        "logging": {
            "level": "INVALID"  # 无效枚举值
        }
    }
    
    try:
        config_manager.import_config(invalid_config, "invalid_test")
        validation_result = config_manager.validate_config("invalid_test")
        print(f"无效配置验证结果: {validation_result.is_valid}")
        if validation_result.errors:
            print(f"错误: {validation_result.errors}")
    except Exception as e:
        print(f"配置验证错误: {e}")
    
    print("配置验证示例完成\n")


def dynamic_config_example():
    """动态配置示例"""
    print("=== 动态配置示例 ===")
    
    # 创建配置管理器
    options = ConfigManagerOptions(
        enable_dynamic=True,
        auto_reload=True,
        watch_interval=1.0
    )
    
    config_manager = ConfigManager(options)
    
    # 添加配置变更回调
    def config_change_handler(key: str, old_value: Any, new_value: Any):
        print(f"配置变更: {key} = {old_value} -> {new_value}")
    
    config_manager.add_change_callback(config_change_handler)
    
    # 初始配置
    initial_config = {
        "sync": {
            "interval": 30,
            "enabled": True
        },
        "api": {
            "timeout": 30,
            "retry_count": 3
        }
    }
    
    config_manager.import_config(initial_config, "dynamic_test")
    
    print(f"初始同步间隔: {config_manager.get('sync.interval', namespace='dynamic_test')}")
    
    # 动态更新配置
    print("\n动态更新配置...")
    config_manager.set("sync.interval", 60, namespace="dynamic_test", notify=True)
    config_manager.set("api.timeout", 45, namespace="dynamic_test", notify=True)
    config_manager.set("sync.enabled", False, namespace="dynamic_test", notify=True)
    
    print(f"更新后同步间隔: {config_manager.get('sync.interval', namespace='dynamic_test')}")
    print(f"更新后API超时: {config_manager.get('api.timeout', namespace='dynamic_test')}")
    print(f"更新后同步状态: {config_manager.get('sync.enabled', namespace='dynamic_test')}")
    
    # 批量更新
    print("\n批量更新配置...")
    batch_updates = {
        "sync.interval": 120,
        "api.retry_count": 5,
        "new_feature.enabled": True
    }
    
    for key, value in batch_updates.items():
        config_manager.set(key, value, namespace="dynamic_test", notify=True)
    
    print("动态配置示例完成\n")


def file_watching_example():
    """文件监控示例"""
    print("=== 文件监控示例 ===")
    
    # 创建临时配置文件
    config_dir = Path("./temp_config")
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "watch_test.json"
    
    initial_config = {
        "app_name": "MyStock",
        "version": "1.0.0",
        "debug": False
    }
    
    # 写入初始配置
    import json
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(initial_config, f, indent=2, ensure_ascii=False)
    
    # 创建配置管理器
    options = ConfigManagerOptions(
        config_dir=config_dir,
        auto_reload=True,
        watch_interval=0.5
    )
    
    config_manager = ConfigManager(options)
    
    # 添加文件变更回调
    def file_change_handler(key: str, old_value: Any, new_value: Any):
        print(f"文件变更检测: {key} = {old_value} -> {new_value}")
    
    config_manager.add_change_callback(file_change_handler)
    
    # 加载配置文件
    config_manager.load_config(config_file, namespace="watch_test")
    
    print(f"初始应用名称: {config_manager.get('app_name', namespace='watch_test')}")
    print(f"初始版本: {config_manager.get('version', namespace='watch_test')}")
    
    # 模拟文件变更
    print("\n模拟文件变更...")
    time.sleep(1)
    
    updated_config = {
        "app_name": "MyStock Pro",
        "version": "2.0.0",
        "debug": True,
        "new_feature": "enabled"
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(updated_config, f, indent=2, ensure_ascii=False)
    
    # 等待文件监控检测到变更
    time.sleep(2)
    
    print(f"更新后应用名称: {config_manager.get('app_name', namespace='watch_test')}")
    print(f"更新后版本: {config_manager.get('version', namespace='watch_test')}")
    print(f"新功能: {config_manager.get('new_feature', namespace='watch_test')}")
    
    # 清理临时文件
    config_file.unlink()
    config_dir.rmdir()
    
    print("文件监控示例完成\n")


def advanced_features_example():
    """高级功能示例"""
    print("=== 高级功能示例 ===")
    
    # 创建配置管理器
    options = ConfigManagerOptions(
        enable_cache=True,
        cache_ttl=60,
        mask_sensitive=True,
        sensitive_keys=["password", "token", "secret", "key"]
    )
    
    config_manager = ConfigManager(options)
    
    # 多命名空间配置
    dev_config = {
        "database": {"host": "dev-db", "password": "dev_secret"},
        "api": {"token": "dev_token_123"},
        "debug": True
    }
    
    prod_config = {
        "database": {"host": "prod-db", "password": "prod_secret"},
        "api": {"token": "prod_token_456"},
        "debug": False
    }
    
    config_manager.import_config(dev_config, "development")
    config_manager.import_config(prod_config, "production")
    
    # 获取不同环境的配置
    dev_db_host = config_manager.get("database.host", namespace="development")
    prod_db_host = config_manager.get("database.host", namespace="production")
    
    print(f"开发环境数据库: {dev_db_host}")
    print(f"生产环境数据库: {prod_db_host}")
    
    # 导出脱敏配置
    dev_export = config_manager.export_config("development", include_metadata=True)
    print(f"\n开发环境导出配置 (脱敏): {dev_export}")
    
    # 配置统计信息
    all_configs = config_manager.get_all_configs()
    print(f"\n所有配置命名空间: {list(all_configs.keys())}")
    
    for namespace in all_configs.keys():
        info = config_manager.get_config_info(namespace)
        print(f"{namespace} 配置信息: {info}")
    
    # 缓存测试
    print("\n缓存性能测试...")
    start_time = time.time()
    
    # 多次获取相同配置 (应该使用缓存)
    for _ in range(1000):
        config_manager.get("database.host", namespace="development")
    
    cached_time = time.time() - start_time
    
    # 清除缓存后再次测试
    config_manager.clear_cache()
    start_time = time.time()
    
    for _ in range(1000):
        config_manager.get("database.host", namespace="development")
    
    uncached_time = time.time() - start_time
    
    print(f"缓存访问时间: {cached_time:.4f}s")
    print(f"非缓存访问时间: {uncached_time:.4f}s")
    print(f"缓存性能提升: {uncached_time/cached_time:.2f}x")
    
    print("高级功能示例完成\n")


def main():
    """运行所有示例"""
    print("配置管理模块使用示例\n")
    
    try:
        basic_config_example()
        environment_config_example()
        validation_example()
        dynamic_config_example()
        file_watching_example()
        advanced_features_example()
        
        print("所有示例运行完成!")
        
    except Exception as e:
        print(f"示例运行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()