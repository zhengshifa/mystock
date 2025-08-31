#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度器模块
支持定时任务、异步任务、任务监控等功能
"""

import asyncio
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import weakref

from ..config.settings import get_scheduler_config, SchedulerConfig
from ..logging.logger import get_task_logger, get_performance_logger


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskInfo:
    """任务信息"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    tags: List[str] = field(default_factory=list)


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        """
        初始化任务调度器
        
        Args:
            config: 调度器配置
        """
        self.config = config or get_scheduler_config()
        self.logger = get_task_logger("TaskScheduler")
        self.performance_logger = get_performance_logger("TaskScheduler")
        
        # 任务存储
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_queue = queue.PriorityQueue()
        
        # 执行器
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix=self.config.thread_name_prefix
        )
        
        # 定时任务
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.scheduler_thread = None
        self.running = False
        
        # 监控
        self.monitoring_enabled = self.config.enable_monitoring
        self.heartbeat_thread = None
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "running_tasks": 0,
            "pending_tasks": 0
        }
    
    def start(self):
        """启动调度器"""
        if self.running:
            self.logger.warning("调度器已经在运行")
            return
        
        self.running = True
        self.logger.info("启动任务调度器")
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="TaskScheduler",
            daemon=True
        )
        self.scheduler_thread.start()
        
        # 启动监控线程
        if self.monitoring_enabled:
            self.heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                name="TaskSchedulerHeartbeat",
                daemon=True
            )
            self.heartbeat_thread.start()
        
        self.logger.info("任务调度器启动成功")
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.logger.info("正在停止任务调度器...")
        self.running = False
        
        # 等待线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)
        
        # 关闭执行器
        self.executor.shutdown(wait=True)
        self.logger.info("任务调度器已停止")
    
    def submit_task(self, name: str, func: Callable, *args, 
                   priority: Union[TaskPriority, int] = TaskPriority.NORMAL,
                   timeout: Optional[float] = None,
                   max_retries: int = 3,
                   tags: Optional[List[str]] = None,
                   **kwargs) -> str:
        """
        提交任务
        
        Args:
            name: 任务名称
            func: 要执行的函数
            *args: 函数参数
            priority: 任务优先级
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            tags: 任务标签
            **kwargs: 函数关键字参数
            
        Returns:
            任务ID
        """
        task_id = f"{name}_{int(time.time() * 1000)}"
        
        # 处理优先级参数
        if isinstance(priority, int):
            priority_enum = TaskPriority(priority)
        else:
            priority_enum = priority
        
        task_info = TaskInfo(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority_enum,
            timeout=timeout,
            max_retries=max_retries,
            tags=tags or []
        )
        
        self.tasks[task_id] = task_info
        self.task_queue.put((priority_enum.value, time.time(), task_id))
        
        self.stats["total_tasks"] += 1
        self.stats["pending_tasks"] += 1
        
        self.logger.info(f"提交任务: {name} (ID: {task_id})")
        return task_id
    
    def schedule_task(self, name: str, func: Callable, schedule_time: Union[datetime, timedelta],
                     *args, **kwargs) -> str:
        """
        调度定时任务
        
        Args:
            name: 任务名称
            schedule_time: 执行时间或延迟时间
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            任务ID
        """
        if isinstance(schedule_time, timedelta):
            schedule_time = datetime.now() + schedule_time
        
        task_id = self.submit_task(name, func, *args, **kwargs)
        
        self.scheduled_tasks[task_id] = {
            "schedule_time": schedule_time,
            "task_id": task_id
        }
        
        self.logger.info(f"调度定时任务: {name} 将在 {schedule_time} 执行")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        if task_id not in self.tasks:
            self.logger.warning(f"任务 {task_id} 不存在")
            return False
        
        task_info = self.tasks[task_id]
        if task_info.status == TaskStatus.RUNNING:
            self.logger.warning(f"任务 {task_id} 正在运行，无法取消")
            return False
        
        if task_info.status == TaskStatus.PENDING:
            # 从队列中移除
            # 注意：PriorityQueue不支持直接移除，这里只是标记状态
            task_info.status = TaskStatus.CANCELLED
            self.stats["pending_tasks"] -= 1
            self.logger.info(f"取消任务: {task_id}")
            return True
        
        return False
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None
    
    def get_task_result(self, task_id: str) -> Any:
        """获取任务结果"""
        if task_id in self.tasks:
            return self.tasks[task_id].result
        return None
    
    def get_task_error(self, task_id: str) -> Optional[str]:
        """获取任务错误信息"""
        if task_id in self.tasks:
            return self.tasks[task_id].error
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.running:
            try:
                # 检查定时任务
                self._check_scheduled_tasks()
                
                # 处理任务队列
                if not self.task_queue.empty():
                    priority, timestamp, task_id = self.task_queue.get_nowait()
                    
                    if task_id in self.tasks:
                        task_info = self.tasks[task_id]
                        if task_info.status == TaskStatus.PENDING:
                            self._execute_task(task_info)
                
                time.sleep(0.1)  # 避免CPU占用过高
                
            except Exception as e:
                self.logger.error(f"调度器循环异常: {e}")
                time.sleep(1)
    
    def _check_scheduled_tasks(self):
        """检查定时任务"""
        current_time = datetime.now()
        tasks_to_execute = []
        
        for task_id, schedule_info in self.scheduled_tasks.items():
            if current_time >= schedule_info["schedule_time"]:
                tasks_to_execute.append(task_id)
        
        for task_id in tasks_to_execute:
            if task_id in self.tasks:
                task_info = self.tasks[task_id]
                if task_info.status == TaskStatus.PENDING:
                    self._execute_task(task_info)
            del self.scheduled_tasks[task_id]
    
    def _execute_task(self, task_info: TaskInfo):
        """执行任务"""
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = datetime.now()
        self.stats["pending_tasks"] -= 1
        self.stats["running_tasks"] += 1
        
        self.logger.info(f"开始执行任务: {task_info.name} (ID: {task_info.id})")
        self.performance_logger.start_timer(task_info.id)
        
        # 提交到线程池执行
        future = self.executor.submit(self._task_wrapper, task_info)
        future.add_done_callback(lambda f: self._task_callback(f, task_info))
    
    def _task_wrapper(self, task_info: TaskInfo):
        """任务包装器"""
        try:
            if task_info.timeout:
                # 带超时的执行
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"任务 {task_info.name} 执行超时")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(task_info.timeout))
                
                try:
                    result = task_info.func(*task_info.args, **task_info.kwargs)
                    signal.alarm(0)
                    return result
                except TimeoutError:
                    signal.alarm(0)
                    raise
            else:
                # 正常执行
                return task_info.func(*task_info.args, **task_info.kwargs)
                
        except Exception as e:
            return e
    
    def _task_callback(self, future, task_info: TaskInfo):
        """任务完成回调"""
        try:
            result = future.result()
            
            if isinstance(result, Exception):
                # 任务执行失败
                task_info.status = TaskStatus.FAILED
                task_info.error = str(result)
                self.stats["failed_tasks"] += 1
                
                # 重试逻辑
                if task_info.retry_count < task_info.max_retries:
                    task_info.retry_count += 1
                    task_info.status = TaskStatus.PENDING
                    self.task_queue.put((task_info.priority.value, time.time(), task_info.id))
                    self.stats["pending_tasks"] += 1
                    self.stats["failed_tasks"] -= 1
                    self.logger.info(f"任务 {task_info.name} 将重试 ({task_info.retry_count}/{task_info.max_retries})")
                else:
                    self.logger.error(f"任务 {task_info.name} 执行失败: {result}")
            else:
                # 任务执行成功
                task_info.status = TaskStatus.COMPLETED
                task_info.result = result
                self.stats["completed_tasks"] += 1
                self.logger.info(f"任务 {task_info.name} 执行成功")
            
        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.error = str(e)
            self.stats["failed_tasks"] += 1
            self.logger.error(f"任务 {task_info.name} 执行异常: {e}")
        
        finally:
            task_info.completed_at = datetime.now()
            self.stats["running_tasks"] -= 1
            self.performance_logger.end_timer(task_info.id)
    
    def _heartbeat_loop(self):
        """心跳监控循环"""
        while self.running:
            try:
                # 记录心跳信息
                self.logger.debug(f"调度器心跳 - 运行中任务: {self.stats['running_tasks']}, "
                                f"等待中任务: {self.stats['pending_tasks']}")
                
                time.sleep(self.config.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"心跳监控异常: {e}")
                time.sleep(5)


# 全局调度器实例
task_scheduler = TaskScheduler()


def get_scheduler() -> TaskScheduler:
    """获取全局调度器"""
    return task_scheduler


def submit_task(name: str, func: Callable, *args, **kwargs) -> str:
    """提交任务到全局调度器"""
    return task_scheduler.submit_task(name, func, *args, **kwargs)


def schedule_task(name: str, func: Callable, schedule_time: Union[datetime, timedelta],
                 *args, **kwargs) -> str:
    """调度定时任务到全局调度器"""
    return task_scheduler.schedule_task(name, func, schedule_time, *args, **kwargs)


def cancel_task(task_id: str) -> bool:
    """取消任务"""
    return task_scheduler.cancel_task(task_id)


def get_task_status(task_id: str) -> Optional[TaskStatus]:
    """获取任务状态"""
    return task_scheduler.get_task_status(task_id)


def get_task_result(task_id: str) -> Any:
    """获取任务结果"""
    return task_scheduler.get_task_result(task_id)
