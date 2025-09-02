#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调度系统使用示例

展示如何使用调度系统的各个组件:
- 任务调度器使用示例
- 作业管理器使用示例
- Cron调度器使用示例
- 任务监控器使用示例
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from .task_scheduler import TaskScheduler, ScheduledTask, TaskPriority
from .job_manager import JobManager, Job, JobType, JobConfig
from .cron_scheduler import CronScheduler, CronJob
from .task_monitor import TaskMonitor, AlertLevel, console_alert_handler, log_alert_handler
from ..utils import get_logger


class SchedulerExamples:
    """调度系统使用示例"""
    
    def __init__(self):
        self.logger = get_logger("SchedulerExamples")
        
        # 初始化各个组件
        self.task_scheduler = TaskScheduler(max_workers=5)
        self.job_manager = JobManager(self.task_scheduler)
        self.cron_scheduler = CronScheduler(self.task_scheduler)
        self.task_monitor = TaskMonitor(
            task_scheduler=self.task_scheduler,
            job_manager=self.job_manager,
            cron_scheduler=self.cron_scheduler
        )
        
        # 添加告警处理器
        self.task_monitor.add_alert_handler(console_alert_handler)
        self.task_monitor.add_alert_handler(log_alert_handler)
    
    def example_task_scheduler(self):
        """任务调度器使用示例"""
        self.logger.info("=== 任务调度器使用示例 ===")
        
        # 定义示例任务函数
        def simple_task(name: str, duration: int = 1) -> str:
            """简单任务"""
            self.logger.info(f"执行任务: {name}")
            time.sleep(duration)
            return f"任务 {name} 完成"
        
        def failing_task() -> str:
            """会失败的任务"""
            self.logger.info("执行会失败的任务")
            raise Exception("任务执行失败")
        
        async def async_task(name: str) -> str:
            """异步任务"""
            self.logger.info(f"执行异步任务: {name}")
            await asyncio.sleep(1)
            return f"异步任务 {name} 完成"
        
        # 启动调度器
        self.task_scheduler.start()
        
        try:
            # 1. 添加一次性任务
            task1 = ScheduledTask(
                task_id="task_1",
                name="一次性任务",
                func=simple_task,
                args=("任务1",),
                kwargs={"duration": 2},
                priority=TaskPriority.HIGH
            )
            self.task_scheduler.add_task(task1)
            
            # 2. 添加间隔任务
            task2 = ScheduledTask(
                task_id="task_2",
                name="间隔任务",
                func=simple_task,
                args=("间隔任务",),
                interval=5.0,  # 每5秒执行一次
                max_executions=3  # 最多执行3次
            )
            self.task_scheduler.add_task(task2)
            
            # 3. 添加延迟任务
            task3 = ScheduledTask(
                task_id="task_3",
                name="延迟任务",
                func=simple_task,
                args=("延迟任务",),
                delay=3.0  # 3秒后执行
            )
            self.task_scheduler.add_task(task3)
            
            # 4. 添加会失败的任务（带重试）
            task4 = ScheduledTask(
                task_id="task_4",
                name="重试任务",
                func=failing_task,
                max_retries=3,
                retry_delay=1.0
            )
            self.task_scheduler.add_task(task4)
            
            # 5. 添加异步任务
            task5 = ScheduledTask(
                task_id="task_5",
                name="异步任务",
                func=async_task,
                args=("异步任务",),
                is_async=True
            )
            self.task_scheduler.add_task(task5)
            
            # 等待任务执行
            time.sleep(15)
            
            # 查看统计信息
            stats = self.task_scheduler.get_stats()
            self.logger.info(f"调度器统计: {stats}")
            
            # 列出所有任务
            tasks = self.task_scheduler.list_tasks()
            for task in tasks:
                self.logger.info(f"任务: {task.name}, 状态: {task.status.value}")
        
        finally:
            self.task_scheduler.stop()
    
    def example_job_manager(self):
        """作业管理器使用示例"""
        self.logger.info("=== 作业管理器使用示例 ===")
        
        # 定义作业函数
        def data_sync_job(symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
            """数据同步作业"""
            self.logger.info(f"同步股票数据: {symbol} ({start_date} - {end_date})")
            time.sleep(2)  # 模拟数据同步
            return {
                "symbol": symbol,
                "records": 100,
                "status": "success"
            }
        
        def data_analysis_job(symbol: str) -> Dict[str, Any]:
            """数据分析作业"""
            self.logger.info(f"分析股票数据: {symbol}")
            time.sleep(3)  # 模拟数据分析
            return {
                "symbol": symbol,
                "indicators": ["MA5", "MA10", "RSI"],
                "status": "completed"
            }
        
        # 启动组件
        self.task_scheduler.start()
        self.job_manager.start()
        
        try:
            # 1. 创建数据同步作业组
            sync_jobs = []
            symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
            
            for symbol in symbols:
                job_config = JobConfig(
                    priority=TaskPriority.HIGH,
                    timeout=30.0,
                    max_retries=2
                )
                
                job = Job(
                    job_id=f"sync_{symbol}",
                    name=f"同步{symbol}数据",
                    job_type=JobType.DATA_SYNC,
                    func=data_sync_job,
                    args=(symbol, "2024-01-01", "2024-01-31"),
                    config=job_config,
                    group="data_sync"
                )
                
                job_id = self.job_manager.submit_job(job)
                sync_jobs.append(job_id)
                self.logger.info(f"提交同步作业: {job_id}")
            
            # 2. 创建依赖于同步作业的分析作业
            analysis_jobs = []
            for symbol in symbols:
                job_config = JobConfig(
                    priority=TaskPriority.MEDIUM,
                    timeout=60.0
                )
                
                job = Job(
                    job_id=f"analysis_{symbol}",
                    name=f"分析{symbol}数据",
                    job_type=JobType.DATA_ANALYSIS,
                    func=data_analysis_job,
                    args=(symbol,),
                    config=job_config,
                    group="data_analysis",
                    dependencies=[f"sync_{symbol}"]  # 依赖同步作业
                )
                
                job_id = self.job_manager.submit_job(job)
                analysis_jobs.append(job_id)
                self.logger.info(f"提交分析作业: {job_id}")
            
            # 3. 批量提交作业
            batch_jobs = []
            for i in range(5):
                job = Job(
                    job_id=f"batch_job_{i}",
                    name=f"批量作业{i}",
                    job_type=JobType.BATCH_PROCESS,
                    func=lambda x: f"批量处理 {x}",
                    args=(i,)
                )
                batch_jobs.append(job)
            
            batch_id = self.job_manager.submit_batch_jobs(batch_jobs, "batch_group")
            self.logger.info(f"提交批量作业: {batch_id}")
            
            # 等待作业完成
            time.sleep(20)
            
            # 查看作业状态
            for job_id in sync_jobs + analysis_jobs:
                job = self.job_manager.get_job(job_id)
                if job:
                    self.logger.info(f"作业 {job_id}: {job.status.value}")
                    if job.result:
                        self.logger.info(f"作业结果: {job.result}")
            
            # 查看统计信息
            stats = self.job_manager.get_stats()
            self.logger.info(f"作业管理器统计: {stats}")
        
        finally:
            self.job_manager.stop()
            self.task_scheduler.stop()
    
    def example_cron_scheduler(self):
        """Cron调度器使用示例"""
        self.logger.info("=== Cron调度器使用示例 ===")
        
        # 定义定时任务函数
        def daily_report() -> str:
            """每日报告"""
            self.logger.info("生成每日报告")
            return f"每日报告已生成 - {datetime.now()}"
        
        def hourly_sync() -> str:
            """每小时同步"""
            self.logger.info("执行每小时数据同步")
            return f"数据同步完成 - {datetime.now()}"
        
        def weekly_cleanup() -> str:
            """每周清理"""
            self.logger.info("执行每周数据清理")
            return f"数据清理完成 - {datetime.now()}"
        
        # 启动组件
        self.task_scheduler.start()
        self.cron_scheduler.start()
        
        try:
            # 1. 每分钟执行的任务（用于测试）
            job1 = CronJob(
                job_id="test_job",
                name="测试任务",
                func=lambda: self.logger.info(f"测试任务执行 - {datetime.now()}"),
                cron_expression="* * * * *"  # 每分钟执行
            )
            self.cron_scheduler.add_job(job1)
            
            # 2. 每小时执行的同步任务
            job2 = CronJob(
                job_id="hourly_sync",
                name="每小时同步",
                func=hourly_sync,
                cron_expression="0 * * * *",  # 每小时的0分执行
                max_executions=24  # 最多执行24次
            )
            self.cron_scheduler.add_job(job2)
            
            # 3. 每日报告任务
            job3 = CronJob(
                job_id="daily_report",
                name="每日报告",
                func=daily_report,
                cron_expression="0 9 * * *",  # 每天9点执行
                timezone="Asia/Shanghai"
            )
            self.cron_scheduler.add_job(job3)
            
            # 4. 每周清理任务
            job4 = CronJob(
                job_id="weekly_cleanup",
                name="每周清理",
                func=weekly_cleanup,
                cron_expression="0 2 * * 0",  # 每周日2点执行
                enabled=True
            )
            self.cron_scheduler.add_job(job4)
            
            # 5. 使用预定义的cron表达式
            from .cron_scheduler import create_daily_cron, create_hourly_cron
            
            job5 = CronJob(
                job_id="daily_backup",
                name="每日备份",
                func=lambda: self.logger.info("执行每日备份"),
                cron_expression=create_daily_cron(hour=23, minute=30)  # 每天23:30执行
            )
            self.cron_scheduler.add_job(job5)
            
            # 等待任务执行
            self.logger.info("等待Cron任务执行...")
            time.sleep(120)  # 等待2分钟观察任务执行
            
            # 查看任务状态
            jobs = self.cron_scheduler.list_jobs()
            for job in jobs:
                self.logger.info(f"Cron任务: {job.name}, 启用: {job.enabled}, 下次执行: {job.next_run_time}")
            
            # 查看统计信息
            stats = self.cron_scheduler.get_stats()
            self.logger.info(f"Cron调度器统计: {stats}")
        
        finally:
            self.cron_scheduler.stop()
            self.task_scheduler.stop()
    
    def example_task_monitor(self):
        """任务监控器使用示例"""
        self.logger.info("=== 任务监控器使用示例 ===")
        
        # 定义监控任务
        def monitored_task(name: str, should_fail: bool = False) -> str:
            """被监控的任务"""
            self.logger.info(f"执行被监控任务: {name}")
            
            if should_fail:
                raise Exception(f"任务 {name} 执行失败")
            
            time.sleep(1)
            return f"任务 {name} 完成"
        
        def slow_task(name: str) -> str:
            """慢任务"""
            self.logger.info(f"执行慢任务: {name}")
            time.sleep(5)  # 模拟慢任务
            return f"慢任务 {name} 完成"
        
        # 启动所有组件
        self.task_scheduler.start()
        self.task_monitor.start()
        
        try:
            # 添加健康检查
            def scheduler_health_check() -> bool:
                """调度器健康检查"""
                return self.task_scheduler.is_running
            
            def task_queue_health_check() -> bool:
                """任务队列健康检查"""
                stats = self.task_scheduler.get_stats()
                return stats.get('pending_tasks', 0) < 100
            
            self.task_monitor.add_health_check("scheduler", scheduler_health_check)
            self.task_monitor.add_health_check("task_queue", task_queue_health_check)
            
            # 1. 添加正常任务
            for i in range(5):
                task = ScheduledTask(
                    task_id=f"normal_task_{i}",
                    name=f"正常任务{i}",
                    func=monitored_task,
                    args=(f"正常任务{i}",),
                    interval=3.0 if i % 2 == 0 else None  # 部分任务设置间隔
                )
                self.task_scheduler.add_task(task)
            
            # 2. 添加会失败的任务
            for i in range(3):
                task = ScheduledTask(
                    task_id=f"failing_task_{i}",
                    name=f"失败任务{i}",
                    func=monitored_task,
                    args=(f"失败任务{i}", True),  # should_fail=True
                    interval=2.0,
                    max_retries=2
                )
                self.task_scheduler.add_task(task)
            
            # 3. 添加慢任务
            task = ScheduledTask(
                task_id="slow_task",
                name="慢任务",
                func=slow_task,
                args=("慢任务",),
                interval=8.0
            )
            self.task_scheduler.add_task(task)
            
            # 等待任务执行和监控数据收集
            time.sleep(30)
            
            # 查看任务指标
            task_metrics = self.task_monitor.get_task_metrics()
            for task_id, metrics in task_metrics.items():
                self.logger.info(f"任务 {task_id} 指标:")
                self.logger.info(f"  总执行次数: {metrics.total_executions}")
                self.logger.info(f"  成功次数: {metrics.successful_executions}")
                self.logger.info(f"  失败次数: {metrics.failed_executions}")
                self.logger.info(f"  成功率: {metrics.get_success_rate():.2%}")
                self.logger.info(f"  平均执行时间: {metrics.avg_execution_time:.2f}s")
                self.logger.info(f"  连续失败次数: {metrics.consecutive_failures}")
            
            # 查看系统指标
            system_metrics = self.task_monitor.get_system_metrics()
            self.logger.info(f"系统指标: {system_metrics}")
            
            # 查看告警
            alerts = self.task_monitor.get_alerts()
            self.logger.info(f"共有 {len(alerts)} 个告警")
            for alert in alerts[:5]:  # 显示前5个告警
                self.logger.info(f"告警: [{alert.level.value}] {alert.title} - {alert.message}")
            
            # 查看健康状态
            health_status = self.task_monitor.get_health_status()
            health_report = self.task_monitor.get_health_report()
            self.logger.info(f"健康状态: {health_status.value}")
            self.logger.info(f"健康报告: {health_report}")
            
            # 手动创建告警
            alert_id = self.task_monitor.create_alert(
                level=AlertLevel.WARNING,
                title="手动测试告警",
                message="这是一个手动创建的测试告警",
                source="example"
            )
            self.logger.info(f"创建测试告警: {alert_id}")
            
            # 确认告警
            self.task_monitor.acknowledge_alert(alert_id, "管理员")
            
        finally:
            self.task_monitor.stop()
            self.task_scheduler.stop()
    
    def run_all_examples(self):
        """运行所有示例"""
        self.logger.info("开始运行调度系统示例")
        
        try:
            # 1. 任务调度器示例
            self.example_task_scheduler()
            time.sleep(2)
            
            # 2. 作业管理器示例
            self.example_job_manager()
            time.sleep(2)
            
            # 3. Cron调度器示例
            self.example_cron_scheduler()
            time.sleep(2)
            
            # 4. 任务监控器示例
            self.example_task_monitor()
            
        except Exception as e:
            self.logger.error(f"示例运行出错: {e}", exc_info=True)
        
        self.logger.info("调度系统示例运行完成")


def main():
    """主函数"""
    examples = SchedulerExamples()
    
    # 可以选择运行特定示例
    import sys
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        if hasattr(examples, f"example_{example_name}"):
            getattr(examples, f"example_{example_name}")()
        else:
            print(f"未找到示例: {example_name}")
            print("可用示例: task_scheduler, job_manager, cron_scheduler, task_monitor")
    else:
        # 运行所有示例
        examples.run_all_examples()


if __name__ == "__main__":
    main()