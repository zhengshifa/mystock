"""
调度系统测试脚本
测试MongoDB连接、数据同步和调度功能
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from src.scheduler import SchedulerService, DataSyncService
from src.database import mongodb_client
from src.config import settings


def setup_logging():
    """设置日志"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file = os.path.join(project_root, 'logs', 'scheduler_test.log')
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )


async def test_mongodb_connection():
    """测试MongoDB连接"""
    print("\n" + "="*60)
    print("测试MongoDB连接")
    print("="*60)
    
    try:
        # 连接数据库
        connected = await mongodb_client.connect()
        
        if connected:
            print("✅ MongoDB连接成功")
            
            # 健康检查
            healthy = await mongodb_client.health_check()
            if healthy:
                print("✅ 数据库健康检查通过")
            else:
                print("❌ 数据库健康检查失败")
            
            # 测试插入数据
            test_data = [{
                'symbol': 'TEST.001',
                'price': 100.0,
                'created_at': datetime.now(),
                'test': True
            }]
            
            success = await mongodb_client.insert_tick_data(test_data)
            if success:
                print("✅ 测试数据插入成功")
            else:
                print("❌ 测试数据插入失败")
            
        else:
            print("❌ MongoDB连接失败")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB测试异常: {e}")
        return False
    
    return True


async def test_data_sync():
    """测试数据同步功能"""
    print("\n" + "="*60)
    print("测试数据同步功能")
    print("="*60)
    
    try:
        sync_service = DataSyncService()
        
        # 测试历史数据同步
        print("\n1. 测试历史数据同步")
        symbols = settings.test_symbols[:1]  # 只测试第一个股票
        results = await sync_service.sync_history_data(symbols)
        
        for symbol, success in results.items():
            if success:
                print(f"✅ {symbol} 历史数据同步成功")
            else:
                print(f"❌ {symbol} 历史数据同步失败")
        
        # 测试实时数据同步
        print("\n2. 测试实时数据同步")
        results = await sync_service.sync_realtime_data(symbols)
        
        for symbol, success in results.items():
            if success:
                print(f"✅ {symbol} 实时数据同步成功")
            else:
                print(f"❌ {symbol} 实时数据同步失败")
        
        # 测试分钟数据同步
        print("\n3. 测试分钟数据同步")
        results = await sync_service.sync_minute_data(symbols, minutes_back=60)
        
        for symbol, success in results.items():
            if success:
                print(f"✅ {symbol} 分钟数据同步成功")
            else:
                print(f"❌ {symbol} 分钟数据同步失败")
        
        # 获取同步状态
        print("\n4. 获取同步状态")
        status = await sync_service.get_sync_status()
        print(f"同步状态: {status}")
        
        print("\n✅ 数据同步功能测试完成")
        
    except Exception as e:
        print(f"\n❌ 数据同步测试失败: {e}")
        logging.error(f"数据同步测试失败: {e}")


async def test_scheduler():
    """测试调度器功能"""
    print("\n" + "="*60)
    print("测试调度器功能")
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
        
        # 等待一段时间观察任务执行
        print("\n3. 观察任务执行 (等待30秒)")
        await asyncio.sleep(30)
        
        # 手动触发一个任务
        print("\n4. 手动触发历史数据同步任务")
        await scheduler_service.trigger_job_now('daily_history_sync')
        
        # 停止调度器
        print("\n5. 停止调度器")
        scheduler_service.stop_scheduler()
        print("✅ 调度器停止成功")
        
        print("\n✅ 调度器功能测试完成")
        
    except Exception as e:
        print(f"\n❌ 调度器测试失败: {e}")
        logging.error(f"调度器测试失败: {e}")


async def test_sync_history():
    """测试同步历史查询"""
    print("\n" + "="*60)
    print("测试同步历史查询")
    print("="*60)
    
    try:
        # 获取同步历史
        history = await mongodb_client.get_sync_history(limit=10)
        
        if history:
            print(f"获取到 {len(history)} 条同步记录:")
            print("-" * 80)
            print(f"{'股票代码':<15} {'操作类型':<10} {'状态':<10} {'记录数':<10} {'同步时间':<20}")
            print("-" * 80)
            
            for record in history:
                print(f"{record['symbol']:<15} {record['operation_type']:<10} "
                      f"{record['status']:<10} {record['record_count']:<10} "
                      f"{record['sync_time'].strftime('%Y-%m-%d %H:%M:%S'):<20}")
        else:
            print("暂无同步历史记录")
        
        print("\n✅ 同步历史查询测试完成")
        
    except Exception as e:
        print(f"\n❌ 同步历史查询测试失败: {e}")
        logging.error(f"同步历史查询测试失败: {e}")


async def test_realtime_sync():
    """测试实时数据同步"""
    print("\n" + "="*60)
    print("测试实时数据同步")
    print("="*60)
    
    try:
        scheduler_service = SchedulerService()
        
        print("启动实时数据同步 (运行60秒后自动停止)")
        print("按 Ctrl+C 可以提前停止")
        
        # 启动实时同步
        sync_task = asyncio.create_task(
            scheduler_service.start_realtime_sync_manual()
        )
        
        # 等待60秒
        try:
            await asyncio.wait_for(sync_task, timeout=60)
        except asyncio.TimeoutError:
            print("\n实时同步运行60秒，现在停止...")
            scheduler_service.stop_realtime_sync_manual()
        
        print("\n✅ 实时数据同步测试完成")
        
    except KeyboardInterrupt:
        print("\n用户中断，停止实时同步...")
        scheduler_service.stop_realtime_sync_manual()
    except Exception as e:
        print(f"\n❌ 实时数据同步测试失败: {e}")
        logging.error(f"实时数据同步测试失败: {e}")


async def main():
    """主函数"""
    print("调度系统测试开始")
    print(f"Token: {settings.gm_token[:10]}...")
    print(f"测试股票: {settings.test_symbols}")
    print(f"MongoDB: {settings.mongodb_url}")
    
    # 设置日志
    setup_logging()
    
    # 验证配置
    if not settings.validate():
        print("❌ 配置验证失败!")
        return
    
    try:
        # 测试MongoDB连接
        mongodb_ok = await test_mongodb_connection()
        if not mongodb_ok:
            print("❌ MongoDB连接失败，跳过后续测试")
            return
        
        # 测试数据同步
        await test_data_sync()
        
        # 测试调度器
        await test_scheduler()
        
        # 测试同步历史
        await test_sync_history()
        
        # 询问是否测试实时同步
        print("\n" + "="*60)
        response = input("是否测试实时数据同步? (y/n): ")
        if response.lower() == 'y':
            await test_realtime_sync()
        
        print("\n" + "="*60)
        print("所有测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        logging.error(f"测试过程中发生异常: {e}")
    
    finally:
        # 断开数据库连接
        await mongodb_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
