"""
多频率数据同步测试脚本
测试多种频率的数据同步功能
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from src.scheduler import SchedulerService, DataSyncService
from src.database import mongodb_client
from src.config import settings


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('multi_frequency_test.log', encoding='utf-8')
        ]
    )


async def test_mongodb_multi_frequency():
    """测试MongoDB多频率集合"""
    print("\n" + "="*60)
    print("测试MongoDB多频率集合")
    print("="*60)
    
    try:
        # 连接数据库
        connected = await mongodb_client.connect()
        
        if connected:
            print("✅ MongoDB连接成功")
            
            # 检查各频率集合
            print("\n检查各频率集合:")
            for frequency in settings.enabled_frequencies:
                collection_key = f'bar_{frequency}'
                if collection_key in mongodb_client._collections:
                    collection = mongodb_client._collections[collection_key]
                    count = await collection.count_documents({})
                    print(f"  ✅ {frequency}: {count:,} 条数据")
                else:
                    print(f"  ❌ {frequency}: 集合不存在")
            
            # 健康检查
            healthy = await mongodb_client.health_check()
            if healthy:
                print("✅ 数据库健康检查通过")
            else:
                print("❌ 数据库健康检查失败")
            
        else:
            print("❌ MongoDB连接失败")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB测试异常: {e}")
        return False
    
    return True


async def test_single_frequency_sync():
    """测试单频率数据同步"""
    print("\n" + "="*60)
    print("测试单频率数据同步")
    print("="*60)
    
    try:
        sync_service = DataSyncService()
        symbols = settings.test_symbols[:1]  # 只测试第一个股票
        
        # 测试各频率的数据同步
        for frequency in settings.enabled_frequencies:
            if settings.is_frequency_enabled(frequency):
                print(f"\n测试 {frequency} 频率同步:")
                
                if frequency == '1d':
                    # 日线数据使用历史同步
                    results = await sync_service.sync_history_data(
                        symbols, frequency=frequency
                    )
                else:
                    # 分钟级数据使用分钟同步
                    results = await sync_service.sync_minute_data(
                        symbols, minutes_back=60, frequency=frequency
                    )
                
                for symbol, success in results.items():
                    if success:
                        print(f"  ✅ {symbol} {frequency} 同步成功")
                    else:
                        print(f"  ❌ {symbol} {frequency} 同步失败")
            else:
                print(f"\n跳过 {frequency} 频率同步（已禁用）")
        
        print("\n✅ 单频率数据同步测试完成")
        
    except Exception as e:
        print(f"\n❌ 单频率数据同步测试失败: {e}")
        logging.error(f"单频率数据同步测试失败: {e}")


async def test_all_frequencies_sync():
    """测试所有频率数据同步"""
    print("\n" + "="*60)
    print("测试所有频率数据同步")
    print("="*60)
    
    try:
        sync_service = DataSyncService()
        symbols = settings.test_symbols[:1]  # 只测试第一个股票
        
        print("开始同步所有频率的历史数据...")
        results = await sync_service.sync_all_frequencies(symbols)
        
        print("\n同步结果:")
        for frequency, freq_results in results.items():
            success_count = sum(1 for success in freq_results.values() if success)
            total_count = len(freq_results)
            print(f"  {frequency}: {success_count}/{total_count} 成功")
        
        print("\n✅ 所有频率数据同步测试完成")
        
    except Exception as e:
        print(f"\n❌ 所有频率数据同步测试失败: {e}")
        logging.error(f"所有频率数据同步测试失败: {e}")


async def test_realtime_multi_frequency():
    """测试实时多频率数据同步"""
    print("\n" + "="*60)
    print("测试实时多频率数据同步")
    print("="*60)
    
    try:
        sync_service = DataSyncService()
        symbols = settings.test_symbols[:1]  # 只测试第一个股票
        
        print("开始同步实时多频率数据...")
        results = await sync_service.sync_realtime_frequencies(symbols)
        
        print("\n实时同步结果:")
        for frequency, freq_results in results.items():
            success_count = sum(1 for success in freq_results.values() if success)
            total_count = len(freq_results)
            print(f"  {frequency}: {success_count}/{total_count} 成功")
        
        print("\n✅ 实时多频率数据同步测试完成")
        
    except Exception as e:
        print(f"\n❌ 实时多频率数据同步测试失败: {e}")
        logging.error(f"实时多频率数据同步测试失败: {e}")


async def test_scheduler_multi_frequency():
    """测试调度器多频率功能"""
    print("\n" + "="*60)
    print("测试调度器多频率功能")
    print("="*60)
    
    try:
        scheduler_service = SchedulerService()
        
        # 启动调度器
        print("\n1. 启动调度器")
        await scheduler_service.start_scheduler()
        print("✅ 调度器启动成功")
        
        # 获取任务状态
        print("\n2. 获取任务状态")
        job_status = scheduler_service.get_job_status()
        print(f"调度器运行状态: {job_status['scheduler_running']}")
        print(f"任务数量: {job_status['job_count']}")
        
        for job in job_status['jobs']:
            print(f"  - {job['name']} (ID: {job['id']})")
            print(f"    下次执行时间: {job['next_run_time']}")
        
        # 手动触发所有频率同步
        print("\n3. 手动触发所有频率同步")
        await scheduler_service.sync_all_frequencies_manual()
        
        # 等待一段时间观察任务执行
        print("\n4. 观察任务执行 (等待30秒)")
        await asyncio.sleep(30)
        
        # 停止调度器
        print("\n5. 停止调度器")
        scheduler_service.stop_scheduler()
        print("✅ 调度器停止成功")
        
        print("\n✅ 调度器多频率功能测试完成")
        
    except Exception as e:
        print(f"\n❌ 调度器多频率功能测试失败: {e}")
        logging.error(f"调度器多频率功能测试失败: {e}")


async def test_frequency_statistics():
    """测试频率数据统计"""
    print("\n" + "="*60)
    print("测试频率数据统计")
    print("="*60)
    
    try:
        # 获取频率统计
        statistics = await mongodb_client.get_frequency_statistics()
        
        print("各频率数据统计:")
        print("-" * 50)
        
        # Tick数据统计
        tick_stats = statistics.get('tick', {})
        print(f"Tick数据: {tick_stats.get('count', 0):,} 条")
        
        # 各频率Bar数据统计
        for frequency in settings.enabled_frequencies:
            freq_stats = statistics.get(frequency, {})
            count = freq_stats.get('count', 0)
            latest_time = freq_stats.get('latest_time')
            latest_symbol = freq_stats.get('latest_symbol')
            
            print(f"{frequency}: {count:,} 条")
            if latest_time and latest_symbol:
                print(f"  最新: {latest_symbol} - {latest_time}")
        
        print("\n✅ 频率数据统计测试完成")
        
    except Exception as e:
        print(f"\n❌ 频率数据统计测试失败: {e}")
        logging.error(f"频率数据统计测试失败: {e}")


async def test_individual_frequency_sync():
    """测试单个频率手动同步"""
    print("\n" + "="*60)
    print("测试单个频率手动同步")
    print("="*60)
    
    try:
        scheduler_service = SchedulerService()
        
        # 测试各频率的手动同步
        for frequency in settings.enabled_frequencies:
            if settings.is_frequency_enabled(frequency):
                print(f"\n测试 {frequency} 频率手动同步:")
                await scheduler_service.sync_frequency_manual(frequency)
            else:
                print(f"\n跳过 {frequency} 频率手动同步（已禁用）")
        
        print("\n✅ 单个频率手动同步测试完成")
        
    except Exception as e:
        print(f"\n❌ 单个频率手动同步测试失败: {e}")
        logging.error(f"单个频率手动同步测试失败: {e}")


async def main():
    """主函数"""
    print("多频率数据同步测试开始")
    print(f"Token: {settings.gm_token[:10]}...")
    print(f"测试股票: {settings.test_symbols}")
    print(f"启用频率: {settings.enabled_frequencies}")
    print(f"MongoDB: {settings.mongodb_url}")
    
    # 设置日志
    setup_logging()
    
    # 验证配置
    if not settings.validate():
        print("❌ 配置验证失败!")
        return
    
    try:
        # 测试MongoDB多频率集合
        mongodb_ok = await test_mongodb_multi_frequency()
        if not mongodb_ok:
            print("❌ MongoDB连接失败，跳过后续测试")
            return
        
        # 测试单频率数据同步
        await test_single_frequency_sync()
        
        # 测试所有频率数据同步
        await test_all_frequencies_sync()
        
        # 测试实时多频率数据同步
        await test_realtime_multi_frequency()
        
        # 测试调度器多频率功能
        await test_scheduler_multi_frequency()
        
        # 测试频率数据统计
        await test_frequency_statistics()
        
        # 测试单个频率手动同步
        await test_individual_frequency_sync()
        
        print("\n" + "="*60)
        print("所有多频率测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        logging.error(f"测试过程中发生异常: {e}")
    
    finally:
        # 断开数据库连接
        await mongodb_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
