#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: get_symbols
获取股票代码列表

功能说明:
- 获取指定交易所或市场的股票代码列表
- 支持多种过滤条件
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
OUTPUT_DIR = 'output/symbols_data'

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

def analyze_symbols(symbols_list):
    """分析股票代码列表"""
    if not symbols_list:
        return {}
    
    analysis = {
        'basic_stats': {
            'total_symbols': len(symbols_list),
            'unique_symbols': len(set(symbols_list))
        }
    }
    
    # 按交易所分类统计
    exchange_stats = {}
    for symbol in symbols_list:
        if '.' in symbol:
            exchange = symbol.split('.')[0]
            exchange_stats[exchange] = exchange_stats.get(exchange, 0) + 1
    
    analysis['exchange_distribution'] = exchange_stats
    
    # 按股票代码前缀分类（主要针对深交所和上交所）
    prefix_stats = {}
    for symbol in symbols_list:
        if '.' in symbol:
            code = symbol.split('.')[1]
            if len(code) >= 3:
                prefix = code[:3]
                prefix_stats[prefix] = prefix_stats.get(prefix, 0) + 1
    
    analysis['code_prefix_distribution'] = prefix_stats
    
    # 按股票代码长度分类
    length_stats = {}
    for symbol in symbols_list:
        if '.' in symbol:
            code = symbol.split('.')[1]
            length = len(code)
            length_stats[length] = length_stats.get(length, 0) + 1
    
    analysis['code_length_distribution'] = length_stats
    
    return analysis

def save_results(symbols_list, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if symbols_list:
        # JSON格式
        json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(symbols_list, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到: {json_file}")
        
        # CSV格式
        csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
        df = pd.DataFrame({'symbol': symbols_list})
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"数据已保存到: {csv_file}")
        
        # TXT格式（每行一个股票代码）
        txt_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            for symbol in symbols_list:
                f.write(f"{symbol}\n")
        print(f"数据已保存到: {txt_file}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

def test_get_symbols():
    """测试get_symbols API"""
    print("=" * 60)
    print("测试 get_symbols API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '获取所有股票代码',
            'params': {}
        },
        {
            'name': '获取深交所股票代码',
            'params': {
                'exchanges': 'SZSE'
            }
        },
        {
            'name': '获取上交所股票代码',
            'params': {
                'exchanges': 'SHSE'
            }
        },
        {
            'name': '获取多个交易所股票代码',
            'params': {
                'exchanges': 'SZSE,SHSE'
            }
        },
        {
            'name': '获取股票类型代码',
            'params': {
                'sec_types': 1  # 股票
            }
        },
        {
            'name': '获取指数类型代码',
            'params': {
                'sec_types': 101  # 指数
            }
        },
        {
            'name': '获取基金类型代码',
            'params': {
                'sec_types': 8  # 基金
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '测试不存在的交易所',
            'params': {
                'exchanges': 'INVALID_EXCHANGE'
            }
        },
        {
            'name': '测试无效的证券类型',
            'params': {
                'sec_types': 999
            }
        },
        {
            'name': '测试空交易所参数',
            'params': {
                'exchanges': ''
            }
        },
        {
            'name': '测试多种证券类型组合',
            'params': {
                'sec_types': '1,8,101'  # 股票、基金、指数
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
            result = get_symbols(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 处理结果
            symbols_list = []
            if result:
                if isinstance(result, list):
                    symbols_list = result
                else:
                    symbols_list = [result]
            
            # 分析数据
            analysis = analyze_symbols(symbols_list)
            analysis['api_call_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"✓ 成功获取数据")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 股票代码数量: {len(symbols_list)}")
            
            if analysis.get('basic_stats'):
                stats = analysis['basic_stats']
                print(f"  - 唯一代码数量: {stats.get('unique_symbols', 0)}")
            
            if analysis.get('exchange_distribution'):
                exchange_dist = analysis['exchange_distribution']
                print(f"  - 交易所分布:")
                for exchange, count in exchange_dist.items():
                    print(f"    {exchange}: {count}")
            
            if analysis.get('code_prefix_distribution'):
                prefix_dist = analysis['code_prefix_distribution']
                print(f"  - 代码前缀分布（前5个）:")
                sorted_prefixes = sorted(prefix_dist.items(), key=lambda x: x[1], reverse=True)[:5]
                for prefix, count in sorted_prefixes:
                    print(f"    {prefix}xxx: {count}")
            
            # 显示部分股票代码示例
            if len(symbols_list) > 0:
                print(f"  - 代码示例（前10个）:")
                for symbol in symbols_list[:10]:
                    print(f"    {symbol}")
                if len(symbols_list) > 10:
                    print(f"    ... 还有 {len(symbols_list) - 10} 个代码")
            
            # 保存结果
            if len(symbols_list) > 0:
                filename_prefix = f"symbols_case_{i}_{case['name'].replace(' ', '_')}"
                save_results(symbols_list, analysis, filename_prefix)
            
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
            filename_prefix = f"symbols_error_case_{i}"
            save_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("get_symbols API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_get_symbols()