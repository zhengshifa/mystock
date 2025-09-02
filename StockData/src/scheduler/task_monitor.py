#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务监控器模块

提供任务监控和告警功能:
- 任务执行监控
- 性能指标收集
- 异常检测和告警
- 健康状态检查
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

from .task_scheduler import TaskScheduler, TaskStatus
from .job_manager import JobManager, JobStatus
from .cron_scheduler import CronScheduler
from ..utils import get_logger, now, ValidationError


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"          # 计数器
    GAUGE = "gauge"              # 仪表盘
    HISTOGRAM = "histogram"      # 直方图
    TIMER = "timer"              # 计时器


@dataclass
class TaskMetrics:
    """任务指标"""
    task_id: str
    task_name: str
    
    # 执行统计
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    
    # 时间统计
    total_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    
    # 最近执行时间（保留最近100次）
    recent_execution_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # 错误统计
    error_count_by_type: Dict[str, int] = field(default_factory=dict)
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    # 状态统计
    last_execution_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    
    def update_execution(self, duration: float, success: bool, 
                       error: Optional[str] = None):
        """更新执行统计"""
        self.total_executions += 1
        self.last_execution_time = now()
        
        if success:
            self.successful_executions += 1
            self.last_success_time = now()
            self.consecutive_failures = 0
        else:
            self.failed_executions += 1
            self.consecutive_failures += 1
            
            if error:
                self.last_error = error
                self.last_error_time = now()
                error_type = type(error).__name__ if isinstance(error, Exception) else str(error)
                self.error_count_by_type[error_type] = self.error_count_by_type.get(error_type, 0) + 1
        
        # 更新时间统计
        self.total_execution_time += duration
        self.min_execution_time = min(self.min_execution_time, duration)
        self.max_execution_time = max(self.max_execution_time, duration)
        
        if self.total_executions > 0:
            self.avg_execution_time = self.total_execution_time / self.total_executions
        
        self.recent_execution_times.append(duration)
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    def get_recent_avg_time(self) -> float:
        """获取最近平均执行时间"""
        if not self.recent_execution_times:
            return 0.0
        return statistics.mean(self.recent_execution_times)
    
    def get_p95_execution_time(self) -> float:
        """获取P95执行时间"""
        if not self.recent_execution_times:
            return 0.0
        sorted_times = sorted(self.recent_execution_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]


@dataclass
class Alert:
    """告警信息"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    source: str  # 告警源（task_id, job_id等）
    
    created_time: datetime = field(default_factory=now)
    acknowledged: bool = False
    acknowledged_time: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    # 告警规则信息
    rule_name: Optional[str] = None
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    
    # 附加信息
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def acknowledge(self, acknowledged_by: str = "system"):
        """确认告警"""
        self.acknowledged = True
        self.acknowledged_time = now()
        self.acknowledged_by = acknowledged_by


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    
    # 条件
    metric_name: str
    operator: str  # >, <, >=, <=, ==, !=
    threshold: float
    
    # 告警配置
    level: AlertLevel
    enabled: bool = True
    
    # 抑制配置
    cooldown_minutes: int = 5  # 冷却时间
    max_alerts_per_hour: int = 10
    
    # 状态
    last_triggered_time: Optional[datetime] = None
    trigger_count: int = 0
    
    def should_trigger(self, value: float) -> bool:
        """判断是否应该触发告警"""
        if not self.enabled:
            return False
        
        # 检查冷却时间
        if (self.last_triggered_time and 
            now() - self.last_triggered_time < timedelta(minutes=self.cooldown_minutes)):
            return False
        
        # 检查频率限制
        if (self.last_triggered_time and 
            now() - self.last_triggered_time < timedelta(hours=1) and
            self.trigger_count >= self.max_alerts_per_hour):
            return False
        
        # 检查条件
        if self.operator == ">":
            return value > self.threshold
        elif self.operator == "<":
            return value < self.threshold
        elif self.operator == ">=":
            return value >= self.threshold
        elif self.operator == "<=":
            return value <= self.threshold
        elif self.operator == "==":
            return value == self.threshold
        elif self.operator == "!=":
            return value != self.threshold
        
        return False
    
    def trigger(self):
        """触发告警"""
        self.last_triggered_time = now()
        self.trigger_count += 1


class TaskMonitor:
    """任务监控器"""
    
    def __init__(self, task_scheduler: Optional[TaskScheduler] = None,
                 job_manager: Optional[JobManager] = None,
                 cron_scheduler: Optional[CronScheduler] = None,
                 logger_name: str = "TaskMonitor"):
        self.task_scheduler = task_scheduler
        self.job_manager = job_manager
        self.cron_scheduler = cron_scheduler
        self.logger = get_logger(logger_name)
        
        # 监控数据
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.system_metrics: Dict[str, Any] = {}
        
        # 告警系统
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        
        # 监控状态
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 配置
        self.monitor_interval = 30.0  # 监控间隔（秒）
        self.metrics_retention_hours = 24  # 指标保留时间
        
        # 健康检查
        self.health_checks: Dict[str, Callable[[], bool]] = {}
        self.health_status = HealthStatus.HEALTHY
        
        self._setup_default_alert_rules()
        self.logger.info("TaskMonitor initialized")
    
    def start(self):
        """启动监控器"""
        if self.is_running:
            self.logger.warning("TaskMonitor is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("TaskMonitor started")
    
    def stop(self):
        """停止监控器"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping TaskMonitor...")
        self.is_running = False
        self.stop_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        self.logger.info("TaskMonitor stopped")
    
    def record_task_execution(self, task_id: str, task_name: str,
                            duration: float, success: bool,
                            error: Optional[str] = None):
        """记录任务执行"""
        if task_id not in self.task_metrics:
            self.task_metrics[task_id] = TaskMetrics(task_id, task_name)
        
        metrics = self.task_metrics[task_id]
        metrics.update_execution(duration, success, error)
        
        # 检查告警规则
        self._check_task_alerts(task_id, metrics)
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"Added alert rule: {rule.name} ({rule.rule_id})")
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """移除告警规则"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            self.logger.info(f"Removed alert rule: {rule_id}")
            return True
        return False
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self.alert_handlers.append(handler)
    
    def create_alert(self, level: AlertLevel, title: str, message: str,
                    source: str, rule_name: Optional[str] = None,
                    threshold_value: Optional[float] = None,
                    actual_value: Optional[float] = None,
                    tags: Set[str] = None,
                    metadata: Dict[str, Any] = None) -> str:
        """创建告警"""
        alert_id = f"alert_{int(now().timestamp())}_{len(self.alerts)}"
        
        alert = Alert(
            alert_id=alert_id,
            level=level,
            title=title,
            message=message,
            source=source,
            rule_name=rule_name,
            threshold_value=threshold_value,
            actual_value=actual_value,
            tags=tags or set(),
            metadata=metadata or {}
        )
        
        self.alerts[alert_id] = alert
        
        # 调用告警处理器
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}", exc_info=True)
        
        self.logger.warning(f"Alert created: {title} ({level.value}) - {message}")
        return alert_id
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """确认告警"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.acknowledge(acknowledged_by)
            self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            return True
        return False
    
    def get_alerts(self, level: Optional[AlertLevel] = None,
                  acknowledged: Optional[bool] = None,
                  source: Optional[str] = None) -> List[Alert]:
        """获取告警列表"""
        alerts = list(self.alerts.values())
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        return sorted(alerts, key=lambda a: a.created_time, reverse=True)
    
    def get_task_metrics(self, task_id: Optional[str] = None) -> Dict[str, TaskMetrics]:
        """获取任务指标"""
        if task_id:
            return {task_id: self.task_metrics.get(task_id)} if task_id in self.task_metrics else {}
        return self.task_metrics.copy()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        return self.system_metrics.copy()
    
    def add_health_check(self, name: str, check_func: Callable[[], bool]):
        """添加健康检查"""
        self.health_checks[name] = check_func
        self.logger.info(f"Added health check: {name}")
    
    def get_health_status(self) -> HealthStatus:
        """获取健康状态"""
        return self.health_status
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        report = {
            'overall_status': self.health_status.value,
            'timestamp': now(),
            'checks': {}
        }
        
        for name, check_func in self.health_checks.items():
            try:
                result = check_func()
                report['checks'][name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'success': result
                }
            except Exception as e:
                report['checks'][name] = {
                    'status': 'error',
                    'success': False,
                    'error': str(e)
                }
        
        return report
    
    def _monitor_loop(self):
        """监控主循环"""
        self.logger.info("Monitor loop started")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # 收集系统指标
                self._collect_system_metrics()
                
                # 执行健康检查
                self._perform_health_checks()
                
                # 检查告警规则
                self._check_system_alerts()
                
                # 清理过期数据
                self._cleanup_old_data()
                
                # 等待下次监控
                self.stop_event.wait(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}", exc_info=True)
                self.stop_event.wait(60.0)  # 出错时等待更长时间
        
        self.logger.info("Monitor loop ended")
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            metrics = {
                'timestamp': now(),
                'monitor_running': self.is_running
            }
            
            # 任务调度器指标
            if self.task_scheduler:
                scheduler_stats = self.task_scheduler.get_stats()
                metrics['scheduler'] = scheduler_stats
            
            # 作业管理器指标
            if self.job_manager:
                job_stats = self.job_manager.get_stats()
                metrics['job_manager'] = job_stats
            
            # Cron调度器指标
            if self.cron_scheduler:
                cron_stats = self.cron_scheduler.get_stats()
                metrics['cron_scheduler'] = cron_stats
            
            # 告警统计
            alert_stats = {
                'total_alerts': len(self.alerts),
                'unacknowledged_alerts': len([a for a in self.alerts.values() if not a.acknowledged]),
                'critical_alerts': len([a for a in self.alerts.values() if a.level == AlertLevel.CRITICAL]),
                'error_alerts': len([a for a in self.alerts.values() if a.level == AlertLevel.ERROR])
            }
            metrics['alerts'] = alert_stats
            
            # 任务指标统计
            task_stats = {
                'total_tasks': len(self.task_metrics),
                'total_executions': sum(m.total_executions for m in self.task_metrics.values()),
                'successful_executions': sum(m.successful_executions for m in self.task_metrics.values()),
                'failed_executions': sum(m.failed_executions for m in self.task_metrics.values()),
                'average_success_rate': statistics.mean([m.get_success_rate() for m in self.task_metrics.values()]) if self.task_metrics else 0.0
            }
            metrics['tasks'] = task_stats
            
            self.system_metrics = metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}", exc_info=True)
    
    def _perform_health_checks(self):
        """执行健康检查"""
        try:
            failed_checks = 0
            total_checks = len(self.health_checks)
            
            for name, check_func in self.health_checks.items():
                try:
                    if not check_func():
                        failed_checks += 1
                        self.logger.warning(f"Health check failed: {name}")
                except Exception as e:
                    failed_checks += 1
                    self.logger.error(f"Health check error: {name} - {e}")
            
            # 更新健康状态
            if total_checks == 0:
                self.health_status = HealthStatus.HEALTHY
            elif failed_checks == 0:
                self.health_status = HealthStatus.HEALTHY
            elif failed_checks / total_checks < 0.3:
                self.health_status = HealthStatus.WARNING
            elif failed_checks / total_checks < 0.7:
                self.health_status = HealthStatus.UNHEALTHY
            else:
                self.health_status = HealthStatus.CRITICAL
            
        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}", exc_info=True)
            self.health_status = HealthStatus.CRITICAL
    
    def _check_task_alerts(self, task_id: str, metrics: TaskMetrics):
        """检查任务告警"""
        # 检查连续失败
        if metrics.consecutive_failures >= 3:
            self.create_alert(
                level=AlertLevel.ERROR,
                title=f"Task Consecutive Failures",
                message=f"Task {metrics.task_name} has failed {metrics.consecutive_failures} times consecutively",
                source=task_id,
                actual_value=float(metrics.consecutive_failures)
            )
        
        # 检查成功率
        success_rate = metrics.get_success_rate()
        if metrics.total_executions >= 10 and success_rate < 0.8:
            self.create_alert(
                level=AlertLevel.WARNING,
                title=f"Low Task Success Rate",
                message=f"Task {metrics.task_name} success rate is {success_rate:.2%}",
                source=task_id,
                actual_value=success_rate
            )
        
        # 检查执行时间异常
        if len(metrics.recent_execution_times) >= 10:
            recent_avg = metrics.get_recent_avg_time()
            if recent_avg > metrics.avg_execution_time * 2:
                self.create_alert(
                    level=AlertLevel.WARNING,
                    title=f"Task Execution Time Anomaly",
                    message=f"Task {metrics.task_name} recent avg time ({recent_avg:.2f}s) is much higher than historical avg ({metrics.avg_execution_time:.2f}s)",
                    source=task_id,
                    actual_value=recent_avg
                )
    
    def _check_system_alerts(self):
        """检查系统告警"""
        for rule_id, rule in self.alert_rules.items():
            try:
                # 获取指标值
                value = self._get_metric_value(rule.metric_name)
                if value is not None and rule.should_trigger(value):
                    self.create_alert(
                        level=rule.level,
                        title=rule.name,
                        message=rule.description,
                        source="system",
                        rule_name=rule.name,
                        threshold_value=rule.threshold,
                        actual_value=value
                    )
                    rule.trigger()
            except Exception as e:
                self.logger.error(f"Error checking alert rule {rule_id}: {e}")
    
    def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """获取指标值"""
        try:
            # 解析指标路径，如 "scheduler.running_tasks"
            parts = metric_name.split('.')
            value = self.system_metrics
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            
            return float(value) if isinstance(value, (int, float)) else None
        except Exception:
            return None
    
    def _cleanup_old_data(self):
        """清理过期数据"""
        try:
            cutoff_time = now() - timedelta(hours=self.metrics_retention_hours)
            
            # 清理过期告警
            expired_alerts = [
                alert_id for alert_id, alert in self.alerts.items()
                if alert.acknowledged and alert.acknowledged_time and alert.acknowledged_time < cutoff_time
            ]
            
            for alert_id in expired_alerts:
                del self.alerts[alert_id]
            
            if expired_alerts:
                self.logger.info(f"Cleaned up {len(expired_alerts)} expired alerts")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}", exc_info=True)
    
    def _setup_default_alert_rules(self):
        """设置默认告警规则"""
        # 系统负载告警
        self.add_alert_rule(AlertRule(
            rule_id="high_running_tasks",
            name="High Running Tasks",
            description="Too many tasks are running simultaneously",
            metric_name="scheduler.running_tasks",
            operator=">",
            threshold=50.0,
            level=AlertLevel.WARNING
        ))
        
        # 失败任务告警
        self.add_alert_rule(AlertRule(
            rule_id="high_failed_tasks",
            name="High Failed Tasks",
            description="High number of failed tasks",
            metric_name="scheduler.failed_tasks",
            operator=">",
            threshold=10.0,
            level=AlertLevel.ERROR
        ))
        
        # 未确认告警数量
        self.add_alert_rule(AlertRule(
            rule_id="too_many_unacknowledged_alerts",
            name="Too Many Unacknowledged Alerts",
            description="Too many unacknowledged alerts",
            metric_name="alerts.unacknowledged_alerts",
            operator=">",
            threshold=20.0,
            level=AlertLevel.WARNING
        ))
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# 默认告警处理器
def console_alert_handler(alert: Alert):
    """控制台告警处理器"""
    print(f"[{alert.level.value.upper()}] {alert.title}: {alert.message}")


def log_alert_handler(alert: Alert):
    """日志告警处理器"""
    logger = get_logger("AlertHandler")
    
    if alert.level == AlertLevel.CRITICAL:
        logger.critical(f"{alert.title}: {alert.message}")
    elif alert.level == AlertLevel.ERROR:
        logger.error(f"{alert.title}: {alert.message}")
    elif alert.level == AlertLevel.WARNING:
        logger.warning(f"{alert.title}: {alert.message}")
    else:
        logger.info(f"{alert.title}: {alert.message}")