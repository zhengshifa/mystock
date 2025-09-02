#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化数据获取器

负责从掘金量化API获取各种类型的股票数据
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

try:
    import gm
except ImportError:
    logger.warning("掘金量化SDK未安装，请安装gm3包")
    gm = None


class GMDataFetcher:
    """掘金量化数据获取器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get('timeout', 30)
        self.retry_times = config.get('retry_times', 3)
        
        # 数据类型映射
        self.data_type_mapping = {
            'income_statement': 'income',
            'balance_sheet': 'balance',
            'cash_flow': 'cashflow',
            'financial_indicator': 'indicator'
        }
        
        logger.info("掘金量化数据获取器初始化完成")
    
    async def initialize(self):
        """初始化数据获取器"""
        try:
            logger.info("初始化掘金量化数据获取器")
            
            if gm is None:
                raise Exception("掘金量化SDK未安装")
            
            # 设置数据模式
            gm.set_data_mode(gm.MD_MODE_LIVE)  # 实时数据模式
            
            logger.info("掘金量化数据获取器初始化成功")
            
        except Exception as e:
            logger.error(f"数据获取器初始化失败: {e}")
            raise
    
    async def shutdown(self):
        """关闭数据获取器"""
        logger.info("掘金量化数据获取器已关闭")
    
    # ==================== 基础数据获取 ====================
    
    async def get_stock_info(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            logger.debug(f"获取股票基本信息: {symbols}")
            
            if symbols:
                # 获取指定股票信息
                instruments = []
                for symbol in symbols:
                    instrument = gm.get_instrument(symbol)
                    if instrument:
                        instruments.append(self._format_instrument_data(instrument))
            else:
                # 获取所有股票信息
                all_instruments = gm.get_instruments(exchanges=['SHSE', 'SZSE'], sec_types=['STOCK'])
                instruments = [self._format_instrument_data(inst) for inst in all_instruments]
            
            logger.debug(f"获取到 {len(instruments)} 条股票信息")
            return instruments
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            return []
    
    async def get_trading_calendar(self, 
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取交易日历"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.debug(f"获取交易日历: {start_date} 到 {end_date}")
            
            # 获取交易日历
            calendar = gm.get_trading_dates(exchange='SHSE', start_date=start_date, end_date=end_date)
            
            result = []
            for date in calendar:
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'is_trading_day': True,
                    'exchange': 'SHSE'
                })
            
            logger.debug(f"获取到 {len(result)} 个交易日")
            return result
            
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            return []
    
    # ==================== 行情数据获取 ====================
    
    async def get_realtime_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """获取实时行情"""
        try:
            logger.debug(f"获取实时行情: {symbols}")
            
            quotes = []
            for symbol in symbols:
                quote = gm.current(symbol)
                if quote:
                    quotes.append(self._format_quote_data(quote))
            
            logger.debug(f"获取到 {len(quotes)} 条实时行情")
            return quotes
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return []
    
    async def get_tick_data(self, 
                           symbol: str,
                           start_time: str,
                           end_time: str) -> List[Dict[str, Any]]:
        """获取逐笔数据"""
        try:
            logger.debug(f"获取逐笔数据: {symbol} {start_time} 到 {end_time}")
            
            # 获取逐笔数据
            ticks = gm.get_ticks(symbol=symbol, start_time=start_time, end_time=end_time)
            
            result = []
            for tick in ticks:
                result.append(self._format_tick_data(tick))
            
            logger.debug(f"获取到 {len(result)} 条逐笔数据")
            return result
            
        except Exception as e:
            logger.error(f"获取逐笔数据失败: {e}")
            return []
    
    async def get_bar_data(self, 
                          symbol: str,
                          period: str,
                          start_time: str,
                          end_time: str) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            logger.debug(f"获取K线数据: {symbol} {period} {start_time} 到 {end_time}")
            
            # 获取K线数据
            bars = gm.get_bars(symbol=symbol, period=period, start_time=start_time, end_time=end_time)
            
            result = []
            for bar in bars:
                result.append(self._format_bar_data(bar))
            
            logger.debug(f"获取到 {len(result)} 条K线数据")
            return result
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return []
    
    # ==================== 财务数据获取 ====================
    
    async def get_financial_data(self, 
                               symbols: List[str],
                               data_type: str,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取财务数据"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.debug(f"获取财务数据: {symbols} {data_type} {start_date} 到 {end_date}")
            
            # 映射数据类型
            gm_data_type = self.data_type_mapping.get(data_type, data_type)
            
            result = []
            for symbol in symbols:
                try:
                    # 获取财务数据
                    financial_data = gm.get_fundamentals(
                        table=gm_data_type,
                        symbols=symbol,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if financial_data is not None and not financial_data.empty:
                        for _, row in financial_data.iterrows():
                            result.append(self._format_financial_data(row, data_type))
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} 财务数据失败: {e}")
                    continue
            
            logger.debug(f"获取到 {len(result)} 条财务数据")
            return result
            
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return []
    
    # ==================== 其他数据获取 ====================
    
    async def get_dividend_data(self, 
                              symbols: List[str],
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取分红数据"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.debug(f"获取分红数据: {symbols} {start_date} 到 {end_date}")
            
            result = []
            for symbol in symbols:
                try:
                    # 获取分红数据
                    dividend_data = gm.get_dividend(symbol=symbol, start_date=start_date, end_date=end_date)
                    
                    if dividend_data:
                        for div in dividend_data:
                            result.append(self._format_dividend_data(div))
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} 分红数据失败: {e}")
                    continue
            
            logger.debug(f"获取到 {len(result)} 条分红数据")
            return result
            
        except Exception as e:
            logger.error(f"获取分红数据失败: {e}")
            return []
    
    async def get_share_change_data(self, 
                                  symbols: List[str],
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取股本变动数据"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.debug(f"获取股本变动数据: {symbols} {start_date} 到 {end_date}")
            
            result = []
            for symbol in symbols:
                try:
                    # 获取股本变动数据
                    share_data = gm.get_share_change(symbol=symbol, start_date=start_date, end_date=end_date)
                    
                    if share_data:
                        for share in share_data:
                            result.append(self._format_share_change_data(share))
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} 股本变动数据失败: {e}")
                    continue
            
            logger.debug(f"获取到 {len(result)} 条股本变动数据")
            return result
            
        except Exception as e:
            logger.error(f"获取股本变动数据失败: {e}")
            return []
    
    async def get_index_constituent(self, 
                                  index_symbol: str,
                                  date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取指数成分股"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.debug(f"获取指数成分股: {index_symbol} {date}")
            
            # 获取指数成分股
            constituents = gm.get_history_constituents(index=index_symbol, start_date=date, end_date=date)
            
            result = []
            if constituents:
                for constituent in constituents:
                    result.append(self._format_constituent_data(constituent))
            
            logger.debug(f"获取到 {len(result)} 条指数成分股数据")
            return result
            
        except Exception as e:
            logger.error(f"获取指数成分股失败: {e}")
            return []
    
    async def get_batch_data(self, data_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量获取数据"""
        results = []
        
        for request in data_requests:
            try:
                data_type = request.get('type')
                params = request.get('params', {})
                
                if data_type == 'stock_info':
                    data = await self.get_stock_info(params.get('symbols'))
                elif data_type == 'realtime_quotes':
                    data = await self.get_realtime_quotes(params.get('symbols', []))
                elif data_type == 'bar_data':
                    data = await self.get_bar_data(**params)
                elif data_type == 'financial_data':
                    data = await self.get_financial_data(**params)
                else:
                    logger.warning(f"不支持的数据类型: {data_type}")
                    continue
                
                results.extend(data)
                
            except Exception as e:
                logger.error(f"批量获取数据失败: {request}, 错误: {e}")
                continue
        
        return results
    
    # ==================== 数据格式化方法 ====================
    
    def _format_instrument_data(self, instrument) -> Dict[str, Any]:
        """格式化股票基本信息"""
        return {
            'symbol': instrument.symbol,
            'sec_name': getattr(instrument, 'sec_name', ''),
            'exchange': getattr(instrument, 'exchange', ''),
            'sec_type': getattr(instrument, 'sec_type', ''),
            'list_date': getattr(instrument, 'list_date', None),
            'delist_date': getattr(instrument, 'delist_date', None),
            'is_active': getattr(instrument, 'is_active', True),
            'multiplier': getattr(instrument, 'multiplier', 1),
            'price_tick': getattr(instrument, 'price_tick', 0.01),
            'update_time': datetime.now().isoformat()
        }
    
    def _format_quote_data(self, quote) -> Dict[str, Any]:
        """格式化实时行情数据"""
        return {
            'symbol': quote.symbol,
            'price': getattr(quote, 'price', 0),
            'open': getattr(quote, 'open', 0),
            'high': getattr(quote, 'high', 0),
            'low': getattr(quote, 'low', 0),
            'pre_close': getattr(quote, 'pre_close', 0),
            'volume': getattr(quote, 'volume', 0),
            'amount': getattr(quote, 'amount', 0),
            'bid_price': getattr(quote, 'bid_price', []),
            'ask_price': getattr(quote, 'ask_price', []),
            'bid_volume': getattr(quote, 'bid_volume', []),
            'ask_volume': getattr(quote, 'ask_volume', []),
            'timestamp': getattr(quote, 'created_at', datetime.now()).isoformat()
        }
    
    def _format_tick_data(self, tick) -> Dict[str, Any]:
        """格式化逐笔数据"""
        return {
            'symbol': tick.symbol,
            'price': tick.price,
            'volume': tick.volume,
            'amount': tick.amount,
            'side': getattr(tick, 'side', ''),
            'timestamp': tick.created_at.isoformat()
        }
    
    def _format_bar_data(self, bar) -> Dict[str, Any]:
        """格式化K线数据"""
        return {
            'symbol': bar.symbol,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'amount': bar.amount,
            'timestamp': bar.eob.isoformat(),
            'period': getattr(bar, 'period', '')
        }
    
    def _format_financial_data(self, row, data_type: str) -> Dict[str, Any]:
        """格式化财务数据"""
        result = {
            'symbol': row.get('symbol', ''),
            'pub_date': row.get('pub_date', ''),
            'end_date': row.get('end_date', ''),
            'data_type': data_type,
            'update_time': datetime.now().isoformat()
        }
        
        # 添加所有财务指标
        for key, value in row.items():
            if key not in ['symbol', 'pub_date', 'end_date']:
                result[key] = value
        
        return result
    
    def _format_dividend_data(self, dividend) -> Dict[str, Any]:
        """格式化分红数据"""
        return {
            'symbol': dividend.symbol,
            'ex_date': getattr(dividend, 'ex_date', ''),
            'pay_date': getattr(dividend, 'pay_date', ''),
            'cash_div': getattr(dividend, 'cash_div', 0),
            'stock_div': getattr(dividend, 'stock_div', 0),
            'update_time': datetime.now().isoformat()
        }
    
    def _format_share_change_data(self, share) -> Dict[str, Any]:
        """格式化股本变动数据"""
        return {
            'symbol': share.symbol,
            'change_date': getattr(share, 'change_date', ''),
            'total_share': getattr(share, 'total_share', 0),
            'float_share': getattr(share, 'float_share', 0),
            'change_reason': getattr(share, 'change_reason', ''),
            'update_time': datetime.now().isoformat()
        }
    
    def _format_constituent_data(self, constituent) -> Dict[str, Any]:
        """格式化指数成分股数据"""
        return {
            'index_symbol': getattr(constituent, 'index_symbol', ''),
            'symbol': constituent.symbol,
            'weight': getattr(constituent, 'weight', 0),
            'in_date': getattr(constituent, 'in_date', ''),
            'out_date': getattr(constituent, 'out_date', ''),
            'update_time': datetime.now().isoformat()
        }