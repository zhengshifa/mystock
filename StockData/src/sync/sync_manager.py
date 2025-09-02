#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步管理器

统一管理所有数据同步功能，包括:
- 实时数据同步管理
- 历史数据同步管理
- 增量数据同步管理
- 同步任务调度
- 同步状态监控
- 同步策略配置
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
import time
from enum import Enum

from .realtime_sync import RealtimeDataSync
from .historical_sync import HistoricalDataSync
from .incremental_sync import IncrementalDataSync
from ..data_processor import DataProcessorManager
from ..database import RepositoryManager
from ..utils.exceptions import SyncError


class SyncType(Enum):
    """同步类型枚举"""
    REALTIME = "realtime"
    HISTORICAL = "historical"
    INCREMENTAL = "incremental"


class SyncStatus(Enum):
    """同步状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class SyncManager:
    """同步管理器"""
    
    def __init__(self, processor_manager: DataProcessorManager, 
                 repository_manager: RepositoryManager, config: Dict[str, Any]):
        self.processor_manager = processor_manager
        self.repository_manager = repository_manager
        self.config = config
        
        # 调试日志（可选）
        # logger.info(f"同步管理器接收到的完整配置: {config}")
        # logger.info(f"同步管理器中的sync配置: {config.get('sync', {})}")
        
        # 同步器配置
        self.realtime_config = config.get('sync', {}).get('realtime_sync', {})
        self.historical_config = config.get('sync', {}).get('historical_sync', {})
        self.incremental_config = config.get('sync', {}).get('incremental_sync', {})
        
        # 创建同步器实例
        self.realtime_sync = RealtimeDataSync(processor_manager, self.realtime_config)
        self.historical_sync = HistoricalDataSync(processor_manager, self.historical_config)
        
        # 为增量同步器添加股票代码配置
        incremental_config_with_symbols = self.incremental_config.copy()
        symbols = self.realtime_config.get('symbols', [])
        incremental_config_with_symbols['symbols'] = symbols
        
        # logger.info(f"同步管理器配置 - 实时同步股票代码: {symbols}")
        # logger.info(f"同步管理器配置 - 增量同步配置: {incremental_config_with_symbols}")
        
        self.incremental_sync = IncrementalDataSync(
            processor_manager, repository_manager, incremental_config_with_symbols
        )
        
        # 管理器状态
        self.is_initialized = False
        self.sync_statuses = {
            SyncType.REALTIME: SyncStatus.STOPPED,
            SyncType.HISTORICAL: SyncStatus.STOPPED,
            SyncType.INCREMENTAL: SyncStatus.STOPPED
        }
        
        # 调度配置
        self.schedule_config = config.get('schedule', {
            'auto_start_realtime': True,      # 自动启动实时同步
            'daily_historical_sync': True,    # 每日历史数据同步
            'historical_sync_time': '18:00',  # 历史数据同步时间
            'incremental_sync_interval': 3600, # 增量同步间隔(秒)
            'weekend_sync': False             # 周末是否同步
        })
        
        # 调度任务
        self._schedule_tasks = []
        self._monitor_task = None
        
        # 统计信息
        self.manager_stats = {
            'start_time': None,
            'total_sync_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'last_error': None,
            'uptime': 0
        }
        
        logger.info("同步管理器初始化完成")
    
    async def start(self) -> None:
        """启动同步管理器"""
        logger.info("启动同步管理器...")
        # 这里可以添加启动逻辑
        logger.info("同步管理器已启动")
    
    async def stop(self) -> None:
        """停止同步管理器"""
        logger.info("停止同步管理器...")
        # 这里可以添加停止逻辑
        logger.info("同步管理器已停止")
    
    async def initialize(self) -> bool:
        """初始化同步管理器"""
        try:
            if self.is_initialized:
                logger.warning("同步管理器已初始化")
                return True
            
            logger.info("初始化同步管理器...")
            
            # 检查依赖
            # 检查数据处理器管理器状态
            if hasattr(self.processor_manager, 'is_running') and not self.processor_manager.is_running:
                logger.error("数据处理器管理器未运行")
                return False
            
            # 启动监控任务
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
            # 根据配置自动启动同步
            if self.schedule_config.get('auto_start_realtime', True):
                # 确保数据处理器管理器已启动
                if hasattr(self.processor_manager, 'is_running') and self.processor_manager.is_running:
                    await self.start_realtime_sync()
                else:
                    logger.warning("数据处理器管理器未运行，跳过自动启动实时同步")
            
            # 启动调度任务
            await self._start_scheduled_tasks()
            
            self.is_initialized = True
            self.manager_stats['start_time'] = datetime.now().isoformat()
            
            logger.info("同步管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化同步管理器失败: {e}")
            return False
    
    async def shutdown(self):
        """关闭同步管理器"""
        try:
            logger.info("关闭同步管理器...")
            
            # 停止所有同步
            await self.stop_all_sync()
            
            # 停止调度任务
            await self._stop_scheduled_tasks()
            
            # 停止监控任务
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            
            self.is_initialized = False
            
            logger.info("同步管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭同步管理器失败: {e}")
    
    async def start_realtime_sync(self) -> bool:
        """启动实时同步"""
        try:
            logger.info("启动实时数据同步...")
            
            success = await self.realtime_sync.start()
            
            if success:
                self.sync_statuses[SyncType.REALTIME] = SyncStatus.RUNNING
                logger.info("实时数据同步启动成功")
            else:
                self.sync_statuses[SyncType.REALTIME] = SyncStatus.ERROR
                logger.error("实时数据同步启动失败")
            
            return success
            
        except Exception as e:
            logger.error(f"启动实时同步失败: {e}")
            self.sync_statuses[SyncType.REALTIME] = SyncStatus.ERROR
            return False
    
    async def stop_realtime_sync(self) -> bool:
        """停止实时同步"""
        try:
            logger.info("停止实时数据同步...")
            
            await self.realtime_sync.stop()
            self.sync_statuses[SyncType.REALTIME] = SyncStatus.STOPPED
            
            logger.info("实时数据同步已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止实时同步失败: {e}")
            return False
    
    async def start_historical_sync(self, symbols: Optional[List[str]] = None,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> bool:
        """启动历史数据同步"""
        try:
            logger.info("启动历史数据同步...")
            
            self.sync_statuses[SyncType.HISTORICAL] = SyncStatus.RUNNING
            
            success = await self.historical_sync.sync_all_historical_data(
                symbols, start_date, end_date
            )
            
            if success:
                self.sync_statuses[SyncType.HISTORICAL] = SyncStatus.STOPPED
                logger.info("历史数据同步完成")
            else:
                self.sync_statuses[SyncType.HISTORICAL] = SyncStatus.ERROR
                logger.error("历史数据同步失败")
            
            return success
            
        except Exception as e:
            logger.error(f"启动历史同步失败: {e}")
            self.sync_statuses[SyncType.HISTORICAL] = SyncStatus.ERROR
            return False
    
    async def start_incremental_sync(self, data_types: Optional[List[str]] = None,
                                   symbols: Optional[List[str]] = None,
                                   force_full_sync: bool = False) -> bool:
        """启动增量同步"""
        try:
            logger.info("启动增量数据同步...")
            
            self.sync_statuses[SyncType.INCREMENTAL] = SyncStatus.RUNNING
            
            success = await self.incremental_sync.start_incremental_sync(
                data_types, symbols, force_full_sync
            )
            
            if success:
                self.sync_statuses[SyncType.INCREMENTAL] = SyncStatus.STOPPED
                logger.info("增量数据同步完成")
            else:
                self.sync_statuses[SyncType.INCREMENTAL] = SyncStatus.ERROR
                logger.error("增量数据同步失败")
            
            return success
            
        except Exception as e:
            logger.error(f"启动增量同步失败: {e}")
            self.sync_statuses[SyncType.INCREMENTAL] = SyncStatus.ERROR
            return False
    
    async def stop_all_sync(self):
        """停止所有同步"""
        try:
            logger.info("停止所有数据同步...")
            
            # 并发停止所有同步
            stop_tasks = [
                self.realtime_sync.stop(),
                self.historical_sync.stop(),
                self.incremental_sync.stop()
            ]
            
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            
            # 更新状态
            for sync_type in self.sync_statuses:
                self.sync_statuses[sync_type] = SyncStatus.STOPPED
            
            logger.info("所有数据同步已停止")
            
        except Exception as e:
            logger.error(f"停止所有同步失败: {e}")
    
    async def pause_realtime_sync(self):
        """暂停实时同步"""
        try:
            await self.realtime_sync.pause()
            self.sync_statuses[SyncType.REALTIME] = SyncStatus.PAUSED
            logger.info("实时同步已暂停")
            
        except Exception as e:
            logger.error(f"暂停实时同步失败: {e}")
    
    async def resume_realtime_sync(self):
        """恢复实时同步"""
        try:
            await self.realtime_sync.resume()
            self.sync_statuses[SyncType.REALTIME] = SyncStatus.RUNNING
            logger.info("实时同步已恢复")
            
        except Exception as e:
            logger.error(f"恢复实时同步失败: {e}")
    
    async def force_sync(self, sync_type: Union[SyncType, str]) -> bool:
        """强制执行同步"""
        try:
            if isinstance(sync_type, str):
                sync_type = SyncType(sync_type)
            
            logger.info(f"强制执行 {sync_type.value} 同步")
            
            if sync_type == SyncType.REALTIME:
                return await self.realtime_sync.force_sync()
            elif sync_type == SyncType.HISTORICAL:
                return await self.start_historical_sync()
            elif sync_type == SyncType.INCREMENTAL:
                return await self.start_incremental_sync()
            else:
                logger.error(f"未知的同步类型: {sync_type}")
                return False
                
        except Exception as e:
            logger.error(f"强制同步失败: {e}")
            return False
    
    async def _start_scheduled_tasks(self):
        """启动调度任务"""
        try:
            # 每日历史数据同步
            if self.schedule_config.get('daily_historical_sync', True):
                task = asyncio.create_task(self._daily_historical_sync_scheduler())
                self._schedule_tasks.append(task)
            
            # 定期增量同步
            if self.schedule_config.get('incremental_sync_interval', 0) > 0:
                task = asyncio.create_task(self._incremental_sync_scheduler())
                self._schedule_tasks.append(task)
            
            logger.info(f"启动了 {len(self._schedule_tasks)} 个调度任务")
            
        except Exception as e:
            logger.error(f"启动调度任务失败: {e}")
    
    async def _stop_scheduled_tasks(self):
        """停止调度任务"""
        try:
            for task in self._schedule_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self._schedule_tasks.clear()
            logger.info("调度任务已停止")
            
        except Exception as e:
            logger.error(f"停止调度任务失败: {e}")
    
    async def _daily_historical_sync_scheduler(self):
        """每日历史数据同步调度器"""
        try:
            sync_time = self.schedule_config.get('historical_sync_time', '18:00')
            weekend_sync = self.schedule_config.get('weekend_sync', False)
            
            logger.info(f"每日历史数据同步调度器启动，同步时间: {sync_time}")
            
            while True:
                try:
                    now = datetime.now()
                    
                    # 检查是否为周末
                    if not weekend_sync and now.weekday() >= 5:
                        await asyncio.sleep(3600)  # 周末每小时检查一次
                        continue
                    
                    # 计算下次同步时间
                    sync_hour, sync_minute = map(int, sync_time.split(':'))
                    next_sync = now.replace(hour=sync_hour, minute=sync_minute, second=0, microsecond=0)
                    
                    if next_sync <= now:
                        next_sync += timedelta(days=1)
                    
                    # 等待到同步时间
                    wait_seconds = (next_sync - now).total_seconds()
                    logger.debug(f"下次历史数据同步时间: {next_sync}, 等待: {wait_seconds:.0f}秒")
                    
                    await asyncio.sleep(wait_seconds)
                    
                    # 执行历史数据同步
                    logger.info("开始执行定时历史数据同步")
                    success = await self.start_historical_sync()
                    
                    if success:
                        logger.info("定时历史数据同步完成")
                    else:
                        logger.error("定时历史数据同步失败")
                    
                except asyncio.CancelledError:
                    logger.info("每日历史数据同步调度器被取消")
                    break
                except Exception as e:
                    logger.error(f"每日历史数据同步调度器异常: {e}")
                    await asyncio.sleep(3600)  # 异常时等待1小时后重试
                    
        except Exception as e:
            logger.error(f"每日历史数据同步调度器严重异常: {e}")
    
    async def _incremental_sync_scheduler(self):
        """增量同步调度器"""
        try:
            interval = self.schedule_config.get('incremental_sync_interval', 3600)
            
            logger.info(f"增量同步调度器启动，同步间隔: {interval}秒")
            
            while True:
                try:
                    await asyncio.sleep(interval)
                    
                    # 检查是否需要执行增量同步
                    if self.sync_statuses[SyncType.INCREMENTAL] == SyncStatus.RUNNING:
                        logger.debug("增量同步正在运行，跳过本次调度")
                        continue
                    
                    # 执行增量同步
                    logger.info("开始执行定时增量同步")
                    success = await self.start_incremental_sync()
                    
                    if success:
                        logger.info("定时增量同步完成")
                    else:
                        logger.error("定时增量同步失败")
                    
                except asyncio.CancelledError:
                    logger.info("增量同步调度器被取消")
                    break
                except Exception as e:
                    logger.error(f"增量同步调度器异常: {e}")
                    await asyncio.sleep(300)  # 异常时等待5分钟后重试
                    
        except Exception as e:
            logger.error(f"增量同步调度器严重异常: {e}")
    
    async def _monitor_loop(self):
        """监控循环"""
        try:
            logger.info("同步监控循环启动")
            
            while self.is_initialized:
                try:
                    # 更新运行时间
                    if self.manager_stats['start_time']:
                        start_time = datetime.fromisoformat(self.manager_stats['start_time'])
                        self.manager_stats['uptime'] = (datetime.now() - start_time).total_seconds()
                    
                    # 检查同步器状态
                    await self._check_sync_health()
                    
                    # 每分钟检查一次
                    await asyncio.sleep(60)
                    
                except asyncio.CancelledError:
                    logger.info("同步监控循环被取消")
                    break
                except Exception as e:
                    logger.error(f"同步监控循环异常: {e}")
                    await asyncio.sleep(60)
                    
        except Exception as e:
            logger.error(f"同步监控循环严重异常: {e}")
    
    async def _check_sync_health(self):
        """检查同步健康状态"""
        try:
            # 检查实时同步状态
            if (self.sync_statuses[SyncType.REALTIME] == SyncStatus.RUNNING and 
                not self.realtime_sync.is_running):
                logger.warning("实时同步状态不一致，尝试重启")
                await self.start_realtime_sync()
            
            # 检查处理器管理器状态
            if not self.processor_manager.is_running:
                logger.error("数据处理器管理器已停止")
                await self.stop_all_sync()
            
        except Exception as e:
            logger.error(f"检查同步健康状态失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        try:
            return {
                'is_initialized': self.is_initialized,
                'sync_statuses': {k.value: v.value for k, v in self.sync_statuses.items()},
                'schedule_config': self.schedule_config,
                'scheduled_tasks_count': len(self._schedule_tasks),
                'manager_stats': self.manager_stats,
                'realtime_sync_status': self.realtime_sync.get_status(),
                'historical_sync_status': self.historical_sync.get_status(),
                'incremental_sync_status': self.incremental_sync.get_status()
            }
            
        except Exception as e:
            logger.error(f"获取管理器状态失败: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            return {
                'manager_stats': self.manager_stats,
                'realtime_sync_stats': self.realtime_sync.get_stats(),
                'historical_sync_stats': self.historical_sync.get_stats(),
                'incremental_sync_stats': self.incremental_sync.get_stats()
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def reset_stats(self):
        """重置统计信息"""
        try:
            self.manager_stats = {
                'start_time': datetime.now().isoformat(),
                'total_sync_sessions': 0,
                'successful_sessions': 0,
                'failed_sessions': 0,
                'last_error': None,
                'uptime': 0
            }
            
            self.realtime_sync.reset_stats()
            
            logger.info("同步管理器统计信息已重置")
            
        except Exception as e:
            logger.error(f"重置统计信息失败: {e}")
    
    def __str__(self) -> str:
        return f"SyncManager(initialized={self.is_initialized}, realtime={self.sync_statuses[SyncType.REALTIME].value})"
    
    def __repr__(self) -> str:
        return self.__str__()