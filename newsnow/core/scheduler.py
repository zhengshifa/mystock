"""新闻调度器模块"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from sources import get_source_getter, get_available_sources
from database.mongodb import get_mongodb_connection
from database.models import SourceInfo


class NewsScheduler:
    """新闻调度器类"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = AsyncIOScheduler()
        self.running = False
        self.jobs = {}
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "total_items_fetched": 0
        }
    
    async def start(self):
        """启动调度器"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("调度器已启动")
            
            # 添加定时任务
            await self._add_scheduled_jobs()
            
            self.running = True
            logger.info("新闻调度器启动成功")
            
        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            raise
    
    async def stop(self):
        """停止调度器"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("调度器已停止")
            
            self.running = False
            logger.info("新闻调度器已停止")
            
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
    
    async def _add_scheduled_jobs(self):
        """添加定时任务"""
        try:
            # 每5分钟运行一次新闻获取
            job = self.scheduler.add_job(
                self.fetch_all_sources,
                IntervalTrigger(minutes=5),
                id="fetch_news",
                name="获取所有新闻源数据",
                max_instances=1
            )
            
            self.jobs["fetch_news"] = job
            logger.info("已添加新闻获取定时任务 (每5分钟)")
            
            # 每1小时运行一次健康检查
            job = self.scheduler.add_job(
                self.health_check,
                IntervalTrigger(hours=1),
                id="health_check",
                name="系统健康检查",
                max_instances=1
            )
            
            self.jobs["health_check"] = job
            logger.info("已添加健康检查定时任务 (每1小时)")
            
        except Exception as e:
            logger.error(f"添加定时任务失败: {e}")
    
    async def fetch_all_sources(self) -> Dict[str, Any]:
        """获取所有新闻源的数据"""
        start_time = time.time()
        success_count = 0
        error_count = 0
        total_items = 0
        
        try:
            logger.info("开始获取所有新闻源数据...")
            
            # 获取可用的新闻源
            sources = get_available_sources()
            logger.info(f"发现 {len(sources)} 个新闻源")
            
            # 并发获取所有新闻源
            tasks = []
            for source_id in sources:
                task = self._fetch_single_source(source_id)
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            for i, result in enumerate(results):
                source_id = sources[i]
                if isinstance(result, Exception):
                    logger.error(f"获取新闻源 {source_id} 失败: {result}")
                    error_count += 1
                else:
                    if result and result.status == "success":
                        success_count += 1
                        total_items += len(result.items)
                        logger.info(f"新闻源 {source_id} 获取成功，共 {len(result.items)} 条新闻")
                    else:
                        error_count += 1
                        logger.warning(f"新闻源 {source_id} 获取失败: {getattr(result, 'error_message', '未知错误')}")
            
            # 更新统计信息
            self.stats["total_runs"] += 1
            self.stats["successful_runs"] += success_count
            self.stats["failed_runs"] += error_count
            self.stats["last_run"] = datetime.now()
            self.stats["total_items_fetched"] += total_items
            
            duration = time.time() - start_time
            logger.info(f"新闻获取完成: {success_count}/{len(sources)} 个源成功，共获取 {total_items} 条新闻，耗时 {duration:.2f}秒")
            
            return {
                "success_count": success_count,
                "error_count": error_count,
                "total_items": total_items,
                "duration": duration
            }
            
        except Exception as e:
            logger.error(f"获取所有新闻源失败: {e}")
            return {
                "success_count": 0,
                "error_count": len(get_available_sources()),
                "total_items": 0,
                "duration": time.time() - start_time
            }
    
    async def _fetch_single_source(self, source_id: str):
        """获取单个新闻源的数据"""
        try:
            # 获取新闻源获取器
            getter = get_source_getter(source_id)
            if not getter:
                logger.warning(f"未找到新闻源 {source_id} 的获取器")
                return None
            
            # 执行获取
            result = await getter()
            
            # 保存到数据库
            if result and result.status == "success" and result.items:
                await self._save_news_to_db(result)
            
            return result
            
        except Exception as e:
            logger.error(f"获取新闻源 {source_id} 失败: {e}")
            raise
    
    async def _save_news_to_db(self, response):
        """保存新闻到数据库"""
        try:
            db_conn = get_mongodb_connection()
            if db_conn:
                success = await db_conn.save_news(response.items)
                if success:
                    logger.debug(f"成功保存 {len(response.items)} 条新闻到数据库")
                else:
                    logger.warning(f"保存新闻到数据库失败，新闻源: {response.source_id}, 新闻数量: {len(response.items)}")
            else:
                logger.warning("数据库连接未建立，跳过保存")
                
        except Exception as e:
            logger.error(f"保存新闻到数据库异常，新闻源: {response.source_id}, 错误: {e}")
            # 记录更详细的错误信息
            import traceback
            logger.debug(f"详细错误堆栈: {traceback.format_exc()}")
    
    async def health_check(self):
        """系统健康检查"""
        try:
            logger.info("开始系统健康检查...")
            
            # 检查数据库连接
            db_conn = get_mongodb_connection()
            if db_conn:
                db_healthy = await db_conn.health_check()
                if db_healthy:
                    logger.info("数据库连接正常")
                else:
                    logger.warning("数据库连接异常")
            else:
                logger.warning("数据库连接未建立")
            
            # 检查新闻源
            sources = get_available_sources()
            logger.info(f"当前可用新闻源数量: {len(sources)}")
            
            # 检查调度器状态
            if self.scheduler.running:
                logger.info("调度器运行正常")
            else:
                logger.warning("调度器未运行")
            
            logger.info("系统健康检查完成")
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "running": self.running,
            "scheduler_running": self.scheduler.running,
            "job_count": len(self.jobs),
            "stats": self.stats.copy(),
            "jobs": {name: job.id for name, job in self.jobs.items()}
        }
    
    def get_job_info(self, job_name: str) -> Optional[Dict[str, Any]]:
        """获取指定任务信息"""
        if job_name not in self.jobs:
            return None
        
        job = self.jobs[job_name]
        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time,
            "trigger": str(job.trigger)
        }
