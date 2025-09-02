#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步监控器

负责监控和管理所有同步任务的状态和性能，包括:
- 同步任务状态监控
- 性能指标收集
- 异常检测和告警
- 健康检查
- 监控数据可视化
- 自动恢复机制
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from loguru import logger
import time
from enum import Enum
from dataclasses import dataclass, asdict
import json
from collections import deque, defaultdict

from ..utils.exceptions import SyncError


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


@dataclass
class SyncMetrics:
    """同步指标数据类"""
    timestamp: str
    sync_type: str
    status: str
    duration: float
    records_processed: int
    success_rate: float
    error_count: int
    memory_usage: float
    cpu_usage: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Alert:
    """告警数据类"""
    id: str
    timestamp: str
    level: AlertLevel
    title: str
    message: str
    source: str
    resolved: bool = False
    resolved_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SyncMonitor:
    """同步监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 监控配置
        self.monitor_config = config.get('monitor', {
            'metrics_retention_hours': 24,     # 指标保留时间(小时)
            'alert_retention_hours': 168,     # 告警保留时间(小时)
            'health_check_interval': 60,      # 健康检查间隔(秒)
            'metrics_collection_interval': 30, # 指标收集间隔(秒)
            'performance_threshold': {        # 性能阈值
                'max_sync_duration': 300,     # 最大同步时长(秒)
                'min_success_rate': 0.95,     # 最小成功率
                'max_error_rate': 0.05,       # 最大错误率
                'max_memory_usage': 1024,     # 最大内存使用(MB)
                'max_cpu_usage': 80           # 最大CPU使用率(%)
            }
        })
        
        # 监控状态
        self.is_running = False
        self.start_time = None
        
        # 数据存储
        self.metrics_history = deque(maxlen=1000)  # 指标历史
        self.alerts = deque(maxlen=500)            # 告警历史
        self.health_status = HealthStatus.HEALTHY
        
        # 统计数据
        self.sync_stats = defaultdict(lambda: {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_duration': 0,
            'total_records': 0,
            'last_run_time': None,
            'last_success_time': None,
            'last_error_time': None,
            'consecutive_failures': 0
        })
        
        # 监控任务
        self._monitor_tasks = []
        self._alert_callbacks = []  # 告警回调函数
        
        # 性能阈值
        self.thresholds = self.monitor_config['performance_threshold']
        
        logger.info("同步监控器初始化完成")
    
    async def start(self) -> bool:
        """启动监控器"""
        try:
            if self.is_running:
                logger.warning("同步监控器已在运行")
                return True
            
            logger.info("启动同步监控器...")
            
            self.is_running = True
            self.start_time = datetime.now()
            
            # 启动监控任务
            self._monitor_tasks = [
                asyncio.create_task(self._health_check_loop()),
                asyncio.create_task(self._metrics_cleanup_loop()),
                asyncio.create_task(self._alert_cleanup_loop())
            ]
            
            logger.info("同步监控器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动同步监控器失败: {e}")
            self.is_running = False
            return False
    
    async def stop(self):
        """停止监控器"""
        try:
            if not self.is_running:
                logger.warning("同步监控器未运行")
                return
            
            logger.info("停止同步监控器...")
            
            self.is_running = False
            
            # 停止监控任务
            for task in self._monitor_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self._monitor_tasks.clear()
            
            logger.info("同步监控器已停止")
            
        except Exception as e:
            logger.error(f"停止同步监控器失败: {e}")
    
    def record_sync_start(self, sync_type: str, sync_id: str) -> str:
        """记录同步开始"""
        try:
            timestamp = datetime.now().isoformat()
            
            # 更新统计
            self.sync_stats[sync_type]['total_runs'] += 1
            self.sync_stats[sync_type]['last_run_time'] = timestamp
            
            logger.debug(f"记录同步开始: {sync_type} - {sync_id}")
            return timestamp
            
        except Exception as e:
            logger.error(f"记录同步开始失败: {e}")
            return datetime.now().isoformat()
    
    def record_sync_end(self, sync_type: str, sync_id: str, start_time: str,
                       success: bool, records_processed: int = 0,
                       error_message: str = None) -> SyncMetrics:
        """记录同步结束"""
        try:
            end_time = datetime.now()
            start_dt = datetime.fromisoformat(start_time)
            duration = (end_time - start_dt).total_seconds()
            
            # 创建指标
            metrics = SyncMetrics(
                timestamp=end_time.isoformat(),
                sync_type=sync_type,
                status="success" if success else "failed",
                duration=duration,
                records_processed=records_processed,
                success_rate=self._calculate_success_rate(sync_type),
                error_count=self.sync_stats[sync_type]['failed_runs'],
                memory_usage=self._get_memory_usage(),
                cpu_usage=self._get_cpu_usage()
            )
            
            # 添加到历史记录
            self.metrics_history.append(metrics)
            
            # 更新统计
            stats = self.sync_stats[sync_type]
            stats['total_duration'] += duration
            stats['total_records'] += records_processed
            
            if success:
                stats['successful_runs'] += 1
                stats['last_success_time'] = end_time.isoformat()
                stats['consecutive_failures'] = 0
            else:
                stats['failed_runs'] += 1
                stats['last_error_time'] = end_time.isoformat()
                stats['consecutive_failures'] += 1
                
                # 生成错误告警
                if error_message:
                    self._create_alert(
                        AlertLevel.ERROR,
                        f"{sync_type} 同步失败",
                        f"同步失败: {error_message}",
                        sync_type
                    )
            
            # 检查性能阈值
            self._check_performance_thresholds(metrics)
            
            logger.debug(f"记录同步结束: {sync_type} - {sync_id}, 成功: {success}, 耗时: {duration:.2f}s")
            return metrics
            
        except Exception as e:
            logger.error(f"记录同步结束失败: {e}")
            return None
    
    def record_custom_metric(self, sync_type: str, metric_name: str, value: Any):
        """记录自定义指标"""
        try:
            timestamp = datetime.now().isoformat()
            
            # 创建自定义指标
            custom_metric = {
                'timestamp': timestamp,
                'sync_type': sync_type,
                'metric_name': metric_name,
                'value': value
            }
            
            # 可以扩展存储自定义指标的逻辑
            logger.debug(f"记录自定义指标: {sync_type}.{metric_name} = {value}")
            
        except Exception as e:
            logger.error(f"记录自定义指标失败: {e}")
    
    def _calculate_success_rate(self, sync_type: str) -> float:
        """计算成功率"""
        try:
            stats = self.sync_stats[sync_type]
            total = stats['total_runs']
            successful = stats['successful_runs']
            
            if total == 0:
                return 1.0
            
            return successful / total
            
        except Exception as e:
            logger.error(f"计算成功率失败: {e}")
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量(MB)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
        except Exception as e:
            logger.error(f"获取内存使用量失败: {e}")
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """获取CPU使用率(%)"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0
        except Exception as e:
            logger.error(f"获取CPU使用率失败: {e}")
            return 0.0
    
    def _check_performance_thresholds(self, metrics: SyncMetrics):
        """检查性能阈值"""
        try:
            # 检查同步时长
            if metrics.duration > self.thresholds['max_sync_duration']:
                self._create_alert(
                    AlertLevel.WARNING,
                    "同步时长过长",
                    f"{metrics.sync_type} 同步耗时 {metrics.duration:.2f}s，超过阈值 {self.thresholds['max_sync_duration']}s",
                    metrics.sync_type
                )
            
            # 检查成功率
            if metrics.success_rate < self.thresholds['min_success_rate']:
                self._create_alert(
                    AlertLevel.WARNING,
                    "同步成功率过低",
                    f"{metrics.sync_type} 成功率 {metrics.success_rate:.2%}，低于阈值 {self.thresholds['min_success_rate']:.2%}",
                    metrics.sync_type
                )
            
            # 检查内存使用
            if metrics.memory_usage > self.thresholds['max_memory_usage']:
                self._create_alert(
                    AlertLevel.WARNING,
                    "内存使用过高",
                    f"内存使用 {metrics.memory_usage:.2f}MB，超过阈值 {self.thresholds['max_memory_usage']}MB",
                    "system"
                )
            
            # 检查CPU使用率
            if metrics.cpu_usage > self.thresholds['max_cpu_usage']:
                self._create_alert(
                    AlertLevel.WARNING,
                    "CPU使用率过高",
                    f"CPU使用率 {metrics.cpu_usage:.1f}%，超过阈值 {self.thresholds['max_cpu_usage']}%",
                    "system"
                )
            
        except Exception as e:
            logger.error(f"检查性能阈值失败: {e}")
    
    def _create_alert(self, level: AlertLevel, title: str, message: str, source: str) -> Alert:
        """创建告警"""
        try:
            alert = Alert(
                id=f"{source}_{int(time.time() * 1000)}",
                timestamp=datetime.now().isoformat(),
                level=level,
                title=title,
                message=message,
                source=source
            )
            
            self.alerts.append(alert)
            
            # 触发告警回调
            for callback in self._alert_callbacks:
                try:
                    asyncio.create_task(callback(alert))
                except Exception as e:
                    logger.error(f"告警回调执行失败: {e}")
            
            logger.warning(f"[{level.value.upper()}] {title}: {message}")
            return alert
            
        except Exception as e:
            logger.error(f"创建告警失败: {e}")
            return None
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调函数"""
        self._alert_callbacks.append(callback)
        logger.info(f"添加告警回调函数: {callback.__name__}")
    
    def remove_alert_callback(self, callback: Callable[[Alert], None]):
        """移除告警回调函数"""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)
            logger.info(f"移除告警回调函数: {callback.__name__}")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        try:
            interval = self.monitor_config.get('health_check_interval', 60)
            logger.info(f"健康检查循环启动，检查间隔: {interval}秒")
            
            while self.is_running:
                try:
                    await self._perform_health_check()
                    await asyncio.sleep(interval)
                    
                except asyncio.CancelledError:
                    logger.info("健康检查循环被取消")
                    break
                except Exception as e:
                    logger.error(f"健康检查循环异常: {e}")
                    await asyncio.sleep(interval)
                    
        except Exception as e:
            logger.error(f"健康检查循环严重异常: {e}")
    
    async def _perform_health_check(self):
        """执行健康检查"""
        try:
            current_status = self.health_status
            new_status = HealthStatus.HEALTHY
            
            # 检查各种健康指标
            issues = []
            
            # 检查连续失败次数
            for sync_type, stats in self.sync_stats.items():
                consecutive_failures = stats['consecutive_failures']
                if consecutive_failures >= 5:
                    issues.append(f"{sync_type} 连续失败 {consecutive_failures} 次")
                    new_status = HealthStatus.CRITICAL
                elif consecutive_failures >= 3:
                    issues.append(f"{sync_type} 连续失败 {consecutive_failures} 次")
                    if new_status == HealthStatus.HEALTHY:
                        new_status = HealthStatus.WARNING
            
            # 检查最近的错误率
            recent_metrics = list(self.metrics_history)[-10:]  # 最近10次
            if recent_metrics:
                error_count = sum(1 for m in recent_metrics if m.status == "failed")
                error_rate = error_count / len(recent_metrics)
                
                if error_rate > 0.5:
                    issues.append(f"最近错误率过高: {error_rate:.2%}")
                    new_status = HealthStatus.UNHEALTHY
                elif error_rate > 0.2:
                    issues.append(f"最近错误率较高: {error_rate:.2%}")
                    if new_status == HealthStatus.HEALTHY:
                        new_status = HealthStatus.WARNING
            
            # 更新健康状态
            if new_status != current_status:
                self.health_status = new_status
                
                # 生成健康状态变化告警
                if new_status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                    self._create_alert(
                        AlertLevel.ERROR if new_status == HealthStatus.CRITICAL else AlertLevel.WARNING,
                        f"系统健康状态变化: {new_status.value}",
                        f"健康状态从 {current_status.value} 变为 {new_status.value}。问题: {'; '.join(issues)}",
                        "health_check"
                    )
                elif new_status == HealthStatus.HEALTHY and current_status != HealthStatus.HEALTHY:
                    self._create_alert(
                        AlertLevel.INFO,
                        "系统健康状态恢复",
                        f"健康状态从 {current_status.value} 恢复为 {new_status.value}",
                        "health_check"
                    )
            
            logger.debug(f"健康检查完成，状态: {new_status.value}")
            
        except Exception as e:
            logger.error(f"执行健康检查失败: {e}")
    
    async def _metrics_cleanup_loop(self):
        """指标清理循环"""
        try:
            retention_hours = self.monitor_config.get('metrics_retention_hours', 24)
            logger.info(f"指标清理循环启动，保留时间: {retention_hours}小时")
            
            while self.is_running:
                try:
                    await self._cleanup_old_metrics(retention_hours)
                    await asyncio.sleep(3600)  # 每小时清理一次
                    
                except asyncio.CancelledError:
                    logger.info("指标清理循环被取消")
                    break
                except Exception as e:
                    logger.error(f"指标清理循环异常: {e}")
                    await asyncio.sleep(3600)
                    
        except Exception as e:
            logger.error(f"指标清理循环严重异常: {e}")
    
    async def _alert_cleanup_loop(self):
        """告警清理循环"""
        try:
            retention_hours = self.monitor_config.get('alert_retention_hours', 168)
            logger.info(f"告警清理循环启动，保留时间: {retention_hours}小时")
            
            while self.is_running:
                try:
                    await self._cleanup_old_alerts(retention_hours)
                    await asyncio.sleep(3600)  # 每小时清理一次
                    
                except asyncio.CancelledError:
                    logger.info("告警清理循环被取消")
                    break
                except Exception as e:
                    logger.error(f"告警清理循环异常: {e}")
                    await asyncio.sleep(3600)
                    
        except Exception as e:
            logger.error(f"告警清理循环严重异常: {e}")
    
    async def _cleanup_old_metrics(self, retention_hours: int):
        """清理过期指标"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)
            
            # 清理过期指标
            original_count = len(self.metrics_history)
            self.metrics_history = deque(
                [m for m in self.metrics_history 
                 if datetime.fromisoformat(m.timestamp) > cutoff_time],
                maxlen=1000
            )
            
            cleaned_count = original_count - len(self.metrics_history)
            if cleaned_count > 0:
                logger.debug(f"清理了 {cleaned_count} 个过期指标")
            
        except Exception as e:
            logger.error(f"清理过期指标失败: {e}")
    
    async def _cleanup_old_alerts(self, retention_hours: int):
        """清理过期告警"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)
            
            # 清理过期告警
            original_count = len(self.alerts)
            self.alerts = deque(
                [a for a in self.alerts 
                 if datetime.fromisoformat(a.timestamp) > cutoff_time],
                maxlen=500
            )
            
            cleaned_count = original_count - len(self.alerts)
            if cleaned_count > 0:
                logger.debug(f"清理了 {cleaned_count} 个过期告警")
            
        except Exception as e:
            logger.error(f"清理过期告警失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控器状态"""
        try:
            uptime = 0
            if self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
            
            return {
                'is_running': self.is_running,
                'health_status': self.health_status.value,
                'uptime': uptime,
                'metrics_count': len(self.metrics_history),
                'alerts_count': len(self.alerts),
                'unresolved_alerts': len([a for a in self.alerts if not a.resolved]),
                'sync_stats': dict(self.sync_stats),
                'monitor_config': self.monitor_config
            }
            
        except Exception as e:
            logger.error(f"获取监控器状态失败: {e}")
            return {}
    
    def get_recent_metrics(self, hours: int = 1) -> List[Dict[str, Any]]:
        """获取最近的指标"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_metrics = [
                m.to_dict() for m in self.metrics_history
                if datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
            
            return recent_metrics
            
        except Exception as e:
            logger.error(f"获取最近指标失败: {e}")
            return []
    
    def get_recent_alerts(self, hours: int = 24, level: Optional[AlertLevel] = None) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_alerts = [
                a.to_dict() for a in self.alerts
                if datetime.fromisoformat(a.timestamp) > cutoff_time
                and (level is None or a.level == level)
            ]
            
            return recent_alerts
            
        except Exception as e:
            logger.error(f"获取最近告警失败: {e}")
            return []
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        try:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now().isoformat()
                    logger.info(f"告警已解决: {alert_id}")
                    return True
            
            logger.warning(f"未找到告警: {alert_id}")
            return False
            
        except Exception as e:
            logger.error(f"解决告警失败: {e}")
            return False
    
    def export_metrics(self, format: str = "json") -> str:
        """导出指标数据"""
        try:
            if format.lower() == "json":
                metrics_data = [m.to_dict() for m in self.metrics_history]
                return json.dumps(metrics_data, indent=2, ensure_ascii=False)
            else:
                logger.error(f"不支持的导出格式: {format}")
                return ""
            
        except Exception as e:
            logger.error(f"导出指标数据失败: {e}")
            return ""
    
    def reset_stats(self):
        """重置统计信息"""
        try:
            self.sync_stats.clear()
            self.metrics_history.clear()
            self.alerts.clear()
            self.health_status = HealthStatus.HEALTHY
            
            logger.info("监控器统计信息已重置")
            
        except Exception as e:
            logger.error(f"重置统计信息失败: {e}")
    
    def __str__(self) -> str:
        return f"SyncMonitor(running={self.is_running}, health={self.health_status.value})"
    
    def __repr__(self) -> str:
        return self.__str__()