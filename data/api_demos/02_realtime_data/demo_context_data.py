#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: context.data
上下文数据访问

功能说明:
- 演示如何使用context.data访问实时数据
- 在策略回调函数中获取当前数据
- 提供数据分析和导出功能
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
OUTPUT_DIR = 'output/context_data'

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
                    # 处理特殊类型
                    if hasattr(value, '__dict__'):
                        # 如果是对象，递归转换
                        data_dict[attr] = convert_data_to_dict(value)
                    else:
                        data_dict[attr] = value
            except:
                pass
    
    return data_dict

def analyze_context_data(data_dict, symbol):
    """分析上下文数据"""
    if not data_dict:
        return {}
    
    analysis = {
        'basic_info': {
            'symbol': symbol,
            'total_attributes': len(data_dict),
            'data_timestamp': datetime.now().isoformat()
        }
    }
    
    # 分析数据类型
    data_types = {}
    price_fields = []
    volume_fields = []
    time_fields = []
    other_fields = []
    
    for key, value in data_dict.items():
        data_type = type(value).__name__
        data_types[data_type] = data_types.get(data_type, 0) + 1
        
        # 分类字段
        key_lower = key.lower()
        if 'price' in key_lower or 'open' in key_lower or 'high' in key_lower or 'low' in key_lower or 'close' in key_lower:
            price_fields.append({'field': key, 'value': value, 'type': data_type})
        elif 'volume' in key_lower or 'amount' in key_lower or 'turnover' in key_lower:
            volume_fields.append({'field': key, 'value': value, 'type': data_type})
        elif 'time' in key_lower or 'date' in key_lower:
            time_fields.append({'field': key, 'value': value, 'type': data_type})
        else:
            other_fields.append({'field': key, 'value': value, 'type': data_type})
    
    analysis['data_types'] = data_types
    
    if price_fields:
        analysis['price_fields'] = price_fields
        # 计算价格统计
        numeric_prices = []
        for field in price_fields:
            try:
                if isinstance(field['value'], (int, float)) and field['value'] > 0:
                    numeric_prices.append(field['value'])
            except:
                pass
        
        if numeric_prices:
            analysis['price_statistics'] = {
                'count': len(numeric_prices),
                'min': min(numeric_prices),
                'max': max(numeric_prices),
                'avg': round(sum(numeric_prices) / len(numeric_prices), 4)
            }
    
    if volume_fields:
        analysis['volume_fields'] = volume_fields
        # 计算成交量统计
        numeric_volumes = []
        for field in volume_fields:
            try:
                if isinstance(field['value'], (int, float)) and field['value'] > 0:
                    numeric_volumes.append(field['value'])
            except:
                pass
        
        if numeric_volumes:
            analysis['volume_statistics'] = {
                'count': len(numeric_volumes),
                'min': min(numeric_volumes),
                'max': max(numeric_volumes),
                'total': sum(numeric_volumes)
            }
    
    if time_fields:
        analysis['time_fields'] = time_fields
    
    if other_fields:
        analysis['other_fields'] = other_fields[:10]  # 只保留前10个
    
    return analysis

def save_results(data_dict, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if data_dict:
        # JSON格式
        json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2, default=str)
        print(f"数据已保存到: {json_file}")
        
        # CSV格式
        try:
            csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
            df = pd.DataFrame([data_dict])
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"数据已保存到: {csv_file}")
        except Exception as e:
            print(f"保存CSV文件失败: {e}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

# 全局变量存储数据
collected_data = []
test_symbols = ['SHSE.000001', 'SZSE.000001', 'SHSE.600000', 'SZSE.000002']
current_test_index = 0

def on_tick(context, tick):
    """tick数据回调函数"""
    global collected_data, current_test_index
    
    try:
        print(f"\n收到tick数据: {tick.symbol}")
        
        # 访问context.data
        if hasattr(context, 'data'):
            context_data = context.data
            print(f"context.data类型: {type(context_data)}")
            
            # 尝试获取当前symbol的数据
            symbol_data = None
            if hasattr(context_data, tick.symbol):
                symbol_data = getattr(context_data, tick.symbol)
            elif hasattr(context_data, 'get'):
                symbol_data = context_data.get(tick.symbol)
            
            if symbol_data:
                print(f"获取到{tick.symbol}的context数据")
                data_dict = convert_data_to_dict(symbol_data)
                
                # 分析数据
                analysis = analyze_context_data(data_dict, tick.symbol)
                analysis['tick_info'] = {
                    'symbol': tick.symbol,
                    'price': tick.price,
                    'volume': tick.volume,
                    'timestamp': str(tick.created_at)
                }
                
                # 保存数据
                collected_data.append({
                    'symbol': tick.symbol,
                    'context_data': data_dict,
                    'analysis': analysis,
                    'tick_data': {
                        'price': tick.price,
                        'volume': tick.volume,
                        'created_at': str(tick.created_at)
                    }
                })
                
                print(f"  - 数据属性数量: {len(data_dict)}")
                if analysis.get('price_statistics'):
                    stats = analysis['price_statistics']
                    print(f"  - 价格统计: 最小{stats['min']}, 最大{stats['max']}, 平均{stats['avg']}")
                
                # 保存结果
                filename_prefix = f"context_data_{tick.symbol.replace('.', '_')}"
                save_results(data_dict, analysis, filename_prefix)
            else:
                print(f"未能获取{tick.symbol}的context数据")
        else:
            print("context中没有data属性")
    
    except Exception as e:
        print(f"处理tick数据时出错: {e}")
    
    # 控制测试时长
    if len(collected_data) >= 5:  # 收集5个数据后停止
        print("已收集足够数据，停止订阅")
        unsubscribe(symbols=test_symbols, data_type=DATATYPE_TICK)

def on_bar(context, bars):
    """bar数据回调函数"""
    global collected_data
    
    try:
        for bar in bars:
            print(f"\n收到bar数据: {bar.symbol}")
            
            # 访问context.data
            if hasattr(context, 'data'):
                context_data = context.data
                
                # 尝试获取当前symbol的数据
                symbol_data = None
                if hasattr(context_data, bar.symbol):
                    symbol_data = getattr(context_data, bar.symbol)
                elif hasattr(context_data, 'get'):
                    symbol_data = context_data.get(bar.symbol)
                
                if symbol_data:
                    print(f"获取到{bar.symbol}的context数据")
                    data_dict = convert_data_to_dict(symbol_data)
                    
                    # 分析数据
                    analysis = analyze_context_data(data_dict, bar.symbol)
                    analysis['bar_info'] = {
                        'symbol': bar.symbol,
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume,
                        'timestamp': str(bar.bob)
                    }
                    
                    # 保存数据
                    collected_data.append({
                        'symbol': bar.symbol,
                        'context_data': data_dict,
                        'analysis': analysis,
                        'bar_data': {
                            'open': bar.open,
                            'high': bar.high,
                            'low': bar.low,
                            'close': bar.close,
                            'volume': bar.volume,
                            'bob': str(bar.bob)
                        }
                    })
                    
                    print(f"  - 数据属性数量: {len(data_dict)}")
                    print(f"  - OHLC: {bar.open}/{bar.high}/{bar.low}/{bar.close}")
                    
                    # 保存结果
                    filename_prefix = f"context_data_bar_{bar.symbol.replace('.', '_')}"
                    save_results(data_dict, analysis, filename_prefix)
    
    except Exception as e:
        print(f"处理bar数据时出错: {e}")

def test_context_data():
    """测试context.data功能"""
    print("=" * 60)
    print("测试 context.data 功能")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    global collected_data, test_symbols
    collected_data = []
    
    try:
        # 设置回调函数
        set_handler('on_tick', on_tick)
        set_handler('on_bar', on_bar)
        
        print(f"开始订阅数据: {test_symbols}")
        
        # 订阅tick数据
        print("\n=== 测试Tick数据中的context.data ===")
        subscribe(symbols=test_symbols, data_type=DATATYPE_TICK)
        
        # 等待数据
        print("等待tick数据...")
        time.sleep(10)  # 等待10秒
        
        # 取消订阅tick
        unsubscribe(symbols=test_symbols, data_type=DATATYPE_TICK)
        
        # 订阅bar数据
        print("\n=== 测试Bar数据中的context.data ===")
        subscribe(symbols=test_symbols[:2], data_type=DATATYPE_BAR_1M)  # 只订阅前两个symbol的1分钟bar
        
        # 等待数据
        print("等待bar数据...")
        time.sleep(30)  # 等待30秒
        
        # 取消订阅bar
        unsubscribe(symbols=test_symbols[:2], data_type=DATATYPE_BAR_1M)
        
    except Exception as e:
        print(f"订阅数据时出错: {e}")
    
    # 汇总结果
    print(f"\n=== 测试结果汇总 ===")
    print(f"总共收集到 {len(collected_data)} 条数据")
    
    if collected_data:
        # 按symbol统计
        symbol_stats = {}
        for data in collected_data:
            symbol = data['symbol']
            symbol_stats[symbol] = symbol_stats.get(symbol, 0) + 1
        
        print("按symbol统计:")
        for symbol, count in symbol_stats.items():
            print(f"  {symbol}: {count} 条")
        
        # 保存汇总数据
        summary_data = {
            'total_records': len(collected_data),
            'symbol_statistics': symbol_stats,
            'test_timestamp': datetime.now().isoformat(),
            'detailed_data': collected_data
        }
        
        filename_prefix = "context_data_summary"
        save_results(summary_data, {'summary': summary_data}, filename_prefix)
    
    print("\n" + "=" * 60)
    print("context.data 测试完成")
    print("=" * 60)

def test_context_data_simple():
    """简单的context.data测试（不依赖实时数据）"""
    print("=" * 60)
    print("简单测试 context.data 功能")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '测试获取当前数据',
            'symbols': ['SHSE.000001', 'SZSE.000001']
        },
        {
            'name': '测试获取股票数据',
            'symbols': ['SHSE.600000', 'SHSE.600036', 'SZSE.000002']
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"测试标的: {case['symbols']}")
        
        try:
            # 获取当前数据
            current_data = current(symbols=case['symbols'])
            
            if current_data:
                print(f"✓ 成功获取当前数据")
                print(f"  - 数据条数: {len(current_data)}")
                
                # 模拟context.data的使用
                for data in current_data:
                    symbol = data.symbol
                    print(f"\n  处理 {symbol}:")
                    
                    # 转换数据
                    data_dict = convert_data_to_dict(data)
                    
                    # 分析数据
                    analysis = analyze_context_data(data_dict, symbol)
                    
                    print(f"    - 属性数量: {len(data_dict)}")
                    print(f"    - 当前价格: {getattr(data, 'price', 'N/A')}")
                    print(f"    - 成交量: {getattr(data, 'volume', 'N/A')}")
                    
                    if analysis.get('price_statistics'):
                        stats = analysis['price_statistics']
                        print(f"    - 价格统计: 最小{stats['min']}, 最大{stats['max']}")
                    
                    # 保存结果
                    filename_prefix = f"context_data_simple_{symbol.replace('.', '_')}"
                    save_results(data_dict, analysis, filename_prefix)
            else:
                print(f"✗ 未获取到数据")
        
        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("简单context.data测试完成")
    print("=" * 60)

if __name__ == '__main__':
    # 可以选择运行哪种测试
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'simple':
        test_context_data_simple()
    else:
        test_context_data()