#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据模型
定义股票相关的所有数据结构
"""

from pydantic import Field, field_validator
from typing import List, Optional, Union
from datetime import datetime
from decimal import Decimal

from .base import TimestampedModel, IdentifiableModel, AppBaseModel


class BidAskQuote(AppBaseModel):
    """买卖盘口数据模型"""
    
    bid_p: float = Field(..., description="买入价格", ge=0)
    bid_v: int = Field(..., description="买入数量", ge=0)
    ask_p: float = Field(..., description="卖出价格", ge=0)
    ask_v: int = Field(..., description="卖出数量", ge=0)
    level: int = Field(1, description="档位级别", ge=1, le=10)
    
    @field_validator('ask_p')
    @classmethod
    def ask_price_must_be_higher_than_bid(cls, v, info):
        """验证卖价必须高于买价"""
        if 'bid_p' in info.data and v <= info.data['bid_p']:
            raise ValueError('卖价必须高于买价')
        return v


class StockQuote(AppBaseModel):
    """股票基础行情数据模型"""
    
    symbol: str = Field(..., description="股票代码", min_length=1)
    open: float = Field(..., description="开盘价", ge=0)
    high: float = Field(..., description="最高价", ge=0)
    low: float = Field(..., description="最低价", ge=0)
    price: float = Field(..., description="当前价格", ge=0)
    pre_close: float = Field(..., description="昨收价", ge=0)
    cum_volume: int = Field(..., description="累计成交量", ge=0)
    cum_amount: float = Field(..., description="累计成交额", ge=0)
    last_volume: int = Field(0, description="最新成交量", ge=0)
    last_amount: float = Field(0, description="最新成交额", ge=0)
    trade_type: int = Field(0, description="交易类型")
    
    # 计算字段
    change: Optional[float] = Field(None, description="涨跌额")
    change_pct: Optional[float] = Field(None, description="涨跌幅(%)")
    
    @field_validator('change', 'change_pct', mode='before')
    @classmethod
    def calculate_change_fields(cls, v, info):
        """计算涨跌额和涨跌幅"""
        if 'price' in info.data and 'pre_close' in info.data:
            if info.data['pre_close'] > 0:
                change = info.data['price'] - info.data['pre_close']
                change_pct = (change / info.data['pre_close']) * 100
                return change_pct if 'change_pct' in info.data else change
        return v


class FullStockData(TimestampedModel):
    """完整股票数据模型"""
    
    quote: StockQuote = Field(..., description="基础行情数据")
    quotes: List[BidAskQuote] = Field(default_factory=list, description="五档买卖盘数据")
    
    # 技术指标
    vwap: Optional[float] = Field(None, description="成交量加权平均价", ge=0)
    total_bid_volume: Optional[int] = Field(None, description="总买入量", ge=0)
    total_ask_volume: Optional[int] = Field(None, description="总卖出量", ge=0)
    bid_ask_ratio: Optional[float] = Field(None, description="买卖比例", ge=0)
    
    @field_validator('total_bid_volume', 'total_ask_volume', mode='before')
    @classmethod
    def calculate_volume_totals(cls, v, info):
        """计算总买卖量"""
        if 'quotes' in info.data:
            quotes = info.data['quotes']
            if 'total_bid_volume' not in info.data:
                total_bid = sum(q.bid_v for q in quotes)
                return total_bid
            elif 'total_ask_volume' not in info.data:
                total_ask = sum(q.ask_v for q in quotes)
                return total_ask
        return v
    
    @field_validator('bid_ask_ratio', mode='before')
    @classmethod
    def calculate_bid_ask_ratio(cls, v, info):
        """计算买卖比例"""
        if 'total_bid_volume' in info.data and 'total_ask_volume' in info.data:
            total_bid = info.data['total_bid_volume']
            total_ask = info.data['total_ask_volume']
            if total_ask > 0:
                return total_bid / total_ask
        return v
    
    @field_validator('vwap', mode='before')
    @classmethod
    def calculate_vwap(cls, v, info):
        """计算VWAP"""
        if 'quote' in info.data:
            quote = info.data['quote']
            if quote.cum_volume > 0 and quote.cum_amount > 0:
                return quote.cum_amount / quote.cum_volume
        return v


class StockTickData(TimestampedModel):
    """股票逐笔数据模型"""
    
    symbol: str = Field(..., description="股票代码")
    price: float = Field(..., description="成交价格", ge=0)
    volume: int = Field(..., description="成交数量", ge=0)
    amount: float = Field(..., description="成交金额", ge=0)
    trade_type: int = Field(..., description="交易类型")
    trade_time: datetime = Field(..., description="成交时间")
    
    # 可选字段
    bid_order_id: Optional[str] = Field(None, description="买方订单ID")
    ask_order_id: Optional[str] = Field(None, description="卖方订单ID")
    trade_id: Optional[str] = Field(None, description="成交ID")


class StockKlineData(TimestampedModel):
    """股票K线数据模型"""
    
    symbol: str = Field(..., description="股票代码")
    period: str = Field(..., description="周期类型", pattern="^(1m|5m|15m|30m|1h|1d|1w|1M)$")
    open_time: datetime = Field(..., description="开盘时间")
    close_time: datetime = Field(..., description="收盘时间")
    
    # OHLC数据
    open: float = Field(..., description="开盘价", ge=0)
    high: float = Field(..., description="最高价", ge=0)
    low: float = Field(..., description="最低价", ge=0)
    close: float = Field(..., description="收盘价", ge=0)
    
    # 成交量和金额
    volume: int = Field(..., description="成交量", ge=0)
    amount: float = Field(..., description="成交额", ge=0)
    
    # 可选字段
    turnover_rate: Optional[float] = Field(None, description="换手率", ge=0, le=100)
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    
    @field_validator('high')
    @classmethod
    def high_must_be_highest(cls, v, info):
        """验证最高价必须是最高值"""
        if 'open' in info.data and 'low' in info.data and 'close' in info.data:
            max_price = max(info.data['open'], info.data['low'], info.data['close'])
            if v < max_price:
                raise ValueError('最高价必须大于等于其他价格')
        return v
    
    @field_validator('low')
    @classmethod
    def low_must_be_lowest(cls, v, info):
        """验证最低价必须是最低值"""
        if 'open' in info.data and 'high' in info.data and 'close' in info.data:
            if v > min(info.data['open'], info.data['high'], info.data['close']):
                return min(info.data['open'], info.data['high'], info.data['close'])
        return v


class Bar(TimestampedModel):
    """Bar数据模型 - 各种频率的行情数据
    
    支持多种频率的行情数据，包括股票和期货
    注意：不活跃标的，没有成交量是不生成bar
    """
    
    symbol: str = Field(..., description="标的代码", min_length=1)
    frequency: str = Field(..., description="频率，支持多种频率")
    
    # OHLC数据
    open: float = Field(..., description="开盘价", ge=0)
    close: float = Field(..., description="收盘价", ge=0)
    high: float = Field(..., description="最高价", ge=0)
    low: float = Field(..., description="最低价", ge=0)
    
    # 成交量和金额
    amount: float = Field(..., description="成交额", ge=0)
    volume: int = Field(..., description="成交量", ge=0)
    
    # 期货特有字段
    position: Optional[int] = Field(None, description="持仓量（仅期货）", ge=0)
    
    # 时间字段
    bob: datetime = Field(..., description="bar开始时间")
    eob: datetime = Field(..., description="bar结束时间")
    
    # 计算字段
    change: Optional[float] = Field(None, description="涨跌额")
    change_pct: Optional[float] = Field(None, description="涨跌幅(%)")
    amplitude: Optional[float] = Field(None, description="振幅(%)")
    
    @field_validator('high')
    @classmethod
    def high_must_be_highest(cls, v, info):
        """验证最高价必须是最高值"""
        if 'open' in info.data and 'low' in info.data and 'close' in info.data:
            max_price = max(info.data['open'], info.data['low'], info.data['close'])
            if v < max_price:
                raise ValueError('最高价必须大于等于其他价格')
        return v
    
    @field_validator('low')
    @classmethod
    def low_must_be_lowest(cls, v, info):
        """验证最低价必须是最低值"""
        if 'open' in info.data and 'high' in info.data and 'close' in info.data:
            if v > min(info.data['open'], info.data['high'], info.data['close']):
                return min(info.data['open'], info.data['high'], info.data['close'])
        return v
    
    @field_validator('change', 'change_pct', mode='before')
    @classmethod
    def calculate_change_fields(cls, v, info):
        """计算涨跌额和涨跌幅"""
        if 'close' in info.data and 'open' in info.data:
            if info.data['open'] > 0:
                change = info.data['close'] - info.data['open']
                change_pct = (change / info.data['open']) * 100
                return change_pct if 'change_pct' in info.data else change
        return v
    
    @field_validator('amplitude', mode='before')
    @classmethod
    def calculate_amplitude(cls, v, info):
        """计算振幅"""
        if 'high' in info.data and 'low' in info.data and 'open' in info.data:
            if info.data['open'] > 0:
                return ((info.data['high'] - info.data['low']) / info.data['open']) * 100
        return v
    
    @field_validator('eob')
    @classmethod
    def eob_must_be_after_bob(cls, v, info):
        """验证结束时间必须晚于开始时间"""
        if 'bob' in info.data and v <= info.data['bob']:
            raise ValueError('结束时间必须晚于开始时间')
        return v
    
    @field_validator('volume')
    @classmethod
    def volume_must_be_positive_for_active_symbols(cls, v, info):
        """验证活跃标的必须有成交量"""
        if v <= 0:
            raise ValueError('活跃标的必须有成交量')
        return v


class BarCollection(TimestampedModel):
    """Bar数据集合模型"""
    
    symbol: str = Field(..., description="标的代码")
    frequency: str = Field(..., description="频率")
    bars: List[Bar] = Field(default_factory=list, description="Bar数据列表")
    
    # 统计信息
    total_bars: int = Field(0, description="总Bar数量")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    
    @field_validator('total_bars', mode='before')
    @classmethod
    def calculate_total_bars(cls, v, info):
        """计算总Bar数量"""
        if 'bars' in info.data:
            return len(info.data['bars'])
        return v
    
    @field_validator('start_time', mode='before')
    @classmethod
    def set_start_time(cls, v, info):
        """设置开始时间"""
        if 'bars' in info.data and info.data['bars']:
            return min(bar.bob for bar in info.data['bars'])
        return v
    
    @field_validator('end_time', mode='before')
    @classmethod
    def set_end_time(cls, v, info):
        """设置结束时间"""
        if 'bars' in info.data and info.data['bars']:
            return max(bar.eob for bar in info.data['bars'])
        return v


class StockBasicInfo(IdentifiableModel):
    """股票基本信息模型"""
    
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    exchange: str = Field(..., description="交易所")
    market: str = Field(..., description="市场类型")
    
    # 基本信息
    industry: Optional[str] = Field(None, description="所属行业")
    sector: Optional[str] = Field(None, description="所属板块")
    listing_date: Optional[datetime] = Field(None, description="上市日期")
    
    # 股本信息
    total_shares: Optional[int] = Field(None, description="总股本", ge=0)
    float_shares: Optional[int] = Field(None, description="流通股本", ge=0)
    
    # 状态
    is_active: bool = Field(True, description="是否活跃")
    is_st: bool = Field(False, description="是否ST")
    is_suspended: bool = Field(False, description="是否停牌")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol_format(cls, v):
        """验证股票代码格式"""
        if not (v.startswith(('SHSE.', 'SZSE.')) or 
                (v.endswith(('.SH', '.SZ')) and len(v) >= 6)):
            raise ValueError('股票代码格式不正确')
        return v


class StockScreeningCriteria(AppBaseModel):
    """股票筛选条件模型"""
    
    # 价格条件
    min_price: Optional[float] = Field(None, description="最低价格", ge=0)
    max_price: Optional[float] = Field(None, description="最高价格", ge=0)
    
    # 涨跌幅条件
    min_change_pct: Optional[float] = Field(None, description="最小涨跌幅", ge=-100)
    max_change_pct: Optional[float] = Field(None, description="最大涨跌幅", le=100)
    
    # 成交量条件
    min_volume: Optional[int] = Field(None, description="最小成交量", ge=0)
    min_amount: Optional[float] = Field(None, description="最小成交额", ge=0)
    
    # 技术指标条件
    min_turnover_rate: Optional[float] = Field(None, description="最小换手率", ge=0)
    max_pe_ratio: Optional[float] = Field(None, description="最大市盈率", ge=0)
    max_pb_ratio: Optional[float] = Field(None, description="最大市净率", ge=0)
    
    # 市场条件
    exchanges: Optional[List[str]] = Field(None, description="指定交易所")
    industries: Optional[List[str]] = Field(None, description="指定行业")
    
    @field_validator('max_price')
    @classmethod
    def max_price_must_be_higher_than_min(cls, v, info):
        """验证最高价必须高于最低价"""
        if v is not None and 'min_price' in info.data and info.data['min_price'] is not None:
            if v <= info.data['min_price']:
                raise ValueError('最高价必须高于最低价')
        return v
    
    @field_validator('max_change_pct')
    @classmethod
    def max_change_must_be_higher_than_min(cls, v, info):
        """验证最大涨跌幅必须高于最小涨跌幅"""
        if v is not None and 'min_change_pct' in info.data and info.data['min_change_pct'] is not None:
            if v <= info.data['min_change_pct']:
                raise ValueError('最大涨跌幅必须高于最小涨跌幅')
        return v
