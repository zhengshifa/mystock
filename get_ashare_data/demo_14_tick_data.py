#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tick数据查询演示

本脚本演示如何使用GM SDK获取Tick数据，包括：
1. current - 查询当前行情快照
2. last_tick - 查询最新tick数据
3. get_history_l2ticks - 查询历史L2 tick数据
4. get_history_ticks_l2 - 查询历史L2 tick数据（另一种接口）

注意：部分功能需要相应的数据权限
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from gm.api import *
import os

# ============================================================
# Token配置 - 从配置文件读取
# ============================================================

def configure_token():
    """
    配置GM SDK的token
    支持多种配置方式：
    1. 从配置文件读取（推荐）
    2. 从环境变量读取
    3. 直接设置token
    """
    
    # 方法1: 从配置文件读取（推荐）
    config_file = 'gm_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'token' in config and config['token']:
                    set_token(config['token'])
                    print(f"已从配置文件 {config_file} 读取token")
                    return True
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    
    # 方法2: 从环境变量读取
    token = os.getenv('GM_TOKEN')
    if token:
        set_token(token)
        print("已从环境变量 GM_TOKEN 读取token")
        return True
    
    # 方法3: 直接设置token（备用）
    set_token('d5791ecb0f33260e9fd719227c36f5c28b42e11c')
    print("使用默认token")
    return True

def test_current_tick():
    """
    测试获取当前行情快照
    """
    print("\n=== 测试 current 函数 - 获取当前行情快照 ===")
    
    test_results = []
    
    # 测试用例
    test_cases = [
        {
            'symbols': ['SHSE.000001', 'SZSE.000001'],
            'fields': '',
            'name': '获取上证指数和深证成指当前行情'
        },
        {
            'symbols': ['SHSE.600000', 'SHSE.600036'],
            'fields': 'symbol,last_price,volume,amount,open,high,low,pre_close',
            'name': '获取浦发银行和招商银行指定字段行情'
        },
        {
            'symbols': ['SZSE.000858', 'SZSE.002415'],
            'fields': 'symbol,last_price,bid_p,ask_p,bid_v,ask_v',
            'name': '获取五粮液和海康威视买卖盘口数据'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试{i}: {case['name']}")
        try:
            result = current(
                symbols=case['symbols'],
                fields=case['fields']
            )
            
            test_result = {
                'test_name': case['name'],
                'function': 'current',
                'symbols': case['symbols'],
                'fields': case['fields'],
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:2] if result and len(result) > 0 else None
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 个标的的tick数据")
                for tick in result[:2]:  # 显示前2个
                    print(f"  标的: {tick.get('symbol', 'N/A')}, 最新价: {tick.get('last_price', 'N/A')}, 成交量: {tick.get('volume', 'N/A')}")
                
                # 保存为CSV
                if isinstance(result, list) and len(result) > 0:
                    df = pd.DataFrame(result)
                    csv_filename = f"current_tick_{case['name'].replace(' ', '_').replace('（', '_').replace('）', '')}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  ✓ 数据已保存到 {csv_filename}")
            else:
                print(f"  ✗ 无数据返回")
                
        except Exception as e:
            test_result = {
                'test_name': case['name'],
                'function': 'current',
                'status': 'error',
                'error': str(e)
            }
            print(f"  ✗ 错误: {e}")
        
        test_results.append(test_result)
    
    return test_results

def test_last_tick():
    """
    测试获取最新tick数据
    """
    print("\n=== 测试 last_tick 函数 - 获取最新tick数据 ===")
    
    test_results = []
    
    # 测试用例
    test_cases = [
        {
            'symbols': ['SHSE.600519', 'SHSE.600036'],
            'fields': '',
            'name': '获取贵州茅台和招商银行最新tick'
        },
        {
            'symbols': ['SZSE.000858', 'SZSE.300750'],
            'fields': 'symbol,last_price,volume,amount,bid_p,ask_p',
            'name': '获取五粮液和宁德时代指定字段tick'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试{i}: {case['name']}")
        try:
            result = last_tick(
                symbols=case['symbols'],
                fields=case['fields']
            )
            
            test_result = {
                'test_name': case['name'],
                'function': 'last_tick',
                'symbols': case['symbols'],
                'fields': case['fields'],
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:2] if result and len(result) > 0 else None
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 个标的的最新tick数据")
                for tick in result[:2]:  # 显示前2个
                    print(f"  标的: {tick.get('symbol', 'N/A')}, 最新价: {tick.get('last_price', 'N/A')}, 时间: {tick.get('created_at', 'N/A')}")
                
                # 保存为CSV
                if isinstance(result, list) and len(result) > 0:
                    df = pd.DataFrame(result)
                    csv_filename = f"last_tick_{case['name'].replace(' ', '_').replace('（', '_').replace('）', '')}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  ✓ 数据已保存到 {csv_filename}")
            else:
                print(f"  ✗ 无数据返回")
                
        except Exception as e:
            test_result = {
                'test_name': case['name'],
                'function': 'last_tick',
                'status': 'error',
                'error': str(e)
            }
            print(f"  ✗ 错误: {e}")
        
        test_results.append(test_result)
    
    return test_results

def test_history_l2ticks():
    """
    测试获取历史L2 tick数据
    """
    print("\n=== 测试 get_history_l2ticks 函数 - 获取历史L2 tick数据 ===")
    
    test_results = []
    
    # 获取最近的交易日
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 测试用例
        test_cases = [
            {
                'symbols': ['SHSE.600000'],
                'start_time': f'{start_date} 09:30:00',
                'end_time': f'{start_date} 10:00:00',
                'fields': None,
                'name': '获取浦发银行30分钟L2 tick数据'
            },
            {
                'symbols': ['SZSE.000001'],
                'start_time': f'{start_date} 14:00:00',
                'end_time': f'{start_date} 14:30:00',
                'fields': 'symbol,created_at,last_price,volume',  # 传入字符串而不是列表
                'name': '获取深证成指指定字段L2 tick数据'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试{i}: {case['name']}")
            try:
                result = get_history_l2ticks(
                    symbols=case['symbols'][0],  # 传入单个字符串而不是列表
                    start_time=case['start_time'],
                    end_time=case['end_time'],
                    fields=case['fields'],
                    df=True
                )
                
                test_result = {
                    'test_name': case['name'],
                    'function': 'get_history_l2ticks',
                    'symbols': case['symbols'],
                    'start_time': case['start_time'],
                    'end_time': case['end_time'],
                    'fields': case['fields'],
                    'status': 'success' if result is not None and not result.empty else 'no_data',
                    'result_count': len(result) if result is not None and not result.empty else 0
                }
                
                if result is not None and not result.empty:
                    print(f"  ✓ 成功获取 {len(result)} 条L2 tick数据")
                    print(f"  ✓ 数据时间范围: {result.index[0]} 到 {result.index[-1]}")
                    print(f"  ✓ 数据列: {list(result.columns)}")
                    
                    # 保存为CSV
                    csv_filename = f"history_l2ticks_{case['symbols'][0].replace('.', '_')}_{start_date.replace('-', '')}.csv"
                    result.to_csv(csv_filename, encoding='utf-8-sig')
                    print(f"  ✓ 数据已保存到 {csv_filename}")
                else:
                    print(f"  ✗ 无数据返回")
                    
            except Exception as e:
                test_result = {
                    'test_name': case['name'],
                    'function': 'get_history_l2ticks',
                    'status': 'error',
                    'error': str(e)
                }
                print(f"  ✗ 错误: {e}")
            
            test_results.append(test_result)
            
    except Exception as e:
        print(f"  ✗ 获取交易日期错误: {e}")
        test_results.append({
            'function': 'get_history_l2ticks',
            'status': 'error',
            'error': f'获取交易日期错误: {e}'
        })
    
    return test_results

def test_history_ticks_l2():
    """
    测试获取历史L2 tick数据（另一种接口）
    """
    print("\n=== 测试 get_history_ticks_l2 函数 - 获取历史L2 tick数据 ===")
    
    test_results = []
    
    # 获取最近的交易日
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 测试用例
        test_cases = [
            {
                'symbols': ['SHSE.600036'],
                'start_time': f'{start_date} 09:30:00',
                'end_time': f'{start_date} 10:00:00',
                'fields': None,
                'name': '获取招商银行30分钟L2 tick数据'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试{i}: {case['name']}")
            try:
                result = get_history_ticks_l2(
                    symbols=case['symbols'][0],  # 传入单个字符串而不是列表
                    start_time=case['start_time'],
                    end_time=case['end_time'],
                    fields=case['fields'],
                    df=True
                )
                
                test_result = {
                    'test_name': case['name'],
                    'function': 'get_history_ticks_l2',
                    'symbols': case['symbols'],
                    'start_time': case['start_time'],
                    'end_time': case['end_time'],
                    'fields': case['fields'],
                    'status': 'success' if result is not None and not result.empty else 'no_data',
                    'result_count': len(result) if result is not None and not result.empty else 0
                }
                
                if result is not None and not result.empty:
                    print(f"  ✓ 成功获取 {len(result)} 条L2 tick数据")
                    print(f"  ✓ 数据时间范围: {result.index[0]} 到 {result.index[-1]}")
                    print(f"  ✓ 数据列: {list(result.columns)}")
                    
                    # 保存为CSV
                    csv_filename = f"history_ticks_l2_{case['symbols'][0].replace('.', '_')}_{start_date.replace('-', '')}.csv"
                    result.to_csv(csv_filename, encoding='utf-8-sig')
                    print(f"  ✓ 数据已保存到 {csv_filename}")
                else:
                    print(f"  ✗ 无数据返回")
                    
            except Exception as e:
                test_result = {
                    'test_name': case['name'],
                    'function': 'get_history_ticks_l2',
                    'status': 'error',
                    'error': str(e)
                }
                print(f"  ✗ 错误: {e}")
            
            test_results.append(test_result)
            
    except Exception as e:
        print(f"  ✗ 获取交易日期错误: {e}")
        test_results.append({
            'function': 'get_history_ticks_l2',
            'status': 'error',
            'error': f'获取交易日期错误: {e}'
        })
    
    return test_results

def main():
    """
    主函数
    """
    print("开始测试GM SDK Tick数据查询功能...")
    print("=" * 60)
    
    # 配置token
    if not configure_token():
        print("Token配置失败，退出测试")
        return
    
    # 存储所有测试结果
    all_results = {
        'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {}
    }
    
    try:
        # 测试当前行情快照
        current_results = test_current_tick()
        all_results['tests']['current_tick'] = current_results
        
        # 测试最新tick数据
        last_tick_results = test_last_tick()
        all_results['tests']['last_tick'] = last_tick_results
        
        # 测试历史L2 tick数据
        history_l2ticks_results = test_history_l2ticks()
        all_results['tests']['history_l2ticks'] = history_l2ticks_results
        
        # 测试历史L2 tick数据（另一种接口）
        history_ticks_l2_results = test_history_ticks_l2()
        all_results['tests']['history_ticks_l2'] = history_ticks_l2_results
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        all_results['error'] = str(e)
    
    # 保存测试结果
    with open('tick_data_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n=== 测试总结 ===")
    print(f"测试时间: {all_results['test_time']}")
    
    if 'tests' in all_results:
        for test_type, results in all_results['tests'].items():
            total_tests = len(results)
            successful_tests = sum(1 for result in results if result.get('status') == 'success')
            print(f"{test_type}测试: {successful_tests}/{total_tests} 成功")
    
    print("\n✓ 测试结果已保存到 tick_data_test_results.json")
    print("✓ CSV数据文件已保存到当前目录")
    print("\n注意: 部分tick数据功能需要相应的数据权限，如果遇到权限问题请联系数据提供商")

if __name__ == '__main__':
    main()