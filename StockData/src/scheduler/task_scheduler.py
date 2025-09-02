#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度器模块

提供核心的任务调度功能:
- 定时任务执行
- 任务队列管理
- 任务状态跟踪
- 异常处理和重试
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
import uuid

from ..utils import get_logger, LoggerManager, now, ValidationError, ResourceError


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 等待执行
    RUNNING = "running"          # 正在执行
    COMPLETED = "completed"      # 执行完成
    FAILED = "failed"            # 执行失败
    CANCELLED = "cancelled"      # 已取消
    RETRYING = "retrying"        # 重试中
    PAUSED = "paused"            # 已暂停


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.start_time and self.end_time:
            self.duration = (self.end_time - self.start_time).total_seconds()


@dataclass
class ScheduledTask:
    """调度任务定义"""
    task_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    
    # 调度配置
    interval: Optional[float] = None  # 间隔秒数
    cron_expression: Optional[str] = None  # Cron表达式
    next_run_time: Optional[datetime] = None
    
    # 任务配置
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 60.0  # 重试延迟秒数
    timeout: Optional[float] = None  # 超时秒数
    
    # 状态信息
    status: TaskStatus = TaskStatus.PENDING
    created_time: datetime = field(default_factory=now)
    last_run_time: Optional[datetime] = None
    last_result: Optional[TaskResult] = None
    retry_count: int = 0
    
    # 依赖关系
    dependencies: List[str] = field(default_factory=list)
    
    # 其他配置
    enabled: bool = True
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        
        # 设置下次执行时间
        if self.next_run_time is None and self.interval:
            self.next_run_time = now() + timedelta(seconds=self.interval)
    
    def should_run(self) -> bool:
        """判断任务是否应该执行"""
        if not self.enabled or self.status in [TaskStatus.RUNNING, TaskStatus.CANCELLED]:
            return False
        
        if self.next_run_time is None:
            return False
        
        return now() >= self.next_run_time
    
    def update_next_run_time(self):
        """更新下次执行时间"""
        if self.interval:
            self.next_run_time = now() + timedelta(seconds=self.interval)
        elif self.cron_expression:
            # TODO: 实现Cron表达式解析
            pass
    
    def reset_retry(self):
        """重置重试计数"""
        self.retry_count = 0
        self.status = TaskStatus.PENDING


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, config: Dict[str, Any], max_workers: int = 10, logger_name: str = "TaskScheduler"):
        self.config = config
        self.max_workers = max_workers
        self.logger = get_logger(logger_name)
        
        # 任务存储
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, Future] = {}
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 调度器状态
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0
        }
        
        self.logger.info(f"TaskScheduler initialized with {max_workers} workers")
    
    async def initialize(self) -> None:
        """初始化任务调度器"""
        self.logger.info("任务调度器初始化中...")
        # 这里可以添加初始化逻辑
        self.logger.info("任务调度器初始化完成")
    
    def start(self) -> None:
        """启动任务调度器"""
        self.logger.info("启动任务调度器...")
        if not self.is_running:
            self.is_running = True
            self.stop_event.clear()
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            self.logger.info("TaskScheduler started")
        else:
            self.logger.warning("TaskScheduler is already running")
    
    def stop(self) -> None:
        """停止任务调度器"""
        self.logger.info("Stopping TaskScheduler...")
        if self.is_running:
            self.is_running = False
            self.stop_event.set()
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            self.logger.info("TaskScheduler stopped")
        else:
            self.logger.warning("TaskScheduler is not running")
    
    def add_task(self, task: ScheduledTask) -> str:
        """添加任务"""
        if task.task_id in self.tasks:
            raise ValidationError(f"Task with ID {task.task_id} already exists")
        
        # 验证依赖关系
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                raise ValidationError(f"Dependency task {dep_id} not found")
        
        self.tasks[task.task_id] = task
        self.stats['total_tasks'] += 1
        
        self.logger.info(f"Added task: {task.name} ({task.task_id})")
        return task.task_id
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id not in self.tasks:
            return False
        
        # 如果任务正在运行，先取消
        if task_id in self.running_tasks:
            self.cancel_task(task_id)
        
        # 检查是否有其他任务依赖此任务
        dependent_tasks = [t for t in self.tasks.values() if task_id in t.dependencies]
        if dependent_tasks:
            task_names = [t.name for t in dependent_tasks]
            raise ValidationError(f"Cannot remove task {task_id}, it has dependent tasks: {task_names}")
        
        del self.tasks[task_id]
        self.logger.info(f"Removed task: {task_id}")
        return True
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: Optional[TaskStatus] = None, 
                  tags: Optional[List[str]] = None) -> List[ScheduledTask]:
        """列出任务"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
        
        return tasks
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.enabled = True
        self.logger.info(f"Enabled task: {task.name} ({task_id})")
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.enabled = False
        self.logger.info(f"Disabled task: {task.name} ({task_id})")
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        # 如果任务正在运行，取消Future
        if task_id in self.running_tasks:
            future = self.running_tasks[task_id]
            future.cancel()
            del self.running_tasks[task_id]
        
        task.status = TaskStatus.CANCELLED
        self.stats['cancelled_tasks'] += 1
        
        self.logger.info(f"Cancelled task: {task.name} ({task_id})")
        return True
    
    def run_task_once(self, task_id: str) -> Optional[TaskResult]:
        """立即执行任务一次"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        if task.status == TaskStatus.RUNNING:
            raise ValidationError(f"Task {task_id} is already running")
        
        return self._execute_task(task)
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("TaskScheduler started")
    
    def stop(self, wait_for_completion: bool = True):
        """停止调度器"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping TaskScheduler...")
        self.is_running = False
        self.stop_event.set()
        
        # 等待调度器线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)
        
        # 取消所有运行中的任务
        if not wait_for_completion:
            for task_id in list(self.running_tasks.keys()):
                self.cancel_task(task_id)
        else:
            # 等待所有任务完成
            for future in self.running_tasks.values():
                try:
                    future.result(timeout=30.0)
                except Exception:
                    pass
        
        # 关闭线程池
        self.executor.shutdown(wait=wait_for_completion)
        
        self.logger.info("TaskScheduler stopped")
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.RUNNING:
            # 不能暂停正在运行的任务
            return False
        
        task.status = TaskStatus.PAUSED
        self.logger.info(f"Paused task: {task.name} ({task_id})")
        return True
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.PAUSED:
            task.status = TaskStatus.PENDING
            self.logger.info(f"Resumed task: {task.name} ({task_id})")
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        running_count = len(self.running_tasks)
        pending_count = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        
        stats = self.stats.copy()
        stats.update({
            'running_tasks': running_count,
            'pending_tasks': pending_count,
            'total_registered_tasks': len(self.tasks),
            'scheduler_running': self.is_running
        })
        
        return stats
    
    def _scheduler_loop(self):
        """调度器主循环"""
        self.logger.info("Scheduler loop started")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 检查需要执行的任务
                ready_tasks = self._get_ready_tasks()
                
                # 按优先级排序
                ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
                
                # 执行任务
                for task in ready_tasks:
                    if len(self.running_tasks) >= self.max_workers:
                        break  # 达到最大并发数
                    
                    self._submit_task(task)
                
                # 清理已完成的任务
                self._cleanup_completed_tasks()
                
                # 短暂休眠
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(5.0)  # 出错时休眠更长时间
        
        self.logger.info("Scheduler loop ended")
    
    def _get_ready_tasks(self) -> List[ScheduledTask]:
        """获取准备执行的任务"""
        ready_tasks = []
        
        for task in self.tasks.values():
            if not task.should_run():
                continue
            
            # 检查依赖关系
            if not self._check_dependencies(task):
                continue
            
            ready_tasks.append(task)
        
        return ready_tasks
    
    def _check_dependencies(self, task: ScheduledTask) -> bool:
        """检查任务依赖关系"""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task:
                continue
            
            # 依赖任务必须已完成
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _submit_task(self, task: ScheduledTask):
        """提交任务执行"""
        if task.task_id in self.running_tasks:
            return
        
        task.status = TaskStatus.RUNNING
        task.last_run_time = now()
        
        future = self.executor.submit(self._execute_task, task)
        self.running_tasks[task.task_id] = future
        
        self.logger.debug(f"Submitted task: {task.name} ({task.task_id})")
    
    def _execute_task(self, task: ScheduledTask) -> TaskResult:
        """执行任务"""
        start_time = now()
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            start_time=start_time,
            retry_count=task.retry_count
        )
        
        try:
            self.logger.info(f"Executing task: {task.name} ({task.task_id})")
            
            # 执行任务函数
            if task.timeout:
                # TODO: 实现超时控制
                task_result = task.func(*task.args, **task.kwargs)
            else:
                task_result = task.func(*task.args, **task.kwargs)
            
            # 任务成功完成
            result.status = TaskStatus.COMPLETED
            result.result = task_result
            task.status = TaskStatus.COMPLETED
            task.reset_retry()
            
            # 更新下次执行时间
            task.update_next_run_time()
            
            self.stats['completed_tasks'] += 1
            self.logger.info(f"Task completed: {task.name} ({task.task_id})")
            
        except Exception as e:
            # 任务执行失败
            result.status = TaskStatus.FAILED
            result.error = e
            
            self.logger.error(f"Task failed: {task.name} ({task.task_id}): {e}", exc_info=True)
            
            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                task.next_run_time = now() + timedelta(seconds=task.retry_delay)
                self.logger.info(f"Task will retry in {task.retry_delay}s: {task.name} ({task.task_id})")
            else:
                task.status = TaskStatus.FAILED
                self.stats['failed_tasks'] += 1
        
        finally:
            result.end_time = now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            task.last_result = result
            
            # 更新统计信息
            self.stats['total_execution_time'] += result.duration
            if self.stats['completed_tasks'] > 0:
                self.stats['average_execution_time'] = (
                    self.stats['total_execution_time'] / self.stats['completed_tasks']
                )
        
        return result
    
    def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed_task_ids = []
        
        for task_id, future in self.running_tasks.items():
            if future.done():
                completed_task_ids.append(task_id)
        
        for task_id in completed_task_ids:
            del self.running_tasks[task_id]
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()