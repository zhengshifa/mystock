#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_trading_dates() 获取交易日历
功能：测试 gm.get_trading_dates() API的各种用法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import gmtrade as gm
import pandas as pd
import json
from datetime import datetime, timedelta
import time

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'gm_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None

def init_gm_api(config):
    """初始化GM API"""
    try:
        # 设置token
        gm.set_token(config['token'])
        
        # 设置服务地址
        gm.set_serv_addr(config['md_addr'])
        
        print("GM API初始化成功")
        return True
    except Exception as e:
        print(f"GM API初始化失败: {e}")
        return False

def format_trading_dates(trading_dates):
    """格式化交易日期数据"""
    if trading_dates is None:
        return []
    
    formatted_dates = []
    
    try:
        if hasattr(trading_dates, '__iter__') and not isinstance(trading_dates, str):
            for date in trading_dates:
                if hasattr(date, 'strftime'):
                    formatted_dates.append(date.strftime('%Y-%m-%d'))
                else:
                    formatted_dates.append(str(date))
        else:
            if hasattr(trading_dates, 'strftime'):
                formatted_dates.append(trading_dates.strftime('%Y-%m-%d'))
            else:
                formatted_dates.append(str(trading_dates))
    except Exception as e:
        print(f"格式化交易日期失败: {e}")
        formatted_dates = [str(trading_dates)]
    
    return formatted_dates

def test_get_trading_dates_basic():
    """测试基本的交易日历查询"""
    print("\n=== 测试基本交易日历查询 ===")
    
    test_cases = [
        {
            'name': '当前月份',
            'start_date': datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '上个月',
            'start_date': (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d'),
            'end_date': (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'name': '2024年1月',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        },
        {
            'name': '2024年全年',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        },
        {
            'name': '2023年全年',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n查询 {test_case['name']} ({test_case['start_date']} 到 {test_case['end_date']})...")
            
            # 获取交易日历
            trading_dates = gm.get_trading_dates(
                exchange='SHSE',
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if trading_dates is not None:
                formatted_dates = format_trading_dates(trading_dates)
                
                result = {
                    'test_name': test_case['name'],
                    'exchange': 'SHSE',
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'trading_dates': formatted_dates,
                    'count': len(formatted_dates),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(formatted_dates)} 个交易日")
                
                if formatted_dates:
                    print(f"  首个交易日: {formatted_dates[0]}")
                    print(f"  最后交易日: {formatted_dates[-1]}")
                    
                    # 显示前几个和后几个交易日
                    if len(formatted_dates) > 10:
                        print(f"  前5个交易日: {', '.join(formatted_dates[:5])}")
                        print(f"  后5个交易日: {', '.join(formatted_dates[-5:])}")
                    else:
                        print(f"  所有交易日: {', '.join(formatted_dates)}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'exchange': 'SHSE',
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'trading_dates': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无数据返回")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'exchange': 'SHSE',
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'trading_dates': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_trading_dates_exchanges():
    """测试不同交易所的交易日历"""
    print("\n=== 测试不同交易所交易日历 ===")
    
    exchanges = ['SHSE', 'SZSE', 'CFFEX', 'SHFE', 'DCE', 'CZCE']
    start_date = '2024-01-01'
    end_date = '2024-01-31'
    
    results = []
    
    for exchange in exchanges:
        try:
            print(f"\n查询 {exchange} 交易所 2024年1月交易日历...")
            
            # 获取指定交易所的交易日历
            trading_dates = gm.get_trading_dates(
                exchange=exchange,
                start_date=start_date,
                end_date=end_date
            )
            
            if trading_dates is not None:
                formatted_dates = format_trading_dates(trading_dates)
                
                result = {
                    'exchange': exchange,
                    'start_date': start_date,
                    'end_date': end_date,
                    'trading_dates': formatted_dates,
                    'count': len(formatted_dates),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(formatted_dates)} 个交易日")
                
                if formatted_dates:
                    print(f"  首个交易日: {formatted_dates[0]}")
                    print(f"  最后交易日: {formatted_dates[-1]}")
                    print(f"  所有交易日: {', '.join(formatted_dates)}")
                
            else:
                result = {
                    'exchange': exchange,
                    'start_date': start_date,
                    'end_date': end_date,
                    'trading_dates': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无数据返回")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'exchange': exchange,
                'start_date': start_date,
                'end_date': end_date,
                'trading_dates': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_trading_dates_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '单日查询',
            'start_date': '2024-01-02',
            'end_date': '2024-01-02'
        },
        {
            'name': '周末日期',
            'start_date': '2024-01-06',  # 周六
            'end_date': '2024-01-07'    # 周日
        },
        {
            'name': '节假日期间',
            'start_date': '2024-02-10',  # 春节期间
            'end_date': '2024-02-17'
        },
        {
            'name': '跨年查询',
            'start_date': '2023-12-25',
            'end_date': '2024-01-05'
        },
        {
            'name': '未来日期',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31'
        },
        {
            'name': '很久以前',
            'start_date': '2020-01-01',
            'end_date': '2020-01-31'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']} ({test_case['start_date']} 到 {test_case['end_date']})...")
            
            # 获取交易日历
            trading_dates = gm.get_trading_dates(
                exchange='SHSE',
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if trading_dates is not None:
                formatted_dates = format_trading_dates(trading_dates)
                
                result = {
                    'test_name': test_case['name'],
                    'exchange': 'SHSE',
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'trading_dates': formatted_dates,
                    'count': len(formatted_dates),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(formatted_dates)} 个交易日")
                
                if formatted_dates:
                    print(f"  交易日: {', '.join(formatted_dates)}")
                else:
                    print(f"  该时间段内无交易日")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'exchange': 'SHSE',
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'trading_dates': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无数据返回")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'exchange': 'SHSE',
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'trading_dates': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_trading_dates_analysis():
    """测试交易日历分析"""
    print("\n=== 交易日历分析 ===")
    
    try:
        # 获取2024年全年交易日历
        print("\n获取2024年全年交易日历进行分析...")
        
        trading_dates = gm.get_trading_dates(
            exchange='SHSE',
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        if trading_dates is not None:
            formatted_dates = format_trading_dates(trading_dates)
            
            # 分析交易日历
            analysis = {
                'total_trading_days': len(formatted_dates),
                'first_trading_day': formatted_dates[0] if formatted_dates else None,
                'last_trading_day': formatted_dates[-1] if formatted_dates else None,
                'monthly_stats': {},
                'weekday_stats': {},
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'error': None
            }
            
            print(f"  2024年总交易日数: {len(formatted_dates)}")
            print(f"  首个交易日: {formatted_dates[0] if formatted_dates else 'N/A'}")
            print(f"  最后交易日: {formatted_dates[-1] if formatted_dates else 'N/A'}")
            
            # 按月统计
            monthly_counts = {}
            weekday_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}  # 0=周一, 6=周日
            weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            
            for date_str in formatted_dates:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    month = date_obj.strftime('%Y-%m')
                    weekday = date_obj.weekday()
                    
                    monthly_counts[month] = monthly_counts.get(month, 0) + 1
                    weekday_counts[weekday] += 1
                except:
                    continue
            
            analysis['monthly_stats'] = monthly_counts
            analysis['weekday_stats'] = {weekday_names[k]: v for k, v in weekday_counts.items()}
            
            print(f"\n  月度交易日统计:")
            for month, count in sorted(monthly_counts.items()):
                print(f"    {month}: {count} 天")
            
            print(f"\n  星期分布统计:")
            for weekday, count in analysis['weekday_stats'].items():
                print(f"    {weekday}: {count} 天")
            
            # 计算平均每月交易日
            if monthly_counts:
                avg_monthly = sum(monthly_counts.values()) / len(monthly_counts)
                print(f"\n  平均每月交易日: {avg_monthly:.1f} 天")
                analysis['avg_monthly_trading_days'] = avg_monthly
            
            return analysis
            
        else:
            return {
                'total_trading_days': 0,
                'first_trading_day': None,
                'last_trading_day': None,
                'monthly_stats': {},
                'weekday_stats': {},
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': 'No data returned'
            }
            
    except Exception as e:
        print(f"  分析失败: {e}")
        return {
            'total_trading_days': 0,
            'first_trading_day': None,
            'last_trading_day': None,
            'monthly_stats': {},
            'weekday_stats': {},
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': str(e)
        }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_trading_dates()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_trading_dates function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平交易日期数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'trading_dates' in data:
                    # 这是一个包含trading_dates的结果
                    base_info = {k: v for k, v in data.items() if k != 'trading_dates'}
                    trading_dates = data['trading_dates']
                    
                    if isinstance(trading_dates, list):
                        for i, date in enumerate(trading_dates):
                            flat_result = base_info.copy()
                            flat_result['date_index'] = i
                            flat_result['trading_date'] = date
                            flattened_results.append(flat_result)
                    else:
                        flat_result = base_info.copy()
                        flat_result['trading_date'] = trading_dates
                        flattened_results.append(flat_result)
                    
                    # 如果没有交易日期，也要保存基础信息
                    if not trading_dates:
                        flattened_results.append(base_info)
                else:
                    # 递归处理嵌套字典
                    for key, value in data.items():
                        if isinstance(value, (dict, list)):
                            flatten_results(value, f"{prefix}{key}_")
            elif isinstance(data, list):
                for item in data:
                    flatten_results(item, prefix)
        
        # 展平所有结果
        for result_set in results:
            flatten_results(result_set)
        
        if flattened_results:
            csv_filename = f"{filename_prefix}_results_{timestamp}.csv"
            df = pd.DataFrame(flattened_results)
            df.to_csv(csv_filename, encoding='utf-8-sig', index=False)
            print(f"结果已保存到: {csv_filename}")
            
    except Exception as e:
        print(f"保存CSV文件失败: {e}")

def main():
    """主函数"""
    print("GM API get_trading_dates() 功能测试")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    if not config:
        print("无法加载配置文件，退出测试")
        return
    
    # 初始化API
    if not init_gm_api(config):
        print("API初始化失败，退出测试")
        return
    
    try:
        all_results = []
        
        # 测试1: 基本交易日历查询
        basic_results = test_get_trading_dates_basic()
        save_results(basic_results, 'get_trading_dates_basic')
        all_results.append(basic_results)
        
        # 测试2: 不同交易所交易日历
        exchange_results = test_get_trading_dates_exchanges()
        save_results(exchange_results, 'get_trading_dates_exchanges')
        all_results.append(exchange_results)
        
        # 测试3: 边界情况测试
        edge_results = test_get_trading_dates_edge_cases()
        save_results(edge_results, 'get_trading_dates_edge_cases')
        all_results.append(edge_results)
        
        # 测试4: 交易日历分析
        analysis_result = test_get_trading_dates_analysis()
        save_results([analysis_result], 'get_trading_dates_analysis')
        all_results.append([analysis_result])
        
        # 汇总统计
        print("\n=== 测试汇总 ===")
        
        # 统计各测试结果
        def count_success_and_data(results):
            success_count = 0
            total_count = 0
            data_count = 0
            
            def count_recursive(data):
                nonlocal success_count, total_count, data_count
                
                if isinstance(data, dict):
                    if 'success' in data:
                        total_count += 1
                        if data['success']:
                            success_count += 1
                        data_count += data.get('count', data.get('total_trading_days', 0))
                    else:
                        for value in data.values():
                            if isinstance(value, (dict, list)):
                                count_recursive(value)
                elif isinstance(data, list):
                    for item in data:
                        count_recursive(item)
            
            count_recursive(results)
            return success_count, total_count, data_count
        
        basic_success, basic_total, basic_data = count_success_and_data(basic_results)
        print(f"基本查询测试: {basic_success}/{basic_total} 成功, {basic_data} 个交易日")
        
        exchange_success, exchange_total, exchange_data = count_success_and_data(exchange_results)
        print(f"交易所查询测试: {exchange_success}/{exchange_total} 成功, {exchange_data} 个交易日")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 个交易日")
        
        analysis_success, analysis_total, analysis_data = count_success_and_data([analysis_result])
        print(f"交易日历分析: {analysis_success}/{analysis_total} 成功, {analysis_data} 个交易日")
        
        # 总体统计
        total_tests = basic_total + exchange_total + edge_total + analysis_total
        total_success = basic_success + exchange_success + edge_success + analysis_success
        total_data_count = basic_data + exchange_data + edge_data + analysis_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总交易日数量: {total_data_count}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_trading_dates() API测试完成！")

if __name__ == "__main__":
    main()