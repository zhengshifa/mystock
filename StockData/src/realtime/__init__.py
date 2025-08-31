#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时数据模块
提供实时行情数据的采集、存储和管理功能
"""

from .realtime_collector import RealtimeDataCollector

__all__ = [
    'RealtimeDataCollector'
]
