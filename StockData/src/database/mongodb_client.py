"""
MongoDB客户端模块
提供异步MongoDB连接和操作功能
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo import ReplaceOne
from ..config import settings


class MongoDBClient:
    """MongoDB异步客户端"""
    
    def __init__(self):
        """初始化MongoDB客户端"""
        self.logger = logging.getLogger(__name__)
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self._collections: Dict[str, AsyncIOMotorCollection] = {}
    
    async def connect(self) -> bool:
        """
        连接到MongoDB数据库
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # 测试连接
            await self.client.admin.command('ping')
            
            # 获取数据库
            self.database = self.client[settings.mongodb_database]
            
            # 初始化集合
            self._collections = {
                'tick': self.database[settings.mongodb_collection_tick],
                'sync_log': self.database[settings.mongodb_collection_sync_log],
                'symbol_info': self.database['symbol_info']
            }
            
            # 初始化多频率Bar集合
            for frequency in settings.enabled_frequencies:
                collection_name = settings.get_frequency_collection_name(frequency)
                self._collections[f'bar_{frequency}'] = self.database[collection_name]
            
            # 创建索引
            await self._create_indexes()
            
            self.logger.info(f"成功连接到MongoDB: {settings.mongodb_database}")
            return True
            
        except ConnectionFailure as e:
            self.logger.error(f"MongoDB连接失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"MongoDB初始化失败: {e}")
            return False
    
    async def disconnect(self):
        """断开MongoDB连接"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB连接已断开")
    
    async def _create_indexes(self):
        """创建数据库索引"""
        try:
            # Tick数据索引
            tick_collection = self._collections['tick']
            await tick_collection.create_index([("symbol", 1), ("created_at", -1)])
            await tick_collection.create_index([("created_at", -1)])
            await tick_collection.create_index([("symbol", 1)])
            
            # 多频率Bar数据索引
            for frequency in settings.enabled_frequencies:
                collection_key = f'bar_{frequency}'
                if collection_key in self._collections:
                    bar_collection = self._collections[collection_key]
                    await bar_collection.create_index([("symbol", 1), ("eob", -1)])
                    await bar_collection.create_index([("eob", -1)])
                    await bar_collection.create_index([("symbol", 1)])
                    await bar_collection.create_index([("symbol", 1), ("frequency", 1)])
            
            # 同步日志索引
            sync_log_collection = self._collections['sync_log']
            await sync_log_collection.create_index([("sync_time", -1)])
            await sync_log_collection.create_index([("symbol", 1), ("sync_time", -1)])
            await sync_log_collection.create_index([("operation_type", 1), ("sync_time", -1)])
            
            self.logger.info("数据库索引创建完成")
            
        except Exception as e:
            self.logger.error(f"创建索引失败: {e}")
    
    async def insert_tick_data(self, tick_data: List[Dict]) -> bool:
        """
        插入Tick数据
        
        Args:
            tick_data: Tick数据列表
            
        Returns:
            bool: 插入是否成功
        """
        try:
            if not tick_data:
                return True
            
            collection = self._collections['tick']
            result = await collection.insert_many(tick_data)
            
            self.logger.info(f"成功插入 {len(result.inserted_ids)} 条Tick数据")
            return True
            
        except Exception as e:
            self.logger.error(f"插入Tick数据失败: {e}")
            return False
    
    async def insert_bar_data(self, bar_data: List[Dict], frequency: str) -> bool:
        """
        插入Bar数据到指定频率集合
        
        Args:
            bar_data: Bar数据列表
            frequency: 数据频率
            
        Returns:
            bool: 插入是否成功
        """
        try:
            if not bar_data:
                return True
            
            collection_key = f'bar_{frequency}'
            if collection_key not in self._collections:
                self.logger.error(f"未找到频率 {frequency} 对应的集合")
                return False
            
            collection = self._collections[collection_key]
            result = await collection.insert_many(bar_data)
            
            self.logger.info(f"成功插入 {len(result.inserted_ids)} 条{frequency} Bar数据")
            return True
            
        except Exception as e:
            self.logger.error(f"插入{frequency} Bar数据失败: {e}")
            return False
    
    async def upsert_bar_data(self, bar_data: List[Dict], frequency: str) -> bool:
        """
        更新或插入Bar数据到指定频率集合（避免重复）
        
        Args:
            bar_data: Bar数据列表
            frequency: 数据频率
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not bar_data:
                return True
            
            collection_key = f'bar_{frequency}'
            if collection_key not in self._collections:
                self.logger.error(f"未找到频率 {frequency} 对应的集合")
                return False
            
            collection = self._collections[collection_key]
            from pymongo import ReplaceOne
            
            operations = []
            
            for data in bar_data:
                filter_doc = {
                    'symbol': data['symbol'],
                    'frequency': data['frequency'],
                    'eob': data['eob']
                }
                operations.append(ReplaceOne(filter_doc, data, upsert=True))
            
            if operations:
                result = await collection.bulk_write(operations)
                self.logger.info(f"成功处理 {result.upserted_count + result.modified_count} 条{frequency} Bar数据")
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新{frequency} Bar数据失败: {e}")
            return False
    
    async def get_latest_tick_time(self, symbol: str) -> Optional[datetime]:
        """
        获取指定股票的最新Tick时间
        
        Args:
            symbol: 股票代码
            
        Returns:
            Optional[datetime]: 最新时间，如果没有数据则返回None
        """
        try:
            collection = self._collections['tick']
            result = await collection.find_one(
                {'symbol': symbol},
                sort=[('created_at', -1)],
                projection={'created_at': 1}
            )
            
            return result['created_at'] if result else None
            
        except Exception as e:
            self.logger.error(f"获取最新Tick时间失败: {e}")
            return None
    
    async def get_latest_bar_time(self, symbol: str, frequency: str) -> Optional[datetime]:
        """
        获取指定股票和频率的最新Bar时间
        
        Args:
            symbol: 股票代码
            frequency: 频率
            
        Returns:
            Optional[datetime]: 最新时间，如果没有数据则返回None
        """
        try:
            collection_key = f'bar_{frequency}'
            if collection_key not in self._collections:
                self.logger.error(f"未找到频率 {frequency} 对应的集合")
                return None
            
            collection = self._collections[collection_key]
            result = await collection.find_one(
                {'symbol': symbol, 'frequency': frequency},
                sort=[('eob', -1)],
                projection={'eob': 1}
            )
            
            return result['eob'] if result else None
            
        except Exception as e:
            self.logger.error(f"获取最新{frequency} Bar时间失败: {e}")
            return None
    
    async def log_sync_operation(self, symbol: str, operation_type: str, 
                                start_time: datetime, end_time: datetime,
                                record_count: int, status: str, 
                                error_message: Optional[str] = None) -> bool:
        """
        记录同步操作日志
        
        Args:
            symbol: 股票代码
            operation_type: 操作类型 (tick/bar)
            start_time: 开始时间
            end_time: 结束时间
            record_count: 记录数量
            status: 状态 (success/failed)
            error_message: 错误信息
            
        Returns:
            bool: 记录是否成功
        """
        try:
            collection = self._collections['sync_log']
            log_entry = {
                'symbol': symbol,
                'operation_type': operation_type,
                'start_time': start_time,
                'end_time': end_time,
                'sync_time': datetime.now(),
                'record_count': record_count,
                'status': status,
                'error_message': error_message
            }
            
            await collection.insert_one(log_entry)
            return True
            
        except Exception as e:
            self.logger.error(f"记录同步日志失败: {e}")
            return False
    
    async def get_sync_history(self, symbol: Optional[str] = None, 
                              limit: int = 100) -> List[Dict]:
        """
        获取同步历史记录
        
        Args:
            symbol: 股票代码，None表示所有股票
            limit: 限制数量
            
        Returns:
            List[Dict]: 同步历史记录
        """
        try:
            collection = self._collections['sync_log']
            filter_doc = {'symbol': symbol} if symbol else {}
            
            cursor = collection.find(filter_doc).sort('sync_time', -1).limit(limit)
            results = await cursor.to_list(length=limit)
            
            return results
            
        except Exception as e:
            self.logger.error(f"获取同步历史失败: {e}")
            return []
    
    async def get_frequency_statistics(self) -> Dict[str, Dict]:
        """
        获取各频率数据统计
        
        Returns:
            Dict[str, Dict]: 各频率的数据统计
        """
        try:
            statistics = {}
            
            # Tick数据统计
            tick_collection = self._collections['tick']
            tick_count = await tick_collection.count_documents({})
            statistics['tick'] = {'count': tick_count}
            
            # 各频率Bar数据统计
            for frequency in settings.enabled_frequencies:
                collection_key = f'bar_{frequency}'
                if collection_key in self._collections:
                    collection = self._collections[collection_key]
                    count = await collection.count_documents({})
                    
                    # 获取最新数据时间
                    latest = await collection.find_one(
                        {}, sort=[('eob', -1)], projection={'eob': 1, 'symbol': 1}
                    )
                    
                    statistics[frequency] = {
                        'count': count,
                        'latest_time': latest['eob'] if latest else None,
                        'latest_symbol': latest['symbol'] if latest else None
                    }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"获取频率统计失败: {e}")
            return {}
    
    async def save_symbol_infos(self, symbol_infos: List[Dict]) -> bool:
        """
        保存标的基本信息到数据库
        
        Args:
            symbol_infos: 标的基本信息列表
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not symbol_infos:
                self.logger.warning("没有标的基本信息需要保存")
                return True
            
            collection = self._collections['symbol_info']
            
            # 准备批量操作
            operations = []
            for info in symbol_infos:
                # 使用symbol作为唯一标识符
                filter_doc = {'symbol': info['symbol']}
                
                # 添加时间戳
                info['updated_at'] = datetime.now()
                if 'created_at' not in info:
                    info['created_at'] = datetime.now()
                
                # 使用upsert操作（存在则更新，不存在则插入）
                operations.append(ReplaceOne(
                    filter=filter_doc,
                    replacement=info,
                    upsert=True
                ))
            
            # 执行批量操作
            if operations:
                result = await collection.bulk_write(operations)
                self.logger.info(f"成功保存 {len(symbol_infos)} 条标的基本信息，"
                               f"插入: {result.upserted_count}, 更新: {result.modified_count}")
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存标的基本信息失败: {e}")
            return False
    
    async def get_symbol_infos(self, 
                              sec_type1: Optional[int] = None,
                              sec_type2: Optional[int] = None,
                              exchange: Optional[str] = None,
                              limit: int = 100) -> List[Dict]:
        """
        从数据库查询标的基本信息
        
        Args:
            sec_type1: 证券品种大类
            sec_type2: 证券品种细类
            exchange: 交易所代码
            limit: 限制数量
            
        Returns:
            List[Dict]: 标的基本信息列表
        """
        try:
            collection = self._collections['symbol_info']
            
            # 构建查询条件
            filter_doc = {}
            if sec_type1 is not None:
                filter_doc['sec_type1'] = sec_type1
            if sec_type2 is not None:
                filter_doc['sec_type2'] = sec_type2
            if exchange:
                filter_doc['exchange'] = exchange
            
            cursor = collection.find(filter_doc).sort('symbol', 1).limit(limit)
            results = await cursor.to_list(length=limit)
            
            self.logger.info(f"从数据库查询到 {len(results)} 条标的基本信息")
            return results
            
        except Exception as e:
            self.logger.error(f"查询标的基本信息失败: {e}")
            return []
    
    async def get_symbol_info_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        根据标的代码查询标的基本信息
        
        Args:
            symbol: 标的代码
            
        Returns:
            Optional[Dict]: 标的基本信息，如果不存在返回None
        """
        try:
            collection = self._collections['symbol_info']
            result = await collection.find_one({'symbol': symbol})
            return result
            
        except Exception as e:
            self.logger.error(f"查询标的 {symbol} 基本信息失败: {e}")
            return None
    
    async def delete_symbol_info(self, symbol: str) -> bool:
        """
        删除标的基本信息
        
        Args:
            symbol: 标的代码
            
        Returns:
            bool: 删除是否成功
        """
        try:
            collection = self._collections['symbol_info']
            result = await collection.delete_one({'symbol': symbol})
            
            if result.deleted_count > 0:
                self.logger.info(f"成功删除标的 {symbol} 的基本信息")
                return True
            else:
                self.logger.warning(f"标的 {symbol} 的基本信息不存在")
                return False
                
        except Exception as e:
            self.logger.error(f"删除标的 {symbol} 基本信息失败: {e}")
            return False
    
    async def get_all_stock_symbols(self, sec_type1: int = 1010, sec_type2: int = 101001) -> List[str]:
        """
        获取所有股票代码列表
        
        Args:
            sec_type1: 证券品种大类，默认1010(股票)
            sec_type2: 证券品种细类，默认101001(A股)
            
        Returns:
            List[str]: 股票代码列表
        """
        try:
            collection = self._collections['symbol_info']
            
            # 查询指定类型的股票
            cursor = collection.find(
                {'sec_type1': sec_type1, 'sec_type2': sec_type2},
                {'symbol': 1, '_id': 0}
            ).sort('symbol', 1)
            
            symbols = await cursor.to_list(length=None)
            symbol_list = [doc['symbol'] for doc in symbols if 'symbol' in doc]
            
            self.logger.info(f"从数据库获取到 {len(symbol_list)} 个股票代码")
            return symbol_list
            
        except Exception as e:
            self.logger.error(f"获取所有股票代码失败: {e}")
            return []
    
    async def get_all_symbols_by_types(self, symbol_types: List[Dict]) -> List[str]:
        """
        根据多个证券类型获取所有标的代码
        
        Args:
            symbol_types: 证券类型列表，格式为[{'sec_type1': 1010, 'sec_type2': 101001}, ...]
            
        Returns:
            List[str]: 标的代码列表
        """
        try:
            collection = self._collections['symbol_info']
            
            # 构建查询条件
            or_conditions = []
            for symbol_type in symbol_types:
                or_conditions.append({
                    'sec_type1': symbol_type['sec_type1'],
                    'sec_type2': symbol_type['sec_type2']
                })
            
            cursor = collection.find(
                {'$or': or_conditions},
                {'symbol': 1, '_id': 0}
            ).sort('symbol', 1)
            
            symbols = await cursor.to_list(length=None)
            symbol_list = [doc['symbol'] for doc in symbols if 'symbol' in doc]
            
            self.logger.info(f"从数据库获取到 {len(symbol_list)} 个标的代码")
            return symbol_list
            
        except Exception as e:
            self.logger.error(f"获取所有标的代码失败: {e}")
            return []
    
    async def get_symbol_info_statistics(self) -> Dict[str, Any]:
        """
        获取标的基本信息统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            collection = self._collections['symbol_info']
            
            # 总数量
            total_count = await collection.count_documents({})
            
            # 按证券大类统计
            pipeline = [
                {'$group': {
                    '_id': '$sec_type1',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]
            
            type1_stats = []
            async for doc in collection.aggregate(pipeline):
                type1_stats.append({
                    'sec_type1': doc['_id'],
                    'count': doc['count']
                })
            
            # 按交易所统计
            pipeline = [
                {'$group': {
                    '_id': '$exchange',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]
            
            exchange_stats = []
            async for doc in collection.aggregate(pipeline):
                exchange_stats.append({
                    'exchange': doc['_id'],
                    'count': doc['count']
                })
            
            # 最新更新时间
            latest = await collection.find_one(
                {}, sort=[('updated_at', -1)], projection={'updated_at': 1, 'symbol': 1}
            )
            
            return {
                'total_count': total_count,
                'type1_statistics': type1_stats,
                'exchange_statistics': exchange_stats,
                'latest_update': latest['updated_at'] if latest else None,
                'latest_symbol': latest['symbol'] if latest else None
            }
            
        except Exception as e:
            self.logger.error(f"获取标的基本信息统计失败: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 数据库是否健康
        """
        try:
            if not self.client:
                return False
            
            await self.client.admin.command('ping')
            return True
            
        except Exception as e:
            self.logger.error(f"数据库健康检查失败: {e}")
            return False


# 全局MongoDB客户端实例
mongodb_client = MongoDBClient()
