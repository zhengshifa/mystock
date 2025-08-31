#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB客户端
提供MongoDB数据库操作的统一接口
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config.settings import AppConfig
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    """MongoDB客户端"""
    
    def __init__(self, config=None):
        """初始化MongoDB客户端
        
        Args:
            config: MongoDB配置，如果为None则使用默认配置
        """
        if config is None:
            app_config = AppConfig()
            self.config = app_config.mongodb
        else:
            self.config = config
        
        self.client = None
        self.database = None
        self.connected = False
    
    def connect(self) -> bool:
        """连接到MongoDB
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 创建MongoDB客户端
            self.client = MongoClient(
                self.config.connection_string,
                serverSelectionTimeoutMS=5000  # 5秒超时
            )
            
            # 测试连接
            self.client.admin.command('ping')
            
            # 获取数据库
            self.database = self.client[self.config.database]
            
            self.connected = True
            logger.info(f"成功连接到MongoDB数据库: {self.config.database}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB连接失败: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"MongoDB连接异常: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开MongoDB连接"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("已断开MongoDB连接")
    
    def is_connected(self) -> bool:
        """检查是否已连接
        
        Returns:
            bool: 是否已连接
        """
        return self.connected and self.client is not None
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> bool:
        """插入单个文档
        
        Args:
            collection_name: 集合名称
            document: 要插入的文档
            
        Returns:
            bool: 插入是否成功
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return False
        
        try:
            collection = self.database[collection_name]
            result = collection.insert_one(document)
            logger.debug(f"成功插入文档到 {collection_name}: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"插入文档失败: {e}")
            return False
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> bool:
        """插入多个文档
        
        Args:
            collection_name: 集合名称
            documents: 要插入的文档列表
            
        Returns:
            bool: 插入是否成功
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return False
        
        if not documents:
            logger.warning("没有文档需要插入")
            return True
        
        try:
            collection = self.database[collection_name]
            result = collection.insert_many(documents)
            logger.info(f"成功插入 {len(result.inserted_ids)} 个文档到 {collection_name}")
            return True
        except Exception as e:
            logger.error(f"批量插入文档失败: {e}")
            return False
    
    def find_one(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """查找单个文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            
        Returns:
            Optional[Dict[str, Any]]: 找到的文档，如果没找到则返回None
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return None
        
        try:
            collection = self.database[collection_name]
            result = collection.find_one(filter_dict or {})
            return result
        except Exception as e:
            logger.error(f"查询文档失败: {e}")
            return None
    
    def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
                  limit: int = None, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """查找多个文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            limit: 限制返回数量
            sort: 排序条件
            
        Returns:
            List[Dict[str, Any]]: 找到的文档列表
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return []
        
        try:
            collection = self.database[collection_name]
            cursor = collection.find(filter_dict or {})
            
            if sort:
                cursor = cursor.sort(sort)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"查询文档失败: {e}")
            return []
    
    def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                   update_dict: Dict[str, Any]) -> bool:
        """更新单个文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            update_dict: 更新内容
            
        Returns:
            bool: 更新是否成功
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return False
        
        try:
            collection = self.database[collection_name]
            result = collection.update_one(filter_dict, {'$set': update_dict})
            logger.debug(f"更新文档: 匹配 {result.matched_count} 个，修改 {result.modified_count} 个")
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """删除单个文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            
        Returns:
            bool: 删除是否成功
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return False
        
        try:
            collection = self.database[collection_name]
            result = collection.delete_one(filter_dict)
            logger.debug(f"删除了 {result.deleted_count} 个文档")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """删除多个文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            
        Returns:
            int: 删除的文档数量
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return 0
        
        try:
            collection = self.database[collection_name]
            result = collection.delete_many(filter_dict)
            logger.info(f"删除了 {result.deleted_count} 个文档")
            return result.deleted_count
        except Exception as e:
            logger.error(f"批量删除文档失败: {e}")
            return 0
    
    def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """统计文档数量
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            
        Returns:
            int: 文档数量
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return 0
        
        try:
            collection = self.database[collection_name]
            count = collection.count_documents(filter_dict or {})
            return count
        except Exception as e:
            logger.error(f"统计文档数量失败: {e}")
            return 0
    
    def create_index(self, collection_name: str, index_spec: List[tuple], 
                     unique: bool = False) -> bool:
        """创建索引
        
        Args:
            collection_name: 集合名称
            index_spec: 索引规范，例如 [('symbol', 1), ('pub_date', -1)]
            unique: 是否为唯一索引
            
        Returns:
            bool: 创建是否成功
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return False
        
        try:
            collection = self.database[collection_name]
            result = collection.create_index(index_spec, unique=unique)
            logger.info(f"成功创建索引 {result} 在集合 {collection_name}")
            return True
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    def get_collection_names(self) -> List[str]:
        """获取所有集合名称
        
        Returns:
            List[str]: 集合名称列表
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return []
        
        try:
            return self.database.list_collection_names()
        except Exception as e:
            logger.error(f"获取集合名称失败: {e}")
            return []
    
    def drop_collection(self, collection_name: str) -> bool:
        """删除集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 删除是否成功
        """
        if not self.is_connected():
            logger.error("MongoDB未连接")
            return False
        
        try:
            self.database.drop_collection(collection_name)
            logger.info(f"成功删除集合 {collection_name}")
            return True
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False