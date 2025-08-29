#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_dividend() 获取分红信息
功能：测试 gm.get_dividend() API的各种用法
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

def dividend_to_dict(dividend):
    """将dividend对象转换为字典格式"""
    if dividend is None:
        return None
    
    try:
        dividend_dict = {}
        
        # 常见的dividend属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'announce_date', 'ex_date', 'record_date', 'pay_date',
            'dividend_type', 'dividend_ratio', 'cash_dividend', 'stock_dividend',
            'bonus_ratio', 'transfer_ratio', 'split_ratio',
            'dividend_yield', 'payout_ratio', 'total_dividend',
            'currency', 'tax_rate', 'created_at', 'updated_at'
        ]
        
        for attr in attributes:
            if hasattr(dividend, attr):
                value = getattr(dividend, attr)
                # 处理日期时间类型
                if attr in ['announce_date', 'ex_date', 'record_date', 'pay_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            dividend_dict[attr] = value.strftime('%Y-%m-%d')
                        else:
                            dividend_dict[attr] = str(value)
                    except:
                        dividend_dict[attr] = str(value)
                else:
                    dividend_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not dividend_dict:
            dividend_dict = {'raw_data': str(dividend)}
        
        return dividend_dict
        
    except Exception as e:
        return {'error': f'Failed to convert dividend: {e}', 'raw_data': str(dividend)}

def test_get_dividend_major_stocks():
    """测试主要股票的分红信息"""
    print("\n=== 测试主要股票分红信息 ===")
    
    major_stocks = [
        {'symbol': 'SHSE.600036', 'name': '招商银行'},
        {'symbol': 'SHSE.600519', 'name': '贵州茅台'},
        {'symbol': 'SHSE.600000', 'name': '浦发银行'},
        {'symbol': 'SZSE.000002', 'name': '万科A'},
        {'symbol': 'SZSE.000001', 'name': '平安银行'},
        {'symbol': 'SHSE.601318', 'name': '中国平安'},
        {'symbol': 'SHSE.600276', 'name': '恒瑞医药'},
        {'symbol': 'SZSE.000858', 'name': '五粮液'}
    ]
    
    results = []
    
    # 查询最近2年的分红信息
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for stock_info in major_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的分红信息...")
            
            # 获取分红信息
            dividends = gm.get_dividend(
                symbol=stock_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if dividends is not None:
                # 转换为字典列表
                dividends_list = []
                if hasattr(dividends, '__iter__') and not isinstance(dividends, str):
                    for dividend in dividends:
                        dividend_dict = dividend_to_dict(dividend)
                        if dividend_dict:
                            dividends_list.append(dividend_dict)
                else:
                    dividend_dict = dividend_to_dict(dividends)
                    if dividend_dict:
                        dividends_list.append(dividend_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'sec_name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'dividends': dividends_list,
                    'count': len(dividends_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(dividends_list)} 条分红记录")
                
                # 显示分红信息
                if dividends_list:
                    print(f"  分红记录:")
                    for i, dividend in enumerate(dividends_list):
                        ex_date = dividend.get('ex_date', 'N/A')
                        cash_dividend = dividend.get('cash_dividend', 'N/A')
                        stock_dividend = dividend.get('stock_dividend', 'N/A')
                        bonus_ratio = dividend.get('bonus_ratio', 'N/A')
                        transfer_ratio = dividend.get('transfer_ratio', 'N/A')
                        
                        print(f"    {i+1}. 除权日: {ex_date}")
                        if cash_dividend != 'N/A' and cash_dividend:
                            print(f"       现金分红: {cash_dividend}元/股")
                        if stock_dividend != 'N/A' and stock_dividend:
                            print(f"       股票股利: {stock_dividend}")
                        if bonus_ratio != 'N/A' and bonus_ratio:
                            print(f"       送股比例: {bonus_ratio}")
                        if transfer_ratio != 'N/A' and transfer_ratio:
                            print(f"       转股比例: {transfer_ratio}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'sec_name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'dividends': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无分红数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'sec_name': stock_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'dividends': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_dividend_by_year():
    """测试按年度查询分红信息"""
    print("\n=== 测试按年度查询分红信息 ===")
    
    # 选择一个经常分红的股票
    test_symbol = 'SHSE.600036'  # 招商银行
    test_name = '招商银行'
    
    # 测试不同年度
    test_years = [2024, 2023, 2022, 2021, 2020]
    
    results = []
    
    for year in test_years:
        try:
            print(f"\n查询 {test_name} {year}年的分红信息...")
            
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            # 获取分红信息
            dividends = gm.get_dividend(
                symbol=test_symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if dividends is not None:
                # 转换为字典列表
                dividends_list = []
                if hasattr(dividends, '__iter__') and not isinstance(dividends, str):
                    for dividend in dividends:
                        dividend_dict = dividend_to_dict(dividend)
                        if dividend_dict:
                            dividends_list.append(dividend_dict)
                else:
                    dividend_dict = dividend_to_dict(dividends)
                    if dividend_dict:
                        dividends_list.append(dividend_dict)
                
                result = {
                    'symbol': test_symbol,
                    'sec_name': test_name,
                    'year': year,
                    'start_date': start_date,
                    'end_date': end_date,
                    'dividends': dividends_list,
                    'count': len(dividends_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  {year}年: {len(dividends_list)} 条分红记录")
                
                # 计算年度分红统计
                if dividends_list:
                    total_cash = 0
                    total_bonus = 0
                    total_transfer = 0
                    
                    for dividend in dividends_list:
                        cash = dividend.get('cash_dividend', 0)
                        bonus = dividend.get('bonus_ratio', 0)
                        transfer = dividend.get('transfer_ratio', 0)
                        
                        if cash and isinstance(cash, (int, float)):
                            total_cash += cash
                        if bonus and isinstance(bonus, (int, float)):
                            total_bonus += bonus
                        if transfer and isinstance(transfer, (int, float)):
                            total_transfer += transfer
                    
                    print(f"    总现金分红: {total_cash:.4f}元/股")
                    if total_bonus > 0:
                        print(f"    总送股比例: {total_bonus:.4f}")
                    if total_transfer > 0:
                        print(f"    总转股比例: {total_transfer:.4f}")
                    
                    # 显示详细分红信息
                    for i, dividend in enumerate(dividends_list):
                        ex_date = dividend.get('ex_date', 'N/A')
                        announce_date = dividend.get('announce_date', 'N/A')
                        cash_dividend = dividend.get('cash_dividend', 'N/A')
                        print(f"    分红{i+1}: 公告日={announce_date}, 除权日={ex_date}, 现金={cash_dividend}")
                
            else:
                result = {
                    'symbol': test_symbol,
                    'sec_name': test_name,
                    'year': year,
                    'start_date': start_date,
                    'end_date': end_date,
                    'dividends': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  {year}年: 无分红数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  {year}年查询失败: {e}")
            results.append({
                'symbol': test_symbol,
                'sec_name': test_name,
                'year': year,
                'start_date': f"{year}-01-01",
                'end_date': f"{year}-12-31",
                'dividends': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_dividend_high_yield_stocks():
    """测试高股息股票的分红信息"""
    print("\n=== 测试高股息股票分红信息 ===")
    
    # 一些知名的高股息股票
    high_yield_stocks = [
        {'symbol': 'SHSE.601857', 'name': '中国石油'},
        {'symbol': 'SHSE.601398', 'name': '工商银行'},
        {'symbol': 'SHSE.601939', 'name': '建设银行'},
        {'symbol': 'SHSE.600028', 'name': '中国石化'},
        {'symbol': 'SHSE.601988', 'name': '中国银行'},
        {'symbol': 'SHSE.600900', 'name': '长江电力'},
        {'symbol': 'SHSE.601088', 'name': '中国神华'},
        {'symbol': 'SHSE.600585', 'name': '海螺水泥'}
    ]
    
    results = []
    
    # 查询最近1年的分红信息
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for stock_info in high_yield_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的分红信息...")
            
            # 获取分红信息
            dividends = gm.get_dividend(
                symbol=stock_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if dividends is not None:
                # 转换为字典列表
                dividends_list = []
                if hasattr(dividends, '__iter__') and not isinstance(dividends, str):
                    for dividend in dividends:
                        dividend_dict = dividend_to_dict(dividend)
                        if dividend_dict:
                            dividends_list.append(dividend_dict)
                else:
                    dividend_dict = dividend_to_dict(dividends)
                    if dividend_dict:
                        dividends_list.append(dividend_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'sec_name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'dividends': dividends_list,
                    'count': len(dividends_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(dividends_list)} 条分红记录")
                
                # 计算分红统计
                if dividends_list:
                    total_cash_dividend = 0
                    dividend_dates = []
                    
                    for dividend in dividends_list:
                        cash = dividend.get('cash_dividend', 0)
                        ex_date = dividend.get('ex_date', '')
                        
                        if cash and isinstance(cash, (int, float)):
                            total_cash_dividend += cash
                        if ex_date:
                            dividend_dates.append(ex_date)
                    
                    print(f"    年度总现金分红: {total_cash_dividend:.4f}元/股")
                    if dividend_dates:
                        print(f"    分红日期: {', '.join(dividend_dates)}")
                    
                    # 显示最新的分红信息
                    latest_dividend = dividends_list[0] if dividends_list else None
                    if latest_dividend:
                        print(f"    最新分红:")
                        for key, value in latest_dividend.items():
                            if value and key not in ['raw_data', 'error']:
                                print(f"      {key}: {value}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'sec_name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'dividends': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无分红数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'sec_name': stock_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'dividends': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_dividend_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的股票',
            'symbol': 'INVALID.000000',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '未来日期范围',
            'symbol': 'SHSE.600036',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'symbol': 'SHSE.600036',
            'start_date': '1990-01-01',
            'end_date': '1990-12-31'
        },
        {
            'name': '单日查询',
            'symbol': 'SHSE.600036',
            'start_date': '2023-06-15',
            'end_date': '2023-06-15'
        },
        {
            'name': '跨年查询',
            'symbol': 'SHSE.600036',
            'start_date': '2022-12-01',
            'end_date': '2023-02-28'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']} ({test_case['symbol']})...")
            
            # 获取分红信息
            dividends = gm.get_dividend(
                symbol=test_case['symbol'],
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if dividends is not None:
                # 转换为字典列表
                dividends_list = []
                if hasattr(dividends, '__iter__') and not isinstance(dividends, str):
                    for dividend in dividends:
                        dividend_dict = dividend_to_dict(dividend)
                        if dividend_dict:
                            dividends_list.append(dividend_dict)
                else:
                    dividend_dict = dividend_to_dict(dividends)
                    if dividend_dict:
                        dividends_list.append(dividend_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'dividends': dividends_list,
                    'count': len(dividends_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(dividends_list)} 条分红记录")
                
                if dividends_list:
                    print(f"  分红信息:")
                    for i, dividend in enumerate(dividends_list[:3]):
                        ex_date = dividend.get('ex_date', 'N/A')
                        cash_dividend = dividend.get('cash_dividend', 'N/A')
                        print(f"    {i+1}. 除权日: {ex_date}, 现金分红: {cash_dividend}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'dividends': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无分红数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'symbol': test_case['symbol'],
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'dividends': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_dividend_data(results):
    """分析分红数据结构"""
    print("\n=== 分红数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_dividends = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_dividends
        
        if isinstance(data, dict):
            if 'dividends' in data:
                dividends = data['dividends']
                if isinstance(dividends, list):
                    total_dividends += len(dividends)
                    for dividend in dividends:
                        if isinstance(dividend, dict):
                            for field in dividend.keys():
                                all_fields.add(field)
                                field_counts[field] = field_counts.get(field, 0) + 1
            else:
                # 递归处理嵌套字典
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        collect_fields_from_results(value)
        elif isinstance(data, list):
            for item in data:
                collect_fields_from_results(item)
    
    # 分析所有结果
    for result_set in results:
        collect_fields_from_results(result_set)
    
    if all_fields:
        print(f"发现的分红字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的分红字段")
    
    print(f"\n总分红记录数量: {total_dividends}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_dividends': total_dividends
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_dividend()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_dividend function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平分红数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'dividends' in data:
                    # 这是一个包含dividends的结果
                    base_info = {k: v for k, v in data.items() if k != 'dividends'}
                    dividends = data['dividends']
                    
                    if isinstance(dividends, list):
                        for i, dividend in enumerate(dividends):
                            flat_result = base_info.copy()
                            flat_result['dividend_index'] = i
                            if isinstance(dividend, dict):
                                for key, value in dividend.items():
                                    flat_result[f'dividend_{key}'] = value
                            flattened_results.append(flat_result)
                    elif dividends:
                        flat_result = base_info.copy()
                        if isinstance(dividends, dict):
                            for key, value in dividends.items():
                                flat_result[f'dividend_{key}'] = value
                        flattened_results.append(flat_result)
                    else:
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
    print("GM API get_dividend() 功能测试")
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
        
        # 测试1: 主要股票分红信息
        major_results = test_get_dividend_major_stocks()
        save_results(major_results, 'get_dividend_major')
        all_results.append(major_results)
        
        # 测试2: 按年度查询分红信息
        yearly_results = test_get_dividend_by_year()
        save_results(yearly_results, 'get_dividend_yearly')
        all_results.append(yearly_results)
        
        # 测试3: 高股息股票分红信息
        high_yield_results = test_get_dividend_high_yield_stocks()
        save_results(high_yield_results, 'get_dividend_high_yield')
        all_results.append(high_yield_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_dividend_edge_cases()
        save_results(edge_results, 'get_dividend_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_dividend_data(all_results)
        
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
                        data_count += data.get('count', 0)
                    else:
                        for value in data.values():
                            if isinstance(value, (dict, list)):
                                count_recursive(value)
                elif isinstance(data, list):
                    for item in data:
                        count_recursive(item)
            
            count_recursive(results)
            return success_count, total_count, data_count
        
        major_success, major_total, major_data = count_success_and_data(major_results)
        print(f"主要股票测试: {major_success}/{major_total} 成功, {major_data} 条分红记录")
        
        yearly_success, yearly_total, yearly_data = count_success_and_data(yearly_results)
        print(f"年度查询测试: {yearly_success}/{yearly_total} 成功, {yearly_data} 条分红记录")
        
        high_yield_success, high_yield_total, high_yield_data = count_success_and_data(high_yield_results)
        print(f"高股息测试: {high_yield_success}/{high_yield_total} 成功, {high_yield_data} 条分红记录")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 条分红记录")
        
        # 总体统计
        total_tests = major_total + yearly_total + high_yield_total + edge_total
        total_success = major_success + yearly_success + high_yield_success + edge_success
        total_data_count = major_data + yearly_data + high_yield_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总分红记录数量: {total_data_count}")
        
        # 数据结构统计
        print(f"\n分红数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_dividend() API测试完成！")

if __name__ == "__main__":
    main()