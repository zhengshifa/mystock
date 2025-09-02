#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量数据同步器

实现增量数据同步功能，包括:
- 智能增量更新策略
- 数据变更检测
- 断点续传功能
- 数据一致性保证
- 优化的同步算法
"""

import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from loguru import logger
import time
from collections import defaultdict

from ..data_processor import DataProcessorManager
from ..database import DataType, RepositoryManager
from ..utils.exceptions import SyncError


class IncrementalDataSync:
    """增量数据同步器"""
    
    def __init__(self, processor_manager: DataProcessorManager, 
                 repository_manager: RepositoryManager, config: Dict[str, Any]):
        self.processor_manager = processor_manager
        self.repository_manager = repository_manager
        self.config = config
        
        # 同步配置
        self.symbols = config.get('symbols', [])  # 要同步的股票代码
        self.batch_size = config.get('batch_size', 100)  # 批处理大小
        self.max_retries = config.get('max_retries', 3)  # 最大重试次数
        self.concurrent_limit = config.get('concurrent_limit', 10)  # 并发限制
        
        # 增量同步策略配置
        self.sync_strategies = config.get('sync_strategies', {
            'daily_bars': 'timestamp_based',     # 基于时间戳
            'realtime_quotes': 'full_refresh',   # 全量刷新
            'financial_data': 'version_based',   # 基于版本号
            'dividend_data': 'checksum_based'    # 基于校验和
        })
        
        # 数据类型优先级
        self.sync_priority = config.get('sync_priority', [
            'stock_info',      # 股票基础信息
            'trading_calendar', # 交易日历
            'daily_bars',      # 日K线
            'realtime_quotes', # 实时行情
            'financial_data',  # 财务数据
            'dividend_data'    # 分红数据
        ])
        
        # 检查点配置
        self.checkpoint_interval = config.get('checkpoint_interval', 100)  # 每处理多少条记录保存检查点
        self.checkpoint_file = config.get('checkpoint_file', 'sync_checkpoint.json')
        
        # 运行状态
        self.is_running = False
        self._sync_task = None
        self._semaphore = asyncio.Semaphore(self.concurrent_limit)
        self._checkpoints = {}  # 检查点数据
        
        # 统计信息
        self.stats = {
            'sync_sessions': 0,
            'total_processed': 0,
            'total_updated': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'last_sync_time': None,
            'avg_sync_time': 0.0,
            'data_type_stats': defaultdict(lambda: {
                'processed': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0,
                'last_sync': None
            }),
            'performance_metrics': {
                'records_per_second': 0.0,
                'avg_batch_time': 0.0,
                'cache_hit_rate': 0.0
            }
        }
        
        logger.info(f"增量数据同步器初始化完成，股票数量: {len(self.symbols)}")
    
    async def start_incremental_sync(self, data_types: Optional[List[str]] = None,
                                   symbols: Optional[List[str]] = None,
                                   force_full_sync: bool = False) -> bool:
        """启动增量同步"""
        try:
            if self.is_running:
                logger.warning("增量同步已在运行中")
                return False
            
            data_types = data_types or self.sync_priority
            symbols = symbols or self.symbols
            
            logger.info(f"启动增量同步: {len(symbols)} 只股票，{len(data_types)} 种数据类型")
            
            self.is_running = True
            self.stats['sync_sessions'] += 1
            sync_start_time = time.time()
            
            # 加载检查点
            if not force_full_sync:
                await self._load_checkpoints()
            
            # 启动同步任务
            self._sync_task = asyncio.create_task(
                self._execute_incremental_sync(data_types, symbols, force_full_sync)
            )
            
            success = await self._sync_task
            
            # 更新统计信息
            sync_duration = time.time() - sync_start_time
            self._update_session_stats(success, sync_duration)
            
            # 保存检查点
            await self._save_checkpoints()
            
            logger.info(f"增量同步完成: {'成功' if success else '失败'}，耗时: {sync_duration:.2f}秒")
            
            return success
            
        except Exception as e:
            logger.error(f"增量同步失败: {e}")
            return False
        finally:
            self.is_running = False
    
    async def _execute_incremental_sync(self, data_types: List[str], 
                                      symbols: List[str], force_full_sync: bool) -> bool:
        """执行增量同步"""
        try:
            total_success = 0
            total_tasks = 0
            
            # 按优先级顺序同步各种数据类型
            for data_type in data_types:
                if data_type not in self.sync_priority:
                    logger.warning(f"未知的数据类型: {data_type}")
                    continue
                
                total_tasks += 1
                logger.info(f"开始同步数据类型: {data_type}")
                
                type_start_time = time.time()
                
                try:
                    success = await self._sync_data_type_incremental(
                        data_type, symbols, force_full_sync
                    )
                    
                    if success:
                        total_success += 1
                    
                    type_duration = time.time() - type_start_time
                    self._update_data_type_stats(data_type, success, type_duration)
                    
                    logger.info(f"数据类型 {data_type} 同步完成: {'成功' if success else '失败'}，"
                               f"耗时: {type_duration:.2f}秒")
                    
                except Exception as e:
                    logger.error(f"同步数据类型 {data_type} 失败: {e}")
                    self._update_data_type_stats(data_type, False, 0)
                
                # 数据类型间短暂休息
                await asyncio.sleep(0.5)
            
            # 计算总体成功率
            success_rate = total_success / total_tasks if total_tasks > 0 else 0
            overall_success = success_rate >= 0.8  # 80%成功率认为整体成功
            
            logger.info(f"增量同步执行完成: {total_success}/{total_tasks} 成功，成功率: {success_rate:.2%}")
            
            return overall_success
            
        except Exception as e:
            logger.error(f"执行增量同步失败: {e}")
            return False
    
    async def _sync_data_type_incremental(self, data_type: str, symbols: List[str], 
                                        force_full_sync: bool) -> bool:
        """增量同步特定数据类型"""
        try:
            strategy = self.sync_strategies.get(data_type, 'timestamp_based')
            
            if strategy == 'timestamp_based':
                return await self._sync_timestamp_based(data_type, symbols, force_full_sync)
            elif strategy == 'version_based':
                return await self._sync_version_based(data_type, symbols, force_full_sync)
            elif strategy == 'checksum_based':
                return await self._sync_checksum_based(data_type, symbols, force_full_sync)
            elif strategy == 'full_refresh':
                return await self._sync_full_refresh(data_type, symbols)
            else:
                logger.warning(f"未知的同步策略: {strategy}")
                return False
                
        except Exception as e:
            logger.error(f"增量同步数据类型 {data_type} 失败: {e}")
            return False
    
    async def _sync_timestamp_based(self, data_type: str, symbols: List[str], 
                                  force_full_sync: bool) -> bool:
        """基于时间戳的增量同步"""
        try:
            success_count = 0
            
            # 获取上次同步时间
            last_sync_time = None if force_full_sync else self._get_last_sync_time(data_type)
            
            if last_sync_time:
                logger.info(f"基于时间戳增量同步 {data_type}，上次同步时间: {last_sync_time}")
                start_time = last_sync_time
            else:
                logger.info(f"全量同步 {data_type}")
                start_time = self.config.get('default_start_date', '2020-01-01')
            
            end_time = datetime.now().strftime('%Y-%m-%d')
            
            # 分批处理股票
            for i in range(0, len(symbols), self.batch_size):
                batch_symbols = symbols[i:i + self.batch_size]
                
                try:
                    # 获取需要更新的数据
                    updates_needed = await self._check_timestamp_updates(
                        data_type, batch_symbols, start_time, end_time
                    )
                    
                    if updates_needed:
                        success = await self._process_timestamp_updates(
                            data_type, updates_needed
                        )
                        
                        if success:
                            success_count += len(updates_needed)
                            
                            # 更新检查点
                            self._update_checkpoint(data_type, {
                                'last_sync_time': datetime.now().isoformat(),
                                'processed_symbols': batch_symbols
                            })
                    
                    # 批次间短暂休息
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"处理批次 {batch_symbols[:3]}... 失败: {e}")
            
            # 更新最后同步时间
            self._set_last_sync_time(data_type, datetime.now().isoformat())
            
            logger.info(f"时间戳增量同步 {data_type} 完成: {success_count} 条记录更新")
            
            return success_count > 0 or len(symbols) == 0
            
        except Exception as e:
            logger.error(f"基于时间戳的增量同步失败: {e}")
            return False
    
    async def _sync_version_based(self, data_type: str, symbols: List[str], 
                                force_full_sync: bool) -> bool:
        """基于版本号的增量同步"""
        try:
            success_count = 0
            
            logger.info(f"基于版本号增量同步 {data_type}")
            
            # 获取本地版本信息
            local_versions = {} if force_full_sync else await self._get_local_versions(data_type, symbols)
            
            # 获取远程版本信息
            remote_versions = await self._get_remote_versions(data_type, symbols)
            
            # 比较版本，找出需要更新的数据
            updates_needed = []
            for symbol in symbols:
                local_version = local_versions.get(symbol, '0')
                remote_version = remote_versions.get(symbol, '0')
                
                if remote_version > local_version:
                    updates_needed.append({
                        'symbol': symbol,
                        'local_version': local_version,
                        'remote_version': remote_version
                    })
            
            logger.info(f"发现 {len(updates_needed)} 个版本更新")
            
            # 处理版本更新
            if updates_needed:
                success = await self._process_version_updates(data_type, updates_needed)
                if success:
                    success_count = len(updates_needed)
            
            logger.info(f"版本增量同步 {data_type} 完成: {success_count} 条记录更新")
            
            return success_count > 0 or len(symbols) == 0
            
        except Exception as e:
            logger.error(f"基于版本号的增量同步失败: {e}")
            return False
    
    async def _sync_checksum_based(self, data_type: str, symbols: List[str], 
                                 force_full_sync: bool) -> bool:
        """基于校验和的增量同步"""
        try:
            success_count = 0
            
            logger.info(f"基于校验和增量同步 {data_type}")
            
            # 获取本地校验和
            local_checksums = {} if force_full_sync else await self._get_local_checksums(data_type, symbols)
            
            # 获取远程校验和
            remote_checksums = await self._get_remote_checksums(data_type, symbols)
            
            # 比较校验和，找出需要更新的数据
            updates_needed = []
            for symbol in symbols:
                local_checksum = local_checksums.get(symbol, '')
                remote_checksum = remote_checksums.get(symbol, '')
                
                if remote_checksum != local_checksum:
                    updates_needed.append({
                        'symbol': symbol,
                        'local_checksum': local_checksum,
                        'remote_checksum': remote_checksum
                    })
            
            logger.info(f"发现 {len(updates_needed)} 个校验和差异")
            
            # 处理校验和更新
            if updates_needed:
                success = await self._process_checksum_updates(data_type, updates_needed)
                if success:
                    success_count = len(updates_needed)
            
            logger.info(f"校验和增量同步 {data_type} 完成: {success_count} 条记录更新")
            
            return success_count > 0 or len(symbols) == 0
            
        except Exception as e:
            logger.error(f"基于校验和的增量同步失败: {e}")
            return False
    
    async def _sync_full_refresh(self, data_type: str, symbols: List[str]) -> bool:
        """全量刷新同步"""
        try:
            logger.info(f"全量刷新同步 {data_type}")
            
            # 直接调用处理器进行全量同步
            success = await self.processor_manager.process_data(
                self._get_data_type_enum(data_type),
                symbols=symbols
            )
            
            logger.info(f"全量刷新同步 {data_type} 完成: {'成功' if success else '失败'}")
            
            return success
            
        except Exception as e:
            logger.error(f"全量刷新同步失败: {e}")
            return False
    
    async def _check_timestamp_updates(self, data_type: str, symbols: List[str], 
                                     start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """检查基于时间戳的更新"""
        try:
            updates_needed = []
            
            for symbol in symbols:
                # 检查本地最新数据时间
                local_latest = await self._get_local_latest_timestamp(data_type, symbol)
                
                # 如果本地没有数据或者数据过期，需要更新
                if not local_latest or local_latest < start_time:
                    updates_needed.append({
                        'symbol': symbol,
                        'local_latest': local_latest,
                        'update_start': start_time,
                        'update_end': end_time
                    })
            
            return updates_needed
            
        except Exception as e:
            logger.error(f"检查时间戳更新失败: {e}")
            return []
    
    async def _process_timestamp_updates(self, data_type: str, 
                                       updates: List[Dict[str, Any]]) -> bool:
        """处理基于时间戳的更新"""
        try:
            symbols = [update['symbol'] for update in updates]
            start_time = min(update['update_start'] for update in updates)
            end_time = max(update['update_end'] for update in updates)
            
            success = await self.processor_manager.process_data(
                self._get_data_type_enum(data_type),
                symbols=symbols,
                start_date=start_time,
                end_date=end_time
            )
            
            return success
            
        except Exception as e:
            logger.error(f"处理时间戳更新失败: {e}")
            return False
    
    async def _process_version_updates(self, data_type: str, 
                                     updates: List[Dict[str, Any]]) -> bool:
        """处理基于版本号的更新"""
        try:
            symbols = [update['symbol'] for update in updates]
            
            success = await self.processor_manager.process_data(
                self._get_data_type_enum(data_type),
                symbols=symbols
            )
            
            return success
            
        except Exception as e:
            logger.error(f"处理版本更新失败: {e}")
            return False
    
    async def _process_checksum_updates(self, data_type: str, 
                                      updates: List[Dict[str, Any]]) -> bool:
        """处理基于校验和的更新"""
        try:
            symbols = [update['symbol'] for update in updates]
            
            success = await self.processor_manager.process_data(
                self._get_data_type_enum(data_type),
                symbols=symbols
            )
            
            return success
            
        except Exception as e:
            logger.error(f"处理校验和更新失败: {e}")
            return False
    
    def _get_data_type_enum(self, data_type: str) -> DataType:
        """获取数据类型枚举"""
        mapping = {
            'stock_info': DataType.STOCK_INFO,
            'trading_calendar': DataType.STOCK_INFO,
            'daily_bars': DataType.MARKET_DATA,
            'realtime_quotes': DataType.MARKET_DATA,
            'financial_data': DataType.FINANCIAL_DATA,
            'dividend_data': DataType.FINANCIAL_DATA
        }
        return mapping.get(data_type, DataType.MARKET_DATA)
    
    async def _get_local_latest_timestamp(self, data_type: str, symbol: str) -> Optional[str]:
        """获取本地最新数据时间戳"""
        try:
            # 这里应该调用相应的repository查询最新时间戳
            # 暂时返回None，表示需要全量同步
            return None
            
        except Exception as e:
            logger.debug(f"获取本地最新时间戳失败: {e}")
            return None
    
    async def _get_local_versions(self, data_type: str, symbols: List[str]) -> Dict[str, str]:
        """获取本地版本信息"""
        try:
            # 这里应该调用相应的repository查询版本信息
            return {}
            
        except Exception as e:
            logger.debug(f"获取本地版本信息失败: {e}")
            return {}
    
    async def _get_remote_versions(self, data_type: str, symbols: List[str]) -> Dict[str, str]:
        """获取远程版本信息"""
        try:
            # 这里应该调用API获取远程版本信息
            return {symbol: '1.0' for symbol in symbols}  # 占位符
            
        except Exception as e:
            logger.debug(f"获取远程版本信息失败: {e}")
            return {}
    
    async def _get_local_checksums(self, data_type: str, symbols: List[str]) -> Dict[str, str]:
        """获取本地校验和"""
        try:
            # 这里应该调用相应的repository计算校验和
            return {}
            
        except Exception as e:
            logger.debug(f"获取本地校验和失败: {e}")
            return {}
    
    async def _get_remote_checksums(self, data_type: str, symbols: List[str]) -> Dict[str, str]:
        """获取远程校验和"""
        try:
            # 这里应该调用API获取远程校验和
            return {symbol: 'checksum_' + symbol for symbol in symbols}  # 占位符
            
        except Exception as e:
            logger.debug(f"获取远程校验和失败: {e}")
            return {}
    
    def _get_last_sync_time(self, data_type: str) -> Optional[str]:
        """获取上次同步时间"""
        return self.stats['data_type_stats'][data_type].get('last_sync')
    
    def _set_last_sync_time(self, data_type: str, sync_time: str):
        """设置上次同步时间"""
        self.stats['data_type_stats'][data_type]['last_sync'] = sync_time
    
    def _update_checkpoint(self, data_type: str, checkpoint_data: Dict[str, Any]):
        """更新检查点"""
        try:
            if data_type not in self._checkpoints:
                self._checkpoints[data_type] = {}
            
            self._checkpoints[data_type].update(checkpoint_data)
            
        except Exception as e:
            logger.warning(f"更新检查点失败: {e}")
    
    async def _load_checkpoints(self):
        """加载检查点"""
        try:
            import json
            import os
            
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    self._checkpoints = json.load(f)
                logger.info(f"检查点加载成功: {len(self._checkpoints)} 个数据类型")
            else:
                self._checkpoints = {}
                logger.info("未找到检查点文件，从头开始同步")
                
        except Exception as e:
            logger.warning(f"加载检查点失败: {e}")
            self._checkpoints = {}
    
    async def _save_checkpoints(self):
        """保存检查点"""
        try:
            import json
            
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self._checkpoints, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"检查点保存成功: {self.checkpoint_file}")
            
        except Exception as e:
            logger.warning(f"保存检查点失败: {e}")
    
    def _update_session_stats(self, success: bool, duration: float):
        """更新会话统计"""
        try:
            self.stats['last_sync_time'] = datetime.now().isoformat()
            
            # 更新平均时间
            if self.stats['sync_sessions'] > 0:
                total_time = self.stats.get('total_time', 0) + duration
                self.stats['total_time'] = total_time
                self.stats['avg_sync_time'] = total_time / self.stats['sync_sessions']
            
        except Exception as e:
            logger.warning(f"更新会话统计失败: {e}")
    
    def _update_data_type_stats(self, data_type: str, success: bool, duration: float):
        """更新数据类型统计"""
        try:
            stats = self.stats['data_type_stats'][data_type]
            stats['processed'] += 1
            
            if success:
                stats['updated'] += 1
            else:
                stats['errors'] += 1
            
            stats['last_sync'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.warning(f"更新数据类型统计失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        try:
            return {
                'is_running': self.is_running,
                'total_symbols': len(self.symbols),
                'batch_size': self.batch_size,
                'concurrent_limit': self.concurrent_limit,
                'sync_strategies': self.sync_strategies,
                'sync_priority': self.sync_priority,
                'checkpoint_file': self.checkpoint_file,
                'checkpoints_count': len(self._checkpoints)
            }
            
        except Exception as e:
            logger.error(f"获取同步状态失败: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = self.stats.copy()
            
            # 计算总体统计
            if stats['total_processed'] > 0:
                stats['update_rate'] = stats['total_updated'] / stats['total_processed']
                stats['skip_rate'] = stats['total_skipped'] / stats['total_processed']
                stats['error_rate'] = stats['total_errors'] / stats['total_processed']
            else:
                stats['update_rate'] = 0.0
                stats['skip_rate'] = 0.0
                stats['error_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    async def stop(self):
        """停止增量同步"""
        try:
            if not self.is_running:
                logger.warning("增量同步未在运行")
                return
            
            logger.info("停止增量数据同步...")
            
            self.is_running = False
            
            # 取消同步任务
            if self._sync_task and not self._sync_task.done():
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass
            
            # 保存检查点
            await self._save_checkpoints()
            
            logger.info("增量数据同步已停止")
            
        except Exception as e:
            logger.error(f"停止增量同步失败: {e}")
    
    def __str__(self) -> str:
        return f"IncrementalDataSync(running={self.is_running}, symbols={len(self.symbols)}, strategies={len(self.sync_strategies)})"
    
    def __repr__(self) -> str:
        return self.__str__()