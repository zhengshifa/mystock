#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: stk_get_finance_indicator
获取股票财务指标

功能说明:
- 获取股票的财务指标数据
- 支持多股票、多时间段查询
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
OUTPUT_DIR = 'output/finance_indicator_data'

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

def convert_finance_indicator_to_dict(indicator_obj):
    """将财务指标对象转换为字典"""
    if not indicator_obj:
        return {}
    
    indicator_dict = {}
    
    # 获取对象的所有属性
    for attr in dir(indicator_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(indicator_obj, attr)
                if not callable(value):
                    indicator_dict[attr] = value
            except:
                pass
    
    return indicator_dict

def analyze_finance_indicator(indicator_list, symbols, start_date, end_date):
    """分析财务指标数据"""
    if not indicator_list:
        return {}
    
    analysis = {
        'basic_stats': {
            'symbols': symbols if isinstance(symbols, list) else [symbols],
            'start_date': start_date,
            'end_date': end_date,
            'total_records': len(indicator_list),
            'data_timestamp': datetime.now().isoformat()
        }
    }
    
    if indicator_list:
        # 转换为字典列表
        indicator_dicts = []
        for indicator in indicator_list:
            indicator_dict = convert_finance_indicator_to_dict(indicator)
            if indicator_dict:
                indicator_dicts.append(indicator_dict)
        
        analysis['indicator_data'] = indicator_dicts
        
        # 按股票统计
        symbol_stats = {}
        # 按报告期统计
        period_stats = {}
        # 数值字段统计
        numeric_fields = {}
        
        for indicator_dict in indicator_dicts:
            # 股票统计
            symbol = indicator_dict.get('symbol', 'Unknown')
            symbol_stats[symbol] = symbol_stats.get(symbol, 0) + 1
            
            # 报告期统计
            pub_date = indicator_dict.get('pub_date', None) or indicator_dict.get('report_date', None)
            if pub_date:
                period_stats[str(pub_date)] = period_stats.get(str(pub_date), 0) + 1
            
            # 数值字段统计
            for key, value in indicator_dict.items():
                if isinstance(value, (int, float)) and value is not None:
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(value)
        
        analysis['symbol_distribution'] = symbol_stats
        analysis['period_distribution'] = period_stats
        
        # 计算数值字段的统计信息
        numeric_stats = {}
        for field, values in numeric_fields.items():
            if values:
                valid_values = [v for v in values if v != 0]  # 排除0值
                if valid_values:
                    numeric_stats[field] = {
                        'count': len(valid_values),
                        'min': min(valid_values),
                        'max': max(valid_values),
                        'avg': round(sum(valid_values) / len(valid_values), 4),
                        'zero_count': len(values) - len(valid_values)
                    }
        
        analysis['numeric_field_statistics'] = numeric_stats
        
        # 提取所有字段名
        all_fields = set()
        for indicator_dict in indicator_dicts:
            all_fields.update(indicator_dict.keys())
        
        analysis['available_fields'] = sorted(list(all_fields))
        
        # 常见财务指标分析
        common_indicators = {
            'revenue': '营业收入',
            'net_profit': '净利润',
            'total_assets': '总资产',
            'total_equity': '股东权益',
            'operating_cash_flow': '经营现金流',
            'eps': '每股收益',
            'bps': '每股净资产',
            'roe': '净资产收益率',
            'roa': '总资产收益率',
            'debt_ratio': '资产负债率',
            'current_ratio': '流动比率',
            'quick_ratio': '速动比率',
            'gross_margin': '毛利率',
            'net_margin': '净利率',
            'asset_turnover': '资产周转率'
        }
        
        found_indicators = {}
        for field in all_fields:
            field_lower = field.lower()
            for indicator, description in common_indicators.items():
                if indicator in field_lower or any(word in field_lower for word in indicator.split('_')):
                    found_indicators[field] = description
                    break
        
        if found_indicators:
            analysis['common_indicators_found'] = found_indicators
        
        # 按指标类型分类
        indicator_categories = {
            'profitability': ['profit', 'margin', 'roe', 'roa', 'eps'],
            'liquidity': ['current', 'quick', 'cash'],
            'leverage': ['debt', 'equity', 'leverage'],
            'efficiency': ['turnover', 'cycle', 'days'],
            'growth': ['growth', 'rate', 'yoy'],
            'valuation': ['pe', 'pb', 'ps', 'pcf']
        }
        
        categorized_fields = {}
        for category, keywords in indicator_categories.items():
            categorized_fields[category] = []
            for field in all_fields:
                field_lower = field.lower()
                if any(keyword in field_lower for keyword in keywords):
                    categorized_fields[category].append(field)
        
        # 只保留非空的分类
        categorized_fields = {k: v for k, v in categorized_fields.items() if v}
        if categorized_fields:
            analysis['indicator_categories'] = categorized_fields
    
    return analysis

def save_results(indicator_list, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if indicator_list:
        # 转换为字典列表
        indicator_dicts = []
        for indicator in indicator_list:
            indicator_dict = convert_finance_indicator_to_dict(indicator)
            if indicator_dict:
                indicator_dicts.append(indicator_dict)
        
        if indicator_dicts:
            # JSON格式
            json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(indicator_dicts, f, ensure_ascii=False, indent=2, default=str)
            print(f"数据已保存到: {json_file}")
            
            # CSV格式
            csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
            df = pd.DataFrame(indicator_dicts)
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

def test_stk_get_finance_indicator():
    """测试stk_get_finance_indicator API"""
    print("=" * 60)
    print("测试 stk_get_finance_indicator API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '获取单只股票财务指标',
            'params': {
                'symbols': 'SHSE.600000',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '获取多只股票财务指标',
            'params': {
                'symbols': ['SHSE.600000', 'SHSE.600036', 'SZSE.000001'],
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '获取银行股财务指标',
            'params': {
                'symbols': ['SHSE.600000', 'SHSE.600036', 'SHSE.601398', 'SHSE.601939'],
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '获取科技股财务指标',
            'params': {
                'symbols': ['SZSE.000002', 'SHSE.600519', 'SZSE.300059'],
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '获取制造业股票财务指标',
            'params': {
                'symbols': ['SZSE.000858', 'SHSE.600104', 'SZSE.002415'],
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '获取短期数据',
            'params': {
                'symbols': 'SHSE.600000',
                'start_date': '2023-10-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '获取更长时间段数据',
            'params': {
                'symbols': 'SHSE.600000',
                'start_date': '2022-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '获取最新数据',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001'],
                'start_date': '2023-12-01',
                'end_date': '2024-01-31'
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '测试不存在的股票',
            'params': {
                'symbols': 'SHSE.999999',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '测试无效日期格式',
            'params': {
                'symbols': 'SHSE.600000',
                'start_date': 'invalid_date',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '测试开始日期晚于结束日期',
            'params': {
                'symbols': 'SHSE.600000',
                'start_date': '2023-12-31',
                'end_date': '2023-01-01'
            }
        },
        {
            'name': '测试未来日期',
            'params': {
                'symbols': 'SHSE.600000',
                'start_date': '2025-01-01',
                'end_date': '2025-12-31'
            }
        },
        {
            'name': '测试很早的历史日期',
            'params': {
                'symbols': 'SHSE.600000',
                'start_date': '1990-01-01',
                'end_date': '1990-12-31'
            }
        },
        {
            'name': '测试空股票列表',
            'params': {
                'symbols': [],
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '测试空字符串股票',
            'params': {
                'symbols': '',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        },
        {
            'name': '测试单日查询',
            'params': {
                'symbols': 'SHSE.600000',
                'start_date': '2023-12-31',
                'end_date': '2023-12-31'
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
            result = stk_get_finance_indicator(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 处理结果
            indicator_list = []
            if result:
                if isinstance(result, list):
                    indicator_list = result
                else:
                    indicator_list = [result]
            
            # 分析数据
            analysis = analyze_finance_indicator(
                indicator_list, 
                case['params'].get('symbols', ''), 
                case['params'].get('start_date', ''),
                case['params'].get('end_date', '')
            )
            analysis['api_call_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"✓ 成功获取数据")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 记录数量: {len(indicator_list)}")
            
            if analysis.get('basic_stats'):
                stats = analysis['basic_stats']
                symbols = stats.get('symbols', [])
                print(f"  - 查询股票: {', '.join(symbols) if len(symbols) <= 3 else f'{len(symbols)}只股票'}")
                print(f"  - 时间范围: {stats.get('start_date', '')} ~ {stats.get('end_date', '')}")
            
            if analysis.get('symbol_distribution'):
                symbol_dist = analysis['symbol_distribution']
                print(f"  - 股票分布:")
                for symbol, count in list(symbol_dist.items())[:5]:
                    print(f"    {symbol}: {count} 条记录")
                if len(symbol_dist) > 5:
                    print(f"    ... 还有 {len(symbol_dist) - 5} 只股票")
            
            if analysis.get('period_distribution'):
                period_dist = analysis['period_distribution']
                print(f"  - 报告期分布（前5个）:")
                sorted_periods = sorted(period_dist.items())[:5]
                for period, count in sorted_periods:
                    print(f"    {period}: {count} 条记录")
            
            if analysis.get('common_indicators_found'):
                indicators = analysis['common_indicators_found']
                print(f"  - 发现的常见指标:")
                for field, description in list(indicators.items())[:5]:
                    print(f"    {field}: {description}")
                if len(indicators) > 5:
                    print(f"    ... 还有 {len(indicators) - 5} 个指标")
            
            if analysis.get('indicator_categories'):
                categories = analysis['indicator_categories']
                print(f"  - 指标分类:")
                for category, fields in categories.items():
                    print(f"    {category}: {len(fields)} 个指标")
            
            if analysis.get('numeric_field_statistics'):
                numeric_stats = analysis['numeric_field_statistics']
                print(f"  - 数值字段统计（前5个）:")
                count = 0
                for field, stats in numeric_stats.items():
                    if count >= 5:
                        break
                    print(f"    {field}: 平均值 {stats.get('avg', 0)}, 范围 [{stats.get('min', 0)}, {stats.get('max', 0)}]")
                    count += 1
                if len(numeric_stats) > 5:
                    print(f"    ... 还有 {len(numeric_stats) - 5} 个数值字段")
            
            if analysis.get('available_fields'):
                fields = analysis['available_fields']
                print(f"  - 可用字段: {', '.join(fields[:8])}")
                if len(fields) > 8:
                    print(f"    ... 还有 {len(fields) - 8} 个字段")
            
            # 显示部分数据示例
            if len(indicator_list) > 0:
                print(f"  - 数据示例（前3条）:")
                for j, indicator in enumerate(indicator_list[:3]):
                    indicator_dict = convert_finance_indicator_to_dict(indicator)
                    symbol = indicator_dict.get('symbol', 'N/A')
                    pub_date = indicator_dict.get('pub_date', 'N/A')
                    print(f"    {j+1}. {symbol} - {pub_date}")
                if len(indicator_list) > 3:
                    print(f"    ... 还有 {len(indicator_list) - 3} 条记录")
            
            # 保存结果
            if len(indicator_list) > 0:
                filename_prefix = f"finance_indicator_case_{i}_{case['name'].replace(' ', '_')}"
                save_results(indicator_list, analysis, filename_prefix)
            
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
            filename_prefix = f"finance_indicator_error_case_{i}"
            save_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("stk_get_finance_indicator API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_stk_get_finance_indicator()