"""
调度服务模块
使用APScheduler实现定时任务调度
"""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from .data_sync import DataSyncService
from .symbol_sync import SymbolSyncService
from ..config import settings


class SchedulerService:
    """调度服务"""
    
    def __init__(self):
        """初始化调度服务"""
        self.logger = logging.getLogger(__name__)
        self.scheduler = AsyncIOScheduler()
        self.data_sync_service = DataSyncService()
        self.symbol_sync_service = SymbolSyncService()
        self.symbols = settings.test_symbols
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """设置事件监听器"""
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
    
    def _job_executed_listener(self, event):
        """任务执行监听器"""
        if event.exception:
            self.logger.error(f"任务执行失败: {event.job_id}, 错误: {event.exception}")
        else:
            self.logger.info(f"任务执行成功: {event.job_id}")
    
    async def start_scheduler(self):
        """启动调度器"""
        if not settings.scheduler_enabled:
            self.logger.info("调度器已禁用")
            return
        
        try:
            # 添加历史数据同步任务（每日定时执行）
            history_sync_time = time.fromisoformat(settings.history_sync_time)
            self.scheduler.add_job(
                self._daily_history_sync,
                CronTrigger(hour=history_sync_time.hour, minute=history_sync_time.minute),
                id='daily_history_sync',
                name='每日历史数据同步',
                replace_existing=True
            )
            
            # 添加开盘前增量同步任务
            if settings.incremental_sync_enabled:
                pre_market_sync_time = time.fromisoformat(settings.pre_market_sync_time)
                self.scheduler.add_job(
                    self._pre_market_incremental_sync,
                    CronTrigger(hour=pre_market_sync_time.hour, minute=pre_market_sync_time.minute),
                    id='pre_market_incremental_sync',
                    name='开盘前增量同步',
                    replace_existing=True
                )
            
            # 添加收盘后增量同步任务
            if settings.incremental_sync_enabled:
                post_market_sync_time = time.fromisoformat(settings.post_market_sync_time)
                self.scheduler.add_job(
                    self._post_market_incremental_sync,
                    CronTrigger(hour=post_market_sync_time.hour, minute=post_market_sync_time.minute),
                    id='post_market_incremental_sync',
                    name='收盘后增量同步',
                    replace_existing=True
                )
            
            # 添加实时数据同步任务（仅在交易时间内执行）
            self.scheduler.add_job(
                self._realtime_sync,
                IntervalTrigger(seconds=settings.realtime_interval_seconds),
                id='realtime_sync',
                name='实时数据同步',
                replace_existing=True
            )
            
            # 添加分钟数据同步任务（仅在交易时间内执行）
            self.scheduler.add_job(
                self._minute_data_sync,
                IntervalTrigger(minutes=5),
                id='minute_data_sync',
                name='分钟数据同步',
                replace_existing=True
            )
            
            # 添加标的基本信息同步任务（每日定时执行）
            if settings.symbol_sync_enabled:
                symbol_sync_time = time.fromisoformat(settings.symbol_sync_time)
                self.scheduler.add_job(
                    self._daily_symbol_sync,
                    CronTrigger(hour=symbol_sync_time.hour, minute=symbol_sync_time.minute),
                    id='daily_symbol_sync',
                    name='每日标的基本信息同步',
                    replace_existing=True
                )
            
            # 添加健康检查任务（每分钟执行一次）
            self.scheduler.add_job(
                self._health_check,
                IntervalTrigger(minutes=1),
                id='health_check',
                name='健康检查',
                replace_existing=True
            )
            
            # 启动调度器
            self.scheduler.start()
            self.logger.info("调度器启动成功")
            
            # 打印任务列表
            self._print_job_list()
            
        except Exception as e:
            self.logger.error(f"启动调度器失败: {e}")
            raise
    
    def stop_scheduler(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("调度器已停止")
    
    def _print_job_list(self):
        """打印任务列表"""
        jobs = self.scheduler.get_jobs()
        self.logger.info(f"已注册 {len(jobs)} 个任务:")
        for job in jobs:
            self.logger.info(f"  - {job.name} (ID: {job.id})")
    
    async def _daily_history_sync(self):
        """每日历史数据同步任务"""
        self.logger.info("开始执行每日历史数据同步")
        try:
            results = await self.data_sync_service.sync_all_frequencies(self.symbols)
            
            # 统计各频率的成功率
            for frequency, freq_results in results.items():
                success_count = sum(1 for success in freq_results.values() if success)
                self.logger.info(f"{frequency}频率同步完成: {success_count}/{len(freq_results)} 成功")
            
        except Exception as e:
            self.logger.error(f"每日历史数据同步失败: {e}")
    
    async def _pre_market_incremental_sync(self):
        """开盘前增量同步任务"""
        self.logger.info("开始执行开盘前增量同步")
        try:
            # 检查是否在开盘前时间
            if not await self.data_sync_service.is_pre_market_time():
                self.logger.info("当前不在开盘前时间，跳过增量同步")
                return
            
            # 执行增量同步，主要同步前一日的数据
            results = await self.data_sync_service.sync_incremental_data(self.symbols, days_back=1)
            
            # 统计各频率的成功率
            for frequency, freq_results in results.items():
                success_count = sum(1 for success in freq_results.values() if success)
                self.logger.info(f"开盘前{frequency}频率增量同步完成: {success_count}/{len(freq_results)} 成功")
            
        except Exception as e:
            self.logger.error(f"开盘前增量同步失败: {e}")
    
    async def _post_market_incremental_sync(self):
        """收盘后增量同步任务"""
        self.logger.info("开始执行收盘后增量同步")
        try:
            # 检查是否在收盘后时间
            if not await self.data_sync_service.is_post_market_time():
                self.logger.info("当前不在收盘后时间，跳过增量同步")
                return
            
            # 执行增量同步，主要同步当日的数据
            results = await self.data_sync_service.sync_incremental_data(self.symbols, days_back=0)
            
            # 统计各频率的成功率
            for frequency, freq_results in results.items():
                success_count = sum(1 for success in freq_results.values() if success)
                self.logger.info(f"收盘后{frequency}频率增量同步完成: {success_count}/{len(freq_results)} 成功")
            
        except Exception as e:
            self.logger.error(f"收盘后增量同步失败: {e}")
    
    async def _realtime_sync(self):
        """实时数据同步任务"""
        try:
            is_trading = await self.data_sync_service.is_trading_time()
            if is_trading:
                self.logger.info("当前在交易时间内，开始执行实时数据同步")
                results = await self.data_sync_service.sync_realtime_frequencies(self.symbols)
                
                # 统计各频率的成功率
                for frequency, freq_results in results.items():
                    success_count = sum(1 for success in freq_results.values() if success)
                    self.logger.info(f"{frequency}实时同步: {success_count}/{len(freq_results)} 成功")
            else:
                self.logger.debug("当前不在交易时间内，跳过实时数据同步")
        except Exception as e:
            self.logger.error(f"实时数据同步失败: {e}")
    
    async def _minute_data_sync(self):
        """分钟数据同步任务"""
        try:
            is_trading = await self.data_sync_service.is_trading_time()
            if is_trading:
                self.logger.info("当前在交易时间内，开始执行分钟数据同步")
                # 同步所有分钟级频率的数据
                for frequency in settings.enabled_frequencies:
                    if settings.is_frequency_enabled(frequency) and frequency != '1d':
                        results = await self.data_sync_service.sync_minute_data(
                            self.symbols, minutes_back=10, frequency=frequency
                        )
                        success_count = sum(1 for success in results.values() if success)
                        self.logger.info(f"{frequency}分钟数据同步: {success_count}/{len(results)} 成功")
            else:
                self.logger.debug("当前不在交易时间内，跳过分钟数据同步")
        except Exception as e:
            self.logger.error(f"分钟数据同步失败: {e}")
    
    async def _daily_symbol_sync(self):
        """每日标的基本信息同步任务"""
        self.logger.info("开始执行每日标的基本信息同步")
        try:
            if settings.symbol_sync_all_types:
                # 同步所有类型的标的基本信息
                success = await self.symbol_sync_service.sync_all_symbol_infos()
                if success:
                    self.logger.info("每日标的基本信息同步完成")
                else:
                    self.logger.error("每日标的基本信息同步失败")
            else:
                # 只同步股票标的基本信息
                success = await self.symbol_sync_service.sync_stock_symbols()
                if success:
                    self.logger.info("每日股票标的基本信息同步完成")
                else:
                    self.logger.error("每日股票标的基本信息同步失败")
            
        except Exception as e:
            self.logger.error(f"每日标的基本信息同步失败: {e}")
    
    async def _health_check(self):
        """健康检查任务"""
        try:
            # 检查数据库连接
            from ..database import mongodb_client
            db_healthy = await mongodb_client.health_check()
            
            # 检查同步状态
            sync_status = await self.data_sync_service.get_sync_status()
            
            if not db_healthy:
                self.logger.warning("数据库连接异常")
            
            self.logger.debug(f"健康检查: 数据库={db_healthy}, 同步状态={sync_status}")
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
    
    async def add_custom_job(self, job_id: str, func, trigger, **kwargs):
        """
        添加自定义任务
        
        Args:
            job_id: 任务ID
            func: 任务函数
            trigger: 触发器
            **kwargs: 其他参数
        """
        try:
            self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                replace_existing=True,
                **kwargs
            )
            self.logger.info(f"添加自定义任务成功: {job_id}")
        except Exception as e:
            self.logger.error(f"添加自定义任务失败: {job_id}, 错误: {e}")
    
    def remove_job(self, job_id: str):
        """
        移除任务
        
        Args:
            job_id: 任务ID
        """
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"移除任务成功: {job_id}")
        except Exception as e:
            self.logger.error(f"移除任务失败: {job_id}, 错误: {e}")
    
    def get_job_status(self) -> Dict:
        """
        获取任务状态
        
        Returns:
            Dict: 任务状态信息
        """
        try:
            jobs = self.scheduler.get_jobs()
            job_list = []
            
            for job in jobs:
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                job_list.append(job_info)
            
            return {
                'scheduler_running': self.scheduler.running,
                'job_count': len(jobs),
                'jobs': job_list
            }
            
        except Exception as e:
            self.logger.error(f"获取任务状态失败: {e}")
            return {'error': str(e)}
    
    async def trigger_job_now(self, job_id: str):
        """
        立即触发任务
        
        Args:
            job_id: 任务ID
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                await job.func()
                self.logger.info(f"立即触发任务成功: {job_id}")
            else:
                self.logger.warning(f"任务不存在: {job_id}")
        except Exception as e:
            self.logger.error(f"立即触发任务失败: {job_id}, 错误: {e}")
    
    async def start_realtime_sync_manual(self):
        """手动启动实时数据同步"""
        self.logger.info("手动启动实时数据同步")
        await self.data_sync_service.start_realtime_sync(self.symbols)
    
    def stop_realtime_sync_manual(self):
        """手动停止实时数据同步"""
        self.logger.info("手动停止实时数据同步")
        self.data_sync_service.stop_realtime_sync()
    
    async def sync_frequency_manual(self, frequency: str):
        """
        手动同步指定频率数据
        
        Args:
            frequency: 数据频率
        """
        self.logger.info(f"手动同步 {frequency} 频率数据")
        try:
            if frequency == 'tick':
                results = await self.data_sync_service.sync_realtime_data(self.symbols)
            else:
                results = await self.data_sync_service.sync_history_data(
                    self.symbols, frequency=frequency
                )
            
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(f"{frequency}频率手动同步完成: {success_count}/{len(results)} 成功")
            
        except Exception as e:
            self.logger.error(f"{frequency}频率手动同步失败: {e}")
    
    async def sync_all_frequencies_manual(self):
        """手动同步所有频率数据"""
        self.logger.info("手动同步所有频率数据")
        try:
            results = await self.data_sync_service.sync_all_frequencies(self.symbols)
            
            # 统计各频率的成功率
            for frequency, freq_results in results.items():
                success_count = sum(1 for success in freq_results.values() if success)
                self.logger.info(f"{frequency}频率手动同步完成: {success_count}/{len(freq_results)} 成功")
            
        except Exception as e:
            self.logger.error(f"手动同步所有频率数据失败: {e}")
    
    async def sync_symbol_infos_manual(self, sync_all_types: bool = True):
        """
        手动同步标的基本信息
        
        Args:
            sync_all_types: 是否同步所有类型，False则只同步股票
            
        Returns:
            bool: 同步是否成功
        """
        self.logger.info(f"手动同步标的基本信息，同步所有类型: {sync_all_types}")
        try:
            if sync_all_types:
                success = await self.symbol_sync_service.sync_all_symbol_infos()
                if success:
                    self.logger.info("手动同步所有标的基本信息完成")
                    return True
                else:
                    self.logger.error("手动同步所有标的基本信息失败")
                    return False
            else:
                success = await self.symbol_sync_service.sync_stock_symbols()
                if success:
                    self.logger.info("手动同步股票标的基本信息完成")
                    return True
                else:
                    self.logger.error("手动同步股票标的基本信息失败")
                    return False
            
        except Exception as e:
            self.logger.error(f"手动同步标的基本信息失败: {e}")
            return False
    
    async def get_symbol_sync_status(self):
        """获取标的基本信息同步状态"""
        try:
            return await self.symbol_sync_service.get_sync_status()
        except Exception as e:
            self.logger.error(f"获取标的基本信息同步状态失败: {e}")
            return {'error': str(e)}
