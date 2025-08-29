#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: get_subscribed_symbols
获取已订阅的股票代码列表

功能说明:
- 获取当前已订阅的股票代码
- 支持按数据类型筛选
- 提供订阅状态管理和监控功能
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
OUTPUT_DIR = 'output/subscribed_symbols_data'

# 全局变量用于模拟订阅管理
subscription_tracker = {
    'subscribed': {},  # {symbol: {data_types: set, subscribe_time: datetime}}
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
    
    elif action == 'unsubscribe':
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

def get_mock_subscribed_symbols(data_type=None):
    """模拟获取已订阅的股票代码（因为实际API可能需要特定环境）"""
    global subscription_tracker
    
    subscribed_symbols = []
    
    for symbol, info in subscription_tracker['subscribed'].items():
        if data_type is None:
            # 返回所有已订阅的股票
            subscribed_symbols.append({
                'symbol': symbol,
                'data_types': list(info['data_types']),
                'subscribe_time': info['subscribe_time'].isoformat(),
                'duration_seconds': (datetime.now() - info['subscribe_time']).total_seconds()
            })
        elif data_type in info['data_types']:
            # 返回特定数据类型的已订阅股票
            subscribed_symbols.append({
                'symbol': symbol,
                'data_type': data_type,
                'subscribe_time': info['subscribe_time'].isoformat(),
                'duration_seconds': (datetime.now() - info['subscribe_time']).total_seconds()
            })
    
    return subscribed_symbols

def analyze_subscribed_symbols_data(subscribed_data):
    """分析已订阅的股票数据"""
    if not subscribed_data:
        return {
            'basic_stats': {
                'total_symbols': 0,
                'analysis_time': datetime.now().isoformat()
            }
        }
    
    analysis = {
        'basic_stats': {
            'total_symbols': len(subscribed_data),
            'analysis_time': datetime.now().isoformat()
        }
    }
    
    # 提取所有股票代码
    symbols = [item['symbol'] for item in subscribed_data]
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
    
    # 数据类型分布
    data_types = []
    for item in subscribed_data:
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
    
    # 订阅持续时间分析
    durations = []
    for item in subscribed_data:
        if 'duration_seconds' in item:
            durations.append(item['duration_seconds'])
    
    if durations:
        analysis['duration_stats'] = {
            'count': len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'avg_duration': sum(durations) / len(durations),
            'total_duration': sum(durations)
        }
    
    # 订阅时间分析
    subscribe_times = []
    for item in subscribed_data:
        if 'subscribe_time' in item:
            try:
                subscribe_times.append(datetime.fromisoformat(item['subscribe_time']))
            except:
                pass
    
    if subscribe_times:
        analysis['time_analysis'] = {
            'earliest_subscribe': min(subscribe_times).isoformat(),
            'latest_subscribe': max(subscribe_times).isoformat(),
            'time_span_seconds': (max(subscribe_times) - min(subscribe_times)).total_seconds()
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
    
    # 股票代码长度分析
    code_lengths = []
    for symbol in symbols:
        if '.' in symbol:
            code = symbol.split('.')[1]
            code_lengths.append(len(code))
    
    if code_lengths:
        length_counts = {}
        for length in code_lengths:
            length_counts[length] = length_counts.get(length, 0) + 1
        
        analysis['code_length_distribution'] = {
            'counts': length_counts,
            'avg_length': sum(code_lengths) / len(code_lengths)
        }
    
    return analysis

def save_subscribed_symbols_results(subscribed_data, analysis, filename_prefix):
    """保存已订阅股票结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据 - JSON格式
    json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(subscribed_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"已订阅股票数据已保存到: {json_file}")
    
    # 保存原始数据 - CSV格式
    if subscribed_data:
        try:
            df = pd.DataFrame(subscribed_data)
            csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"已订阅股票数据已保存到: {csv_file}")
        except Exception as e:
            print(f"保存CSV文件时出错: {e}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")
    
    # 保存股票代码列表 - TXT格式
    if subscribed_data:
        symbols = list(set([item['symbol'] for item in subscribed_data]))
        txt_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_symbols_{timestamp}.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            for symbol in sorted(symbols):
                f.write(f"{symbol}\n")
        print(f"股票代码列表已保存到: {txt_file}")
    
    # 保存Excel格式（如果有数据）
    if subscribed_data:
        try:
            excel_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.xlsx')
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 原始数据
                df = pd.DataFrame(subscribed_data)
                df.to_excel(writer, sheet_name='订阅数据', index=False)
                
                # 分析结果
                if 'symbols' in analysis:
                    symbols_df = pd.DataFrame({'symbol': analysis['symbols']['unique_symbols']})
                    symbols_df.to_excel(writer, sheet_name='股票列表', index=False)
                
                if 'exchange_distribution' in analysis:
                    exchange_df = pd.DataFrame(list(analysis['exchange_distribution']['counts'].items()), 
                                             columns=['交易所', '数量'])
                    exchange_df.to_excel(writer, sheet_name='交易所分布', index=False)
            
            print(f"Excel文件已保存到: {excel_file}")
        except Exception as e:
            print(f"保存Excel文件时出错: {e}")

def dummy_callback(context, data):
    """虚拟回调函数"""
    pass

def test_get_subscribed_symbols():
    """测试get_subscribed_symbols API"""
    global subscription_tracker
    
    print("=" * 60)
    print("测试 get_subscribed_symbols API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '基本功能测试 - 获取所有已订阅股票',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600036', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe'),
                ('SZSE.000002', 'l2tick', 'subscribe')
            ],
            'params': {'data_type': None}
        },
        {
            'name': '按数据类型筛选 - tick数据',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600036', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe'),
                ('SZSE.000002', 'l2tick', 'subscribe')
            ],
            'params': {'data_type': 'tick'}
        },
        {
            'name': '按数据类型筛选 - bar数据',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe'),
                ('SZSE.000002', 'bar.300s', 'subscribe'),
                ('SHSE.600036', 'bar.60s', 'subscribe')
            ],
            'params': {'data_type': 'bar.60s'}
        },
        {
            'name': '混合订阅和取消订阅',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600036', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe'),
                ('SHSE.600000', 'tick', 'unsubscribe'),  # 取消一个
                ('SZSE.000002', 'l2tick', 'subscribe')   # 新增一个
            ],
            'params': {'data_type': None}
        },
        {
            'name': '大量股票订阅',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600036', 'tick', 'subscribe'),
                ('SHSE.600519', 'tick', 'subscribe'),
                ('SHSE.600887', 'tick', 'subscribe'),
                ('SZSE.000001', 'tick', 'subscribe'),
                ('SZSE.000002', 'tick', 'subscribe'),
                ('SZSE.000858', 'tick', 'subscribe'),
                ('SHSE.600000', 'bar.60s', 'subscribe'),
                ('SHSE.600036', 'bar.300s', 'subscribe'),
                ('SZSE.000001', 'l2tick', 'subscribe')
            ],
            'params': {'data_type': 'tick'}
        },
        {
            'name': '多种数据类型订阅同一股票',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600000', 'bar.60s', 'subscribe'),
                ('SHSE.600000', 'bar.300s', 'subscribe'),
                ('SHSE.600000', 'l2tick', 'subscribe')
            ],
            'params': {'data_type': None}
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
            'name': '全部取消订阅后查询',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe'),
                ('SHSE.600000', 'tick', 'unsubscribe'),
                ('SZSE.000001', 'bar.60s', 'unsubscribe')
            ],
            'params': {'data_type': None}
        },
        {
            'name': '查询不存在的数据类型',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SZSE.000001', 'bar.60s', 'subscribe')
            ],
            'params': {'data_type': 'nonexistent_type'}
        },
        {
            'name': '无效股票代码处理',
            'setup_subscriptions': [
                ('INVALID.SYMBOL', 'tick', 'subscribe'),
                ('', 'tick', 'subscribe'),
                ('SHSE.600000', 'tick', 'subscribe')  # 有效的作为对比
            ],
            'params': {'data_type': None}
        },
        {
            'name': '重复订阅同一股票同一数据类型',
            'setup_subscriptions': [
                ('SHSE.600000', 'tick', 'subscribe'),
                ('SHSE.600000', 'tick', 'subscribe'),  # 重复订阅
                ('SHSE.600000', 'tick', 'subscribe')   # 再次重复
            ],
            'params': {'data_type': 'tick'}
        }
    ]
    
    all_cases = test_cases + edge_cases
    
    for i, case in enumerate(all_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"参数: {case['params']}")
        
        # 重置订阅跟踪器
        subscription_tracker = {
            'subscribed': {},
            'history': []
        }
        
        try:
            start_time = time.time()
            
            # 设置订阅状态
            print("设置订阅状态...")
            for symbol, data_type, action in case['setup_subscriptions']:
                track_subscription(symbol, data_type, action)
                print(f"  {action}: {symbol} - {data_type}")
                time.sleep(0.1)  # 模拟时间间隔
            
            # 显示当前订阅状态
            print(f"\n当前状态:")
            print(f"  已订阅: {len(subscription_tracker['subscribed'])} 个股票")
            print(f"  历史记录: {len(subscription_tracker['history'])} 条")
            
            # 显示详细订阅信息
            if subscription_tracker['subscribed']:
                print("  详细订阅信息:")
                for symbol, info in subscription_tracker['subscribed'].items():
                    data_types = ', '.join(info['data_types'])
                    print(f"    {symbol}: {data_types}")
            
            # 获取已订阅的股票
            print("\n获取已订阅的股票...")
            
            # 注意：这里使用模拟函数，实际使用时应该调用 get_subscribed_symbols()
            # subscribed_data = get_subscribed_symbols(**case['params'])
            subscribed_data = get_mock_subscribed_symbols(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✓ 获取已订阅股票成功")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 返回数据: {len(subscribed_data)} 条")
            
            # 显示部分结果
            if subscribed_data:
                print("\n已订阅的股票（前5个）:")
                for j, item in enumerate(subscribed_data[:5]):
                    symbol = item['symbol']
                    if 'data_types' in item:
                        data_types = ', '.join(item['data_types'])
                        duration_sec = item.get('duration_seconds', 0)
                        print(f"  {j+1}. {symbol} ({data_types}) - 持续 {duration_sec:.1f}秒")
                    else:
                        data_type = item.get('data_type', 'unknown')
                        duration_sec = item.get('duration_seconds', 0)
                        print(f"  {j+1}. {symbol} ({data_type}) - 持续 {duration_sec:.1f}秒")
                
                if len(subscribed_data) > 5:
                    print(f"  ... 还有 {len(subscribed_data) - 5} 个")
            else:
                print("  没有已订阅的股票")
            
            # 分析数据
            analysis = analyze_subscribed_symbols_data(subscribed_data)
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
                
                if 'duration_stats' in analysis:
                    duration_stats = analysis['duration_stats']
                    print(f"  - 平均订阅时长: {duration_stats['avg_duration']:.1f}秒")
                    print(f"  - 最长订阅时长: {duration_stats['max_duration']:.1f}秒")
            
            # 保存结果
            filename_prefix = f"subscribed_symbols_case_{i}_{case['name'].replace(' ', '_').replace('-', '_')}"
            save_subscribed_symbols_results(subscribed_data, analysis, filename_prefix)
            
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
            filename_prefix = f"subscribed_symbols_error_case_{i}"
            save_subscribed_symbols_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
        time.sleep(1)  # 测试间隔
    
    print("\n" + "=" * 60)
    print("get_subscribed_symbols API 测试完成")
    print("=" * 60)
    
    # 显示最终的订阅跟踪状态
    print("\n最终订阅跟踪状态:")
    print(f"已订阅股票: {list(subscription_tracker['subscribed'].keys())}")
    print(f"总历史记录: {len(subscription_tracker['history'])} 条")
    
    # 显示订阅历史统计
    if subscription_tracker['history']:
        subscribe_count = sum(1 for h in subscription_tracker['history'] if h['action'] == 'subscribe')
        unsubscribe_count = sum(1 for h in subscription_tracker['history'] if h['action'] == 'unsubscribe')
        print(f"历史订阅次数: {subscribe_count}")
        print(f"历史取消次数: {unsubscribe_count}")

if __name__ == '__main__':
    test_get_subscribed_symbols()