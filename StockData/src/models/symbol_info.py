"""
标的基本信息数据模型
"""
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class SymbolInfo:
    """标的基本信息数据模型"""
    
    # 基本信息
    symbol: str  # 标的代码
    sec_type1: int  # 证券品种大类
    sec_type2: Optional[int] = None  # 证券品种细类
    board: Optional[int] = None  # 板块
    exchange: str = ""  # 交易所代码
    sec_id: str = ""  # 交易所标的代码
    sec_name: str = ""  # 交易所标的名称
    sec_abbr: str = ""  # 交易所标的简称
    
    # 交易信息
    price_tick: float = 0.0  # 最小变动单位
    trade_n: int = 1  # 交易制度 (0=T+0, 1=T+1, 2=T+2)
    
    # 时间信息
    listed_date: Optional[datetime] = None  # 上市日期
    delisted_date: Optional[datetime] = None  # 退市日期
    
    # 期货/期权特有字段
    underlying_symbol: str = ""  # 标的资产
    option_type: str = ""  # 行权方式 (E=欧式, A=美式)
    option_margin_ratio1: float = 0.0  # 期权保证金计算系数1
    option_margin_ratio2: float = 0.0  # 期权保证金计算系数2
    call_or_put: str = ""  # 合约类型 (C=Call, P=Put)
    
    # 可转债特有字段
    conversion_start_date: Optional[datetime] = None  # 可转债开始转股日期
    delisting_begin_date: Optional[datetime] = None  # 退市整理开始日
    
    # 系统字段
    created_at: Optional[datetime] = None  # 创建时间
    updated_at: Optional[datetime] = None  # 更新时间
    
    def __post_init__(self):
        """初始化后处理"""
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SymbolInfo':
        """
        从字典创建SymbolInfo对象
        
        Args:
            data: 包含标的基本信息的字典
            
        Returns:
            SymbolInfo: 标的基本信息对象
        """
        # 处理时间字段
        listed_date = data.get('listed_date')
        if listed_date and not isinstance(listed_date, datetime):
            try:
                if isinstance(listed_date, str):
                    listed_date = datetime.fromisoformat(listed_date.replace('Z', '+00:00'))
                else:
                    listed_date = None
            except (ValueError, AttributeError):
                listed_date = None
        
        delisted_date = data.get('delisted_date')
        if delisted_date and not isinstance(delisted_date, datetime):
            try:
                if isinstance(delisted_date, str):
                    delisted_date = datetime.fromisoformat(delisted_date.replace('Z', '+00:00'))
                else:
                    delisted_date = None
            except (ValueError, AttributeError):
                delisted_date = None
        
        conversion_start_date = data.get('conversion_start_date')
        if conversion_start_date and not isinstance(conversion_start_date, datetime):
            try:
                if isinstance(conversion_start_date, str):
                    conversion_start_date = datetime.fromisoformat(conversion_start_date.replace('Z', '+00:00'))
                else:
                    conversion_start_date = None
            except (ValueError, AttributeError):
                conversion_start_date = None
        
        delisting_begin_date = data.get('delisting_begin_date')
        if delisting_begin_date and not isinstance(delisting_begin_date, datetime):
            try:
                if isinstance(delisting_begin_date, str):
                    delisting_begin_date = datetime.fromisoformat(delisting_begin_date.replace('Z', '+00:00'))
                else:
                    delisting_begin_date = None
            except (ValueError, AttributeError):
                delisting_begin_date = None
        
        return cls(
            symbol=data.get('symbol', ''),
            sec_type1=data.get('sec_type1', 0),
            sec_type2=data.get('sec_type2'),
            board=data.get('board'),
            exchange=data.get('exchange', ''),
            sec_id=data.get('sec_id', ''),
            sec_name=data.get('sec_name', ''),
            sec_abbr=data.get('sec_abbr', ''),
            price_tick=data.get('price_tick', 0.0),
            trade_n=data.get('trade_n', 1),
            listed_date=listed_date,
            delisted_date=delisted_date,
            underlying_symbol=data.get('underlying_symbol', ''),
            option_type=data.get('option_type', ''),
            option_margin_ratio1=data.get('option_margin_ratio1', 0.0),
            option_margin_ratio2=data.get('option_margin_ratio2', 0.0),
            call_or_put=data.get('call_or_put', ''),
            conversion_start_date=conversion_start_date,
            delisting_begin_date=delisting_begin_date,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的标的基本信息
        """
        return asdict(self)
    
    def to_mongo_dict(self) -> Dict[str, Any]:
        """
        转换为MongoDB存储格式
        
        Returns:
            Dict[str, Any]: MongoDB存储格式的标的基本信息
        """
        data = self.to_dict()
        
        # 确保时间字段为datetime对象
        for field in ['listed_date', 'delisted_date', 'conversion_start_date', 
                     'delisting_begin_date', 'created_at', 'updated_at']:
            if data.get(field) and not isinstance(data[field], datetime):
                try:
                    if isinstance(data[field], str):
                        data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    data[field] = None
        
        return data
    
    def get_sec_type_name(self) -> str:
        """
        获取证券类型名称
        
        Returns:
            str: 证券类型名称
        """
        type1_names = {
            1010: "股票",
            1020: "基金", 
            1030: "债券",
            1040: "期货",
            1050: "期权",
            1060: "指数",
            1070: "板块"
        }
        
        type2_names = {
            # 股票
            101001: "A股",
            101002: "B股", 
            101003: "存托凭证",
            # 基金
            102001: "ETF",
            102002: "LOF",
            102005: "FOF",
            102009: "基础设施REITs",
            # 债券
            103001: "可转债",
            103003: "国债",
            103006: "企业债",
            103008: "回购",
            # 期货
            104001: "股指期货",
            104003: "商品期货",
            104006: "国债期货",
            # 期权
            105001: "股票期权",
            105002: "指数期权",
            105003: "商品期权",
            # 指数
            106001: "股票指数",
            106002: "基金指数",
            106003: "债券指数",
            106004: "期货指数",
            # 板块
            107001: "概念板块"
        }
        
        type1_name = type1_names.get(self.sec_type1, f"未知类型({self.sec_type1})")
        if self.sec_type2:
            type2_name = type2_names.get(self.sec_type2, f"未知细类({self.sec_type2})")
            return f"{type1_name} - {type2_name}"
        else:
            return type1_name
    
    def is_active(self) -> bool:
        """
        判断标的是否活跃（未退市）
        
        Returns:
            bool: 是否活跃
        """
        if self.delisted_date is None:
            return True
        
        # 如果退市日期是默认的2038年，表示未退市
        if self.delisted_date.year == 2038:
            return True
        
        return self.delisted_date > datetime.now()
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SymbolInfo(symbol={self.symbol}, name={self.sec_name}, type={self.get_sec_type_name()})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"SymbolInfo(symbol='{self.symbol}', sec_name='{self.sec_name}', "
                f"sec_type1={self.sec_type1}, sec_type2={self.sec_type2}, "
                f"exchange='{self.exchange}', listed_date={self.listed_date})")
