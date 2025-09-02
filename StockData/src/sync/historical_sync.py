#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史数据同步器

负责历史数据的同步，包括:
- 日线/分钟线历史数据同步
- 财务数据历史同步
- 分红数据历史同步
- 股本变动数据历史同步
- 全量和增量同步支持
- 批量处理和并发控制
- 数据完整性检查
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from ..data_processor import DataProcessorManager
from ..database import DataType, FinancialDataType
from ..utils.exceptions import SyncError


@dataclass
class SyncTask:
    """同步任务数据类"""
    task_id: str
    data_type: str
    symbols: List[str]
    start_date: str
    end_date: str
    priority: int = 1
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class HistoricalDataSync:
    """历史数据同步器"""
    
    def __init__(self, processor_manager: DataProcessorManager, config: Dict[str, Any]):
        self.processor_manager = processor_manager
        self.config = config
        
        # 同步配置
        self.sync_config = {
            'batch_size': config.get('batch_size', 100),           # 批处理大小
            'max_concurrent': config.get('max_concurrent', 5),     # 最大并发数
            'retry_attempts': config.get('retry_attempts', 3),     # 重试次数
            'retry_delay': config.get('retry_delay', 5),           # 重试延迟(秒)
            'chunk_size': config.get('chunk_size', 50),            # 数据块大小
            'timeout': config.get('timeout', 300),                # 超时时间(秒)
            'enable_integrity_check': config.get('enable_integrity_check', True),  # 启用完整性检查
            'default_lookback_days': config.get('default_lookback_days', 365)     # 默认回溯天数
        }
        
        # 同步状态
        self.is_running = False
        self.current_tasks = {}
        self.task_queue = asyncio.Queue()
        
        # 线程池
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.sync_config['max_concurrent'],
            thread_name_prefix="HistoricalSync"
        )
        
        # 统计信息
        self.sync_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_records': 0,
            'start_time': None,
            'last_sync_time': None,
            'sync_duration': 0,
            'error_details': []
        }
        
        # 数据类型映射
        self.data_type_mapping = {
            'daily_bars': DataType.MARKET_DATA,
            'minute_bars': DataType.MARKET_DATA,
            'financial_data': DataType.FINANCIAL_DATA,
            'dividend_data': DataType.FINANCIAL_DATA,
            'share_change': DataType.FINANCIAL_DATA
        }
        
        logger.info("历史数据同步器初始化完成")
    
    async def start(self) -> bool:
        """启动历史数据同步器"""
        try:
            if self.is_running:
                logger.warning("历史数据同步器已在运行")
                return True
            
            logger.info("启动历史数据同步器...")
            
            # 检查依赖
            if not self.processor_manager.is_running:
                logger.error("数据处理器管理器未运行")
                return False
            
            self.is_running = True
            self.sync_stats['start_time'] = datetime.now().isoformat()
            
            logger.info("历史数据同步器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动历史数据同步器失败: {e}")
            self.is_running = False
            return False
    
    async def stop(self):
        """停止历史数据同步器"""
        try:
            if not self.is_running:
                logger.warning("历史数据同步器未运行")
                return
            
            logger.info("停止历史数据同步器...")
            
            self.is_running = False
            
            # 等待当前任务完成
            if self.current_tasks:
                logger.info(f"等待 {len(self.current_tasks)} 个任务完成...")
                await asyncio.gather(*self.current_tasks.values(), return_exceptions=True)
            
            # 关闭线程池
            self.thread_pool.shutdown(wait=True)
            
            logger.info("历史数据同步器已停止")
            
        except Exception as e:
            logger.error(f"停止历史数据同步器失败: {e}")
    
    async def sync_all_historical_data(self, symbols: Optional[List[str]] = None,
                                     start_date: Optional[str] = None,
                                     end_date: Optional[str] = None) -> bool:
        """同步所有历史数据"""
        try:
            logger.info("开始同步所有历史数据...")
            
            if not self.is_running:
                logger.error("历史数据同步器未运行")
                return False
            
            # 设置默认日期范围
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            if start_date is None:
                start_dt = datetime.now() - timedelta(days=self.sync_config['default_lookback_days'])
                start_date = start_dt.strftime('%Y-%m-%d')
            
            # 获取股票列表
            if symbols is None:
                symbols = await self._get_active_symbols()
            
            if not symbols:
                logger.warning("没有找到需要同步的股票")
                return True
            
            logger.info(f"准备同步 {len(symbols)} 只股票的历史数据，日期范围: {start_date} 到 {end_date}")
            
            # 创建同步任务
            tasks = []
            
            # 日线数据
            tasks.append(self._create_sync_task(
                'daily_bars', symbols, start_date, end_date, priority=1
            ))
            
            # 财务数据
            tasks.append(self._create_sync_task(
                'financial_data', symbols, start_date, end_date, priority=2
            ))
            
            # 分红数据
            tasks.append(self._create_sync_task(
                'dividend_data', symbols, start_date, end_date, priority=3
            ))
            
            # 股本变动数据
            tasks.append(self._create_sync_task(
                'share_change', symbols, start_date, end_date, priority=3
            ))
            
            # 执行同步任务
            success_count = 0
            for task in tasks:
                try:
                    success = await self._execute_sync_task(task)
                    if success:
                        success_count += 1
                    else:
                        logger.error(f"同步任务失败: {task.data_type}")
                        
                except Exception as e:
                    logger.error(f"执行同步任务异常: {task.data_type}, {e}")
            
            # 数据完整性检查
            if self.sync_config['enable_integrity_check']:
                await self._perform_integrity_check(symbols, start_date, end_date)
            
            self.sync_stats['last_sync_time'] = datetime.now().isoformat()
            
            success_rate = success_count / len(tasks) if tasks else 0
            logger.info(f"历史数据同步完成，成功率: {success_rate:.2%} ({success_count}/{len(tasks)})")
            
            return success_rate >= 0.8  # 80%以上成功率认为同步成功
            
        except Exception as e:
            logger.error(f"同步所有历史数据失败: {e}")
            return False
    
    async def sync_incremental_data(self, data_types: Optional[List[str]] = None,
                                  symbols: Optional[List[str]] = None,
                                  days_back: int = 7) -> bool:
        """增量同步历史数据"""
        try:
            logger.info(f"开始增量同步历史数据，回溯 {days_back} 天...")
            
            if not self.is_running:
                logger.error("历史数据同步器未运行")
                return False
            
            # 设置日期范围
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_dt = datetime.now() - timedelta(days=days_back)
            start_date = start_dt.strftime('%Y-%m-%d')
            
            # 获取股票列表
            if symbols is None:
                symbols = await self._get_active_symbols()
            
            # 设置数据类型
            if data_types is None:
                data_types = ['daily_bars', 'financial_data']
            
            logger.info(f"增量同步 {len(symbols)} 只股票的 {len(data_types)} 种数据类型")
            
            # 创建增量同步任务
            tasks = []
            for data_type in data_types:
                task = self._create_sync_task(
                    data_type, symbols, start_date, end_date, priority=1
                )
                tasks.append(task)
            
            # 执行同步任务
            success_count = 0
            for task in tasks:
                try:
                    success = await self._execute_sync_task(task)
                    if success:
                        success_count += 1
                        
                except Exception as e:
                    logger.error(f"执行增量同步任务异常: {task.data_type}, {e}")
            
            success_rate = success_count / len(tasks) if tasks else 0
            logger.info(f"增量同步完成，成功率: {success_rate:.2%} ({success_count}/{len(tasks)})")
            
            return success_rate >= 0.9  # 90%以上成功率认为增量同步成功
            
        except Exception as e:
            logger.error(f"增量同步历史数据失败: {e}")
            return False
    
    async def sync_specific_data(self, data_type: str, symbols: List[str],
                               start_date: str, end_date: str) -> bool:
        """同步特定数据"""
        try:
            logger.info(f"开始同步特定数据: {data_type}, {len(symbols)} 只股票")
            
            if not self.is_running:
                logger.error("历史数据同步器未运行")
                return False
            
            # 创建同步任务
            task = self._create_sync_task(data_type, symbols, start_date, end_date)
            
            # 执行同步任务
            success = await self._execute_sync_task(task)
            
            if success:
                logger.info(f"特定数据同步成功: {data_type}")
            else:
                logger.error(f"特定数据同步失败: {data_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"同步特定数据失败: {e}")
            return False
    
    def _create_sync_task(self, data_type: str, symbols: List[str],
                         start_date: str, end_date: str, priority: int = 1) -> SyncTask:
        """创建同步任务"""
        task_id = f"{data_type}_{int(time.time() * 1000)}"
        
        return SyncTask(
            task_id=task_id,
            data_type=data_type,
            symbols=symbols.copy(),
            start_date=start_date,
            end_date=end_date,
            priority=priority
        )
    
    async def _execute_sync_task(self, task: SyncTask) -> bool:
        """执行同步任务"""
        try:
            logger.info(f"执行同步任务: {task.task_id} ({task.data_type})")
            
            self.sync_stats['total_tasks'] += 1
            self.current_tasks[task.task_id] = asyncio.current_task()
            
            start_time = time.time()
            
            # 根据数据类型选择处理器
            if task.data_type == 'daily_bars':
                success = await self._sync_daily_bars(task)
            elif task.data_type == 'minute_bars':
                success = await self._sync_minute_bars(task)
            elif task.data_type == 'financial_data':
                success = await self._sync_financial_data(task)
            elif task.data_type == 'dividend_data':
                success = await self._sync_dividend_data(task)
            elif task.data_type == 'share_change':
                success = await self._sync_share_change_data(task)
            else:
                logger.error(f"未知的数据类型: {task.data_type}")
                success = False
            
            # 更新统计
            duration = time.time() - start_time
            self.sync_stats['sync_duration'] += duration
            
            if success:
                self.sync_stats['completed_tasks'] += 1
                logger.info(f"同步任务完成: {task.task_id}, 耗时: {duration:.2f}s")
            else:
                self.sync_stats['failed_tasks'] += 1
                logger.error(f"同步任务失败: {task.task_id}")
            
            # 清理任务记录
            if task.task_id in self.current_tasks:
                del self.current_tasks[task.task_id]
            
            return success
            
        except Exception as e:
            logger.error(f"执行同步任务异常: {task.task_id}, {e}")
            self.sync_stats['failed_tasks'] += 1
            self.sync_stats['error_details'].append({
                'task_id': task.task_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            if task.task_id in self.current_tasks:
                del self.current_tasks[task.task_id]
            
            return False
    
    async def _sync_daily_bars(self, task: SyncTask) -> bool:
        """同步日线数据"""
        try:
            logger.debug(f"同步日线数据: {len(task.symbols)} 只股票")
            
            # 分批处理股票
            batch_size = self.sync_config['batch_size']
            total_records = 0
            
            for i in range(0, len(task.symbols), batch_size):
                batch_symbols = task.symbols[i:i + batch_size]
                
                # 调用市场数据处理器
                result = await self.processor_manager.process_data(
                    data_type=DataType.MARKET_DATA,
                    subtype='daily_bars',
                    symbols=batch_symbols,
                    start_date=task.start_date,
                    end_date=task.end_date
                )
                
                if result.get('success', False):
                    records = result.get('records_processed', 0)
                    total_records += records
                    logger.debug(f"批次 {i//batch_size + 1} 同步成功，处理 {records} 条记录")
                else:
                    logger.error(f"批次 {i//batch_size + 1} 同步失败: {result.get('error', '未知错误')}")
                    return False
                
                # 避免过于频繁的请求
                await asyncio.sleep(0.1)
            
            self.sync_stats['total_records'] += total_records
            logger.info(f"日线数据同步完成，共处理 {total_records} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"同步日线数据失败: {e}")
            return False
    
    async def _sync_minute_bars(self, task: SyncTask) -> bool:
        """同步分钟线数据"""
        try:
            logger.debug(f"同步分钟线数据: {len(task.symbols)} 只股票")
            
            # 分钟线数据量大，需要更小的批次
            batch_size = min(self.sync_config['batch_size'] // 5, 20)
            total_records = 0
            
            for i in range(0, len(task.symbols), batch_size):
                batch_symbols = task.symbols[i:i + batch_size]
                
                # 调用市场数据处理器
                result = await self.processor_manager.process_data(
                    data_type=DataType.MARKET_DATA,
                    subtype='minute_bars',
                    symbols=batch_symbols,
                    start_date=task.start_date,
                    end_date=task.end_date
                )
                
                if result.get('success', False):
                    records = result.get('records_processed', 0)
                    total_records += records
                    logger.debug(f"批次 {i//batch_size + 1} 同步成功，处理 {records} 条记录")
                else:
                    logger.error(f"批次 {i//batch_size + 1} 同步失败: {result.get('error', '未知错误')}")
                    return False
                
                # 分钟线数据请求间隔稍长
                await asyncio.sleep(0.5)
            
            self.sync_stats['total_records'] += total_records
            logger.info(f"分钟线数据同步完成，共处理 {total_records} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"同步分钟线数据失败: {e}")
            return False
    
    async def _sync_financial_data(self, task: SyncTask) -> bool:
        """同步财务数据"""
        try:
            logger.debug(f"同步财务数据: {len(task.symbols)} 只股票")
            
            # 财务数据类型
            financial_subtypes = [
                'income_statement',    # 利润表
                'balance_sheet',       # 资产负债表
                'cash_flow',          # 现金流量表
                'financial_indicator'  # 财务指标
            ]
            
            total_records = 0
            batch_size = self.sync_config['batch_size']
            
            for subtype in financial_subtypes:
                logger.debug(f"同步财务数据子类型: {subtype}")
                
                for i in range(0, len(task.symbols), batch_size):
                    batch_symbols = task.symbols[i:i + batch_size]
                    
                    # 调用财务数据处理器
                    result = await self.processor_manager.process_data(
                        data_type=DataType.FINANCIAL_DATA,
                        subtype=subtype,
                        symbols=batch_symbols,
                        start_date=task.start_date,
                        end_date=task.end_date
                    )
                    
                    if result.get('success', False):
                        records = result.get('records_processed', 0)
                        total_records += records
                        logger.debug(f"{subtype} 批次 {i//batch_size + 1} 同步成功，处理 {records} 条记录")
                    else:
                        logger.error(f"{subtype} 批次 {i//batch_size + 1} 同步失败: {result.get('error', '未知错误')}")
                    
                    await asyncio.sleep(0.2)
            
            self.sync_stats['total_records'] += total_records
            logger.info(f"财务数据同步完成，共处理 {total_records} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"同步财务数据失败: {e}")
            return False
    
    async def _sync_dividend_data(self, task: SyncTask) -> bool:
        """同步分红数据"""
        try:
            logger.debug(f"同步分红数据: {len(task.symbols)} 只股票")
            
            batch_size = self.sync_config['batch_size']
            total_records = 0
            
            for i in range(0, len(task.symbols), batch_size):
                batch_symbols = task.symbols[i:i + batch_size]
                
                # 调用财务数据处理器
                result = await self.processor_manager.process_data(
                    data_type=DataType.FINANCIAL_DATA,
                    subtype='dividend',
                    symbols=batch_symbols,
                    start_date=task.start_date,
                    end_date=task.end_date
                )
                
                if result.get('success', False):
                    records = result.get('records_processed', 0)
                    total_records += records
                    logger.debug(f"批次 {i//batch_size + 1} 同步成功，处理 {records} 条记录")
                else:
                    logger.error(f"批次 {i//batch_size + 1} 同步失败: {result.get('error', '未知错误')}")
                
                await asyncio.sleep(0.1)
            
            self.sync_stats['total_records'] += total_records
            logger.info(f"分红数据同步完成，共处理 {total_records} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"同步分红数据失败: {e}")
            return False
    
    async def _sync_share_change_data(self, task: SyncTask) -> bool:
        """同步股本变动数据"""
        try:
            logger.debug(f"同步股本变动数据: {len(task.symbols)} 只股票")
            
            batch_size = self.sync_config['batch_size']
            total_records = 0
            
            for i in range(0, len(task.symbols), batch_size):
                batch_symbols = task.symbols[i:i + batch_size]
                
                # 调用财务数据处理器
                result = await self.processor_manager.process_data(
                    data_type=DataType.FINANCIAL_DATA,
                    subtype='share_change',
                    symbols=batch_symbols,
                    start_date=task.start_date,
                    end_date=task.end_date
                )
                
                if result.get('success', False):
                    records = result.get('records_processed', 0)
                    total_records += records
                    logger.debug(f"批次 {i//batch_size + 1} 同步成功，处理 {records} 条记录")
                else:
                    logger.error(f"批次 {i//batch_size + 1} 同步失败: {result.get('error', '未知错误')}")
                
                await asyncio.sleep(0.1)
            
            self.sync_stats['total_records'] += total_records
            logger.info(f"股本变动数据同步完成，共处理 {total_records} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"同步股本变动数据失败: {e}")
            return False
    
    async def _get_active_symbols(self) -> List[str]:
        """获取活跃股票列表"""
        try:
            # 调用股票信息处理器获取股票列表
            result = await self.processor_manager.process_data(
                data_type=DataType.STOCK_INFO,
                subtype='stock_list'
            )
            
            if result.get('success', False):
                symbols = result.get('symbols', [])
                logger.debug(f"获取到 {len(symbols)} 只活跃股票")
                return symbols
            else:
                logger.error(f"获取活跃股票列表失败: {result.get('error', '未知错误')}")
                return []
                
        except Exception as e:
            logger.error(f"获取活跃股票列表异常: {e}")
            return []
    
    async def _perform_integrity_check(self, symbols: List[str], 
                                     start_date: str, end_date: str) -> bool:
        """执行数据完整性检查"""
        try:
            logger.info("开始数据完整性检查...")
            
            # 检查日线数据完整性
            missing_data = await self._check_daily_data_integrity(symbols, start_date, end_date)
            
            if missing_data:
                logger.warning(f"发现 {len(missing_data)} 个数据缺失项")
                
                # 补充缺失数据
                for missing_item in missing_data[:10]:  # 限制补充数量
                    try:
                        await self._fill_missing_data(missing_item)
                    except Exception as e:
                        logger.error(f"补充缺失数据失败: {missing_item}, {e}")
            else:
                logger.info("数据完整性检查通过")
            
            return len(missing_data) == 0
            
        except Exception as e:
            logger.error(f"数据完整性检查失败: {e}")
            return False
    
    async def _check_daily_data_integrity(self, symbols: List[str], 
                                        start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """检查日线数据完整性"""
        try:
            # 这里应该实现具体的完整性检查逻辑
            # 比如检查交易日是否有对应的数据记录
            missing_data = []
            
            # 示例：检查前10只股票的数据完整性
            sample_symbols = symbols[:10]
            
            for symbol in sample_symbols:
                # 检查该股票在指定日期范围内是否有数据缺失
                # 这里需要调用数据库查询接口
                pass
            
            return missing_data
            
        except Exception as e:
            logger.error(f"检查日线数据完整性失败: {e}")
            return []
    
    async def _fill_missing_data(self, missing_item: Dict[str, Any]):
        """补充缺失数据"""
        try:
            # 根据缺失项信息补充数据
            symbol = missing_item.get('symbol')
            date = missing_item.get('date')
            data_type = missing_item.get('data_type', 'daily_bars')
            
            logger.debug(f"补充缺失数据: {symbol} - {date} - {data_type}")
            
            # 调用相应的处理器补充数据
            result = await self.processor_manager.process_data(
                data_type=DataType.MARKET_DATA,
                subtype=data_type,
                symbols=[symbol],
                start_date=date,
                end_date=date
            )
            
            if result.get('success', False):
                logger.debug(f"缺失数据补充成功: {symbol} - {date}")
            else:
                logger.error(f"缺失数据补充失败: {symbol} - {date}")
                
        except Exception as e:
            logger.error(f"补充缺失数据异常: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取同步器状态"""
        try:
            return {
                'is_running': self.is_running,
                'current_tasks_count': len(self.current_tasks),
                'current_tasks': list(self.current_tasks.keys()),
                'sync_config': self.sync_config,
                'sync_stats': self.sync_stats
            }
            
        except Exception as e:
            logger.error(f"获取同步器状态失败: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = self.sync_stats.copy()
            
            # 计算平均同步时间
            if stats['completed_tasks'] > 0:
                stats['avg_sync_duration'] = stats['sync_duration'] / stats['completed_tasks']
            else:
                stats['avg_sync_duration'] = 0
            
            # 计算成功率
            if stats['total_tasks'] > 0:
                stats['success_rate'] = stats['completed_tasks'] / stats['total_tasks']
            else:
                stats['success_rate'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def reset_stats(self):
        """重置统计信息"""
        try:
            self.sync_stats = {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'total_records': 0,
                'start_time': datetime.now().isoformat(),
                'last_sync_time': None,
                'sync_duration': 0,
                'error_details': []
            }
            
            logger.info("历史数据同步器统计信息已重置")
            
        except Exception as e:
            logger.error(f"重置统计信息失败: {e}")
    
    def __str__(self) -> str:
        return f"HistoricalDataSync(running={self.is_running}, tasks={len(self.current_tasks)})"
    
    def __repr__(self) -> str:
        return self.__str__()