#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票基本信息数据处理器

处理股票基本信息相关数据，包括:
- 股票列表
- 股票基本信息
- 交易日历
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from loguru import logger
import pandas as pd

from .base_processor import BaseDataProcessor, DataProcessingError
from ..database import DataType, StockInfoRepository, TradingCalendarRepository
from ..database.models import StockInfo, TradingCalendar, Exchange, SecType


class StockInfoProcessor(BaseDataProcessor):
    """股票基本信息处理器"""
    
    @property
    def data_type(self) -> DataType:
        return DataType.STOCK_INFO
    
    @property
    def processor_name(self) -> str:
        return "股票基本信息处理器"
    
    def __init__(self, gm_client, repository_manager, config):
        super().__init__(gm_client, repository_manager, config)
        
        # 获取相关仓库
        self.stock_info_repo = repository_manager.get_repository(StockInfoRepository)
        self.trading_calendar_repo = repository_manager.get_repository(TradingCalendarRepository)
        
        # 处理器特定配置
        self.exchanges = config.get('exchanges', ['SZSE', 'SHSE'])  # 默认处理深交所和上交所
        self.sec_types = config.get('sec_types', ['STOCK'])  # 默认处理股票
        self.update_existing = config.get('update_existing', True)  # 是否更新已存在的数据
        
        logger.info(f"股票基本信息处理器初始化完成，交易所: {self.exchanges}, 证券类型: {self.sec_types}")
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取股票基本信息数据"""
        try:
            data_subtype = kwargs.get('data_subtype', 'stock_list')
            
            if data_subtype == 'stock_list':
                return await self._fetch_stock_list(**kwargs)
            elif data_subtype == 'trading_calendar':
                return await self._fetch_trading_calendar(**kwargs)
            else:
                raise DataProcessingError(f"不支持的数据子类型: {data_subtype}")
                
        except Exception as e:
            logger.error(f"获取股票基本信息数据失败: {e}")
            raise
    
    async def _fetch_stock_list(self, **kwargs) -> List[Dict[str, Any]]:
        """获取股票列表"""
        try:
            all_stocks = []
            
            for exchange in self.exchanges:
                for sec_type in self.sec_types:
                    logger.info(f"获取 {exchange}.{sec_type} 股票列表")
                    
                    # 调用掘金API获取股票列表
                    stocks = await self.gm_client.get_instruments(
                        exchanges=[exchange],
                        sec_types=[sec_type]
                    )
                    
                    if stocks:
                        logger.info(f"获取到 {len(stocks)} 只 {exchange}.{sec_type} 股票")
                        all_stocks.extend(stocks)
                    else:
                        logger.warning(f"未获取到 {exchange}.{sec_type} 股票数据")
            
            logger.info(f"总共获取到 {len(all_stocks)} 只股票")
            return all_stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise
    
    async def _fetch_trading_calendar(self, **kwargs) -> List[Dict[str, Any]]:
        """获取交易日历"""
        try:
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            if not start_date or not end_date:
                # 默认获取当年的交易日历
                current_year = datetime.now().year
                start_date = f"{current_year}-01-01"
                end_date = f"{current_year}-12-31"
            
            logger.info(f"获取交易日历: {start_date} 到 {end_date}")
            
            # 调用掘金API获取交易日历
            calendar_data = await self.gm_client.get_trading_calendar(
                start_date=start_date,
                end_date=end_date
            )
            
            if calendar_data:
                logger.info(f"获取到 {len(calendar_data)} 个交易日历记录")
            else:
                logger.warning("未获取到交易日历数据")
                calendar_data = []
            
            return calendar_data
            
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            raise
    
    async def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理股票基本信息数据"""
        try:
            if not raw_data:
                return []
            
            # 判断数据类型并分别处理
            first_item = raw_data[0]
            
            if 'symbol' in first_item and 'exchange' in first_item:
                # 股票列表数据
                return await self._process_stock_list(raw_data)
            elif 'trade_date' in first_item:
                # 交易日历数据
                return await self._process_trading_calendar(raw_data)
            else:
                logger.warning(f"未知的数据格式: {first_item.keys()}")
                return []
                
        except Exception as e:
            logger.error(f"处理股票基本信息数据失败: {e}")
            raise
    
    async def _process_stock_list(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理股票列表数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'sec_name': self._clean_string_data(item.get('sec_name')),
                        'exchange': self._parse_exchange(item.get('exchange')),
                        'sec_type': self._parse_sec_type(item.get('sec_type')),
                        'list_date': self._format_datetime(item.get('list_date')),
                        'delist_date': self._format_datetime(item.get('delist_date')),
                        'is_active': item.get('is_active', True),
                        'industry': self._clean_string_data(item.get('industry')),
                        'sector': self._clean_string_data(item.get('sector')),
                        'market_cap': self._clean_numeric_data(item.get('market_cap')),
                        'total_shares': self._clean_numeric_data(item.get('total_shares')),
                        'float_shares': self._clean_numeric_data(item.get('float_shares')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 验证必要字段
                    if processed_item['symbol'] and processed_item['exchange']:
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"股票数据缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理股票数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条股票数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理股票列表数据失败: {e}")
            raise
    
    async def _process_trading_calendar(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理交易日历数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'trade_date': self._format_datetime(item.get('trade_date')),
                        'is_trading_day': bool(item.get('is_trading_day', True)),
                        'exchange': self._parse_exchange(item.get('exchange', 'SHSE')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 验证必要字段
                    if processed_item['trade_date']:
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"交易日历数据缺少日期字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理交易日历数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条交易日历数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理交易日历数据失败: {e}")
            raise
    
    async def save_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存股票基本信息数据"""
        try:
            if not processed_data:
                return True
            
            # 判断数据类型并分别保存
            first_item = processed_data[0]
            
            if 'symbol' in first_item and 'sec_name' in first_item:
                # 股票列表数据
                return await self._save_stock_list(processed_data)
            elif 'trade_date' in first_item and 'is_trading_day' in first_item:
                # 交易日历数据
                return await self._save_trading_calendar(processed_data)
            else:
                logger.error(f"未知的数据格式，无法保存: {first_item.keys()}")
                return False
                
        except Exception as e:
            logger.error(f"保存股票基本信息数据失败: {e}")
            return False
    
    async def _save_stock_list(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存股票列表数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建StockInfo模型实例
                        stock_info = StockInfo(**item)
                        
                        if self.update_existing:
                            # 更新或插入
                            result = await self.stock_info_repo.save_or_update(
                                stock_info,
                                filter_dict={'symbol': item['symbol']}
                            )
                        else:
                            # 仅插入新数据
                            existing = await self.stock_info_repo.find_one({'symbol': item['symbol']})
                            if not existing:
                                result = await self.stock_info_repo.save(stock_info)
                            else:
                                result = True  # 跳过已存在的数据
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存股票信息失败: {item.get('symbol')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"股票信息保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存股票列表数据失败: {e}")
            return False
    
    async def _save_trading_calendar(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存交易日历数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建TradingCalendar模型实例
                        calendar_item = TradingCalendar(**item)
                        
                        if self.update_existing:
                            # 更新或插入
                            result = await self.trading_calendar_repo.save_or_update(
                                calendar_item,
                                filter_dict={
                                    'trade_date': item['trade_date'],
                                    'exchange': item['exchange']
                                }
                            )
                        else:
                            # 仅插入新数据
                            existing = await self.trading_calendar_repo.find_one({
                                'trade_date': item['trade_date'],
                                'exchange': item['exchange']
                            })
                            if not existing:
                                result = await self.trading_calendar_repo.save(calendar_item)
                            else:
                                result = True  # 跳过已存在的数据
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存交易日历失败: {item.get('trade_date')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"交易日历保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存交易日历数据失败: {e}")
            return False
    
    def _parse_exchange(self, exchange_str: str) -> Exchange:
        """解析交易所"""
        try:
            if not exchange_str:
                return Exchange.SHSE  # 默认上交所
            
            exchange_str = exchange_str.upper().strip()
            
            if exchange_str in ['SHSE', 'SH', 'SSE']:
                return Exchange.SHSE
            elif exchange_str in ['SZSE', 'SZ', 'SZSE']:
                return Exchange.SZSE
            elif exchange_str in ['BSE', 'BJ', 'BJSE']:
                return Exchange.BSE
            else:
                logger.warning(f"未知交易所: {exchange_str}, 使用默认值 SHSE")
                return Exchange.SHSE
                
        except Exception:
            return Exchange.SHSE
    
    def _parse_sec_type(self, sec_type_str: str) -> SecType:
        """解析证券类型"""
        try:
            if not sec_type_str:
                return SecType.STOCK  # 默认股票
            
            sec_type_str = sec_type_str.upper().strip()
            
            if sec_type_str in ['STOCK', 'STK']:
                return SecType.STOCK
            elif sec_type_str in ['INDEX', 'IDX']:
                return SecType.INDEX
            elif sec_type_str in ['FUND', 'FD']:
                return SecType.FUND
            elif sec_type_str in ['BOND', 'BD']:
                return SecType.BOND
            elif sec_type_str in ['FUTURE', 'FUT']:
                return SecType.FUTURE
            elif sec_type_str in ['OPTION', 'OPT']:
                return SecType.OPTION
            else:
                logger.warning(f"未知证券类型: {sec_type_str}, 使用默认值 STOCK")
                return SecType.STOCK
                
        except Exception:
            return SecType.STOCK
    
    def _validate_data_item(self, item: Dict[str, Any]) -> bool:
        """验证数据项"""
        try:
            # 股票信息验证
            if 'symbol' in item:
                return bool(item.get('symbol') and item.get('exchange'))
            
            # 交易日历验证
            elif 'trade_date' in item:
                return bool(item.get('trade_date'))
            
            return False
            
        except Exception:
            return False
    
    # ==================== 特定功能方法 ====================
    
    async def update_stock_list(self, exchanges: Optional[List[str]] = None, sec_types: Optional[List[str]] = None) -> bool:
        """更新股票列表"""
        try:
            # 使用指定的交易所和证券类型，或使用默认配置
            old_exchanges = self.exchanges
            old_sec_types = self.sec_types
            
            if exchanges:
                self.exchanges = exchanges
            if sec_types:
                self.sec_types = sec_types
            
            # 运行数据处理流程
            result = await self.run(data_subtype='stock_list')
            
            # 恢复原配置
            self.exchanges = old_exchanges
            self.sec_types = old_sec_types
            
            return result
            
        except Exception as e:
            logger.error(f"更新股票列表失败: {e}")
            return False
    
    async def update_trading_calendar(self, start_date: str, end_date: str) -> bool:
        """更新交易日历"""
        try:
            return await self.run(
                data_subtype='trading_calendar',
                start_date=start_date,
                end_date=end_date
            )
            
        except Exception as e:
            logger.error(f"更新交易日历失败: {e}")
            return False
    
    async def get_active_stocks(self, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取活跃股票列表"""
        try:
            filter_dict = {'is_active': True}
            if exchange:
                filter_dict['exchange'] = self._parse_exchange(exchange)
            
            stocks = await self.stock_info_repo.find_many(filter_dict)
            return [stock.to_dict() for stock in stocks] if stocks else []
            
        except Exception as e:
            logger.error(f"获取活跃股票列表失败: {e}")
            return []
    
    async def get_trading_days(self, start_date: str, end_date: str, exchange: str = 'SHSE') -> List[str]:
        """获取交易日列表"""
        try:
            filter_dict = {
                'trade_date': {'$gte': start_date, '$lte': end_date},
                'is_trading_day': True,
                'exchange': self._parse_exchange(exchange)
            }
            
            trading_days = await self.trading_calendar_repo.find_many(filter_dict)
            return [day.trade_date for day in trading_days] if trading_days else []
            
        except Exception as e:
            logger.error(f"获取交易日列表失败: {e}")
            return []