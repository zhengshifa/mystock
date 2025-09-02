#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB管理器

负责MongoDB数据库的连接管理、健康检查和基础操作
"""

import asyncio
from typing import Optional, Dict, Any, Union, List
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from ..config.config_manager import ConfigManager
from ..utils.exceptions import DatabaseError


class MongoManager:
    """MongoDB数据库管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化MongoDB管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # MongoDB连接相关
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        
        # 连接状态
        self._is_connected = False
        self._connection_string = self._build_connection_string()
        
        logger.info("MongoDB管理器已创建")
    
    def _build_connection_string(self) -> str:
        """
        构建MongoDB连接字符串
        
        Returns:
            MongoDB连接字符串
        """
        mongodb_config = self.config.get('mongodb', {})
        
        host = mongodb_config.get('host', 'localhost')
        port = mongodb_config.get('port', 27017)
        username = mongodb_config.get('username')
        password = mongodb_config.get('password')
        database = mongodb_config.get('database', 'stock_data')
        auth_source = mongodb_config.get('auth_source', 'admin')
        
        if username and password:
            # 带认证的连接字符串
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource={auth_source}"
        else:
            # 无认证的连接字符串
            connection_string = f"mongodb://{host}:{port}/{database}"
        
        logger.info(f"MongoDB连接字符串已构建: {host}:{port}/{database}")
        return connection_string
    
    async def initialize(self) -> None:
        """
        初始化MongoDB连接
        
        Raises:
            DatabaseError: 初始化失败时抛出
        """
        try:
            logger.info("开始初始化MongoDB连接...")
            
            # 创建MongoDB客户端
            mongodb_config = self.config.get('mongodb', {})
            self.client = AsyncIOMotorClient(
                self._connection_string,
                maxPoolSize=mongodb_config.get('max_pool_size', 100),
                minPoolSize=mongodb_config.get('min_pool_size', 10),
                maxIdleTimeMS=mongodb_config.get('max_idle_time_ms', 30000),
                connectTimeoutMS=mongodb_config.get('connect_timeout_ms', 5000),
                serverSelectionTimeoutMS=mongodb_config.get('server_selection_timeout_ms', 5000)
            )
            
            # 获取数据库实例
            database_name = self.config.get('mongodb', {}).get('database', 'stock_data')
            self.database = self.client[database_name]
            
            logger.info("MongoDB连接初始化完成")
            
        except Exception as e:
            logger.error(f"MongoDB连接初始化失败: {e}")
            raise DatabaseError(f"MongoDB连接初始化失败: {e}") from e
    
    async def start(self) -> None:
        """
        启动MongoDB连接
        
        Raises:
            DatabaseError: 连接失败时抛出
        """
        if not self.client:
            raise DatabaseError("MongoDB客户端未初始化")
        
        try:
            logger.info("正在连接MongoDB...")
            
            # 测试连接
            await self.client.admin.command('ping')
            
            self._is_connected = True
            logger.info("MongoDB连接成功")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB连接失败: {e}")
            raise DatabaseError(f"MongoDB连接失败: {e}") from e
        except Exception as e:
            logger.error(f"MongoDB连接异常: {e}")
            raise DatabaseError(f"MongoDB连接异常: {e}") from e
    
    async def stop(self) -> None:
        """关闭MongoDB连接"""
        try:
            if self.client:
                self.client.close()
                self._is_connected = False
                logger.info("MongoDB连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭MongoDB连接时发生异常: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        执行MongoDB健康检查
        
        Returns:
            包含健康状态的字典
        """
        try:
            if not self.client or not self._is_connected:
                return {
                    "status": "disconnected",
                    "message": "MongoDB未连接"
                }
            
            # 执行ping命令
            result = await self.client.admin.command('ping')
            
            # 获取服务器信息
            server_info = await self.client.server_info()
            
            return {
                "status": "healthy",
                "message": "MongoDB连接正常",
                "server_version": server_info.get('version'),
                "ping_result": result
            }
            
        except Exception as e:
            logger.error(f"MongoDB健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"MongoDB健康检查失败: {e}"
            }
    
    def is_connected(self) -> bool:
        """
        检查MongoDB连接状态
        
        Returns:
            是否已连接
        """
        return self._is_connected
    
    def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        """
        获取数据库实例
        
        Returns:
            MongoDB数据库实例
        """
        return self.database
    
    def get_client(self) -> Optional[AsyncIOMotorClient]:
        """
        获取MongoDB客户端
        
        Returns:
            MongoDB客户端实例
        """
        return self.client
    
    async def create_indexes(self) -> None:
        """
        创建数据库索引
        
        为常用查询字段创建索引以提高查询性能
        """
        try:
            if not self.database:
                raise DatabaseError("数据库未初始化")
            
            logger.info("开始创建数据库索引...")
            
            # 股票信息索引
            stock_info_collection = self.database.stock_info
            await stock_info_collection.create_index("symbol", unique=True)
            await stock_info_collection.create_index("exchange")
            await stock_info_collection.create_index("sec_type")
            
            # 实时行情索引
            quote_collection = self.database.realtime_quote
            await quote_collection.create_index("symbol")
            await quote_collection.create_index("timestamp")
            await quote_collection.create_index([("symbol", 1), ("timestamp", -1)])
            
            # K线数据索引
            bar_collection = self.database.bar_data
            await bar_collection.create_index("symbol")
            await bar_collection.create_index("timestamp")
            await bar_collection.create_index([("symbol", 1), ("timestamp", -1)])
            
            # 财务数据索引
            financial_collection = self.database.financial_data
            await financial_collection.create_index("symbol")
            await financial_collection.create_index("report_date")
            await financial_collection.create_index([("symbol", 1), ("report_date", -1)])
            
            logger.info("数据库索引创建完成")
            
        except Exception as e:
            logger.error(f"创建数据库索引失败: {e}")
            raise DatabaseError(f"创建数据库索引失败: {e}") from e
    
    async def save_document(self, collection_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存文档到指定集合"""
        try:
            if not self.is_connected():
                raise DatabaseError("数据库未连接")
            
            collection = self.database[collection_name]
            
            if isinstance(data, list):
                # 批量插入
                if data:
                    result = await collection.insert_many(data)
                    logger.debug(f"批量插入到 {collection_name}: {len(result.inserted_ids)} 条记录")
                    return len(result.inserted_ids) > 0
            else:
                # 单条插入
                result = await collection.insert_one(data)
                logger.debug(f"插入到 {collection_name}: {result.inserted_id}")
                return result.inserted_id is not None
            
            return True
            
        except Exception as e:
            logger.error(f"保存文档到 {collection_name} 失败: {e}")
            return False
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单条文档"""
        try:
            if not self.is_connected():
                raise DatabaseError("数据库未连接")
            
            collection = self.database[collection_name]
            result = await collection.find_one(filter_dict)
            return result
            
        except Exception as e:
            logger.error(f"查找文档失败: {collection_name}, {e}")
            return None
    
    async def find_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查找多条文档"""
        try:
            if not self.is_connected():
                raise DatabaseError("数据库未连接")
            
            collection = self.database[collection_name]
            cursor = collection.find(filter_dict)
            result = await cursor.to_list(length=None)
            return result
            
        except Exception as e:
            logger.error(f"查找文档失败: {collection_name}, {e}")
            return []
    
    async def update_one(self, collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
        """更新单条文档"""
        try:
            if not self.is_connected():
                raise DatabaseError("数据库未连接")
            
            collection = self.database[collection_name]
            result = await collection.update_one(filter_dict, {"$set": update_dict})
            return result.modified_count
            
        except Exception as e:
            logger.error(f"更新文档失败: {collection_name}, {e}")
            return 0
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取数据库集合统计信息
        
        Returns:
            包含各集合统计信息的字典
        """
        try:
            if not self.database:
                raise DatabaseError("数据库未初始化")
            
            stats = {}
            collection_names = await self.database.list_collection_names()
            
            for collection_name in collection_names:
                collection = self.database[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = {
                    "count": count,
                    "exists": True
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {e}")
            raise DatabaseError(f"获取数据库统计信息失败: {e}") from e
