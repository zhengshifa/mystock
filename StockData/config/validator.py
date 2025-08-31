#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证器
专门负责配置的验证和检查
"""

from typing import List, Dict, Any, Tuple
from .settings import AppConfig


class ConfigValidator:
    """配置验证器类"""
    
    @staticmethod
    def validate_config(config: AppConfig) -> Tuple[bool, List[str]]:
        """
        验证配置是否有效
        
        Args:
            config: 配置实例
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 验证MongoDB配置
        mongodb_errors = ConfigValidator._validate_mongodb_config(config.mongodb)
        errors.extend(mongodb_errors)
        
        # 验证GM SDK配置
        gm_errors = ConfigValidator._validate_gm_sdk_config(config.gm_sdk)
        errors.extend(gm_errors)
        
        # 验证日志配置
        logging_errors = ConfigValidator._validate_logging_config(config.logging)
        errors.extend(logging_errors)
        
        # 验证调度器配置
        scheduler_errors = ConfigValidator._validate_scheduler_config(config.scheduler)
        errors.extend(scheduler_errors)
        
        # 验证数据配置
        data_errors = ConfigValidator._validate_data_config(config.data)
        errors.extend(data_errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_mongodb_config(mongodb_config) -> List[str]:
        """验证MongoDB配置"""
        errors = []
        
        if mongodb_config.url:
            # 如果提供了URL，验证URL格式
            if not mongodb_config.url.startswith("mongodb://"):
                errors.append("MongoDB URL必须以'mongodb://'开头")
        else:
            # 验证分离式配置
            if not mongodb_config.host:
                errors.append("MongoDB主机地址不能为空")
            
            if not isinstance(mongodb_config.port, int) or mongodb_config.port <= 0:
                errors.append("MongoDB端口必须是正整数")
            
            if not mongodb_config.database:
                errors.append("MongoDB数据库名不能为空")
        
        return errors
    
    @staticmethod
    def _validate_gm_sdk_config(gm_config) -> List[str]:
        """验证GM SDK配置"""
        errors = []
        
        if not gm_config.token or gm_config.token == "your_gm_token_here":
            errors.append("请设置有效的GM SDK token")
        
        if not gm_config.endpoint:
            errors.append("GM SDK端点不能为空")
        
        return errors
    
    @staticmethod
    def _validate_logging_config(logging_config) -> List[str]:
        """验证日志配置"""
        errors = []
        
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if logging_config.level.upper() not in valid_levels:
            errors.append(f"日志级别必须是以下之一: {', '.join(valid_levels)}")
        
        if logging_config.max_file_size <= 0:
            errors.append("日志文件最大大小必须大于0")
        
        if logging_config.backup_count < 0:
            errors.append("日志备份文件数量不能为负数")
        
        return errors
    
    @staticmethod
    def _validate_scheduler_config(scheduler_config) -> List[str]:
        """验证调度器配置"""
        errors = []
        
        # 验证时间格式
        time_fields = [
            ("market_open_time", scheduler_config.market_open_time),
            ("market_close_time", scheduler_config.market_close_time),
            ("lunch_break_start", scheduler_config.lunch_break_start),
            ("lunch_break_end", scheduler_config.lunch_break_end)
        ]
        
        for field_name, time_value in time_fields:
            if not ConfigValidator._is_valid_time_format(time_value):
                errors.append(f"{field_name} 时间格式无效，应为HH:MM格式")
        
        # 验证间隔时间
        if scheduler_config.realtime_interval <= 0:
            errors.append("实时数据采集间隔必须大于0")
        
        if scheduler_config.minute_interval <= 0:
            errors.append("分钟数据采集间隔必须大于0")
        
        if scheduler_config.daily_interval <= 0:
            errors.append("日线数据采集间隔必须大于0")
        
        # 验证重试配置
        if scheduler_config.max_retries < 0:
            errors.append("最大重试次数不能为负数")
        
        if scheduler_config.retry_delay < 0:
            errors.append("重试延迟不能为负数")
        
        # 验证股票代码
        if scheduler_config.stock_symbols:
            for code in scheduler_config.stock_symbols:
                if not ConfigValidator._is_valid_stock_code(code):
                    errors.append(f"无效的股票代码格式: {code}")
        
        return errors
    
    @staticmethod
    def _validate_data_config(data_config) -> List[str]:
        """验证数据配置"""
        errors = []
        
        # 验证集合名称
        for collection_name in data_config.collections.values():
            if not collection_name or not isinstance(collection_name, str):
                errors.append(f"数据集合名称无效: {collection_name}")
        
        # 验证数据保留天数
        for collection_name, retention_days in data_config.data_retention_days.items():
            if not isinstance(retention_days, int) or retention_days <= 0:
                errors.append(f"数据保留天数无效 {collection_name}: {retention_days}")
        
        return errors
    
    @staticmethod
    def _is_valid_time_format(time_str: str) -> bool:
        """验证时间格式是否为HH:MM"""
        try:
            if not isinstance(time_str, str):
                return False
            
            parts = time_str.split(":")
            if len(parts) != 2:
                return False
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def _is_valid_stock_code(code: str) -> bool:
        """验证股票代码格式"""
        if not isinstance(code, str):
            return False
        
        # 支持GM格式: SHSE.xxxxx 或 SZSE.xxxxx
        if code.startswith(("SHSE.", "SZSE.")):
            return True
        
        # 支持传统格式: xxxxx.SH 或 xxxxx.SZ
        if "." in code:
            parts = code.split(".")
            if len(parts) == 2 and parts[1] in ["SH", "SZ"]:
                return True
        
        return False
    
    @staticmethod
    def get_config_summary(config: AppConfig) -> Dict[str, Any]:
        """
        获取配置摘要信息
        
        Args:
            config: 配置实例
            
        Returns:
            配置摘要字典
        """
        is_valid, errors = ConfigValidator.validate_config(config)
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "mongodb": {
                "host": config.mongodb.host,
                "port": config.mongodb.port,
                "database": config.mongodb.database,
                "has_auth": bool(config.mongodb.username and config.mongodb.password),
                "has_url": bool(config.mongodb.url)
            },
            "gm_sdk": {
                "endpoint": config.gm_sdk.endpoint,
                "token_configured": config.gm_sdk.token != "your_gm_token_here"
            },
            "logging": {
                "level": config.logging.level,
                "log_dir": config.logging.log_dir,
                "max_file_size_mb": round(config.logging.max_file_size / 1024 / 1024, 2)
            },
            "scheduler": {
                "realtime_interval": config.scheduler.realtime_interval,
                "stock_count": len(config.scheduler.stock_symbols) if config.scheduler.stock_symbols else 0,
                "trading_hours": config.scheduler.trading_hours
            }
        }
