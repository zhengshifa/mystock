#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_symbol_infos() 获取标的基础信息
功能：测试 gm.get_symbol_infos() API的各种用法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import gmtrade as gm
import pandas as pd
import json
from datetime import datetime
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

def symbol_info_to_dict(symbol_info):
    """将symbol_info对象转换为字典格式"""
    if symbol_info is None:
        return None
    
    try:
        info_dict = {}
        
        # 常见的symbol_info属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'list_date', 'delist_date', 'is_active', 'multiplier',
            'price_tick', 'upper_limit', 'lower_limit', 'pre_close',
            'margin_ratio', 'settle_mode', 'product_type', 'contract_type',
            'exercise_type', 'delivery_year', 'delivery_month', 'strike_price',
            'call_put', 'underlying_symbol', 'underlying_type', 'maturity_date',
            'created_at', 'updated_at', 'min_order_volume', 'max_order_volume',
            'trade_unit', 'currency', 'board_type', 'status'
        ]
        
        for attr in attributes:
            if hasattr(symbol_info, attr):
                value = getattr(symbol_info, attr)
                # 处理日期时间类型
                if attr in ['list_date', 'delist_date', 'maturity_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            info_dict[attr] = value.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            info_dict[attr] = str(value)
                    except:
                        info_dict[attr] = str(value)
                else:
                    info_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not info_dict:
            info_dict = {'raw_data': str(symbol_info)}
        
        return info_dict
        
    except Exception as e:
        return {'error': f'Failed to convert symbol_info: {e}', 'raw_data': str(symbol_info)}

def test_get_symbol_infos_single():
    """测试获取单个标的信息"""
    print("\n=== 测试获取单个标的信息 ===")
    
    test_symbols = [
        'SZSE.000001',  # 平安银行
        'SHSE.600000',  # 浦发银行
        'SZSE.000002',  # 万科A
        'SHSE.600036',  # 招商银行
        'SHSE.600519',  # 贵州茅台
        'SHSE.000001',  # 上证指数
        'SZSE.399001',  # 深证成指
        'SZSE.300015'   # 爱尔眼科
    ]
    
    results = []
    
    for symbol in test_symbols:
        try:
            print(f"\n查询 {symbol} 的基础信息...")
            
            # 获取单个标的信息
            symbol_info = gm.get_symbol_infos(symbols=symbol)
            
            if symbol_info is not None:
                # 转换为字典
                if hasattr(symbol_info, '__iter__') and not isinstance(symbol_info, str):
                    # 如果返回的是列表或其他可迭代对象
                    info_list = []
                    for info in symbol_info:
                        info_dict = symbol_info_to_dict(info)
                        if info_dict:
                            info_list.append(info_dict)
                    
                    result = {
                        'symbol': symbol,
                        'symbol_infos': info_list,
                        'count': len(info_list),
                        'timestamp': datetime.now().isoformat(),
                        'success': True,
                        'error': None
                    }
                    
                    print(f"  获取到 {len(info_list)} 个结果")
                    
                    # 显示详细信息
                    if info_list:
                        info = info_list[0]
                        print(f"  标的名称: {info.get('sec_name', 'N/A')}")
                        print(f"  证券类型: {info.get('sec_type', 'N/A')}")
                        print(f"  交易所: {info.get('exchange', 'N/A')}")
                        print(f"  上市日期: {info.get('list_date', 'N/A')}")
                        print(f"  是否活跃: {info.get('is_active', 'N/A')}")
                        print(f"  最小价格变动: {info.get('price_tick', 'N/A')}")
                        print(f"  交易单位: {info.get('trade_unit', 'N/A')}")
                else:
                    # 单个对象
                    info_dict = symbol_info_to_dict(symbol_info)
                    
                    result = {
                        'symbol': symbol,
                        'symbol_infos': [info_dict] if info_dict else [],
                        'count': 1 if info_dict else 0,
                        'timestamp': datetime.now().isoformat(),
                        'success': True,
                        'error': None
                    }
                    
                    print(f"  获取到 1 个结果")
                    
                    if info_dict:
                        print(f"  标的名称: {info_dict.get('sec_name', 'N/A')}")
                        print(f"  证券类型: {info_dict.get('sec_type', 'N/A')}")
                        print(f"  交易所: {info_dict.get('exchange', 'N/A')}")
                        print(f"  上市日期: {info_dict.get('list_date', 'N/A')}")
                        print(f"  是否活跃: {info_dict.get('is_active', 'N/A')}")
                        print(f"  最小价格变动: {info_dict.get('price_tick', 'N/A')}")
                        print(f"  交易单位: {info_dict.get('trade_unit', 'N/A')}")
                
            else:
                result = {
                    'symbol': symbol,
                    'symbol_infos': [],
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
                'symbol': symbol,
                'symbol_infos': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_symbol_infos_multiple():
    """测试批量获取标的信息"""
    print("\n=== 测试批量获取标的信息 ===")
    
    test_cases = [
        {
            'name': '银行股',
            'symbols': ['SZSE.000001', 'SHSE.600000', 'SHSE.600036', 'SHSE.601398']
        },
        {
            'name': '科技股',
            'symbols': ['SZSE.000002', 'SZSE.300015', 'SHSE.600519', 'SZSE.002415']
        },
        {
            'name': '指数',
            'symbols': ['SHSE.000001', 'SZSE.399001', 'SZSE.399006']
        },
        {
            'name': '混合类型',
            'symbols': ['SHSE.600000', 'SZSE.399001', 'SZSE.000001', 'SHSE.000001']
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n批量查询 {test_case['name']} ({len(test_case['symbols'])}个标的)...")
            
            # 批量获取标的信息
            symbol_infos = gm.get_symbol_infos(symbols=test_case['symbols'])
            
            if symbol_infos is not None:
                # 转换为字典列表
                info_list = []
                if hasattr(symbol_infos, '__iter__') and not isinstance(symbol_infos, str):
                    for info in symbol_infos:
                        info_dict = symbol_info_to_dict(info)
                        if info_dict:
                            info_list.append(info_dict)
                else:
                    info_dict = symbol_info_to_dict(symbol_infos)
                    if info_dict:
                        info_list.append(info_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'input_symbols': test_case['symbols'],
                    'symbol_infos': info_list,
                    'input_count': len(test_case['symbols']),
                    'output_count': len(info_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  输入 {len(test_case['symbols'])} 个标的，获取到 {len(info_list)} 个结果")
                
                # 显示结果摘要
                if info_list:
                    print(f"  结果摘要:")
                    for i, info in enumerate(info_list[:5]):  # 只显示前5个
                        symbol = info.get('symbol', 'N/A')
                        sec_name = info.get('sec_name', 'N/A')
                        sec_type = info.get('sec_type', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} ({sec_type})")
                    
                    if len(info_list) > 5:
                        print(f"    ... 还有 {len(info_list) - 5} 个结果")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'input_symbols': test_case['symbols'],
                    'symbol_infos': [],
                    'input_count': len(test_case['symbols']),
                    'output_count': 0,
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
                'input_symbols': test_case['symbols'],
                'symbol_infos': [],
                'input_count': len(test_case['symbols']),
                'output_count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_symbol_infos_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的标的',
            'symbols': ['INVALID.000000', 'FAKE.999999']
        },
        {
            'name': '空列表',
            'symbols': []
        },
        {
            'name': '重复标的',
            'symbols': ['SZSE.000001', 'SZSE.000001', 'SHSE.600000', 'SHSE.600000']
        },
        {
            'name': '格式错误的标的',
            'symbols': ['000001', 'SZSE000001', 'SHSE.', '.600000']
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']}...")
            
            # 获取标的信息
            symbol_infos = gm.get_symbol_infos(symbols=test_case['symbols'])
            
            if symbol_infos is not None:
                # 转换为字典列表
                info_list = []
                if hasattr(symbol_infos, '__iter__') and not isinstance(symbol_infos, str):
                    for info in symbol_infos:
                        info_dict = symbol_info_to_dict(info)
                        if info_dict:
                            info_list.append(info_dict)
                else:
                    info_dict = symbol_info_to_dict(symbol_infos)
                    if info_dict:
                        info_list.append(info_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'input_symbols': test_case['symbols'],
                    'symbol_infos': info_list,
                    'input_count': len(test_case['symbols']),
                    'output_count': len(info_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  输入 {len(test_case['symbols'])} 个标的，获取到 {len(info_list)} 个结果")
                
                if info_list:
                    print(f"  有效结果:")
                    for info in info_list:
                        symbol = info.get('symbol', 'N/A')
                        sec_name = info.get('sec_name', 'N/A')
                        print(f"    {symbol} - {sec_name}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'input_symbols': test_case['symbols'],
                    'symbol_infos': [],
                    'input_count': len(test_case['symbols']),
                    'output_count': 0,
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
                'input_symbols': test_case['symbols'],
                'symbol_infos': [],
                'input_count': len(test_case['symbols']),
                'output_count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_symbol_infos_data(results):
    """分析标的信息数据结构"""
    print("\n=== 标的信息数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_symbols = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_symbols
        
        if isinstance(data, dict):
            if 'symbol_infos' in data:
                symbol_infos = data['symbol_infos']
                if isinstance(symbol_infos, list):
                    total_symbols += len(symbol_infos)
                    for info in symbol_infos:
                        if isinstance(info, dict):
                            for field in info.keys():
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
        print(f"发现的标的信息字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的标的信息字段")
    
    print(f"\n总标的数量: {total_symbols}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_symbols': total_symbols
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_symbol_infos()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_symbol_infos function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平标的信息数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'symbol_infos' in data:
                    # 这是一个包含symbol_infos的结果
                    base_info = {k: v for k, v in data.items() if k != 'symbol_infos'}
                    symbol_infos = data['symbol_infos']
                    
                    if isinstance(symbol_infos, list):
                        for i, info in enumerate(symbol_infos):
                            flat_result = base_info.copy()
                            flat_result['symbol_info_index'] = i
                            if isinstance(info, dict):
                                for key, value in info.items():
                                    flat_result[f'info_{key}'] = value
                            flattened_results.append(flat_result)
                    elif symbol_infos:
                        flat_result = base_info.copy()
                        if isinstance(symbol_infos, dict):
                            for key, value in symbol_infos.items():
                                flat_result[f'info_{key}'] = value
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
    print("GM API get_symbol_infos() 功能测试")
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
        
        # 测试1: 获取单个标的信息
        single_results = test_get_symbol_infos_single()
        save_results(single_results, 'get_symbol_infos_single')
        all_results.append(single_results)
        
        # 测试2: 批量获取标的信息
        multiple_results = test_get_symbol_infos_multiple()
        save_results(multiple_results, 'get_symbol_infos_multiple')
        all_results.append(multiple_results)
        
        # 测试3: 边界情况测试
        edge_results = test_get_symbol_infos_edge_cases()
        save_results(edge_results, 'get_symbol_infos_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_symbol_infos_data(all_results)
        
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
                        data_count += data.get('output_count', data.get('count', 0))
                    else:
                        for value in data.values():
                            if isinstance(value, (dict, list)):
                                count_recursive(value)
                elif isinstance(data, list):
                    for item in data:
                        count_recursive(item)
            
            count_recursive(results)
            return success_count, total_count, data_count
        
        single_success, single_total, single_data = count_success_and_data(single_results)
        print(f"单个标的查询: {single_success}/{single_total} 成功, {single_data} 个标的")
        
        multiple_success, multiple_total, multiple_data = count_success_and_data(multiple_results)
        print(f"批量标的查询: {multiple_success}/{multiple_total} 成功, {multiple_data} 个标的")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 个标的")
        
        # 总体统计
        total_tests = single_total + multiple_total + edge_total
        total_success = single_success + multiple_success + edge_success
        total_data_count = single_data + multiple_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总标的数量: {total_data_count}")
        
        # 数据结构统计
        print(f"\n标的信息数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_symbol_infos() API测试完成！")

if __name__ == "__main__":
    main()