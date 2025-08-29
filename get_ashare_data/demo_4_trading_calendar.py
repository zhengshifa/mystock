#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK - 交易日历查询测试Demo
测试 get_trading_dates, get_next_trading_date, get_previous_trading_date 等函数
"""

import json
import pandas as pd
import os
from datetime import datetime, timedelta
from gm.api import *

def configure_token():
    """
    配置GM SDK的token
    支持多种配置方式：
    1. 直接设置token
    2. 从配置文件读取
    3. 从环境变量读取
    """
    
    # 方法1: 直接设置token（不推荐，仅用于测试）
    # set_token('your_token_here')
    
    # 方法2: 从配置文件读取（推荐）
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
    
    # 方法3: 从环境变量读取
    token = os.getenv('GM_TOKEN')
    if token:
        set_token(token)
        print("已从环境变量 GM_TOKEN 读取token")
        return True
    
    print("警告: 未找到有效的token配置")
    print("请通过以下方式之一配置token:")
    print("1. 创建 gm_config.json 文件并设置token")
    print("2. 设置环境变量 GM_TOKEN")
    print("3. 在代码中直接调用 set_token('your_token')")
    return False

def test_trading_calendar():
    """测试交易日历查询"""
    print("=" * 60)
    print("交易日历查询测试Demo")
    print("=" * 60)
    
    results = {}
    
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试 get_trading_dates 函数
    print("\n" + "=" * 40)
    print("1. 测试 get_trading_dates 函数")
    print("=" * 40)
    
    trading_dates_results = {}
    
    # 测试不同时间范围的交易日
    date_test_cases = [
        {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'name': '2024年1月交易日'
        },
        {
            'start_date': '2024-06-01',
            'end_date': '2024-06-30',
            'name': '2024年6月交易日'
        },
        {
            'start_date': '2023-12-01',
            'end_date': '2023-12-31',
            'name': '2023年12月交易日'
        },
        {
            'start_date': '2024-10-01',
            'end_date': '2024-10-31',
            'name': '2024年10月交易日（含国庆假期）'
        }
    ]
    
    for case in date_test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            trading_dates = get_trading_dates(
                exchange='SHSE',
                start_date=case['start_date'],
                end_date=case['end_date']
            )
            
            if trading_dates is not None and len(trading_dates) > 0:
                trading_dates_results[case['name']] = {
                    'count': len(trading_dates),
                    'start_date': case['start_date'],
                    'end_date': case['end_date'],
                    'first_trading_date': str(trading_dates[0]),
                    'last_trading_date': str(trading_dates[-1]),
                    'all_dates': [str(date) for date in trading_dates]
                }
                print(f"    ✓ 获取到 {len(trading_dates)} 个交易日")
                print(f"    ✓ 首个交易日: {trading_dates[0]}")
                print(f"    ✓ 最后交易日: {trading_dates[-1]}")
                
                # 保存到CSV
                df = pd.DataFrame({
                    'trading_date': [str(date) for date in trading_dates]
                })
                csv_filename = f"trading_dates_{case['name'].replace('/', '_').replace('（', '_').replace('）', '')}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                trading_dates_results[case['name']] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            trading_dates_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['trading_dates_test'] = trading_dates_results
    
    # 2. 测试 get_trading_dates_by_year 函数
    print("\n" + "=" * 40)
    print("2. 测试 get_trading_dates_by_year 函数")
    print("=" * 40)
    
    yearly_dates_results = {}
    
    # 测试不同年份的交易日
    years = [2022, 2023, 2024]
    
    for year in years:
        try:
            print(f"\n测试: {year}年交易日")
            
            # 修复：get_trading_dates_by_year 的正确参数是 start_year 和 end_year
            yearly_dates = get_trading_dates_by_year(
                exchange='SHSE',
                start_year=year,
                end_year=year
            )
            
            if yearly_dates is not None and len(yearly_dates) > 0:
                yearly_dates_results[f'{year}年'] = {
                    'count': len(yearly_dates),
                    'year': year,
                    'first_trading_date': str(yearly_dates[0]),
                    'last_trading_date': str(yearly_dates[-1]),
                    'sample_dates': [str(date) for date in yearly_dates[:10]]  # 前10个交易日
                }
                print(f"    ✓ 获取到 {len(yearly_dates)} 个交易日")
                print(f"    ✓ 首个交易日: {yearly_dates[0]}")
                print(f"    ✓ 最后交易日: {yearly_dates[-1]}")
                
                # 保存到CSV
                df = pd.DataFrame({
                    'trading_date': [str(date) for date in yearly_dates]
                })
                csv_filename = f"trading_dates_{year}年.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                yearly_dates_results[f'{year}年'] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            yearly_dates_results[f'{year}年'] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['yearly_dates_test'] = yearly_dates_results
    
    # 3. 测试 get_next_trading_date 函数
    print("\n" + "=" * 40)
    print("3. 测试 get_next_trading_date 函数")
    print("=" * 40)
    
    next_date_results = {}
    
    # 测试不同日期的下一个交易日
    test_dates = [
        '2024-01-01',  # 元旦
        '2024-02-09',  # 春节前
        '2024-02-18',  # 春节后
        '2024-05-01',  # 劳动节
        '2024-10-01',  # 国庆节
        '2024-12-31',  # 年末
        '2024-06-15',  # 普通工作日
        '2024-06-16',  # 周日
    ]
    
    for test_date in test_dates:
        try:
            print(f"\n测试日期: {test_date}")
            
            next_date = get_next_trading_date(
                exchange='SHSE',
                date=test_date
            )
            
            if next_date is not None:
                next_date_results[test_date] = {
                    'input_date': test_date,
                    'next_trading_date': str(next_date)
                }
                print(f"    ✓ 下一个交易日: {next_date}")
                
            else:
                next_date_results[test_date] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            next_date_results[test_date] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['next_date_test'] = next_date_results
    
    # 4. 测试 get_previous_trading_date 函数
    print("\n" + "=" * 40)
    print("4. 测试 get_previous_trading_date 函数")
    print("=" * 40)
    
    prev_date_results = {}
    
    for test_date in test_dates:
        try:
            print(f"\n测试日期: {test_date}")
            
            prev_date = get_previous_trading_date(
                exchange='SHSE',
                date=test_date
            )
            
            if prev_date is not None:
                prev_date_results[test_date] = {
                    'input_date': test_date,
                    'previous_trading_date': str(prev_date)
                }
                print(f"    ✓ 上一个交易日: {prev_date}")
                
            else:
                prev_date_results[test_date] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            prev_date_results[test_date] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['prev_date_test'] = prev_date_results
    
    # 5. 测试 get_next_n_trading_dates 函数
    print("\n" + "=" * 40)
    print("5. 测试 get_next_n_trading_dates 函数")
    print("=" * 40)
    
    next_n_dates_results = {}
    
    # 测试获取未来N个交易日
    n_dates_test_cases = [
        {'date': '2024-01-01', 'n': 5, 'name': '元旦后5个交易日'},
        {'date': '2024-06-15', 'n': 10, 'name': '6月15日后10个交易日'},
        {'date': '2024-09-30', 'n': 3, 'name': '国庆前后3个交易日'},
    ]
    
    for case in n_dates_test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            next_n_dates = get_next_n_trading_dates(
                exchange='SHSE',
                date=case['date'],
                n=case['n']
            )
            
            if next_n_dates is not None and len(next_n_dates) > 0:
                next_n_dates_results[case['name']] = {
                    'input_date': case['date'],
                    'n': case['n'],
                    'count': len(next_n_dates),
                    'dates': [str(date) for date in next_n_dates]
                }
                print(f"    ✓ 获取到 {len(next_n_dates)} 个交易日")
                print(f"    ✓ 日期列表: {[str(date) for date in next_n_dates]}")
                
            else:
                next_n_dates_results[case['name']] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            next_n_dates_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['next_n_dates_test'] = next_n_dates_results
    
    # 6. 测试 get_previous_n_trading_dates 函数
    print("\n" + "=" * 40)
    print("6. 测试 get_previous_n_trading_dates 函数")
    print("=" * 40)
    
    prev_n_dates_results = {}
    
    for case in n_dates_test_cases:
        try:
            print(f"\n测试: {case['name'].replace('后', '前')}")
            
            prev_n_dates = get_previous_n_trading_dates(
                exchange='SHSE',
                date=case['date'],
                n=case['n']
            )
            
            if prev_n_dates is not None and len(prev_n_dates) > 0:
                prev_n_dates_results[case['name'].replace('后', '前')] = {
                    'input_date': case['date'],
                    'n': case['n'],
                    'count': len(prev_n_dates),
                    'dates': [str(date) for date in prev_n_dates]
                }
                print(f"    ✓ 获取到 {len(prev_n_dates)} 个交易日")
                print(f"    ✓ 日期列表: {[str(date) for date in prev_n_dates]}")
                
            else:
                prev_n_dates_results[case['name'].replace('后', '前')] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            prev_n_dates_results[case['name'].replace('后', '前')] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['prev_n_dates_test'] = prev_n_dates_results
    
    # 7. 测试交易时间查询
    print("\n" + "=" * 40)
    print("7. 测试交易时间查询")
    print("=" * 40)
    
    trading_times_results = {}
    
    try:
        print(f"\n查询交易时间信息...")
        
        # 测试不同交易所的交易时间
        exchanges = ['SHSE', 'SZSE']
        
        for exchange in exchanges:
            try:
                # 修复：get_trading_times 的参数是 variety_names，不是 exchange
                # 对于股票市场，使用对应的品种名称
                variety_name = 'STK' if exchange == 'SHSE' or exchange == 'SZSE' else exchange
                trading_times = get_trading_times(variety_names=variety_name)
                
                if trading_times is not None:
                    trading_times_results[exchange] = {
                        'exchange': exchange,
                        'trading_times': str(trading_times)
                    }
                    print(f"    ✓ {exchange} 交易时间: {trading_times}")
                    
                else:
                    trading_times_results[exchange] = {'error': '无数据返回'}
                    print(f"    ✗ {exchange} 无数据返回")
                    
            except Exception as e:
                trading_times_results[exchange] = {'error': str(e)}
                print(f"    ✗ {exchange} 错误: {e}")
        
    except Exception as e:
        trading_times_results = {'error': str(e)}
        print(f"    ✗ 交易时间查询错误: {e}")
    
    results['trading_times_test'] = trading_times_results
    
    # 保存测试结果
    with open('demo_4_trading_calendar_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("交易日历查询测试完成！")
    print("详细结果已保存到: demo_4_trading_calendar_results.json")
    print("CSV数据文件已保存到当前目录")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    try:
        # 配置token
        if not configure_token():
            print("\n请先配置有效的token后再运行测试")
            exit(1)
        
        # 测试token有效性
        try:
            test_dates = get_trading_dates('SHSE', '2024-01-01', '2024-01-05')
            if not test_dates:
                print("Token验证失败，请检查token是否有效")
                exit(1)
            print("Token验证成功")
        except Exception as e:
            print(f"Token验证失败: {e}")
            exit(1)
        
        # 运行测试
        test_results = test_trading_calendar()
        
        # 打印总结
        print("\n测试总结:")
        
        if 'trading_dates_test' in test_results:
            total_dates = len(test_results['trading_dates_test'])
            successful_dates = sum(1 for data in test_results['trading_dates_test'].values() if 'error' not in data)
            print(f"get_trading_dates函数测试: {successful_dates}/{total_dates} 成功")
        
        if 'yearly_dates_test' in test_results:
            total_yearly = len(test_results['yearly_dates_test'])
            successful_yearly = sum(1 for data in test_results['yearly_dates_test'].values() if 'error' not in data)
            print(f"get_trading_dates_by_year函数测试: {successful_yearly}/{total_yearly} 成功")
        
        if 'next_date_test' in test_results:
            total_next = len(test_results['next_date_test'])
            successful_next = sum(1 for data in test_results['next_date_test'].values() if 'error' not in data)
            print(f"get_next_trading_date函数测试: {successful_next}/{total_next} 成功")
        
        if 'prev_date_test' in test_results:
            total_prev = len(test_results['prev_date_test'])
            successful_prev = sum(1 for data in test_results['prev_date_test'].values() if 'error' not in data)
            print(f"get_previous_trading_date函数测试: {successful_prev}/{total_prev} 成功")
        
        if 'next_n_dates_test' in test_results:
            total_next_n = len(test_results['next_n_dates_test'])
            successful_next_n = sum(1 for data in test_results['next_n_dates_test'].values() if 'error' not in data)
            print(f"get_next_n_trading_dates函数测试: {successful_next_n}/{total_next_n} 成功")
        
        if 'prev_n_dates_test' in test_results:
            total_prev_n = len(test_results['prev_n_dates_test'])
            successful_prev_n = sum(1 for data in test_results['prev_n_dates_test'].values() if 'error' not in data)
            print(f"get_previous_n_trading_dates函数测试: {successful_prev_n}/{total_prev_n} 成功")
        
        trading_times_success = 'error' not in test_results.get('trading_times_test', {'error': 'not tested'})
        print(f"交易时间查询测试: {'成功' if trading_times_success else '失败'}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()