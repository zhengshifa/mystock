#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM SDK客户端工具模块
提供掘金量化SDK的统一接口和工具函数
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

try:
    import pandas as pd
    import gm
    from gm.api import *
    from gm.api import (
        stk_get_fundamentals_balance,
        stk_get_fundamentals_income,
        stk_get_fundamentals_cashflow
    )
    GM_AVAILABLE = True
except ImportError as e:
    if "pandas" in str(e):
        print("警告: pandas未安装，请运行 'pip install pandas' 安装")
    else:
        print("警告: GM SDK未安装，请运行 'pip install gm' 安装")
    gm = None
    GM_AVAILABLE = False
    
    # 定义占位符函数，避免NameError
    def login():
        raise RuntimeError("GM SDK未安装")
    
    def logout():
        raise RuntimeError("GM SDK未安装")
    
    def set_token(token):
        raise RuntimeError("GM SDK未安装")
    
    def set_serv_addr(endpoint):
        raise RuntimeError("GM SDK未安装")
    
    def stk_get_fundamentals_balance(*args, **kwargs):
        raise RuntimeError("GM SDK未安装")
    
    def stk_get_fundamentals_income(*args, **kwargs):
        raise RuntimeError("GM SDK未安装")
    
    def stk_get_fundamentals_cashflow(*args, **kwargs):
        raise RuntimeError("GM SDK未安装")

from config import config
import logging

logger = logging.getLogger(__name__)

class GMClient:
    """掘金量化客户端"""
    
    def __init__(self, gm_config=None):
        self.config = gm_config or config.gm_sdk
        self._initialized = False
        self._connected = False
    
    def initialize(self) -> bool:
        """初始化GM SDK"""
        if not GM_AVAILABLE:
            logger.error("GM SDK未安装")
            return False
        
        if self._initialized:
            return True
        
        try:
            # 设置token和endpoint
            set_token(self.config.token)
            
            if hasattr(gm.api, 'set_serv_addr'):
                set_serv_addr(self.config.endpoint)
            
            logger.info(f"GM SDK初始化成功: {self.config.endpoint}")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"GM SDK初始化失败: {e}")
            return False
    
    def connect(self) -> bool:
        """连接到GM服务"""
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            # GM SDK在设置token后自动连接，无需显式登录
            logger.info("GM SDK连接成功")
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"GM SDK连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开GM连接"""
        if self._connected:
            try:
                # GM SDK无需显式断开连接
                logger.info("GM SDK已断开连接")
                self._connected = False
            except Exception as e:
                logger.error(f"GM SDK断开连接失败: {e}")
    
    def get_current_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """获取实时行情数据"""
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        try:
            # 获取实时行情
            quotes = current(symbols)
            if not quotes:
                logger.warning(f"未获取到行情数据: {symbols}")
                return []
            
            result = []
            for quote in quotes:
                # 构建标准化数据结构
                data = self._format_quote_data(quote)
                result.append(data)
            
            logger.debug(f"获取到{len(result)}条实时行情数据")
            return result
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return []
    
    def get_history_data(self, symbol: str, start_time: str, end_time: str, 
                        frequency: str = '1d') -> List[Dict[str, Any]]:
        """获取历史数据"""
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        try:
            # 获取历史数据
            data = history(
                symbol=symbol,
                frequency=frequency,
                start_time=start_time,
                end_time=end_time,
                fields='symbol,eob,open,high,low,close,volume,amount',
                skip_suspended=True,
                fill_missing='Last',
                adjust=ADJUST_PREV,
                df=True
            )
            
            if data is None or data.empty:
                logger.warning(f"未获取到历史数据: {symbol}")
                return []
            
            # 转换为字典列表
            result = []
            for _, row in data.iterrows():
                result.append({
                    'symbol': row['symbol'],
                    'datetime': row['eob'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'amount': float(row['amount']),
                    'created_at': datetime.now()
                })
            
            logger.info(f"获取到{len(result)}条历史数据: {symbol}")
            return result
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return []
    
    def get_tick_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """获取tick数据"""
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        try:
            # 获取tick数据
            ticks = current(symbols)
            if not ticks:
                return []
            
            result = []
            for tick in ticks:
                data = {
                    'symbol': tick.symbol,
                    'price': float(tick.price),
                    'volume': int(getattr(tick, 'last_volume', 0)),
                    'amount': float(getattr(tick, 'last_amount', 0)),
                    'bid_price': float(getattr(tick, 'bid_p', 0)),
                    'ask_price': float(getattr(tick, 'ask_p', 0)),
                    'trade_time': datetime.now(),
                    'created_at': datetime.now()
                }
                result.append(data)
            
            logger.debug(f"获取到{len(result)}条tick数据")
            return result
        except Exception as e:
            logger.error(f"获取tick数据失败: {e}")
            return []
    
    def get_history_tick_data(self, symbol: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """获取历史Tick数据 - 使用掘金量化history接口
        
        Args:
            symbol: 标的代码
            start_time: 开始时间，格式：'2023-01-01' 或 '2023-01-01 09:30:00'
            end_time: 结束时间，格式：'2023-12-31' 或 '2023-12-31 15:00:00'
        
        Returns:
            历史Tick数据列表
        """
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        try:
            # 获取历史Tick数据，使用'tick'频率
            # 注意：tick是分笔成交数据，股票频率为3s, 期货为0.5s, 指数5s
            tick_data = history(
                symbol=symbol,
                frequency='tick',  # 使用tick频率获取逐笔数据
                start_time=start_time,
                end_time=end_time,
                fields='symbol,eob,open,high,low,price,cum_volume,cum_amount,cum_position,trade_type,last_volume,last_amount,quotes',
                skip_suspended=True,
                fill_missing='Last',
                adjust=ADJUST_NONE,  # Tick数据不复权
                df=True
            )
            
            if tick_data is None or tick_data.empty:
                logger.warning(f"未获取到历史Tick数据: {symbol}")
                return []
            
            # 转换为标准化的Tick数据结构
            result = []
            for _, row in tick_data.iterrows():
                try:
                    # 处理quotes字段（买卖档位数据）
                    quotes = []
                    raw_quotes = row.get('quotes', [])
                    
                    if isinstance(raw_quotes, list):
                        for quote in raw_quotes:
                            if isinstance(quote, dict):
                                quote_data = {
                                    'bid_p': float(quote.get('bid_p', 0)),
                                    'bid_v': int(quote.get('bid_v', 0)),
                                    'ask_p': float(quote.get('ask_p', 0)),
                                    'ask_v': int(quote.get('ask_v', 0))
                                }
                                
                                # 处理委买委卖队列（level2行情）
                                if 'bid_q' in quote and isinstance(quote['bid_q'], dict):
                                    quote_data['bid_q'] = {
                                        'total_orders': int(quote['bid_q'].get('total_orders', 0)),
                                        'queue_volumes': quote['bid_q'].get('queue_volumes', [])
                                    }
                                
                                if 'ask_q' in quote and isinstance(quote['ask_q'], dict):
                                    quote_data['ask_q'] = {
                                        'total_orders': int(quote['ask_q'].get('total_orders', 0)),
                                        'queue_volumes': quote['ask_q'].get('queue_volumes', [])
                                    }
                                
                                quotes.append(quote_data)
                    
                    # 构建Tick数据
                    tick_item = {
                        'symbol': row['symbol'],
                        'open': float(row.get('open', 0)) if not pd.isna(row.get('open')) else 0.0,
                        'high': float(row.get('high', 0)) if not pd.isna(row.get('high')) else 0.0,
                        'low': float(row.get('low', 0)) if not pd.isna(row.get('low')) else 0.0,
                        'price': float(row.get('price', 0)) if not pd.isna(row.get('price')) else 0.0,
                        'cum_volume': int(row.get('cum_volume', 0)) if not pd.isna(row.get('cum_volume')) else 0,
                        'cum_amount': float(row.get('cum_amount', 0)) if not pd.isna(row.get('cum_amount')) else 0.0,
                        'cum_position': int(row.get('cum_position', 0)) if not pd.isna(row.get('cum_position')) else 0,
                        'trade_type': int(row.get('trade_type', 0)) if not pd.isna(row.get('trade_type')) else 0,
                        'last_volume': int(row.get('last_volume', 0)) if not pd.isna(row.get('last_volume')) else 0,
                        'last_amount': float(row.get('last_amount', 0)) if not pd.isna(row.get('last_amount')) else 0.0,
                        'quotes': quotes,
                        'created_at': row.get('eob', datetime.now()) if not pd.isna(row.get('eob')) else datetime.now()
                    }
                    
                    result.append(tick_item)
                    
                except Exception as e:
                    logger.error(f"处理Tick数据行失败: {e}, 数据: {row}")
                    continue
            
            logger.info(f"获取到{len(result)}条历史Tick数据: {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"获取历史Tick数据失败: {e}")
            return []
    
    def get_multi_symbol_history_tick_data(self, symbols: List[str], start_time: str, end_time: str) -> Dict[str, List[Dict[str, Any]]]:
        """获取多个标的的历史Tick数据
        
        Args:
            symbols: 标的代码列表
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            按标的分组的Tick数据字典
        """
        result = {}
        
        for symbol in symbols:
            try:
                ticks = self.get_history_tick_data(symbol, start_time, end_time)
                if ticks:
                    result[symbol] = ticks
                    logger.info(f"获取{symbol}历史Tick数据: {len(ticks)}条")
                else:
                    logger.warning(f"未获取到{symbol}历史Tick数据")
            except Exception as e:
                logger.error(f"获取{symbol}历史Tick数据失败: {e}")
                continue
        
        return result
    
    def get_tick_data_summary(self, symbol: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """获取Tick数据摘要统计
        
        Args:
            symbol: 标的代码
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            Tick数据摘要统计
        """
        try:
            ticks = self.get_history_tick_data(symbol, start_time, end_time)
            if not ticks:
                return {}
            
            # 计算统计信息
            prices = [tick['price'] for tick in ticks if tick['price'] > 0]
            volumes = [tick['last_volume'] for tick in ticks if tick['last_volume'] > 0]
            amounts = [tick['last_amount'] for tick in ticks if tick['last_amount'] > 0]
            
            if not prices:
                return {}
            
            summary = {
                'symbol': symbol,
                'total_ticks': len(ticks),
                'start_time': start_time,
                'end_time': end_time,
                'price_stats': {
                    'min': min(prices),
                    'max': max(prices),
                    'avg': sum(prices) / len(prices),
                    'first': prices[0],
                    'last': prices[-1]
                },
                'volume_stats': {
                    'total': sum(volumes),
                    'avg': sum(volumes) / len(volumes) if volumes else 0,
                    'max': max(volumes) if volumes else 0
                },
                'amount_stats': {
                    'total': sum(amounts),
                    'avg': sum(amounts) / len(amounts) if amounts else 0,
                    'max': max(amounts) if amounts else 0
                },
                'created_at': datetime.now()
            }
            
            # 计算价格变化
            if len(prices) >= 2:
                summary['price_stats']['change'] = prices[-1] - prices[0]
                summary['price_stats']['change_pct'] = (summary['price_stats']['change'] / prices[0]) * 100 if prices[0] > 0 else 0
            
            logger.info(f"生成Tick数据摘要: {symbol}, 总计{len(ticks)}条")
            return summary
            
        except Exception as e:
            logger.error(f"生成Tick数据摘要失败: {e}")
            return {}
    
    def get_bar_data(self, symbols: List[str], frequency: str = '1d', 
                     start_time: str = None, end_time: str = None,
                     fields: str = None, adjust: str = 'PREV') -> List[Dict[str, Any]]:
        """获取Bar数据 - 各种频率的行情数据
        
        Args:
            symbols: 标的代码列表
            frequency: 频率，支持多种频率
            start_time: 开始时间，格式：'2023-01-01' 或 '2023-01-01 09:30:00'
            end_time: 结束时间，格式：'2023-12-31' 或 '2023-12-31 15:00:00'
            fields: 字段列表，默认获取OHLCV数据
            adjust: 复权类型，'PREV'前复权, 'NEXT'后复权, 'NONE'不复权
        
        Returns:
            Bar数据列表
        """
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        if not fields:
            fields = 'symbol,eob,bob,open,high,low,close,volume,amount'
        
        try:
            # 设置默认时间范围（最近一年）
            if not end_time:
                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if not start_time:
                start_time = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
            
            # 转换adjust参数为GM SDK常量
            adjust_value = ADJUST_PREV  # 默认前复权
            if adjust == 'NEXT':
                adjust_value = ADJUST_NEXT
            elif adjust == 'NONE':
                adjust_value = ADJUST_NONE
            
            # 获取Bar数据
            bars = history(
                symbol=symbols,
                frequency=frequency,
                start_time=start_time,
                end_time=end_time,
                fields=fields,
                skip_suspended=True,
                fill_missing='Last',
                adjust=adjust_value,
                df=True
            )
            
            if bars is None or bars.empty:
                logger.warning(f"未获取到Bar数据: {symbols}, 频率: {frequency}")
                return []
            
            # 转换为标准化的Bar数据结构
            result = []
            for _, row in bars.iterrows():
                try:
                    # 处理时间字段
                    bob = row.get('bob')
                    eob = row.get('eob')
                    
                    # 如果bob为空，使用eob减去一个周期
                    if pd.isna(bob) and not pd.isna(eob):
                        if frequency == '1d':
                            bob = eob - timedelta(days=1)
                        elif frequency == '1h':
                            bob = eob - timedelta(hours=1)
                        elif frequency == '30m':
                            bob = eob - timedelta(minutes=30)
                        elif frequency == '15m':
                            bob = eob - timedelta(minutes=15)
                        elif frequency == '5m':
                            bob = eob - timedelta(minutes=5)
                        elif frequency == '1m':
                            bob = eob - timedelta(minutes=1)
                        else:
                            bob = eob - timedelta(days=1)
                    
                    bar_data = {
                        'symbol': row['symbol'],
                        'frequency': frequency,
                        'open': float(row['open']) if not pd.isna(row['open']) else 0.0,
                        'close': float(row['close']) if not pd.isna(row['close']) else 0.0,
                        'high': float(row['high']) if not pd.isna(row['high']) else 0.0,
                        'low': float(row['low']) if not pd.isna(row['low']) else 0.0,
                        'amount': float(row['amount']) if not pd.isna(row['amount']) else 0.0,
                        'volume': int(row['volume']) if not pd.isna(row['volume']) else 0,
                        'bob': bob if not pd.isna(bob) else datetime.now(),
                        'eob': eob if not pd.isna(eob) else datetime.now(),
                        'created_at': datetime.now()
                    }
                    
                    # 添加期货特有字段（如果存在）
                    if 'position' in row and not pd.isna(row['position']):
                        bar_data['position'] = int(row['position'])
                    
                    result.append(bar_data)
                    
                except Exception as e:
                    logger.error(f"处理Bar数据行失败: {e}, 数据: {row}")
                    continue
            
            logger.info(f"获取到{len(result)}条Bar数据: {symbols}, 频率: {frequency}")
            return result
            
        except Exception as e:
            logger.error(f"获取Bar数据失败: {e}")
            return []
    
    def get_multi_frequency_bars(self, symbols: List[str], 
                                frequencies: List[str] = None,
                                start_time: str = None, end_time: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取多种频率的Bar数据
        
        Args:
            symbols: 标的代码列表
            frequencies: 频率列表，默认获取常用频率
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            按频率分组的Bar数据字典
        """
        if not frequencies:
            frequencies = ['1m', '5m', '15m', '30m', '1h', '1d']
        
        result = {}
        
        for frequency in frequencies:
            try:
                bars = self.get_bar_data(symbols, frequency, start_time, end_time)
                if bars:
                    result[frequency] = bars
                    logger.info(f"获取{frequency}频率数据: {len(bars)}条")
                else:
                    logger.warning(f"未获取到{frequency}频率数据")
            except Exception as e:
                logger.error(f"获取{frequency}频率数据失败: {e}")
                continue
        
        return result
    
    def get_latest_bar(self, symbol: str, frequency: str = '1d') -> Optional[Dict[str, Any]]:
        """获取最新的Bar数据
        
        Args:
            symbol: 标的代码
            frequency: 频率
        
        Returns:
            最新的Bar数据，如果没有则返回None
        """
        try:
            # 获取最近的数据
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if frequency == '1d':
                start_time = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            elif frequency == '1h':
                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            elif frequency in ['30m', '15m', '5m']:
                start_time = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
            elif frequency == '1m':
                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                start_time = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            
            bars = self.get_bar_data([symbol], frequency, start_time, end_time)
            
            if bars:
                # 返回最新的Bar数据
                latest_bar = max(bars, key=lambda x: x['eob'])
                logger.info(f"获取到最新{frequency}频率数据: {symbol}, 时间: {latest_bar['eob']}")
                return latest_bar
            else:
                logger.warning(f"未获取到最新{frequency}频率数据: {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"获取最新Bar数据失败: {e}")
            return None
    
    def _format_quote_data(self, quote) -> Dict[str, Any]:
        """格式化行情数据 - 匹配完整数据格式"""
        try:
            # 基础行情数据
            data = {
                'symbol': quote.get('symbol', ''),
                'open': float(quote.get('open', 0)),
                'high': float(quote.get('high', 0)),
                'low': float(quote.get('low', 0)),
                'price': float(quote.get('price', 0)),
                'pre_close': float(quote.get('pre_close', 0)),
                'cum_volume': int(quote.get('cum_volume', 0)),
                'cum_amount': float(quote.get('cum_amount', 0)),
                'last_amount': float(quote.get('last_amount', 0)),
                'last_volume': int(quote.get('last_volume', 0)),
                'trade_type': int(quote.get('trade_type', 0)),  # 新增交易类型字段
                'created_at': quote.get('created_at', datetime.now())  # 保持原始时间或使用当前时间
            }
            
            # 五档买卖盘数据 - 直接使用GM SDK返回的quotes字段
            quotes = quote.get('quotes', [])
            # 确保quotes格式正确
            formatted_quotes = []
            for q in quotes:
                if isinstance(q, dict):
                    formatted_quotes.append({
                        'bid_p': float(q.get('bid_p', 0)),
                        'bid_v': int(q.get('bid_v', 0)),
                        'ask_p': float(q.get('ask_p', 0)),
                        'ask_v': int(q.get('ask_v', 0))
                    })
            
            data['quotes'] = formatted_quotes
            
            # 计算技术指标
            if data['price'] > 0 and data['pre_close'] > 0:
                data['change'] = data['price'] - data['pre_close']
                data['change_pct'] = (data['change'] / data['pre_close']) * 100
            else:
                data['change'] = 0
                data['change_pct'] = 0
            
            # 计算VWAP
            if data['cum_volume'] > 0:
                data['vwap'] = data['cum_amount'] / data['cum_volume']
            else:
                data['vwap'] = data['price']
            
            # 盘口统计
            total_bid_volume = sum(q['bid_v'] for q in formatted_quotes)
            total_ask_volume = sum(q['ask_v'] for q in formatted_quotes)
            
            data['total_bid_volume'] = total_bid_volume
            data['total_ask_volume'] = total_ask_volume
            
            if total_ask_volume > 0:
                data['bid_ask_ratio'] = total_bid_volume / total_ask_volume
            else:
                data['bid_ask_ratio'] = 0
            
            return data
        except Exception as e:
            logger.error(f"格式化行情数据失败: {e}")
            return {}
    
    def get_instruments(self, exchanges: List[str] = None) -> List[Dict[str, Any]]:
        """获取交易标的信息"""
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        try:
            exchanges = exchanges or ['SHSE', 'SZSE']
            instruments = []
            
            for exchange in exchanges:
                data = get_instruments(exchange=exchange, df=True)
                if data is not None and not data.empty:
                    for _, row in data.iterrows():
                        instruments.append({
                            'symbol': row['symbol'],
                            'sec_name': row.get('sec_name', ''),
                            'exchange': exchange,
                            'sec_type': row.get('sec_type', ''),
                            'list_date': row.get('list_date', ''),
                            'delist_date': row.get('delist_date', '')
                        })
            
            logger.info(f"获取到{len(instruments)}个交易标的")
            return instruments
        except Exception as e:
            logger.error(f"获取交易标的失败: {e}")
            return []
    
    def get_fundamentals_balance(self, symbols: List[str], fields: str = 'total_ast,total_liab,total_hldr_eqy_exc_min_int', 
                               rpt_type: int = 0, data_type: int = 0,
                               start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """获取资产负债表数据
        
        Args:
            symbols: 股票代码列表
            fields: 字段列表，默认为总资产、总负债、总权益
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
            start_date: 开始日期
            end_date: 结束日期
        """
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        all_results = []
        
        # 逐个处理股票代码，因为掘金API要求一次只能查询一个代码
        for symbol in symbols:
            try:
                data = stk_get_fundamentals_balance(
                    symbol=symbol,
                    fields=fields,
                    rpt_type=rpt_type,
                    data_type=data_type,
                    start_date=start_date,
                    end_date=end_date,
                    df=True
                )
                
                if data is None or data.empty:
                    logger.warning(f"未获取到资产负债表数据: {symbol}")
                    continue
                
                for _, row in data.iterrows():
                    record = {
                        'symbol': row.get('symbol', ''),
                        'pub_date': row.get('pub_date', ''),
                        'end_date': row.get('end_date', ''),
                        'rpt_type': rpt_type,
                        'data_type': data_type,
                        'created_at': datetime.now()
                    }
                    
                    # 添加所有字段数据（除了已有的基础字段）
                    for col in data.columns:
                        if col not in ['symbol', 'pub_date', 'end_date']:
                            value = row[col]
                            if value is not None:
                                try:
                                    # 尝试转换为数值
                                    record[col] = float(value)
                                except (ValueError, TypeError):
                                    # 如果转换失败，保持原值
                                    record[col] = value
                            else:
                                record[col] = 0.0
                    
                    all_results.append(record)
                    
            except Exception as e:
                logger.error(f"获取资产负债表数据失败 {symbol}: {e}")
                continue
        
        logger.info(f"获取到{len(all_results)}条资产负债表数据")
        return all_results
    
    def get_fundamentals_income(self, symbols: List[str], fields: str = 'oper_rev,net_profit_incl_min_int_inc,total_profit',
                              rpt_type: int = 0, data_type: int = 0,
                              start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        获取利润表数据
        
        Args:
            symbols: 股票代码列表
            fields: 字段列表，默认为营业总收入、净利润、利润总额
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
            start_date: 开始日期
            end_date: 结束日期
        """
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        all_results = []
        
        # 逐个处理股票代码，因为掘金API要求一次只能查询一个代码
        for symbol in symbols:
            try:
                data = stk_get_fundamentals_income(
                    symbol=symbol,
                    fields=fields,
                    rpt_type=rpt_type,
                    data_type=data_type,
                    start_date=start_date,
                    end_date=end_date,
                    df=True
                )
                
                if data is None or data.empty:
                    logger.warning(f"未获取到利润表数据: {symbol}")
                    continue
                
                for _, row in data.iterrows():
                    record = {
                        'symbol': row.get('symbol', ''),
                        'pub_date': row.get('pub_date', ''),
                        'end_date': row.get('end_date', ''),
                        'rpt_type': rpt_type,
                        'data_type': data_type,
                        'created_at': datetime.now()
                    }
                    
                    # 添加所有字段数据（除了已有的基础字段）
                    for col in data.columns:
                        if col not in ['symbol', 'pub_date', 'end_date']:
                            value = row[col]
                            if value is not None:
                                try:
                                    # 尝试转换为数值
                                    record[col] = float(value)
                                except (ValueError, TypeError):
                                    # 如果转换失败，保持原值
                                    record[col] = value
                            else:
                                record[col] = 0.0
                    
                    all_results.append(record)
                    
            except Exception as e:
                logger.error(f"获取利润表数据失败 {symbol}: {e}")
                continue
        
        logger.info(f"获取到{len(all_results)}条利润表数据")
        return all_results
    
    def get_fundamentals_cashflow(self, symbols: List[str], fields: str = 'net_cash_flows_oper_act,net_cash_flows_inv_act,net_cash_flows_fnc_act',
                                rpt_type: int = 0, data_type: int = 0,
                                start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        获取现金流量表数据
        
        Args:
            symbols: 股票代码列表
            fields: 字段列表，默认为经营活动现金流净额、投资活动现金流净额、筹资活动现金流净额
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
            start_date: 开始日期
            end_date: 结束日期
        """
        if not self._connected:
            logger.error("GM SDK未连接")
            return []
        
        all_results = []
        
        # 逐个处理股票代码，因为掘金API要求一次只能查询一个代码
        for symbol in symbols:
            try:
                data = stk_get_fundamentals_cashflow(
                    symbol=symbol,
                    fields=fields,
                    rpt_type=rpt_type,
                    data_type=data_type,
                    start_date=start_date,
                    end_date=end_date,
                    df=True
                )
                
                if data is None or data.empty:
                    logger.warning(f"未获取到现金流量表数据: {symbol}")
                    continue
                
                for _, row in data.iterrows():
                    record = {
                        'symbol': row.get('symbol', ''),
                        'pub_date': row.get('pub_date', ''),
                        'end_date': row.get('end_date', ''),
                        'rpt_type': rpt_type,
                        'data_type': data_type,
                        'created_at': datetime.now()
                    }
                    
                    # 添加所有字段数据（除了已有的基础字段）
                    for col in data.columns:
                        if col not in ['symbol', 'pub_date', 'end_date']:
                            value = row[col]
                            if value is not None:
                                try:
                                    # 尝试转换为数值
                                    record[col] = float(value)
                                except (ValueError, TypeError):
                                    # 如果转换失败，保持原值
                                    record[col] = value
                            else:
                                record[col] = 0.0
                    
                    all_results.append(record)
                    
            except Exception as e:
                logger.error(f"获取现金流量表数据失败 {symbol}: {e}")
                continue
        
        logger.info(f"获取到{len(all_results)}条现金流量表数据")
        return all_results
    
    def get_fundamentals_all(self, symbols: List[str], start_date: str = None, 
                           end_date: str = None, rpt_type: int = 0, 
                           data_type: int = 0) -> Dict[str, List[Dict[str, Any]]]:
        """获取完整的基本面数据（资产负债表、利润表、现金流量表）
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
        
        Returns:
            包含三张表数据的字典
        """
        result = {
            'balance': [],
            'income': [],
            'cashflow': []
        }
        
        try:
            # 获取资产负债表数据
            balance_data = self.get_fundamentals_balance(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                rpt_type=rpt_type,
                data_type=data_type
            )
            result['balance'] = balance_data
            
            # 获取利润表数据
            income_data = self.get_fundamentals_income(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                rpt_type=rpt_type,
                data_type=data_type
            )
            result['income'] = income_data
            
            # 获取现金流量表数据
            cashflow_data = self.get_fundamentals_cashflow(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                rpt_type=rpt_type,
                data_type=data_type
            )
            result['cashflow'] = cashflow_data
            
            total_records = len(balance_data) + len(income_data) + len(cashflow_data)
            logger.info(f"获取完整基本面数据完成，共{total_records}条记录")
            
        except Exception as e:
            logger.error(f"获取完整基本面数据失败: {e}")
        
        return result
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()

# 全局GM客户端实例
gm_client = GMClient()