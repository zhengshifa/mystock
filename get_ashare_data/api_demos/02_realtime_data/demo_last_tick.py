#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: last_tick() 最新tick数据查询
功能：测试 gm.last_tick() API的各种用法
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

def tick_to_dict(tick_data):
    """将tick数据转换为字典格式"""
    if tick_data is None:
        return None
    
    try:
        # 如果tick_data有属性，提取所有属性
        tick_dict = {}
        
        # 常见的tick数据属性
        attributes = [
            'symbol', 'created_at', 'price', 'volume', 'amount',
            'pre_close', 'open', 'high', 'low', 'last_price',
            'bid_p', 'bid_v', 'ask_p', 'ask_v',
            'bid_p1', 'bid_v1', 'ask_p1', 'ask_v1',
            'bid_p2', 'bid_v2', 'ask_p2', 'ask_v2',
            'bid_p3', 'bid_v3', 'ask_p3', 'ask_v3',
            'bid_p4', 'bid_v4', 'ask_p4', 'ask_v4',
            'bid_p5', 'bid_v5', 'ask_p5', 'ask_v5',
            'cum_volume', 'cum_amount', 'cum_position',
            'last_amount', 'last_volume', 'trade_type'
        ]
        
        for attr in attributes:
            if hasattr(tick_data, attr):
                value = getattr(tick_data, attr)
                # 处理时间戳
                if attr == 'created_at' and value:
                    try:
                        tick_dict[attr] = value.strftime('%Y-%m-%d %H:%M:%S.%f')
                    except:
                        tick_dict[attr] = str(value)
                else:
                    tick_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not tick_dict:
            tick_dict = {'raw_data': str(tick_data)}
        
        return tick_dict
        
    except Exception as e:
        return {'error': f'Failed to convert tick data: {e}', 'raw_data': str(tick_data)}

def test_last_tick_single():
    """测试单个股票的最新tick数据"""
    print("\n=== 测试单个股票最新tick数据 ===")
    
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
            print(f"\n查询 {symbol} 的最新tick数据...")
            
            # 获取最新tick数据
            tick_data = gm.last_tick(symbol)
            
            if tick_data is not None:
                tick_dict = tick_to_dict(tick_data)
                
                result = {
                    'symbol': symbol,
                    'tick_data': tick_dict,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                # 显示关键信息
                if tick_dict and 'price' in tick_dict:
                    print(f"  最新价格: {tick_dict.get('price', 'N/A')}")
                if tick_dict and 'volume' in tick_dict:
                    print(f"  成交量: {tick_dict.get('volume', 'N/A')}")
                if tick_dict and 'created_at' in tick_dict:
                    print(f"  时间: {tick_dict.get('created_at', 'N/A')}")
                
                print(f"  数据字段数: {len(tick_dict) if tick_dict else 0}")
            else:
                result = {
                    'symbol': symbol,
                    'tick_data': None,
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
                'tick_data': None,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_last_tick_multiple():
    """测试多个股票的最新tick数据"""
    print("\n=== 测试多个股票最新tick数据 ===")
    
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
    
    print(f"\n批量查询 {len(symbols)} 个股票的最新tick数据...")
    
    for symbol in symbols:
        try:
            tick_data = gm.last_tick(symbol)
            
            if tick_data is not None:
                tick_dict = tick_to_dict(tick_data)
                
                result = {
                    'symbol': symbol,
                    'tick_data': tick_dict,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                # 显示简要信息
                price = tick_dict.get('price', 'N/A') if tick_dict else 'N/A'
                volume = tick_dict.get('volume', 'N/A') if tick_dict else 'N/A'
                print(f"  {symbol}: 价格={price}, 量={volume}")
                
            else:
                result = {
                    'symbol': symbol,
                    'tick_data': None,
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
                'tick_data': None,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_last_tick_different_markets():
    """测试不同市场的最新tick数据"""
    print("\n=== 测试不同市场最新tick数据 ===")
    
    market_symbols = {
        '沪市主板': ['SHSE.600000', 'SHSE.600036', 'SHSE.600519'],
        '深市主板': ['SZSE.000001', 'SZSE.000002', 'SZSE.000858'],
        '创业板': ['SZSE.300001', 'SZSE.300015', 'SZSE.300059'],
        '科创板': ['SHSE.688001', 'SHSE.688009', 'SHSE.688036'],
        '指数': ['SHSE.000001', 'SZSE.399001', 'SZSE.399006']
    }
    
    all_results = {}
    
    for market_name, symbols in market_symbols.items():
        print(f"\n测试 {market_name}:")
        market_results = []
        
        for symbol in symbols:
            try:
                tick_data = gm.last_tick(symbol)
                
                if tick_data is not None:
                    tick_dict = tick_to_dict(tick_data)
                    
                    result = {
                        'symbol': symbol,
                        'tick_data': tick_dict,
                        'timestamp': datetime.now().isoformat(),
                        'success': True,
                        'error': None
                    }
                    
                    # 显示关键信息
                    price = tick_dict.get('price', 'N/A') if tick_dict else 'N/A'
                    print(f"  {symbol}: {price}")
                    
                else:
                    result = {
                        'symbol': symbol,
                        'tick_data': None,
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
                    'tick_data': None,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
        
        all_results[market_name] = market_results
    
    return all_results

def test_last_tick_monitoring():
    """测试tick数据监控（连续获取）"""
    print("\n=== 测试tick数据监控 ===")
    
    symbol = 'SZSE.000001'  # 平安银行
    monitoring_duration = 30  # 监控30秒
    interval = 3  # 每3秒获取一次
    
    print(f"监控 {symbol} 的tick数据变化，持续 {monitoring_duration} 秒，每 {interval} 秒获取一次")
    
    results = []
    start_time = time.time()
    
    while time.time() - start_time < monitoring_duration:
        try:
            current_time = datetime.now()
            tick_data = gm.last_tick(symbol)
            
            if tick_data is not None:
                tick_dict = tick_to_dict(tick_data)
                
                result = {
                    'symbol': symbol,
                    'tick_data': tick_dict,
                    'timestamp': current_time.isoformat(),
                    'elapsed_seconds': round(time.time() - start_time, 1),
                    'success': True,
                    'error': None
                }
                
                # 显示关键信息
                price = tick_dict.get('price', 'N/A') if tick_dict else 'N/A'
                volume = tick_dict.get('volume', 'N/A') if tick_dict else 'N/A'
                tick_time = tick_dict.get('created_at', 'N/A') if tick_dict else 'N/A'
                
                print(f"  {current_time.strftime('%H:%M:%S')} - 价格: {price}, 量: {volume}, tick时间: {tick_time}")
                
            else:
                result = {
                    'symbol': symbol,
                    'tick_data': None,
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
                'tick_data': None,
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': round(time.time() - start_time, 1),
                'success': False,
                'error': str(e)
            })
        
        time.sleep(interval)
    
    return results

def analyze_tick_data_structure(results):
    """分析tick数据结构"""
    print("\n=== Tick数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    
    # 收集所有字段
    for result in results:
        if result['success'] and result['tick_data']:
            tick_data = result['tick_data']
            for field in tick_data.keys():
                all_fields.add(field)
                field_counts[field] = field_counts.get(field, 0) + 1
    
    if all_fields:
        print(f"发现的tick数据字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            percentage = count / len([r for r in results if r['success']]) * 100
            print(f"  {field}: 出现在 {count} 个结果中 ({percentage:.1f}%)")
    else:
        print("未发现有效的tick数据字段")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.last_tick()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API last_tick function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平tick数据）
    try:
        flattened_results = []
        
        if isinstance(results, list):
            for result in results:
                flat_result = {
                    'symbol': result.get('symbol'),
                    'timestamp': result.get('timestamp'),
                    'success': result.get('success'),
                    'error': result.get('error')
                }
                
                # 展平tick数据
                if result.get('tick_data'):
                    for key, value in result['tick_data'].items():
                        flat_result[f'tick_{key}'] = value
                
                flattened_results.append(flat_result)
        
        elif isinstance(results, dict):
            for market, market_results in results.items():
                for result in market_results:
                    flat_result = {
                        'market': market,
                        'symbol': result.get('symbol'),
                        'timestamp': result.get('timestamp'),
                        'success': result.get('success'),
                        'error': result.get('error')
                    }
                    
                    # 展平tick数据
                    if result.get('tick_data'):
                        for key, value in result['tick_data'].items():
                            flat_result[f'tick_{key}'] = value
                    
                    flattened_results.append(flat_result)
        
        if flattened_results:
            csv_filename = f"{filename_prefix}_results_{timestamp}.csv"
            df = pd.DataFrame(flattened_results)
            df.to_csv(csv_filename, encoding='utf-8-sig', index=False)
            print(f"结果已保存到: {csv_filename}")
            
    except Exception as e:
        print(f"保存CSV文件失败: {e}")

def main():
    """主函数"""
    print("GM API last_tick() 功能测试")
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
        # 测试1: 单个股票最新tick数据
        single_results = test_last_tick_single()
        save_results(single_results, 'last_tick_single')
        
        # 测试2: 多个股票最新tick数据
        multiple_results = test_last_tick_multiple()
        save_results(multiple_results, 'last_tick_multiple')
        
        # 测试3: 不同市场最新tick数据
        market_results = test_last_tick_different_markets()
        save_results(market_results, 'last_tick_markets')
        
        # 测试4: tick数据监控
        print("\n即将开始tick数据监控测试...")
        monitoring_results = test_last_tick_monitoring()
        save_results(monitoring_results, 'last_tick_monitoring')
        
        # 分析tick数据结构
        all_results = single_results + multiple_results
        for market_results_list in market_results.values():
            all_results.extend(market_results_list)
        all_results.extend(monitoring_results)
        
        structure_analysis = analyze_tick_data_structure(all_results)
        
        # 汇总统计
        print("\n=== 测试汇总 ===")
        
        # 统计各测试结果
        single_success = sum(1 for r in single_results if r['success'])
        print(f"单个股票测试: {single_success}/{len(single_results)} 成功")
        
        multiple_success = sum(1 for r in multiple_results if r['success'])
        print(f"多个股票测试: {multiple_success}/{len(multiple_results)} 成功")
        
        market_total = sum(len(results) for results in market_results.values())
        market_success = sum(sum(1 for r in results if r['success']) for results in market_results.values())
        print(f"不同市场测试: {market_success}/{market_total} 成功")
        
        monitoring_success = sum(1 for r in monitoring_results if r['success'])
        print(f"tick监控测试: {monitoring_success}/{len(monitoring_results)} 成功")
        
        # 总体统计
        total_tests = len(single_results) + len(multiple_results) + market_total + len(monitoring_results)
        total_success = single_success + multiple_success + market_success + monitoring_success
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        
        # 数据结构统计
        print(f"\nTick数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nlast_tick() API测试完成！")

if __name__ == "__main__":
    main()