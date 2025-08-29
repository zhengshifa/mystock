#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: current_l2() Level 2实时行情查询
功能：测试 gm.current_l2() API的各种用法
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

def l2_data_to_dict(l2_data):
    """将L2数据转换为字典格式"""
    if l2_data is None:
        return None
    
    try:
        # 如果l2_data是列表或可迭代对象
        if hasattr(l2_data, '__iter__') and not isinstance(l2_data, str):
            l2_list = []
            for item in l2_data:
                item_dict = {}
                
                # 常见的L2数据属性
                attributes = [
                    'symbol', 'created_at', 'price', 'volume', 'amount',
                    'pre_close', 'open', 'high', 'low', 'last_price',
                    'bid_p', 'bid_v', 'ask_p', 'ask_v',
                    'bid_p1', 'bid_v1', 'ask_p1', 'ask_v1',
                    'bid_p2', 'bid_v2', 'ask_p2', 'ask_v2',
                    'bid_p3', 'bid_v3', 'ask_p3', 'ask_v3',
                    'bid_p4', 'bid_v4', 'ask_p4', 'ask_v4',
                    'bid_p5', 'bid_v5', 'ask_p5', 'ask_v5',
                    'bid_p6', 'bid_v6', 'ask_p6', 'ask_v6',
                    'bid_p7', 'bid_v7', 'ask_p7', 'ask_v7',
                    'bid_p8', 'bid_v8', 'ask_p8', 'ask_v8',
                    'bid_p9', 'bid_v9', 'ask_p9', 'ask_v9',
                    'bid_p10', 'bid_v10', 'ask_p10', 'ask_v10',
                    'cum_volume', 'cum_amount', 'cum_position',
                    'last_amount', 'last_volume', 'trade_type'
                ]
                
                for attr in attributes:
                    if hasattr(item, attr):
                        value = getattr(item, attr)
                        # 处理时间戳
                        if attr == 'created_at' and value:
                            try:
                                item_dict[attr] = value.strftime('%Y-%m-%d %H:%M:%S.%f')
                            except:
                                item_dict[attr] = str(value)
                        else:
                            item_dict[attr] = value
                
                # 如果没有提取到任何属性，尝试直接转换
                if not item_dict:
                    item_dict = {'raw_data': str(item)}
                
                l2_list.append(item_dict)
            
            return l2_list
        
        else:
            # 单个L2数据对象
            l2_dict = {}
            
            attributes = [
                'symbol', 'created_at', 'price', 'volume', 'amount',
                'pre_close', 'open', 'high', 'low', 'last_price',
                'bid_p', 'bid_v', 'ask_p', 'ask_v',
                'bid_p1', 'bid_v1', 'ask_p1', 'ask_v1',
                'bid_p2', 'bid_v2', 'ask_p2', 'ask_v2',
                'bid_p3', 'bid_v3', 'ask_p3', 'ask_v3',
                'bid_p4', 'bid_v4', 'ask_p4', 'ask_v4',
                'bid_p5', 'bid_v5', 'ask_p5', 'ask_v5',
                'bid_p6', 'bid_v6', 'ask_p6', 'ask_v6',
                'bid_p7', 'bid_v7', 'ask_p7', 'ask_v7',
                'bid_p8', 'bid_v8', 'ask_p8', 'ask_v8',
                'bid_p9', 'bid_v9', 'ask_p9', 'ask_v9',
                'bid_p10', 'bid_v10', 'ask_p10', 'ask_v10',
                'cum_volume', 'cum_amount', 'cum_position',
                'last_amount', 'last_volume', 'trade_type'
            ]
            
            for attr in attributes:
                if hasattr(l2_data, attr):
                    value = getattr(l2_data, attr)
                    # 处理时间戳
                    if attr == 'created_at' and value:
                        try:
                            l2_dict[attr] = value.strftime('%Y-%m-%d %H:%M:%S.%f')
                        except:
                            l2_dict[attr] = str(value)
                    else:
                        l2_dict[attr] = value
            
            # 如果没有提取到任何属性，尝试直接转换
            if not l2_dict:
                l2_dict = {'raw_data': str(l2_data)}
            
            return l2_dict
        
    except Exception as e:
        return {'error': f'Failed to convert L2 data: {e}', 'raw_data': str(l2_data)}

def test_current_l2_single():
    """测试单个股票的L2实时行情"""
    print("\n=== 测试单个股票L2实时行情 ===")
    
    test_symbols = [
        'SZSE.000001',  # 平安银行
        'SHSE.600000',  # 浦发银行
        'SZSE.000002',  # 万科A
        'SHSE.600036',  # 招商银行
        'SHSE.600519'   # 贵州茅台
    ]
    
    results = []
    
    for symbol in test_symbols:
        try:
            print(f"\n查询 {symbol} 的L2实时行情...")
            
            # 获取L2实时行情
            l2_data = gm.current_l2(symbol)
            
            if l2_data is not None:
                l2_dict = l2_data_to_dict(l2_data)
                
                result = {
                    'symbol': symbol,
                    'l2_data': l2_dict,
                    'data_count': len(l2_dict) if isinstance(l2_dict, list) else (1 if l2_dict else 0),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                # 显示关键信息
                if isinstance(l2_dict, list) and l2_dict:
                    first_item = l2_dict[0]
                    print(f"  数据条数: {len(l2_dict)}")
                    print(f"  最新价格: {first_item.get('price', 'N/A')}")
                    print(f"  买一价: {first_item.get('bid_p1', 'N/A')}")
                    print(f"  卖一价: {first_item.get('ask_p1', 'N/A')}")
                elif isinstance(l2_dict, dict):
                    print(f"  数据字段数: {len(l2_dict)}")
                    print(f"  最新价格: {l2_dict.get('price', 'N/A')}")
                    print(f"  买一价: {l2_dict.get('bid_p1', 'N/A')}")
                    print(f"  卖一价: {l2_dict.get('ask_p1', 'N/A')}")
            else:
                result = {
                    'symbol': symbol,
                    'l2_data': None,
                    'data_count': 0,
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
                'l2_data': None,
                'data_count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_current_l2_multiple():
    """测试多个股票的L2实时行情"""
    print("\n=== 测试多个股票L2实时行情 ===")
    
    symbols = [
        'SZSE.000001',  # 平安银行
        'SHSE.600000',  # 浦发银行
        'SZSE.000002',  # 万科A
        'SHSE.600036',  # 招商银行
        'SHSE.600519',  # 贵州茅台
        'SZSE.300015',  # 爱尔眼科
        'SHSE.688001'   # 华兴源创
    ]
    
    results = []
    
    print(f"\n批量查询 {len(symbols)} 个股票的L2实时行情...")
    
    for symbol in symbols:
        try:
            l2_data = gm.current_l2(symbol)
            
            if l2_data is not None:
                l2_dict = l2_data_to_dict(l2_data)
                
                result = {
                    'symbol': symbol,
                    'l2_data': l2_dict,
                    'data_count': len(l2_dict) if isinstance(l2_dict, list) else (1 if l2_dict else 0),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                # 显示简要信息
                if isinstance(l2_dict, list) and l2_dict:
                    price = l2_dict[0].get('price', 'N/A')
                    print(f"  {symbol}: {len(l2_dict)}条数据, 价格={price}")
                elif isinstance(l2_dict, dict):
                    price = l2_dict.get('price', 'N/A')
                    print(f"  {symbol}: 1条数据, 价格={price}")
                else:
                    print(f"  {symbol}: 数据格式异常")
                
            else:
                result = {
                    'symbol': symbol,
                    'l2_data': None,
                    'data_count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  {symbol}: 无数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  {symbol}: 查询失败 - {e}")
            results.append({
                'symbol': symbol,
                'l2_data': None,
                'data_count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_current_l2_different_markets():
    """测试不同市场的L2实时行情"""
    print("\n=== 测试不同市场L2实时行情 ===")
    
    market_symbols = {
        '沪市主板': ['SHSE.600000', 'SHSE.600036', 'SHSE.600519'],
        '深市主板': ['SZSE.000001', 'SZSE.000002', 'SZSE.000858'],
        '创业板': ['SZSE.300001', 'SZSE.300015', 'SZSE.300059'],
        '科创板': ['SHSE.688001', 'SHSE.688009', 'SHSE.688036']
    }
    
    all_results = {}
    
    for market_name, symbols in market_symbols.items():
        print(f"\n测试 {market_name}:")
        market_results = []
        
        for symbol in symbols:
            try:
                l2_data = gm.current_l2(symbol)
                
                if l2_data is not None:
                    l2_dict = l2_data_to_dict(l2_data)
                    
                    result = {
                        'symbol': symbol,
                        'l2_data': l2_dict,
                        'data_count': len(l2_dict) if isinstance(l2_dict, list) else (1 if l2_dict else 0),
                        'timestamp': datetime.now().isoformat(),
                        'success': True,
                        'error': None
                    }
                    
                    # 显示关键信息
                    if isinstance(l2_dict, list) and l2_dict:
                        price = l2_dict[0].get('price', 'N/A')
                        print(f"  {symbol}: {len(l2_dict)}条, 价格={price}")
                    elif isinstance(l2_dict, dict):
                        price = l2_dict.get('price', 'N/A')
                        print(f"  {symbol}: 价格={price}")
                    else:
                        print(f"  {symbol}: 数据异常")
                    
                else:
                    result = {
                        'symbol': symbol,
                        'l2_data': None,
                        'data_count': 0,
                        'timestamp': datetime.now().isoformat(),
                        'success': False,
                        'error': 'No data returned'
                    }
                    print(f"  {symbol}: 无数据")
                
                market_results.append(result)
                
            except Exception as e:
                print(f"  {symbol}: 查询失败 - {e}")
                market_results.append({
                    'symbol': symbol,
                    'l2_data': None,
                    'data_count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
        
        all_results[market_name] = market_results
    
    return all_results

def test_current_l2_monitoring():
    """测试L2行情监控（连续获取）"""
    print("\n=== 测试L2行情监控 ===")
    
    symbol = 'SZSE.000001'  # 平安银行
    monitoring_duration = 30  # 监控30秒
    interval = 5  # 每5秒获取一次
    
    print(f"监控 {symbol} 的L2行情变化，持续 {monitoring_duration} 秒，每 {interval} 秒获取一次")
    
    results = []
    start_time = time.time()
    
    while time.time() - start_time < monitoring_duration:
        try:
            current_time = datetime.now()
            l2_data = gm.current_l2(symbol)
            
            if l2_data is not None:
                l2_dict = l2_data_to_dict(l2_data)
                
                result = {
                    'symbol': symbol,
                    'l2_data': l2_dict,
                    'data_count': len(l2_dict) if isinstance(l2_dict, list) else (1 if l2_dict else 0),
                    'timestamp': current_time.isoformat(),
                    'elapsed_seconds': round(time.time() - start_time, 1),
                    'success': True,
                    'error': None
                }
                
                # 显示关键信息
                if isinstance(l2_dict, list) and l2_dict:
                    price = l2_dict[0].get('price', 'N/A')
                    bid1 = l2_dict[0].get('bid_p1', 'N/A')
                    ask1 = l2_dict[0].get('ask_p1', 'N/A')
                    print(f"  {current_time.strftime('%H:%M:%S')} - 价格: {price}, 买一: {bid1}, 卖一: {ask1}")
                elif isinstance(l2_dict, dict):
                    price = l2_dict.get('price', 'N/A')
                    bid1 = l2_dict.get('bid_p1', 'N/A')
                    ask1 = l2_dict.get('ask_p1', 'N/A')
                    print(f"  {current_time.strftime('%H:%M:%S')} - 价格: {price}, 买一: {bid1}, 卖一: {ask1}")
                else:
                    print(f"  {current_time.strftime('%H:%M:%S')} - 数据格式异常")
                
            else:
                result = {
                    'symbol': symbol,
                    'l2_data': None,
                    'data_count': 0,
                    'timestamp': current_time.isoformat(),
                    'elapsed_seconds': round(time.time() - start_time, 1),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  {current_time.strftime('%H:%M:%S')} - 无数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  {datetime.now().strftime('%H:%M:%S')} - 查询失败: {e}")
            results.append({
                'symbol': symbol,
                'l2_data': None,
                'data_count': 0,
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': round(time.time() - start_time, 1),
                'success': False,
                'error': str(e)
            })
        
        time.sleep(interval)
    
    return results

def analyze_l2_data_structure(results):
    """分析L2数据结构"""
    print("\n=== L2数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_data_count = 0
    
    # 收集所有字段
    for result in results:
        if result['success'] and result['l2_data']:
            total_data_count += result['data_count']
            
            l2_data = result['l2_data']
            if isinstance(l2_data, list):
                for item in l2_data:
                    if isinstance(item, dict):
                        for field in item.keys():
                            all_fields.add(field)
                            field_counts[field] = field_counts.get(field, 0) + 1
            elif isinstance(l2_data, dict):
                for field in l2_data.keys():
                    all_fields.add(field)
                    field_counts[field] = field_counts.get(field, 0) + 1
    
    if all_fields:
        print(f"发现的L2数据字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的L2数据字段")
    
    print(f"\n总数据条数: {total_data_count}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_data_count': total_data_count
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.current_l2()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API current_l2 function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平L2数据）
    try:
        flattened_results = []
        
        if isinstance(results, list):
            for result in results:
                base_info = {
                    'symbol': result.get('symbol'),
                    'timestamp': result.get('timestamp'),
                    'success': result.get('success'),
                    'data_count': result.get('data_count', 0),
                    'error': result.get('error')
                }
                
                # 展平L2数据
                if result.get('l2_data'):
                    l2_data = result['l2_data']
                    if isinstance(l2_data, list):
                        for i, item in enumerate(l2_data):
                            flat_result = base_info.copy()
                            flat_result['data_index'] = i
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    flat_result[f'l2_{key}'] = value
                            flattened_results.append(flat_result)
                    elif isinstance(l2_data, dict):
                        flat_result = base_info.copy()
                        for key, value in l2_data.items():
                            flat_result[f'l2_{key}'] = value
                        flattened_results.append(flat_result)
                else:
                    flattened_results.append(base_info)
        
        elif isinstance(results, dict):
            for market, market_results in results.items():
                for result in market_results:
                    base_info = {
                        'market': market,
                        'symbol': result.get('symbol'),
                        'timestamp': result.get('timestamp'),
                        'success': result.get('success'),
                        'data_count': result.get('data_count', 0),
                        'error': result.get('error')
                    }
                    
                    # 展平L2数据
                    if result.get('l2_data'):
                        l2_data = result['l2_data']
                        if isinstance(l2_data, list):
                            for i, item in enumerate(l2_data):
                                flat_result = base_info.copy()
                                flat_result['data_index'] = i
                                if isinstance(item, dict):
                                    for key, value in item.items():
                                        flat_result[f'l2_{key}'] = value
                                flattened_results.append(flat_result)
                        elif isinstance(l2_data, dict):
                            flat_result = base_info.copy()
                            for key, value in l2_data.items():
                                flat_result[f'l2_{key}'] = value
                            flattened_results.append(flat_result)
                    else:
                        flattened_results.append(base_info)
        
        if flattened_results:
            csv_filename = f"{filename_prefix}_results_{timestamp}.csv"
            df = pd.DataFrame(flattened_results)
            df.to_csv(csv_filename, encoding='utf-8-sig', index=False)
            print(f"结果已保存到: {csv_filename}")
            
    except Exception as e:
        print(f"保存CSV文件失败: {e}")

def main():
    """主函数"""
    print("GM API current_l2() 功能测试")
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
        # 测试1: 单个股票L2实时行情
        single_results = test_current_l2_single()
        save_results(single_results, 'current_l2_single')
        
        # 测试2: 多个股票L2实时行情
        multiple_results = test_current_l2_multiple()
        save_results(multiple_results, 'current_l2_multiple')
        
        # 测试3: 不同市场L2实时行情
        market_results = test_current_l2_different_markets()
        save_results(market_results, 'current_l2_markets')
        
        # 测试4: L2行情监控
        print("\n即将开始L2行情监控测试...")
        monitoring_results = test_current_l2_monitoring()
        save_results(monitoring_results, 'current_l2_monitoring')
        
        # 分析L2数据结构
        all_results = single_results + multiple_results
        for market_results_list in market_results.values():
            all_results.extend(market_results_list)
        all_results.extend(monitoring_results)
        
        structure_analysis = analyze_l2_data_structure(all_results)
        
        # 汇总统计
        print("\n=== 测试汇总 ===")
        
        # 统计各测试结果
        single_success = sum(1 for r in single_results if r['success'])
        single_data_count = sum(r['data_count'] for r in single_results)
        print(f"单个股票测试: {single_success}/{len(single_results)} 成功, {single_data_count} 条数据")
        
        multiple_success = sum(1 for r in multiple_results if r['success'])
        multiple_data_count = sum(r['data_count'] for r in multiple_results)
        print(f"多个股票测试: {multiple_success}/{len(multiple_results)} 成功, {multiple_data_count} 条数据")
        
        market_total = sum(len(results) for results in market_results.values())
        market_success = sum(sum(1 for r in results if r['success']) for results in market_results.values())
        market_data_count = sum(sum(r['data_count'] for r in results) for results in market_results.values())
        print(f"不同市场测试: {market_success}/{market_total} 成功, {market_data_count} 条数据")
        
        monitoring_success = sum(1 for r in monitoring_results if r['success'])
        monitoring_data_count = sum(r['data_count'] for r in monitoring_results)
        print(f"L2监控测试: {monitoring_success}/{len(monitoring_results)} 成功, {monitoring_data_count} 条数据")
        
        # 总体统计
        total_tests = len(single_results) + len(multiple_results) + market_total + len(monitoring_results)
        total_success = single_success + multiple_success + market_success + monitoring_success
        total_data_count = single_data_count + multiple_data_count + market_data_count + monitoring_data_count
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总数据条数: {total_data_count}")
        
        # 数据结构统计
        print(f"\nL2数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\ncurrent_l2() API测试完成！")

if __name__ == "__main__":
    main()