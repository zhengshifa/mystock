#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据采集系统
重构后的模块化架构，按数据类型和功能分类组织
"""

# 导入主要模块
from .market_data import TickDataCollector, BarDataCollector, MarketDataAnalyzer
from .fundamentals import FundamentalsDataCollector
from .realtime import RealtimeDataCollector
from .scheduler import TaskScheduler, StockDataInterface
from .services import data_model_service

# 主系统类
from .main import StockDataSystem

__all__ = [
    # 市场数据模块
    'TickDataCollector',
    'BarDataCollector', 
    'MarketDataAnalyzer',
    
    # 基本面数据模块
    'FundamentalsDataCollector',
    
    # 实时数据模块
    'RealtimeDataCollector',
    
    # 调度器模块
    'TaskScheduler',
    'StockDataInterface',
    
    # 服务模块
    'data_model_service',
    
    # 主系统
    'StockDataSystem'
]

__version__ = "2.0.0"
__author__ = "StockData Team"
__description__ = "重构后的股票数据采集系统，采用模块化架构设计"