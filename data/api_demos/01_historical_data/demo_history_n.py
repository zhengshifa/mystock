#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: history_n() 函数测试
功能：获取N个历史数据点
"""

import gmtrade as gm
import pandas as pd
import json
import os
from datetime import datetime

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'gm_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_history_n_api():
    """测试 gm.history_n() API"""
    print("=" * 60)
    print("GM API Demo: history_n() 函数测试")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 设置token
    gm.set_token(config['token'])
    
    # 测试参数
    symbols = ['SHSE.000001', 'SZSE.000001', 'SHSE.600000']
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    results = {}
    
    for symbol in symbols:
        print(f"\n测试标的: {symbol}")
        print("-" * 40)
        
        try:
            # 测试不同频率和数量的历史数据
            test_cases = [
                {'frequency': '1d', 'count': 10, 'desc': '最近10个交易日'},
                {'frequency': '1d', 'count': 30, 'desc': '最近30个交易日'},
                {'frequency': '1m', 'count': 60, 'desc': '最近60分钟'},
                {'frequency': '5m', 'count': 48, 'desc': '最近48个5分钟'},
                {'frequency': '15m', 'count': 32, 'desc': '最近32个15分钟'},
                {'frequency': '60m', 'count': 24, 'desc': '最近24小时'}
            ]
            
            for case in test_cases:
                freq = case['frequency']
                count = case['count']
                desc = case['desc']
                
                print(f"\n获取 {desc} ({freq}, {count}条)...")
                
                # 调用 gm.history_n() API
                data = gm.history_n(
                    symbol=symbol,
                    frequency=freq,
                    count=count,
                    end_time=end_time,
                    fields='symbol,eob,open,high,low,close,volume,amount',
                    skip_suspended=True,
                    fill_missing='Last',
                    adjust=gm.ADJUST_PREV,
                    df=True
                )
                
                if data is not None and not data.empty:
                    print(f"✓ 成功获取 {len(data)} 条数据")
                    print(f"  数据列: {list(data.columns)}")
                    print(f"  时间范围: {data.index[0]} 到 {data.index[-1]}")
                    print(f"  最新价格: {data['close'].iloc[-1]:.2f}")
                    print(f"  价格变化: {((data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100):.2f}%")
                    
                    # 保存结果
                    if symbol not in results:
                        results[symbol] = {}
                    
                    results[symbol][f"{freq}_{count}"] = {
                        'data_count': len(data),
                        'columns': list(data.columns),
                        'start_time': str(data.index[0]),
                        'end_time': str(data.index[-1]),
                        'latest_price': float(data['close'].iloc[-1]),
                        'price_change_pct': float((data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100),
                        'volume_sum': int(data['volume'].sum()),
                        'amount_sum': float(data['amount'].sum()),
                        'sample_data': data.tail(3).to_dict()
                    }
                    
                    # 保存CSV文件
                    csv_filename = f"history_n_{symbol.replace('.', '_')}_{freq}_{count}.csv"
                    csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
                    data.to_csv(csv_path, encoding='utf-8-sig')
                    print(f"  已保存到: {csv_filename}")
                    
                else:
                    print(f"✗ 未获取到数据")
                    
        except Exception as e:
            print(f"✗ 获取 {symbol} 数据时出错: {str(e)}")
            if symbol not in results:
                results[symbol] = {}
            results[symbol]['error'] = str(e)
    
    # 保存测试结果
    result_file = os.path.join(os.path.dirname(__file__), 'history_n_test_results.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=" * 60)
    print(f"测试完成！结果已保存到: history_n_test_results.json")
    print(f"=" * 60)
    
    return results

def test_history_n_edge_cases():
    """测试 history_n() 的边界情况"""
    print("\n" + "=" * 60)
    print("测试 history_n() 边界情况")
    print("=" * 60)
    
    config = load_config()
    gm.set_token(config['token'])
    
    symbol = 'SHSE.000001'
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 测试不同的count值
    test_counts = [1, 5, 100, 500, 1000]
    
    for count in test_counts:
        print(f"\n测试获取 {count} 条日线数据...")
        try:
            data = gm.history_n(
                symbol=symbol,
                frequency='1d',
                count=count,
                end_time=end_time,
                fields='symbol,eob,open,high,low,close,volume',
                df=True
            )
            
            if data is not None and not data.empty:
                print(f"✓ 成功获取 {len(data)} 条数据")
                if len(data) != count:
                    print(f"  注意: 请求 {count} 条，实际获取 {len(data)} 条")
            else:
                print("✗ 未获取到数据")
                
        except Exception as e:
            print(f"✗ 错误: {str(e)}")

def test_history_n_multiple_symbols():
    """测试 history_n() 多标的同时获取"""
    print("\n" + "=" * 60)
    print("测试 history_n() 多标的获取")
    print("=" * 60)
    
    config = load_config()
    gm.set_token(config['token'])
    
    # 多个标的
    symbols = ['SHSE.000001', 'SZSE.000001', 'SHSE.600000', 'SHSE.600036', 'SZSE.000002']
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # 同时获取多个标的的数据
        symbols_str = ','.join(symbols)
        print(f"同时获取标的: {symbols_str}")
        
        data = gm.history_n(
            symbol=symbols_str,
            frequency='1d',
            count=5,
            end_time=end_time,
            fields='symbol,eob,open,high,low,close,volume',
            df=True
        )
        
        if data is not None and not data.empty:
            print(f"✓ 成功获取 {len(data)} 条数据")
            print(f"  包含标的: {data['symbol'].unique()}")
            
            # 按标的分组显示
            for symbol in data['symbol'].unique():
                symbol_data = data[data['symbol'] == symbol]
                print(f"  {symbol}: {len(symbol_data)} 条数据")
                
        else:
            print("✗ 未获取到数据")
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")

if __name__ == "__main__":
    # 运行测试
    test_history_n_api()
    test_history_n_edge_cases()
    test_history_n_multiple_symbols()