#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB数据库模块

包含MongoDB数据库连接、管理和操作相关的所有组件:
- MongoClient: MongoDB异步客户端
- MongoManager: MongoDB管理器
- 各种数据模型
- 数据仓库
"""

from .mongo_client import MongoClient
from .mongo_manager import MongoManager
from .models import (
    DataType, Exchange, SecType, FinancialDataType,
    BaseModel, StockInfo, TradingCalendar, RealtimeQuote, TickData, 
    BarData, FinancialData, DividendData, ShareChangeData, IndexConstituent,
    MODEL_MAPPING, COLLECTION_MAPPING,
    get_model_class, create_model_instance, validate_model_data, get_collection_name
)
from .repositories import (
    BaseRepository, StockInfoRepository, TradingCalendarRepository,
    RealtimeQuoteRepository, TickDataRepository, BarDataRepository,
    FinancialDataRepository, DividendDataRepository, ShareChangeDataRepository,
    IndexConstituentRepository, RepositoryManager
)

__all__ = [
    # 客户端和管理器
    'MongoClient',
    'MongoManager',
    
    # 枚举类型
    'DataType',
    'Exchange',
    'SecType',
    'FinancialDataType',
    
    # 数据模型
    'BaseModel',
    'StockInfo',
    'TradingCalendar',
    'RealtimeQuote',
    'TickData',
    'BarData',
    'FinancialData',
    'DividendData',
    'ShareChangeData',
    'IndexConstituent',
    
    # 模型映射和工具函数
    'MODEL_MAPPING',
    'COLLECTION_MAPPING',
    'get_model_class',
    'create_model_instance',
    'validate_model_data',
    'get_collection_name',
    
    # 数据仓库
    'BaseRepository',
    'StockInfoRepository',
    'TradingCalendarRepository',
    'RealtimeQuoteRepository',
    'TickDataRepository',
    'BarDataRepository',
    'FinancialDataRepository',
    'DividendDataRepository',
    'ShareChangeDataRepository',
    'IndexConstituentRepository',
    'RepositoryManager'
]