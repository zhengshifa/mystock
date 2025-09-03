"""
掘金量化API测试脚本
测试current和history接口
"""
import logging
import sys
import os
from datetime import datetime, timedelta
from src.services import GMService
from src.config import settings


def setup_logging():
    """设置日志"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file = os.path.join(project_root, 'logs', 'gm_test.log')
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )


def test_current_api():
    """测试current接口"""
    print("\n" + "="*50)
    print("测试 current 接口")
    print("="*50)
    
    try:
        gm_service = GMService()
        
        # 测试单个股票
        print(f"\n1. 测试单个股票: {settings.test_symbols[0]}")
        current_data = gm_service.get_current_data(symbols=settings.test_symbols[0])
        
        if current_data:
            tick = current_data[0]
            print(f"股票代码: {tick.symbol}")
            print(f"最新价: {tick.price}")
            print(f"开盘价: {tick.open}")
            print(f"最高价: {tick.high}")
            print(f"最低价: {tick.low}")
            print(f"成交量: {tick.cum_volume}")
            print(f"成交额: {tick.cum_amount}")
            print(f"创建时间: {tick.created_at}")
            print(f"买卖档位数量: {len(tick.quotes)}")
            
            # 显示前3档买卖盘
            for i, quote in enumerate(tick.quotes[:3]):
                print(f"  第{i+1}档: 买价={quote.bid_p}, 买量={quote.bid_v}, 卖价={quote.ask_p}, 卖量={quote.ask_v}")
        
        # 测试多个股票
        print(f"\n2. 测试多个股票: {settings.test_symbols}")
        current_data_multi = gm_service.get_current_data(symbols=settings.test_symbols)
        
        for tick in current_data_multi:
            print(f"  {tick.symbol}: 最新价={tick.price}, 成交量={tick.cum_volume}")
        
        # 测试指定字段
        print(f"\n3. 测试指定字段查询")
        current_data_fields = gm_service.get_current_data(
            symbols=settings.test_symbols[0],
            fields='symbol,price,open,high,low'
        )
        
        if current_data_fields:
            tick = current_data_fields[0]
            print(f"指定字段查询结果: {tick.symbol} - 价格={tick.price}")
        
        print("\n✅ current 接口测试成功!")
        
    except Exception as e:
        print(f"\n❌ current 接口测试失败: {e}")
        logging.error(f"current接口测试失败: {e}")


def test_history_api():
    """测试history接口"""
    print("\n" + "="*50)
    print("测试 history 接口")
    print("="*50)
    
    try:
        gm_service = GMService()
        
        # 测试日线数据
        print(f"\n1. 测试日线数据: {settings.test_symbols[0]}")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 最近30天
        
        history_data = gm_service.get_history_data(
            symbol=settings.test_symbols[0],
            frequency='1d',
            start_time=start_date.strftime('%Y-%m-%d'),
            end_time=end_date.strftime('%Y-%m-%d'),
            fields='symbol,open,close,high,low,volume,amount,eob'
        )
        
        if history_data:
            print(f"获取到 {len(history_data)} 条日线数据")
            # 显示最近5条数据
            for i, bar in enumerate(history_data[-5:]):
                print(f"  {i+1}. {bar.eob.strftime('%Y-%m-%d')}: 开={bar.open:.2f}, 高={bar.high:.2f}, 低={bar.low:.2f}, 收={bar.close:.2f}, 量={bar.volume}")
        
        # 测试分钟线数据
        print(f"\n2. 测试分钟线数据: {settings.test_symbols[0]}")
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=2)  # 最近2小时
        
        minute_data = gm_service.get_history_data(
            symbol=settings.test_symbols[0],
            frequency='60s',
            start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        if minute_data:
            print(f"获取到 {len(minute_data)} 条分钟线数据")
            # 显示最近3条数据
            for i, bar in enumerate(minute_data[-3:]):
                print(f"  {i+1}. {bar.eob.strftime('%Y-%m-%d %H:%M:%S')}: 开={bar.open:.2f}, 收={bar.close:.2f}, 量={bar.volume}")
        
        # 测试DataFrame格式
        print(f"\n3. 测试DataFrame格式返回")
        df_data = gm_service.get_history_data(
            symbol=settings.test_symbols[0],
            frequency='1d',
            start_time=start_date.strftime('%Y-%m-%d'),
            end_time=end_date.strftime('%Y-%m-%d'),
            fields='open,close,high,low,volume',
            df=True
        )
        
        if df_data is not None:
            print(f"DataFrame形状: {df_data.shape}")
            print("DataFrame列名:", list(df_data.columns))
            print("最近3行数据:")
            print(df_data.tail(3))
        
        print("\n✅ history 接口测试成功!")
        
    except Exception as e:
        print(f"\n❌ history 接口测试失败: {e}")
        logging.error(f"history接口测试失败: {e}")


def test_connection():
    """测试连接"""
    print("\n" + "="*50)
    print("测试连接")
    print("="*50)
    
    try:
        gm_service = GMService()
        is_connected = gm_service.test_connection()
        
        if is_connected:
            print("✅ 连接测试成功!")
        else:
            print("❌ 连接测试失败!")
            
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
        logging.error(f"连接测试异常: {e}")


def main():
    """主函数"""
    print("掘金量化API测试开始")
    print(f"Token: {settings.gm_token[:10]}...")
    print(f"测试股票: {settings.test_symbols}")
    
    # 设置日志
    setup_logging()
    
    # 验证配置
    if not settings.validate():
        print("❌ 配置验证失败!")
        return
    
    try:
        # 测试连接
        test_connection()
        
        # 测试current接口
        test_current_api()
        
        # 测试history接口
        test_history_api()
        
        print("\n" + "="*50)
        print("所有测试完成!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        logging.error(f"测试过程中发生异常: {e}")


if __name__ == "__main__":
    main()
