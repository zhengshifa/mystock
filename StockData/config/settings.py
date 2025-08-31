#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置定义模块
提供项目所有配置的数据结构定义
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

@dataclass
class MongoDBConfig:
    """MongoDB配置"""
    host: str = "localhost"
    port: int = 27017
    database: str = "stock_data"
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None  # 支持完整的MongoDB URL
    
    def __post_init__(self):
        """初始化后处理，从URL中提取数据库名"""
        if self.url:
            self._extract_database_from_url()
    
    def _extract_database_from_url(self):
        """从MongoDB URL中提取数据库名"""
        try:
            # 解析URL格式: mongodb://[username:password@]host:port/database[?options]
            if '/' in self.url:
                # 找到最后一个'/'后的部分
                url_parts = self.url.split('/')
                if len(url_parts) >= 4:  # mongodb://host:port/database
                    db_part = url_parts[3]  # 获取database部分
                    # 移除查询参数（如果有的话）
                    if '?' in db_part:
                        db_part = db_part.split('?')[0]
                    if db_part:  # 确保数据库名不为空
                        self.database = db_part
        except Exception:
            # 如果解析失败，保持默认数据库名
            pass
    
    @property
    def connection_string(self) -> str:
        """获取MongoDB连接字符串"""
        # 如果提供了完整的URL，直接使用
        if self.url:
            return self.url
        
        # 否则使用传统的分离式配置构建URL
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"mongodb://{self.host}:{self.port}/{self.database}"

@dataclass
class GMSDKConfig:
    """掘金量化SDK配置"""
    token: str = "your_gm_token_here"
    endpoint: str = "api.myquant.cn:9000"
    
@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_dir: str = str(PROJECT_ROOT / "logs")
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
@dataclass
class SchedulerConfig:
    """调度器配置"""
    # 交易时间配置
    market_open_time: str = "09:30"
    market_close_time: str = "15:00"
    lunch_break_start: str = "11:30"
    lunch_break_end: str = "13:00"
    
    # 数据采集间隔（秒）
    realtime_interval: int = 3
    minute_interval: int = 60
    daily_interval: int = 3600
    
    # 重试配置
    max_retries: int = 3
    retry_delay: int = 5
    
    # 股票代码列表
    stock_symbols: List[str] = field(default_factory=lambda: [
        "SZSE.000001",  # 平安银行
        "SZSE.000002",  # 万科A
        "SHSE.600000",  # 浦发银行
        "SHSE.600036",  # 招商银行
        "SHSE.600519",  # 贵州茅台
    ])
    
    # 交易时间段配置 (上午, 下午)
    trading_hours: List[List[str]] = field(default_factory=lambda: None)
    
    # 节假日列表
    holidays: List[str] = field(default_factory=lambda: [
        "2024-01-01",  # 元旦
        "2024-02-10",  # 春节
        "2024-02-11",
        "2024-02-12",
        "2024-02-13",
        "2024-02-14",
        "2024-02-15",
        "2024-02-16",
        "2024-02-17",
        "2024-04-04",  # 清明节
        "2024-04-05",
        "2024-04-06",
        "2024-05-01",  # 劳动节
        "2024-05-02",
        "2024-05-03",
        "2024-06-10",  # 端午节
        "2024-09-15",  # 中秋节
        "2024-09-16",
        "2024-09-17",
        "2024-10-01",  # 国庆节
        "2024-10-02",
        "2024-10-03",
        "2024-10-04",
        "2024-10-05",
        "2024-10-06",
        "2024-10-07",
    ])
    
    def __post_init__(self):
        """初始化后处理"""
        if self.trading_hours is None:
            self.trading_hours = [
                [self.market_open_time, self.lunch_break_start],  # 上午时段
                [self.lunch_break_end, self.market_close_time]    # 下午时段
            ]

@dataclass
class DataConfig:
    """数据配置"""
    
    # 数据集合名称
    collections = {
        "realtime_quotes": "realtime_quotes",
        "minute_kline": "minute_kline", 
        "daily_kline": "daily_kline",
        "tick_data": "tick_data",
        "market_status": "market_status",
        # 基本面数据集合
        "fundamentals_balance": "fundamentals_balance",
        "fundamentals_income": "fundamentals_income",
        "fundamentals_cashflow": "fundamentals_cashflow"
    }
    
    # 数据保留天数
    data_retention_days = {
        "realtime_quotes": 7,
        "minute_kline": 30,
        "daily_kline": 365,
        "tick_data": 3,
        "market_status": 30,
        # 基本面数据保留时间（更长，因为更新频率低）
        "fundamentals_balance": 1095,  # 3年
        "fundamentals_income": 1095,   # 3年
        "fundamentals_cashflow": 1095  # 3年
    }
    
    # 基本面数据集合属性（便于访问）
    @property
    def fundamentals_balance_collection(self) -> str:
        return self.collections["fundamentals_balance"]
    
    @property
    def fundamentals_income_collection(self) -> str:
        return self.collections["fundamentals_income"]
    
    @property
    def fundamentals_cashflow_collection(self) -> str:
        return self.collections["fundamentals_cashflow"]
    
    @property
    def fundamentals_retention_days(self) -> int:
        """获取基本面数据保留天数（统一使用3年）"""
        return 1095

class AppConfig:
    """应用配置管理类"""
    
    def __init__(self):
        """初始化配置"""
        self.mongodb = MongoDBConfig()
        self.gm_sdk = GMSDKConfig()
        self.logging = LoggingConfig()
        self.scheduler = SchedulerConfig()
        self.data = DataConfig()
    
    def get_log_file_path(self, log_name: str) -> str:
        """获取日志文件路径"""
        return os.path.join(self.logging.log_dir, f"{log_name}.log")
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        if self.gm_sdk.token == "your_gm_token_here":
            print("警告: 请设置有效的GM SDK token")
            return False
        return True