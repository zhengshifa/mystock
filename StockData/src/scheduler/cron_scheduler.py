#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cron调度器模块

提供基于Cron表达式的任务调度功能:
- Cron表达式解析
- 定时任务调度
- 时区支持
- 任务执行历史
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import threading
import time

from .task_scheduler import TaskScheduler, ScheduledTask, TaskStatus, TaskPriority
from ..utils import get_logger, now, ValidationError, DateValidationError


class CronField(Enum):
    """Cron字段枚举"""
    MINUTE = 0      # 分钟 (0-59)
    HOUR = 1        # 小时 (0-23)
    DAY = 2         # 日 (1-31)
    MONTH = 3       # 月 (1-12)
    WEEKDAY = 4     # 星期 (0-7, 0和7都表示周日)


@dataclass
class CronExpression:
    """Cron表达式"""
    minute: str = "*"       # 分钟
    hour: str = "*"         # 小时
    day: str = "*"          # 日
    month: str = "*"        # 月
    weekday: str = "*"      # 星期
    
    def __post_init__(self):
        self.validate()
    
    def validate(self):
        """验证Cron表达式"""
        fields = {
            'minute': (self.minute, 0, 59),
            'hour': (self.hour, 0, 23),
            'day': (self.day, 1, 31),
            'month': (self.month, 1, 12),
            'weekday': (self.weekday, 0, 7)
        }
        
        for field_name, (value, min_val, max_val) in fields.items():
            if not self._validate_field(value, min_val, max_val):
                raise ValidationError(f"Invalid cron field '{field_name}': {value}")
    
    def _validate_field(self, field_value: str, min_val: int, max_val: int) -> bool:
        """验证单个字段"""
        if field_value == "*":
            return True
        
        # 处理逗号分隔的值
        for part in field_value.split(','):
            part = part.strip()
            
            # 处理范围 (e.g., "1-5")
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if not (min_val <= start <= max_val and min_val <= end <= max_val and start <= end):
                        return False
                except ValueError:
                    return False
            
            # 处理步长 (e.g., "*/5" or "1-10/2")
            elif '/' in part:
                try:
                    base, step = part.split('/')
                    step = int(step)
                    if step <= 0:
                        return False
                    
                    if base == "*":
                        continue
                    elif '-' in base:
                        start, end = map(int, base.split('-'))
                        if not (min_val <= start <= max_val and min_val <= end <= max_val):
                            return False
                    else:
                        value = int(base)
                        if not (min_val <= value <= max_val):
                            return False
                except ValueError:
                    return False
            
            # 处理单个数值
            else:
                try:
                    value = int(part)
                    if not (min_val <= value <= max_val):
                        return False
                except ValueError:
                    return False
        
        return True
    
    @classmethod
    def from_string(cls, cron_str: str) -> 'CronExpression':
        """从字符串创建Cron表达式"""
        parts = cron_str.strip().split()
        if len(parts) != 5:
            raise ValidationError(f"Invalid cron expression: {cron_str}. Expected 5 fields.")
        
        return cls(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            weekday=parts[4]
        )
    
    def to_string(self) -> str:
        """转换为字符串"""
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"
    
    def matches(self, dt: datetime) -> bool:
        """检查时间是否匹配Cron表达式"""
        return (
            self._matches_field(self.minute, dt.minute, 0, 59) and
            self._matches_field(self.hour, dt.hour, 0, 23) and
            self._matches_field(self.day, dt.day, 1, 31) and
            self._matches_field(self.month, dt.month, 1, 12) and
            self._matches_weekday(self.weekday, dt.weekday())
        )
    
    def _matches_field(self, field_value: str, actual_value: int, 
                      min_val: int, max_val: int) -> bool:
        """检查字段是否匹配"""
        if field_value == "*":
            return True
        
        for part in field_value.split(','):
            part = part.strip()
            
            if '-' in part and '/' not in part:
                # 范围匹配
                start, end = map(int, part.split('-'))
                if start <= actual_value <= end:
                    return True
            
            elif '/' in part:
                # 步长匹配
                base, step = part.split('/')
                step = int(step)
                
                if base == "*":
                    if actual_value % step == 0:
                        return True
                elif '-' in base:
                    start, end = map(int, base.split('-'))
                    if start <= actual_value <= end and (actual_value - start) % step == 0:
                        return True
                else:
                    base_val = int(base)
                    if actual_value >= base_val and (actual_value - base_val) % step == 0:
                        return True
            
            else:
                # 精确匹配
                if int(part) == actual_value:
                    return True
        
        return False
    
    def _matches_weekday(self, weekday_field: str, actual_weekday: int) -> bool:
        """检查星期是否匹配"""
        if weekday_field == "*":
            return True
        
        # Python的weekday(): Monday=0, Sunday=6
        # Cron的weekday: Sunday=0, Monday=1, ..., Saturday=6, Sunday=7
        # 转换: Python weekday -> Cron weekday
        cron_weekday = (actual_weekday + 1) % 7
        
        for part in weekday_field.split(','):
            part = part.strip()
            
            if '-' in part and '/' not in part:
                start, end = map(int, part.split('-'))
                # 处理7作为周日的情况
                if start == 7:
                    start = 0
                if end == 7:
                    end = 0
                
                if start <= end:
                    if start <= cron_weekday <= end:
                        return True
                else:  # 跨周的情况，如 6-1 (周六到周一)
                    if cron_weekday >= start or cron_weekday <= end:
                        return True
            
            elif '/' in part:
                # 步长匹配
                base, step = part.split('/')
                step = int(step)
                
                if base == "*":
                    if cron_weekday % step == 0:
                        return True
                else:
                    base_val = int(base)
                    if base_val == 7:
                        base_val = 0
                    if cron_weekday >= base_val and (cron_weekday - base_val) % step == 0:
                        return True
            
            else:
                # 精确匹配
                target = int(part)
                if target == 7:
                    target = 0
                if target == cron_weekday:
                    return True
        
        return False
    
    def next_run_time(self, after: datetime) -> datetime:
        """计算下次执行时间"""
        # 从下一分钟开始检查
        next_time = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # 最多检查4年（避免无限循环）
        max_iterations = 4 * 365 * 24 * 60
        iterations = 0
        
        while iterations < max_iterations:
            if self.matches(next_time):
                return next_time
            
            next_time += timedelta(minutes=1)
            iterations += 1
        
        raise ValidationError("Could not find next run time within 4 years")


@dataclass
class CronJob:
    """Cron任务"""
    job_id: str
    name: str
    cron_expression: CronExpression
    func: callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    
    # 配置
    timezone: str = "CST"
    enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 60.0
    timeout: Optional[float] = None
    priority: TaskPriority = TaskPriority.NORMAL
    
    # 状态
    created_time: datetime = field(default_factory=now)
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    run_count: int = 0
    
    # 执行历史
    execution_history: List[Dict] = field(default_factory=list)
    
    # 其他
    description: str = ""
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        if self.next_run_time is None:
            self.update_next_run_time()
    
    def update_next_run_time(self, after: Optional[datetime] = None):
        """更新下次执行时间"""
        if after is None:
            after = now()
        
        try:
            self.next_run_time = self.cron_expression.next_run_time(after)
        except ValidationError as e:
            self.next_run_time = None
            raise e
    
    def should_run(self, current_time: Optional[datetime] = None) -> bool:
        """判断是否应该执行"""
        if not self.enabled or self.next_run_time is None:
            return False
        
        if current_time is None:
            current_time = now()
        
        return current_time >= self.next_run_time
    
    def add_execution_record(self, start_time: datetime, end_time: datetime,
                           success: bool, error: Optional[str] = None,
                           result: Optional[any] = None):
        """添加执行记录"""
        record = {
            'start_time': start_time,
            'end_time': end_time,
            'duration': (end_time - start_time).total_seconds(),
            'success': success,
            'error': error,
            'result': str(result) if result is not None else None
        }
        
        self.execution_history.append(record)
        
        # 只保留最近100次执行记录
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        self.run_count += 1
        self.last_run_time = start_time


class CronScheduler:
    """Cron调度器"""
    
    def __init__(self, scheduler: Optional[TaskScheduler] = None,
                 logger_name: str = "CronScheduler"):
        self.scheduler = scheduler or TaskScheduler()
        self.logger = get_logger(logger_name)
        
        # Cron任务存储
        self.cron_jobs: Dict[str, CronJob] = {}
        
        # 调度器状态
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 统计信息
        self.stats = {
            'total_cron_jobs': 0,
            'active_cron_jobs': 0,
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0
        }
        
        self.logger.info("CronScheduler initialized")
    
    def add_cron_job(self, name: str, cron_expression: Union[str, CronExpression],
                    func: callable, args: tuple = (), kwargs: dict = None,
                    timezone: str = "CST", enabled: bool = True,
                    max_retries: int = 3, retry_delay: float = 60.0,
                    timeout: Optional[float] = None,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    description: str = "", tags: Set[str] = None) -> str:
        """添加Cron任务"""
        job_id = f"cron_{int(now().timestamp())}_{len(self.cron_jobs)}"
        
        if isinstance(cron_expression, str):
            cron_expr = CronExpression.from_string(cron_expression)
        else:
            cron_expr = cron_expression
        
        cron_job = CronJob(
            job_id=job_id,
            name=name,
            cron_expression=cron_expr,
            func=func,
            args=args,
            kwargs=kwargs or {},
            timezone=timezone,
            enabled=enabled,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            priority=priority,
            description=description,
            tags=tags or set()
        )
        
        self.cron_jobs[job_id] = cron_job
        self.stats['total_cron_jobs'] += 1
        if enabled:
            self.stats['active_cron_jobs'] += 1
        
        self.logger.info(f"Added cron job: {name} ({job_id}) - {cron_expr.to_string()}")
        return job_id
    
    def remove_cron_job(self, job_id: str) -> bool:
        """移除Cron任务"""
        if job_id not in self.cron_jobs:
            return False
        
        cron_job = self.cron_jobs[job_id]
        if cron_job.enabled:
            self.stats['active_cron_jobs'] -= 1
        
        del self.cron_jobs[job_id]
        self.logger.info(f"Removed cron job: {cron_job.name} ({job_id})")
        return True
    
    def enable_cron_job(self, job_id: str) -> bool:
        """启用Cron任务"""
        cron_job = self.cron_jobs.get(job_id)
        if not cron_job:
            return False
        
        if not cron_job.enabled:
            cron_job.enabled = True
            cron_job.update_next_run_time()
            self.stats['active_cron_jobs'] += 1
            self.logger.info(f"Enabled cron job: {cron_job.name} ({job_id})")
        
        return True
    
    def disable_cron_job(self, job_id: str) -> bool:
        """禁用Cron任务"""
        cron_job = self.cron_jobs.get(job_id)
        if not cron_job:
            return False
        
        if cron_job.enabled:
            cron_job.enabled = False
            self.stats['active_cron_jobs'] -= 1
            self.logger.info(f"Disabled cron job: {cron_job.name} ({job_id})")
        
        return True
    
    def get_cron_job(self, job_id: str) -> Optional[CronJob]:
        """获取Cron任务"""
        return self.cron_jobs.get(job_id)
    
    def list_cron_jobs(self, enabled_only: bool = False,
                      tags: Optional[Set[str]] = None) -> List[CronJob]:
        """列出Cron任务"""
        jobs = list(self.cron_jobs.values())
        
        if enabled_only:
            jobs = [j for j in jobs if j.enabled]
        
        if tags:
            jobs = [j for j in jobs if tags.intersection(j.tags)]
        
        return jobs
    
    def run_cron_job_once(self, job_id: str) -> bool:
        """立即执行Cron任务一次"""
        cron_job = self.cron_jobs.get(job_id)
        if not cron_job:
            return False
        
        self._execute_cron_job(cron_job)
        return True
    
    def start(self):
        """启动Cron调度器"""
        if self.is_running:
            self.logger.warning("CronScheduler is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # 启动底层调度器
        self.scheduler.start()
        
        # 启动Cron调度线程
        self.scheduler_thread = threading.Thread(target=self._cron_scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("CronScheduler started")
    
    def stop(self, wait_for_completion: bool = True):
        """停止Cron调度器"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping CronScheduler...")
        self.is_running = False
        self.stop_event.set()
        
        # 等待调度线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)
        
        # 停止底层调度器
        self.scheduler.stop(wait_for_completion)
        
        self.logger.info("CronScheduler stopped")
    
    def get_stats(self) -> Dict[str, any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats.update({
            'scheduler_running': self.is_running,
            'base_scheduler_stats': self.scheduler.get_stats()
        })
        
        return stats
    
    def _cron_scheduler_loop(self):
        """Cron调度主循环"""
        self.logger.info("Cron scheduler loop started")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                current_time = now()
                
                # 检查需要执行的Cron任务
                for cron_job in self.cron_jobs.values():
                    if cron_job.should_run(current_time):
                        self._execute_cron_job(cron_job)
                        # 更新下次执行时间
                        cron_job.update_next_run_time(current_time)
                
                # 每分钟检查一次
                self.stop_event.wait(60.0)
                
            except Exception as e:
                self.logger.error(f"Error in cron scheduler loop: {e}", exc_info=True)
                self.stop_event.wait(60.0)
        
        self.logger.info("Cron scheduler loop ended")
    
    def _execute_cron_job(self, cron_job: CronJob):
        """执行Cron任务"""
        try:
            self.logger.info(f"Executing cron job: {cron_job.name} ({cron_job.job_id})")
            
            # 创建调度任务
            task = ScheduledTask(
                task_id=f"cron_{cron_job.job_id}_{int(now().timestamp())}",
                name=f"{cron_job.name}_execution",
                func=cron_job.func,
                args=cron_job.args,
                kwargs=cron_job.kwargs,
                priority=cron_job.priority,
                max_retries=cron_job.max_retries,
                retry_delay=cron_job.retry_delay,
                timeout=cron_job.timeout
            )
            
            # 执行任务
            start_time = now()
            task_id = self.scheduler.add_task(task)
            result = self.scheduler.run_task_once(task_id)
            end_time = now()
            
            # 记录执行结果
            if result:
                success = result.status == TaskStatus.COMPLETED
                error = str(result.error) if result.error else None
                
                cron_job.add_execution_record(
                    start_time=start_time,
                    end_time=end_time,
                    success=success,
                    error=error,
                    result=result.result
                )
                
                # 更新统计信息
                self.stats['total_executions'] += 1
                if success:
                    self.stats['successful_executions'] += 1
                else:
                    self.stats['failed_executions'] += 1
            
            # 清理任务
            self.scheduler.remove_task(task_id)
            
        except Exception as e:
            self.logger.error(f"Failed to execute cron job {cron_job.job_id}: {e}", exc_info=True)
            
            # 记录失败
            cron_job.add_execution_record(
                start_time=now(),
                end_time=now(),
                success=False,
                error=str(e)
            )
            
            self.stats['total_executions'] += 1
            self.stats['failed_executions'] += 1
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# 便捷函数
def create_cron_expression(minute: str = "*", hour: str = "*", 
                          day: str = "*", month: str = "*", 
                          weekday: str = "*") -> CronExpression:
    """创建Cron表达式"""
    return CronExpression(minute, hour, day, month, weekday)


# 预定义的Cron表达式
CRON_PRESETS = {
    'every_minute': "* * * * *",
    'every_5_minutes': "*/5 * * * *",
    'every_15_minutes': "*/15 * * * *",
    'every_30_minutes': "*/30 * * * *",
    'hourly': "0 * * * *",
    'daily': "0 0 * * *",
    'daily_at_6am': "0 6 * * *",
    'daily_at_9am': "0 9 * * *",
    'daily_at_6pm': "0 18 * * *",
    'weekly': "0 0 * * 0",
    'monthly': "0 0 1 * *",
    'yearly': "0 0 1 1 *",
    'weekdays_9am': "0 9 * * 1-5",
    'weekends_10am': "0 10 * * 0,6",
    'market_open': "30 9 * * 1-5",  # 工作日9:30
    'market_close': "0 15 * * 1-5",  # 工作日15:00
}