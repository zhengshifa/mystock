#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具模块
提供MongoDB连接和操作的统一接口
"""

import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime, timedelta

from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, mongodb_config=None):
        self.config = mongodb_config or config.mongodb
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
        
    def connect(self) -> bool:
        """连接到MongoDB"""
        try:
            self._client = MongoClient(
                self.config.connection_string,
                serverSelectionTimeoutMS=5000
            )
            # 测试连接
            self._client.admin.command('ping')
            self._database = self._client[self.config.database]
            logger.info(f"成功连接到MongoDB: {self.config.host}:{self.config.port}/{self.config.database}")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"MongoDB连接异常: {e}")
            return False
    
    def disconnect(self):
        """断开MongoDB连接"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB连接已关闭")
    
    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """获取集合"""
        if self._database is None:
            logger.error("数据库未连接")
            return None
        return self._database[collection_name]
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> bool:
        """插入单个文档"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return False
            
            # 添加时间戳
            if 'created_at' not in document:
                document['created_at'] = datetime.now()
            
            result = collection.insert_one(document)
            logger.debug(f"文档插入成功: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"插入文档失败: {e}")
            return False
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> bool:
        """批量插入文档"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return False
            
            # 添加时间戳
            now = datetime.now()
            for doc in documents:
                if 'created_at' not in doc:
                    doc['created_at'] = now
            
            result = collection.insert_many(documents)
            logger.info(f"批量插入成功: {len(result.inserted_ids)}条记录")
            return True
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            return False
    
    def find_one(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return None
            
            return collection.find_one(filter_dict or {})
        except Exception as e:
            logger.error(f"查询文档失败: {e}")
            return None
    
    def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
                  limit: int = 0, sort_field: str = None, sort_order: int = -1) -> List[Dict[str, Any]]:
        """查找多个文档"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return []
            
            cursor = collection.find(filter_dict or {})
            
            if sort_field:
                cursor = cursor.sort(sort_field, sort_order)
            
            if limit > 0:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"查询文档失败: {e}")
            return []
    
    def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                   update_dict: Dict[str, Any]) -> bool:
        """更新单个文档"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return False
            
            # 添加更新时间戳
            if '$set' not in update_dict:
                update_dict = {'$set': update_dict}
            update_dict['$set']['updated_at'] = datetime.now()
            
            result = collection.update_one(filter_dict, update_dict)
            logger.debug(f"文档更新成功: 匹配{result.matched_count}条，修改{result.modified_count}条")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    def update_one_upsert(self, collection_name: str, filter_dict: Dict[str, Any], 
                          update_dict: Dict[str, Any]) -> bool:
        """更新单个文档，如果不存在则插入（upsert）"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return False
            
            # 添加更新时间戳
            if '$set' not in update_dict:
                update_dict = {'$set': update_dict}
            update_dict['$set']['updated_at'] = datetime.now()
            
            result = collection.update_one(filter_dict, update_dict, upsert=True)
            logger.debug(f"文档更新/插入成功: 匹配{result.matched_count}条，修改{result.modified_count}条，插入{result.upserted_id}")
            return True
        except Exception as e:
            logger.error(f"更新/插入文档失败: {e}")
            return False
    
    def delete_old_data(self, collection_name: str, days: int) -> int:
        """删除指定天数前的旧数据"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=days)
            result = collection.delete_many({'created_at': {'$lt': cutoff_date}})
            
            if result.deleted_count > 0:
                logger.info(f"删除{collection_name}中{result.deleted_count}条旧数据")
            
            return result.deleted_count
        except Exception as e:
            logger.error(f"删除旧数据失败: {e}")
            return 0
    
    def create_index(self, collection_name: str, index_spec: List[tuple]):
        """创建索引"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return False
            
            collection.create_index(index_spec)
            logger.info(f"为{collection_name}创建索引成功")
            return True
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    def get_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return {}
            
            stats = self._database.command('collStats', collection_name)
            return {
                'count': stats.get('count', 0),
                'size': stats.get('size', 0),
                'avgObjSize': stats.get('avgObjSize', 0),
                'storageSize': stats.get('storageSize', 0)
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def cleanup_old_data(self):
        """清理所有集合的旧数据"""
        logger.info("开始清理旧数据...")
        total_deleted = 0
        
        for collection_name, retention_days in config.data.data_retention_days.items():
            deleted_count = self.delete_old_data(collection_name, retention_days)
            total_deleted += deleted_count
        
        logger.info(f"旧数据清理完成，共删除{total_deleted}条记录")
        return total_deleted
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._client is not None and self._database is not None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()

# 全局数据库管理器实例
db_manager = DatabaseManager()