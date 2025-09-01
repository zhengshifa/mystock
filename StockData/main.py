#!/usr/bin/env python3
"""
股票数据收集器主程序
使用掘金量化SDK获取股票数据并存储到MongoDB
支持实时调度和增量同步两种模式
"""
import sys
import signal
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from src.config.settings import get_settings
from src.utils.logger import setup_logger
from src.utils.helpers import create_directories
from src.scheduler.data_scheduler import DataScheduler
from src.scheduler.incremental_sync import get_incremental_sync_manager
from src.utils.logger import get_logger


class StockDataCollector:
    """股票数据收集器主类"""
    
    def __init__(self):
        """初始化主程序"""
        self.logger = get_logger("Main")
        self.scheduler = None
        self.sync_manager = None
        self.is_running = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        self.logger.info(f"收到信号 {signum}，正在关闭程序...")
        self.stop()
        sys.exit(0)
    
    def initialize(self) -> None:
        """初始化程序"""
        try:
            self.logger.info("正在初始化股票数据收集器...")
            
            # 创建必要的目录
            create_directories("logs", "data", "config")
            
            # 设置日志系统
            setup_logger()
            
            # 设置代理（如果需要）
            settings = get_settings()
            settings.setup_proxy()
            
            self.logger.info("程序初始化完成")
            
        except Exception as e:
            self.logger.error(f"程序初始化失败: {e}")
            raise
    
    def start(self) -> None:
        """启动程序"""
        if self.is_running:
            self.logger.warning("程序已在运行中")
            return
        
        try:
            self.logger.info("启动股票数据收集器...")
            
            # 创建并启动调度器
            self.scheduler = DataScheduler()
            self.scheduler.start()
            
            self.is_running = True
            self.logger.info("股票数据收集器启动成功")
            
            # 保持程序运行
            self._keep_alive()
            
        except Exception as e:
            self.logger.error(f"启动程序失败: {e}")
            raise
    
    def start_incremental_sync(self, frequency: str, start_date: str, 
                              end_date: str = None, symbols: str = None, 
                              force_sync: bool = False) -> None:
        """启动增量同步模式"""
        try:
            self.logger.info("启动增量同步模式...")
            
            # 初始化增量同步管理器
            self.sync_manager = get_incremental_sync_manager()
            
            # 解析股票代码
            if symbols:
                symbol_list = symbols.split(',')
            else:
                # 从配置获取默认股票列表
                from src.config.scheduler_config import get_scheduler_config
                scheduler_config = get_scheduler_config()
                symbol_list = scheduler_config.get_stock_symbols()
            
            # 设置默认结束日期
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            self.logger.info(f"增量同步配置:")
            self.logger.info(f"  频率: {frequency}")
            self.logger.info(f"  时间范围: {start_date} 到 {end_date}")
            self.logger.info(f"  股票数量: {len(symbol_list)} 只")
            self.logger.info(f"  强制同步: {force_sync}")
            
            # 执行增量同步
            result = self.sync_manager.sync_data_range(
                symbols=symbol_list,
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                force_sync=force_sync
            )
            
            # 显示同步结果
            self._display_sync_result(result)
            
            # 同步完成后关闭
            self.stop()
            
        except Exception as e:
            self.logger.error(f"增量同步失败: {e}")
            raise
    
    def _display_sync_result(self, result: dict) -> None:
        """显示同步结果"""
        print("\n" + "=" * 60)
        print("📊 增量同步结果")
        print("=" * 60)
        
        if result.get("status") == "completed":
            print(f"✅ 状态: 完成")
            print(f"🆔 任务ID: {result.get('sync_id', 'N/A')}")
            print(f"📈 股票数量: {result.get('symbols_count', 0)} 只")
            print(f"✅ 成功: {result.get('success_count', 0)} 只")
            print(f"❌ 失败: {result.get('failed_count', 0)} 只")
            print(f"📊 总记录数: {result.get('total_records', 0)} 条")
            print(f"⏱️ 频率: {result.get('frequency', 'N/A')}")
            print(f"📅 时间范围: {result.get('start_date', 'N/A')} 到 {result.get('end_date', 'N/A')}")
            print(f"🕐 完成时间: {result.get('completed_at', 'N/A')}")
            
            if result.get('failed_symbols'):
                print(f"\n❌ 失败的股票:")
                for symbol in result['failed_symbols']:
                    print(f"  - {symbol}")
                    
        else:
            print(f"❌ 状态: 失败")
            print(f"🆔 任务ID: {result.get('sync_id', 'N/A')}")
            print(f"❌ 错误: {result.get('error', 'N/A')}")
            print(f"📈 股票数量: {result.get('symbols_count', 0)} 只")
            print(f"⏱️ 频率: {result.get('frequency', 'N/A')}")
            print(f"📅 时间范围: {result.get('start_date', 'N/A')} 到 {result.get('end_date', 'N/A')}")
    
    def stop(self) -> None:
        """停止程序"""
        if not self.is_running and not self.sync_manager:
            self.logger.warning("程序未在运行")
            return
        
        try:
            self.logger.info("正在停止股票数据收集器...")
            
            # 停止调度器
            if self.scheduler:
                self.scheduler.close()
                self.scheduler = None
            
            # 关闭增量同步管理器
            if self.sync_manager:
                self.sync_manager.close()
                self.sync_manager = None
            
            self.is_running = False
            self.logger.info("股票数据收集器已停止")
            
        except Exception as e:
            self.logger.error(f"停止程序失败: {e}")
    
    def _keep_alive(self) -> None:
        """保持程序运行"""
        try:
            self.logger.info("程序正在运行，按 Ctrl+C 停止...")
            
            while self.is_running:
                # 主循环，保持程序运行
                import time
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号")
        except Exception as e:
            self.logger.error(f"主循环异常: {e}")
        finally:
            self.stop()


def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description="股票数据收集器 - 支持实时调度和增量同步",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 添加运行模式选择
    parser.add_argument('--mode', choices=['scheduler', 'sync'], default='scheduler',
                       help='运行模式: scheduler(实时调度) 或 sync(增量同步)')
    
    # 增量同步相关参数
    parser.add_argument('--frequency', choices=['1m', '5m', '15m', '1h', '1d'],
                       help='数据频率 (增量同步模式必需)')
    parser.add_argument('--start-date',
                       help='开始日期 YYYY-MM-DD (增量同步模式必需)')
    parser.add_argument('--end-date',
                       help='结束日期 YYYY-MM-DD (增量同步模式默认为今天)')
    parser.add_argument('--symbols',
                       help='股票代码列表，用逗号分隔 (增量同步模式可选)')
    parser.add_argument('--force', action='store_true',
                       help='强制重新同步 (增量同步模式)')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    try:
        # 创建主程序实例
        collector = StockDataCollector()
        
        # 初始化程序
        collector.initialize()
        
        if args.mode == 'sync':
            # 增量同步模式
            if not args.frequency or not args.start_date:
                print("❌ 增量同步模式需要指定 --frequency 和 --start-date 参数")
                print("\n示例:")
                print("  uv run python main.py --mode sync --frequency 1m --start-date 2024-01-01")
                print("  uv run python main.py --mode sync --frequency 1d --start-date 2024-01-01 --symbols SH600000,SH600036")
                sys.exit(1)
            
            # 启动增量同步
            collector.start_incremental_sync(
                frequency=args.frequency,
                start_date=args.start_date,
                end_date=args.end_date,
                symbols=args.symbols,
                force_sync=args.force
            )
            
        else:
            # 实时调度模式（默认）
            print("🚀 启动实时调度模式...")
            print("💡 提示: 使用 --mode sync 启动增量同步模式")
            print("💡 示例: uv run python main.py --mode sync --frequency 1m --start-date 2024-01-01")
            print()
            
            # 启动实时调度器
            collector.start()
            
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
