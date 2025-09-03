"""
掘金量化API高级测试脚本
展示更多功能和数据处理
"""
import logging
import sys
import pandas as pd
from datetime import datetime, timedelta
from src.services import GMService
from src.config import settings


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def test_tick_data_analysis():
    """测试Tick数据分析"""
    print("\n" + "="*60)
    print("Tick数据分析测试")
    print("="*60)
    
    try:
        gm_service = GMService()
        
        # 获取多个股票的当前行情
        symbols = ['SZSE.000001', 'SHSE.000300', 'SZSE.000002']
        current_data = gm_service.get_current_data(symbols=symbols)
        
        print(f"\n获取到 {len(current_data)} 只股票的实时行情:")
        print("-" * 80)
        print(f"{'股票代码':<15} {'最新价':<10} {'涨跌幅':<10} {'成交量':<15} {'成交额(万)':<15}")
        print("-" * 80)
        
        for tick in current_data:
            # 计算涨跌幅 (假设开盘价作为基准)
            if tick.open > 0:
                change_pct = ((tick.price - tick.open) / tick.open) * 100
            else:
                change_pct = 0
            
            # 成交额转换为万元
            amount_wan = tick.cum_amount / 10000
            
            print(f"{tick.symbol:<15} {tick.price:<10.2f} {change_pct:<10.2f}% {tick.cum_volume:<15,} {amount_wan:<15.2f}")
        
        # 分析买卖盘情况
        print(f"\n买卖盘分析 (以 {current_data[0].symbol} 为例):")
        tick = current_data[0]
        print(f"股票: {tick.symbol}")
        print(f"最新价: {tick.price}")
        print(f"买卖档位详情:")
        print(f"{'档位':<6} {'买价':<10} {'买量':<12} {'卖价':<10} {'卖量':<12} {'价差':<10}")
        print("-" * 70)
        
        for i, quote in enumerate(tick.quotes):
            if quote.bid_p > 0 and quote.ask_p > 0:
                spread = quote.ask_p - quote.bid_p
                print(f"{i+1:<6} {quote.bid_p:<10.2f} {quote.bid_v:<12,} {quote.ask_p:<10.2f} {quote.ask_v:<12,} {spread:<10.4f}")
        
        print("\n✅ Tick数据分析完成!")
        
    except Exception as e:
        print(f"\n❌ Tick数据分析失败: {e}")


def test_historical_analysis():
    """测试历史数据分析"""
    print("\n" + "="*60)
    print("历史数据分析测试")
    print("="*60)
    
    try:
        gm_service = GMService()
        
        # 获取最近30天的日线数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        symbol = 'SZSE.000001'
        history_data = gm_service.get_history_data(
            symbol=symbol,
            frequency='1d',
            start_time=start_date.strftime('%Y-%m-%d'),
            end_time=end_date.strftime('%Y-%m-%d'),
            df=True
        )
        
        if history_data is not None and not history_data.empty:
            print(f"\n{symbol} 最近30天行情分析:")
            print(f"数据条数: {len(history_data)}")
            
            # 基本统计
            print(f"\n基本统计信息:")
            print(f"最高价: {history_data['high'].max():.2f}")
            print(f"最低价: {history_data['low'].min():.2f}")
            print(f"平均收盘价: {history_data['close'].mean():.2f}")
            print(f"总成交量: {history_data['volume'].sum():,}")
            print(f"平均成交量: {history_data['volume'].mean():,.0f}")
            
            # 计算技术指标
            history_data['ma5'] = history_data['close'].rolling(window=5).mean()
            history_data['ma10'] = history_data['close'].rolling(window=10).mean()
            history_data['volatility'] = history_data['close'].pct_change().rolling(window=5).std()
            
            # 显示最近5天的数据
            print(f"\n最近5天行情 (含技术指标):")
            recent_data = history_data.tail(5)[['close', 'ma5', 'ma10', 'volatility']]
            for i, (idx, row) in enumerate(recent_data.iterrows()):
                date_str = f"第{i+1}天"  # 简化日期显示
                print(f"{date_str}: 收盘={row['close']:.2f}, MA5={row['ma5']:.2f}, MA10={row['ma10']:.2f}, 波动率={row['volatility']:.4f}")
            
            # 涨跌统计
            history_data['daily_return'] = history_data['close'].pct_change()
            up_days = (history_data['daily_return'] > 0).sum()
            down_days = (history_data['daily_return'] < 0).sum()
            flat_days = (history_data['daily_return'] == 0).sum()
            
            print(f"\n涨跌统计:")
            print(f"上涨天数: {up_days}")
            print(f"下跌天数: {down_days}")
            print(f"平盘天数: {flat_days}")
            print(f"上涨概率: {up_days/len(history_data)*100:.1f}%")
        
        print("\n✅ 历史数据分析完成!")
        
    except Exception as e:
        print(f"\n❌ 历史数据分析失败: {e}")


def test_multi_symbol_comparison():
    """测试多股票对比分析"""
    print("\n" + "="*60)
    print("多股票对比分析")
    print("="*60)
    
    try:
        gm_service = GMService()
        
        # 获取多个股票的历史数据
        symbols = ['SZSE.000001', 'SHSE.000300']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        comparison_data = {}
        
        for symbol in symbols:
            history_data = gm_service.get_history_data(
                symbol=symbol,
                frequency='1d',
                start_time=start_date.strftime('%Y-%m-%d'),
                end_time=end_date.strftime('%Y-%m-%d'),
                df=True
            )
            
            if history_data is not None and not history_data.empty:
                # 计算收益率
                history_data['return'] = history_data['close'].pct_change()
                comparison_data[symbol] = history_data
        
        if comparison_data:
            print(f"\n股票对比分析 (最近10天):")
            print(f"{'股票代码':<15} {'当前价':<10} {'10日收益率':<12} {'平均成交量':<15} {'波动率':<10}")
            print("-" * 80)
            
            for symbol, data in comparison_data.items():
                current_price = data['close'].iloc[-1]
                total_return = (data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100
                avg_volume = data['volume'].mean()
                volatility = data['return'].std() * 100
                
                print(f"{symbol:<15} {current_price:<10.2f} {total_return:<12.2f}% {avg_volume:<15,.0f} {volatility:<10.2f}%")
        
        print("\n✅ 多股票对比分析完成!")
        
    except Exception as e:
        print(f"\n❌ 多股票对比分析失败: {e}")


def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*60)
    print("错误处理测试")
    print("="*60)
    
    try:
        gm_service = GMService()
        
        # 测试无效股票代码
        print("\n1. 测试无效股票代码:")
        try:
            invalid_data = gm_service.get_current_data(symbols='INVALID.SYMBOL')
            print(f"无效代码返回数据: {len(invalid_data)} 条")
        except Exception as e:
            print(f"无效代码处理: {e}")
        
        # 测试无效时间范围
        print("\n2. 测试无效时间范围:")
        try:
            invalid_history = gm_service.get_history_data(
                symbol='SZSE.000001',
                frequency='1d',
                start_time='2025-12-01',
                end_time='2025-12-31'
            )
            print(f"未来时间范围返回数据: {len(invalid_history)} 条")
        except Exception as e:
            print(f"未来时间范围处理: {e}")
        
        # 测试空字段查询
        print("\n3. 测试空字段查询:")
        try:
            empty_fields = gm_service.get_current_data(
                symbols='SZSE.000001',
                fields=''
            )
            if empty_fields:
                print(f"空字段查询成功，返回字段数: {len(empty_fields[0].to_dict())}")
        except Exception as e:
            print(f"空字段查询处理: {e}")
        
        print("\n✅ 错误处理测试完成!")
        
    except Exception as e:
        print(f"\n❌ 错误处理测试失败: {e}")


def main():
    """主函数"""
    print("掘金量化API高级测试开始")
    print(f"Token: {settings.gm_token[:10]}...")
    print(f"测试股票: {settings.test_symbols}")
    
    # 设置日志
    setup_logging()
    
    # 验证配置
    if not settings.validate():
        print("❌ 配置验证失败!")
        return
    
    try:
        # 测试Tick数据分析
        test_tick_data_analysis()
        
        # 测试历史数据分析
        test_historical_analysis()
        
        # 测试多股票对比
        test_multi_symbol_comparison()
        
        # 测试错误处理
        test_error_handling()
        
        print("\n" + "="*60)
        print("所有高级测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")


if __name__ == "__main__":
    main()
