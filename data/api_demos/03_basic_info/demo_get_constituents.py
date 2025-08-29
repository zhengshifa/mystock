#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_constituents() 获取指数成分股
功能：测试 gm.get_constituents() API的各种用法
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
            'weight', 'in_date', 'out_date', 'is_active',
            'industry', 'sector', 'market_cap', 'free_float_market_cap',
            'created_at', 'updated_at'
        ]
        
        for attr in attributes:
            if hasattr(constituent, attr):
                value = getattr(constituent, attr)
                # 处理日期时间类型
                if attr in ['in_date', 'out_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            constituent_dict[attr] = value.strftime('%Y-%m-%d %H:%M:%S')
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

def test_get_constituents_major_indices():
    """测试主要指数的成分股"""
    print("\n=== 测试主要指数成分股 ===")
    
    major_indices = [
        {'symbol': 'SHSE.000001', 'name': '上证指数'},
        {'symbol': 'SZSE.399001', 'name': '深证成指'},
        {'symbol': 'SZSE.399006', 'name': '创业板指'},
        {'symbol': 'SHSE.000016', 'name': '上证50'},
        {'symbol': 'SHSE.000300', 'name': '沪深300'},
        {'symbol': 'SHSE.000905', 'name': '中证500'},
        {'symbol': 'SZSE.399905', 'name': '中证500(深)'},
        {'symbol': 'SHSE.000852', 'name': '中证1000'}
    ]
    
    results = []
    
    for index_info in major_indices:
        try:
            print(f"\n查询 {index_info['name']} ({index_info['symbol']}) 的成分股...")
            
            # 获取指数成分股
            constituents = gm.get_constituents(
                index=index_info['symbol'],
                trade_date=datetime.now().strftime('%Y-%m-%d')
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
                    'trade_date': datetime.now().strftime('%Y-%m-%d'),
                    'constituents': constituents_list,
                    'count': len(constituents_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(constituents_list)} 个成分股")
                
                # 显示前几个成分股的信息
                if constituents_list:
                    print(f"  示例成分股:")
                    for i, constituent in enumerate(constituents_list[:5]):
                        symbol = constituent.get('symbol', 'N/A')
                        sec_name = constituent.get('sec_name', 'N/A')
                        weight = constituent.get('weight', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} (权重: {weight})")
                    
                    if len(constituents_list) > 5:
                        print(f"    ... 还有 {len(constituents_list) - 5} 个成分股")
                
            else:
                result = {
                    'index_symbol': index_info['symbol'],
                    'index_name': index_info['name'],
                    'trade_date': datetime.now().strftime('%Y-%m-%d'),
                    'constituents': [],
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
                'index_symbol': index_info['symbol'],
                'index_name': index_info['name'],
                'trade_date': datetime.now().strftime('%Y-%m-%d'),
                'constituents': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_constituents_historical():
    """测试历史日期的成分股"""
    print("\n=== 测试历史日期成分股 ===")
    
    # 测试不同历史日期的沪深300成分股
    test_dates = [
        (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),  # 一个月前
        (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),  # 三个月前
        (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'), # 半年前
        '2024-01-01',  # 2024年初
        '2023-12-31',  # 2023年末
        '2023-06-30'   # 2023年中
    ]
    
    index_symbol = 'SHSE.000300'  # 沪深300
    index_name = '沪深300'
    
    results = []
    
    for trade_date in test_dates:
        try:
            print(f"\n查询 {index_name} 在 {trade_date} 的成分股...")
            
            # 获取指定日期的成分股
            constituents = gm.get_constituents(
                index=index_symbol,
                trade_date=trade_date
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
                    'index_symbol': index_symbol,
                    'index_name': index_name,
                    'trade_date': trade_date,
                    'constituents': constituents_list,
                    'count': len(constituents_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(constituents_list)} 个成分股")
                
                # 显示权重统计
                if constituents_list:
                    weights = [c.get('weight', 0) for c in constituents_list if c.get('weight') is not None]
                    if weights:
                        total_weight = sum(weights)
                        max_weight = max(weights)
                        min_weight = min(weights)
                        print(f"  权重统计: 总权重={total_weight:.2f}%, 最大权重={max_weight:.2f}%, 最小权重={min_weight:.2f}%")
                    
                    # 显示前几个权重最大的成分股
                    sorted_constituents = sorted(constituents_list, 
                                               key=lambda x: x.get('weight', 0) if x.get('weight') is not None else 0, 
                                               reverse=True)
                    print(f"  权重最大的5个成分股:")
                    for i, constituent in enumerate(sorted_constituents[:5]):
                        symbol = constituent.get('symbol', 'N/A')
                        sec_name = constituent.get('sec_name', 'N/A')
                        weight = constituent.get('weight', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} (权重: {weight}%)")
                
            else:
                result = {
                    'index_symbol': index_symbol,
                    'index_name': index_name,
                    'trade_date': trade_date,
                    'constituents': [],
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
                'index_symbol': index_symbol,
                'index_name': index_name,
                'trade_date': trade_date,
                'constituents': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_constituents_sector_indices():
    """测试行业指数成分股"""
    print("\n=== 测试行业指数成分股 ===")
    
    # 常见行业指数
    sector_indices = [
        {'symbol': 'SHSE.000037', 'name': '上证医药'},
        {'symbol': 'SHSE.000036', 'name': '上证消费'},
        {'symbol': 'SHSE.000035', 'name': '上证金融'},
        {'symbol': 'SHSE.000034', 'name': '上证地产'},
        {'symbol': 'SHSE.000033', 'name': '上证能源'},
        {'symbol': 'SHSE.000032', 'name': '上证材料'}
    ]
    
    results = []
    trade_date = datetime.now().strftime('%Y-%m-%d')
    
    for index_info in sector_indices:
        try:
            print(f"\n查询 {index_info['name']} ({index_info['symbol']}) 的成分股...")
            
            # 获取行业指数成分股
            constituents = gm.get_constituents(
                index=index_info['symbol'],
                trade_date=trade_date
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
                    'trade_date': trade_date,
                    'constituents': constituents_list,
                    'count': len(constituents_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(constituents_list)} 个成分股")
                
                # 显示成分股信息
                if constituents_list:
                    print(f"  成分股列表:")
                    for i, constituent in enumerate(constituents_list[:10]):
                        symbol = constituent.get('symbol', 'N/A')
                        sec_name = constituent.get('sec_name', 'N/A')
                        weight = constituent.get('weight', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} (权重: {weight})")
                    
                    if len(constituents_list) > 10:
                        print(f"    ... 还有 {len(constituents_list) - 10} 个成分股")
                
            else:
                result = {
                    'index_symbol': index_info['symbol'],
                    'index_name': index_info['name'],
                    'trade_date': trade_date,
                    'constituents': [],
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
                'index_symbol': index_info['symbol'],
                'index_name': index_info['name'],
                'trade_date': trade_date,
                'constituents': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_constituents_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的指数',
            'symbol': 'INVALID.000000',
            'trade_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '未来日期',
            'symbol': 'SHSE.000300',
            'trade_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'symbol': 'SHSE.000300',
            'trade_date': '2000-01-01'
        },
        {
            'name': '非交易日',
            'symbol': 'SHSE.000300',
            'trade_date': '2024-01-01'  # 元旦
        },
        {
            'name': '周末日期',
            'symbol': 'SHSE.000300',
            'trade_date': '2024-01-06'  # 周六
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']} ({test_case['symbol']}, {test_case['trade_date']})...")
            
            # 获取成分股
            constituents = gm.get_constituents(
                index=test_case['symbol'],
                trade_date=test_case['trade_date']
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
                    'index_symbol': test_case['symbol'],
                    'trade_date': test_case['trade_date'],
                    'constituents': constituents_list,
                    'count': len(constituents_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(constituents_list)} 个成分股")
                
                if constituents_list:
                    print(f"  前几个成分股:")
                    for i, constituent in enumerate(constituents_list[:3]):
                        symbol = constituent.get('symbol', 'N/A')
                        sec_name = constituent.get('sec_name', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'index_symbol': test_case['symbol'],
                    'trade_date': test_case['trade_date'],
                    'constituents': [],
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
                'index_symbol': test_case['symbol'],
                'trade_date': test_case['trade_date'],
                'constituents': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_constituents_data(results):
    """分析成分股数据结构"""
    print("\n=== 成分股数据结构分析 ===")
    
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
        print(f"发现的成分股字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的成分股字段")
    
    print(f"\n总成分股数量: {total_constituents}")
    
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
                'api_function': 'gm.get_constituents()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_constituents function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平成分股数据）
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
    print("GM API get_constituents() 功能测试")
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
        
        # 测试1: 主要指数成分股
        major_results = test_get_constituents_major_indices()
        save_results(major_results, 'get_constituents_major')
        all_results.append(major_results)
        
        # 测试2: 历史日期成分股
        historical_results = test_get_constituents_historical()
        save_results(historical_results, 'get_constituents_historical')
        all_results.append(historical_results)
        
        # 测试3: 行业指数成分股
        sector_results = test_get_constituents_sector_indices()
        save_results(sector_results, 'get_constituents_sector')
        all_results.append(sector_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_constituents_edge_cases()
        save_results(edge_results, 'get_constituents_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_constituents_data(all_results)
        
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
        print(f"主要指数测试: {major_success}/{major_total} 成功, {major_data} 个成分股")
        
        historical_success, historical_total, historical_data = count_success_and_data(historical_results)
        print(f"历史日期测试: {historical_success}/{historical_total} 成功, {historical_data} 个成分股")
        
        sector_success, sector_total, sector_data = count_success_and_data(sector_results)
        print(f"行业指数测试: {sector_success}/{sector_total} 成功, {sector_data} 个成分股")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 个成分股")
        
        # 总体统计
        total_tests = major_total + historical_total + sector_total + edge_total
        total_success = major_success + historical_success + sector_success + edge_success
        total_data_count = major_data + historical_data + sector_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总成分股数量: {total_data_count}")
        
        # 数据结构统计
        print(f"\n成分股数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_constituents() API测试完成！")

if __name__ == "__main__":
    main()