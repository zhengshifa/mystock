#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据系统核心应用程序

功能:
- 系统初始化和启动
- 组件管理和协调
- 生命周期管理
"""

import asyncio
from typing import Optional, Dict, Any
from loguru import logger

from ..config.config_manager import ConfigManager
from ..database.mongo_manager import MongoManager
from ..gm_api.gm_connection_manager import GMConnectionManager
from ..sync.sync_manager import SyncManager
from ..scheduler.task_scheduler import TaskScheduler
from ..utils.exceptions import StockDataError


class StockDataApplication:
    """股票数据系统核心应用程序"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化应用程序
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.config = config_manager.get_config() if hasattr(config_manager, 'get_config') else config_manager
        
        # 核心组件
        self.mongo_manager: Optional[MongoManager] = None
        self.gm_connection_manager: Optional[GMConnectionManager] = None
        self.processor_manager = None
        self.sync_manager: Optional[SyncManager] = None
        self.task_scheduler: Optional[TaskScheduler] = None
        
        # 运行状态
        self._is_initialized = False
        self._is_running = False
        
        logger.info("股票数据应用程序实例已创建")
    
    async def initialize(self) -> None:
        """
        初始化应用程序组件
        
        Raises:
            StockDataError: 初始化失败时抛出
        """
        try:
            logger.info("开始初始化股票数据应用程序...")
            
            # 初始化数据库管理器
            await self._initialize_database()
            
            # 初始化掘金API连接管理器
            await self._initialize_gm_connection()
            
            # 初始化同步管理器
            await self._initialize_sync_manager()
            
            # 初始化任务调度器
            await self._initialize_scheduler()
            
            self._is_initialized = True
            logger.info("股票数据应用程序初始化完成")
            
        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}")
            raise StockDataError(f"应用程序初始化失败: {e}") from e
    
    async def start(self) -> None:
        """
        启动应用程序
        
        Raises:
            StockDataError: 启动失败时抛出
        """
        if not self._is_initialized:
            raise StockDataError("应用程序未初始化，请先调用 initialize()")
        
        try:
            logger.info("启动股票数据应用程序...")
            
            # 启动数据库连接
            if self.mongo_manager:
                await self.mongo_manager.start()
            
            # 启动掘金API连接
            if self.gm_connection_manager:
                await self.gm_connection_manager.start()
            
            # 启动同步管理器
            if self.sync_manager:
                await self.sync_manager.start()
                # 确保数据处理器管理器已启动后再启动实时同步
                if hasattr(self, 'processor_manager') and self.processor_manager and self.processor_manager.is_running:
                    await self.sync_manager.start_realtime_sync()
                    
                    # 启动时先执行一次增量同步
                    logger.info("启动时执行增量数据同步...")
                    try:
                        await self.sync_manager.start_incremental_sync()
                        logger.info("启动时增量同步完成")
                    except Exception as e:
                        logger.warning(f"启动时增量同步失败: {e}")
            
            # 启动任务调度器
            if self.task_scheduler:
                self.task_scheduler.start()
            
            self._is_running = True
            logger.info("股票数据应用程序启动成功")
            
        except Exception as e:
            logger.error(f"应用程序启动失败: {e}")
            raise StockDataError(f"应用程序启动失败: {e}") from e
    
    async def shutdown(self) -> None:
        """
        关闭应用程序
        
        按相反顺序关闭各个组件
        """
        try:
            logger.info("开始关闭股票数据应用程序...")
            
            # 停止任务调度器
            if self.task_scheduler:
                self.task_scheduler.stop()
                logger.info("任务调度器已停止")
            
            # 停止同步管理器
            if self.sync_manager:
                await self.sync_manager.stop()
                logger.info("同步管理器已停止")
            
            # 停止数据处理器管理器
            if self.processor_manager:
                await self.processor_manager.shutdown()
                logger.info("数据处理器管理器已停止")
            
            # 关闭掘金API连接
            if self.gm_connection_manager:
                await self.gm_connection_manager.stop()
                logger.info("掘金API连接已关闭")
            
            # 关闭数据库连接
            if self.mongo_manager:
                await self.mongo_manager.stop()
                logger.info("数据库连接已关闭")
            
            self._is_running = False
            logger.info("股票数据应用程序已安全关闭")
            
        except Exception as e:
            logger.error(f"应用程序关闭异常: {e}")
    
    async def _initialize_database(self) -> None:
        """初始化数据库管理器"""
        try:
            from ..database.mongo_manager import MongoManager
            
            self.mongo_manager = MongoManager(self.config_manager)
            await self.mongo_manager.initialize()
            
            logger.info("数据库管理器初始化完成")
            
        except Exception as e:
            logger.error(f"数据库管理器初始化失败: {e}")
            raise
    
    async def _initialize_gm_connection(self) -> None:
        """初始化掘金API连接管理器"""
        try:
            from ..gm_api.gm_connection_manager import GMConnectionManager
            
            self.gm_connection_manager = GMConnectionManager(self.config_manager)
            await self.gm_connection_manager.initialize()
            
            logger.info("掘金API连接管理器初始化完成")
            
        except Exception as e:
            logger.error(f"掘金API连接管理器初始化失败: {e}")
            raise
    
    async def _initialize_sync_manager(self) -> None:
        """初始化同步管理器"""
        try:
            from ..sync.sync_manager import SyncManager
            
            # 创建同步管理器需要processor_manager, repository_manager和config参数
            from ..database.repositories import RepositoryManager
            from ..data_processor import DataProcessorManager
            
            repository_manager = RepositoryManager(self.mongo_manager)
            # DataProcessorManager需要gm_client参数
            processor_manager = DataProcessorManager(self.gm_connection_manager, repository_manager, self.config)
            await processor_manager.initialize()  # 初始化数据处理器管理器
            self.processor_manager = processor_manager  # 保存引用
            self.sync_manager = SyncManager(processor_manager, repository_manager, self.config)
            await self.sync_manager.initialize()
            
            logger.info("同步管理器初始化完成")
            
        except Exception as e:
            logger.error(f"同步管理器初始化失败: {e}")
            raise
    
    async def _initialize_scheduler(self) -> None:
        """初始化任务调度器"""
        try:
            from ..scheduler.task_scheduler import TaskScheduler
            
            self.task_scheduler = TaskScheduler(self.config)
            await self.task_scheduler.initialize()
            
            logger.info("任务调度器初始化完成")
            
        except Exception as e:
            logger.error(f"任务调度器初始化失败: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取应用程序状态
        
        Returns:
            包含各组件状态的字典
        """
        return {
            "is_initialized": self._is_initialized,
            "is_running": self._is_running,
            "components": {
                "mongo_manager": self.mongo_manager is not None,
                "gm_connection_manager": self.gm_connection_manager is not None,
                "sync_manager": self.sync_manager is not None,
                "task_scheduler": self.task_scheduler is not None,
            }
        }
    
    def is_healthy(self) -> bool:
        """
        检查应用程序健康状态
        
        Returns:
            应用程序是否健康
        """
        if not self._is_initialized or not self._is_running:
            return False
        
        # 检查各组件状态
        if self.mongo_manager and not self.mongo_manager.is_connected():
            return False
        
        if self.gm_connection_manager and not self.gm_connection_manager.is_connected():
            return False
        
        return True
