#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_contract_expire_rest_days() 获取合约到期剩余天数
功能：测试 gm.get_contract_expire_rest_days() API的各种用法
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

def test_get_contract_expire_rest_days_futures():
    """测试期货合约到期剩余天数"""
    print("\n=== 测试期货合约到期剩余天数 ===")
    
    # 常见期货合约（需要根据实际情况调整）
    futures_contracts = [
        {'symbol': 'CFFEX.IF2412', 'name': '沪深300股指期货2024年12月'},
        {'symbol': 'CFFEX.IC2412', 'name': '中证500股指期货2024年12月'},
        {'symbol': 'CFFEX.IH2412', 'name': '上证50股指期货2024年12月'},
        {'symbol': 'SHFE.cu2412', 'name': '沪铜2024年12月'},
        {'symbol': 'SHFE.au2412', 'name': '沪金2024年12月'},
        {'symbol': 'DCE.i2405', 'name': '铁矿石2024年5月'},
        {'symbol': 'CZCE.MA405', 'name': '甲醇2024年5月'},
        {'symbol': 'CZCE.TA405', 'name': 'PTA2024年5月'}
    ]
    
    results = []
    
    for contract_info in futures_contracts:
        try:
            print(f"\n查询 {contract_info['name']} ({contract_info['symbol']}) 的到期剩余天数...")
            
            # 获取合约到期剩余天数
            rest_days = gm.get_contract_expire_rest_days(contract_info['symbol'])
            
            result = {
                'symbol': contract_info['symbol'],
                'contract_name': contract_info['name'],
                'rest_days': rest_days,
                'query_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'success': rest_days is not None,
                'error': None if rest_days is not None else 'No data returned'
            }
            
            if rest_days is not None:
                print(f"  剩余天数: {rest_days} 天")
                
                # 计算到期日期（估算）
                if isinstance(rest_days, (int, float)) and rest_days >= 0:
                    expire_date = datetime.now() + timedelta(days=int(rest_days))
                    result['estimated_expire_date'] = expire_date.strftime('%Y-%m-%d')
                    print(f"  预计到期日: {expire_date.strftime('%Y-%m-%d')}")
                    
                    # 分析到期状态
                    if rest_days <= 0:
                        status = "已到期"
                    elif rest_days <= 7:
                        status = "即将到期（一周内）"
                    elif rest_days <= 30:
                        status = "临近到期（一月内）"
                    else:
                        status = "正常"
                    
                    result['expire_status'] = status
                    print(f"  到期状态: {status}")
                
            else:
                print(f"  无法获取到期天数")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': contract_info['symbol'],
                'contract_name': contract_info['name'],
                'rest_days': None,
                'query_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_contract_expire_rest_days_options():
    """测试期权合约到期剩余天数"""
    print("\n=== 测试期权合约到期剩余天数 ===")
    
    # 常见期权合约（需要根据实际情况调整）
    options_contracts = [
        {'symbol': 'SHSE.10004820', 'name': '50ETF期权'},
        {'symbol': 'SHSE.10004821', 'name': '50ETF期权'},
        {'symbol': 'SZSE.90000001', 'name': '300ETF期权'},
        {'symbol': 'SZSE.90000002', 'name': '300ETF期权'},
        {'symbol': 'CFFEX.IO2412-C-4000', 'name': '沪深300股指期权'},
        {'symbol': 'CFFEX.IO2412-P-4000', 'name': '沪深300股指期权'},
        {'symbol': 'CFFEX.HO2412-C-2800', 'name': '上证50股指期权'},
        {'symbol': 'CFFEX.MO2412-C-7000', 'name': '中证1000股指期权'}
    ]
    
    results = []
    
    for contract_info in options_contracts:
        try:
            print(f"\n查询 {contract_info['name']} ({contract_info['symbol']}) 的到期剩余天数...")
            
            # 获取合约到期剩余天数
            rest_days = gm.get_contract_expire_rest_days(contract_info['symbol'])
            
            result = {
                'symbol': contract_info['symbol'],
                'contract_name': contract_info['name'],
                'rest_days': rest_days,
                'query_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'success': rest_days is not None,
                'error': None if rest_days is not None else 'No data returned'
            }
            
            if rest_days is not None:
                print(f"  剩余天数: {rest_days} 天")
                
                # 计算到期日期（估算）
                if isinstance(rest_days, (int, float)) and rest_days >= 0:
                    expire_date = datetime.now() + timedelta(days=int(rest_days))
                    result['estimated_expire_date'] = expire_date.strftime('%Y-%m-%d')
                    print(f"  预计到期日: {expire_date.strftime('%Y-%m-%d')}")
                    
                    # 期权特殊的到期状态分析
                    if rest_days <= 0:
                        status = "已到期"
                        risk_level = "极高"
                    elif rest_days <= 3:
                        status = "即将到期（3天内）"
                        risk_level = "极高"
                    elif rest_days <= 7:
                        status = "临近到期（一周内）"
                        risk_level = "高"
                    elif rest_days <= 30:
                        status = "接近到期（一月内）"
                        risk_level = "中等"
                    else:
                        status = "正常"
                        risk_level = "低"
                    
                    result['expire_status'] = status
                    result['risk_level'] = risk_level
                    print(f"  到期状态: {status}")
                    print(f"  风险等级: {risk_level}")
                
            else:
                print(f"  无法获取到期天数")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': contract_info['symbol'],
                'contract_name': contract_info['name'],
                'rest_days': None,
                'query_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_contract_expire_rest_days_batch():
    """测试批量查询合约到期剩余天数"""
    print("\n=== 测试批量查询合约到期剩余天数 ===")
    
    # 混合不同类型的合约
    mixed_contracts = [
        {'symbol': 'CFFEX.IF2412', 'type': '股指期货', 'name': '沪深300股指期货'},
        {'symbol': 'CFFEX.IC2412', 'type': '股指期货', 'name': '中证500股指期货'},
        {'symbol': 'SHFE.cu2412', 'type': '商品期货', 'name': '沪铜期货'},
        {'symbol': 'SHFE.au2412', 'type': '商品期货', 'name': '沪金期货'},
        {'symbol': 'DCE.i2405', 'type': '商品期货', 'name': '铁矿石期货'},
        {'symbol': 'CZCE.MA405', 'type': '商品期货', 'name': '甲醇期货'},
        {'symbol': 'SHSE.10004820', 'type': 'ETF期权', 'name': '50ETF期权'},
        {'symbol': 'CFFEX.IO2412-C-4000', 'type': '股指期权', 'name': '沪深300股指期权'}
    ]
    
    results = []
    contract_types = {}
    
    for contract_info in mixed_contracts:
        try:
            print(f"\n查询 {contract_info['name']} ({contract_info['symbol']})...")
            
            # 获取合约到期剩余天数
            rest_days = gm.get_contract_expire_rest_days(contract_info['symbol'])
            
            result = {
                'symbol': contract_info['symbol'],
                'contract_name': contract_info['name'],
                'contract_type': contract_info['type'],
                'rest_days': rest_days,
                'query_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'success': rest_days is not None,
                'error': None if rest_days is not None else 'No data returned'
            }
            
            if rest_days is not None:
                print(f"  类型: {contract_info['type']}")
                print(f"  剩余天数: {rest_days} 天")
                
                # 按类型统计
                contract_type = contract_info['type']
                if contract_type not in contract_types:
                    contract_types[contract_type] = {'count': 0, 'total_days': 0, 'contracts': []}
                
                contract_types[contract_type]['count'] += 1
                if isinstance(rest_days, (int, float)):
                    contract_types[contract_type]['total_days'] += rest_days
                contract_types[contract_type]['contracts'].append({
                    'symbol': contract_info['symbol'],
                    'name': contract_info['name'],
                    'rest_days': rest_days
                })
                
                # 计算到期日期
                if isinstance(rest_days, (int, float)) and rest_days >= 0:
                    expire_date = datetime.now() + timedelta(days=int(rest_days))
                    result['estimated_expire_date'] = expire_date.strftime('%Y-%m-%d')
                    print(f"  预计到期日: {expire_date.strftime('%Y-%m-%d')}")
                
            else:
                print(f"  无法获取到期天数")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': contract_info['symbol'],
                'contract_name': contract_info['name'],
                'contract_type': contract_info['type'],
                'rest_days': None,
                'query_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    # 按类型统计分析
    print("\n=== 按合约类型统计 ===")
    for contract_type, stats in contract_types.items():
        avg_days = stats['total_days'] / stats['count'] if stats['count'] > 0 else 0
        print(f"\n{contract_type}:")
        print(f"  合约数量: {stats['count']}")
        print(f"  平均剩余天数: {avg_days:.1f} 天")
        
        # 显示该类型的合约详情
        for contract in stats['contracts']:
            print(f"    {contract['symbol']} - {contract['name']}: {contract['rest_days']} 天")
    
    return results, contract_types

def test_get_contract_expire_rest_days_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的合约',
            'symbol': 'INVALID.000000'
        },
        {
            'name': '格式错误的合约代码',
            'symbol': 'WRONGFORMAT'
        },
        {
            'name': '空字符串',
            'symbol': ''
        },
        {
            'name': '已过期的合约（可能）',
            'symbol': 'CFFEX.IF2301'  # 2023年1月的合约
        },
        {
            'name': '股票代码（非合约）',
            'symbol': 'SHSE.600036'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']} ({test_case['symbol']})...")
            
            # 获取合约到期剩余天数
            rest_days = gm.get_contract_expire_rest_days(test_case['symbol'])
            
            result = {
                'test_name': test_case['name'],
                'symbol': test_case['symbol'],
                'rest_days': rest_days,
                'query_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'success': rest_days is not None,
                'error': None if rest_days is not None else 'No data returned'
            }
            
            if rest_days is not None:
                print(f"  剩余天数: {rest_days} 天")
                
                # 分析异常情况
                if isinstance(rest_days, (int, float)):
                    if rest_days < 0:
                        print(f"  注意: 剩余天数为负数，可能已过期")
                    elif rest_days > 1000:
                        print(f"  注意: 剩余天数过大，可能数据异常")
                
            else:
                print(f"  无法获取到期天数（预期结果）")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'symbol': test_case['symbol'],
                'rest_days': None,
                'query_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_expire_data(results):
    """分析到期数据"""
    print("\n=== 到期数据分析 ===")
    
    valid_results = []
    
    # 收集有效数据
    def collect_valid_data(data):
        if isinstance(data, dict):
            if 'rest_days' in data and data.get('success') and data['rest_days'] is not None:
                valid_results.append(data)
            else:
                # 递归处理嵌套数据
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        collect_valid_data(value)
        elif isinstance(data, list):
            for item in data:
                collect_valid_data(item)
    
    # 分析所有结果
    for result_set in results:
        collect_valid_data(result_set)
    
    if valid_results:
        rest_days_list = []
        for result in valid_results:
            rest_days = result['rest_days']
            if isinstance(rest_days, (int, float)):
                rest_days_list.append(rest_days)
        
        if rest_days_list:
            print(f"有效数据数量: {len(rest_days_list)}")
            print(f"最小剩余天数: {min(rest_days_list)} 天")
            print(f"最大剩余天数: {max(rest_days_list)} 天")
            print(f"平均剩余天数: {sum(rest_days_list)/len(rest_days_list):.1f} 天")
            
            # 按到期时间分类
            expired = [d for d in rest_days_list if d <= 0]
            within_week = [d for d in rest_days_list if 0 < d <= 7]
            within_month = [d for d in rest_days_list if 7 < d <= 30]
            normal = [d for d in rest_days_list if d > 30]
            
            print(f"\n到期状态分布:")
            print(f"  已到期: {len(expired)} 个")
            print(f"  一周内到期: {len(within_week)} 个")
            print(f"  一月内到期: {len(within_month)} 个")
            print(f"  正常: {len(normal)} 个")
        
    else:
        print("未发现有效的到期数据")
    
    return {
        'total_valid': len(valid_results),
        'rest_days_data': rest_days_list if 'rest_days_list' in locals() else [],
        'valid_results': valid_results
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_contract_expire_rest_days()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_contract_expire_rest_days function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'rest_days' in data:
                    # 这是一个包含rest_days的结果
                    flattened_results.append(data)
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
    print("GM API get_contract_expire_rest_days() 功能测试")
    print("=" * 60)
    
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
        
        # 测试1: 期货合约到期剩余天数
        futures_results = test_get_contract_expire_rest_days_futures()
        save_results(futures_results, 'get_contract_expire_futures')
        all_results.append(futures_results)
        
        # 测试2: 期权合约到期剩余天数
        options_results = test_get_contract_expire_rest_days_options()
        save_results(options_results, 'get_contract_expire_options')
        all_results.append(options_results)
        
        # 测试3: 批量查询合约到期剩余天数
        batch_results, contract_types = test_get_contract_expire_rest_days_batch()
        save_results(batch_results, 'get_contract_expire_batch')
        all_results.append(batch_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_contract_expire_rest_days_edge_cases()
        save_results(edge_results, 'get_contract_expire_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据
        data_analysis = analyze_expire_data(all_results)
        
        # 汇总统计
        print("\n=== 测试汇总 ===")
        
        # 统计各测试结果
        def count_success_and_data(results):
            success_count = 0
            total_count = 0
            
            def count_recursive(data):
                nonlocal success_count, total_count
                
                if isinstance(data, dict):
                    if 'success' in data:
                        total_count += 1
                        if data['success']:
                            success_count += 1
                    else:
                        for value in data.values():
                            if isinstance(value, (dict, list)):
                                count_recursive(value)
                elif isinstance(data, list):
                    for item in data:
                        count_recursive(item)
            
            count_recursive(results)
            return success_count, total_count
        
        futures_success, futures_total = count_success_and_data(futures_results)
        print(f"期货合约测试: {futures_success}/{futures_total} 成功")
        
        options_success, options_total = count_success_and_data(options_results)
        print(f"期权合约测试: {options_success}/{options_total} 成功")
        
        batch_success, batch_total = count_success_and_data(batch_results)
        print(f"批量查询测试: {batch_success}/{batch_total} 成功")
        
        edge_success, edge_total = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功")
        
        # 总体统计
        total_tests = futures_total + options_total + batch_total + edge_total
        total_success = futures_success + options_success + batch_success + edge_success
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"有效数据数量: {data_analysis['total_valid']}")
        
        # 数据分析结果
        if data_analysis['rest_days_data']:
            rest_days_data = data_analysis['rest_days_data']
            print(f"\n到期数据统计:")
            print(f"  数据范围: {min(rest_days_data)} ~ {max(rest_days_data)} 天")
            print(f"  平均剩余天数: {sum(rest_days_data)/len(rest_days_data):.1f} 天")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_contract_expire_rest_days() API测试完成！")

if __name__ == "__main__":
    main()