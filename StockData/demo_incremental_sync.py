#!/usr/bin/env python3
"""
增量同步功能演示脚本
展示如何使用增量同步功能进行股票数据同步
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scheduler.incremental_sync import get_incremental_sync_manager
from src.config.scheduler_config import get_scheduler_config
from src.utils.logger import setup_logger


def demo_basic_sync():
    """演示基本增量同步功能"""
    print("🚀 演示1: 基本增量同步功能")
    print("=" * 60)
    
    sync_manager = get_incremental_sync_manager()
    
    # 同步最近7天的日线数据
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📅 同步时间范围: {start_date} 到 {end_date}")
    print(f"⏱️ 数据频率: 1d (日线)")
    print(f"📊 股票数量: 10只 (配置文件中的默认股票)")
    print()
    
    result = sync_manager.sync_data_range(
        symbols=["600000", "600036", "600519"],  # 只同步3只股票作为演示
        frequency="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    print("📊 同步结果:")
    print(f"  状态: {result.get('status', 'N/A')}")
    print(f"  任务ID: {result.get('sync_id', 'N/A')}")
    print(f"  成功: {result.get('success_count', 0)} 只")
    print(f"  失败: {result.get('failed_count', 0)} 只")
    print(f"  总记录数: {result.get('total_records', 0)} 条")
    
    if result.get('failed_symbols'):
        print(f"  失败股票: {', '.join(result['failed_symbols'])}")
    
    print()


def demo_sync_from_last_record():
    """演示从最后记录开始同步"""
    print("🔄 演示2: 从最后记录开始同步")
    print("=" * 60)
    
    sync_manager = get_incremental_sync_manager()
    
    print("📊 从最后一条记录开始同步1小时K线数据")
    print("💡 如果找不到最后记录，会从30天前开始同步")
    print()
    
    result = sync_manager.sync_from_last_record(
        symbols=["600000", "600036"],
        frequency="1h",
        days_back=30
    )
    
    for symbol, sync_result in result.items():
        print(f"📈 {symbol}:")
        print(f"  状态: {sync_result.get('status', 'N/A')}")
        if sync_result.get('error'):
            print(f"  错误: {sync_result['error']}")
        print()


def demo_sync_status_management():
    """演示同步状态管理"""
    print("📋 演示3: 同步状态管理")
    print("=" * 60)
    
    sync_manager = get_incremental_sync_manager()
    
    # 获取所有同步状态
    all_status = sync_manager.get_sync_status()
    
    if all_status:
        print(f"📊 当前同步任务状态 (共 {len(all_status)} 个):")
        for sync_id, status in all_status.items():
            print(f"\n🆔 任务ID: {sync_id}")
            print(f"  状态: {status.get('status', 'N/A')}")
            if "started_at" in status:
                print(f"  开始时间: {status['started_at']}")
            if "completed_at" in status:
                print(f"  完成时间: {status['completed_at']}")
            if "failed_at" in status:
                print(f"  失败时间: {status['failed_at']}")
            if "error" in status:
                print(f"  错误: {status['error']}")
    else:
        print("📋 暂无同步任务")
    
    print()


def demo_data_completeness_check():
    """演示数据完整性检查"""
    print("🔍 演示4: 数据完整性检查")
    print("=" * 60)
    
    sync_manager = get_incremental_sync_manager()
    
    # 检查最近3天的数据完整性
    start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📅 检查时间范围: {start_date} 到 {end_date}")
    print(f"⏱️ 数据频率: 1d (日线)")
    print()
    
    # 这里我们直接调用内部方法进行演示
    missing_ranges = sync_manager._check_data_completeness(
        symbols=["600000", "600036"],
        frequency="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    if missing_ranges:
        print("❌ 发现数据缺失:")
        for missing in missing_ranges:
            print(f"  📈 {missing['symbol']}:")
            print(f"    期望: {missing['expected']} 条")
            print(f"    已有: {missing['existing']} 条")
            print(f"    缺失: {missing['missing']} 条")
    else:
        print("✅ 数据完整，无需同步")
    
    print()


def demo_cleanup_sync_status():
    """演示清理同步状态"""
    print("🧹 演示5: 清理同步状态")
    print("=" * 60)
    
    sync_manager = get_incremental_sync_manager()
    
    print("🧹 清理7天前的同步状态记录...")
    
    cleaned_count = sync_manager.cleanup_sync_status(days=7)
    
    print(f"✅ 清理完成，共清理 {cleaned_count} 条记录")
    print()


def show_usage_examples():
    """显示使用示例"""
    print("📖 使用示例")
    print("=" * 60)
    
    print("1. 基本增量同步:")
    print("   uv run python main.py --mode sync --frequency 1d --start-date 2024-08-01")
    print()
    
    print("2. 同步指定股票:")
    print("   uv run python main.py --mode sync --frequency 1h --start-date 2024-08-01 --symbols SH600000,SH600036")
    print()
    
    print("3. 强制重新同步:")
    print("   uv run python main.py --mode sync --frequency 1m --start-date 2024-08-01 --force")
    print()
    
    print("4. 查看同步状态:")
    print("   uv run python incremental_sync.py status")
    print()
    
    print("5. 清理同步状态:")
    print("   uv run python incremental_sync.py cleanup --days 7")
    print()


def main():
    """主函数"""
    print("🎯 股票数据增量同步功能演示")
    print("=" * 60)
    print()
    
    try:
        # 设置日志系统
        setup_logger()
        
        # 演示各项功能
        demo_basic_sync()
        demo_sync_from_last_record()
        demo_sync_status_management()
        demo_data_completeness_check()
        demo_cleanup_sync_status()
        
        # 显示使用示例
        show_usage_examples()
        
        print("🎉 演示完成！")
        print()
        print("💡 提示:")
        print("- 由于GM API的'获取orgcode错误'，实际数据获取会失败")
        print("- 但增量同步的架构和流程已经完整实现")
        print("- 当API问题解决后，增量同步功能将正常工作")
        print("- 你可以使用 --force 参数强制同步，或等待API问题解决")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
