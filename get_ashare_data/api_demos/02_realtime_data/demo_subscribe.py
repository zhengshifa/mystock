#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: subscribe
订阅实时数据

功能说明:
- 订阅股票的实时行情数据
- 支持多种数据类型订阅（tick, bar, l2tick等）
- 提供订阅状态监控和数据接收功能
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
OUTPUT_DIR = 'output/subscribe_data'

# 全局变量用于存储接收到的数据
received_data = {
    'ticks': [],
    'bars': [],
    'l2ticks': [],
    'l2orders': [],
    'l2transactions': []
}

# 数据接收计数器
data_counters = {
    'tick_count': 0,
    'bar_count': 0,
    'l2tick_count': 0,
    'l2order_count': 0,
    'l2transaction_count': 0
}

# 订阅状态
subscription_status = {
    'active_subscriptions': [],
    'start_time': None,
    'last_data_time': None
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
    global received_data, data_counters, subscription_status
    
    try:
        tick_dict = convert_data_to_dict(tick)
        tick_dict['receive_time'] = datetime.now().isoformat()
        
        received_data['ticks'].append(tick_dict)
        data_counters['tick_count'] += 1
        subscription_status['last_data_time'] = datetime.now()
        
        # 限制存储的数据量
        if len(received_data['ticks']) > 1000:
            received_data['ticks'] = received_data['ticks'][-500:]
        
        # 打印接收到的数据信息
        symbol = tick_dict.get('symbol', 'Unknown')
        price = tick_dict.get('price', 0)
        volume = tick_dict.get('volume', 0)
        print(f"[TICK] {symbol}: 价格={price}, 成交量={volume}, 时间={tick_dict.get('created_at', '')}")
        
    except Exception as e:
        print(f"处理Tick数据时出错: {e}")

def on_bar(context, bar):
    """Bar数据回调函数"""
    global received_data, data_counters, subscription_status
    
    try:
        bar_dict = convert_data_to_dict(bar)
        bar_dict['receive_time'] = datetime.now().isoformat()
        
        received_data['bars'].append(bar_dict)
        data_counters['bar_count'] += 1
        subscription_status['last_data_time'] = datetime.now()
        
        # 限制存储的数据量
        if len(received_data['bars']) > 1000:
            received_data['bars'] = received_data['bars'][-500:]
        
        # 打印接收到的数据信息
        symbol = bar_dict.get('symbol', 'Unknown')
        close = bar_dict.get('close', 0)
        volume = bar_dict.get('volume', 0)
        print(f"[BAR] {symbol}: 收盘={close}, 成交量={volume}, 时间={bar_dict.get('eob', '')}")
        
    except Exception as e:
        print(f"处理Bar数据时出错: {e}")

def on_l2tick(context, l2tick):
    """L2 Tick数据回调函数"""
    global received_data, data_counters, subscription_status
    
    try:
        l2tick_dict = convert_data_to_dict(l2tick)
        l2tick_dict['receive_time'] = datetime.now().isoformat()
        
        received_data['l2ticks'].append(l2tick_dict)
        data_counters['l2tick_count'] += 1
        subscription_status['last_data_time'] = datetime.now()
        
        # 限制存储的数据量
        if len(received_data['l2ticks']) > 1000:
            received_data['l2ticks'] = received_data['l2ticks'][-500:]
        
        # 打印接收到的数据信息
        symbol = l2tick_dict.get('symbol', 'Unknown')
        price = l2tick_dict.get('price', 0)
        volume = l2tick_dict.get('volume', 0)
        print(f"[L2TICK] {symbol}: 价格={price}, 成交量={volume}, 时间={l2tick_dict.get('created_at', '')}")
        
    except Exception as e:
        print(f"处理L2 Tick数据时出错: {e}")

def on_l2order(context, l2order):
    """L2 Order数据回调函数"""
    global received_data, data_counters, subscription_status
    
    try:
        l2order_dict = convert_data_to_dict(l2order)
        l2order_dict['receive_time'] = datetime.now().isoformat()
        
        received_data['l2orders'].append(l2order_dict)
        data_counters['l2order_count'] += 1
        subscription_status['last_data_time'] = datetime.now()
        
        # 限制存储的数据量
        if len(received_data['l2orders']) > 1000:
            received_data['l2orders'] = received_data['l2orders'][-500:]
        
        # 打印接收到的数据信息
        symbol = l2order_dict.get('symbol', 'Unknown')
        price = l2order_dict.get('price', 0)
        volume = l2order_dict.get('volume', 0)
        side = l2order_dict.get('side', 'Unknown')
        print(f"[L2ORDER] {symbol}: 价格={price}, 数量={volume}, 方向={side}, 时间={l2order_dict.get('created_at', '')}")
        
    except Exception as e:
        print(f"处理L2 Order数据时出错: {e}")

def on_l2transaction(context, l2transaction):
    """L2 Transaction数据回调函数"""
    global received_data, data_counters, subscription_status
    
    try:
        l2transaction_dict = convert_data_to_dict(l2transaction)
        l2transaction_dict['receive_time'] = datetime.now().isoformat()
        
        received_data['l2transactions'].append(l2transaction_dict)
        data_counters['l2transaction_count'] += 1
        subscription_status['last_data_time'] = datetime.now()
        
        # 限制存储的数据量
        if len(received_data['l2transactions']) > 1000:
            received_data['l2transactions'] = received_data['l2transactions'][-500:]
        
        # 打印接收到的数据信息
        symbol = l2transaction_dict.get('symbol', 'Unknown')
        price = l2transaction_dict.get('price', 0)
        volume = l2transaction_dict.get('volume', 0)
        side = l2transaction_dict.get('side', 'Unknown')
        print(f"[L2TRANSACTION] {symbol}: 价格={price}, 数量={volume}, 方向={side}, 时间={l2transaction_dict.get('created_at', '')}")
        
    except Exception as e:
        print(f"处理L2 Transaction数据时出错: {e}")

def analyze_subscription_data():
    """分析订阅数据"""
    global received_data, data_counters, subscription_status
    
    analysis = {
        'subscription_info': {
            'active_subscriptions': subscription_status['active_subscriptions'],
            'start_time': subscription_status['start_time'].isoformat() if subscription_status['start_time'] else None,
            'last_data_time': subscription_status['last_data_time'].isoformat() if subscription_status['last_data_time'] else None,
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
    
    return analysis

def save_subscription_results(analysis, filename_prefix):
    """保存订阅结果到文件"""
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
            
            # CSV格式
            try:
                csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_{data_type}_{timestamp}.csv')
                df = pd.DataFrame(data_list)
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"{data_type}数据已保存到: {csv_file}")
            except Exception as e:
                print(f"保存{data_type} CSV文件时出错: {e}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

def print_subscription_status():
    """打印订阅状态"""
    global data_counters, subscription_status
    
    print("\n" + "=" * 50)
    print("订阅状态统计")
    print("=" * 50)
    
    if subscription_status['start_time']:
        duration = datetime.now() - subscription_status['start_time']
        print(f"订阅时长: {duration}")
    
    print(f"活跃订阅: {', '.join(subscription_status['active_subscriptions'])}")
    
    if subscription_status['last_data_time']:
        last_data_ago = datetime.now() - subscription_status['last_data_time']
        print(f"最后数据接收: {last_data_ago.total_seconds():.1f}秒前")
    
    print("\n数据接收统计:")
    for data_type, count in data_counters.items():
        print(f"  {data_type}: {count}")
    
    print("=" * 50)

def test_subscribe():
    """测试subscribe API"""
    global subscription_status, received_data, data_counters
    
    print("=" * 60)
    print("测试 subscribe API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '订阅单只股票Tick数据',
            'params': {
                'symbols': 'SHSE.600000',
                'data_type': 'tick',
                'callback': on_tick,
                'duration': 30  # 订阅30秒
            }
        },
        {
            'name': '订阅多只股票Tick数据',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001', 'SHSE.600036'],
                'data_type': 'tick',
                'callback': on_tick,
                'duration': 30
            }
        },
        {
            'name': '订阅Bar数据',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001'],
                'data_type': 'bar.60s',
                'callback': on_bar,
                'duration': 60  # 订阅60秒
            }
        },
        {
            'name': '订阅L2 Tick数据',
            'params': {
                'symbols': 'SHSE.600000',
                'data_type': 'l2tick',
                'callback': on_l2tick,
                'duration': 30
            }
        },
        {
            'name': '订阅L2 Order数据',
            'params': {
                'symbols': 'SHSE.600000',
                'data_type': 'l2order',
                'callback': on_l2order,
                'duration': 30
            }
        },
        {
            'name': '订阅L2 Transaction数据',
            'params': {
                'symbols': 'SHSE.600000',
                'data_type': 'l2transaction',
                'callback': on_l2transaction,
                'duration': 30
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '订阅不存在的股票',
            'params': {
                'symbols': 'SHSE.999999',
                'data_type': 'tick',
                'callback': on_tick,
                'duration': 10
            }
        },
        {
            'name': '订阅无效数据类型',
            'params': {
                'symbols': 'SHSE.600000',
                'data_type': 'invalid_type',
                'callback': on_tick,
                'duration': 10
            }
        },
        {
            'name': '订阅空股票列表',
            'params': {
                'symbols': [],
                'data_type': 'tick',
                'callback': on_tick,
                'duration': 10
            }
        }
    ]
    
    all_cases = test_cases + edge_cases
    
    for i, case in enumerate(all_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"参数: {case['params']}")
        
        # 重置数据
        received_data = {
            'ticks': [],
            'bars': [],
            'l2ticks': [],
            'l2orders': [],
            'l2transactions': []
        }
        data_counters = {
            'tick_count': 0,
            'bar_count': 0,
            'l2tick_count': 0,
            'l2order_count': 0,
            'l2transaction_count': 0
        }
        subscription_status = {
            'active_subscriptions': [],
            'start_time': None,
            'last_data_time': None
        }
        
        try:
            start_time = time.time()
            subscription_status['start_time'] = datetime.now()
            
            # 调用订阅API
            symbols = case['params']['symbols']
            data_type = case['params']['data_type']
            callback = case['params']['callback']
            duration = case['params']['duration']
            
            print(f"开始订阅: {symbols} - {data_type}")
            
            # 执行订阅
            if isinstance(symbols, list):
                for symbol in symbols:
                    try:
                        subscribe(symbol, data_type, callback)
                        subscription_status['active_subscriptions'].append(f"{symbol}:{data_type}")
                        print(f"✓ 成功订阅: {symbol} - {data_type}")
                    except Exception as e:
                        print(f"✗ 订阅失败: {symbol} - {data_type}, 错误: {e}")
            else:
                try:
                    subscribe(symbols, data_type, callback)
                    subscription_status['active_subscriptions'].append(f"{symbols}:{data_type}")
                    print(f"✓ 成功订阅: {symbols} - {data_type}")
                except Exception as e:
                    print(f"✗ 订阅失败: {symbols} - {data_type}, 错误: {e}")
            
            if subscription_status['active_subscriptions']:
                print(f"等待数据接收 {duration} 秒...")
                
                # 等待数据接收
                for second in range(duration):
                    time.sleep(1)
                    if (second + 1) % 10 == 0 or second == duration - 1:
                        print_subscription_status()
                
                # 取消订阅
                print("\n取消订阅...")
                if isinstance(symbols, list):
                    for symbol in symbols:
                        try:
                            unsubscribe(symbol, data_type)
                            print(f"✓ 成功取消订阅: {symbol} - {data_type}")
                        except Exception as e:
                            print(f"✗ 取消订阅失败: {symbol} - {data_type}, 错误: {e}")
                else:
                    try:
                        unsubscribe(symbols, data_type)
                        print(f"✓ 成功取消订阅: {symbols} - {data_type}")
                    except Exception as e:
                        print(f"✗ 取消订阅失败: {symbols} - {data_type}, 错误: {e}")
                
                end_time = time.time()
                duration_actual = end_time - start_time
                
                # 分析数据
                analysis = analyze_subscription_data()
                analysis['test_info'] = {
                    'duration_seconds': round(duration_actual, 3),
                    'timestamp': datetime.now().isoformat(),
                    'parameters': case['params']
                }
                
                print(f"\n✓ 订阅测试完成")
                print(f"  - 实际耗时: {duration_actual:.3f}秒")
                print(f"  - 活跃订阅数: {len(subscription_status['active_subscriptions'])}")
                
                # 显示数据接收统计
                total_received = sum(data_counters.values())
                print(f"  - 总接收数据: {total_received} 条")
                for data_type, count in data_counters.items():
                    if count > 0:
                        print(f"    {data_type}: {count} 条")
                
                # 保存结果
                if total_received > 0:
                    filename_prefix = f"subscribe_case_{i}_{case['name'].replace(' ', '_')}"
                    save_subscription_results(analysis, filename_prefix)
                else:
                    print("  - 未接收到任何数据")
            else:
                print("✗ 没有成功的订阅")
            
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
            filename_prefix = f"subscribe_error_case_{i}"
            save_subscription_results(error_analysis, filename_prefix)
        
        print("-" * 40)
        time.sleep(2)  # 测试间隔
    
    print("\n" + "=" * 60)
    print("subscribe API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_subscribe()