#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场数据模型
包含行情、交易等市场相关数据的数据模型
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import Field

from .base import TimestampedModel


class QuoteLevel(TimestampedModel):
    """买卖档位报价数据模型"""
    
    bid_p: float = Field(0.0, description="买价")
    bid_v: int = Field(0, description="买量")
    ask_p: float = Field(0.0, description="卖价")
    ask_v: int = Field(0, description="卖量")
    bid_q: Optional[Dict[str, Any]] = Field(None, description="委买队列，仅level2行情支持")
    ask_q: Optional[Dict[str, Any]] = Field(None, description="委卖队列，仅level2行情支持")


class Tick(TimestampedModel):
    """Tick数据模型 - 逐笔行情数据
    
    掘金量化SDK的Tick对象，包含分笔成交数据
    股票频率为3s, 期货为0.5s, 指数5s
    """
    
    symbol: str = Field(..., description="标的代码")
    open: float = Field(0.0, description="日线开盘价")
    high: float = Field(0.0, description="日线最高价")
    low: float = Field(0.0, description="日线最低价")
    price: float = Field(0.0, description="最新价")
    cum_volume: int = Field(0, description="成交总量/最新成交量,累计值（日线成交量）")
    cum_amount: float = Field(0.0, description="成交总金额/最新成交额,累计值（日线成交金额）")
    cum_position: int = Field(0, description="合约持仓量(只适用于期货),累计值（股票此值为0）")
    trade_type: int = Field(0, description="交易类型（只适用于期货）")
    last_volume: int = Field(0, description="瞬时成交量")
    last_amount: float = Field(0.0, description="瞬时成交额（郑商所last_amount为0）")
    quotes: List[QuoteLevel] = Field(default_factory=list, description="买卖档位数据")
    
    # 计算字段
    change: Optional[float] = Field(None, description="价格变化")
    change_pct: Optional[float] = Field(None, description="价格变化百分比")
    vwap: Optional[float] = Field(None, description="成交量加权平均价")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._calculate_derived_fields()
    
    def _calculate_derived_fields(self):
        """计算派生字段"""
        # 计算价格变化（如果有前收盘价）
        if hasattr(self, 'pre_close') and self.pre_close and self.price:
            self.change = self.price - self.pre_close
            self.change_pct = (self.change / self.pre_close) * 100 if self.pre_close > 0 else 0
        
        # 计算VWAP
        if self.cum_volume > 0:
            self.vwap = self.cum_amount / self.cum_volume
        else:
            self.vwap = self.price
    
    def get_bid_ask_spread(self) -> float:
        """获取买卖价差"""
        if self.quotes and len(self.quotes) > 0:
            first_quote = self.quotes[0]
            if first_quote.ask_p > 0 and first_quote.bid_p > 0:
                return first_quote.ask_p - first_quote.bid_p
        return 0.0
    
    def get_total_bid_volume(self) -> int:
        """获取总买量"""
        return sum(q.bid_v for q in self.quotes if q.bid_v > 0)
    
    def get_total_ask_volume(self) -> int:
        """获取总卖量"""
        return sum(q.ask_v for q in self.quotes if q.ask_v > 0)
    
    def get_bid_ask_ratio(self) -> float:
        """获取买卖比例"""
        total_bid = self.get_total_bid_volume()
        total_ask = self.get_total_ask_volume()
        return total_bid / total_ask if total_ask > 0 else 0.0


class Bar(TimestampedModel):
    """Bar数据模型 - K线数据"""
    
    symbol: str = Field(..., description="标的代码")
    frequency: str = Field(..., description="频率")
    open: float = Field(0.0, description="开盘价")
    high: float = Field(0.0, description="最高价")
    low: float = Field(0.0, description="最低价")
    close: float = Field(0.0, description="收盘价")
    volume: int = Field(0, description="成交量")
    amount: float = Field(0.0, description="成交额")
    bob: datetime = Field(..., description="Bar开始时间")
    eob: datetime = Field(..., description="Bar结束时间")
    position: Optional[int] = Field(None, description="持仓量（期货）")
    
    # 计算字段
    change: Optional[float] = Field(None, description="价格变化")
    change_pct: Optional[float] = Field(None, description="价格变化百分比")
    amplitude: Optional[float] = Field(None, description="振幅")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._calculate_derived_fields()
    
    def _calculate_derived_fields(self):
        """计算派生字段"""
        # 计算价格变化
        if self.open > 0:
            self.change = self.close - self.open
            self.change_pct = (self.change / self.open) * 100 if self.open > 0 else 0
        
        # 计算振幅
        if self.open > 0:
            self.amplitude = ((self.high - self.low) / self.open) * 100


class MarketDataSummary(TimestampedModel):
    """市场数据摘要"""
    
    symbol: str = Field(..., description="标的代码")
    last_price: float = Field(0.0, description="最新价格")
    change: float = Field(0.0, description="价格变化")
    change_pct: float = Field(0.0, description="价格变化百分比")
    volume: int = Field(0, description="成交量")
    amount: float = Field(0.0, description="成交额")
    high: float = Field(0.0, description="最高价")
    low: float = Field(0.0, description="最低价")
    open: float = Field(0.0, description="开盘价")
    pre_close: float = Field(0.0, description="前收盘价")
    timestamp: datetime = Field(default_factory=datetime.now, description="数据时间戳")
