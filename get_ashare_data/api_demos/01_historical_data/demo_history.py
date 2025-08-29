#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: history() 函数测试
功能：获取历史数据
"""

import gmtrade as gm
import pandas as pd
import json
import os
from datetime import datetime, timedelta

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'gm_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_history_api():
    """测试 gm.history() API"""
    print("=" * 60)
    print("GM API Demo: history() 函数测试")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 设置token
    gm.set_token(config['token'])
    
    # 测试参数
    symbols = ['SHSE.000001', 'SZSE.000001', 'SHSE.600000']
    end_time = datetime.now().strftime('%Y-%m-%d')
    start_time = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    results = {}
    
    for symbol in symbols:
        print(f"\n测试标的: {symbol}")
        print("-" * 40)
        
        try:
            # 测试不同频率的历史数据
            frequencies = ['1d', '1m', '5m', '15m', '30m', '60m']
            
            for freq in frequencies:
                print(f"\n获取 {freq} 频率数据...")
                
                # 调用 gm.history() API
                data = gm.history(
                    symbol=symbol,
                    frequency=freq,
                    start_time=start_time,
                    end_time=end_time,
                    fields='symbol,eob,open,high,low,close,volume,amount',
                    skip_suspended=True,
                    fill_missing='Last',
                    adjust=gm.ADJUST_PREV,
                    df=True
                )
                
                if data is not None and not data.empty:
                    print(f"✓ 成功获取 {len(data)} 条 {freq} 数据")
                    print(f"  数据列: {list(data.columns)}")
                    print(f"  时间范围: {data.index[0]} 到 {data.index[-1]}")
                    print(f"  样本数据:")
                    print(data.head(2).to_string())
                    
                    # 保存结果
                    if symbol not in results:
                        results[symbol] = {}
                    
                    results[symbol][freq] = {
                        'data_count': len(data),
                        'columns': list(data.columns),
                        'start_time': str(data.index[0]),
                        'end_time': str(data.index[-1]),
                        'sample_data': data.head(2).to_dict(),
                        'data_types': {col: str(data[col].dtype) for col in data.columns}
                    }
                    
                    # 保存CSV文件
                    csv_filename = f"history_{symbol.replace('.', '_')}_{freq}.csv"
                    csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
                    data.to_csv(csv_path, encoding='utf-8-sig')
                    print(f"  已保存到: {csv_filename}")
                    
                else:
                    print(f"✗ 未获取到 {freq} 数据")
                    
        except Exception as e:
            print(f"✗ 获取 {symbol} 数据时出错: {str(e)}")
            results[symbol] = {'error': str(e)}
    
    # 保存测试结果
    result_file = os.path.join(os.path.dirname(__file__), 'history_test_results.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=" * 60)
    print(f"测试完成！结果已保存到: history_test_results.json")
    print(f"=" * 60)
    
    return results

def test_history_with_different_params():
    """测试 history() 的不同参数组合"""
    print("\n" + "=" * 60)
    print("测试 history() 不同参数组合")
    print("=" * 60)
    
    config = load_config()
    gm.set_token(config['token'])
    
    symbol = 'SHSE.000001'
    end_time = datetime.now().strftime('%Y-%m-%d')
    start_time = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # 测试不同的复权方式
    adjust_types = {
        'ADJUST_NONE': gm.ADJUST_NONE,
        'ADJUST_PREV': gm.ADJUST_PREV,
        'ADJUST_POST': gm.ADJUST_POST
    }
    
    for adjust_name, adjust_type in adjust_types.items():
        print(f"\n测试复权方式: {adjust_name}")
        try:
            data = gm.history(
                symbol=symbol,
                frequency='1d',
                start_time=start_time,
                end_time=end_time,
                fields='symbol,eob,open,high,low,close,volume,amount',
                adjust=adjust_type,
                df=True
            )
            
            if data is not None and not data.empty:
                print(f"✓ 获取到 {len(data)} 条数据")
                print(f"  收盘价范围: {data['close'].min():.2f} - {data['close'].max():.2f}")
            else:
                print("✗ 未获取到数据")
                
        except Exception as e:
            print(f"✗ 错误: {str(e)}")

if __name__ == "__main__":
    # 运行测试
    test_history_api()
    test_history_with_different_params()