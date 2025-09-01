"""
股票数据模型类
基于掘金量化的数据结构定义
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.utils.helpers import generate_hash


class QuoteData(BaseModel):
    """报价数据模型"""
    bid_p: float = Field(0.0, description="买价")
    bid_v: int = Field(0, description="买量")
    ask_p: float = Field(0.0, description="卖价")
    ask_v: int = Field(0, description="卖量")
    bid_q: Optional[Dict[str, Any]] = Field(None, description="委买队列")
    ask_q: Optional[Dict[str, Any]] = Field(None, description="委卖队列")


class TickData(BaseModel):
    """Tick数据模型"""
    symbol: str = Field(..., description="标的代码")
    open: float = Field(0.0, description="日线开盘价")
    high: float = Field(0.0, description="日线最高价")
    low: float = Field(0.0, description="日线最低价")
    price: float = Field(0.0, description="最新价")
    cum_volume: int = Field(0, description="最新总成交量")
    cum_amount: float = Field(0.0, description="最新总成交额")
    cum_position: int = Field(0, description="合约持仓量")
    trade_type: int = Field(0, description="交易类型")
    last_volume: int = Field(0, description="最新瞬时成交量")
    last_amount: float = Field(0.0, description="最新瞬时成交额")
    created_at: datetime = Field(..., description="创建时间")
    quotes: List[QuoteData] = Field(default_factory=list, description="买卖档数据")
    iopv: Optional[float] = Field(None, description="基金份额参考净值")
    
    # 用于去重的字段
    data_hash: str = Field("", description="数据哈希值")
    collection_time: datetime = Field(default_factory=datetime.now, description="数据收集时间")
    
    def __init__(self, **data):
        super().__init__(**data)
        # 生成数据哈希值用于去重
        self.data_hash = generate_hash({
            'symbol': self.symbol,
            'price': self.price,
            'created_at': self.created_at.isoformat(),
            'cum_volume': self.cum_volume
        })
    
    class Config:
        """模型配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BarData(BaseModel):
    """Bar数据模型"""
    symbol: str = Field(..., description="标的代码")
    frequency: str = Field("1d", description="频率")
    open: float = Field(0.0, description="开盘价")
    close: float = Field(0.0, description="收盘价")
    high: float = Field(0.0, description="最高价")
    low: float = Field(0.0, description="最低价")
    amount: float = Field(0.0, description="成交额")
    volume: int = Field(0, description="成交量")
    position: Optional[int] = Field(None, description="持仓量")
    bob: datetime = Field(..., description="bar开始时间")
    eob: datetime = Field(..., description="bar结束时间")
    
    # 用于去重的字段
    data_hash: str = Field("", description="数据哈希值")
    collection_time: datetime = Field(default_factory=datetime.now, description="数据收集时间")
    
    def __init__(self, **data):
        super().__init__(**data)
        # 生成数据哈希值用于去重
        self.data_hash = generate_hash({
            'symbol': self.symbol,
            'frequency': self.frequency,
            'bob': self.bob.isoformat(),
            'eob': self.eob.isoformat()
        })
    
    class Config:
        """模型配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StockData(BaseModel):
    """股票数据基类"""
    symbol: str = Field(..., description="股票代码")
    data_type: str = Field(..., description="数据类型")
    collection_time: datetime = Field(default_factory=datetime.now, description="数据收集时间")
    
    class Config:
        """模型配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
