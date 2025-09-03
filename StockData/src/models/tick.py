"""
Tick数据模型
根据掘金量化SDK的Tick对象定义
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Quote:
    """
    报价数据类
    包含买卖档位信息
    """
    bid_p: float  # 买价
    bid_v: int    # 买量
    ask_p: float  # 卖价
    ask_v: int    # 卖量
    bid_q: Optional[Dict] = None  # 委买队列 (仅level2行情支持)
    ask_q: Optional[Dict] = None  # 委卖队列 (仅level2行情支持)


@dataclass
class Tick:
    """
    Tick数据类
    行情快照数据(包含盘口数据和当天动态日线数据)
    """
    symbol: str                    # 标的代码
    open: float                    # 日线开盘价
    high: float                    # 日线最高价
    low: float                     # 日线最低价
    price: float                   # 最新价(集合竞价成交前price为0)
    cum_volume: int                # 最新总成交量,累计值（日线成交量）
    cum_amount: float              # 最新总成交额,累计值（日线成交金额）
    cum_position: int              # 合约持仓量(只适用于期货),累计值（股票此值为0）
    trade_type: int                # 交易类型（只适用于期货）
    last_volume: int               # 最新瞬时成交量
    last_amount: float             # 最新瞬时成交额（郑商所不支持）
    created_at: datetime           # 创建时间
    quotes: List[Quote]            # 买卖档位数据
    iopv: Optional[float] = None   # 基金份额参考净值，(只适用于基金)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Tick':
        """
        从字典创建Tick对象
        
        Args:
            data: 包含tick数据的字典
            
        Returns:
            Tick: Tick对象实例
        """
        # 处理quotes数据
        quotes = []
        if 'quotes' in data and data['quotes']:
            for quote_data in data['quotes']:
                quote = Quote(
                    bid_p=quote_data.get('bid_p', 0.0),
                    bid_v=quote_data.get('bid_v', 0),
                    ask_p=quote_data.get('ask_p', 0.0),
                    ask_v=quote_data.get('ask_v', 0),
                    bid_q=quote_data.get('bid_q'),
                    ask_q=quote_data.get('ask_q')
                )
                quotes.append(quote)
        
        return cls(
            symbol=data.get('symbol', ''),
            open=data.get('open', 0.0),
            high=data.get('high', 0.0),
            low=data.get('low', 0.0),
            price=data.get('price', 0.0),
            cum_volume=data.get('cum_volume', 0),
            cum_amount=data.get('cum_amount', 0.0),
            cum_position=data.get('cum_position', 0),
            trade_type=data.get('trade_type', 0),
            last_volume=data.get('last_volume', 0),
            last_amount=data.get('last_amount', 0.0),
            created_at=data.get('created_at'),
            quotes=quotes,
            iopv=data.get('iopv')
        )
    
    def to_dict(self) -> Dict:
        """
        将Tick对象转换为字典
        
        Returns:
            Dict: 包含tick数据的字典
        """
        quotes_data = []
        for quote in self.quotes:
            quote_dict = {
                'bid_p': quote.bid_p,
                'bid_v': quote.bid_v,
                'ask_p': quote.ask_p,
                'ask_v': quote.ask_v
            }
            if quote.bid_q:
                quote_dict['bid_q'] = quote.bid_q
            if quote.ask_q:
                quote_dict['ask_q'] = quote.ask_q
            quotes_data.append(quote_dict)
        
        result = {
            'symbol': self.symbol,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'price': self.price,
            'cum_volume': self.cum_volume,
            'cum_amount': self.cum_amount,
            'cum_position': self.cum_position,
            'trade_type': self.trade_type,
            'last_volume': self.last_volume,
            'last_amount': self.last_amount,
            'created_at': self.created_at,
            'quotes': quotes_data
        }
        
        if self.iopv is not None:
            result['iopv'] = self.iopv
        
        return result
