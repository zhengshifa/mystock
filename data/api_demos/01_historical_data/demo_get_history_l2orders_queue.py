#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: get_history_l2orders_queue
获取历史L2委托队列快照数据

功能说明:
- 获取指定时间段内的L2委托队列快照数据
- 支持多种数据字段和过滤条件
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
OUTPUT_DIR = 'output/l2orders_queue_data'

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

def l2orders_queue_to_dict(queue_data):
    """将L2OrdersQueue对象转换为字典"""
    if queue_data is None:
        return None
    
    return {
        'symbol': getattr(queue_data, 'symbol', ''),
        'created_at': getattr(queue_data, 'created_at', ''),
        'bid_prices': getattr(queue_data, 'bid_prices', []),
        'bid_volumes': getattr(queue_data, 'bid_volumes', []),
        'bid_orders_count': getattr(queue_data, 'bid_orders_count', []),
        'ask_prices': getattr(queue_data, 'ask_prices', []),
        'ask_volumes': getattr(queue_data, 'ask_volumes', []),
        'ask_orders_count': getattr(queue_data, 'ask_orders_count', []),
        'total_bid_volume': getattr(queue_data, 'total_bid_volume', 0),
        'total_ask_volume': getattr(queue_data, 'total_ask_volume', 0),
        'weighted_bid_price': getattr(queue_data, 'weighted_bid_price', 0),
        'weighted_ask_price': getattr(queue_data, 'weighted_ask_price', 0)
    }

def analyze_l2orders_queue(queue_data_list):
    """分析L2委托队列快照数据"""
    if not queue_data_list:
        return {}
    
    df = pd.DataFrame(queue_data_list)
    
    analysis = {
        'basic_stats': {
            'total_records': len(df),
            'unique_symbols': df['symbol'].nunique() if 'symbol' in df.columns else 0,
            'time_range': {
                'start': df['created_at'].min() if 'created_at' in df.columns else '',
                'end': df['created_at'].max() if 'created_at' in df.columns else ''
            }
        }
    }
    
    if len(df) > 0:
        # 买卖盘统计
        if 'total_bid_volume' in df.columns and df['total_bid_volume'].sum() > 0:
            analysis['bid_stats'] = {
                'total_bid_volume': int(df['total_bid_volume'].sum()),
                'avg_bid_volume': float(df['total_bid_volume'].mean()),
                'max_bid_volume': int(df['total_bid_volume'].max()),
                'min_bid_volume': int(df['total_bid_volume'].min())
            }
        
        if 'total_ask_volume' in df.columns and df['total_ask_volume'].sum() > 0:
            analysis['ask_stats'] = {
                'total_ask_volume': int(df['total_ask_volume'].sum()),
                'avg_ask_volume': float(df['total_ask_volume'].mean()),
                'max_ask_volume': int(df['total_ask_volume'].max()),
                'min_ask_volume': int(df['total_ask_volume'].min())
            }
        
        # 加权价格统计
        if 'weighted_bid_price' in df.columns and df['weighted_bid_price'].sum() > 0:
            analysis['weighted_bid_price_stats'] = {
                'avg_weighted_bid_price': float(df['weighted_bid_price'].mean()),
                'max_weighted_bid_price': float(df['weighted_bid_price'].max()),
                'min_weighted_bid_price': float(df['weighted_bid_price'].min())
            }
        
        if 'weighted_ask_price' in df.columns and df['weighted_ask_price'].sum() > 0:
            analysis['weighted_ask_price_stats'] = {
                'avg_weighted_ask_price': float(df['weighted_ask_price'].mean()),
                'max_weighted_ask_price': float(df['weighted_ask_price'].max()),
                'min_weighted_ask_price': float(df['weighted_ask_price'].min())
            }
        
        # 买卖盘价格档位分析
        bid_prices_analysis = []
        ask_prices_analysis = []
        
        for _, row in df.iterrows():
            if 'bid_prices' in row and row['bid_prices']:
                bid_prices_analysis.extend(row['bid_prices'])
            if 'ask_prices' in row and row['ask_prices']:
                ask_prices_analysis.extend(row['ask_prices'])
        
        if bid_prices_analysis:
            analysis['bid_prices_stats'] = {
                'avg_bid_price': float(sum(bid_prices_analysis) / len(bid_prices_analysis)),
                'max_bid_price': float(max(bid_prices_analysis)),
                'min_bid_price': float(min(bid_prices_analysis)),
                'price_levels': len(set(bid_prices_analysis))
            }
        
        if ask_prices_analysis:
            analysis['ask_prices_stats'] = {
                'avg_ask_price': float(sum(ask_prices_analysis) / len(ask_prices_analysis)),
                'max_ask_price': float(max(ask_prices_analysis)),
                'min_ask_price': float(min(ask_prices_analysis)),
                'price_levels': len(set(ask_prices_analysis))
            }
        
        # 买卖盘量分析
        bid_volumes_analysis = []
        ask_volumes_analysis = []
        
        for _, row in df.iterrows():
            if 'bid_volumes' in row and row['bid_volumes']:
                bid_volumes_analysis.extend(row['bid_volumes'])
            if 'ask_volumes' in row and row['ask_volumes']:
                ask_volumes_analysis.extend(row['ask_volumes'])
        
        if bid_volumes_analysis:
            analysis['bid_volumes_stats'] = {
                'total_bid_volume_detailed': int(sum(bid_volumes_analysis)),
                'avg_bid_volume_per_level': float(sum(bid_volumes_analysis) / len(bid_volumes_analysis)),
                'max_bid_volume_level': int(max(bid_volumes_analysis)),
                'min_bid_volume_level': int(min(bid_volumes_analysis))
            }
        
        if ask_volumes_analysis:
            analysis['ask_volumes_stats'] = {
                'total_ask_volume_detailed': int(sum(ask_volumes_analysis)),
                'avg_ask_volume_per_level': float(sum(ask_volumes_analysis) / len(ask_volumes_analysis)),
                'max_ask_volume_level': int(max(ask_volumes_analysis)),
                'min_ask_volume_level': int(min(ask_volumes_analysis))
            }
        
        # 按股票分组统计
        if 'symbol' in df.columns:
            symbol_stats = df.groupby('symbol').agg({
                'total_bid_volume': 'mean',
                'total_ask_volume': 'mean',
                'weighted_bid_price': 'mean',
                'weighted_ask_price': 'mean'
            }).round(4).to_dict('index')
            analysis['symbol_stats'] = symbol_stats
        
        # 时间分布分析（按小时）
        if 'created_at' in df.columns:
            try:
                df['hour'] = pd.to_datetime(df['created_at']).dt.hour
                hourly_stats = df.groupby('hour').agg({
                    'total_bid_volume': 'mean',
                    'total_ask_volume': 'mean',
                    'weighted_bid_price': 'mean',
                    'weighted_ask_price': 'mean'
                }).to_dict('index')
                analysis['hourly_distribution'] = hourly_stats
            except:
                pass
    
    return analysis

def save_results(queue_data_list, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if queue_data_list:
        # JSON格式
        json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(queue_data_list, f, ensure_ascii=False, indent=2, default=str)
        print(f"数据已保存到: {json_file}")
        
        # CSV格式
        csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
        df = pd.DataFrame(queue_data_list)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"数据已保存到: {csv_file}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

def test_get_history_l2orders_queue():
    """测试get_history_l2orders_queue API"""
    print("=" * 60)
    print("测试 get_history_l2orders_queue API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '获取单只股票L2委托队列快照',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2024-01-15 09:30:00',
                'end_time': '2024-01-15 10:00:00'
            }
        },
        {
            'name': '获取多只股票L2委托队列快照',
            'params': {
                'symbol': 'SZSE.000001,SZSE.000002',
                'start_time': '2024-01-15 14:30:00',
                'end_time': '2024-01-15 15:00:00'
            }
        },
        {
            'name': '获取上海股票的委托队列快照',
            'params': {
                'symbol': 'SHSE.600000',
                'start_time': '2024-01-15 09:30:00',
                'end_time': '2024-01-15 10:00:00'
            }
        },
        {
            'name': '获取短时间窗口的委托队列快照',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2024-01-15 09:30:00',
                'end_time': '2024-01-15 09:35:00'
            }
        },
        {
            'name': '获取开盘时段的委托队列快照',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2024-01-15 09:25:00',
                'end_time': '2024-01-15 09:35:00'
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '测试不存在的股票代码',
            'params': {
                'symbol': 'SZSE.999999',
                'start_time': '2024-01-15 09:30:00',
                'end_time': '2024-01-15 10:00:00'
            }
        },
        {
            'name': '测试未来时间',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2025-12-31 09:30:00',
                'end_time': '2025-12-31 10:00:00'
            }
        },
        {
            'name': '测试过去很久的时间',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2020-01-01 09:30:00',
                'end_time': '2020-01-01 10:00:00'
            }
        },
        {
            'name': '测试无效时间格式',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': 'invalid_time',
                'end_time': '2024-01-15 10:00:00'
            }
        },
        {
            'name': '测试空股票代码',
            'params': {
                'symbol': '',
                'start_time': '2024-01-15 09:30:00',
                'end_time': '2024-01-15 10:00:00'
            }
        },
        {
            'name': '测试非交易时间段',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2024-01-15 12:00:00',
                'end_time': '2024-01-15 13:00:00'
            }
        },
        {
            'name': '测试跨天时间段',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2024-01-15 15:00:00',
                'end_time': '2024-01-16 09:30:00'
            }
        }
    ]
    
    all_cases = test_cases + edge_cases
    
    for i, case in enumerate(all_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"参数: {case['params']}")
        
        try:
            start_time = time.time()
            
            # 调用API
            result = get_history_l2orders_queue(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 转换数据
            queue_data_list = []
            if result:
                if isinstance(result, list):
                    queue_data_list = [l2orders_queue_to_dict(queue_data) for queue_data in result]
                else:
                    queue_data_list = [l2orders_queue_to_dict(result)]
            
            # 分析数据
            analysis = analyze_l2orders_queue(queue_data_list)
            analysis['api_call_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"✓ 成功获取数据")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 记录数: {len(queue_data_list)}")
            
            if analysis.get('basic_stats'):
                stats = analysis['basic_stats']
                print(f"  - 股票数量: {stats.get('unique_symbols', 0)}")
                if stats.get('time_range'):
                    print(f"  - 时间范围: {stats['time_range'].get('start', '')} ~ {stats['time_range'].get('end', '')}")
            
            if analysis.get('bid_stats'):
                bid_stats = analysis['bid_stats']
                print(f"  - 总买盘量: {bid_stats.get('total_bid_volume', 0):,}")
                print(f"  - 平均买盘量: {bid_stats.get('avg_bid_volume', 0):.2f}")
            
            if analysis.get('ask_stats'):
                ask_stats = analysis['ask_stats']
                print(f"  - 总卖盘量: {ask_stats.get('total_ask_volume', 0):,}")
                print(f"  - 平均卖盘量: {ask_stats.get('avg_ask_volume', 0):.2f}")
            
            if analysis.get('weighted_bid_price_stats'):
                bid_price_stats = analysis['weighted_bid_price_stats']
                print(f"  - 平均加权买价: {bid_price_stats.get('avg_weighted_bid_price', 0):.4f}")
            
            if analysis.get('weighted_ask_price_stats'):
                ask_price_stats = analysis['weighted_ask_price_stats']
                print(f"  - 平均加权卖价: {ask_price_stats.get('avg_weighted_ask_price', 0):.4f}")
            
            # 保存结果
            if len(queue_data_list) > 0:
                filename_prefix = f"l2orders_queue_case_{i}_{case['name'].replace(' ', '_')}"
                save_results(queue_data_list, analysis, filename_prefix)
            
        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
            # 记录错误信息
            error_analysis = {
                'error': str(e),
                'api_call_info': {
                    'timestamp': datetime.now().isoformat(),
                    'parameters': case['params']
                }
            }
            filename_prefix = f"l2orders_queue_error_case_{i}"
            save_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("get_history_l2orders_queue API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_get_history_l2orders_queue()