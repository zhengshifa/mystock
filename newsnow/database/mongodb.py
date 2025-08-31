"""MongoDB 数据库连接和操作"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from loguru import logger

from .models import NewsItem, SourceResponse, SourceInfo


class MongoDBConnection:
    """MongoDB 连接管理类"""
    
    def __init__(self):
        """初始化 MongoDB 连接"""
        self.client: Optional[MongoClient] = None
        self.db = None
        self.news_collection = None
        self.sources_collection = None
        
    async def connect(self, connection_string: str = "mongodb://localhost:27017/", 
                     database_name: str = "newsnow"):
        """连接到 MongoDB"""
        try:
            # 创建客户端连接
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # 测试连接
            self.client.admin.command('ping')
            logger.info("MongoDB 连接成功")
            
            # 获取数据库和集合
            self.db = self.client[database_name]
            self.news_collection = self.db.news
            self.sources_collection = self.db.sources
            
            # 创建索引
            await self._create_indexes()
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB 连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"MongoDB 初始化失败: {e}")
            return False
    
    async def _create_indexes(self):
        """创建数据库索引"""
        try:
            # 新闻集合索引
            if self.news_collection is not None:
                self.news_collection.create_index([("source_id", 1)])
                self.news_collection.create_index([("published_at", -1)])
                self.news_collection.create_index([("url", 1)], unique=True)
            
            # 新闻源集合索引
            if self.sources_collection is not None:
                self.sources_collection.create_index([("id", 1)], unique=True)
            
            logger.info("数据库索引创建完成")
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
    
    async def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 连接已关闭")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.client:
                return False
            
            self.client.admin.command('ping')
            return True
            
        except Exception:
            return False
    
    async def save_news(self, news_items: List[NewsItem]) -> bool:
        """保存新闻数据"""
        try:
            if self.news_collection is None:
                logger.error("数据库连接未建立")
                return False
            
            # 使用 upsert 操作，避免重复键错误
            saved_count = 0
            updated_count = 0
            
            for item in news_items:
                news_dict = item.to_dict()
                news_dict["created_at"] = datetime.now()
                
                # 使用 upsert 操作，如果 URL 已存在则更新，否则插入
                result = self.news_collection.update_one(
                    {"url": item.url},  # 根据 URL 查找
                    {"$set": news_dict},  # 设置新值
                    upsert=True  # 如果不存在则插入
                )
                
                if result.upserted_id:
                    saved_count += 1
                elif result.modified_count > 0:
                    updated_count += 1
            
            if saved_count > 0 or updated_count > 0:
                logger.info(f"成功处理 {len(news_items)} 条新闻: 新增 {saved_count} 条，更新 {updated_count} 条")
                return True
            else:
                logger.warning("没有新闻需要保存或更新")
                return True
            
        except Exception as e:
            logger.error(f"保存新闻失败: {e}")
            return False
    
    async def get_news_by_source(self, source_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """根据新闻源获取新闻"""
        try:
            if not self.news_collection:
                return []
            
            cursor = self.news_collection.find(
                {"source_id": source_id},
                {"_id": 0}
            ).sort("published_at", -1).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            return []
    
    async def save_source_info(self, source_info: SourceInfo) -> bool:
        """保存新闻源信息"""
        try:
            if not self.sources_collection:
                return False
            
            # 更新或插入
            self.sources_collection.update_one(
                {"id": source_info.id},
                {"$set": source_info.to_dict()},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"保存新闻源信息失败: {e}")
            return False
    
    async def get_all_sources_info(self) -> List[Dict[str, Any]]:
        """获取所有新闻源信息"""
        try:
            if not self.sources_collection:
                return []
            
            cursor = self.sources_collection.find({}, {"_id": 0})
            return list(cursor)
            
        except Exception as e:
            logger.error(f"获取新闻源信息失败: {e}")
            return []


# 全局数据库连接实例
_mongodb_connection: Optional[MongoDBConnection] = None


async def init_mongodb(connection_string: str = None, 
                      database_name: str = None) -> bool:
    """初始化 MongoDB 连接"""
    global _mongodb_connection
    
    try:
        # 导入配置
        from utils.config import get_config
        config = get_config()
        
        # 如果没有提供连接字符串，从配置构建
        if connection_string is None:
            username = config.get("MONGODB_USERNAME")
            password = config.get("MONGODB_PASSWORD")
            host = config.get("MONGODB_HOST", "localhost")
            port = config.get("MONGODB_PORT", "27017")
            auth_source = config.get("MONGODB_AUTH_SOURCE", "admin")
            
            if username and password:
                # 使用认证的连接字符串
                connection_string = f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_source}"
                logger.info(f"使用认证连接 MongoDB: {host}:{port}")
            else:
                # 无认证连接
                connection_string = f"mongodb://{host}:{port}/"
                logger.info(f"使用无认证连接 MongoDB: {host}:{port}")
        
        # 如果没有提供数据库名，从配置获取
        if database_name is None:
            database_name = config.get("MONGODB_DATABASE", "newsnow")
        
        _mongodb_connection = MongoDBConnection()
        success = await _mongodb_connection.connect(connection_string, database_name)
        
        if success:
            logger.info("MongoDB 初始化成功")
        else:
            logger.error("MongoDB 初始化失败")
        
        return success
        
    except Exception as e:
        logger.error(f"MongoDB 初始化异常: {e}")
        return False


async def close_mongodb():
    """关闭 MongoDB 连接"""
    global _mongodb_connection
    
    if _mongodb_connection:
        await _mongodb_connection.close()
        _mongodb_connection = None


def get_mongodb_connection() -> Optional[MongoDBConnection]:
    """获取 MongoDB 连接实例"""
    return _mongodb_connection
