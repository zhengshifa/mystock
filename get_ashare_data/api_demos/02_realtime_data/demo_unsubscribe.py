#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: unsubscribe
取消订阅实时数据

功能说明:
- 取消股票的实时行情数据订阅
- 支持取消多种数据类型订阅（tick, bar, l2tick等）
- 提供订阅管理和状态监控功能
"""

import gm
from gm.api import *
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time
import threading

# 配置信息
CONFIG_FILE = 'gm_config.json'
OUTPUT_DIR = 'output/unsubscribe_data'

# 全局变量用于存储接收到的数据和订阅状态
received_data = {
    'ticks': [],
    'bars': [],
    'l2ticks': []
}

# 数据接收计数器
data_counters = {
    'tick_count': 0,
    'bar_count': 0,
    'l2tick_count': 0
}

# 订阅管理
subscription_manager = {
    'active_subscriptions': {},  # {subscription_key: {'symbol': '', 'data_type': '', 'start_time': datetime}}
    'subscription_history': [],
    'unsubscribe_history': []
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

def convert_data_to_dict(data_obj):
    """将数据对象转换为字典"""
    if not data_obj:
        return {}
    
    data_dict = {}
    
    # 获取对象的所有属性
    for attr in dir(data_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(data_obj, attr)
                if not callable(value):
                    data_dict[attr] = value
            except:
                pass
    
    return data_dict

def on_tick(context, tick):
    """Tick数据回调函数"""
    global received_data, data_counters
    
    try:
        tick_dict = convert_data_to_dict(tick)
        tick_dict['receive_time'] = datetime.now().isoformat()
        
        received_data['ticks'].append(tick_dict)
        data_counters['tick_count'] += 1
        
        # 限制存储的数据量
        if len(received_data['ticks']) > 100:
            received_data['ticks'] = received_data['ticks'][-50:]
        
        # 打印接收到的数据信息
        symbol = tick_dict.get('symbol', 'Unknown')
        price = tick_dict.get('price', 0)
        print(f"[TICK] {symbol}: {price} - {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"处理Tick数据时出错: {e}")

def on_bar(context, bar):
    """Bar数据回调函数"""
    global received_data, data_counters
    
    try:
        bar_dict = convert_data_to_dict(bar)
        bar_dict['receive_time'] = datetime.now().isoformat()
        
        received_data['bars'].append(bar_dict)
        data_counters['bar_count'] += 1
        
        # 限制存储的数据量
        if len(received_data['bars']) > 100:
            received_data['bars'] = received_data['bars'][-50:]
        
        # 打印接收到的数据信息
        symbol = bar_dict.get('symbol', 'Unknown')
        close = bar_dict.get('close', 0)
        print(f"[BAR] {symbol}: {close} - {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"处理Bar数据时出错: {e}")

def on_l2tick(context, l2tick):
    """L2 Tick数据回调函数"""
    global received_data, data_counters
    
    try:
        l2tick_dict = convert_data_to_dict(l2tick)
        l2tick_dict['receive_time'] = datetime.now().isoformat()
        
        received_data['l2ticks'].append(l2tick_dict)
        data_counters['l2tick_count'] += 1
        
        # 限制存储的数据量
        if len(received_data['l2ticks']) > 100:
            received_data['l2ticks'] = received_data['l2ticks'][-50:]
        
        # 打印接收到的数据信息
        symbol = l2tick_dict.get('symbol', 'Unknown')
        price = l2tick_dict.get('price', 0)
        print(f"[L2TICK] {symbol}: {price} - {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"处理L2 Tick数据时出错: {e}")

def add_subscription(symbol, data_type):
    """添加订阅记录"""
    global subscription_manager
    
    subscription_key = f"{symbol}:{data_type}"
    subscription_manager['active_subscriptions'][subscription_key] = {
        'symbol': symbol,
        'data_type': data_type,
        'start_time': datetime.now()
    }
    
    subscription_manager['subscription_history'].append({
        'action': 'subscribe',
        'symbol': symbol,
        'data_type': data_type,
        'timestamp': datetime.now().isoformat()
    })

def remove_subscription(symbol, data_type):
    """移除订阅记录"""
    global subscription_manager
    
    subscription_key = f"{symbol}:{data_type}"
    if subscription_key in subscription_manager['active_subscriptions']:
        subscription_info = subscription_manager['active_subscriptions'].pop(subscription_key)
        
        duration = datetime.now() - subscription_info['start_time']
        
        subscription_manager['unsubscribe_history'].append({
            'action': 'unsubscribe',
            'symbol': symbol,
            'data_type': data_type,
            'duration_seconds': duration.total_seconds(),
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    return False

def get_subscription_status():
    """获取订阅状态"""
    global subscription_manager
    
    status = {
        'active_count': len(subscription_manager['active_subscriptions']),
        'active_subscriptions': list(subscription_manager['active_subscriptions'].keys()),
        'total_subscribed': len(subscription_manager['subscription_history']),
        'total_unsubscribed': len(subscription_manager['unsubscribe_history']),
        'subscription_details': subscription_manager['active_subscriptions'].copy()
    }
    
    # 转换datetime为字符串
    for key, value in status['subscription_details'].items():
        if 'start_time' in value:
            value['start_time'] = value['start_time'].isoformat()
            value['duration_seconds'] = (datetime.now() - datetime.fromisoformat(value['start_time'].replace('T', ' '))).total_seconds()
    
    return status

def analyze_unsubscribe_data():
    """分析取消订阅数据"""
    global received_data, data_counters, subscription_manager
    
    analysis = {
        'subscription_management': {
            'active_subscriptions': len(subscription_manager['active_subscriptions']),
            'subscription_history': subscription_manager['subscription_history'],
            'unsubscribe_history': subscription_manager['unsubscribe_history'],
            'analysis_time': datetime.now().isoformat()
        },
        'data_counters': data_counters.copy(),
        'data_summary': {}
    }
    
    # 分析各类型数据
    for data_type, data_list in received_data.items():
        if data_list:
            analysis['data_summary'][data_type] = {
                'total_records': len(data_list),
                'latest_record': data_list[-1] if data_list else None,
                'symbols': list(set([item.get('symbol', 'Unknown') for item in data_list])),
                'time_range': {
                    'first': data_list[0].get('created_at', '') if data_list else '',
                    'last': data_list[-1].get('created_at', '') if data_list else ''
                }
            }
    
    # 订阅持续时间统计
    if subscription_manager['unsubscribe_history']:
        durations = [item['duration_seconds'] for item in subscription_manager['unsubscribe_history'] if 'duration_seconds' in item]
        if durations:
            analysis['subscription_duration_stats'] = {
                'count': len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'avg_duration': sum(durations) / len(durations)
            }
    
    return analysis

def save_unsubscribe_results(analysis, filename_prefix):
    """保存取消订阅结果到文件"""
    global received_data
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    for data_type, data_list in received_data.items():
        if data_list:
            # JSON格式
            json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_{data_type}_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2, default=str)
            print(f"{data_type}数据已保存到: {json_file}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

def print_subscription_status():
    """打印订阅状态"""
    status = get_subscription_status()
    
    print("\n" + "=" * 40)
    print("订阅状态")
    print("=" * 40)
    print(f"活跃订阅: {status['active_count']}")
    print(f"历史订阅: {status['total_subscribed']}")
    print(f"已取消订阅: {status['total_unsubscribed']}")
    
    if status['active_subscriptions']:
        print("\n当前活跃订阅:")
        for subscription in status['active_subscriptions']:
            print(f"  - {subscription}")
    
    print("\n数据接收统计:")
    for data_type, count in data_counters.items():
        print(f"  {data_type}: {count}")
    
    print("=" * 40)

def test_unsubscribe():
    """测试unsubscribe API"""
    global subscription_manager, received_data, data_counters
    
    print("=" * 60)
    print("测试 unsubscribe API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '订阅后立即取消订阅',
            'params': {
                'symbol': 'SHSE.600000',
                'data_type': 'tick',
                'callback': on_tick,
                'subscribe_duration': 5,  # 订阅5秒后取消
                'wait_after_unsubscribe': 5  # 取消订阅后等待5秒
            }
        },
        {
            'name': '订阅多只股票后分别取消',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001', 'SHSE.600036'],
                'data_type': 'tick',
                'callback': on_tick,
                'subscribe_duration': 10,
                'wait_after_unsubscribe': 5
            }
        },
        {
            'name': '订阅Bar数据后取消',
            'params': {
                'symbol': 'SHSE.600000',
                'data_type': 'bar.60s',
                'callback': on_bar,
                'subscribe_duration': 15,
                'wait_after_unsubscribe': 5
            }
        },
        {
            'name': '订阅L2数据后取消',
            'params': {
                'symbol': 'SHSE.600000',
                'data_type': 'l2tick',
                'callback': on_l2tick,
                'subscribe_duration': 10,
                'wait_after_unsubscribe': 5
            }
        },
        {
            'name': '订阅多种数据类型后取消',
            'params': {
                'symbol': 'SHSE.600000',
                'data_types': ['tick', 'bar.60s'],
                'callbacks': [on_tick, on_bar],
                'subscribe_duration': 15,
                'wait_after_unsubscribe': 5
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '取消不存在的订阅',
            'params': {
                'symbol': 'SHSE.600000',
                'data_type': 'tick',
                'callback': on_tick,
                'subscribe_duration': 0,  # 不订阅，直接尝试取消
                'wait_after_unsubscribe': 2
            }
        },
        {
            'name': '重复取消同一订阅',
            'params': {
                'symbol': 'SHSE.600000',
                'data_type': 'tick',
                'callback': on_tick,
                'subscribe_duration': 5,
                'repeat_unsubscribe': True,  # 重复取消订阅
                'wait_after_unsubscribe': 3
            }
        },
        {
            'name': '取消无效股票代码的订阅',
            'params': {
                'symbol': 'INVALID.SYMBOL',
                'data_type': 'tick',
                'callback': on_tick,
                'subscribe_duration': 5,
                'wait_after_unsubscribe': 2
            }
        }
    ]
    
    all_cases = test_cases + edge_cases
    
    for i, case in enumerate(all_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"参数: {case['params']}")
        
        # 重置数据
        received_data = {'ticks': [], 'bars': [], 'l2ticks': []}
        data_counters = {'tick_count': 0, 'bar_count': 0, 'l2tick_count': 0}
        subscription_manager = {
            'active_subscriptions': {},
            'subscription_history': [],
            'unsubscribe_history': []
        }
        
        try:
            start_time = time.time()
            params = case['params']
            
            # 处理订阅
            if params.get('subscribe_duration', 0) > 0:
                print("开始订阅...")
                
                # 处理单个或多个股票
                if 'symbols' in params:
                    # 多只股票
                    symbols = params['symbols']
                    data_type = params['data_type']
                    callback = params['callback']
                    
                    for symbol in symbols:
                        try:
                            subscribe(symbol, data_type, callback)
                            add_subscription(symbol, data_type)
                            print(f"✓ 成功订阅: {symbol} - {data_type}")
                        except Exception as e:
                            print(f"✗ 订阅失败: {symbol} - {data_type}, 错误: {e}")
                
                elif 'data_types' in params:
                    # 多种数据类型
                    symbol = params['symbol']
                    data_types = params['data_types']
                    callbacks = params['callbacks']
                    
                    for data_type, callback in zip(data_types, callbacks):
                        try:
                            subscribe(symbol, data_type, callback)
                            add_subscription(symbol, data_type)
                            print(f"✓ 成功订阅: {symbol} - {data_type}")
                        except Exception as e:
                            print(f"✗ 订阅失败: {symbol} - {data_type}, 错误: {e}")
                
                else:
                    # 单个股票和数据类型
                    symbol = params['symbol']
                    data_type = params['data_type']
                    callback = params['callback']
                    
                    try:
                        subscribe(symbol, data_type, callback)
                        add_subscription(symbol, data_type)
                        print(f"✓ 成功订阅: {symbol} - {data_type}")
                    except Exception as e:
                        print(f"✗ 订阅失败: {symbol} - {data_type}, 错误: {e}")
                
                # 等待数据接收
                subscribe_duration = params['subscribe_duration']
                print(f"等待数据接收 {subscribe_duration} 秒...")
                
                for second in range(subscribe_duration):
                    time.sleep(1)
                    if (second + 1) % 5 == 0:
                        print_subscription_status()
            
            # 执行取消订阅
            print("\n开始取消订阅...")
            
            if 'symbols' in params:
                # 多只股票
                symbols = params['symbols']
                data_type = params['data_type']
                
                for symbol in symbols:
                    try:
                        unsubscribe(symbol, data_type)
                        remove_subscription(symbol, data_type)
                        print(f"✓ 成功取消订阅: {symbol} - {data_type}")
                    except Exception as e:
                        print(f"✗ 取消订阅失败: {symbol} - {data_type}, 错误: {e}")
            
            elif 'data_types' in params:
                # 多种数据类型
                symbol = params['symbol']
                data_types = params['data_types']
                
                for data_type in data_types:
                    try:
                        unsubscribe(symbol, data_type)
                        remove_subscription(symbol, data_type)
                        print(f"✓ 成功取消订阅: {symbol} - {data_type}")
                    except Exception as e:
                        print(f"✗ 取消订阅失败: {symbol} - {data_type}, 错误: {e}")
            
            else:
                # 单个股票和数据类型
                symbol = params['symbol']
                data_type = params['data_type']
                
                try:
                    unsubscribe(symbol, data_type)
                    remove_subscription(symbol, data_type)
                    print(f"✓ 成功取消订阅: {symbol} - {data_type}")
                except Exception as e:
                    print(f"✗ 取消订阅失败: {symbol} - {data_type}, 错误: {e}")
                
                # 处理重复取消订阅
                if params.get('repeat_unsubscribe', False):
                    print("尝试重复取消订阅...")
                    try:
                        unsubscribe(symbol, data_type)
                        print(f"✓ 重复取消订阅成功: {symbol} - {data_type}")
                    except Exception as e:
                        print(f"✗ 重复取消订阅失败: {symbol} - {data_type}, 错误: {e}")
            
            # 取消订阅后等待
            wait_duration = params.get('wait_after_unsubscribe', 0)
            if wait_duration > 0:
                print(f"取消订阅后等待 {wait_duration} 秒...")
                time.sleep(wait_duration)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 分析数据
            analysis = analyze_unsubscribe_data()
            analysis['test_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"\n✓ 取消订阅测试完成")
            print(f"  - 总耗时: {duration:.3f}秒")
            
            # 显示最终状态
            final_status = get_subscription_status()
            print(f"  - 剩余活跃订阅: {final_status['active_count']}")
            print(f"  - 总订阅次数: {final_status['total_subscribed']}")
            print(f"  - 总取消次数: {final_status['total_unsubscribed']}")
            
            # 显示数据接收统计
            total_received = sum(data_counters.values())
            print(f"  - 总接收数据: {total_received} 条")
            for data_type, count in data_counters.items():
                if count > 0:
                    print(f"    {data_type}: {count} 条")
            
            # 保存结果
            filename_prefix = f"unsubscribe_case_{i}_{case['name'].replace(' ', '_')}"
            save_unsubscribe_results(analysis, filename_prefix)
            
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
            filename_prefix = f"unsubscribe_error_case_{i}"
            save_unsubscribe_results(error_analysis, filename_prefix)
        
        print("-" * 40)
        time.sleep(2)  # 测试间隔
    
    print("\n" + "=" * 60)
    print("unsubscribe API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_unsubscribe()