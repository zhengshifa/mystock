#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK - 历史行情数据测试Demo
测试 history 和 history_n 函数

重要提示：运行前请先配置token！
方法1：直接在代码中设置 set_token('your_token_here')
方法2：从配置文件读取，参考 token_config_example.py
"""

import json
import pandas as pd
import os
from datetime import datetime, timedelta
from gm.api import *

def configure_token():
    """
    配置掘金量化API Token
    请根据实际情况选择配置方法
    """
    # 方法1: 直接设置token（请替换为你的实际token）
    # set_token('your_actual_token_here')
    
    # 方法2: 从配置文件读取token
    config_file = 'gm_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                token = config.get('token', '')
                if token and token != '请在此处填入你的掘金量化API Token':
                    set_token(token)
                    print(f"✓ 已从配置文件加载token: {token[:10]}...")
                    return True
        except Exception as e:
            print(f"✗ 读取配置文件失败: {e}")
    
    # 方法3: 从环境变量读取token
    env_token = os.getenv('GM_TOKEN')
    if env_token:
        set_token(env_token)
        print(f"✓ 已从环境变量加载token: {env_token[:10]}...")
        return True
    
    print("\n⚠️  警告：未配置有效的token！")
    print("请选择以下方法之一配置token:")
    print("1. 在代码中直接设置: set_token('your_token')")
    print("2. 创建gm_config.json文件并填入token")
    print("3. 设置环境变量: set GM_TOKEN=your_token")
    print("4. 参考 token_config_example.py 文件")
    return False

def test_history_data():
    """测试历史行情数据获取"""
    print("=" * 60)
    print("历史行情数据测试Demo")
    print("=" * 60)
    
    results = {}
    
    # 测试股票代码
    test_symbols = [
        'SHSE.000001',  # 上证指数
        'SHSE.600111',
    ]
    
    # 测试不同频率
    frequencies = ['1d', '1m', '5m', '15m', '30m', '60m']
    
    # 设置时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)  # 最近30天
    
    print(f"测试时间范围: {start_time.strftime('%Y-%m-%d')} 到 {end_time.strftime('%Y-%m-%d')}")
    print(f"测试标的: {test_symbols}")
    print(f"测试频率: {frequencies}")
    
    # 1. 测试 history 函数
    print("\n" + "=" * 40)
    print("1. 测试 history 函数")
    print("=" * 40)
    
    history_results = {}
    
    for symbol in test_symbols:
        print(f"\n测试标的: {symbol}")
        symbol_results = {}
        
        for freq in frequencies:
            try:
                print(f"  频率: {freq}")
                
                # 获取历史数据
                data = history(
                    symbol=symbol,
                    frequency=freq,
                    start_time=start_time,
                    end_time=end_time,
                    fields='open,high,low,close,volume,amount',
                    df=True
                )
                
                if data is not None and not data.empty:
                    symbol_results[freq] = {
                        'data_count': len(data),
                        'columns': list(data.columns),
                        'date_range': {
                            'start': str(data.index[0]) if len(data) > 0 else None,
                            'end': str(data.index[-1]) if len(data) > 0 else None
                        },
                        'sample_data': data.head(3).to_dict() if len(data) > 0 else {},
                        'data_types': {col: str(data[col].dtype) for col in data.columns}
                    }
                    print(f"    ✓ 成功获取 {len(data)} 条数据")
                    print(f"    ✓ 列名: {list(data.columns)}")
                    print(f"    ✓ 时间范围: {data.index[0]} 到 {data.index[-1]}")
                    
                    # 保存样本数据到CSV
                    csv_filename = f"history_{symbol.replace('.', '_')}_{freq}.csv"
                    data.to_csv(csv_filename, encoding='utf-8-sig')
                    print(f"    ✓ 数据已保存到: {csv_filename}")
                    
                else:
                    symbol_results[freq] = {'error': '无数据返回'}
                    print(f"    ✗ 无数据返回")
                    
            except Exception as e:
                symbol_results[freq] = {'error': str(e)}
                print(f"    ✗ 错误: {e}")
        
        history_results[symbol] = symbol_results
    
    results['history_test'] = history_results
    
    # 2. 测试 history_n 函数
    print("\n" + "=" * 40)
    print("2. 测试 history_n 函数")
    print("=" * 40)
    
    history_n_results = {}
    
    # 测试不同的数据条数
    test_counts = [10, 50, 100, 200]
    
    for symbol in test_symbols[:2]:  # 只测试前两个标的
        print(f"\n测试标的: {symbol}")
        symbol_results = {}
        
        for count in test_counts:
            try:
                print(f"  获取最近 {count} 条日线数据")
                
                # 获取最近N条数据
                data = history_n(
                    symbol=symbol,
                    frequency='1d',
                    count=count,
                    fields='open,high,low,close,volume,amount',
                    df=True
                )
                
                if data is not None and not data.empty:
                    symbol_results[f'count_{count}'] = {
                        'actual_count': len(data),
                        'columns': list(data.columns),
                        'date_range': {
                            'start': str(data.index[0]) if len(data) > 0 else None,
                            'end': str(data.index[-1]) if len(data) > 0 else None
                        },
                        'latest_data': data.tail(1).to_dict() if len(data) > 0 else {}
                    }
                    print(f"    ✓ 实际获取 {len(data)} 条数据")
                    print(f"    ✓ 最新日期: {data.index[-1]}")
                    
                    # 保存数据
                    csv_filename = f"history_n_{symbol.replace('.', '_')}_last_{count}.csv"
                    data.to_csv(csv_filename, encoding='utf-8-sig')
                    print(f"    ✓ 数据已保存到: {csv_filename}")
                    
                else:
                    symbol_results[f'count_{count}'] = {'error': '无数据返回'}
                    print(f"    ✗ 无数据返回")
                    
            except Exception as e:
                symbol_results[f'count_{count}'] = {'error': str(e)}
                print(f"    ✗ 错误: {e}")
        
        history_n_results[symbol] = symbol_results
    
    results['history_n_test'] = history_n_results
    
    # 3. 测试不同字段组合
    print("\n" + "=" * 40)
    print("3. 测试不同字段组合")
    print("=" * 40)
    
    field_combinations = [
        'open,high,low,close',
        'open,high,low,close,volume',
        'open,high,low,close,volume,amount',
        'open,high,low,close,volume,amount,pre_close',
        None  # 默认字段
    ]
    
    field_test_results = {}
    test_symbol = 'SHSE.600036'  # 招商银行
    
    for i, fields in enumerate(field_combinations):
        try:
            field_name = f"fields_{i+1}" if fields else "default_fields"
            print(f"\n测试字段组合 {i+1}: {fields if fields else '默认字段'}")
            
            data = history(
                symbol=test_symbol,
                frequency='1d',
                start_time=end_time - timedelta(days=10),
                end_time=end_time,
                fields=fields,
                df=True
            )
            
            if data is not None and not data.empty:
                field_test_results[field_name] = {
                    'fields_requested': fields,
                    'columns_returned': list(data.columns),
                    'data_count': len(data),
                    'sample_row': data.iloc[0].to_dict() if len(data) > 0 else {}
                }
                print(f"    ✓ 返回列: {list(data.columns)}")
                print(f"    ✓ 数据条数: {len(data)}")
            else:
                field_test_results[field_name] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            field_test_results[field_name] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['field_test'] = field_test_results
    
    # 保存测试结果
    with open('demo_1_history_data_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("历史行情数据测试完成！")
    print("详细结果已保存到: demo_1_history_data_results.json")
    print("CSV数据文件已保存到当前目录")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    try:
        # 配置token
        if not configure_token():
            print("\n测试终止：请先配置有效的token")
            exit(1)
        
        # 运行测试
        test_results = test_history_data()
        
        # 打印总结
        print("\n测试总结:")
        if 'history_test' in test_results:
            total_tests = sum(len(symbol_data) for symbol_data in test_results['history_test'].values())
            successful_tests = sum(
                sum(1 for freq_data in symbol_data.values() if 'error' not in freq_data)
                for symbol_data in test_results['history_test'].values()
            )
            print(f"history函数测试: {successful_tests}/{total_tests} 成功")
        
        if 'history_n_test' in test_results:
            total_n_tests = sum(len(symbol_data) for symbol_data in test_results['history_n_test'].values())
            successful_n_tests = sum(
                sum(1 for count_data in symbol_data.values() if 'error' not in count_data)
                for symbol_data in test_results['history_n_test'].values()
            )
            print(f"history_n函数测试: {successful_n_tests}/{total_n_tests} 成功")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()