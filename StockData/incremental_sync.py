#!/usr/bin/env python3
"""
增量同步命令行工具
支持指定时间范围的数据同步，具备断点续传和数据完整性检查功能
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scheduler.incremental_sync import get_incremental_sync_manager
from src.config.scheduler_config import get_scheduler_config
from src.utils.logger import setup_logger


class IncrementalSyncCLI:
    """增量同步命令行界面"""
    
    def __init__(self):
        """初始化命令行界面"""
        self.sync_manager = get_incremental_sync_manager()
        self.scheduler_config = get_scheduler_config()
    
    def run(self, args):
        """运行增量同步"""
        try:
            if args.command == "sync":
                self._sync_data(args)
            elif args.command == "status":
                self._show_status(args)
            elif args.command == "resume":
                self._resume_sync(args)
            elif args.command == "cleanup":
                self._cleanup_status(args)
            else:
                print(f"❌ 未知命令: {args.command}")
                self._show_help()
                
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            sys.exit(1)
    
    def _sync_data(self, args):
        """同步数据"""
        print(f"🚀 开始增量同步 {args.frequency} 数据...")
        
        # 获取股票列表
        if args.symbols:
            symbols = args.symbols.split(',')
        else:
            # 从配置获取默认股票列表
            symbols = self.scheduler_config.get_stock_symbols()
        
        print(f"📊 同步股票: {len(symbols)} 只")
        print(f"📅 时间范围: {args.start_date} 到 {args.end_date}")
        print(f"⏱️ 数据频率: {args.frequency}")
        
        # 执行同步
        result = self.sync_manager.sync_data_range(
            symbols=symbols,
            frequency=args.frequency,
            start_date=args.start_date,
            end_date=args.end_date,
            force_sync=args.force
        )
        
        # 显示结果
        self._display_sync_result(result)
    
    def _show_status(self, args):
        """显示同步状态"""
        if args.sync_id:
            # 显示特定同步任务状态
            status = self.sync_manager.get_sync_status(args.sync_id)
            if status:
                self._display_sync_status(status)
            else:
                print(f"❌ 未找到同步任务: {args.sync_id}")
        else:
            # 显示所有同步任务状态
            all_status = self.sync_manager.get_sync_status()
            if all_status:
                print(f"📋 同步任务状态 (共 {len(all_status)} 个):")
                print("-" * 60)
                for sync_id, status in all_status.items():
                    print(f"\n🆔 任务ID: {sync_id}")
                    self._display_sync_status(status)
            else:
                print("📋 暂无同步任务")
    
    def _resume_sync(self, args):
        """恢复失败的同步任务"""
        print(f"🔄 尝试恢复同步任务: {args.sync_id}")
        
        result = self.sync_manager.resume_failed_sync(args.sync_id)
        if result.get("status") == "failed":
            print(f"❌ 恢复失败: {result.get('error')}")
        else:
            print(f"✅ 恢复成功: {result}")
    
    def _cleanup_status(self, args):
        """清理同步状态"""
        days = args.days if args.days else 7
        print(f"🧹 清理 {days} 天前的同步状态记录...")
        
        cleaned_count = self.sync_manager.cleanup_sync_status(days)
        print(f"✅ 清理完成，共清理 {cleaned_count} 条记录")
    
    def _display_sync_result(self, result):
        """显示同步结果"""
        print("\n" + "=" * 60)
        print("📊 同步结果")
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
    
    def _display_sync_status(self, status):
        """显示同步状态"""
        if status.get("status") == "running":
            print(f"🔄 状态: 运行中")
            if "progress" in status:
                print(f"📊 进度: {status['progress']}%")
        elif status.get("status") == "completed":
            print(f"✅ 状态: 已完成")
        elif status.get("status") == "failed":
            print(f"❌ 状态: 失败")
            if "error" in status:
                print(f"❌ 错误: {status['error']}")
        else:
            print(f"❓ 状态: 未知")
        
        if "started_at" in status:
            print(f"🕐 开始时间: {status['started_at']}")
        if "completed_at" in status:
            print(f"🕐 完成时间: {status['completed_at']}")
        if "failed_at" in status:
            print(f"🕐 失败时间: {status['failed_at']}")
        if "total_symbols" in status:
            print(f"📈 总股票数: {status['total_symbols']} 只")
    
    def _show_help(self):
        """显示帮助信息"""
        print("""
📖 增量同步工具使用说明

用法:
  python incremental_sync.py <命令> [选项]

命令:
  sync      同步指定时间范围的数据
  status    显示同步任务状态
  resume    恢复失败的同步任务
  cleanup   清理旧的同步状态记录

示例:
  # 同步最近30天的1分钟K线数据
  python incremental_sync.py sync --frequency 1m --start-date 2024-01-01

  # 同步指定股票的历史数据
  python incremental_sync.py sync --symbols SH600000,SH600036 --frequency 1d --start-date 2024-01-01

  # 查看同步状态
  python incremental_sync.py status

  # 恢复失败的同步任务
  python incremental_sync.py resume --sync-id sync_1d_2024-01-01_2024-01-31_1234567890

  # 清理7天前的同步状态
  python incremental_sync.py cleanup --days 7

选项:
  --frequency    数据频率 (1m, 5m, 15m, 1h, 1d)
  --start-date   开始日期 (YYYY-MM-DD)
  --end-date     结束日期 (YYYY-MM-DD)，默认为今天
  --symbols      股票代码列表，用逗号分隔
  --force        强制重新同步
  --sync-id      同步任务ID
  --days         清理天数
        """)


def main():
    """主函数"""
    # 设置日志系统
    setup_logger()
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description="股票数据增量同步工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # sync 命令
    sync_parser = subparsers.add_parser('sync', help='同步数据')
    sync_parser.add_argument('--frequency', required=True, 
                            choices=['1m', '5m', '15m', '1h', '1d'],
                            help='数据频率')
    sync_parser.add_argument('--start-date', required=True,
                            help='开始日期 (YYYY-MM-DD)')
    sync_parser.add_argument('--end-date',
                            help='结束日期 (YYYY-MM-DD)，默认为今天')
    sync_parser.add_argument('--symbols',
                            help='股票代码列表，用逗号分隔')
    sync_parser.add_argument('--force', action='store_true',
                            help='强制重新同步')
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='显示同步状态')
    status_parser.add_argument('--sync-id',
                              help='同步任务ID')
    
    # resume 命令
    resume_parser = subparsers.add_parser('resume', help='恢复同步任务')
    resume_parser.add_argument('--sync-id', required=True,
                              help='同步任务ID')
    
    # cleanup 命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理同步状态')
    cleanup_parser.add_argument('--days', type=int, default=7,
                               help='清理天数，默认7天')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 设置默认结束日期
    if args.command == 'sync' and not args.end_date:
        args.end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 创建并运行CLI
    cli = IncrementalSyncCLI()
    cli.run(args)


if __name__ == "__main__":
    main()
