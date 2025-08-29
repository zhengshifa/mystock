#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_history_constituents() 获取历史成分股信息
功能：测试 gm.get_history_constituents() API的各种用法
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

def constituent_to_dict(constituent):
    """将constituent对象转换为字典格式"""
    if constituent is None:
        return None
    
    try:
        constituent_dict = {}
        
        # 常见的constituent属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'index_symbol', 'index_name', 'weight', 'in_date', 'out_date',
            'is_active', 'change_type', 'change_date', 'change_reason',
            'market_cap', 'free_float_cap', 'industry', 'sector',
            'created_at', 'updated_at'
        ]
        
        for attr in attributes:
            if hasattr(constituent, attr):
                value = getattr(constituent, attr)
                # 处理日期时间类型
                if attr in ['in_date', 'out_date', 'change_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            constituent_dict[attr] = value.strftime('%Y-%m-%d')
                        else:
                            constituent_dict[attr] = str(value)
                    except:
                        constituent_dict[attr] = str(value)
                else:
                    constituent_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not constituent_dict:
            constituent_dict = {'raw_data': str(constituent)}
        
        return constituent_dict
        
    except Exception as e:
        return {'error': f'Failed to convert constituent: {e}', 'raw_data': str(constituent)}

def test_get_history_constituents_major_indices():
    """测试主要指数的历史成分股查询"""
    print("\n=== 测试主要指数的历史成分股查询 ===")
    
    # 测试主要指数
    major_indices = [
        {'symbol': 'SHSE.000001', 'name': '上证指数'},
        {'symbol': 'SZSE.399001', 'name': '深证成指'},
        {'symbol': 'SZSE.399006', 'name': '创业板指'},
        {'symbol': 'SHSE.000016', 'name': '上证50'},
        {'symbol': 'SHSE.000300', 'name': '沪深300'},
        {'symbol': 'SHSE.000905', 'name': '中证500'}
    ]
    
    results = []
    
    # 查询最近6个月的历史成分股
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for index_info in major_indices:
        try:
            print(f"\n查询 {index_info['name']} ({index_info['symbol']}) 的历史成分股...")
            
            # 获取历史成分股信息
            constituents = gm.get_history_constituents(
                index=index_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if constituents is not None:
                # 转换为字典列表
                constituents_list = []
                if hasattr(constituents, '__iter__') and not isinstance(constituents, str):
                    for constituent in constituents:
                        constituent_dict = constituent_to_dict(constituent)
                        if constituent_dict:
                            constituents_list.append(constituent_dict)
                else:
                    constituent_dict = constituent_to_dict(constituents)
                    if constituent_dict:
                        constituents_list.append(constituent_dict)
                
                result = {
                    'index_symbol': index_info['symbol'],
                    'index_name': index_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'constituents': constituents_list,
                    'count': len(constituents_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(constituents_list)} 条历史成分股记录")
                
                # 分析成分股变化
                if constituents_list:
                    # 统计变化类型
                    change_types = {}
                    for constituent in constituents_list:
                        change_type = constituent.get('change_type', 'Unknown')
                        change_types[change_type] = change_types.get(change_type, 0) + 1
                    
                    print(f"  变化类型分布:")
                    for change_type, count in change_types.items():
                        print(f"    {change_type}: {count} 次")
                    
                    # 统计新增和剔除
                    added_stocks = [c for c in constituents_list if c.get('change_type') == 'ADD' or c.get('in_date')]
                    removed_stocks = [c for c in constituents_list if c.get('change_type') == 'REMOVE' or c.get('out_date')]
                    
                    print(f"  新增成分股: {len(added_stocks)} 个")
                    print(f"  剔除成分股: {len(removed_stocks)} 个")
                    
                    # 显示最近的变化
                    recent_changes = sorted(
                        [c for c in constituents_list if c.get('change_date')],
                        key=lambda x: x.get('change_date', ''),
                        reverse=True
                    )
                    
                    if recent_changes:
                        print(f"  最近的成分股变化:")
                        for i, change in enumerate(recent_changes[:5]):
                            symbol = change.get('symbol', 'N/A')
                            sec_name = change.get('sec_name', 'N/A')
                            change_type = change.get('change_type', 'N/A')
                            change_date = change.get('change_date', 'N/A')
                            print(f"    {i+1}. {symbol} - {sec_name} ({change_type}) - {change_date}")
                
            else:
                result = {
                    'index_symbol': index_info['symbol'],
                    'index_name': index_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'constituents': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史成分股数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'index_symbol': index_info['symbol'],
                'index_name': index_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'constituents': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_constituents_date_ranges():
    """测试不同日期范围的历史成分股查询"""
    print("\n=== 测试不同日期范围的历史成分股查询 ===")
    
    # 测试不同的日期范围
    date_ranges = [
        {
            'name': '最近1个月',
            'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '最近3个月',
            'start_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '2024年第一季度',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31'
        },
        {
            'name': '2023年全年',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '2022年下半年',
            'start_date': '2022-07-01',
            'end_date': '2022-12-31'
        }
    ]
    
    results = []
    
    # 选择沪深300作为测试对象
    test_index = 'SHSE.000300'
    test_index_name = '沪深300'
    
    for date_range in date_ranges:
        try:
            print(f"\n查询 {test_index_name} 在 {date_range['name']} ({date_range['start_date']} 到 {date_range['end_date']}) 的历史成分股...")
            
            # 获取历史成分股信息
            constituents = gm.get_history_constituents(
                index=test_index,
                start_date=date_range['start_date'],
                end_date=date_range['end_date']
            )
            
            if constituents is not None:
                # 转换为字典列表
                constituents_list = []
                if hasattr(constituents, '__iter__') and not isinstance(constituents, str):
                    for constituent in constituents:
                        constituent_dict = constituent_to_dict(constituent)
                        if constituent_dict:
                            constituents_list.append(constituent_dict)
                else:
                    constituent_dict = constituent_to_dict(constituents)
                    if constituent_dict:
                        constituents_list.append(constituent_dict)
                
                result = {
                    'date_range_name': date_range['name'],
                    'index_symbol': test_index,
                    'index_name': test_index_name,
                    'start_date': date_range['start_date'],
                    'end_date': date_range['end_date'],
                    'constituents': constituents_list,
                    'count': len(constituents_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(constituents_list)} 条历史成分股记录")
                
                # 分析时间分布
                if constituents_list:
                    # 统计各月份的变化数量
                    monthly_changes = {}
                    for constituent in constituents_list:
                        change_date = constituent.get('change_date')
                        if change_date and change_date != 'N/A':
                            try:
                                month = change_date[:7]  # YYYY-MM
                                monthly_changes[month] = monthly_changes.get(month, 0) + 1
                            except:
                                pass
                    
                    if monthly_changes:
                        print(f"  月度变化分布:")
                        for month in sorted(monthly_changes.keys()):
                            count = monthly_changes[month]
                            print(f"    {month}: {count} 次变化")
                    
                    # 分析行业分布（如果有行业信息）
                    industries = {}
                    for constituent in constituents_list:
                        industry = constituent.get('industry', 'Unknown')
                        if industry and industry != 'N/A':
                            industries[industry] = industries.get(industry, 0) + 1
                    
                    if industries:
                        print(f"  涉及行业分布:")
                        sorted_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)
                        for industry, count in sorted_industries[:5]:
                            print(f"    {industry}: {count} 次变化")
                    
                    # 显示权重变化（如果有权重信息）
                    weighted_changes = [c for c in constituents_list if c.get('weight') is not None]
                    if weighted_changes:
                        avg_weight = sum(float(c.get('weight', 0)) for c in weighted_changes) / len(weighted_changes)
                        print(f"  平均权重: {avg_weight:.4f}")
                        
                        # 显示权重最大的变化
                        sorted_by_weight = sorted(weighted_changes, key=lambda x: float(x.get('weight', 0)), reverse=True)
                        print(f"  权重最大的变化:")
                        for i, change in enumerate(sorted_by_weight[:3]):
                            symbol = change.get('symbol', 'N/A')
                            sec_name = change.get('sec_name', 'N/A')
                            weight = change.get('weight', 'N/A')
                            change_type = change.get('change_type', 'N/A')
                            print(f"    {i+1}. {symbol} - {sec_name} (权重: {weight}, 类型: {change_type})")
                
            else:
                result = {
                    'date_range_name': date_range['name'],
                    'index_symbol': test_index,
                    'index_name': test_index_name,
                    'start_date': date_range['start_date'],
                    'end_date': date_range['end_date'],
                    'constituents': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史成分股数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'date_range_name': date_range['name'],
                'index_symbol': test_index,
                'index_name': test_index_name,
                'start_date': date_range['start_date'],
                'end_date': date_range['end_date'],
                'constituents': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_constituents_sector_indices():
    """测试行业指数的历史成分股查询"""
    print("\n=== 测试行业指数的历史成分股查询 ===")
    
    # 测试行业指数
    sector_indices = [
        {'symbol': 'SHSE.000037', 'name': '上证医药'},
        {'symbol': 'SHSE.000036', 'name': '上证消费'},
        {'symbol': 'SHSE.000035', 'name': '上证资源'},
        {'symbol': 'SHSE.000034', 'name': '上证金融'},
        {'symbol': 'SHSE.000033', 'name': '上证地产'},
        {'symbol': 'SHSE.000032', 'name': '上证能源'}
    ]
    
    results = []
    
    # 查询最近3个月的历史成分股
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for index_info in sector_indices:
        try:
            print(f"\n查询 {index_info['name']} ({index_info['symbol']}) 的历史成分股...")
            
            # 获取历史成分股信息
            constituents = gm.get_history_constituents(
                index=index_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if constituents is not None:
                # 转换为字典列表
                constituents_list = []
                if hasattr(constituents, '__iter__') and not isinstance(constituents, str):
                    for constituent in constituents:
                        constituent_dict = constituent_to_dict(constituent)
                        if constituent_dict:
                            constituents_list.append(constituent_dict)
                else:
                    constituent_dict = constituent_to_dict(constituents)
                    if constituent_dict:
                        constituents_list.append(constituent_dict)
                
                result = {
                    'index_symbol': index_info['symbol'],
                    'index_name': index_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'constituents': constituents_list,
                    'count': len(constituents_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(constituents_list)} 条历史成分股记录")
                
                # 分析成分股特征
                if constituents_list:
                    # 统计交易所分布
                    exchanges = {}
                    for constituent in constituents_list:
                        exchange = constituent.get('exchange', 'Unknown')
                        exchanges[exchange] = exchanges.get(exchange, 0) + 1
                    
                    print(f"  交易所分布:")
                    for exchange, count in exchanges.items():
                        print(f"    {exchange}: {count} 个")
                    
                    # 统计市值分布（如果有市值信息）
                    market_caps = [c for c in constituents_list if c.get('market_cap') is not None]
                    if market_caps:
                        total_market_cap = sum(float(c.get('market_cap', 0)) for c in market_caps)
                        avg_market_cap = total_market_cap / len(market_caps)
                        print(f"  平均市值: {avg_market_cap:.2f}")
                        
                        # 显示市值最大的成分股
                        sorted_by_cap = sorted(market_caps, key=lambda x: float(x.get('market_cap', 0)), reverse=True)
                        print(f"  市值最大的成分股:")
                        for i, constituent in enumerate(sorted_by_cap[:3]):
                            symbol = constituent.get('symbol', 'N/A')
                            sec_name = constituent.get('sec_name', 'N/A')
                            market_cap = constituent.get('market_cap', 'N/A')
                            print(f"    {i+1}. {symbol} - {sec_name} (市值: {market_cap})")
                    
                    # 显示最近的变化
                    recent_changes = [c for c in constituents_list if c.get('change_date')]
                    if recent_changes:
                        sorted_changes = sorted(recent_changes, key=lambda x: x.get('change_date', ''), reverse=True)
                        print(f"  最近的变化:")
                        for i, change in enumerate(sorted_changes[:3]):
                            symbol = change.get('symbol', 'N/A')
                            sec_name = change.get('sec_name', 'N/A')
                            change_type = change.get('change_type', 'N/A')
                            change_date = change.get('change_date', 'N/A')
                            print(f"    {i+1}. {symbol} - {sec_name} ({change_type}) - {change_date}")
                
            else:
                result = {
                    'index_symbol': index_info['symbol'],
                    'index_name': index_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'constituents': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史成分股数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'index_symbol': index_info['symbol'],
                'index_name': index_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'constituents': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_constituents_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的指数',
            'index': 'INVALID.123456',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '未来日期范围',
            'index': 'SHSE.000300',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'index': 'SHSE.000300',
            'start_date': '1990-01-01',
            'end_date': '1990-12-31'
        },
        {
            'name': '单日查询',
            'index': 'SHSE.000300',
            'start_date': '2023-06-15',
            'end_date': '2023-06-15'
        },
        {
            'name': '日期顺序颠倒',
            'index': 'SHSE.000300',
            'start_date': '2023-12-31',
            'end_date': '2023-01-01'
        },
        {
            'name': '非交易日查询',
            'index': 'SHSE.000300',
            'start_date': '2023-01-01',  # 元旦
            'end_date': '2023-01-01'
        },
        {
            'name': '周末查询',
            'index': 'SHSE.000300',
            'start_date': '2023-07-01',  # 周六
            'end_date': '2023-07-02'   # 周日
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']}...")
            print(f"  指数: {test_case['index']}")
            print(f"  日期范围: {test_case['start_date']} 到 {test_case['end_date']}")
            
            # 获取历史成分股信息
            constituents = gm.get_history_constituents(
                index=test_case['index'],
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if constituents is not None:
                # 转换为字典列表
                constituents_list = []
                if hasattr(constituents, '__iter__') and not isinstance(constituents, str):
                    for constituent in constituents:
                        constituent_dict = constituent_to_dict(constituent)
                        if constituent_dict:
                            constituents_list.append(constituent_dict)
                else:
                    constituent_dict = constituent_to_dict(constituents)
                    if constituent_dict:
                        constituents_list.append(constituent_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'index': test_case['index'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'constituents': constituents_list,
                    'count': len(constituents_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(constituents_list)} 条历史成分股记录")
                
                if constituents_list:
                    print(f"  前几条记录:")
                    for i, constituent in enumerate(constituents_list[:3]):
                        symbol = constituent.get('symbol', 'N/A')
                        sec_name = constituent.get('sec_name', 'N/A')
                        change_type = constituent.get('change_type', 'N/A')
                        change_date = constituent.get('change_date', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} ({change_type}) - {change_date}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'index': test_case['index'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'constituents': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史成分股数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'index': test_case['index'],
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'constituents': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_history_constituents_data(results):
    """分析历史成分股数据结构"""
    print("\n=== 历史成分股数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_constituents = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_constituents
        
        if isinstance(data, dict):
            if 'constituents' in data:
                constituents = data['constituents']
                if isinstance(constituents, list):
                    total_constituents += len(constituents)
                    for constituent in constituents:
                        if isinstance(constituent, dict):
                            for field in constituent.keys():
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
        print(f"发现的历史成分股字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的历史成分股字段")
    
    print(f"\n总历史成分股记录数: {total_constituents}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_constituents': total_constituents
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_history_constituents()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_history_constituents function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平历史成分股数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'constituents' in data:
                    # 这是一个包含constituents的结果
                    base_info = {k: v for k, v in data.items() if k != 'constituents'}
                    constituents = data['constituents']
                    
                    if isinstance(constituents, list):
                        for i, constituent in enumerate(constituents):
                            flat_result = base_info.copy()
                            flat_result['constituent_index'] = i
                            if isinstance(constituent, dict):
                                for key, value in constituent.items():
                                    flat_result[f'constituent_{key}'] = value
                            flattened_results.append(flat_result)
                    elif constituents:
                        flat_result = base_info.copy()
                        if isinstance(constituents, dict):
                            for key, value in constituents.items():
                                flat_result[f'constituent_{key}'] = value
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
    print("GM API get_history_constituents() 功能测试")
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
        
        # 测试1: 主要指数的历史成分股查询
        major_results = test_get_history_constituents_major_indices()
        save_results(major_results, 'get_history_constituents_major')
        all_results.append(major_results)
        
        # 测试2: 不同日期范围的历史成分股查询
        date_range_results = test_get_history_constituents_date_ranges()
        save_results(date_range_results, 'get_history_constituents_date_ranges')
        all_results.append(date_range_results)
        
        # 测试3: 行业指数的历史成分股查询
        sector_results = test_get_history_constituents_sector_indices()
        save_results(sector_results, 'get_history_constituents_sector')
        all_results.append(sector_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_history_constituents_edge_cases()
        save_results(edge_results, 'get_history_constituents_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_history_constituents_data(all_results)
        
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
        print(f"主要指数测试: {major_success}/{major_total} 成功, {major_data} 条历史成分股记录")
        
        date_range_success, date_range_total, date_range_data = count_success_and_data(date_range_results)
        print(f"日期范围测试: {date_range_success}/{date_range_total} 成功, {date_range_data} 条历史成分股记录")
        
        sector_success, sector_total, sector_data = count_success_and_data(sector_results)
        print(f"行业指数测试: {sector_success}/{sector_total} 成功, {sector_data} 条历史成分股记录")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 条历史成分股记录")
        
        # 总体统计
        total_tests = major_total + date_range_total + sector_total + edge_total
        total_success = major_success + date_range_success + sector_success + edge_success
        total_data_count = major_data + date_range_data + sector_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总历史成分股记录数: {total_data_count}")
        
        # 数据结构统计
        print(f"\n历史成分股数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_history_constituents() API测试完成！")

if __name__ == "__main__":
    main()