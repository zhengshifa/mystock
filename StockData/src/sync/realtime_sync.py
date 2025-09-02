#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时数据同步器

实现实时数据同步功能，包括:
- 30秒间隔的实时行情同步
- 实时tick数据同步
- 实时指数数据同步
- 异步任务调度
- 错误处理和重试
- 性能监控
"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from loguru import logger
import time
from collections import defaultdict

from ..data_processor import DataProcessorManager
from ..database import DataType
from ..utils.exceptions import SyncError


class RealtimeDataSync:
    """实时数据同步器"""
    
    def __init__(self, processor_manager: DataProcessorManager, config: Dict[str, Any]):
        self.processor_manager = processor_manager
        self.config = config
        
        # 同步配置
        self.sync_interval = config.get('sync_interval', 30)  # 同步间隔(秒)
        self.symbols = config.get('symbols', [])  # 要同步的股票代码
        self.index_symbols = config.get('index_symbols', [])  # 要同步的指数代码
        self.max_retries = config.get('max_retries', 3)  # 最大重试次数
        self.retry_delay = config.get('retry_delay', 5)  # 重试延迟(秒)
        self.batch_size = config.get('batch_size', 100)  # 批处理大小
        
        # 同步任务配置
        self.sync_tasks = config.get('sync_tasks', {
            'realtime_quotes': True,  # 实时行情
            'tick_data': False,       # tick数据(可选)
            'index_data': True,       # 指数数据
            'market_status': True     # 市场状态
        })
        
        # 运行状态
        self.is_running = False
        self.is_paused = False
        self._sync_task = None
        self._last_sync_time = None
        self._sync_count = 0
        
        # 统计信息
        self.stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'avg_sync_time': 0.0,
            'last_sync_time': None,
            'sync_errors': [],
            'task_stats': defaultdict(lambda: {
                'syncs': 0,
                'success': 0,
                'errors': 0,
                'avg_time': 0.0
            })
        }
        
        # 错误处理
        self._consecutive_errors = 0
        self._max_consecutive_errors = config.get('max_consecutive_errors', 10)
        self._error_backoff_factor = config.get('error_backoff_factor', 2.0)
        
        logger.info(f"实时数据同步器初始化完成，同步间隔: {self.sync_interval}秒，股票数量: {len(self.symbols)}")
    
    async def start(self):
        """启动实时同步"""
        try:
            if self.is_running:
                logger.warning("实时同步已在运行中")
                return True
            
            logger.info("启动实时数据同步...")
            
            # 检查处理器管理器状态
            if hasattr(self.processor_manager, 'is_running') and not self.processor_manager.is_running:
                logger.warning("数据处理器管理器未运行，尝试等待...")
                # 等待一段时间让处理器管理器启动
                await asyncio.sleep(1)
                if hasattr(self.processor_manager, 'is_running') and not self.processor_manager.is_running:
                    raise SyncError("数据处理器管理器未运行")
            
            self.is_running = True
            self.is_paused = False
            self._consecutive_errors = 0
            
            # 启动同步任务
            self._sync_task = asyncio.create_task(self._sync_loop())
            
            logger.info("实时数据同步已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动实时同步失败: {e}")
            self.is_running = False
            return False
    
    async def stop(self):
        """停止实时同步"""
        try:
            if not self.is_running:
                logger.warning("实时同步未在运行")
                return
            
            logger.info("停止实时数据同步...")
            
            self.is_running = False
            
            # 取消同步任务
            if self._sync_task and not self._sync_task.done():
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("实时数据同步已停止")
            
        except Exception as e:
            logger.error(f"停止实时同步失败: {e}")
    
    async def pause(self):
        """暂停同步"""
        if self.is_running:
            self.is_paused = True
            logger.info("实时数据同步已暂停")
    
    async def resume(self):
        """恢复同步"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            logger.info("实时数据同步已恢复")
    
    async def _sync_loop(self):
        """同步循环"""
        try:
            logger.info("开始实时数据同步循环")
            
            while self.is_running:
                try:
                    # 检查是否暂停
                    if self.is_paused:
                        await asyncio.sleep(1)
                        continue
                    
                    # 检查市场状态
                    if not await self._is_market_open():
                        logger.debug("市场未开盘，跳过同步")
                        await asyncio.sleep(self.sync_interval)
                        continue
                    
                    # 执行同步
                    sync_start_time = time.time()
                    success = await self._perform_sync()
                    sync_duration = time.time() - sync_start_time
                    
                    # 更新统计信息
                    self._update_sync_stats(success, sync_duration)
                    
                    if success:
                        self._consecutive_errors = 0
                        logger.debug(f"实时同步完成，耗时: {sync_duration:.2f}秒")
                    else:
                        self._consecutive_errors += 1
                        logger.warning(f"实时同步失败，连续失败次数: {self._consecutive_errors}")
                    
                    # 检查连续错误次数
                    if self._consecutive_errors >= self._max_consecutive_errors:
                        logger.error(f"连续失败次数达到上限({self._max_consecutive_errors})，停止同步")
                        break
                    
                    # 计算下次同步时间
                    next_sync_delay = self._calculate_next_sync_delay(success)
                    await asyncio.sleep(next_sync_delay)
                    
                except asyncio.CancelledError:
                    logger.info("同步循环被取消")
                    break
                except Exception as e:
                    logger.error(f"同步循环异常: {e}")
                    self._consecutive_errors += 1
                    
                    # 异常时增加延迟
                    error_delay = min(self.sync_interval * self._error_backoff_factor, 300)  # 最大5分钟
                    await asyncio.sleep(error_delay)
            
        except Exception as e:
            logger.error(f"同步循环严重异常: {e}")
        finally:
            logger.info("实时数据同步循环结束")
    
    async def _perform_sync(self) -> bool:
        """执行同步操作"""
        try:
            sync_tasks = []
            
            # 实时行情同步
            if self.sync_tasks.get('realtime_quotes', True):
                sync_tasks.append(self._sync_realtime_quotes())
            
            # tick数据同步
            if self.sync_tasks.get('tick_data', False):
                sync_tasks.append(self._sync_tick_data())
            
            # 指数数据同步
            if self.sync_tasks.get('index_data', True):
                sync_tasks.append(self._sync_index_data())
            
            if not sync_tasks:
                logger.warning("没有配置同步任务")
                return True
            
            # 并发执行所有同步任务
            results = await asyncio.gather(*sync_tasks, return_exceptions=True)
            
            # 检查结果
            success_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"同步任务 {i} 异常: {result}")
                elif result:
                    success_count += 1
            
            # 如果至少有一半任务成功，认为同步成功
            success = success_count >= len(results) / 2
            
            self._last_sync_time = datetime.now()
            self._sync_count += 1
            
            return success
            
        except Exception as e:
            logger.error(f"执行同步操作失败: {e}")
            return False
    
    async def _sync_realtime_quotes(self) -> bool:
        """同步实时行情"""
        try:
            task_start_time = time.time()
            
            if not self.symbols:
                logger.debug("未配置股票代码，跳过实时行情同步")
                return True
            
            # 分批同步
            success_count = 0
            total_batches = 0
            
            for i in range(0, len(self.symbols), self.batch_size):
                batch_symbols = self.symbols[i:i + self.batch_size]
                total_batches += 1
                
                try:
                    success = await self.processor_manager.update_realtime_quotes(batch_symbols)
                    if success:
                        success_count += 1
                    
                    # 批次间短暂休息
                    if i + self.batch_size < len(self.symbols):
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    logger.warning(f"同步实时行情批次失败: {batch_symbols[:3]}..., 错误: {e}")
            
            task_duration = time.time() - task_start_time
            task_success = success_count >= total_batches / 2
            
            # 更新任务统计
            self._update_task_stats('realtime_quotes', task_success, task_duration)
            
            logger.debug(f"实时行情同步完成: {success_count}/{total_batches} 批次成功")
            return task_success
            
        except Exception as e:
            logger.error(f"同步实时行情失败: {e}")
            self._update_task_stats('realtime_quotes', False, 0)
            return False
    
    async def _sync_tick_data(self) -> bool:
        """同步tick数据"""
        try:
            task_start_time = time.time()
            
            # tick数据通常只同步重点关注的股票
            focus_symbols = self.config.get('focus_symbols', self.symbols[:50])  # 默认前50只
            
            if not focus_symbols:
                logger.debug("未配置重点股票，跳过tick数据同步")
                return True
            
            # 获取最近的tick数据
            success = await self.processor_manager.process_data(
                DataType.MARKET_DATA,
                data_subtype='tick_data',
                symbols=focus_symbols,
                start_time=(datetime.now() - timedelta(minutes=1)).strftime('%H:%M:%S'),
                end_time=datetime.now().strftime('%H:%M:%S')
            )
            
            task_duration = time.time() - task_start_time
            self._update_task_stats('tick_data', success, task_duration)
            
            logger.debug(f"tick数据同步完成: {'成功' if success else '失败'}")
            return success
            
        except Exception as e:
            logger.error(f"同步tick数据失败: {e}")
            self._update_task_stats('tick_data', False, 0)
            return False
    
    async def _sync_index_data(self) -> bool:
        """同步指数数据"""
        try:
            task_start_time = time.time()
            
            if not self.index_symbols:
                logger.debug("未配置指数代码，跳过指数数据同步")
                return True
            
            # 同步指数实时行情
            success = await self.processor_manager.update_realtime_quotes(self.index_symbols)
            
            task_duration = time.time() - task_start_time
            self._update_task_stats('index_data', success, task_duration)
            
            logger.debug(f"指数数据同步完成: {'成功' if success else '失败'}")
            return success
            
        except Exception as e:
            logger.error(f"同步指数数据失败: {e}")
            self._update_task_stats('index_data', False, 0)
            return False
    
    async def _is_market_open(self) -> bool:
        """检查市场是否开盘"""
        try:
            now = datetime.now()
            current_time = now.time()
            weekday = now.weekday()
            
            # 周末不开盘
            if weekday >= 5:  # 5=周六, 6=周日
                return False
            
            # 交易时间: 9:30-11:30, 13:00-15:00
            morning_start = datetime.strptime('09:30', '%H:%M').time()
            morning_end = datetime.strptime('11:30', '%H:%M').time()
            afternoon_start = datetime.strptime('13:00', '%H:%M').time()
            afternoon_end = datetime.strptime('15:00', '%H:%M').time()
            
            is_morning_session = morning_start <= current_time <= morning_end
            is_afternoon_session = afternoon_start <= current_time <= afternoon_end
            
            return is_morning_session or is_afternoon_session
            
        except Exception as e:
            logger.warning(f"检查市场状态失败: {e}")
            return True  # 默认认为开盘
    
    def _calculate_next_sync_delay(self, last_sync_success: bool) -> float:
        """计算下次同步延迟"""
        try:
            base_delay = self.sync_interval
            
            # 如果连续失败，增加延迟
            if not last_sync_success and self._consecutive_errors > 0:
                backoff_multiplier = min(self._error_backoff_factor ** self._consecutive_errors, 10)
                base_delay *= backoff_multiplier
            
            # 添加随机抖动，避免所有实例同时同步
            import random
            jitter = random.uniform(0.9, 1.1)
            
            return base_delay * jitter
            
        except Exception:
            return self.sync_interval
    
    def _update_sync_stats(self, success: bool, duration: float):
        """更新同步统计信息"""
        try:
            self.stats['total_syncs'] += 1
            
            if success:
                self.stats['successful_syncs'] += 1
            else:
                self.stats['failed_syncs'] += 1
                # 记录错误
                error_info = {
                    'timestamp': datetime.now().isoformat(),
                    'consecutive_errors': self._consecutive_errors
                }
                self.stats['sync_errors'].append(error_info)
                
                # 只保留最近100个错误记录
                if len(self.stats['sync_errors']) > 100:
                    self.stats['sync_errors'] = self.stats['sync_errors'][-100:]
            
            # 更新平均时间
            if self.stats['total_syncs'] > 0:
                total_time = self.stats.get('total_time', 0) + duration
                self.stats['total_time'] = total_time
                self.stats['avg_sync_time'] = total_time / self.stats['total_syncs']
            
            self.stats['last_sync_time'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.warning(f"更新同步统计失败: {e}")
    
    def _update_task_stats(self, task_name: str, success: bool, duration: float):
        """更新任务统计信息"""
        try:
            task_stats = self.stats['task_stats'][task_name]
            task_stats['syncs'] += 1
            
            if success:
                task_stats['success'] += 1
            else:
                task_stats['errors'] += 1
            
            # 更新平均时间
            if task_stats['syncs'] > 0:
                total_time = task_stats.get('total_time', 0) + duration
                task_stats['total_time'] = total_time
                task_stats['avg_time'] = total_time / task_stats['syncs']
            
        except Exception as e:
            logger.warning(f"更新任务统计失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        try:
            return {
                'is_running': self.is_running,
                'is_paused': self.is_paused,
                'sync_interval': self.sync_interval,
                'last_sync_time': self._last_sync_time.isoformat() if self._last_sync_time else None,
                'sync_count': self._sync_count,
                'consecutive_errors': self._consecutive_errors,
                'symbols_count': len(self.symbols),
                'index_symbols_count': len(self.index_symbols),
                'sync_tasks': self.sync_tasks
            }
            
        except Exception as e:
            logger.error(f"获取同步状态失败: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = self.stats.copy()
            
            # 计算成功率
            if stats['total_syncs'] > 0:
                stats['success_rate'] = stats['successful_syncs'] / stats['total_syncs']
            else:
                stats['success_rate'] = 0.0
            
            # 计算各任务成功率
            for task_name, task_stats in stats['task_stats'].items():
                if task_stats['syncs'] > 0:
                    task_stats['success_rate'] = task_stats['success'] / task_stats['syncs']
                else:
                    task_stats['success_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def reset_stats(self):
        """重置统计信息"""
        try:
            self.stats = {
                'total_syncs': 0,
                'successful_syncs': 0,
                'failed_syncs': 0,
                'avg_sync_time': 0.0,
                'last_sync_time': None,
                'sync_errors': [],
                'task_stats': defaultdict(lambda: {
                    'syncs': 0,
                    'success': 0,
                    'errors': 0,
                    'avg_time': 0.0
                })
            }
            self._consecutive_errors = 0
            logger.info("实时同步统计信息已重置")
            
        except Exception as e:
            logger.error(f"重置统计信息失败: {e}")
    
    async def force_sync(self) -> bool:
        """强制执行一次同步"""
        try:
            logger.info("执行强制同步...")
            
            if not self.processor_manager.is_running:
                logger.error("数据处理器管理器未运行")
                return False
            
            success = await self._perform_sync()
            
            logger.info(f"强制同步完成: {'成功' if success else '失败'}")
            return success
            
        except Exception as e:
            logger.error(f"强制同步失败: {e}")
            return False
    
    def __str__(self) -> str:
        return f"RealtimeDataSync(running={self.is_running}, interval={self.sync_interval}s, symbols={len(self.symbols)})"
    
    def __repr__(self) -> str:
        return self.__str__()