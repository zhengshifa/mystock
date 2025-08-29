#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_history_symbol_infos() 获取历史股票信息
功能：测试 gm.get_history_symbol_infos() API的各种用法
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
            'price_tick', 'upper_limit', 'lower_limit',
            'pre_close', 'pre_settle', 'margin_ratio',
            'contract_month', 'exercise_type', 'exercise_price',
            'underlying_symbol', 'option_type', 'delivery_month',
            'created_at', 'updated_at', 'currency', 'lot_size',
            'board_type', 'status', 'suspend_type', 'suspend_date',
            'resume_date', 'change_reason', 'change_date'
        ]
        
        for attr in attributes:
            if hasattr(symbol_info, attr):
                value = getattr(symbol_info, attr)
                # 处理日期时间类型
                if attr in ['list_date', 'delist_date', 'created_at', 'updated_at', 'suspend_date', 'resume_date', 'change_date'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            info_dict[attr] = value.strftime('%Y-%m-%d')
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

def test_get_history_symbol_infos_single():
    """测试单个股票的历史信息查询"""
    print("\n=== 测试单个股票的历史信息查询 ===")
    
    # 测试不同类型的股票
    test_symbols = [
        {'symbol': 'SHSE.000001', 'name': '上证指数'},
        {'symbol': 'SHSE.600000', 'name': '浦发银行'},
        {'symbol': 'SHSE.600036', 'name': '招商银行'},
        {'symbol': 'SZSE.000001', 'name': '平安银行'},
        {'symbol': 'SZSE.000002', 'name': '万科A'},
        {'symbol': 'SZSE.399001', 'name': '深证成指'}
    ]
    
    results = []
    
    # 查询最近一年的历史信息
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for symbol_info in test_symbols:
        try:
            print(f"\n查询 {symbol_info['name']} ({symbol_info['symbol']}) 的历史信息...")
            
            # 获取历史股票信息
            history_infos = gm.get_history_symbol_infos(
                symbols=symbol_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if history_infos is not None:
                # 转换为字典列表
                infos_list = []
                if hasattr(history_infos, '__iter__') and not isinstance(history_infos, str):
                    for info in history_infos:
                        info_dict = symbol_info_to_dict(info)
                        if info_dict:
                            infos_list.append(info_dict)
                else:
                    info_dict = symbol_info_to_dict(history_infos)
                    if info_dict:
                        infos_list.append(info_dict)
                
                result = {
                    'symbol': symbol_info['symbol'],
                    'symbol_name': symbol_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'history_infos': infos_list,
                    'count': len(infos_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(infos_list)} 条历史信息记录")
                
                # 分析历史信息变化
                if infos_list:
                    # 按日期排序
                    sorted_infos = sorted(
                        [i for i in infos_list if i.get('change_date')],
                        key=lambda x: x.get('change_date', ''),
                        reverse=True
                    )
                    
                    if sorted_infos:
                        print(f"  最近的信息变更:")
                        for i, info in enumerate(sorted_infos[:3]):
                            change_date = info.get('change_date', 'N/A')
                            change_reason = info.get('change_reason', 'N/A')
                            status = info.get('status', 'N/A')
                            print(f"    {i+1}. {change_date}: {change_reason} (状态: {status})")
                    
                    # 显示当前信息
                    current_info = infos_list[0] if infos_list else {}
                    sec_name = current_info.get('sec_name', 'N/A')
                    sec_type = current_info.get('sec_type', 'N/A')
                    exchange = current_info.get('exchange', 'N/A')
                    is_active = current_info.get('is_active', 'N/A')
                    list_date = current_info.get('list_date', 'N/A')
                    
                    print(f"  当前信息: {sec_name} ({sec_type}) - {exchange} - 活跃: {is_active} - 上市: {list_date}")
                
            else:
                result = {
                    'symbol': symbol_info['symbol'],
                    'symbol_name': symbol_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'history_infos': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史信息数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': symbol_info['symbol'],
                'symbol_name': symbol_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'history_infos': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_symbol_infos_batch():
    """测试批量股票的历史信息查询"""
    print("\n=== 测试批量股票的历史信息查询 ===")
    
    # 测试不同的股票组合
    test_batches = [
        {
            'name': '银行股',
            'symbols': ['SHSE.600000', 'SHSE.600036', 'SZSE.000001', 'SHSE.601398']
        },
        {
            'name': '科技股',
            'symbols': ['SZSE.000858', 'SHSE.600519', 'SZSE.300059', 'SHSE.688981']
        },
        {
            'name': '指数',
            'symbols': ['SHSE.000001', 'SZSE.399001', 'SZSE.399006']
        },
        {
            'name': '混合类型',
            'symbols': ['SHSE.600000', 'SZSE.399001', 'SHSE.510050', 'SHSE.688001']
        }
    ]
    
    results = []
    
    # 查询最近6个月的历史信息
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for batch in test_batches:
        try:
            print(f"\n批量查询 {batch['name']} 的历史信息...")
            print(f"  股票列表: {', '.join(batch['symbols'])}")
            
            # 获取历史股票信息
            history_infos = gm.get_history_symbol_infos(
                symbols=batch['symbols'],
                start_date=start_date,
                end_date=end_date
            )
            
            if history_infos is not None:
                # 转换为字典列表
                infos_list = []
                if hasattr(history_infos, '__iter__') and not isinstance(history_infos, str):
                    for info in history_infos:
                        info_dict = symbol_info_to_dict(info)
                        if info_dict:
                            infos_list.append(info_dict)
                else:
                    info_dict = symbol_info_to_dict(history_infos)
                    if info_dict:
                        infos_list.append(info_dict)
                
                result = {
                    'batch_name': batch['name'],
                    'symbols': batch['symbols'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'history_infos': infos_list,
                    'count': len(infos_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(infos_list)} 条历史信息记录")
                
                # 按股票分组统计
                if infos_list:
                    symbol_counts = {}
                    for info in infos_list:
                        symbol = info.get('symbol', 'Unknown')
                        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
                    
                    print(f"  各股票历史记录数:")
                    for symbol, count in symbol_counts.items():
                        print(f"    {symbol}: {count} 条")
                    
                    # 分析信息变更类型
                    change_reasons = {}
                    for info in infos_list:
                        reason = info.get('change_reason', 'Unknown')
                        if reason and reason != 'N/A':
                            change_reasons[reason] = change_reasons.get(reason, 0) + 1
                    
                    if change_reasons:
                        print(f"  变更原因分布:")
                        for reason, count in change_reasons.items():
                            print(f"    {reason}: {count} 次")
                
            else:
                result = {
                    'batch_name': batch['name'],
                    'symbols': batch['symbols'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'history_infos': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史信息数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'batch_name': batch['name'],
                'symbols': batch['symbols'],
                'start_date': start_date,
                'end_date': end_date,
                'history_infos': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_symbol_infos_date_ranges():
    """测试不同日期范围的历史信息查询"""
    print("\n=== 测试不同日期范围的历史信息查询 ===")
    
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
    
    # 选择几个代表性股票进行测试
    test_symbols = ['SHSE.600000', 'SZSE.000001', 'SHSE.000001']
    
    for date_range in date_ranges:
        try:
            print(f"\n查询 {date_range['name']} ({date_range['start_date']} 到 {date_range['end_date']}) 的历史信息...")
            
            # 获取历史股票信息
            history_infos = gm.get_history_symbol_infos(
                symbols=test_symbols,
                start_date=date_range['start_date'],
                end_date=date_range['end_date']
            )
            
            if history_infos is not None:
                # 转换为字典列表
                infos_list = []
                if hasattr(history_infos, '__iter__') and not isinstance(history_infos, str):
                    for info in history_infos:
                        info_dict = symbol_info_to_dict(info)
                        if info_dict:
                            infos_list.append(info_dict)
                else:
                    info_dict = symbol_info_to_dict(history_infos)
                    if info_dict:
                        infos_list.append(info_dict)
                
                result = {
                    'date_range_name': date_range['name'],
                    'symbols': test_symbols,
                    'start_date': date_range['start_date'],
                    'end_date': date_range['end_date'],
                    'history_infos': infos_list,
                    'count': len(infos_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(infos_list)} 条历史信息记录")
                
                # 分析时间分布
                if infos_list:
                    # 统计各月份的变更数量
                    monthly_changes = {}
                    for info in infos_list:
                        change_date = info.get('change_date')
                        if change_date and change_date != 'N/A':
                            try:
                                month = change_date[:7]  # YYYY-MM
                                monthly_changes[month] = monthly_changes.get(month, 0) + 1
                            except:
                                pass
                    
                    if monthly_changes:
                        print(f"  月度变更分布:")
                        for month in sorted(monthly_changes.keys()):
                            count = monthly_changes[month]
                            print(f"    {month}: {count} 次变更")
                    
                    # 显示主要变更事件
                    important_changes = []
                    for info in infos_list:
                        change_reason = info.get('change_reason', '')
                        if change_reason and '上市' in change_reason or '退市' in change_reason or '停牌' in change_reason:
                            important_changes.append(info)
                    
                    if important_changes:
                        print(f"  重要变更事件 ({len(important_changes)} 个):")
                        for i, info in enumerate(important_changes[:5]):
                            symbol = info.get('symbol', 'N/A')
                            change_date = info.get('change_date', 'N/A')
                            change_reason = info.get('change_reason', 'N/A')
                            print(f"    {i+1}. {symbol} - {change_date}: {change_reason}")
                
            else:
                result = {
                    'date_range_name': date_range['name'],
                    'symbols': test_symbols,
                    'start_date': date_range['start_date'],
                    'end_date': date_range['end_date'],
                    'history_infos': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史信息数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'date_range_name': date_range['name'],
                'symbols': test_symbols,
                'start_date': date_range['start_date'],
                'end_date': date_range['end_date'],
                'history_infos': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_history_symbol_infos_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的股票代码',
            'symbols': ['INVALID.123456'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '空股票列表',
            'symbols': [],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '未来日期范围',
            'symbols': ['SHSE.600000'],
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'symbols': ['SHSE.600000'],
            'start_date': '1990-01-01',
            'end_date': '1990-12-31'
        },
        {
            'name': '单日查询',
            'symbols': ['SHSE.600000'],
            'start_date': '2023-06-15',
            'end_date': '2023-06-15'
        },
        {
            'name': '日期顺序颠倒',
            'symbols': ['SHSE.600000'],
            'start_date': '2023-12-31',
            'end_date': '2023-01-01'
        },
        {
            'name': '重复股票代码',
            'symbols': ['SHSE.600000', 'SHSE.600000', 'SHSE.600000'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '格式错误的股票代码',
            'symbols': ['600000', 'SHSE600000', 'SHSE.'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']}...")
            print(f"  股票代码: {test_case['symbols']}")
            
            # 获取历史股票信息
            history_infos = gm.get_history_symbol_infos(
                symbols=test_case['symbols'],
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if history_infos is not None:
                # 转换为字典列表
                infos_list = []
                if hasattr(history_infos, '__iter__') and not isinstance(history_infos, str):
                    for info in history_infos:
                        info_dict = symbol_info_to_dict(info)
                        if info_dict:
                            infos_list.append(info_dict)
                else:
                    info_dict = symbol_info_to_dict(history_infos)
                    if info_dict:
                        infos_list.append(info_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'symbols': test_case['symbols'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'history_infos': infos_list,
                    'count': len(infos_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(infos_list)} 条历史信息记录")
                
                if infos_list:
                    print(f"  前几条记录:")
                    for i, info in enumerate(infos_list[:3]):
                        symbol = info.get('symbol', 'N/A')
                        sec_name = info.get('sec_name', 'N/A')
                        change_date = info.get('change_date', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name} ({change_date})")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'symbols': test_case['symbols'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'history_infos': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无历史信息数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'symbols': test_case['symbols'],
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'history_infos': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_history_symbol_infos_data(results):
    """分析历史股票信息数据结构"""
    print("\n=== 历史股票信息数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_infos = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_infos
        
        if isinstance(data, dict):
            if 'history_infos' in data:
                infos = data['history_infos']
                if isinstance(infos, list):
                    total_infos += len(infos)
                    for info in infos:
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
        print(f"发现的历史股票信息字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的历史股票信息字段")
    
    print(f"\n总历史信息记录数: {total_infos}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_infos': total_infos
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_history_symbol_infos()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_history_symbol_infos function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平历史信息数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'history_infos' in data:
                    # 这是一个包含history_infos的结果
                    base_info = {k: v for k, v in data.items() if k != 'history_infos'}
                    infos = data['history_infos']
                    
                    if isinstance(infos, list):
                        for i, info in enumerate(infos):
                            flat_result = base_info.copy()
                            flat_result['info_index'] = i
                            if isinstance(info, dict):
                                for key, value in info.items():
                                    flat_result[f'info_{key}'] = value
                            flattened_results.append(flat_result)
                    elif infos:
                        flat_result = base_info.copy()
                        if isinstance(infos, dict):
                            for key, value in infos.items():
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
    print("GM API get_history_symbol_infos() 功能测试")
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
        
        # 测试1: 单个股票的历史信息查询
        single_results = test_get_history_symbol_infos_single()
        save_results(single_results, 'get_history_symbol_infos_single')
        all_results.append(single_results)
        
        # 测试2: 批量股票的历史信息查询
        batch_results = test_get_history_symbol_infos_batch()
        save_results(batch_results, 'get_history_symbol_infos_batch')
        all_results.append(batch_results)
        
        # 测试3: 不同日期范围的历史信息查询
        date_range_results = test_get_history_symbol_infos_date_ranges()
        save_results(date_range_results, 'get_history_symbol_infos_date_ranges')
        all_results.append(date_range_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_history_symbol_infos_edge_cases()
        save_results(edge_results, 'get_history_symbol_infos_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_history_symbol_infos_data(all_results)
        
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
        
        single_success, single_total, single_data = count_success_and_data(single_results)
        print(f"单股票查询测试: {single_success}/{single_total} 成功, {single_data} 条历史信息")
        
        batch_success, batch_total, batch_data = count_success_and_data(batch_results)
        print(f"批量查询测试: {batch_success}/{batch_total} 成功, {batch_data} 条历史信息")
        
        date_range_success, date_range_total, date_range_data = count_success_and_data(date_range_results)
        print(f"日期范围测试: {date_range_success}/{date_range_total} 成功, {date_range_data} 条历史信息")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 条历史信息")
        
        # 总体统计
        total_tests = single_total + batch_total + date_range_total + edge_total
        total_success = single_success + batch_success + date_range_success + edge_success
        total_data_count = single_data + batch_data + date_range_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总历史信息记录数: {total_data_count}")
        
        # 数据结构统计
        print(f"\n历史股票信息数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_history_symbol_infos() API测试完成！")

if __name__ == "__main__":
    main()