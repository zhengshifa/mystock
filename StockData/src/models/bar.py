"""
Bar数据模型
根据掘金量化SDK的Bar对象定义
"""
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime


@dataclass
class Bar:
    """
    Bar数据类
    各种频率的行情数据
    """
    symbol: str                    # 标的代码
    frequency: str                 # 频率, 支持 'tick', '60s', '300s', '900s' 等, 默认'1d'
    open: float                    # 开盘价
    close: float                   # 收盘价
    high: float                    # 最高价
    low: float                     # 最低价
    amount: float                  # 成交额
    volume: int                    # 成交量
    bob: datetime                  # bar开始时间
    eob: datetime                  # bar结束时间
    position: Optional[int] = None # 持仓量（仅期货）
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Bar':
        """
        从字典创建Bar对象
        
        Args:
            data: 包含bar数据的字典
            
        Returns:
            Bar: Bar对象实例
        """
        return cls(
            symbol=data.get('symbol', ''),
            frequency=data.get('frequency', '1d'),
            open=data.get('open', 0.0),
            close=data.get('close', 0.0),
            high=data.get('high', 0.0),
            low=data.get('low', 0.0),
            amount=data.get('amount', 0.0),
            volume=data.get('volume', 0),
            position=data.get('position'),
            bob=data.get('bob'),
            eob=data.get('eob')
        )
    
    def to_dict(self) -> Dict:
        """
        将Bar对象转换为字典
        
        Returns:
            Dict: 包含bar数据的字典
        """
        result = {
            'symbol': self.symbol,
            'frequency': self.frequency,
            'open': self.open,
            'close': self.close,
            'high': self.high,
            'low': self.low,
            'amount': self.amount,
            'volume': self.volume,
            'bob': self.bob,
            'eob': self.eob
        }
        
        if self.position is not None:
            result['position'] = self.position
        
        return result
