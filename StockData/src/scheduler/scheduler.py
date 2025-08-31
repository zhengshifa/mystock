#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度器
负责管理和调度各种数据采集任务
"""

import sys
import os
import time
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import config
from utils import get_logger
from src.market_data import TickDataCollector, BarDataCollector, MarketDataAnalyzer
from src.fundamentals import FundamentalsDataCollector
from src.realtime import RealtimeDataCollector

# 获取日志记录器
logger = get_logger(__name__)


class StockDataInterface:
    """股票数据接口 - 统一管理各种数据采集器"""
    
    def __init__(self):
        """初始化股票数据接口"""
        self.tick_collector = None
        self.bar_collector = None
        self.fundamentals_collector = None
        self.realtime_collector = None
        self.market_analyzer = None
        
        self._init_collectors()
    
    def _init_collectors(self):
        """初始化各种数据采集器"""
        try:
            logger.info("初始化数据采集器...")
            
            # 初始化市场数据采集器
            self.tick_collector = TickDataCollector()
            self.bar_collector = BarDataCollector()
            self.market_analyzer = MarketDataAnalyzer()
            
            # 初始化基本面数据采集器
            self.fundamentals_collector = FundamentalsDataCollector()
            
            # 初始化实时数据采集器
            self.realtime_collector = RealtimeDataCollector()
            
            logger.info("所有数据采集器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化数据采集器失败: {e}")
            raise
    
    def collect_all_data(self, symbols: List[str], 
                         start_time: str = None, 
                         end_time: str = None,
                         save_to_db: bool = True) -> Dict[str, Any]:
        """采集所有类型的数据
        
        Args:
            symbols: 股票代码列表
            start_time: 开始时间
            end_time: 结束时间
            save_to_db: 是否保存到数据库
        
        Returns:
            采集结果统计
        """
        try:
            logger.info(f"开始采集所有类型数据: {symbols}")
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'symbols': symbols,
                'tick_data': {},
                'bar_data': {},
                'fundamentals_data': {},
                'realtime_data': {},
                'summary': {}
            }
            
            # 1. 采集Tick数据
            if self.tick_collector:
                logger.info("开始采集Tick数据...")
                tick_result = self.tick_collector.collect_and_save_tick_data(
                    symbols=symbols,
                    start_time=start_time,
                    end_time=end_time,
                    save_to_db=save_to_db,
                    show_summary=False
                )
                results['tick_data'] = tick_result
                logger.info(f"Tick数据采集完成: {tick_result}")
            
            # 2. 采集Bar数据
            if self.bar_collector:
                logger.info("开始采集Bar数据...")
                bar_result = self.bar_collector.collect_and_save_bars(
                    symbols=symbols,
                    start_time=start_time,
                    end_time=end_time,
                    save_to_db=save_to_db,
                    show_summary=False
                )
                results['bar_data'] = bar_result
                logger.info(f"Bar数据采集完成: {bar_result}")
            
            # 3. 采集基本面数据
            if self.fundamentals_collector:
                logger.info("开始采集基本面数据...")
                fundamentals_result = self.fundamentals_collector.collect_fundamentals_data(
                    symbols=symbols,
                    start_date=start_time,
                    end_date=end_time,
                    save_to_db=save_to_db
                )
                results['fundamentals_data'] = fundamentals_result
                logger.info(f"基本面数据采集完成: {fundamentals_result}")
            
            # 4. 采集实时数据
            if self.realtime_collector:
                logger.info("开始采集实时数据...")
                realtime_result = self.realtime_collector.collect_and_save(
                    symbols=symbols,
                    collection_name='current_quotes',
                    show_data=False
                )
                results['realtime_data'] = {
                    'success': realtime_result is not None,
                    'data_count': len(realtime_result) if realtime_result else 0
                }
                logger.info(f"实时数据采集完成: {results['realtime_data']}")
            
            # 生成摘要
            results['summary'] = self._generate_collection_summary(results)
            
            logger.info(f"所有数据采集完成: {results['summary']}")
            return results
            
        except Exception as e:
            logger.error(f"采集所有数据失败: {e}")
            return {}
    
    def _generate_collection_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成采集结果摘要
        
        Args:
            results: 采集结果
        
        Returns:
            摘要信息
        """
        try:
            summary = {
                'total_symbols': len(results.get('symbols', [])),
                'successful_collections': 0,
                'total_records': 0,
                'collection_status': {}
            }
            
            # 统计Tick数据
            tick_data = results.get('tick_data', {})
            if tick_data and tick_data.get('total_ticks', 0) > 0:
                summary['successful_collections'] += 1
                summary['total_records'] += tick_data.get('total_ticks', 0)
                summary['collection_status']['tick_data'] = 'success'
            else:
                summary['collection_status']['tick_data'] = 'failed'
            
            # 统计Bar数据
            bar_data = results.get('bar_data', {})
            if bar_data and bar_data.get('total_bars', 0) > 0:
                summary['successful_collections'] += 1
                summary['total_records'] += bar_data.get('total_bars', 0)
                summary['collection_status']['bar_data'] = 'success'
            else:
                summary['collection_status']['bar_data'] = 'failed'
            
            # 统计基本面数据
            fundamentals_data = results.get('fundamentals_data', {})
            if fundamentals_data and fundamentals_data.get('total_records', 0) > 0:
                summary['successful_collections'] += 1
                summary['total_records'] += fundamentals_data.get('total_records', 0)
                summary['collection_status']['fundamentals_data'] = 'success'
            else:
                summary['collection_status']['fundamentals_data'] = 'failed'
            
            # 统计实时数据
            realtime_data = results.get('realtime_data', {})
            if realtime_data and realtime_data.get('success', False):
                summary['successful_collections'] += 1
                summary['total_records'] += realtime_data.get('data_count', 0)
                summary['collection_status']['realtime_data'] = 'success'
            else:
                summary['collection_status']['realtime_data'] = 'failed'
            
            return summary
            
        except Exception as e:
            logger.error(f"生成采集摘要失败: {e}")
            return {}
    
    def close(self):
        """关闭所有采集器连接"""
        try:
            if self.tick_collector:
                self.tick_collector.close()
            if self.bar_collector:
                self.bar_collector.close()
            if self.fundamentals_collector:
                self.fundamentals_collector.disconnect()
            if self.realtime_collector:
                self.realtime_collector.close()
            
            logger.info("所有数据采集器连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭采集器连接失败: {e}")


class TaskScheduler:
    """任务调度器 - 管理定时任务"""
    
    def __init__(self):
        """初始化任务调度器"""
        self.data_interface = StockDataInterface()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_running = False
        
        # 从配置文件读取设置
        self.scheduler_config = config.scheduler
        self.stock_symbols = self.scheduler_config.stock_symbols or []
        
        logger.info("任务调度器初始化完成")
    
    def start_scheduler(self):
        """启动调度器"""
        try:
            if self.is_running:
                logger.warning("调度器已在运行中")
                return
            
            logger.info("启动任务调度器...")
            self.is_running = True
            
            # 设置定时任务
            self._setup_scheduled_tasks()
            
            # 启动调度循环
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止调度器...")
            self.stop_scheduler()
        except Exception as e:
            logger.error(f"调度器运行失败: {e}")
            self.stop_scheduler()
    
    def stop_scheduler(self):
        """停止调度器"""
        try:
            logger.info("正在停止任务调度器...")
            self.is_running = False
            
            # 关闭线程池
            if self.executor:
                self.executor.shutdown(wait=True)
            
            # 关闭数据接口
            if self.data_interface:
                self.data_interface.close()
            
            logger.info("任务调度器已停止")
            
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
    
    def _setup_scheduled_tasks(self):
        """设置定时任务"""
        try:
            # 市场开盘前任务（9:15）
            schedule.every().day.at("09:15").do(self._pre_market_task)
            
            # 市场开盘任务（9:30）
            schedule.every().day.at("09:30").do(self._market_open_task)
            
            # 午盘前任务（13:00）
            schedule.every().day.at("13:00").do(self._afternoon_pre_task)
            
            # 市场收盘任务（15:00）
            schedule.every().day.at("15:00").do(self._market_close_task)
            
            # 盘后数据整理任务（15:30）
            schedule.every().day.at("15:30").do(self._post_market_task)
            
            # 每日基本面数据采集任务（20:00）
            schedule.every().day.at("20:00").do(self._daily_fundamentals_task)
            
            # 每周历史数据补充任务（周日 02:00）
            schedule.every().sunday.at("02:00").do(self._weekly_history_task)
            
            logger.info("定时任务设置完成")
            
        except Exception as e:
            logger.error(f"设置定时任务失败: {e}")
    
    def _pre_market_task(self):
        """开盘前任务"""
        try:
            logger.info("执行开盘前任务...")
            
            # 获取最新基本面数据
            if self.data_interface.fundamentals_collector:
                self.data_interface.fundamentals_collector.collect_fundamentals_data(
                    symbols=self.stock_symbols,
                    save_to_db=True
                )
            
            # 获取最新Bar数据
            if self.data_interface.bar_collector:
                self.data_interface.bar_collector.collect_and_save_bars(
                    symbols=self.stock_symbols,
                    frequencies=['1d', '1h'],
                    save_to_db=True,
                    show_summary=False
                )
            
            logger.info("开盘前任务完成")
            
        except Exception as e:
            logger.error(f"执行开盘前任务失败: {e}")
    
    def _market_open_task(self):
        """市场开盘任务"""
        try:
            logger.info("执行市场开盘任务...")
            
            # 开始实时数据采集
            if self.data_interface.realtime_collector:
                self.data_interface.realtime_collector.collect_and_save(
                    symbols=self.stock_symbols,
                    collection_name='market_open_quotes',
                    show_data=False
                )
            
            logger.info("市场开盘任务完成")
            
        except Exception as e:
            logger.error(f"执行市场开盘任务失败: {e}")
    
    def _afternoon_pre_task(self):
        """午盘前任务"""
        try:
            logger.info("执行午盘前任务...")
            
            # 获取上午的实时数据摘要
            if self.data_interface.realtime_collector:
                market_overview = self.data_interface.realtime_collector.get_market_overview(
                    self.stock_symbols
                )
                logger.info(f"上午市场概览: {market_overview}")
            
            logger.info("午盘前任务完成")
            
        except Exception as e:
            logger.error(f"执行午盘前任务失败: {e}")
    
    def _market_close_task(self):
        """市场收盘任务"""
        try:
            logger.info("执行市场收盘任务...")
            
            # 获取收盘实时数据
            if self.data_interface.realtime_collector:
                self.data_interface.realtime_collector.collect_and_save(
                    symbols=self.stock_symbols,
                    collection_name='market_close_quotes',
                    show_data=False
                )
            
            # 获取当日Bar数据
            if self.data_interface.bar_collector:
                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                start_time = datetime.now().strftime('%Y-%m-%d 09:30:00')
                
                self.data_interface.bar_collector.collect_and_save_bars(
                    symbols=self.stock_symbols,
                    frequencies=['1m', '5m', '15m', '30m', '1h'],
                    start_time=start_time,
                    end_time=end_time,
                    save_to_db=True,
                    show_summary=False
                )
            
            logger.info("市场收盘任务完成")
            
        except Exception as e:
            logger.error(f"执行市场收盘任务失败: {e}")
    
    def _post_market_task(self):
        """盘后数据整理任务"""
        try:
            logger.info("执行盘后数据整理任务...")
            
            # 生成市场分析报告
            if self.data_interface.market_analyzer:
                # 获取当日Tick数据进行分析
                if self.data_interface.tick_collector:
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    start_time = datetime.now().strftime('%Y-%m-%d 09:30:00')
                    
                    for symbol in self.stock_symbols[:5]:  # 只分析前5只股票
                        tick_data = self.data_interface.tick_collector.get_history_tick_data(
                            symbol, start_time, end_time
                        )
                        if tick_data:
                            analysis = self.data_interface.market_analyzer.analyze_tick_data(tick_data)
                            logger.info(f"{symbol} Tick数据分析完成: {analysis}")
            
            logger.info("盘后数据整理任务完成")
            
        except Exception as e:
            logger.error(f"执行盘后数据整理任务失败: {e}")
    
    def _daily_fundamentals_task(self):
        """每日基本面数据采集任务"""
        try:
            logger.info("执行每日基本面数据采集任务...")
            
            if self.data_interface.fundamentals_collector:
                # 采集最近一年的基本面数据
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                
                self.data_interface.fundamentals_collector.collect_fundamentals_data(
                    symbols=self.stock_symbols,
                    start_date=start_date,
                    end_date=end_date,
                    save_to_db=True
                )
            
            logger.info("每日基本面数据采集任务完成")
            
        except Exception as e:
            logger.error(f"执行每日基本面数据采集任务失败: {e}")
    
    def _weekly_history_task(self):
        """每周历史数据补充任务"""
        try:
            logger.info("执行每周历史数据补充任务...")
            
            # 补充历史Tick数据
            if self.data_interface.tick_collector:
                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                start_time = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                
                self.data_interface.tick_collector.collect_and_save_tick_data(
                    symbols=self.stock_symbols,
                    start_time=start_time,
                    end_time=end_time,
                    save_to_db=True,
                    show_summary=False
                )
            
            # 补充历史Bar数据
            if self.data_interface.bar_collector:
                end_time = datetime.now().strftime('%Y-%m-%d')
                start_time = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                self.data_interface.bar_collector.collect_and_save_bars(
                    symbols=self.stock_symbols,
                    frequencies=['1d', '1h'],
                    start_time=start_time,
                    end_time=end_time,
                    save_to_db=True,
                    show_summary=False
                )
            
            logger.info("每周历史数据补充任务完成")
            
        except Exception as e:
            logger.error(f"执行每周历史数据补充任务失败: {e}")
    
    def run_manual_task(self, task_type: str, symbols: List[str] = None, **kwargs) -> Dict[str, Any]:
        """运行手动任务
        
        Args:
            task_type: 任务类型 ('tick', 'bar', 'fundamentals', 'realtime', 'all')
            symbols: 股票代码列表，如果为None则使用配置的股票代码
            **kwargs: 其他参数
        
        Returns:
            任务执行结果
        """
        try:
            if not symbols:
                symbols = self.stock_symbols
            
            if not symbols:
                logger.warning("没有指定股票代码")
                return {}
            
            logger.info(f"开始执行手动任务: {task_type}, 股票: {symbols}")
            
            if task_type == 'tick':
                return self._run_tick_task(symbols, **kwargs)
            elif task_type == 'bar':
                return self._run_bar_task(symbols, **kwargs)
            elif task_type == 'fundamentals':
                return self._run_fundamentals_task(symbols, **kwargs)
            elif task_type == 'realtime':
                return self._run_realtime_task(symbols, **kwargs)
            elif task_type == 'all':
                return self.data_interface.collect_all_data(symbols, **kwargs)
            else:
                logger.error(f"不支持的任务类型: {task_type}")
                return {}
                
        except Exception as e:
            logger.error(f"执行手动任务失败: {e}")
            return {}
    
    def _run_tick_task(self, symbols: List[str], **kwargs) -> Dict[str, Any]:
        """运行Tick数据采集任务"""
        if not self.data_interface.tick_collector:
            return {}
        
        start_time = kwargs.get('start_time', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
        end_time = kwargs.get('end_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return self.data_interface.tick_collector.collect_and_save_tick_data(
            symbols=symbols,
            start_time=start_time,
            end_time=end_time,
            save_to_db=True,
            show_summary=True
        )
    
    def _run_bar_task(self, symbols: List[str], **kwargs) -> Dict[str, Any]:
        """运行Bar数据采集任务"""
        if not self.data_interface.bar_collector:
            return {}
        
        start_time = kwargs.get('start_time', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_time = kwargs.get('end_time', datetime.now().strftime('%Y-%m-%d'))
        frequencies = kwargs.get('frequencies', ['1d', '1h', '30m', '15m', '5m'])
        
        return self.data_interface.bar_collector.collect_and_save_bars(
            symbols=symbols,
            frequencies=frequencies,
            start_time=start_time,
            end_time=end_time,
            save_to_db=True,
            show_summary=True
        )
    
    def _run_fundamentals_task(self, symbols: List[str], **kwargs) -> Dict[str, Any]:
        """运行基本面数据采集任务"""
        if not self.data_interface.fundamentals_collector:
            return {}
        
        start_date = kwargs.get('start_date', (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
        end_date = kwargs.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        return self.data_interface.fundamentals_collector.collect_fundamentals_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            save_to_db=True
        )
    
    def _run_realtime_task(self, symbols: List[str], **kwargs) -> Dict[str, Any]:
        """运行实时数据采集任务"""
        if not self.data_interface.realtime_collector:
            return {}
        
        collection_name = kwargs.get('collection_name', 'manual_realtime_quotes')
        
        return self.data_interface.realtime_collector.collect_and_save(
            symbols=symbols,
            collection_name=collection_name,
            show_data=True
        )


def main():
    """主函数 - 演示调度器功能"""
    try:
        print("🚀 股票数据采集调度系统")
        print("=" * 50)
        
        # 创建调度器
        scheduler = TaskScheduler()
        
        # 显示配置信息
        print(f"配置的股票代码: {scheduler.stock_symbols}")
        print(f"调度器配置: {scheduler.scheduler_config}")
        
        # 运行手动任务示例
        print("\n1️⃣ 运行手动任务示例...")
        
        # 采集实时数据
        print("\n--- 采集实时数据 ---")
        realtime_result = scheduler.run_manual_task('realtime', symbols=scheduler.stock_symbols[:3])
        if realtime_result:
            print(f"实时数据采集结果: {realtime_result}")
        
        # 采集Bar数据
        print("\n--- 采集Bar数据 ---")
        bar_result = scheduler.run_manual_task('bar', symbols=scheduler.stock_symbols[:3])
        if bar_result:
            print(f"Bar数据采集结果: {bar_result}")
        
        # 采集基本面数据
        print("\n--- 采集基本面数据 ---")
        fundamentals_result = scheduler.run_manual_task('fundamentals', symbols=scheduler.stock_symbols[:2])
        if fundamentals_result:
            print(f"基本面数据采集结果: {fundamentals_result}")
        
        print("\n🎉 手动任务执行完成！")
        
        # 询问是否启动调度器
        print("\n是否启动自动调度器？(y/n): ", end="")
        user_input = input().strip().lower()
        
        if user_input == 'y':
            print("\n启动自动调度器...")
            print("按 Ctrl+C 停止调度器")
            scheduler.start_scheduler()
        else:
            print("\n调度器未启动，程序结束")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'scheduler' in locals():
            scheduler.stop_scheduler()


if __name__ == "__main__":
    main()
