"""
数据查询脚本
查询MongoDB中存储的股票数据
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from src.database import mongodb_client
from src.config import settings


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


async def query_tick_data(symbol: str, limit: int = 10):
    """查询Tick数据"""
    print(f"\n查询 {symbol} 的Tick数据 (最近{limit}条):")
    print("-" * 80)
    
    try:
        collection = mongodb_client._collections['tick']
        cursor = collection.find(
            {'symbol': symbol}
        ).sort('created_at', -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        
        if results:
            print(f"{'时间':<20} {'价格':<10} {'成交量':<15} {'成交额':<15}")
            print("-" * 80)
            
            for data in results:
                time_str = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"{time_str:<20} {data['price']:<10.2f} "
                      f"{data['cum_volume']:<15,} {data['cum_amount']:<15.2f}")
        else:
            print("未找到Tick数据")
            
    except Exception as e:
        print(f"查询Tick数据失败: {e}")


async def query_bar_data(symbol: str, frequency: str = '1d', limit: int = 10):
    """查询Bar数据"""
    print(f"\n查询 {symbol} 的{frequency} Bar数据 (最近{limit}条):")
    print("-" * 80)
    
    try:
        collection_key = f'bar_{frequency}'
        if collection_key not in mongodb_client._collections:
            print(f"未找到频率 {frequency} 对应的集合")
            return
        
        collection = mongodb_client._collections[collection_key]
        cursor = collection.find(
            {'symbol': symbol, 'frequency': frequency}
        ).sort('eob', -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        
        if results:
            print(f"{'结束时间':<20} {'开盘':<8} {'最高':<8} {'最低':<8} {'收盘':<8} {'成交量':<15}")
            print("-" * 80)
            
            for data in results:
                time_str = data['eob'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"{time_str:<20} {data['open']:<8.2f} {data['high']:<8.2f} "
                      f"{data['low']:<8.2f} {data['close']:<8.2f} {data['volume']:<15,}")
        else:
            print("未找到Bar数据")
            
    except Exception as e:
        print(f"查询{frequency} Bar数据失败: {e}")


async def query_sync_log(limit: int = 20):
    """查询同步日志"""
    print(f"\n查询同步日志 (最近{limit}条):")
    print("-" * 80)
    
    try:
        history = await mongodb_client.get_sync_history(limit=limit)
        
        if history:
            print(f"{'股票代码':<15} {'操作类型':<10} {'状态':<10} {'记录数':<10} {'同步时间':<20}")
            print("-" * 80)
            
            for record in history:
                print(f"{record['symbol']:<15} {record['operation_type']:<10} "
                      f"{record['status']:<10} {record['record_count']:<10} "
                      f"{record['sync_time'].strftime('%Y-%m-%d %H:%M:%S'):<20}")
        else:
            print("未找到同步日志")
            
    except Exception as e:
        print(f"查询同步日志失败: {e}")


async def get_data_statistics():
    """获取数据统计"""
    print("\n数据统计:")
    print("-" * 50)
    
    try:
        # 使用新的统计方法
        statistics = await mongodb_client.get_frequency_statistics()
        
        # Tick数据统计
        tick_stats = statistics.get('tick', {})
        print(f"Tick数据总数: {tick_stats.get('count', 0):,}")
        
        # 各频率Bar数据统计
        print("\n各频率数据统计:")
        for frequency in settings.enabled_frequencies:
            freq_stats = statistics.get(frequency, {})
            count = freq_stats.get('count', 0)
            latest_time = freq_stats.get('latest_time')
            latest_symbol = freq_stats.get('latest_symbol')
            
            print(f"  {frequency}: {count:,} 条")
            if latest_time and latest_symbol:
                print(f"    最新: {latest_symbol} - {latest_time}")
        
        # 按股票统计
        print("\n按股票统计:")
        symbols = settings.test_symbols
        tick_collection = mongodb_client._collections['tick']
        
        for symbol in symbols:
            tick_count = await tick_collection.count_documents({'symbol': symbol})
            print(f"  {symbol}: Tick={tick_count:,}")
            
            # 各频率数据统计
            for frequency in settings.enabled_frequencies:
                collection_key = f'bar_{frequency}'
                if collection_key in mongodb_client._collections:
                    collection = mongodb_client._collections[collection_key]
                    bar_count = await collection.count_documents({'symbol': symbol})
                    print(f"    {frequency}: {bar_count:,}")
            
    except Exception as e:
        print(f"获取数据统计失败: {e}")


async def main():
    """主函数"""
    print("数据查询工具")
    print("="*50)
    
    # 设置日志
    setup_logging()
    
    try:
        # 连接数据库
        connected = await mongodb_client.connect()
        if not connected:
            print("❌ 数据库连接失败")
            return
        
        print("✅ 数据库连接成功")
        
        while True:
            print("\n" + "="*50)
            print("请选择操作:")
            print("1. 查询Tick数据")
            print("2. 查询Bar数据")
            print("3. 查询同步日志")
            print("4. 数据统计")
            print("5. 退出")
            print("="*50)
            
            choice = input("请输入选择 (1-5): ").strip()
            
            if choice == '1':
                symbol = input(f"请输入股票代码 (默认: {settings.test_symbols[0]}): ").strip()
                if not symbol:
                    symbol = settings.test_symbols[0]
                
                limit = input("请输入查询条数 (默认: 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                
                await query_tick_data(symbol, limit)
                
            elif choice == '2':
                symbol = input(f"请输入股票代码 (默认: {settings.test_symbols[0]}): ").strip()
                if not symbol:
                    symbol = settings.test_symbols[0]
                
                print("可用频率:", ", ".join(settings.enabled_frequencies))
                frequency = input("请输入频率 (默认: 1d): ").strip()
                if not frequency:
                    frequency = '1d'
                
                if frequency not in settings.enabled_frequencies:
                    print(f"频率 {frequency} 不在可用频率列表中")
                    continue
                
                limit = input("请输入查询条数 (默认: 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                
                await query_bar_data(symbol, frequency, limit)
                
            elif choice == '3':
                limit = input("请输入查询条数 (默认: 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                
                await query_sync_log(limit)
                
            elif choice == '4':
                await get_data_statistics()
                
            elif choice == '5':
                print("退出程序")
                break
                
            else:
                print("无效选择，请重新输入")
    
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"程序异常: {e}")
        logging.error(f"程序异常: {e}")
    
    finally:
        await mongodb_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
