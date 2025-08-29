#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: current() 函数测试
功能：获取实时行情数据
"""

import gmtrade as gm
import pandas as pd
import json
import os
import time
from datetime import datetime

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'gm_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_current_api():
    """测试 gm.current() API"""
    print("=" * 60)
    print("GM API Demo: current() 函数测试")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 设置token
    gm.set_token(config['token'])
    
    # 测试参数
    symbols = ['SHSE.000001', 'SZSE.000001', 'SHSE.600000', 'SHSE.600036', 'SZSE.000002']
    
    results = {}
    
    for symbol in symbols:
        print(f"\n测试标的: {symbol}")
        print("-" * 40)
        
        try:
            # 获取实时行情数据
            print("获取实时行情数据...")
            
            # 调用 gm.current() API
            data = gm.current(
                symbols=symbol,
                fields='symbol,last_price,open,high,low,prev_close,volume,amount,position,bid,ask,bid_v,ask_v,created_at'
            )
            
            if data is not None and len(data) > 0:
                # 转换为DataFrame便于处理
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
                
                print(f"✓ 成功获取实时数据")
                print(f"  数据列: {list(df.columns)}")
                
                # 显示关键信息
                for _, row in df.iterrows():
                    print(f"  标的代码: {row.get('symbol', 'N/A')}")
                    print(f"  最新价: {row.get('last_price', 'N/A')}")
                    print(f"  开盘价: {row.get('open', 'N/A')}")
                    print(f"  最高价: {row.get('high', 'N/A')}")
                    print(f"  最低价: {row.get('low', 'N/A')}")
                    print(f"  昨收价: {row.get('prev_close', 'N/A')}")
                    print(f"  成交量: {row.get('volume', 'N/A')}")
                    print(f"  成交额: {row.get('amount', 'N/A')}")
                    
                    # 计算涨跌幅
                    if row.get('last_price') and row.get('prev_close'):
                        change_pct = (row['last_price'] / row['prev_close'] - 1) * 100
                        print(f"  涨跌幅: {change_pct:.2f}%")
                    
                    # 显示买卖盘信息
                    if row.get('bid') and row.get('ask'):
                        print(f"  买一价: {row.get('bid', 'N/A')} (量: {row.get('bid_v', 'N/A')})")
                        print(f"  卖一价: {row.get('ask', 'N/A')} (量: {row.get('ask_v', 'N/A')})")
                    
                    print(f"  数据时间: {row.get('created_at', 'N/A')}")
                
                # 保存结果
                results[symbol] = {
                    'success': True,
                    'data_count': len(df),
                    'columns': list(df.columns),
                    'data': df.to_dict('records')[0] if len(df) > 0 else {},
                    'timestamp': datetime.now().isoformat()
                }
                
                # 保存CSV文件
                csv_filename = f"current_{symbol.replace('.', '_')}.csv"
                csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
                df.to_csv(csv_path, encoding='utf-8-sig', index=False)
                print(f"  已保存到: {csv_filename}")
                
            else:
                print(f"✗ 未获取到实时数据")
                results[symbol] = {
                    'success': False,
                    'error': 'No data returned',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"✗ 获取 {symbol} 实时数据时出错: {str(e)}")
            results[symbol] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # 保存测试结果
    result_file = os.path.join(os.path.dirname(__file__), 'current_test_results.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=" * 60)
    print(f"测试完成！结果已保存到: current_test_results.json")
    print(f"=" * 60)
    
    return results

def test_current_multiple_symbols():
    """测试 current() 多标的同时获取"""
    print("\n" + "=" * 60)
    print("测试 current() 多标的同时获取")
    print("=" * 60)
    
    config = load_config()
    gm.set_token(config['token'])
    
    # 多个标的
    symbols = ['SHSE.000001', 'SZSE.000001', 'SHSE.600000', 'SHSE.600036', 'SZSE.000002']
    symbols_str = ','.join(symbols)
    
    try:
        print(f"同时获取标的: {symbols_str}")
        
        data = gm.current(
            symbols=symbols_str,
            fields='symbol,last_price,open,high,low,prev_close,volume,amount,created_at'
        )
        
        if data is not None and len(data) > 0:
            df = pd.DataFrame(data)
            print(f"✓ 成功获取 {len(df)} 个标的的实时数据")
            
            # 显示汇总信息
            print("\n实时数据汇总:")
            for _, row in df.iterrows():
                symbol = row.get('symbol', 'N/A')
                last_price = row.get('last_price', 0)
                prev_close = row.get('prev_close', 0)
                
                if last_price and prev_close:
                    change_pct = (last_price / prev_close - 1) * 100
                    print(f"  {symbol}: {last_price} ({change_pct:+.2f}%)")
                else:
                    print(f"  {symbol}: {last_price}")
            
            # 保存多标的数据
            csv_filename = "current_multiple_symbols.csv"
            csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
            df.to_csv(csv_path, encoding='utf-8-sig', index=False)
            print(f"\n已保存到: {csv_filename}")
            
        else:
            print("✗ 未获取到数据")
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")

def test_current_different_fields():
    """测试 current() 不同字段组合"""
    print("\n" + "=" * 60)
    print("测试 current() 不同字段组合")
    print("=" * 60)
    
    config = load_config()
    gm.set_token(config['token'])
    
    symbol = 'SHSE.000001'
    
    # 测试不同的字段组合
    field_combinations = [
        {
            'name': '基础字段',
            'fields': 'symbol,last_price,open,high,low,prev_close'
        },
        {
            'name': '成交信息',
            'fields': 'symbol,last_price,volume,amount,position'
        },
        {
            'name': '买卖盘信息',
            'fields': 'symbol,last_price,bid,ask,bid_v,ask_v'
        },
        {
            'name': '完整信息',
            'fields': 'symbol,last_price,open,high,low,prev_close,volume,amount,position,bid,ask,bid_v,ask_v,created_at,updated_at'
        }
    ]
    
    for combo in field_combinations:
        print(f"\n测试字段组合: {combo['name']}")
        print(f"字段: {combo['fields']}")
        
        try:
            data = gm.current(
                symbols=symbol,
                fields=combo['fields']
            )
            
            if data is not None and len(data) > 0:
                df = pd.DataFrame(data)
                print(f"✓ 成功获取数据")
                print(f"  返回字段: {list(df.columns)}")
                print(f"  数据样本: {df.iloc[0].to_dict()}")
            else:
                print("✗ 未获取到数据")
                
        except Exception as e:
            print(f"✗ 错误: {str(e)}")

def test_current_realtime_monitoring():
    """测试 current() 实时监控"""
    print("\n" + "=" * 60)
    print("测试 current() 实时监控 (5次采样)")
    print("=" * 60)
    
    config = load_config()
    gm.set_token(config['token'])
    
    symbol = 'SHSE.000001'
    monitoring_data = []
    
    try:
        for i in range(5):
            print(f"\n第 {i+1} 次采样 ({datetime.now().strftime('%H:%M:%S')})")
            
            data = gm.current(
                symbols=symbol,
                fields='symbol,last_price,volume,amount,created_at'
            )
            
            if data is not None and len(data) > 0:
                df = pd.DataFrame(data)
                row = df.iloc[0]
                
                sample_data = {
                    'sample_time': datetime.now().isoformat(),
                    'data_time': row.get('created_at'),
                    'last_price': row.get('last_price'),
                    'volume': row.get('volume'),
                    'amount': row.get('amount')
                }
                
                monitoring_data.append(sample_data)
                
                print(f"  价格: {sample_data['last_price']}")
                print(f"  成交量: {sample_data['volume']}")
                print(f"  成交额: {sample_data['amount']}")
                print(f"  数据时间: {sample_data['data_time']}")
                
            else:
                print("  ✗ 未获取到数据")
            
            # 间隔3秒
            if i < 4:
                time.sleep(3)
        
        # 保存监控数据
        if monitoring_data:
            monitoring_df = pd.DataFrame(monitoring_data)
            csv_filename = "current_monitoring.csv"
            csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
            monitoring_df.to_csv(csv_path, encoding='utf-8-sig', index=False)
            
            print(f"\n监控数据已保存到: {csv_filename}")
            
            # 分析价格变化
            if len(monitoring_data) > 1:
                prices = [d['last_price'] for d in monitoring_data if d['last_price']]
                if len(prices) > 1:
                    price_change = prices[-1] - prices[0]
                    print(f"监控期间价格变化: {price_change:+.4f}")
        
    except Exception as e:
        print(f"✗ 监控过程中出错: {str(e)}")

if __name__ == "__main__":
    # 运行测试
    test_current_api()
    test_current_multiple_symbols()
    test_current_different_fields()
    test_current_realtime_monitoring()