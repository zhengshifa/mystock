#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理器管理器

统一管理所有数据处理器，提供:
- 处理器注册和获取
- 批量数据处理
- 处理器状态监控
- 错误处理和重试
- 性能统计
"""

import asyncio
from typing import Dict, Any, List, Optional, Type, Union
from datetime import datetime, timedelta
from loguru import logger
from collections import defaultdict
import time

from .base_processor import BaseDataProcessor, DataProcessingError
from .stock_info_processor import StockInfoProcessor
from .market_data_processor import MarketDataProcessor
from .financial_data_processor import FinancialDataProcessor
from .other_data_processor import OtherDataProcessor
from ..database import DataType


class DataProcessorManager:
    """数据处理器管理器"""
    
    def __init__(self, gm_client, repository_manager, config):
        self.gm_client = gm_client
        self.repository_manager = repository_manager
        self.config = config
        
        # 处理器注册表
        self._processors: Dict[DataType, BaseDataProcessor] = {}
        self._processor_classes: Dict[DataType, Type[BaseDataProcessor]] = {
            DataType.STOCK_INFO: StockInfoProcessor,
            DataType.MARKET_DATA: MarketDataProcessor,
            DataType.FINANCIAL_DATA: FinancialDataProcessor,
            DataType.OTHER_DATA: OtherDataProcessor
        }
        
        # 管理器配置
        self.max_concurrent_processors = config.get('max_concurrent_processors', 3)
        self.processor_timeout = config.get('processor_timeout', 300)  # 5分钟超时
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_delay = config.get('retry_delay', 5)  # 重试延迟(秒)
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'processing_time': 0.0,
            'processor_stats': defaultdict(lambda: {
                'processed': 0,
                'success': 0,
                'error': 0,
                'avg_time': 0.0
            })
        }
        
        # 运行状态
        self.is_running = False
        self._running_tasks = set()
        
        logger.info(f"数据处理器管理器初始化完成，支持处理器类型: {list(self._processor_classes.keys())}")
    
    async def initialize(self):
        """初始化管理器"""
        try:
            logger.info("初始化数据处理器管理器...")
            
            # 初始化所有处理器
            for data_type, processor_class in self._processor_classes.items():
                try:
                    processor_config = self.config.get('processors', {}).get(data_type.value, {})
                    
                    # 为不同数据处理器添加相应配置
                    sync_config = self.config.get('sync', {})
                    realtime_config = sync_config.get('realtime_sync', {})
                    symbols = realtime_config.get('symbols', [])
                    
                    if data_type.value == 'market_data':
                        processor_config['symbols'] = symbols
                        processor_config['bar_periods'] = ['1m', '5m', '15m', '30m', '1h', '1d']
                        processor_config['enable_realtime'] = True
                        processor_config['enable_bar'] = True
                    elif data_type.value == 'stock_info':
                        processor_config['symbols'] = symbols
                        processor_config['exchanges'] = ['SZSE', 'SHSE']
                        processor_config['security_types'] = ['STOCK']
                    elif data_type.value == 'financial_data':
                        processor_config['symbols'] = symbols
                        processor_config['data_types'] = ['income_statement', 'balance_sheet', 'cash_flow', 'financial_indicator']
                    elif data_type.value == 'other_data':
                        processor_config['index_symbols'] = ['000001.SH', '000300.SH', '000905.SH', '399001.SZ', '399006.SZ', '399005.SZ']
                    
                    processor = processor_class(
                        self.gm_client,
                        self.repository_manager,
                        processor_config
                    )
                    
                    self._processors[data_type] = processor
                    logger.info(f"初始化处理器: {processor.processor_name}")
                    
                except Exception as e:
                    logger.error(f"初始化处理器 {data_type} 失败: {e}")
                    continue
            
            self.is_running = True
            logger.info(f"数据处理器管理器初始化完成，已注册 {len(self._processors)} 个处理器")
            
        except Exception as e:
            logger.error(f"初始化数据处理器管理器失败: {e}")
            raise
    
    async def shutdown(self):
        """关闭管理器"""
        try:
            logger.info("关闭数据处理器管理器...")
            self.is_running = False
            
            # 等待所有运行中的任务完成
            if self._running_tasks:
                logger.info(f"等待 {len(self._running_tasks)} 个运行中的任务完成...")
                await asyncio.gather(*self._running_tasks, return_exceptions=True)
            
            # 关闭所有处理器
            for processor in self._processors.values():
                try:
                    if hasattr(processor, 'shutdown'):
                        await processor.shutdown()
                except Exception as e:
                    logger.warning(f"关闭处理器失败: {e}")
            
            self._processors.clear()
            logger.info("数据处理器管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭数据处理器管理器失败: {e}")
    
    def get_processor(self, data_type: DataType) -> Optional[BaseDataProcessor]:
        """获取指定类型的处理器"""
        return self._processors.get(data_type)
    
    def list_processors(self) -> List[BaseDataProcessor]:
        """列出所有处理器"""
        return list(self._processors.values())
    
    async def process_data(self, data_type: DataType, **kwargs) -> bool:
        """处理指定类型的数据"""
        try:
            if not self.is_running:
                logger.error("数据处理器管理器未运行")
                return False
            
            processor = self.get_processor(data_type)
            if not processor:
                logger.error(f"未找到数据类型 {data_type} 的处理器")
                return False
            
            start_time = time.time()
            
            # 执行处理
            success = await self._execute_with_retry(processor, **kwargs)
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_stats(data_type, success, processing_time)
            
            return success
            
        except Exception as e:
            logger.error(f"处理数据失败: {data_type}, 错误: {e}")
            self._update_stats(data_type, False, 0)
            return False
    
    async def process_multiple_data(self, data_requests: List[Dict[str, Any]]) -> Dict[DataType, bool]:
        """批量处理多种类型的数据"""
        try:
            if not self.is_running:
                logger.error("数据处理器管理器未运行")
                return {}
            
            logger.info(f"开始批量处理 {len(data_requests)} 个数据请求")
            
            # 创建处理任务
            tasks = []
            data_types = []
            
            for request in data_requests:
                data_type = request.get('data_type')
                if not data_type or data_type not in self._processors:
                    logger.warning(f"跳过无效的数据请求: {request}")
                    continue
                
                # 移除data_type，剩余参数传给处理器
                kwargs = {k: v for k, v in request.items() if k != 'data_type'}
                
                task = self._create_processing_task(data_type, **kwargs)
                tasks.append(task)
                data_types.append(data_type)
            
            if not tasks:
                logger.warning("没有有效的数据处理任务")
                return {}
            
            # 限制并发数量
            semaphore = asyncio.Semaphore(self.max_concurrent_processors)
            
            async def limited_task(task, data_type):
                async with semaphore:
                    return data_type, await task
            
            # 执行所有任务
            results = await asyncio.gather(
                *[limited_task(task, dt) for task, dt in zip(tasks, data_types)],
                return_exceptions=True
            )
            
            # 处理结果
            result_dict = {}
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"批量处理任务异常: {result}")
                    continue
                
                data_type, success = result
                result_dict[data_type] = success
            
            success_count = sum(1 for success in result_dict.values() if success)
            logger.info(f"批量处理完成: 成功 {success_count}/{len(result_dict)}")
            
            return result_dict
            
        except Exception as e:
            logger.error(f"批量处理数据失败: {e}")
            return {}
    
    async def _create_processing_task(self, data_type: DataType, **kwargs):
        """创建处理任务"""
        try:
            processor = self.get_processor(data_type)
            if not processor:
                return False
            
            # 添加超时控制
            return await asyncio.wait_for(
                self._execute_with_retry(processor, **kwargs),
                timeout=self.processor_timeout
            )
            
        except asyncio.TimeoutError:
            logger.error(f"处理器 {data_type} 执行超时")
            return False
        except Exception as e:
            logger.error(f"创建处理任务失败: {data_type}, 错误: {e}")
            return False
    
    async def _execute_with_retry(self, processor: BaseDataProcessor, **kwargs) -> bool:
        """带重试的执行处理器"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"执行处理器 {processor.processor_name}, 尝试 {attempt + 1}/{self.retry_attempts}")
                
                success = await processor.run(**kwargs)
                
                if success:
                    if attempt > 0:
                        logger.info(f"处理器 {processor.processor_name} 重试成功")
                    return True
                else:
                    logger.warning(f"处理器 {processor.processor_name} 执行失败")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"处理器 {processor.processor_name} 执行异常: {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))  # 递增延迟
        
        logger.error(f"处理器 {processor.processor_name} 重试 {self.retry_attempts} 次后仍然失败")
        if last_error:
            logger.error(f"最后一次错误: {last_error}")
        
        return False
    
    def _update_stats(self, data_type: DataType, success: bool, processing_time: float):
        """更新统计信息"""
        try:
            # 更新总体统计
            self.stats['total_processed'] += 1
            if success:
                self.stats['success_count'] += 1
            else:
                self.stats['error_count'] += 1
            self.stats['processing_time'] += processing_time
            
            # 更新处理器统计
            processor_stats = self.stats['processor_stats'][data_type.value]
            processor_stats['processed'] += 1
            if success:
                processor_stats['success'] += 1
            else:
                processor_stats['error'] += 1
            
            # 计算平均处理时间
            if processor_stats['processed'] > 0:
                total_time = processor_stats.get('total_time', 0) + processing_time
                processor_stats['total_time'] = total_time
                processor_stats['avg_time'] = total_time / processor_stats['processed']
            
        except Exception as e:
            logger.warning(f"更新统计信息失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = self.stats.copy()
            
            # 计算总体成功率
            if stats['total_processed'] > 0:
                stats['success_rate'] = stats['success_count'] / stats['total_processed']
                stats['avg_processing_time'] = stats['processing_time'] / stats['total_processed']
            else:
                stats['success_rate'] = 0.0
                stats['avg_processing_time'] = 0.0
            
            # 计算各处理器成功率
            for processor_name, processor_stats in stats['processor_stats'].items():
                if processor_stats['processed'] > 0:
                    processor_stats['success_rate'] = processor_stats['success'] / processor_stats['processed']
                else:
                    processor_stats['success_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def reset_stats(self):
        """重置统计信息"""
        try:
            self.stats = {
                'total_processed': 0,
                'success_count': 0,
                'error_count': 0,
                'processing_time': 0.0,
                'processor_stats': defaultdict(lambda: {
                    'processed': 0,
                    'success': 0,
                    'error': 0,
                    'avg_time': 0.0
                })
            }
            logger.info("统计信息已重置")
            
        except Exception as e:
            logger.error(f"重置统计信息失败: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                'manager_status': 'running' if self.is_running else 'stopped',
                'processor_count': len(self._processors),
                'running_tasks': len(self._running_tasks),
                'processors': {}
            }
            
            # 检查各处理器状态
            for data_type, processor in self._processors.items():
                try:
                    processor_health = {
                        'name': processor.processor_name,
                        'status': 'healthy',
                        'last_run': getattr(processor, 'last_run_time', None)
                    }
                    
                    # 如果处理器有健康检查方法，调用它
                    if hasattr(processor, 'health_check'):
                        processor_health.update(await processor.health_check())
                    
                    health_status['processors'][data_type.value] = processor_health
                    
                except Exception as e:
                    health_status['processors'][data_type.value] = {
                        'name': processor.processor_name,
                        'status': 'error',
                        'error': str(e)
                    }
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    # ==================== 便捷方法 ====================
    
    async def update_stock_list(self) -> bool:
        """更新股票列表"""
        return await self.process_data(DataType.STOCK_INFO, data_subtype='stock_list')
    
    async def update_trading_calendar(self) -> bool:
        """更新交易日历"""
        return await self.process_data(DataType.STOCK_INFO, data_subtype='trading_calendar')
    
    async def update_realtime_quotes(self, symbols: Optional[List[str]] = None) -> bool:
        """更新实时行情"""
        return await self.process_data(
            DataType.MARKET_DATA, 
            data_subtype='realtime_quote',
            symbols=symbols
        )
    
    async def update_daily_bars(self, symbols: Optional[List[str]] = None,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> bool:
        """更新日线数据"""
        return await self.process_data(
            DataType.MARKET_DATA,
            data_subtype='bar_data',
            symbols=symbols,
            frequency='1d',
            start_date=start_date,
            end_date=end_date
        )
    
    async def update_financial_data(self, symbols: Optional[List[str]] = None,
                                   data_type: str = 'income_statement') -> bool:
        """更新财务数据"""
        return await self.process_data(
            DataType.FINANCIAL_DATA,
            data_subtype='financial_data',
            symbols=symbols,
            financial_data_type=data_type
        )
    
    async def update_index_constituents(self, index_symbols: Optional[List[str]] = None) -> bool:
        """更新指数成分股"""
        return await self.process_data(
            DataType.OTHER_DATA,
            data_subtype='index_constituent',
            index_symbols=index_symbols
        )
    
    async def run_full_update(self) -> Dict[str, bool]:
        """运行完整更新"""
        try:
            logger.info("开始运行完整数据更新...")
            
            # 定义更新任务
            update_tasks = [
                {'data_type': DataType.STOCK_INFO, 'data_subtype': 'stock_list'},
                {'data_type': DataType.STOCK_INFO, 'data_subtype': 'trading_calendar'},
                {'data_type': DataType.MARKET_DATA, 'data_subtype': 'realtime_quote'},
                {'data_type': DataType.OTHER_DATA, 'data_subtype': 'index_constituent'}
            ]
            
            # 执行批量更新
            results = await self.process_multiple_data(update_tasks)
            
            success_count = sum(1 for success in results.values() if success)
            logger.info(f"完整数据更新完成: 成功 {success_count}/{len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"运行完整更新失败: {e}")
            return {}
    
    def __str__(self) -> str:
        return f"DataProcessorManager(processors={len(self._processors)}, running={self.is_running})"
    
    def __repr__(self) -> str:
        return self.__str__()