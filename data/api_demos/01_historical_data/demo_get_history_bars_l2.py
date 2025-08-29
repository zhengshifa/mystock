#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_history_bars_l2() 函数测试
功能：获取L2历史Bar数据
"""

import gm
import pandas as pd
import json
import os
from datetime import datetime, timedelta

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'gm_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_get_history_bars_l2_api():
    """测试 gm.get_history_bars_l2() API"""
    print("=" * 60)
    print("GM API Demo: get_history_bars_l2() 函数测试")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 设置token
    gm.set_token(config['token'])
    
    # 测试参数 - L2数据通常只对部分标的可用
    symbols = ['SHSE.000001', 'SZSE.000001', 'SHSE.600000', 'SHSE.600036']
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_time = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    results = {}
    
    for symbol in symbols:
        print(f"\n测试标的: {symbol}")
        print("-" * 40)
        
        try:
            # 测试不同频率的L2历史数据
            frequencies = ['1m', '5m', '15m', '30m']
            
            for freq in frequencies:
                print(f"\n获取 {freq} 频率L2数据...")
                
                # 调用 gm.get_history_bars_l2() API
                data = gm.get_history_bars_l2(
                    symbol=symbol,
                    frequency=freq,
                    start_time=start_time,
                    end_time=end_time,
                    fields='symbol,eob,open,high,low,close,volume,amount,vwap',
                    df=True
                )
                
                if data is not None and not data.empty:
                    print(f"✓ 成功获取 {len(data)} 条L2数据")
                    print(f"  数据列: {list(data.columns)}")
                    print(f"  时间范围: {data.index[0]} 到 {data.index[-1]}")
                    
                    # 显示VWAP信息（如果有）
                    if 'vwap' in data.columns:
                        print(f"  VWAP范围: {data['vwap'].min():.2f} - {data['vwap'].max():.2f}")
                    
                    print(f"  样本数据:")
                    print(data.head(2).to_string())
                    
                    # 保存结果
                    if symbol not in results:
                        results[symbol] = {}
                    
                    results[symbol][f"l2_{freq}"] = {
                        'data_count': len(data),
                        'columns': list(data.columns),
                        'start_time': str(data.index[0]),
                        'end_time': str(data.index[-1]),
                        'has_vwap': 'vwap' in data.columns,
                        'sample_data': data.head(2).to_dict(),
                        'data_types': {col: str(data[col].dtype) for col in data.columns}
                    }
                    
                    # 保存CSV文件
                    csv_filename = f"history_bars_l2_{symbol.replace('.', '_')}_{freq}.csv"
                    csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
                    data.to_csv(csv_path, encoding='utf-8-sig')
                    print(f"  已保存到: {csv_filename}")
                    
                else:
                    print(f"✗ 未获取到 {freq} L2数据")
                    
        except Exception as e:
            print(f"✗ 获取 {symbol} L2数据时出错: {str(e)}")
            if symbol not in results:
                results[symbol] = {}
            results[symbol]['error'] = str(e)
    
    # 保存测试结果
    result_file = os.path.join(os.path.dirname(__file__), 'history_bars_l2_test_results.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=" * 60)
    print(f"测试完成！结果已保存到: history_bars_l2_test_results.json")
    print(f"=" * 60)
    
    return results

def test_l2_data_analysis():
    """分析L2数据的特点"""
    print("\n" + "=" * 60)
    print("L2数据特点分析")
    print("=" * 60)
    
    config = load_config()
    gm.set_token(config['token'])
    
    symbol = 'SHSE.000001'
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_time = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # 获取L2数据
        print(f"获取 {symbol} 的L2数据进行分析...")
        
        l2_data = gm.get_history_bars_l2(
            symbol=symbol,
            frequency='1m',
            start_time=start_time,
            end_time=end_time,
            fields='symbol,eob,open,high,low,close,volume,amount,vwap',
            df=True
        )
        
        # 获取普通数据进行对比
        normal_data = gm.history(
            symbol=symbol,
            frequency='1m',
            start_time=start_time,
            end_time=end_time,
            fields='symbol,eob,open,high,low,close,volume,amount',
            df=True
        )
        
        if l2_data is not None and not l2_data.empty:
            print(f"✓ L2数据: {len(l2_data)} 条")
            print(f"  L2数据列: {list(l2_data.columns)}")
            
            if normal_data is not None and not normal_data.empty:
                print(f"✓ 普通数据: {len(normal_data)} 条")
                print(f"  普通数据列: {list(normal_data.columns)}")
                
                # 比较数据差异
                print("\n数据对比分析:")
                if len(l2_data) == len(normal_data):
                    print("  数据条数相同")
                else:
                    print(f"  数据条数不同: L2({len(l2_data)}) vs 普通({len(normal_data)})")
                
                # 比较VWAP与收盘价
                if 'vwap' in l2_data.columns:
                    vwap_close_diff = (l2_data['vwap'] - l2_data['close']).abs().mean()
                    print(f"  VWAP与收盘价平均差异: {vwap_close_diff:.4f}")
                    
                    # 显示VWAP统计信息
                    print(f"  VWAP统计:")
                    print(f"    最小值: {l2_data['vwap'].min():.2f}")
                    print(f"    最大值: {l2_data['vwap'].max():.2f}")
                    print(f"    平均值: {l2_data['vwap'].mean():.2f}")
                    print(f"    标准差: {l2_data['vwap'].std():.4f}")
            
        else:
            print("✗ 未获取到L2数据")
            
    except Exception as e:
        print(f"✗ 分析L2数据时出错: {str(e)}")

def test_l2_data_availability():
    """测试L2数据的可用性"""
    print("\n" + "=" * 60)
    print("测试L2数据可用性")
    print("=" * 60)
    
    config = load_config()
    gm.set_token(config['token'])
    
    # 测试更多标的的L2数据可用性
    test_symbols = [
        'SHSE.000001',  # 上证指数
        'SZSE.000001',  # 深证成指
        'SHSE.600000',  # 浦发银行
        'SHSE.600036',  # 招商银行
        'SZSE.000002',  # 万科A
        'SZSE.000858',  # 五粮液
        'SHSE.600519',  # 贵州茅台
        'SZSE.000001'   # 平安银行
    ]
    
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_time = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    availability_results = {}
    
    for symbol in test_symbols:
        print(f"\n测试 {symbol} L2数据可用性...")
        
        try:
            data = gm.get_history_bars_l2(
                symbol=symbol,
                frequency='1m',
                start_time=start_time,
                end_time=end_time,
                fields='symbol,eob,open,high,low,close,volume,amount',
                df=True
            )
            
            if data is not None and not data.empty:
                print(f"✓ 可用 - {len(data)} 条数据")
                availability_results[symbol] = {
                    'available': True,
                    'data_count': len(data),
                    'columns': list(data.columns)
                }
            else:
                print("✗ 不可用")
                availability_results[symbol] = {
                    'available': False,
                    'data_count': 0
                }
                
        except Exception as e:
            print(f"✗ 错误: {str(e)}")
            availability_results[symbol] = {
                'available': False,
                'error': str(e)
            }
    
    # 统计可用性
    available_count = sum(1 for result in availability_results.values() if result.get('available', False))
    total_count = len(availability_results)
    
    print(f"\nL2数据可用性统计:")
    print(f"  总测试标的: {total_count}")
    print(f"  可用标的: {available_count}")
    print(f"  可用率: {(available_count/total_count*100):.1f}%")
    
    # 保存可用性结果
    result_file = os.path.join(os.path.dirname(__file__), 'l2_availability_results.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(availability_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # 运行测试
    test_get_history_bars_l2_api()
    test_l2_data_analysis()
    test_l2_data_availability()