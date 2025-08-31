#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据采集系统主入口
整合所有重构后的模块，提供统一的接口
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import config
from utils import get_logger
from src.scheduler import TaskScheduler, StockDataInterface
from src.market_data import TickDataCollector, BarDataCollector, MarketDataAnalyzer
from src.fundamentals import FundamentalsDataCollector
from src.realtime import RealtimeDataCollector

# 获取日志记录器
logger = get_logger(__name__)


class StockDataSystem:
    """股票数据采集系统 - 主控制器"""
    
    def __init__(self):
        """初始化系统"""
        self.scheduler = None
        self.data_interface = None
        self.stock_symbols = config.scheduler.stock_symbols or []
        
        logger.info("股票数据采集系统初始化完成")
    
    def initialize(self):
        """初始化系统组件"""
        try:
            logger.info("正在初始化系统组件...")
            
            # 初始化数据接口
            self.data_interface = StockDataInterface()
            
            # 初始化调度器
            self.scheduler = TaskScheduler()
            
            logger.info("系统组件初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False
    
    def run_collection_task(self, task_type: str, symbols: List[str] = None, **kwargs) -> Dict[str, Any]:
        """运行数据采集任务
        
        Args:
            task_type: 任务类型
            symbols: 股票代码列表
            **kwargs: 其他参数
        
        Returns:
            任务执行结果
        """
        try:
            if not self.scheduler:
                logger.error("调度器未初始化")
                return {}
            
            if not symbols:
                symbols = self.stock_symbols
            
            if not symbols:
                logger.warning("没有指定股票代码")
                return {}
            
            logger.info(f"开始执行{task_type}任务，股票: {symbols}")
            
            result = self.scheduler.run_manual_task(task_type, symbols, **kwargs)
            
            logger.info(f"{task_type}任务执行完成")
            return result
            
        except Exception as e:
            logger.error(f"执行{task_type}任务失败: {e}")
            return {}
    
    def start_scheduler(self):
        """启动自动调度器"""
        try:
            if not self.scheduler:
                logger.error("调度器未初始化")
                return False
            
            logger.info("启动自动调度器...")
            self.scheduler.start_scheduler()
            return True
            
        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            return False
    
    def stop_scheduler(self):
        """停止自动调度器"""
        try:
            if self.scheduler:
                self.scheduler.stop_scheduler()
                logger.info("调度器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'system_status': 'running',
                'stock_symbols_count': len(self.stock_symbols),
                'stock_symbols': self.stock_symbols[:5],  # 只显示前5个
                'scheduler_running': self.scheduler.is_running if self.scheduler else False,
                'data_interface_ready': self.data_interface is not None
            }
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {'system_status': 'error', 'error': str(e)}
    
    def run_demo(self):
        """运行演示程序"""
        try:
            print("🚀 股票数据采集系统演示")
            print("=" * 50)
            
            # 显示系统状态
            status = self.get_system_status()
            print(f"系统状态: {status['system_status']}")
            print(f"配置股票数量: {status['stock_symbols_count']}")
            print(f"示例股票: {', '.join(status['stock_symbols'])}")
            
            # 运行各种采集任务演示
            demo_symbols = self.stock_symbols[:3]  # 只演示前3只股票
            
            print("\n1️⃣ 演示实时数据采集...")
            realtime_result = self.run_collection_task('realtime', demo_symbols)
            if realtime_result:
                print(f"✅ 实时数据采集成功: {len(realtime_result)}条数据")
            else:
                print("❌ 实时数据采集失败")
            
            print("\n2️⃣ 演示Bar数据采集...")
            bar_result = self.run_collection_task('bar', demo_symbols)
            if bar_result:
                print(f"✅ Bar数据采集成功: {bar_result.get('total_bars', 0)}条数据")
            else:
                print("❌ Bar数据采集失败")
            
            print("\n3️⃣ 演示基本面数据采集...")
            fundamentals_result = self.run_collection_task('fundamentals', demo_symbols[:2])
            if fundamentals_result:
                print(f"✅ 基本面数据采集成功: {fundamentals_result.get('total_records', 0)}条数据")
            else:
                print("❌ 基本面数据采集失败")
            
            print("\n🎉 演示程序执行完成！")
            
        except Exception as e:
            logger.error(f"演示程序执行失败: {e}")
            print(f"演示程序执行失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票数据采集系统')
    parser.add_argument('--task', choices=['tick', 'bar', 'fundamentals', 'realtime', 'all', 'demo', 'scheduler'],
                       help='要执行的任务类型')
    parser.add_argument('--symbols', nargs='+', help='股票代码列表')
    parser.add_argument('--start-time', help='开始时间 (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end-time', help='结束时间 (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--frequencies', nargs='+', default=['1d', '1h'],
                       help='Bar数据频率列表')
    
    args = parser.parse_args()
    
    try:
        # 创建系统实例
        system = StockDataSystem()
        
        # 初始化系统
        if not system.initialize():
            print("❌ 系统初始化失败")
            return
        
        # 根据参数执行相应任务
        if args.task == 'demo':
            # 运行演示程序
            system.run_demo()
            
        elif args.task == 'scheduler':
            # 启动调度器
            print("🚀 启动自动调度器...")
            print("按 Ctrl+C 停止调度器")
            system.start_scheduler()
            
        elif args.task in ['tick', 'bar', 'fundamentals', 'realtime', 'all']:
            # 执行数据采集任务
            symbols = args.symbols or system.stock_symbols
            
            if not symbols:
                print("❌ 没有指定股票代码")
                return
            
            print(f"🚀 开始执行{args.task}任务...")
            print(f"目标股票: {symbols}")
            
            # 准备任务参数
            task_kwargs = {}
            if args.start_time:
                task_kwargs['start_time'] = args.start_time
            if args.end_time:
                task_kwargs['end_time'] = args.end_time
            if args.frequencies and args.task == 'bar':
                task_kwargs['frequencies'] = args.frequencies
            
            # 执行任务
            result = system.run_collection_task(args.task, symbols, **task_kwargs)
            
            if result:
                print(f"✅ {args.task}任务执行成功")
                print(f"结果摘要: {result}")
            else:
                print(f"❌ {args.task}任务执行失败")
                
        else:
            # 显示帮助信息
            print("🚀 股票数据采集系统")
            print("=" * 50)
            print("可用命令:")
            print("  --task demo         运行演示程序")
            print("  --task scheduler    启动自动调度器")
            print("  --task tick         采集Tick数据")
            print("  --task bar          采集Bar数据")
            print("  --task fundamentals 采集基本面数据")
            print("  --task realtime     采集实时数据")
            print("  --task all          采集所有类型数据")
            print("\n示例:")
            print("  python src/main.py --task demo")
            print("  python src/main.py --task tick --symbols SZSE.000001 SZSE.000002")
            print("  python src/main.py --task bar --symbols SHSE.600000 --frequencies 1d 1h")
            print("  python src/main.py --task scheduler")
    
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在关闭系统...")
        if 'system' in locals():
            system.stop_scheduler()
        print("系统已关闭")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'system' in locals():
            system.stop_scheduler()


if __name__ == "__main__":
    main()
