#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_history_instruments() 获取历史合约信息
功能：测试 gm.get_history_instruments() API的各种用法
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
            'price_tick', 'upper_limit', 'lower_limit',
            'pre_close', 'pre_settle', 'margin_ratio',
            'contract_month', 'exercise_type', 'exercise_price',
            'underlying_symbol', 'option_type', 'delivery_month',
            'created_at', 'updated_at', 'currency', 'lot_size'
        ]
        
        for attr in attributes:
            if hasattr(instrument, attr):
                value = getattr(instrument, attr)
                # 处理日期时间类型
                if attr in ['list_date', 'delist_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            instrument_dict[attr] = value.strftime('%Y-%m-%d')
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

def test_get_history_instruments_by_exchange():
    """测试按交易所查询历史合约信息"""
    print("\n=== 测试按交易所查询历史合约信息 ===")
    
    exchanges = [
        {'exchange': 'SHSE', 'name': '上海证券交易所'},
        {'exchange': 'SZSE', 'name': '深圳证券交易所'},
        {'exchange': 'CFFEX', 'name': '中国金融期货交易所'},
        {'exchange': 'SHFE', 'name': '上海期货交易所'},
        {'exchange': 'DCE', 'name': '大连商品交易所'},
        {'exchange': 'CZCE', 'name': '郑州商品交易所'}
    ]
    
    results = []
    
    # 查询最近一年的历史合约
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for exchange_info in exchanges:
        try:
            print(f"\n查询 {exchange_info['name']} ({exchange_info['exchange']}) 的历史合约...")
            
            # 获取历史合约信息
            instruments = gm.get_history_instruments(
                exchange=exchange_info['exchange'],
                start_date=start_date,
                end_date=end_date
            )
            
            if instruments is not None:
                # 转换为字典列表
                instruments_list = []
                if hasattr(instruments, '__iter__') and not isinstance(instruments, str):
                    for instrument in instruments:
                        instrument_dict = instrument_to_dict(instrument)
                        if instrument_dict:
                            instruments_list.append(instrument_dict)
                else:
                    instrument_dict = instrument_to_dict(instruments)
                    if instrument_dict:
                        instruments_list.append(instrument_dict)
                
                result = {
                    'exchange': exchange_info['exchange'],
                    'exchange_name': exchange_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'instruments': instruments_list,
                    'count': len(instruments_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(instruments_list)} 个历史合约")
                
                # 分析合约类型分布
                if instruments_list:
                    sec_types = {}
                    for instrument in instruments_list:
                        sec_type = instrument.get('sec_type', 'Unknown')
                        sec_types[sec_type] = sec_types.get(sec_type, 0) + 1
                    
                    print(f"  合约类型分布:")
                    for sec_type, count in sec_types.items():
                        print(f"    {sec_type}: {count} 个")
                    
                    # 显示部分合约信息
                    print(f"  示例合约:")
                    for i, instrument in enumerate(instruments_list[:5]):
                        symbol = instrument.get('symbol', 'N/A')
                        sec_name = instrument.get('sec_name', 'N/A')
                        sec_type = instrument.get('sec_type', 'N/A')
                        list_date = instrument.get('list_date', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} ({sec_type}) 上市日期: {list_date}")
                
            else:
                result = {
                    'exchange': exchange_info['exchange'],
                    'exchange_name': exchange_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'instruments': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史合约数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'exchange': exchange_info['exchange'],
                'exchange_name': exchange_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'instruments': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_instruments_by_sec_type():
    """测试按证券类型查询历史合约信息"""
    print("\n=== 测试按证券类型查询历史合约信息 ===")
    
    sec_types = [
        {'sec_type': 'STOCK', 'name': '股票'},
        {'sec_type': 'FUND', 'name': '基金'},
        {'sec_type': 'INDEX', 'name': '指数'},
        {'sec_type': 'FUTURE', 'name': '期货'},
        {'sec_type': 'OPTION', 'name': '期权'},
        {'sec_type': 'BOND', 'name': '债券'}
    ]
    
    results = []
    
    # 查询最近6个月的历史合约
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for sec_type_info in sec_types:
        try:
            print(f"\n查询 {sec_type_info['name']} ({sec_type_info['sec_type']}) 类型的历史合约...")
            
            # 获取历史合约信息
            instruments = gm.get_history_instruments(
                sec_type=sec_type_info['sec_type'],
                start_date=start_date,
                end_date=end_date
            )
            
            if instruments is not None:
                # 转换为字典列表
                instruments_list = []
                if hasattr(instruments, '__iter__') and not isinstance(instruments, str):
                    for instrument in instruments:
                        instrument_dict = instrument_to_dict(instrument)
                        if instrument_dict:
                            instruments_list.append(instrument_dict)
                else:
                    instrument_dict = instrument_to_dict(instruments)
                    if instrument_dict:
                        instruments_list.append(instrument_dict)
                
                result = {
                    'sec_type': sec_type_info['sec_type'],
                    'sec_type_name': sec_type_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'instruments': instruments_list,
                    'count': len(instruments_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(instruments_list)} 个历史合约")
                
                # 分析交易所分布
                if instruments_list:
                    exchanges = {}
                    for instrument in instruments_list:
                        exchange = instrument.get('exchange', 'Unknown')
                        exchanges[exchange] = exchanges.get(exchange, 0) + 1
                    
                    print(f"  交易所分布:")
                    for exchange, count in exchanges.items():
                        print(f"    {exchange}: {count} 个")
                    
                    # 显示部分合约信息
                    print(f"  示例合约:")
                    for i, instrument in enumerate(instruments_list[:5]):
                        symbol = instrument.get('symbol', 'N/A')
                        sec_name = instrument.get('sec_name', 'N/A')
                        exchange = instrument.get('exchange', 'N/A')
                        list_date = instrument.get('list_date', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} ({exchange}) 上市日期: {list_date}")
                
            else:
                result = {
                    'sec_type': sec_type_info['sec_type'],
                    'sec_type_name': sec_type_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'instruments': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史合约数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'sec_type': sec_type_info['sec_type'],
                'sec_type_name': sec_type_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'instruments': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_instruments_by_date_range():
    """测试按不同日期范围查询历史合约信息"""
    print("\n=== 测试按不同日期范围查询历史合约信息 ===")
    
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
    
    # 选择上海证券交易所作为测试对象
    test_exchange = 'SHSE'
    
    for date_range in date_ranges:
        try:
            print(f"\n查询 {date_range['name']} ({date_range['start_date']} 到 {date_range['end_date']}) 的历史合约...")
            
            # 获取历史合约信息
            instruments = gm.get_history_instruments(
                exchange=test_exchange,
                start_date=date_range['start_date'],
                end_date=date_range['end_date']
            )
            
            if instruments is not None:
                # 转换为字典列表
                instruments_list = []
                if hasattr(instruments, '__iter__') and not isinstance(instruments, str):
                    for instrument in instruments:
                        instrument_dict = instrument_to_dict(instrument)
                        if instrument_dict:
                            instruments_list.append(instrument_dict)
                else:
                    instrument_dict = instrument_to_dict(instruments)
                    if instrument_dict:
                        instruments_list.append(instrument_dict)
                
                result = {
                    'date_range_name': date_range['name'],
                    'exchange': test_exchange,
                    'start_date': date_range['start_date'],
                    'end_date': date_range['end_date'],
                    'instruments': instruments_list,
                    'count': len(instruments_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(instruments_list)} 个历史合约")
                
                # 分析上市和退市情况
                if instruments_list:
                    listed_count = 0
                    delisted_count = 0
                    active_count = 0
                    
                    for instrument in instruments_list:
                        list_date = instrument.get('list_date')
                        delist_date = instrument.get('delist_date')
                        is_active = instrument.get('is_active')
                        
                        if list_date and list_date != 'N/A':
                            # 检查是否在查询期间上市
                            if date_range['start_date'] <= list_date <= date_range['end_date']:
                                listed_count += 1
                        
                        if delist_date and delist_date != 'N/A':
                            # 检查是否在查询期间退市
                            if date_range['start_date'] <= delist_date <= date_range['end_date']:
                                delisted_count += 1
                        
                        if is_active:
                            active_count += 1
                    
                    print(f"  期间上市: {listed_count} 个")
                    print(f"  期间退市: {delisted_count} 个")
                    print(f"  当前活跃: {active_count} 个")
                    
                    # 显示最新上市的合约
                    sorted_instruments = sorted(
                        [i for i in instruments_list if i.get('list_date') and i.get('list_date') != 'N/A'],
                        key=lambda x: x.get('list_date', ''),
                        reverse=True
                    )
                    
                    if sorted_instruments:
                        print(f"  最新上市的5个合约:")
                        for i, instrument in enumerate(sorted_instruments[:5]):
                            symbol = instrument.get('symbol', 'N/A')
                            sec_name = instrument.get('sec_name', 'N/A')
                            list_date = instrument.get('list_date', 'N/A')
                            print(f"    {i+1}. {symbol} - {sec_name} (上市日期: {list_date})")
                
            else:
                result = {
                    'date_range_name': date_range['name'],
                    'exchange': test_exchange,
                    'start_date': date_range['start_date'],
                    'end_date': date_range['end_date'],
                    'instruments': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史合约数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'date_range_name': date_range['name'],
                'exchange': test_exchange,
                'start_date': date_range['start_date'],
                'end_date': date_range['end_date'],
                'instruments': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_instruments_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的交易所',
            'exchange': 'INVALID',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '未来日期范围',
            'exchange': 'SHSE',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'exchange': 'SHSE',
            'start_date': '1990-01-01',
            'end_date': '1990-12-31'
        },
        {
            'name': '单日查询',
            'exchange': 'SHSE',
            'start_date': '2023-06-15',
            'end_date': '2023-06-15'
        },
        {
            'name': '日期顺序颠倒',
            'exchange': 'SHSE',
            'start_date': '2023-12-31',
            'end_date': '2023-01-01'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']}...")
            
            # 获取历史合约信息
            instruments = gm.get_history_instruments(
                exchange=test_case.get('exchange'),
                sec_type=test_case.get('sec_type'),
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if instruments is not None:
                # 转换为字典列表
                instruments_list = []
                if hasattr(instruments, '__iter__') and not isinstance(instruments, str):
                    for instrument in instruments:
                        instrument_dict = instrument_to_dict(instrument)
                        if instrument_dict:
                            instruments_list.append(instrument_dict)
                else:
                    instrument_dict = instrument_to_dict(instruments)
                    if instrument_dict:
                        instruments_list.append(instrument_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'exchange': test_case.get('exchange'),
                    'sec_type': test_case.get('sec_type'),
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'instruments': instruments_list,
                    'count': len(instruments_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(instruments_list)} 个历史合约")
                
                if instruments_list:
                    print(f"  前几个合约:")
                    for i, instrument in enumerate(instruments_list[:3]):
                        symbol = instrument.get('symbol', 'N/A')
                        sec_name = instrument.get('sec_name', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'exchange': test_case.get('exchange'),
                    'sec_type': test_case.get('sec_type'),
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'instruments': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史合约数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'exchange': test_case.get('exchange'),
                'sec_type': test_case.get('sec_type'),
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'instruments': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_history_instruments_data(results):
    """分析历史合约数据结构"""
    print("\n=== 历史合约数据结构分析 ===")
    
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
                    for instrument in instruments:
                        if isinstance(instrument, dict):
                            for field in instrument.keys():
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
        print(f"发现的历史合约字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的历史合约字段")
    
    print(f"\n总历史合约数量: {total_instruments}")
    
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
                'api_function': 'gm.get_history_instruments()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_history_instruments function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平历史合约数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'instruments' in data:
                    # 这是一个包含instruments的结果
                    base_info = {k: v for k, v in data.items() if k != 'instruments'}
                    instruments = data['instruments']
                    
                    if isinstance(instruments, list):
                        for i, instrument in enumerate(instruments):
                            flat_result = base_info.copy()
                            flat_result['instrument_index'] = i
                            if isinstance(instrument, dict):
                                for key, value in instrument.items():
                                    flat_result[f'instrument_{key}'] = value
                            flattened_results.append(flat_result)
                    elif instruments:
                        flat_result = base_info.copy()
                        if isinstance(instruments, dict):
                            for key, value in instruments.items():
                                flat_result[f'instrument_{key}'] = value
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
    print("GM API get_history_instruments() 功能测试")
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
        
        # 测试1: 按交易所查询历史合约信息
        exchange_results = test_get_history_instruments_by_exchange()
        save_results(exchange_results, 'get_history_instruments_exchange')
        all_results.append(exchange_results)
        
        # 测试2: 按证券类型查询历史合约信息
        sec_type_results = test_get_history_instruments_by_sec_type()
        save_results(sec_type_results, 'get_history_instruments_sec_type')
        all_results.append(sec_type_results)
        
        # 测试3: 按不同日期范围查询历史合约信息
        date_range_results = test_get_history_instruments_by_date_range()
        save_results(date_range_results, 'get_history_instruments_date_range')
        all_results.append(date_range_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_history_instruments_edge_cases()
        save_results(edge_results, 'get_history_instruments_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_history_instruments_data(all_results)
        
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
        print(f"交易所查询测试: {exchange_success}/{exchange_total} 成功, {exchange_data} 个历史合约")
        
        sec_type_success, sec_type_total, sec_type_data = count_success_and_data(sec_type_results)
        print(f"证券类型测试: {sec_type_success}/{sec_type_total} 成功, {sec_type_data} 个历史合约")
        
        date_range_success, date_range_total, date_range_data = count_success_and_data(date_range_results)
        print(f"日期范围测试: {date_range_success}/{date_range_total} 成功, {date_range_data} 个历史合约")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 个历史合约")
        
        # 总体统计
        total_tests = exchange_total + sec_type_total + date_range_total + edge_total
        total_success = exchange_success + sec_type_success + date_range_success + edge_success
        total_data_count = exchange_data + sec_type_data + date_range_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总历史合约数量: {total_data_count}")
        
        # 数据结构统计
        print(f"\n历史合约数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_history_instruments() API测试完成！")

if __name__ == "__main__":
    main()