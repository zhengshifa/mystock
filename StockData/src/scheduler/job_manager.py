#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器模块

提供高级任务管理功能:
- 任务生命周期管理
- 任务分组和批处理
- 任务队列管理
- 任务持久化
"""

import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading
from collections import defaultdict

from .task_scheduler import TaskScheduler, ScheduledTask, TaskStatus, TaskPriority, TaskResult
from ..utils import get_logger, now, ValidationError, ResourceError, ConfigError


class JobStatus(Enum):
    """作业状态枚举"""
    CREATED = "created"          # 已创建
    QUEUED = "queued"            # 已排队
    RUNNING = "running"          # 运行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消
    PAUSED = "paused"            # 已暂停
    RETRYING = "retrying"        # 重试中


class JobType(Enum):
    """作业类型枚举"""
    REALTIME_SYNC = "realtime_sync"      # 实时同步
    HISTORICAL_SYNC = "historical_sync"  # 历史同步
    INCREMENTAL_SYNC = "incremental_sync" # 增量同步
    DATA_CLEANUP = "data_cleanup"        # 数据清理
    SYSTEM_MAINTENANCE = "system_maintenance" # 系统维护
    CUSTOM = "custom"                    # 自定义


@dataclass
class JobConfig:
    """作业配置"""
    max_retries: int = 3
    retry_delay: float = 60.0
    timeout: Optional[float] = None
    priority: TaskPriority = TaskPriority.NORMAL
    
    # 资源限制
    max_memory_mb: Optional[int] = None
    max_cpu_percent: Optional[float] = None
    
    # 通知配置
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_emails: List[str] = field(default_factory=list)
    
    # 持久化配置
    persist_result: bool = True
    result_ttl_hours: int = 24


@dataclass
class Job:
    """作业定义"""
    job_id: str
    name: str
    job_type: JobType
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    
    # 调度配置
    schedule_config: dict = field(default_factory=dict)
    config: JobConfig = field(default_factory=JobConfig)
    
    # 状态信息
    status: JobStatus = JobStatus.CREATED
    created_time: datetime = field(default_factory=now)
    started_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    
    # 执行信息
    task_ids: List[str] = field(default_factory=list)  # 关联的任务ID
    results: List[TaskResult] = field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # 分组和标签
    group: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    
    # 依赖关系
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    # 其他属性
    description: str = ""
    metadata: dict = field(default_factory=dict)
    
    def add_result(self, result: TaskResult):
        """添加任务结果"""
        self.results.append(result)
        
        # 更新作业状态
        if result.status == TaskStatus.COMPLETED:
            if all(r.status == TaskStatus.COMPLETED for r in self.results):
                self.status = JobStatus.COMPLETED
                self.completed_time = now()
        elif result.status == TaskStatus.FAILED:
            self.status = JobStatus.FAILED
            self.error_message = str(result.error) if result.error else "Unknown error"
    
    def get_duration(self) -> Optional[float]:
        """获取作业执行时长"""
        if self.started_time and self.completed_time:
            return (self.completed_time - self.started_time).total_seconds()
        return None
    
    def is_finished(self) -> bool:
        """判断作业是否已结束"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]


class JobQueue:
    """作业队列"""
    
    def __init__(self, name: str, max_size: int = 1000):
        self.name = name
        self.max_size = max_size
        self.jobs: List[Job] = []
        self.lock = threading.RLock()
    
    def enqueue(self, job: Job) -> bool:
        """入队"""
        with self.lock:
            if len(self.jobs) >= self.max_size:
                return False
            
            self.jobs.append(job)
            job.status = JobStatus.QUEUED
            return True
    
    def dequeue(self) -> Optional[Job]:
        """出队"""
        with self.lock:
            if not self.jobs:
                return None
            
            # 按优先级排序
            self.jobs.sort(key=lambda j: j.config.priority.value, reverse=True)
            return self.jobs.pop(0)
    
    def peek(self) -> Optional[Job]:
        """查看队首"""
        with self.lock:
            return self.jobs[0] if self.jobs else None
    
    def size(self) -> int:
        """队列大小"""
        with self.lock:
            return len(self.jobs)
    
    def clear(self):
        """清空队列"""
        with self.lock:
            self.jobs.clear()


class JobManager:
    """作业管理器"""
    
    def __init__(self, scheduler: Optional[TaskScheduler] = None, 
                 persistence_dir: Optional[str] = None,
                 logger_name: str = "JobManager"):
        self.scheduler = scheduler or TaskScheduler()
        self.logger = get_logger(logger_name)
        
        # 作业存储
        self.jobs: Dict[str, Job] = {}
        self.job_groups: Dict[str, List[str]] = defaultdict(list)
        
        # 作业队列
        self.queues: Dict[str, JobQueue] = {
            'default': JobQueue('default'),
            'high_priority': JobQueue('high_priority'),
            'low_priority': JobQueue('low_priority')
        }
        
        # 持久化配置
        self.persistence_dir = Path(persistence_dir) if persistence_dir else None
        if self.persistence_dir:
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        # 状态管理
        self.is_running = False
        self.processor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 统计信息
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'cancelled_jobs': 0,
            'average_execution_time': 0.0
        }
        
        self.logger.info("JobManager initialized")
    
    def create_job(self, name: str, job_type: JobType, func: Callable,
                  args: tuple = (), kwargs: dict = None,
                  config: Optional[JobConfig] = None,
                  schedule_config: dict = None,
                  group: Optional[str] = None,
                  tags: Set[str] = None,
                  dependencies: List[str] = None) -> str:
        """创建作业"""
        job_id = f"{job_type.value}_{int(now().timestamp())}_{len(self.jobs)}"
        
        job = Job(
            job_id=job_id,
            name=name,
            job_type=job_type,
            func=func,
            args=args,
            kwargs=kwargs or {},
            config=config or JobConfig(),
            schedule_config=schedule_config or {},
            group=group,
            tags=tags or set(),
            dependencies=dependencies or []
        )
        
        self.jobs[job_id] = job
        self.stats['total_jobs'] += 1
        
        # 添加到分组
        if group:
            self.job_groups[group].append(job_id)
        
        # 持久化
        if self.persistence_dir:
            self._persist_job(job)
        
        self.logger.info(f"Created job: {name} ({job_id})")
        return job_id
    
    def submit_job(self, job_id: str, queue_name: str = 'default') -> bool:
        """提交作业到队列"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status != JobStatus.CREATED:
            return False
        
        # 检查依赖关系
        if not self._check_job_dependencies(job):
            self.logger.warning(f"Job dependencies not satisfied: {job_id}")
            return False
        
        queue = self.queues.get(queue_name)
        if not queue:
            return False
        
        if queue.enqueue(job):
            self.logger.info(f"Submitted job to queue '{queue_name}': {job.name} ({job_id})")
            return True
        
        return False
    
    def cancel_job(self, job_id: str) -> bool:
        """取消作业"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        # 取消关联的任务
        for task_id in job.task_ids:
            self.scheduler.cancel_task(task_id)
        
        job.status = JobStatus.CANCELLED
        self.stats['cancelled_jobs'] += 1
        
        self.logger.info(f"Cancelled job: {job.name} ({job_id})")
        return True
    
    def pause_job(self, job_id: str) -> bool:
        """暂停作业"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status == JobStatus.RUNNING:
            # 暂停关联的任务
            for task_id in job.task_ids:
                self.scheduler.pause_task(task_id)
            
            job.status = JobStatus.PAUSED
            self.logger.info(f"Paused job: {job.name} ({job_id})")
            return True
        
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """恢复作业"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status == JobStatus.PAUSED:
            # 恢复关联的任务
            for task_id in job.task_ids:
                self.scheduler.resume_task(task_id)
            
            job.status = JobStatus.RUNNING
            self.logger.info(f"Resumed job: {job.name} ({job_id})")
            return True
        
        return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """获取作业"""
        return self.jobs.get(job_id)
    
    def list_jobs(self, status: Optional[JobStatus] = None,
                 job_type: Optional[JobType] = None,
                 group: Optional[str] = None,
                 tags: Optional[Set[str]] = None) -> List[Job]:
        """列出作业"""
        jobs = list(self.jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        
        if group:
            jobs = [j for j in jobs if j.group == group]
        
        if tags:
            jobs = [j for j in jobs if tags.intersection(j.tags)]
        
        return jobs
    
    def get_job_groups(self) -> Dict[str, List[str]]:
        """获取作业分组"""
        return dict(self.job_groups)
    
    def start(self):
        """启动作业管理器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # 启动调度器
        self.scheduler.start()
        
        # 启动作业处理线程
        self.processor_thread = threading.Thread(target=self._job_processor_loop, daemon=True)
        self.processor_thread.start()
        
        self.logger.info("JobManager started")
    
    def stop(self, wait_for_completion: bool = True):
        """停止作业管理器"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping JobManager...")
        self.is_running = False
        self.stop_event.set()
        
        # 停止作业处理线程
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=5.0)
        
        # 停止调度器
        self.scheduler.stop(wait_for_completion)
        
        self.logger.info("JobManager stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        running_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
        queued_jobs = sum(q.size() for q in self.queues.values())
        
        stats = self.stats.copy()
        stats.update({
            'running_jobs': running_jobs,
            'queued_jobs': queued_jobs,
            'total_registered_jobs': len(self.jobs),
            'job_groups': len(self.job_groups),
            'scheduler_stats': self.scheduler.get_stats()
        })
        
        return stats
    
    def cleanup_finished_jobs(self, older_than_hours: int = 24):
        """清理已完成的作业"""
        cutoff_time = now() - timedelta(hours=older_than_hours)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if (job.is_finished() and 
                job.completed_time and 
                job.completed_time < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            self._remove_job(job_id)
        
        self.logger.info(f"Cleaned up {len(jobs_to_remove)} finished jobs")
    
    def _check_job_dependencies(self, job: Job) -> bool:
        """检查作业依赖关系"""
        for dep_id in job.dependencies:
            dep_job = self.jobs.get(dep_id)
            if not dep_job or dep_job.status != JobStatus.COMPLETED:
                return False
        return True
    
    def _job_processor_loop(self):
        """作业处理循环"""
        self.logger.info("Job processor loop started")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 处理各个队列中的作业
                for queue_name in ['high_priority', 'default', 'low_priority']:
                    queue = self.queues[queue_name]
                    job = queue.dequeue()
                    
                    if job:
                        self._process_job(job)
                        break  # 一次只处理一个作业
                
                # 短暂休眠
                self.stop_event.wait(1.0)
                
            except Exception as e:
                self.logger.error(f"Error in job processor loop: {e}", exc_info=True)
                self.stop_event.wait(5.0)
        
        self.logger.info("Job processor loop ended")
    
    def _process_job(self, job: Job):
        """处理作业"""
        try:
            self.logger.info(f"Processing job: {job.name} ({job.job_id})")
            
            job.status = JobStatus.RUNNING
            job.started_time = now()
            
            # 创建调度任务
            task = ScheduledTask(
                task_id=f"job_{job.job_id}_task",
                name=f"{job.name}_task",
                func=job.func,
                args=job.args,
                kwargs=job.kwargs,
                priority=job.config.priority,
                max_retries=job.config.max_retries,
                retry_delay=job.config.retry_delay,
                timeout=job.config.timeout
            )
            
            # 添加任务到调度器
            task_id = self.scheduler.add_task(task)
            job.task_ids.append(task_id)
            
            # 立即执行任务
            result = self.scheduler.run_task_once(task_id)
            if result:
                job.add_result(result)
            
            # 更新统计信息
            if job.status == JobStatus.COMPLETED:
                self.stats['completed_jobs'] += 1
                duration = job.get_duration()
                if duration:
                    total_time = self.stats.get('total_execution_time', 0) + duration
                    self.stats['total_execution_time'] = total_time
                    self.stats['average_execution_time'] = (
                        total_time / self.stats['completed_jobs']
                    )
            elif job.status == JobStatus.FAILED:
                self.stats['failed_jobs'] += 1
            
            # 持久化结果
            if self.persistence_dir and job.config.persist_result:
                self._persist_job_result(job)
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self.stats['failed_jobs'] += 1
            self.logger.error(f"Failed to process job {job.job_id}: {e}", exc_info=True)
    
    def _persist_job(self, job: Job):
        """持久化作业"""
        if not self.persistence_dir:
            return
        
        try:
            job_file = self.persistence_dir / f"job_{job.job_id}.json"
            job_data = asdict(job)
            
            # 处理不能序列化的字段
            job_data['func'] = job.func.__name__ if hasattr(job.func, '__name__') else str(job.func)
            job_data['created_time'] = job.created_time.isoformat()
            job_data['started_time'] = job.started_time.isoformat() if job.started_time else None
            job_data['completed_time'] = job.completed_time.isoformat() if job.completed_time else None
            job_data['tags'] = list(job.tags)
            
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to persist job {job.job_id}: {e}")
    
    def _persist_job_result(self, job: Job):
        """持久化作业结果"""
        if not self.persistence_dir:
            return
        
        try:
            result_file = self.persistence_dir / f"result_{job.job_id}.pkl"
            with open(result_file, 'wb') as f:
                pickle.dump(job.results, f)
                
        except Exception as e:
            self.logger.error(f"Failed to persist job result {job.job_id}: {e}")
    
    def _remove_job(self, job_id: str):
        """移除作业"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            
            # 从分组中移除
            if job.group and job_id in self.job_groups[job.group]:
                self.job_groups[job.group].remove(job_id)
                if not self.job_groups[job.group]:
                    del self.job_groups[job.group]
            
            # 删除持久化文件
            if self.persistence_dir:
                job_file = self.persistence_dir / f"job_{job_id}.json"
                result_file = self.persistence_dir / f"result_{job_id}.pkl"
                
                for file_path in [job_file, result_file]:
                    if file_path.exists():
                        try:
                            file_path.unlink()
                        except Exception as e:
                            self.logger.error(f"Failed to delete file {file_path}: {e}")
            
            del self.jobs[job_id]
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()