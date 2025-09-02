#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场数据处理器

处理市场数据相关信息，包括:
- 实时行情数据
- Tick数据
- K线数据(分钟、日线等)
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

from .base_processor import BaseDataProcessor, DataProcessingError
from ..database import DataType, RealtimeQuoteRepository, TickDataRepository, BarDataRepository
from ..database.models import RealtimeQuote, TickData, BarData


class MarketDataProcessor(BaseDataProcessor):
    """市场数据处理器"""
    
    @property
    def data_type(self) -> DataType:
        return DataType.MARKET_DATA
    
    @property
    def processor_name(self) -> str:
        return "市场数据处理器"
    
    def __init__(self, gm_client, repository_manager, config):
        super().__init__(gm_client, repository_manager, config)
        
        # 获取相关仓库
        self.realtime_quote_repo = repository_manager.get_repository(DataType.REALTIME_QUOTE)
        self.tick_data_repo = repository_manager.get_repository(DataType.TICK_DATA)
        self.bar_data_repo = repository_manager.get_repository(DataType.BAR_DATA)
        
        # 处理器特定配置
        self.symbols = config.get('symbols', [])  # 要处理的股票代码列表
        self.bar_periods = config.get('bar_periods', ['1m', '5m', '15m', '30m', '1h', '1d'])  # K线周期
        self.max_days_per_request = config.get('max_days_per_request', 30)  # 单次请求最大天数
        self.enable_realtime = config.get('enable_realtime', True)  # 是否启用实时数据
        self.enable_tick = config.get('enable_tick', False)  # 是否启用tick数据
        self.enable_bar = config.get('enable_bar', True)  # 是否启用K线数据
        
        logger.info(f"市场数据处理器初始化完成，股票数量: {len(self.symbols)}, K线周期: {self.bar_periods}")
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取市场数据"""
        try:
            data_subtype = kwargs.get('data_subtype', 'realtime_quote')
            
            if data_subtype == 'realtime_quote':
                return await self._fetch_realtime_quotes(**kwargs)
            elif data_subtype == 'tick_data':
                return await self._fetch_tick_data(**kwargs)
            elif data_subtype == 'bar_data':
                return await self._fetch_bar_data(**kwargs)
            else:
                raise DataProcessingError(f"不支持的数据子类型: {data_subtype}")
                
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            raise
    
    async def _fetch_realtime_quotes(self, **kwargs) -> List[Dict[str, Any]]:
        """获取实时行情数据"""
        try:
            symbols = kwargs.get('symbols', self.symbols)
            if not symbols:
                logger.warning("未指定股票代码，跳过实时行情获取")
                return []
            
            logger.info(f"获取 {len(symbols)} 只股票的实时行情")
            
            # 调用掘金API获取实时行情
            quotes = await self.gm_client.get_current_quotes(symbols)
            
            if quotes:
                logger.info(f"获取到 {len(quotes)} 条实时行情数据")
            else:
                logger.warning("未获取到实时行情数据")
                quotes = []
            
            return quotes
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            raise
    
    async def _fetch_tick_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取Tick数据"""
        try:
            symbols = kwargs.get('symbols', self.symbols)
            start_time = kwargs.get('start_time')
            end_time = kwargs.get('end_time')
            
            if not symbols:
                logger.warning("未指定股票代码，跳过Tick数据获取")
                return []
            
            if not start_time or not end_time:
                # 默认获取当天的数据
                today = datetime.now().date()
                start_time = f"{today} 09:30:00"
                end_time = f"{today} 15:00:00"
            
            logger.info(f"获取 {len(symbols)} 只股票的Tick数据: {start_time} 到 {end_time}")
            
            all_ticks = []
            
            # 分批获取，避免单次请求过多数据
            for symbol in symbols:
                try:
                    # 暂时跳过Tick数据，因为GMConnectionManager没有这个方法
                    logger.warning(f"GMConnectionManager暂不支持Tick数据获取，跳过 {symbol}")
                    ticks = []
                    
                    if ticks:
                        all_ticks.extend(ticks)
                        logger.debug(f"获取到 {symbol} 的 {len(ticks)} 条Tick数据")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} Tick数据失败: {e}")
                    continue
            
            logger.info(f"总共获取到 {len(all_ticks)} 条Tick数据")
            return all_ticks
            
        except Exception as e:
            logger.error(f"获取Tick数据失败: {e}")
            raise
    
    async def _fetch_bar_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            symbols = kwargs.get('symbols', self.symbols)
            period = kwargs.get('period', '1d')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            if not symbols:
                logger.warning("未指定股票代码，跳过K线数据获取")
                return []
            
            if not start_date or not end_date:
                # 默认获取最近30天的数据
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
                start_date = start_date.strftime('%Y-%m-%d')
                end_date = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"获取 {len(symbols)} 只股票的 {period} K线数据: {start_date} 到 {end_date}")
            
            all_bars = []
            
            # 分批获取，避免单次请求过多数据
            for symbol in symbols:
                try:
                    bars = await self.gm_client.get_bars(
                        symbol=symbol,
                        period=period,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if bars:
                        # 为每条K线数据添加股票代码和周期信息
                        for bar in bars:
                            bar['symbol'] = symbol
                            bar['period'] = period
                        
                        all_bars.extend(bars)
                        logger.debug(f"获取到 {symbol} 的 {len(bars)} 条 {period} K线数据")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} K线数据失败: {e}")
                    continue
            
            logger.info(f"总共获取到 {len(all_bars)} 条K线数据")
            return all_bars
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise
    
    async def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理市场数据"""
        try:
            if not raw_data:
                return []
            
            # 判断数据类型并分别处理
            first_item = raw_data[0]
            
            if 'last_price' in first_item and 'quote_time' in first_item:
                # 实时行情数据（原始格式）
                return await self._process_realtime_quotes(raw_data)
            elif 'tick_time' in first_item and 'price' in first_item:
                # Tick数据
                return await self._process_tick_data(raw_data)
            elif 'open' in first_item and 'high' in first_item and 'low' in first_item and 'close' in first_item:
                # K线数据
                return await self._process_bar_data(raw_data)
            else:
                logger.warning(f"未知的市场数据格式: {first_item.keys()}")
                return []
                
        except Exception as e:
            logger.error(f"处理市场数据失败: {e}")
            raise
    
    async def _process_realtime_quotes(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理实时行情数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'price': self._clean_numeric_data(item.get('last_price')),  # 映射到price字段
                        'open': self._clean_numeric_data(item.get('open')),  # 映射到open字段
                        'high': self._clean_numeric_data(item.get('high')),  # 映射到high字段
                        'low': self._clean_numeric_data(item.get('low')),  # 映射到low字段
                        'pre_close': self._clean_numeric_data(item.get('pre_close')),
                        'volume': self._clean_numeric_data(item.get('volume')),
                        'amount': self._clean_numeric_data(item.get('amount')),
                        'turnover_rate': self._clean_numeric_data(item.get('turnover_rate')),
                        'pe_ratio': self._clean_numeric_data(item.get('pe_ratio')),
                        'pb_ratio': self._clean_numeric_data(item.get('pb_ratio')),
                        'bid1': self._clean_numeric_data(item.get('bid_price_1')),  # 映射到bid1字段
                        'bid1_volume': self._clean_numeric_data(item.get('bid_volume_1')),  # 映射到bid1_volume字段
                        'ask1': self._clean_numeric_data(item.get('ask_price_1')),  # 映射到ask1字段
                        'ask1_volume': self._clean_numeric_data(item.get('ask_volume_1')),  # 映射到ask1_volume字段
                        'timestamp': self._format_datetime(item.get('quote_time', datetime.now()), '%Y-%m-%d %H:%M:%S'),  # 映射到timestamp字段
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 计算涨跌幅
                    if processed_item['price'] and processed_item['pre_close'] and processed_item['pre_close'] > 0:
                        change = processed_item['price'] - processed_item['pre_close']
                        change_pct = (change / processed_item['pre_close']) * 100
                        processed_item['change'] = round(change, 2)
                        processed_item['change_pct'] = round(change_pct, 2)
                    else:
                        processed_item['change'] = None
                        processed_item['change_pct'] = None
                    
                    # 验证必要字段
                    if processed_item['symbol'] and processed_item['price'] is not None:
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"实时行情数据缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理实时行情数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条实时行情数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理实时行情数据失败: {e}")
            raise
    
    async def _process_tick_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理Tick数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'tick_time': self._format_datetime(item.get('tick_time'), '%Y-%m-%d %H:%M:%S'),
                        'price': self._clean_numeric_data(item.get('price')),
                        'volume': self._clean_numeric_data(item.get('volume')),
                        'amount': self._clean_numeric_data(item.get('amount')),
                        'bid_price': self._clean_numeric_data(item.get('bid_price')),
                        'bid_volume': self._clean_numeric_data(item.get('bid_volume')),
                        'ask_price': self._clean_numeric_data(item.get('ask_price')),
                        'ask_volume': self._clean_numeric_data(item.get('ask_volume')),
                        'trade_type': self._clean_string_data(item.get('trade_type')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 验证必要字段
                    if processed_item['symbol'] and processed_item['tick_time'] and processed_item['price'] is not None:
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"Tick数据缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理Tick数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条Tick数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理Tick数据失败: {e}")
            raise
    
    async def _process_bar_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理K线数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'period': self._clean_string_data(item.get('period', '1d')),
                        'timestamp': self._format_datetime(item.get('eob'), '%Y-%m-%d %H:%M:%S'),
                        'open': self._clean_numeric_data(item.get('open')),
                        'high': self._clean_numeric_data(item.get('high')),
                        'low': self._clean_numeric_data(item.get('low')),
                        'close': self._clean_numeric_data(item.get('close')),
                        'volume': self._clean_numeric_data(item.get('volume')),
                        'amount': self._clean_numeric_data(item.get('amount')),
                        'pre_close': self._clean_numeric_data(item.get('pre_close')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 计算涨跌幅
                    if processed_item['close'] and processed_item['pre_close'] and processed_item['pre_close'] > 0:
                        change = processed_item['close'] - processed_item['pre_close']
                        change_pct = (change / processed_item['pre_close']) * 100
                        processed_item['change'] = round(change, 2)
                        processed_item['pct_change'] = round(change_pct, 2)
                    else:
                        processed_item['change'] = None
                        processed_item['pct_change'] = None
                    
                    # 验证必要字段
                    if (processed_item['symbol'] and processed_item['timestamp'] and 
                        processed_item['open'] is not None and processed_item['close'] is not None):
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"K线数据缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理K线数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条K线数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理K线数据失败: {e}")
            raise
    
    async def save_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存市场数据"""
        try:
            if not processed_data:
                return True
            
            # 判断数据类型并分别保存
            first_item = processed_data[0]
            
            if 'timestamp' in first_item and 'price' in first_item:
                # 实时行情数据（处理后格式）
                return await self._save_realtime_quotes(processed_data)
            elif 'tick_time' in first_item:
                # Tick数据
                return await self._save_tick_data(processed_data)
            elif 'timestamp' in first_item and 'period' in first_item:
                # K线数据
                return await self._save_bar_data(processed_data)
            else:
                logger.error(f"未知的市场数据格式，无法保存: {first_item.keys()}")
                return False
                
        except Exception as e:
            logger.error(f"保存市场数据失败: {e}")
            return False
    
    async def _save_realtime_quotes(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存实时行情数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建RealtimeQuote模型实例，移除BaseModel字段
                        quote_data = {k: v for k, v in item.items() if k not in ['created_at', 'updated_at']}
                        quote = RealtimeQuote(**quote_data)
                        
                        # 实时行情通常是更新操作
                        result = await self.realtime_quote_repo.save(quote)
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存实时行情失败: {item.get('symbol')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"实时行情保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存实时行情数据失败: {e}")
            return False
    
    async def _save_tick_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存Tick数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建TickData模型实例，移除BaseModel字段
                        tick_data = {k: v for k, v in item.items() if k not in ['created_at', 'updated_at']}
                        tick = TickData(**tick_data)
                        
                        # Tick数据通常是插入操作，避免重复
                        existing = await self.tick_data_repo.find_one({
                            'symbol': item['symbol'],
                            'tick_time': item['tick_time']
                        })
                        
                        if not existing:
                            result = await self.tick_data_repo.save(tick)
                        else:
                            result = True  # 跳过已存在的数据
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存Tick数据失败: {item.get('symbol')} {item.get('tick_time')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"Tick数据保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存Tick数据失败: {e}")
            return False
    
    async def _save_bar_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存K线数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建BarData模型实例，移除BaseModel字段
                        bar_data = {k: v for k, v in item.items() if k not in ['created_at', 'updated_at']}
                        bar = BarData(**bar_data)
                        
                        # K线数据通常是更新或插入操作
                        result = await self.bar_data_repo.save(bar)
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存K线数据失败: {item.get('symbol')} {item.get('timestamp')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"K线数据保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存K线数据失败: {e}")
            return False
    
    def _validate_data_item(self, item: Dict[str, Any]) -> bool:
        """验证数据项"""
        try:
            # 实时行情验证
            if 'price' in item and 'timestamp' in item:
                return bool(item.get('symbol') and item.get('price') is not None and item.get('timestamp'))
            
            # Tick数据验证
            elif 'tick_time' in item:
                return bool(item.get('symbol') and item.get('tick_time') and item.get('price') is not None)
            
            # K线数据验证
            elif 'timestamp' in item and 'open' in item and 'close' in item:
                return bool(
                    item.get('symbol') and item.get('timestamp') and 
                    item.get('open') is not None and item.get('close') is not None
                )
            
            return False
            
        except Exception:
            return False
    
    # ==================== 特定功能方法 ====================
    
    async def update_realtime_quotes(self, symbols: Optional[List[str]] = None) -> bool:
        """更新实时行情"""
        try:
            return await self.run(
                data_subtype='realtime_quote',
                symbols=symbols or self.symbols
            )
            
        except Exception as e:
            logger.error(f"更新实时行情失败: {e}")
            return False
    
    async def update_tick_data(self, symbols: Optional[List[str]] = None, 
                              start_time: Optional[str] = None, 
                              end_time: Optional[str] = None) -> bool:
        """更新Tick数据"""
        try:
            return await self.run(
                data_subtype='tick_data',
                symbols=symbols or self.symbols,
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            logger.error(f"更新Tick数据失败: {e}")
            return False
    
    async def update_bar_data(self, symbols: Optional[List[str]] = None, 
                             period: str = '1d',
                             start_date: Optional[str] = None, 
                             end_date: Optional[str] = None) -> bool:
        """更新K线数据"""
        try:
            return await self.run(
                data_subtype='bar_data',
                symbols=symbols or self.symbols,
                period=period,
                start_date=start_date,
                end_date=end_date
            )
            
        except Exception as e:
            logger.error(f"更新K线数据失败: {e}")
            return False
    
    async def get_latest_quotes(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取最新行情"""
        try:
            filter_dict = {}
            if symbols:
                filter_dict['symbol'] = {'$in': symbols}
            
            quotes = await self.realtime_quote_repo.find_many(filter_dict)
            return [quote.to_dict() for quote in quotes] if quotes else []
            
        except Exception as e:
            logger.error(f"获取最新行情失败: {e}")
            return []
    
    async def get_bar_data_range(self, symbol: str, period: str, 
                                start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取指定时间范围的K线数据"""
        try:
            filter_dict = {
                'symbol': symbol,
                'period': period,
                'bar_time': {'$gte': start_date, '$lte': end_date}
            }
            
            bars = await self.bar_data_repo.find_many(filter_dict)
            return [bar.to_dict() for bar in bars] if bars else []
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return []