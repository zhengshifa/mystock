#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: stk_get_index_constituents
获取指数成分股

功能说明:
- 获取指定指数的成分股列表
- 支持不同时间点的成分股查询
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
OUTPUT_DIR = 'output/index_constituents_data'

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

def convert_constituent_to_dict(constituent_obj):
    """将成分股对象转换为字典"""
    if not constituent_obj:
        return {}
    
    constituent_dict = {}
    
    # 获取对象的所有属性
    for attr in dir(constituent_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(constituent_obj, attr)
                if not callable(value):
                    constituent_dict[attr] = value
            except:
                pass
    
    return constituent_dict

def analyze_constituents(constituents_list, index_symbol, trade_date):
    """分析成分股数据"""
    if not constituents_list:
        return {}
    
    analysis = {
        'basic_stats': {
            'index_symbol': index_symbol,
            'trade_date': trade_date,
            'total_constituents': len(constituents_list),
            'data_timestamp': datetime.now().isoformat()
        }
    }
    
    if constituents_list:
        # 转换为字典列表
        constituents_dicts = []
        for constituent in constituents_list:
            constituent_dict = convert_constituent_to_dict(constituent)
            if constituent_dict:
                constituents_dicts.append(constituent_dict)
        
        analysis['constituents_data'] = constituents_dicts
        
        # 按交易所统计
        exchange_stats = {}
        # 按行业统计（如果有行业信息）
        industry_stats = {}
        # 按权重统计（如果有权重信息）
        weight_stats = []
        
        for constituent_dict in constituents_dicts:
            # 提取symbol中的交易所信息
            symbol = constituent_dict.get('symbol', '')
            if '.' in symbol:
                exchange = symbol.split('.')[0]
                exchange_stats[exchange] = exchange_stats.get(exchange, 0) + 1
            
            # 统计权重信息
            weight = constituent_dict.get('weight', None)
            if weight is not None:
                try:
                    weight_value = float(weight)
                    weight_stats.append(weight_value)
                except:
                    pass
            
            # 统计行业信息
            industry = constituent_dict.get('industry', None) or constituent_dict.get('sector', None)
            if industry:
                industry_stats[industry] = industry_stats.get(industry, 0) + 1
        
        if exchange_stats:
            analysis['exchange_distribution'] = exchange_stats
        
        if industry_stats:
            analysis['industry_distribution'] = industry_stats
        
        if weight_stats:
            analysis['weight_statistics'] = {
                'count': len(weight_stats),
                'min_weight': min(weight_stats),
                'max_weight': max(weight_stats),
                'avg_weight': round(sum(weight_stats) / len(weight_stats), 4),
                'total_weight': round(sum(weight_stats), 4)
            }
        
        # 按symbol前缀统计（股票代码特征）
        symbol_prefix_stats = {}
        for constituent_dict in constituents_dicts:
            symbol = constituent_dict.get('symbol', '')
            if '.' in symbol:
                code = symbol.split('.')[1]
                if len(code) >= 3:
                    prefix = code[:3]
                    symbol_prefix_stats[prefix] = symbol_prefix_stats.get(prefix, 0) + 1
        
        if symbol_prefix_stats:
            analysis['symbol_prefix_distribution'] = symbol_prefix_stats
        
        # 提取所有字段名
        all_fields = set()
        for constituent_dict in constituents_dicts:
            all_fields.update(constituent_dict.keys())
        
        analysis['available_fields'] = sorted(list(all_fields))
    
    return analysis

def save_results(constituents_list, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if constituents_list:
        # 转换为字典列表
        constituents_dicts = []
        for constituent in constituents_list:
            constituent_dict = convert_constituent_to_dict(constituent)
            if constituent_dict:
                constituents_dicts.append(constituent_dict)
        
        if constituents_dicts:
            # JSON格式
            json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(constituents_dicts, f, ensure_ascii=False, indent=2, default=str)
            print(f"数据已保存到: {json_file}")
            
            # CSV格式
            csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
            df = pd.DataFrame(constituents_dicts)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"数据已保存到: {csv_file}")
            
            # Excel格式
            try:
                excel_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.xlsx')
                df.to_excel(excel_file, index=False, engine='openpyxl')
                print(f"数据已保存到: {excel_file}")
            except ImportError:
                print("未安装openpyxl，跳过Excel文件保存")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

def test_stk_get_index_constituents():
    """测试stk_get_index_constituents API"""
    print("=" * 60)
    print("测试 stk_get_index_constituents API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '获取沪深300成分股',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': '2024-01-15'
            }
        },
        {
            'name': '获取中证500成分股',
            'params': {
                'index': 'SHSE.000905',
                'trade_date': '2024-01-15'
            }
        },
        {
            'name': '获取上证50成分股',
            'params': {
                'index': 'SHSE.000016',
                'trade_date': '2024-01-15'
            }
        },
        {
            'name': '获取创业板指成分股',
            'params': {
                'index': 'SZSE.399006',
                'trade_date': '2024-01-15'
            }
        },
        {
            'name': '获取中小板指成分股',
            'params': {
                'index': 'SZSE.399005',
                'trade_date': '2024-01-15'
            }
        },
        {
            'name': '获取科创50成分股',
            'params': {
                'index': 'SHSE.000688',
                'trade_date': '2024-01-15'
            }
        },
        {
            'name': '获取不同日期的沪深300成分股',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': '2023-12-29'
            }
        },
        {
            'name': '获取更早日期的沪深300成分股',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': '2023-06-30'
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '测试不存在的指数',
            'params': {
                'index': 'SHSE.999999',
                'trade_date': '2024-01-15'
            }
        },
        {
            'name': '测试无效日期格式',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': 'invalid_date'
            }
        },
        {
            'name': '测试未来日期',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': '2025-12-31'
            }
        },
        {
            'name': '测试很早的历史日期',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': '2000-01-01'
            }
        },
        {
            'name': '测试周末日期',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': '2024-01-13'  # 周六
            }
        },
        {
            'name': '测试节假日日期',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': '2024-01-01'  # 元旦
            }
        },
        {
            'name': '测试空指数代码',
            'params': {
                'index': '',
                'trade_date': '2024-01-15'
            }
        },
        {
            'name': '测试空日期',
            'params': {
                'index': 'SHSE.000300',
                'trade_date': ''
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
            result = stk_get_index_constituents(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 处理结果
            constituents_list = []
            if result:
                if isinstance(result, list):
                    constituents_list = result
                else:
                    constituents_list = [result]
            
            # 分析数据
            analysis = analyze_constituents(
                constituents_list, 
                case['params'].get('index', ''), 
                case['params'].get('trade_date', '')
            )
            analysis['api_call_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"✓ 成功获取数据")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 成分股数量: {len(constituents_list)}")
            
            if analysis.get('basic_stats'):
                stats = analysis['basic_stats']
                print(f"  - 指数代码: {stats.get('index_symbol', '')}")
                print(f"  - 交易日期: {stats.get('trade_date', '')}")
            
            if analysis.get('exchange_distribution'):
                exchange_dist = analysis['exchange_distribution']
                print(f"  - 交易所分布:")
                for exchange, count in exchange_dist.items():
                    print(f"    {exchange}: {count}")
            
            if analysis.get('weight_statistics'):
                weight_stats = analysis['weight_statistics']
                print(f"  - 权重统计:")
                print(f"    总权重: {weight_stats.get('total_weight', 0)}")
                print(f"    平均权重: {weight_stats.get('avg_weight', 0)}")
                print(f"    最大权重: {weight_stats.get('max_weight', 0)}")
            
            if analysis.get('symbol_prefix_distribution'):
                prefix_dist = analysis['symbol_prefix_distribution']
                print(f"  - 代码前缀分布（前5个）:")
                sorted_prefixes = sorted(prefix_dist.items(), key=lambda x: x[1], reverse=True)[:5]
                for prefix, count in sorted_prefixes:
                    print(f"    {prefix}xxx: {count}")
            
            if analysis.get('available_fields'):
                fields = analysis['available_fields']
                print(f"  - 可用字段: {', '.join(fields[:10])}")
                if len(fields) > 10:
                    print(f"    ... 还有 {len(fields) - 10} 个字段")
            
            # 显示部分成分股示例
            if len(constituents_list) > 0:
                print(f"  - 成分股示例（前5个）:")
                for j, constituent in enumerate(constituents_list[:5]):
                    constituent_dict = convert_constituent_to_dict(constituent)
                    symbol = constituent_dict.get('symbol', 'N/A')
                    weight = constituent_dict.get('weight', 'N/A')
                    print(f"    {j+1}. {symbol} (权重: {weight})")
                if len(constituents_list) > 5:
                    print(f"    ... 还有 {len(constituents_list) - 5} 个成分股")
            
            # 保存结果
            if len(constituents_list) > 0:
                filename_prefix = f"index_constituents_case_{i}_{case['name'].replace(' ', '_')}"
                save_results(constituents_list, analysis, filename_prefix)
            
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
            filename_prefix = f"index_constituents_error_case_{i}"
            save_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("stk_get_index_constituents API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_stk_get_index_constituents()