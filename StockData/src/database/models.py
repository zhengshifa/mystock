#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义

定义各种股票数据的数据模型，包括:
- 股票基本信息
- 交易日历
- 实时行情
- 逐笔数据
- K线数据
- 财务数据
- 分红数据
- 股本变动数据
- 指数成分股
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class DataType(Enum):
    """数据类型枚举"""
    STOCK_INFO = "stock_info"
    TRADING_CALENDAR = "trading_calendar"
    REALTIME_QUOTE = "realtime_quote"
    TICK_DATA = "tick_data"
    BAR_DATA = "bar_data"
    FINANCIAL_DATA = "financial_data"
    DIVIDEND_DATA = "dividend_data"
    SHARE_CHANGE_DATA = "share_change_data"
    INDEX_CONSTITUENT = "index_constituent"


class Exchange(Enum):
    """交易所枚举"""
    SHSE = "SHSE"  # 上海证券交易所
    SZSE = "SZSE"  # 深圳证券交易所
    BSE = "BSE"    # 北京证券交易所


class SecType(Enum):
    """证券类型枚举"""
    STOCK = "STOCK"        # 股票
    INDEX = "INDEX"        # 指数
    FUND = "FUND"          # 基金
    BOND = "BOND"          # 债券
    OPTION = "OPTION"      # 期权
    FUTURE = "FUTURE"      # 期货


class FinancialDataType(Enum):
    """财务数据类型枚举"""
    INCOME_STATEMENT = "income_statement"      # 利润表
    BALANCE_SHEET = "balance_sheet"            # 资产负债表
    CASH_FLOW = "cash_flow"                    # 现金流量表
    FINANCIAL_INDICATOR = "financial_indicator" # 财务指标


@dataclass
class BaseModel:
    """基础数据模型"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime对象
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建对象"""
        # 处理datetime字段
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)


@dataclass
class StockInfo(BaseModel):
    """股票基本信息模型"""
    symbol: str                    # 股票代码
    sec_name: str                  # 证券名称
    exchange: str                  # 交易所
    sec_type: str                  # 证券类型
    list_date: Optional[str] = None        # 上市日期
    delist_date: Optional[str] = None      # 退市日期
    is_active: bool = True         # 是否活跃
    industry: Optional[str] = None         # 行业
    sector: Optional[str] = None           # 板块
    market_cap: Optional[float] = None     # 市值
    total_shares: Optional[float] = None   # 总股本
    float_shares: Optional[float] = None   # 流通股本
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class TradingCalendar(BaseModel):
    """交易日历模型"""
    date: str                      # 日期
    exchange: str                  # 交易所
    is_trading_day: bool           # 是否交易日
    pre_trade_date: Optional[str] = None   # 前一交易日
    next_trade_date: Optional[str] = None  # 下一交易日
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class RealtimeQuote(BaseModel):
    """实时行情模型"""
    symbol: str                    # 股票代码
    timestamp: str                 # 时间戳
    price: float                   # 最新价
    open: float                    # 开盘价
    high: float                    # 最高价
    low: float                     # 最低价
    pre_close: float               # 昨收价
    volume: int                    # 成交量
    amount: float                  # 成交额
    turnover_rate: Optional[float] = None  # 换手率
    pe_ratio: Optional[float] = None       # 市盈率
    pb_ratio: Optional[float] = None       # 市净率
    bid1: Optional[float] = None           # 买一价
    bid1_volume: Optional[int] = None      # 买一量
    ask1: Optional[float] = None           # 卖一价
    ask1_volume: Optional[int] = None      # 卖一量
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class TickData(BaseModel):
    """逐笔数据模型"""
    symbol: str                    # 股票代码
    timestamp: str                 # 时间戳
    price: float                   # 成交价
    volume: int                    # 成交量
    amount: float                  # 成交额
    side: Optional[str] = None             # 买卖方向
    order_kind: Optional[str] = None       # 订单类型
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class BarData(BaseModel):
    """K线数据模型"""
    symbol: str                    # 股票代码
    timestamp: str                 # 时间戳
    period: str                    # 周期(1m, 5m, 15m, 30m, 1h, 1d等)
    open: float                    # 开盘价
    high: float                    # 最高价
    low: float                     # 最低价
    close: float                   # 收盘价
    volume: int                    # 成交量
    amount: float                  # 成交额
    pre_close: Optional[float] = None      # 昨收价
    change: Optional[float] = None         # 涨跌额
    pct_change: Optional[float] = None     # 涨跌幅
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class FinancialData(BaseModel):
    """财务数据模型"""
    symbol: str                    # 股票代码
    data_type: str                 # 数据类型
    end_date: str                  # 报告期
    pub_date: Optional[str] = None         # 公布日期
    
    # 利润表相关字段
    total_revenue: Optional[float] = None          # 营业总收入
    operating_revenue: Optional[float] = None      # 营业收入
    total_costs: Optional[float] = None            # 营业总成本
    operating_costs: Optional[float] = None        # 营业成本
    operating_profit: Optional[float] = None       # 营业利润
    total_profit: Optional[float] = None           # 利润总额
    net_profit: Optional[float] = None             # 净利润
    net_profit_parent: Optional[float] = None      # 归母净利润
    
    # 资产负债表相关字段
    total_assets: Optional[float] = None           # 总资产
    current_assets: Optional[float] = None         # 流动资产
    non_current_assets: Optional[float] = None     # 非流动资产
    total_liabilities: Optional[float] = None      # 总负债
    current_liabilities: Optional[float] = None    # 流动负债
    non_current_liabilities: Optional[float] = None # 非流动负债
    total_equity: Optional[float] = None           # 所有者权益
    
    # 现金流量表相关字段
    net_cash_operating: Optional[float] = None     # 经营活动现金流净额
    net_cash_investing: Optional[float] = None     # 投资活动现金流净额
    net_cash_financing: Optional[float] = None     # 筹资活动现金流净额
    net_cash_increase: Optional[float] = None      # 现金净增加额
    
    # 财务指标相关字段
    roe: Optional[float] = None                    # 净资产收益率
    roa: Optional[float] = None                    # 总资产收益率
    gross_profit_margin: Optional[float] = None    # 毛利率
    net_profit_margin: Optional[float] = None      # 净利率
    debt_to_asset_ratio: Optional[float] = None    # 资产负债率
    current_ratio: Optional[float] = None          # 流动比率
    quick_ratio: Optional[float] = None            # 速动比率
    eps: Optional[float] = None                    # 每股收益
    bvps: Optional[float] = None                   # 每股净资产
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class DividendData(BaseModel):
    """分红数据模型"""
    symbol: str                    # 股票代码
    ex_date: str                   # 除权除息日
    record_date: Optional[str] = None      # 股权登记日
    pay_date: Optional[str] = None         # 派息日
    dividend_cash: Optional[float] = None  # 现金分红(每股)
    dividend_stock: Optional[float] = None # 股票分红(每股)
    split_ratio: Optional[float] = None    # 拆股比例
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class ShareChangeData(BaseModel):
    """股本变动数据模型"""
    symbol: str                    # 股票代码
    change_date: str               # 变动日期
    change_type: str               # 变动类型
    total_shares_before: Optional[float] = None    # 变动前总股本
    total_shares_after: Optional[float] = None     # 变动后总股本
    float_shares_before: Optional[float] = None    # 变动前流通股本
    float_shares_after: Optional[float] = None     # 变动后流通股本
    change_reason: Optional[str] = None            # 变动原因
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class IndexConstituent(BaseModel):
    """指数成分股模型"""
    index_symbol: str              # 指数代码
    symbol: str                    # 成分股代码
    weight: Optional[float] = None         # 权重
    in_date: Optional[str] = None          # 纳入日期
    out_date: Optional[str] = None         # 剔除日期
    is_active: bool = True         # 是否活跃成分股
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


# 数据模型映射字典
MODEL_MAPPING = {
    DataType.STOCK_INFO: StockInfo,
    DataType.TRADING_CALENDAR: TradingCalendar,
    DataType.REALTIME_QUOTE: RealtimeQuote,
    DataType.TICK_DATA: TickData,
    DataType.BAR_DATA: BarData,
    DataType.FINANCIAL_DATA: FinancialData,
    DataType.DIVIDEND_DATA: DividendData,
    DataType.SHARE_CHANGE_DATA: ShareChangeData,
    DataType.INDEX_CONSTITUENT: IndexConstituent,
}


def get_model_class(data_type: DataType):
    """根据数据类型获取对应的模型类"""
    return MODEL_MAPPING.get(data_type)


def create_model_instance(data_type: DataType, data: Dict[str, Any]):
    """根据数据类型和数据创建模型实例"""
    model_class = get_model_class(data_type)
    if model_class:
        return model_class.from_dict(data)
    return None


def validate_model_data(data_type: DataType, data: Dict[str, Any]) -> bool:
    """验证数据是否符合模型要求"""
    try:
        model_class = get_model_class(data_type)
        if not model_class:
            return False
        
        # 尝试创建实例来验证数据
        instance = model_class.from_dict(data)
        return True
        
    except Exception:
        return False


# 集合名称映射
COLLECTION_MAPPING = {
    DataType.STOCK_INFO: "stock_info",
    DataType.TRADING_CALENDAR: "trading_calendar",
    DataType.REALTIME_QUOTE: "realtime_quotes",
    DataType.TICK_DATA: "tick_data",
    DataType.BAR_DATA: "bar_data",
    DataType.FINANCIAL_DATA: "financial_data",
    DataType.DIVIDEND_DATA: "dividend_data",
    DataType.SHARE_CHANGE_DATA: "share_change_data",
    DataType.INDEX_CONSTITUENT: "index_constituent",
}


def get_collection_name(data_type: DataType) -> str:
    """根据数据类型获取对应的集合名称"""
    return COLLECTION_MAPPING.get(data_type, "unknown")