#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_instruments() 获取交易标的基础信息
功能：测试 gm.get_instruments() API的各种用法
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

def instrument_to_dict(instrument):
    """将instrument对象转换为字典格式"""
    if instrument is None:
        return None
    
    try:
        instrument_dict = {}
        
        # 常见的instrument属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'list_date', 'delist_date', 'is_active', 'multiplier',
            'price_tick', 'upper_limit', 'lower_limit', 'pre_close',
            'margin_ratio', 'settle_mode', 'product_type', 'contract_type',
            'exercise_type', 'delivery_year', 'delivery_month', 'strike_price',
            'call_put', 'underlying_symbol', 'underlying_type', 'maturity_date',
            'created_at', 'updated_at'
        ]
        
        for attr in attributes:
            if hasattr(instrument, attr):
                value = getattr(instrument, attr)
                # 处理日期时间类型
                if attr in ['list_date', 'delist_date', 'maturity_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            instrument_dict[attr] = value.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            instrument_dict[attr] = str(value)
                    except:
                        instrument_dict[attr] = str(value)
                else:
                    instrument_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not instrument_dict:
            instrument_dict = {'raw_data': str(instrument)}
        
        return instrument_dict
        
    except Exception as e:
        return {'error': f'Failed to convert instrument: {e}', 'raw_data': str(instrument)}

def test_get_instruments_by_exchange():
    """测试按交易所获取交易标的"""
    print("\n=== 测试按交易所获取交易标的 ===")
    
    exchanges = ['SHSE', 'SZSE', 'CFFEX', 'SHFE', 'DCE', 'CZCE']
    
    results = {}
    
    for exchange in exchanges:
        try:
            print(f"\n查询 {exchange} 交易所的交易标的...")
            
            # 获取指定交易所的交易标的
            instruments = gm.get_instruments(exchange=exchange)
            
            if instruments is not None:
                # 转换为字典列表
                instruments_list = []
                if hasattr(instruments, '__iter__'):
                    for instrument in instruments:
                        instrument_dict = instrument_to_dict(instrument)
                        if instrument_dict:
                            instruments_list.append(instrument_dict)
                else:
                    instrument_dict = instrument_to_dict(instruments)
                    if instrument_dict:
                        instruments_list.append(instrument_dict)
                
                result = {
                    'exchange': exchange,
                    'instruments': instruments_list,
                    'count': len(instruments_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(instruments_list)} 个交易标的")
                
                # 显示前几个标的的信息
                if instruments_list:
                    print(f"  示例标的:")
                    for i, inst in enumerate(instruments_list[:3]):
                        symbol = inst.get('symbol', 'N/A')
                        sec_name = inst.get('sec_name', 'N/A')
                        sec_type = inst.get('sec_type', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} ({sec_type})")
                
            else:
                result = {
                    'exchange': exchange,
                    'instruments': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无数据返回")
            
            results[exchange] = result
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results[exchange] = {
                'exchange': exchange,
                'instruments': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    return results

def test_get_instruments_by_sec_type():
    """测试按证券类型获取交易标的"""
    print("\n=== 测试按证券类型获取交易标的 ===")
    
    sec_types = ['STOCK', 'INDEX', 'FUND', 'BOND', 'FUTURE', 'OPTION']
    
    results = {}
    
    for sec_type in sec_types:
        try:
            print(f"\n查询 {sec_type} 类型的交易标的...")
            
            # 获取指定类型的交易标的
            instruments = gm.get_instruments(sec_type=sec_type)
            
            if instruments is not None:
                # 转换为字典列表
                instruments_list = []
                if hasattr(instruments, '__iter__'):
                    for instrument in instruments:
                        instrument_dict = instrument_to_dict(instrument)
                        if instrument_dict:
                            instruments_list.append(instrument_dict)
                else:
                    instrument_dict = instrument_to_dict(instruments)
                    if instrument_dict:
                        instruments_list.append(instrument_dict)
                
                result = {
                    'sec_type': sec_type,
                    'instruments': instruments_list,
                    'count': len(instruments_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(instruments_list)} 个交易标的")
                
                # 显示前几个标的的信息
                if instruments_list:
                    print(f"  示例标的:")
                    for i, inst in enumerate(instruments_list[:3]):
                        symbol = inst.get('symbol', 'N/A')
                        sec_name = inst.get('sec_name', 'N/A')
                        exchange = inst.get('exchange', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} ({exchange})")
                
            else:
                result = {
                    'sec_type': sec_type,
                    'instruments': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无数据返回")
            
            results[sec_type] = result
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results[sec_type] = {
                'sec_type': sec_type,
                'instruments': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    return results

def test_get_instruments_specific_symbols():
    """测试获取特定标的的信息"""
    print("\n=== 测试获取特定标的信息 ===")
    
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
            
            # 获取特定标的信息
            instruments = gm.get_instruments(symbols=symbol)
            
            if instruments is not None:
                # 转换为字典列表
                instruments_list = []
                if hasattr(instruments, '__iter__'):
                    for instrument in instruments:
                        instrument_dict = instrument_to_dict(instrument)
                        if instrument_dict:
                            instruments_list.append(instrument_dict)
                else:
                    instrument_dict = instrument_to_dict(instruments)
                    if instrument_dict:
                        instruments_list.append(instrument_dict)
                
                result = {
                    'symbol': symbol,
                    'instruments': instruments_list,
                    'count': len(instruments_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(instruments_list)} 个结果")
                
                # 显示详细信息
                if instruments_list:
                    inst = instruments_list[0]
                    print(f"  标的名称: {inst.get('sec_name', 'N/A')}")
                    print(f"  证券类型: {inst.get('sec_type', 'N/A')}")
                    print(f"  交易所: {inst.get('exchange', 'N/A')}")
                    print(f"  上市日期: {inst.get('list_date', 'N/A')}")
                    print(f"  是否活跃: {inst.get('is_active', 'N/A')}")
                
            else:
                result = {
                    'symbol': symbol,
                    'instruments': [],
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
                'instruments': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_instruments_combined_filters():
    """测试组合条件筛选交易标的"""
    print("\n=== 测试组合条件筛选交易标的 ===")
    
    test_cases = [
        {'exchange': 'SHSE', 'sec_type': 'STOCK', 'name': '上交所股票'},
        {'exchange': 'SZSE', 'sec_type': 'STOCK', 'name': '深交所股票'},
        {'exchange': 'SHSE', 'sec_type': 'INDEX', 'name': '上交所指数'},
        {'exchange': 'SZSE', 'sec_type': 'INDEX', 'name': '深交所指数'},
        {'sec_type': 'FUND', 'name': '基金产品'}
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n查询 {test_case['name']}...")
            
            # 构建查询参数
            kwargs = {k: v for k, v in test_case.items() if k != 'name'}
            
            # 获取交易标的
            instruments = gm.get_instruments(**kwargs)
            
            if instruments is not None:
                # 转换为字典列表
                instruments_list = []
                if hasattr(instruments, '__iter__'):
                    for instrument in instruments:
                        instrument_dict = instrument_to_dict(instrument)
                        if instrument_dict:
                            instruments_list.append(instrument_dict)
                else:
                    instrument_dict = instrument_to_dict(instruments)
                    if instrument_dict:
                        instruments_list.append(instrument_dict)
                
                result = {
                    'filter_name': test_case['name'],
                    'filters': kwargs,
                    'instruments': instruments_list,
                    'count': len(instruments_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(instruments_list)} 个交易标的")
                
                # 显示前几个标的的信息
                if instruments_list:
                    print(f"  示例标的:")
                    for i, inst in enumerate(instruments_list[:3]):
                        symbol = inst.get('symbol', 'N/A')
                        sec_name = inst.get('sec_name', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name}")
                
            else:
                result = {
                    'filter_name': test_case['name'],
                    'filters': kwargs,
                    'instruments': [],
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
                'filter_name': test_case['name'],
                'filters': kwargs,
                'instruments': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_instruments_data(results):
    """分析交易标的数据结构"""
    print("\n=== 交易标的数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_instruments = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_instruments
        
        if isinstance(data, dict):
            if 'instruments' in data:
                instruments = data['instruments']
                if isinstance(instruments, list):
                    total_instruments += len(instruments)
                    for inst in instruments:
                        if isinstance(inst, dict):
                            for field in inst.keys():
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
        print(f"发现的交易标的字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的交易标的字段")
    
    print(f"\n总交易标的数量: {total_instruments}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_instruments': total_instruments
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_instruments()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_instruments function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平交易标的数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'instruments' in data:
                    # 这是一个包含instruments的结果
                    base_info = {k: v for k, v in data.items() if k != 'instruments'}
                    instruments = data['instruments']
                    
                    if isinstance(instruments, list):
                        for i, inst in enumerate(instruments):
                            flat_result = base_info.copy()
                            flat_result['instrument_index'] = i
                            if isinstance(inst, dict):
                                for key, value in inst.items():
                                    flat_result[f'inst_{key}'] = value
                            flattened_results.append(flat_result)
                    elif instruments:
                        flat_result = base_info.copy()
                        if isinstance(instruments, dict):
                            for key, value in instruments.items():
                                flat_result[f'inst_{key}'] = value
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
    print("GM API get_instruments() 功能测试")
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
        
        # 测试1: 按交易所获取交易标的
        exchange_results = test_get_instruments_by_exchange()
        save_results(exchange_results, 'get_instruments_by_exchange')
        all_results.append(exchange_results)
        
        # 测试2: 按证券类型获取交易标的
        sec_type_results = test_get_instruments_by_sec_type()
        save_results(sec_type_results, 'get_instruments_by_sec_type')
        all_results.append(sec_type_results)
        
        # 测试3: 获取特定标的信息
        specific_results = test_get_instruments_specific_symbols()
        save_results(specific_results, 'get_instruments_specific')
        all_results.append(specific_results)
        
        # 测试4: 组合条件筛选
        combined_results = test_get_instruments_combined_filters()
        save_results(combined_results, 'get_instruments_combined')
        all_results.append(combined_results)
        
        # 分析数据结构
        structure_analysis = analyze_instruments_data(all_results)
        
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
        
        exchange_success, exchange_total, exchange_data = count_success_and_data(exchange_results)
        print(f"按交易所查询: {exchange_success}/{exchange_total} 成功, {exchange_data} 个标的")
        
        sec_type_success, sec_type_total, sec_type_data = count_success_and_data(sec_type_results)
        print(f"按证券类型查询: {sec_type_success}/{sec_type_total} 成功, {sec_type_data} 个标的")
        
        specific_success, specific_total, specific_data = count_success_and_data(specific_results)
        print(f"特定标的查询: {specific_success}/{specific_total} 成功, {specific_data} 个标的")
        
        combined_success, combined_total, combined_data = count_success_and_data(combined_results)
        print(f"组合条件查询: {combined_success}/{combined_total} 成功, {combined_data} 个标的")
        
        # 总体统计
        total_tests = exchange_total + sec_type_total + specific_total + combined_total
        total_success = exchange_success + sec_type_success + specific_success + combined_success
        total_data_count = exchange_data + sec_type_data + specific_data + combined_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总标的数量: {total_data_count}")
        
        # 数据结构统计
        print(f"\n交易标的数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_instruments() API测试完成！")

if __name__ == "__main__":
    main()