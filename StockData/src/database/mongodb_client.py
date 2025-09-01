"""
MongoDB客户端类
包含连接管理和数据操作
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.models.stock_data import TickData, BarData


class MongoDBClient:
    """MongoDB客户端类"""
    
    def __init__(self):
        """初始化MongoDB客户端"""
        self.logger = get_logger("MongoDBClient")
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.collections: Dict[str, Collection] = {}
        
        # 集合名称映射 - 按照时间频率区分
        self.collection_names = {
            'tick': 'tick',           # 实时Tick数据
            '60s': '60s',             # 1分钟K线数据
            '300s': '300s',           # 5分钟K线数据
            '900s': '900s',           # 15分钟K线数据
            '1d': '1d'                # 日线数据
        }
        
        self._connect()
        self._setup_collections()
        self._setup_indexes()
    
    def _connect(self) -> None:
        """连接到MongoDB"""
        try:
            settings = get_settings()
            connection_string = settings.get_mongodb_connection_string()
            self.client = MongoClient(connection_string)
            
            # 测试连接 - 使用admin数据库进行认证
            self.client.admin.command('ping')
            self.database = self.client[settings.mongodb_database]
            
            self.logger.info(f"成功连接到MongoDB: {settings.mongodb_database}")
            
        except ConnectionFailure as e:
            self.logger.error(f"MongoDB连接失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"MongoDB初始化失败: {e}")
            raise
    
    def _setup_collections(self) -> None:
        """设置集合"""
        for data_type, collection_name in self.collection_names.items():
            self.collections[data_type] = self.database[collection_name]
            self.logger.debug(f"初始化集合: {collection_name}")
    
    def _setup_indexes(self) -> None:
        """设置索引"""
        try:
            # Tick数据索引
            tick_collection = self.collections['tick']
            tick_collection.create_index([("symbol", 1), ("created_at", -1)])
            tick_collection.create_index([("data_hash", 1)], unique=True)
            tick_collection.create_index([("collection_time", -1)])
            
            # 时间频率K线数据索引 (60s, 300s, 900s, 1d)
            for freq in ['60s', '300s', '900s', '1d']:
                if freq in self.collections:
                    freq_collection = self.collections[freq]
                    freq_collection.create_index([("symbol", 1), ("bob", -1)])
                    freq_collection.create_index([("data_hash", 1)], unique=True)
                    freq_collection.create_index([("collection_time", -1)])
            
            self.logger.info("MongoDB索引设置完成")
            
        except Exception as e:
            self.logger.error(f"设置索引失败: {e}")
    
    def insert_tick_data(self, tick_data: TickData) -> bool:
        """插入Tick数据"""
        try:
            collection = self.collections['tick']
            
            # 转换为字典
            data_dict = tick_data.dict()
            
            # 尝试插入数据
            result = collection.insert_one(data_dict)
            
            if result.inserted_id:
                self.logger.debug(f"成功插入Tick数据: {tick_data.symbol}")
                return True
            else:
                self.logger.warning(f"插入Tick数据失败: {tick_data.symbol}")
                return False
                
        except DuplicateKeyError:
            # 数据已存在，跳过
            self.logger.debug(f"Tick数据已存在，跳过: {tick_data.symbol}")
            return True
        except Exception as e:
            self.logger.error(f"插入Tick数据异常: {e}")
            return False
    
    def insert_bar_data(self, bar_data: BarData, frequency: str = '1d') -> bool:
        """插入Bar数据到指定频率的集合"""
        try:
            # 根据频率选择集合
            if frequency not in self.collections:
                self.logger.error(f"不支持的时间频率: {frequency}")
                return False
            
            collection = self.collections[frequency]
            
            # 转换为字典
            data_dict = bar_data.dict()
            
            # 尝试插入数据
            result = collection.insert_one(data_dict)
            
            if result.inserted_id:
                self.logger.debug(f"成功插入{frequency}数据: {bar_data.symbol}")
                return True
            else:
                self.logger.warning(f"插入{frequency}数据失败: {bar_data.symbol}")
                return False
                
        except DuplicateKeyError:
            # 数据已存在，跳过
            self.logger.debug(f"{frequency}数据已存在，跳过: {bar_data.symbol}")
            return True
        except Exception as e:
            self.logger.error(f"插入{frequency}数据异常: {e}")
            return False
    
    def batch_insert_tick_data(self, tick_data_list: List[TickData]) -> Dict[str, int]:
        """批量插入Tick数据"""
        if not tick_data_list:
            return {"success": 0, "failed": 0, "skipped": 0}
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        collection = self.collections['tick']
        
        # 分批处理
        settings = get_settings()
        batch_size = settings.batch_size
        for i in range(0, len(tick_data_list), batch_size):
            batch = tick_data_list[i:i + batch_size]
            
            try:
                # 转换为字典列表
                data_dicts = [data.dict() for data in batch]
                
                # 批量插入
                result = collection.insert_many(data_dicts, ordered=False)
                success_count += len(result.inserted_ids)
                
            except Exception as e:
                # 如果批量插入失败，尝试逐个插入
                self.logger.warning(f"批量插入失败，尝试逐个插入: {e}")
                for data in batch:
                    if self.insert_tick_data(data):
                        success_count += 1
                    else:
                        failed_count += 1
        
        self.logger.info(f"批量插入Tick数据完成: 成功{success_count}条, 失败{failed_count}条")
        return {"success": success_count, "failed": failed_count, "skipped": skipped_count}
    
    def batch_insert_bar_data(self, bar_data_list: List[BarData], frequency: str = '1d') -> Dict[str, int]:
        """批量插入Bar数据到指定频率的集合"""
        if not bar_data_list:
            return {"success": 0, "failed": 0, "skipped": 0}
        
        # 根据频率选择集合
        if frequency not in self.collections:
            self.logger.error(f"不支持的时间频率: {frequency}")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        collection = self.collections[frequency]
        
        # 分批处理
        settings = get_settings()
        batch_size = settings.batch_size
        for i in range(0, len(bar_data_list), batch_size):
            batch = bar_data_list[i:i + batch_size]
            
            try:
                # 转换为字典列表
                data_dicts = [data.dict() for data in batch]
                
                # 批量插入
                result = collection.insert_many(data_dicts, ordered=False)
                success_count += len(result.inserted_ids)
                
            except Exception as e:
                # 如果批量插入失败，尝试逐个插入
                self.logger.warning(f"批量插入{frequency}数据失败，尝试逐个插入: {e}")
                for data in batch:
                    if self.insert_bar_data(data, frequency):
                        success_count += 1
                    else:
                        failed_count += 1
        
        self.logger.info(f"批量插入{frequency}数据完成: 成功{success_count}条, 失败{failed_count}条")
        return {"success": success_count, "failed": failed_count, "skipped": skipped_count}
    
    def get_latest_data(self, symbol: str, data_type: str = 'tick', limit: int = 1) -> List[Dict[str, Any]]:
        """获取最新数据"""
        try:
            collection = self.collections.get(data_type)
            if not collection:
                self.logger.error(f"未知的数据类型: {data_type}")
                return []
            
            # 根据数据类型选择排序字段
            if data_type == 'tick':
                sort_field = "created_at"
            else:
                sort_field = "bob"  # K线数据使用bob字段排序
            
            # 查询最新数据
            cursor = collection.find(
                {"symbol": symbol},
                {"_id": 0}  # 排除_id字段
            ).sort(sort_field, -1).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            self.logger.error(f"获取最新数据失败: {e}")
            return []
    
    def get_bar_data(self, symbol: str, frequency: str, 
                     start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """获取指定时间范围的Bar数据"""
        try:
            collection = self.collections.get(frequency)
            if collection is None:
                self.logger.error(f"不支持的时间频率: {frequency}")
                return []
            
            # 构建查询条件
            query = {"symbol": symbol}
            
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                
                if date_query:
                    query["bob"] = date_query
            
            # 查询数据
            cursor = collection.find(
                query,
                {"_id": 0}  # 排除_id字段
            ).sort("bob", 1)  # 按时间正序排列
            
            return list(cursor)
            
        except Exception as e:
            self.logger.error(f"获取Bar数据失败: {e}")
            return []
    
    def get_last_bar_data(self, symbol: str, frequency: str) -> Optional[Dict[str, Any]]:
        """获取最后一条Bar数据"""
        try:
            collection = self.collections.get(frequency)
            if collection is None:
                self.logger.error(f"不支持的时间频率: {frequency}")
                return None
            
            # 查询最后一条数据
            result = collection.find_one(
                {"symbol": symbol},
                {"_id": 0}  # 排除_id字段
            )
            
            if result:
                # 转换为datetime对象
                if "bob" in result and isinstance(result["bob"], str):
                    try:
                        from datetime import datetime
                        result["bob"] = datetime.fromisoformat(result["bob"])
                    except:
                        pass
                
                if "eob" in result and isinstance(result["eob"], str):
                    try:
                        from datetime import datetime
                        result["eob"] = datetime.fromisoformat(result["eob"])
                    except:
                        pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取最后Bar数据失败: {e}")
            return None
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB连接已关闭")
