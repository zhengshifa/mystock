#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: get_history_l2ticks
获取历史L2逐笔成交数据

功能说明:
- 获取指定时间段内的L2逐笔成交数据
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
OUTPUT_DIR = 'output/l2ticks_data'

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

def l2tick_to_dict(tick):
    """将L2Tick对象转换为字典"""
    if tick is None:
        return None
    
    return {
        'symbol': getattr(tick, 'symbol', ''),
        'created_at': getattr(tick, 'created_at', ''),
        'price': getattr(tick, 'price', 0),
        'volume': getattr(tick, 'volume', 0),
        'amount': getattr(tick, 'amount', 0),
        'side': getattr(tick, 'side', 0),  # 1=买入, 2=卖出
        'order_type': getattr(tick, 'order_type', 0),
        'exec_type': getattr(tick, 'exec_type', 0),
        'exec_id': getattr(tick, 'exec_id', ''),
        'ask_order_id': getattr(tick, 'ask_order_id', ''),
        'bid_order_id': getattr(tick, 'bid_order_id', ''),
        'trade_index': getattr(tick, 'trade_index', 0)
    }

def analyze_l2ticks(ticks_data):
    """分析L2逐笔成交数据"""
    if not ticks_data:
        return {}
    
    df = pd.DataFrame(ticks_data)
    
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
        # 交易方向分析
        if 'side' in df.columns:
            side_stats = df['side'].value_counts().to_dict()
            analysis['side_distribution'] = {
                'buy_orders': side_stats.get(1, 0),
                'sell_orders': side_stats.get(2, 0),
                'unknown': side_stats.get(0, 0)
            }
        
        # 价格和成交量统计
        if 'price' in df.columns and df['price'].sum() > 0:
            analysis['price_stats'] = {
                'min_price': float(df['price'].min()),
                'max_price': float(df['price'].max()),
                'avg_price': float(df['price'].mean()),
                'median_price': float(df['price'].median())
            }
        
        if 'volume' in df.columns and df['volume'].sum() > 0:
            analysis['volume_stats'] = {
                'total_volume': int(df['volume'].sum()),
                'avg_volume': float(df['volume'].mean()),
                'max_volume': int(df['volume'].max()),
                'min_volume': int(df['volume'].min())
            }
        
        if 'amount' in df.columns and df['amount'].sum() > 0:
            analysis['amount_stats'] = {
                'total_amount': float(df['amount'].sum()),
                'avg_amount': float(df['amount'].mean()),
                'max_amount': float(df['amount'].max()),
                'min_amount': float(df['amount'].min())
            }
        
        # 订单类型分析
        if 'order_type' in df.columns:
            analysis['order_type_distribution'] = df['order_type'].value_counts().to_dict()
        
        # 执行类型分析
        if 'exec_type' in df.columns:
            analysis['exec_type_distribution'] = df['exec_type'].value_counts().to_dict()
        
        # 按股票分组统计
        if 'symbol' in df.columns:
            symbol_stats = df.groupby('symbol').agg({
                'volume': 'sum',
                'amount': 'sum',
                'price': 'mean'
            }).round(4).to_dict('index')
            analysis['symbol_stats'] = symbol_stats
    
    return analysis

def save_results(ticks_data, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if ticks_data:
        # JSON格式
        json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(ticks_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"数据已保存到: {json_file}")
        
        # CSV格式
        csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
        df = pd.DataFrame(ticks_data)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"数据已保存到: {csv_file}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

def test_get_history_l2ticks():
    """测试get_history_l2ticks API"""
    print("=" * 60)
    print("测试 get_history_l2ticks API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '获取单只股票L2逐笔数据',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2024-01-15 09:30:00',
                'end_time': '2024-01-15 10:00:00'
            }
        },
        {
            'name': '获取多只股票L2逐笔数据',
            'params': {
                'symbol': 'SZSE.000001,SZSE.000002',
                'start_time': '2024-01-15 14:30:00',
                'end_time': '2024-01-15 15:00:00'
            }
        },
        {
            'name': '获取指定交易方向的数据',
            'params': {
                'symbol': 'SZSE.000001',
                'start_time': '2024-01-15 09:30:00',
                'end_time': '2024-01-15 09:45:00',
                'side': 1  # 只获取买入数据
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
        }
    ]
    
    all_cases = test_cases + edge_cases
    
    for i, case in enumerate(all_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"参数: {case['params']}")
        
        try:
            start_time = time.time()
            
            # 调用API
            result = get_history_l2ticks(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 转换数据
            ticks_data = []
            if result:
                if isinstance(result, list):
                    ticks_data = [l2tick_to_dict(tick) for tick in result]
                else:
                    ticks_data = [l2tick_to_dict(result)]
            
            # 分析数据
            analysis = analyze_l2ticks(ticks_data)
            analysis['api_call_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"✓ 成功获取数据")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 记录数: {len(ticks_data)}")
            
            if analysis.get('basic_stats'):
                stats = analysis['basic_stats']
                print(f"  - 股票数量: {stats.get('unique_symbols', 0)}")
                if stats.get('time_range'):
                    print(f"  - 时间范围: {stats['time_range'].get('start', '')} ~ {stats['time_range'].get('end', '')}")
            
            if analysis.get('side_distribution'):
                side_dist = analysis['side_distribution']
                print(f"  - 买入笔数: {side_dist.get('buy_orders', 0)}")
                print(f"  - 卖出笔数: {side_dist.get('sell_orders', 0)}")
            
            if analysis.get('volume_stats'):
                vol_stats = analysis['volume_stats']
                print(f"  - 总成交量: {vol_stats.get('total_volume', 0):,}")
                print(f"  - 平均成交量: {vol_stats.get('avg_volume', 0):.2f}")
            
            if analysis.get('amount_stats'):
                amt_stats = analysis['amount_stats']
                print(f"  - 总成交额: {amt_stats.get('total_amount', 0):,.2f}")
                print(f"  - 平均成交额: {amt_stats.get('avg_amount', 0):.2f}")
            
            # 保存结果
            if len(ticks_data) > 0:
                filename_prefix = f"l2ticks_case_{i}_{case['name'].replace(' ', '_')}"
                save_results(ticks_data, analysis, filename_prefix)
            
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
            filename_prefix = f"l2ticks_error_case_{i}"
            save_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("get_history_l2ticks API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_get_history_l2ticks()