#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: get_unsubscribed_symbols
获取已取消订阅的股票代码列表

功能说明:
- 获取当前已取消订阅的股票代码
- 支持按数据类型筛选
- 提供订阅状态管理和历史记录功能
"""

import gm
from gm.api import *
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

# 配置信息
CONFIG_FILE = 'gm_config.json'
OUTPUT_DIR = 'output/unsubscribed_symbols_data'

# 全局变量用于模拟订阅管理
subscription_tracker = {
    'subscribed': {},  # {symbol: {data_types: set, subscribe_time: datetime}}
    'unsubscribed': {},  # {symbol: {data_types: set, unsubscribe_time: datetime}}
    'history': []  # 订阅历史记录
}

def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件 {CONFIG_FILE} 不存在")
        return None
    except json.JSONDecodeError:
        print(f"配置文件 {CONFIG_FILE} 格式错误")
        return None

def init_gm_api():
    """初始化GM API"""
    config = load_config()
    if not config:
        return False
    
    try:
        # 设置token
        set_token(config['token'])
        print(f"GM API初始化成功，Token: {config['token'][:10]}...")
        return True
    except Exception as e:
        print(f"GM API初始化失败: {e}")
        return False

def track_subscription(symbol, data_type, action='subscribe'):
    """跟踪订阅状态"""
    global subscription_tracker
    
    current_time = datetime.now()
    
    if action == 'subscribe':
        if symbol not in subscription_tracker['subscribed']:
            subscription_tracker['subscribed'][symbol] = {
                'data_types': set(),
                'subscribe_time': current_time
            }
        subscription_tracker['subscribed'][symbol]['data_types'].add(data_type)
        
        # 从已取消订阅中移除（如果存在）
        if symbol in subscription_tracker['unsubscribed']:
            subscription_tracker['unsubscribed'][symbol]['data_types'].discard(data_type)
            if not subscription_tracker['unsubscribed'][symbol]['data_types']:
                del subscription_tracker['unsubscribed'][symbol]
    
    elif action == 'unsubscribe':
        if symbol not in subscription_tracker['unsubscribed']:
            subscription_tracker['unsubscribed'][symbol] = {
                'data_types': set(),
                'unsubscribe_time': current_time
            }
        subscription_tracker['unsubscribed'][symbol]['data_types'].add(data_type)
        
        # 从已订阅中移除
        if symbol in subscription_tracker['subscribed']:
            subscription_tracker['subscribed'][symbol]['data_types'].discard(data_type)
            if not subscription_tracker['subscribed'][symbol]['data_types']:
                del subscription_tracker['subscribed'][symbol]
    
    # 记录历史
    subscription_tracker['history'].append({
        'symbol': symbol,
        'data_type': data_type,
        'action': action,
        'timestamp': current_time.isoformat()
    })

def get_mock_unsubscribed_symbols(data_type=None):
    """模拟获取已取消订阅的股票代码（因为实际API可能需要特定环境）"""
    global subscription_tracker
    
    unsubscribed_symbols = []
    
    for symbol, info in subscription_tracker['unsubscribed'].items():
        if data_type is None:
            # 返回所有已取消订阅的股票
            unsubscribed_symbols.append({
                'symbol': symbol,
                'data_types': list(info['data_types']),
                'unsubscribe_time': info['unsubscribe_time'].isoformat()
            })
        elif data_type in info['data_types']:
            # 返回特定数据类型的已取消订阅股票
            unsubscribed_symbols.append({
                'symbol': symbol,
                'data_type': data_type,
                'unsubscribe_time': info['unsubscribe_time'].isoformat()
            })
    
    return unsubscribed_symbols

def analyze_unsubscribed_symbols_data(unsubscribed_data):
    """分析已取消订阅的股票数据"""
    if not unsubscribed_data:
        return {
            'basic_stats': {
                'total_symbols': 0,
                'analysis_time': datetime.now().isoformat()
            }
        }
    
    analysis = {
        'basic_stats': {
            'total_symbols': len(unsubscribed_data),
            'analysis_time': datetime.now().isoformat()
        }
    }
    
    # 提取所有股票代码
    symbols = [item['symbol'] for item in unsubscribed_data]
    analysis['symbols'] = {
        'unique_symbols': list(set(symbols)),
        'unique_count': len(set(symbols))
    }
    
    # 交易所分布
    exchanges = []
    for symbol in symbols:
        if '.' in symbol:
            exchange = symbol.split('.')[0]
            exchanges.append(exchange)
    
    if exchanges:
        exchange_counts = {}
        for exchange in exchanges:
            exchange_counts[exchange] = exchange_counts.get(exchange, 0) + 1
        
        analysis['exchange_distribution'] = {
            'counts': exchange_counts,
            'total_exchanges': len(exchange_counts)
        }
    
    # 数据类型分布（如果有）
    data_types = []
    for item in unsubscribed_data:
        if 'data_type' in item:
            data_types.append(item['data_type'])
        elif 'data_types' in item:
            data_types.extend(item['data_types'])
    
    if data_types:
        data_type_counts = {}
        for dt in data_types:
            data_type_counts[dt] = data_type_counts.get(dt, 0) + 1
        
        analysis['data_type_distribution'] = {
            'counts': data_type_counts,
            'total_types': len(data_type_counts)
        }
    
    # 时间分析（如果有取消订阅时间）
    unsubscribe_times = []
    for item in unsubscribed_data:
        if 'unsubscribe_time' in item:
            try:
                unsubscribe_times.append(datetime.fromisoformat(item['unsubscribe_time']))
            except:
                pass
    
    if unsubscribe_times:
        analysis['time_analysis'] = {
            'earliest_unsubscribe': min(unsubscribe_times).isoformat(),
            'latest_unsubscribe': max(unsubscribe_times).isoformat(),
            'time_span_seconds': (max(unsubscribe_times) - min(unsubscribe_times)).total_seconds()
        }
    
    # 股票代码前缀分析
    prefixes = []
    for symbol in symbols:
        if '.' in symbol:
            code = symbol.split('.')[1]
            if len(code) >= 3:
                prefix = code[:3]
                prefixes.append(prefix)
    
    if prefixes:
        prefix_counts = {}
        for prefix in prefixes:
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
        
        analysis['code_prefix_distribution'] = {
            'counts': prefix_counts,
            'total_prefixes': len(prefix_counts)
        }
    
    return analysis

def save_unsubscribed_symbols_results(unsubscribed_data, analysis, filename_prefix):
    """保存已取消订阅股票结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据 - JSON格式
    json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(unsubscribed_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"已取消订阅股票数据已保存到: {json_file}")
    
    # 保存原始数据 - CSV格式
    if unsubscribed_data:
        try:
            df = pd.DataFrame(unsubscribed_data)
            csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"已取消订阅股票数据已保存到: {csv_file}")
        except Exception as e:
            print(f"保存CSV文件时出错: {e}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")
    
    # 保存股票代码列表 - TXT格式
    if unsubscribed_data:
        symbols = list(set([item['symbol'] for item in unsubscribed_data]))
        txt_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_symbols_{timestamp}.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            for symbol in sorted(symbols):
                f.write(f"{symbol}\n")
        print(f"股票代码列表已保存到: {txt_file}")

def dummy_callback(context, data):
    """虚拟回调函数"""
    pass

def test_get_unsubscribed_symbols():
    """测试get_unsubscribed_symbols API"""
    global subscription_tracker
    
    print("=" * 60)
    print("测试 get_unsubscribed_symbols API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '基本功能测试 - 获取所有已取消订阅股票',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600036', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe'),
                ('SHSE.600000', 'tick', 'unsubscribe'),
                ('SZSE.000001', 'bar.60s', 'unsubscribe')
            ],
            'params': {'data_type': None}
        },
        {
            'name': '按数据类型筛选 - tick数据',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600036', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe'),
                ('SHSE.600000', 'tick', 'unsubscribe'),
                ('SHSE.600036', 'bar.60s', 'subscribe'),
                ('SHSE.600036', 'bar.60s', 'unsubscribe')
            ],
            'params': {'data_type': 'tick'}
        },
        {
            'name': '按数据类型筛选 - bar数据',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe'),
                ('SZSE.000002', 'bar.300s', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'unsubscribe'),
                ('SZSE.000002', 'bar.300s', 'unsubscribe')
            ],
            'params': {'data_type': 'bar.60s'}
        },
        {
            'name': '多次订阅和取消订阅',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600000', 'tick', 'unsubscribe'),
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600000', 'bar.60s', 'subscribe'),
                ('SHSE.600000', 'tick', 'unsubscribe'),
                ('SHSE.600000', 'bar.60s', 'unsubscribe')
            ],
            'params': {'data_type': None}
        },
        {
            'name': '大量股票订阅管理',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600036', 'tick', 'subscribe'),
                ('SHSE.600519', 'tick', 'subscribe'),
                ('SZSE.000001', 'tick', 'subscribe'),
                ('SZSE.000002', 'tick', 'subscribe'),
                ('SHSE.600000', 'tick', 'unsubscribe'),
                ('SHSE.600036', 'tick', 'unsubscribe'),
                ('SZSE.000001', 'tick', 'unsubscribe')
            ],
            'params': {'data_type': 'tick'}
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '空订阅状态',
            'setup_subscriptions': [],
            'params': {'data_type': None}
        },
        {
            'name': '只有订阅没有取消订阅',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe')
            ],
            'params': {'data_type': None}
        },
        {
            'name': '查询不存在的数据类型',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600000', 'tick', 'unsubscribe')
            ],
            'params': {'data_type': 'nonexistent_type'}
        },
        {
            'name': '无效股票代码处理',
            'setup_subscriptions': [
                ('INVALID.SYMBOL', 'tick', 'subscribe'),
                ('INVALID.SYMBOL', 'tick', 'unsubscribe'),
                ('', 'tick', 'subscribe'),
                ('', 'tick', 'unsubscribe')
            ],
            'params': {'data_type': None}
        }
    ]
    
    all_cases = test_cases + edge_cases
    
    for i, case in enumerate(all_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"参数: {case['params']}")
        
        # 重置订阅跟踪器
        subscription_tracker = {
            'subscribed': {},
            'unsubscribed': {},
            'history': []
        }
        
        try:
            start_time = time.time()
            
            # 设置订阅状态
            print("设置订阅状态...")
            for symbol, data_type, action in case['setup_subscriptions']:
                track_subscription(symbol, data_type, action)
                print(f"  {action}: {symbol} - {data_type}")
            
            # 显示当前订阅状态
            print(f"\n当前状态:")
            print(f"  已订阅: {len(subscription_tracker['subscribed'])} 个股票")
            print(f"  已取消订阅: {len(subscription_tracker['unsubscribed'])} 个股票")
            print(f"  历史记录: {len(subscription_tracker['history'])} 条")
            
            # 获取已取消订阅的股票
            print("\n获取已取消订阅的股票...")
            
            # 注意：这里使用模拟函数，实际使用时应该调用 get_unsubscribed_symbols()
            # unsubscribed_data = get_unsubscribed_symbols(**case['params'])
            unsubscribed_data = get_mock_unsubscribed_symbols(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✓ 获取已取消订阅股票成功")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 返回数据: {len(unsubscribed_data)} 条")
            
            # 显示部分结果
            if unsubscribed_data:
                print("\n已取消订阅的股票（前5个）:")
                for j, item in enumerate(unsubscribed_data[:5]):
                    print(f"  {j+1}. {item}")
                
                if len(unsubscribed_data) > 5:
                    print(f"  ... 还有 {len(unsubscribed_data) - 5} 个")
            else:
                print("  没有已取消订阅的股票")
            
            # 分析数据
            analysis = analyze_unsubscribed_symbols_data(unsubscribed_data)
            analysis['test_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params'],
                'setup_operations': len(case['setup_subscriptions'])
            }
            
            # 显示分析结果
            if 'basic_stats' in analysis:
                stats = analysis['basic_stats']
                print(f"\n分析结果:")
                print(f"  - 总股票数: {stats['total_symbols']}")
                
                if 'symbols' in analysis:
                    print(f"  - 唯一股票数: {analysis['symbols']['unique_count']}")
                
                if 'exchange_distribution' in analysis:
                    print(f"  - 交易所分布: {analysis['exchange_distribution']['counts']}")
                
                if 'data_type_distribution' in analysis:
                    print(f"  - 数据类型分布: {analysis['data_type_distribution']['counts']}")
            
            # 保存结果
            filename_prefix = f"unsubscribed_symbols_case_{i}_{case['name'].replace(' ', '_').replace('-', '_')}"
            save_unsubscribed_symbols_results(unsubscribed_data, analysis, filename_prefix)
            
        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
            # 记录错误信息
            error_analysis = {
                'error': str(e),
                'test_info': {
                    'timestamp': datetime.now().isoformat(),
                    'parameters': case['params']
                }
            }
            filename_prefix = f"unsubscribed_symbols_error_case_{i}"
            save_unsubscribed_symbols_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
        time.sleep(1)  # 测试间隔
    
    print("\n" + "=" * 60)
    print("get_unsubscribed_symbols API 测试完成")
    print("=" * 60)
    
    # 显示最终的订阅跟踪状态
    print("\n最终订阅跟踪状态:")
    print(f"已订阅股票: {list(subscription_tracker['subscribed'].keys())}")
    print(f"已取消订阅股票: {list(subscription_tracker['unsubscribed'].keys())}")
    print(f"总历史记录: {len(subscription_tracker['history'])} 条")

if __name__ == '__main__':
    test_get_unsubscribed_symbols()