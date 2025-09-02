#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据仓库

提供各种股票数据的专业化操作接口，包括:
- 基础仓库类
- 股票信息仓库
- 行情数据仓库
- 财务数据仓库
- 其他数据仓库
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from loguru import logger
from abc import ABC, abstractmethod

from .mongo_manager import MongoManager
from .models import (
    DataType, StockInfo, TradingCalendar, RealtimeQuote, TickData, 
    BarData, FinancialData, DividendData, ShareChangeData, IndexConstituent,
    get_collection_name, create_model_instance
)


class BaseRepository(ABC):
    """基础仓库类"""
    
    def __init__(self, mongo_manager: MongoManager, data_type: DataType):
        self.mongo_manager = mongo_manager
        self.data_type = data_type
        self.collection_name = get_collection_name(data_type)
        
    @abstractmethod
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存数据"""
        pass
    
    @abstractmethod
    async def find(self, **kwargs) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """查找数据"""
        pass
    
    async def count(self, filter_dict: Dict[str, Any] = None) -> int:
        """统计数量"""
        try:
            return await self.mongo_manager.client.count_documents(
                self.collection_name, 
                filter_dict or {}
            )
        except Exception as e:
            logger.error(f"统计数据失败: {self.collection_name}, {e}")
            return 0
    
    async def delete(self, filter_dict: Dict[str, Any]) -> int:
        """删除数据"""
        try:
            return await self.mongo_manager.client.delete_many(
                self.collection_name, 
                filter_dict
            )
        except Exception as e:
            logger.error(f"删除数据失败: {self.collection_name}, {e}")
            return 0


class StockInfoRepository(BaseRepository):
    """股票信息仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.STOCK_INFO)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存股票信息"""
        return await self.mongo_manager.save_stock_info(data)
    
    async def find(self, symbol: str = None, exchange: str = None, sec_type: str = None, is_active: bool = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """查找股票信息"""
        try:
            filter_dict = {}
            
            if symbol:
                filter_dict['symbol'] = symbol
            if exchange:
                filter_dict['exchange'] = exchange
            if sec_type:
                filter_dict['sec_type'] = sec_type
            if is_active is not None:
                filter_dict['is_active'] = is_active
            
            if symbol:
                return await self.mongo_manager.client.find_one(self.collection_name, filter_dict)
            else:
                return await self.mongo_manager.client.find_many(self.collection_name, filter_dict)
                
        except Exception as e:
            logger.error(f"查找股票信息失败: {e}")
            return None
    
    async def get_active_stocks(self, exchange: str = None) -> List[Dict[str, Any]]:
        """获取活跃股票列表"""
        filter_dict = {'is_active': True}
        if exchange:
            filter_dict['exchange'] = exchange
        
        result = await self.find(is_active=True)
        return result if isinstance(result, list) else []
    
    async def update_stock_status(self, symbol: str, is_active: bool) -> bool:
        """更新股票状态"""
        try:
            count = await self.mongo_manager.client.update_one(
                self.collection_name,
                {'symbol': symbol},
                {'is_active': is_active, 'updated_at': datetime.now()}
            )
            return count > 0
        except Exception as e:
            logger.error(f"更新股票状态失败: {symbol}, {e}")
            return False


class TradingCalendarRepository(BaseRepository):
    """交易日历仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.TRADING_CALENDAR)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存交易日历"""
        return await self.mongo_manager.save_trading_calendar(data)
    
    async def find(self, start_date: str = None, end_date: str = None, exchange: str = 'SHSE', is_trading_day: bool = None) -> List[Dict[str, Any]]:
        """查找交易日历"""
        try:
            filter_dict = {'exchange': exchange}
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter['$gte'] = start_date
                if end_date:
                    date_filter['$lte'] = end_date
                filter_dict['date'] = date_filter
            
            if is_trading_day is not None:
                filter_dict['is_trading_day'] = is_trading_day
            
            return await self.mongo_manager.client.find_many(
                self.collection_name,
                filter_dict,
                sort=[('date', 1)]
            )
            
        except Exception as e:
            logger.error(f"查找交易日历失败: {e}")
            return []
    
    async def get_trading_days(self, start_date: str, end_date: str, exchange: str = 'SHSE') -> List[str]:
        """获取交易日列表"""
        try:
            result = await self.find(start_date, end_date, exchange, is_trading_day=True)
            return [item['date'] for item in result]
        except Exception as e:
            logger.error(f"获取交易日列表失败: {e}")
            return []
    
    async def is_trading_day(self, date: str, exchange: str = 'SHSE') -> bool:
        """判断是否为交易日"""
        try:
            result = await self.mongo_manager.client.find_one(
                self.collection_name,
                {'date': date, 'exchange': exchange}
            )
            return result.get('is_trading_day', False) if result else False
        except Exception as e:
            logger.error(f"判断交易日失败: {date}, {e}")
            return False


class RealtimeQuoteRepository(BaseRepository):
    """实时行情仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.REALTIME_QUOTE)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存实时行情"""
        return await self.mongo_manager.save_realtime_quotes(data)
    
    async def find(self, symbols: List[str] = None, start_time: str = None, end_time: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """查找实时行情"""
        try:
            filter_dict = {}
            
            if symbols:
                filter_dict['symbol'] = {'$in': symbols}
            
            if start_time or end_time:
                time_filter = {}
                if start_time:
                    time_filter['$gte'] = start_time
                if end_time:
                    time_filter['$lte'] = end_time
                filter_dict['timestamp'] = time_filter
            
            return await self.mongo_manager.client.find_many(
                self.collection_name,
                filter_dict,
                sort=[('timestamp', -1)],
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"查找实时行情失败: {e}")
            return []
    
    async def get_latest_quotes(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """获取最新行情"""
        return await self.mongo_manager.get_latest_quotes(symbols)
    
    async def cleanup_old_quotes(self, days: int = 7) -> int:
        """清理过期行情数据"""
        return await self.mongo_manager.cleanup_old_data(
            self.collection_name, 
            'timestamp', 
            days
        )


class TickDataRepository(BaseRepository):
    """逐笔数据仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.TICK_DATA)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存逐笔数据"""
        return await self.mongo_manager.save_tick_data(data)
    
    async def find(self, symbol: str, start_time: str = None, end_time: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """查找逐笔数据"""
        try:
            filter_dict = {'symbol': symbol}
            
            if start_time or end_time:
                time_filter = {}
                if start_time:
                    time_filter['$gte'] = start_time
                if end_time:
                    time_filter['$lte'] = end_time
                filter_dict['timestamp'] = time_filter
            
            return await self.mongo_manager.client.find_many(
                self.collection_name,
                filter_dict,
                sort=[('timestamp', 1)],
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"查找逐笔数据失败: {e}")
            return []


class BarDataRepository(BaseRepository):
    """K线数据仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.BAR_DATA)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存K线数据"""
        return await self.mongo_manager.save_bar_data(data)
    
    async def find(self, symbol: str, period: str, start_time: str = None, end_time: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """查找K线数据"""
        return await self.mongo_manager.get_bar_data(symbol, period, start_time, end_time, limit)
    
    async def get_latest_bar(self, symbol: str, period: str) -> Optional[Dict[str, Any]]:
        """获取最新K线"""
        try:
            result = await self.find(symbol, period, limit=1)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"获取最新K线失败: {symbol}, {e}")
            return None
    
    async def get_last_timestamp(self, symbol: str, period: str) -> Optional[str]:
        """获取最后时间戳"""
        try:
            latest_bar = await self.get_latest_bar(symbol, period)
            return latest_bar['timestamp'] if latest_bar else None
        except Exception as e:
            logger.error(f"获取最后时间戳失败: {symbol}, {e}")
            return None


class FinancialDataRepository(BaseRepository):
    """财务数据仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.FINANCIAL_DATA)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存财务数据"""
        return await self.mongo_manager.save_financial_data(data)
    
    async def find(self, symbol: str, data_type: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """查找财务数据"""
        return await self.mongo_manager.get_financial_data(symbol, data_type, start_date, end_date)
    
    async def get_latest_financial_data(self, symbol: str, data_type: str) -> Optional[Dict[str, Any]]:
        """获取最新财务数据"""
        try:
            result = await self.find(symbol, data_type)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"获取最新财务数据失败: {symbol}, {e}")
            return None
    
    async def get_financial_indicators(self, symbol: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """获取财务指标"""
        return await self.find(symbol, 'financial_indicator', start_date, end_date)


class DividendDataRepository(BaseRepository):
    """分红数据仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.DIVIDEND_DATA)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存分红数据"""
        return await self.mongo_manager.save_dividend_data(data)
    
    async def find(self, symbol: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """查找分红数据"""
        try:
            filter_dict = {}
            
            if symbol:
                filter_dict['symbol'] = symbol
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter['$gte'] = start_date
                if end_date:
                    date_filter['$lte'] = end_date
                filter_dict['ex_date'] = date_filter
            
            return await self.mongo_manager.client.find_many(
                self.collection_name,
                filter_dict,
                sort=[('ex_date', -1)]
            )
            
        except Exception as e:
            logger.error(f"查找分红数据失败: {e}")
            return []


class ShareChangeDataRepository(BaseRepository):
    """股本变动数据仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.SHARE_CHANGE_DATA)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存股本变动数据"""
        return await self.mongo_manager.save_share_change_data(data)
    
    async def find(self, symbol: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """查找股本变动数据"""
        try:
            filter_dict = {}
            
            if symbol:
                filter_dict['symbol'] = symbol
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter['$gte'] = start_date
                if end_date:
                    date_filter['$lte'] = end_date
                filter_dict['change_date'] = date_filter
            
            return await self.mongo_manager.client.find_many(
                self.collection_name,
                filter_dict,
                sort=[('change_date', -1)]
            )
            
        except Exception as e:
            logger.error(f"查找股本变动数据失败: {e}")
            return []


class IndexConstituentRepository(BaseRepository):
    """指数成分股仓库"""
    
    def __init__(self, mongo_manager: MongoManager):
        super().__init__(mongo_manager, DataType.INDEX_CONSTITUENT)
    
    async def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存指数成分股数据"""
        return await self.mongo_manager.save_index_constituent(data)
    
    async def find(self, index_symbol: str = None, symbol: str = None, is_active: bool = None) -> List[Dict[str, Any]]:
        """查找指数成分股数据"""
        try:
            filter_dict = {}
            
            if index_symbol:
                filter_dict['index_symbol'] = index_symbol
            if symbol:
                filter_dict['symbol'] = symbol
            if is_active is not None:
                filter_dict['is_active'] = is_active
            
            return await self.mongo_manager.client.find_many(
                self.collection_name,
                filter_dict,
                sort=[('weight', -1)]
            )
            
        except Exception as e:
            logger.error(f"查找指数成分股数据失败: {e}")
            return []
    
    async def get_index_constituents(self, index_symbol: str) -> List[Dict[str, Any]]:
        """获取指数成分股"""
        return await self.find(index_symbol=index_symbol, is_active=True)
    
    async def get_stock_indexes(self, symbol: str) -> List[Dict[str, Any]]:
        """获取股票所属指数"""
        return await self.find(symbol=symbol, is_active=True)


class RepositoryManager:
    """仓库管理器"""
    
    def __init__(self, mongo_manager: MongoManager):
        self.mongo_manager = mongo_manager
        
        # 初始化各种仓库
        self.stock_info = StockInfoRepository(mongo_manager)
        self.trading_calendar = TradingCalendarRepository(mongo_manager)
        self.realtime_quote = RealtimeQuoteRepository(mongo_manager)
        self.tick_data = TickDataRepository(mongo_manager)
        self.bar_data = BarDataRepository(mongo_manager)
        self.financial_data = FinancialDataRepository(mongo_manager)
        self.dividend_data = DividendDataRepository(mongo_manager)
        self.share_change_data = ShareChangeDataRepository(mongo_manager)
        self.index_constituent = IndexConstituentRepository(mongo_manager)
        
        logger.info("仓库管理器初始化完成")
    
    def get_repository(self, data_type: DataType) -> Optional[BaseRepository]:
        """根据数据类型获取对应的仓库"""
        mapping = {
            DataType.STOCK_INFO: self.stock_info,
            DataType.TRADING_CALENDAR: self.trading_calendar,
            DataType.REALTIME_QUOTE: self.realtime_quote,
            DataType.TICK_DATA: self.tick_data,
            DataType.BAR_DATA: self.bar_data,
            DataType.FINANCIAL_DATA: self.financial_data,
            DataType.DIVIDEND_DATA: self.dividend_data,
            DataType.SHARE_CHANGE_DATA: self.share_change_data,
            DataType.INDEX_CONSTITUENT: self.index_constituent,
        }
        return mapping.get(data_type)
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            stats = {}
            
            # 获取各集合统计信息
            for data_type in DataType:
                collection_name = get_collection_name(data_type)
                collection_stats = await self.mongo_manager.get_collection_stats(collection_name)
                stats[data_type.value] = collection_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {e}")
            return {}