#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB客户端

负责MongoDB数据库连接管理，包括:
- 连接池管理
- 连接状态监控
- 自动重连机制
- 数据库操作封装
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo import IndexModel, ASCENDING, DESCENDING


class MongoClient:
    """MongoDB异步客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 27017)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.database_name = config.get('database', 'stock_data')
        self.auth_source = config.get('auth_source', 'admin')
        
        # 连接池配置
        self.max_pool_size = config.get('max_pool_size', 100)
        self.min_pool_size = config.get('min_pool_size', 10)
        self.max_idle_time_ms = config.get('max_idle_time_ms', 30000)
        self.connect_timeout_ms = config.get('connect_timeout_ms', 5000)
        self.server_selection_timeout_ms = config.get('server_selection_timeout_ms', 5000)
        
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.is_connected = False
        self.connection_time = None
        
        logger.info("MongoDB客户端初始化完成")
    
    async def connect(self) -> bool:
        """连接到MongoDB"""
        try:
            logger.info(f"正在连接MongoDB: {self.host}:{self.port}")
            
            # 构建连接URI
            if self.username and self.password:
                uri = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}?authSource={self.auth_source}"
            else:
                uri = f"mongodb://{self.host}:{self.port}/{self.database_name}"
            
            # 创建客户端
            self.client = AsyncIOMotorClient(
                uri,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                maxIdleTimeMS=self.max_idle_time_ms,
                connectTimeoutMS=self.connect_timeout_ms,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms
            )
            
            # 获取数据库
            self.database = self.client[self.database_name]
            
            # 测试连接
            await self.client.admin.command('ping')
            
            self.is_connected = True
            self.connection_time = datetime.now()
            
            logger.info(f"MongoDB连接成功: {self.database_name}")
            
            # 创建索引
            await self._create_indexes()
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"MongoDB连接异常: {e}")
            return False
    
    async def disconnect(self):
        """断开MongoDB连接"""
        try:
            if self.client:
                logger.info("正在断开MongoDB连接")
                self.client.close()
                self.client = None
                self.database = None
                self.is_connected = False
                self.connection_time = None
                logger.info("MongoDB连接已断开")
        except Exception as e:
            logger.error(f"断开MongoDB连接异常: {e}")
    
    async def _create_indexes(self):
        """创建数据库索引"""
        try:
            logger.info("正在创建数据库索引")
            
            # 股票基本信息索引
            await self.database.stock_info.create_indexes([
                IndexModel([('symbol', ASCENDING)], unique=True),
                IndexModel([('exchange', ASCENDING)]),
                IndexModel([('sec_type', ASCENDING)]),
                IndexModel([('is_active', ASCENDING)])
            ])
            
            # 交易日历索引
            await self.database.trading_calendar.create_indexes([
                IndexModel([('date', ASCENDING)], unique=True),
                IndexModel([('exchange', ASCENDING)])
            ])
            
            # 实时行情索引
            await self.database.realtime_quotes.create_indexes([
                IndexModel([('symbol', ASCENDING), ('timestamp', DESCENDING)]),
                IndexModel([('timestamp', DESCENDING)])
            ])
            
            # 逐笔数据索引
            await self.database.tick_data.create_indexes([
                IndexModel([('symbol', ASCENDING), ('timestamp', DESCENDING)]),
                IndexModel([('timestamp', DESCENDING)])
            ])
            
            # K线数据索引
            await self.database.bar_data.create_indexes([
                IndexModel([('symbol', ASCENDING), ('period', ASCENDING), ('timestamp', DESCENDING)]),
                IndexModel([('timestamp', DESCENDING)])
            ])
            
            # 财务数据索引
            await self.database.financial_data.create_indexes([
                IndexModel([('symbol', ASCENDING), ('data_type', ASCENDING), ('end_date', DESCENDING)]),
                IndexModel([('data_type', ASCENDING)]),
                IndexModel([('end_date', DESCENDING)])
            ])
            
            # 分红数据索引
            await self.database.dividend_data.create_indexes([
                IndexModel([('symbol', ASCENDING), ('ex_date', DESCENDING)]),
                IndexModel([('ex_date', DESCENDING)])
            ])
            
            # 股本变动数据索引
            await self.database.share_change_data.create_indexes([
                IndexModel([('symbol', ASCENDING), ('change_date', DESCENDING)]),
                IndexModel([('change_date', DESCENDING)])
            ])
            
            # 指数成分股索引
            await self.database.index_constituent.create_indexes([
                IndexModel([('index_symbol', ASCENDING), ('symbol', ASCENDING)]),
                IndexModel([('symbol', ASCENDING)]),
                IndexModel([('in_date', DESCENDING)])
            ])
            
            logger.info("数据库索引创建完成")
            
        except Exception as e:
            logger.error(f"创建数据库索引失败: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.is_connected or not self.client:
                return {
                    'status': 'disconnected',
                    'error': 'MongoDB未连接'
                }
            
            # 执行ping命令
            start_time = datetime.now()
            await self.client.admin.command('ping')
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 获取服务器状态
            server_status = await self.client.admin.command('serverStatus')
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'connection_time': self.connection_time.isoformat() if self.connection_time else None,
                'database': self.database_name,
                'server_version': server_status.get('version', 'unknown'),
                'uptime_seconds': server_status.get('uptime', 0)
            }
            
        except Exception as e:
            logger.error(f"MongoDB健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    # ==================== 数据库操作方法 ====================
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """插入单个文档"""
        try:
            result = await self.database[collection].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"插入文档失败: {collection}, {e}")
            raise
    
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """插入多个文档"""
        try:
            if not documents:
                return []
            
            result = await self.database[collection].insert_many(documents, ordered=False)
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"批量插入文档失败: {collection}, {e}")
            raise
    
    async def find_one(self, collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        try:
            return await self.database[collection].find_one(filter_dict)
        except Exception as e:
            logger.error(f"查找文档失败: {collection}, {e}")
            raise
    
    async def find_many(self, 
                       collection: str, 
                       filter_dict: Dict[str, Any] = None,
                       sort: List[tuple] = None,
                       limit: int = None,
                       skip: int = None) -> List[Dict[str, Any]]:
        """查找多个文档"""
        try:
            cursor = self.database[collection].find(filter_dict or {})
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"查找文档失败: {collection}, {e}")
            raise
    
    async def update_one(self, 
                        collection: str, 
                        filter_dict: Dict[str, Any], 
                        update_dict: Dict[str, Any],
                        upsert: bool = False) -> int:
        """更新单个文档"""
        try:
            result = await self.database[collection].update_one(
                filter_dict, 
                {'$set': update_dict}, 
                upsert=upsert
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"更新文档失败: {collection}, {e}")
            raise
    
    async def update_many(self, 
                         collection: str, 
                         filter_dict: Dict[str, Any], 
                         update_dict: Dict[str, Any]) -> int:
        """更新多个文档"""
        try:
            result = await self.database[collection].update_many(
                filter_dict, 
                {'$set': update_dict}
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"批量更新文档失败: {collection}, {e}")
            raise
    
    async def delete_one(self, collection: str, filter_dict: Dict[str, Any]) -> int:
        """删除单个文档"""
        try:
            result = await self.database[collection].delete_one(filter_dict)
            return result.deleted_count
        except Exception as e:
            logger.error(f"删除文档失败: {collection}, {e}")
            raise
    
    async def delete_many(self, collection: str, filter_dict: Dict[str, Any]) -> int:
        """删除多个文档"""
        try:
            result = await self.database[collection].delete_many(filter_dict)
            return result.deleted_count
        except Exception as e:
            logger.error(f"批量删除文档失败: {collection}, {e}")
            raise
    
    async def count_documents(self, collection: str, filter_dict: Dict[str, Any] = None) -> int:
        """统计文档数量"""
        try:
            return await self.database[collection].count_documents(filter_dict or {})
        except Exception as e:
            logger.error(f"统计文档数量失败: {collection}, {e}")
            raise
    
    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """聚合查询"""
        try:
            cursor = self.database[collection].aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"聚合查询失败: {collection}, {e}")
            raise
    
    async def bulk_write(self, collection: str, operations: List) -> Dict[str, Any]:
        """批量写操作"""
        try:
            result = await self.database[collection].bulk_write(operations, ordered=False)
            return {
                'inserted_count': result.inserted_count,
                'modified_count': result.modified_count,
                'deleted_count': result.deleted_count,
                'upserted_count': result.upserted_count
            }
        except Exception as e:
            logger.error(f"批量写操作失败: {collection}, {e}")
            raise
    
    # ==================== 上下文管理器 ====================
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    def get_collection(self, name: str):
        """获取集合对象"""
        if not self.database:
            raise Exception("数据库未连接")
        return self.database[name]
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            'is_connected': self.is_connected,
            'host': self.host,
            'port': self.port,
            'database': self.database_name,
            'connection_time': self.connection_time.isoformat() if self.connection_time else None,
            'max_pool_size': self.max_pool_size,
            'min_pool_size': self.min_pool_size
        }