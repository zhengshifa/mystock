#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: stk_get_multi_symbols_trading_info
获取多股票交易信息

功能说明:
- 获取多只股票的交易信息
- 支持批量查询股票的交易状态、涨跌停价格等信息
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
OUTPUT_DIR = 'output/multi_symbols_trading_info_data'

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

def convert_trading_info_to_dict(trading_info_obj):
    """将交易信息对象转换为字典"""
    if not trading_info_obj:
        return {}
    
    trading_info_dict = {}
    
    # 获取对象的所有属性
    for attr in dir(trading_info_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(trading_info_obj, attr)
                if not callable(value):
                    trading_info_dict[attr] = value
            except:
                pass
    
    return trading_info_dict

def analyze_multi_symbols_trading_info(trading_info_list, symbols, date):
    """分析多股票交易信息数据"""
    if not trading_info_list:
        return {}
    
    analysis = {
        'basic_stats': {
            'symbols': symbols if isinstance(symbols, list) else [symbols],
            'date': date,
            'total_records': len(trading_info_list),
            'data_timestamp': datetime.now().isoformat()
        }
    }
    
    if trading_info_list:
        # 转换为字典列表
        trading_info_dicts = []
        for trading_info in trading_info_list:
            trading_info_dict = convert_trading_info_to_dict(trading_info)
            if trading_info_dict:
                trading_info_dicts.append(trading_info_dict)
        
        analysis['trading_info_data'] = trading_info_dicts
        
        # 按股票统计
        symbol_stats = {}
        # 按交易所统计
        exchange_stats = {}
        # 交易状态统计
        trading_status_stats = {}
        # 涨跌停统计
        limit_stats = {'up_limit': 0, 'down_limit': 0, 'normal': 0}
        # 数值字段统计
        numeric_fields = {}
        
        for trading_info_dict in trading_info_dicts:
            # 股票统计
            symbol = trading_info_dict.get('symbol', 'Unknown')
            symbol_stats[symbol] = symbol_stats.get(symbol, 0) + 1
            
            # 交易所统计
            if '.' in symbol:
                exchange = symbol.split('.')[0]
                exchange_stats[exchange] = exchange_stats.get(exchange, 0) + 1
            
            # 交易状态统计
            trading_status = trading_info_dict.get('trading_status', 'Unknown')
            trading_status_stats[str(trading_status)] = trading_status_stats.get(str(trading_status), 0) + 1
            
            # 涨跌停统计
            upper_limit = trading_info_dict.get('upper_limit', None)
            lower_limit = trading_info_dict.get('lower_limit', None)
            current_price = trading_info_dict.get('price', None) or trading_info_dict.get('close', None)
            
            if upper_limit and lower_limit and current_price:
                if abs(current_price - upper_limit) < 0.01:
                    limit_stats['up_limit'] += 1
                elif abs(current_price - lower_limit) < 0.01:
                    limit_stats['down_limit'] += 1
                else:
                    limit_stats['normal'] += 1
            
            # 数值字段统计
            for key, value in trading_info_dict.items():
                if isinstance(value, (int, float)) and value is not None:
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(value)
        
        analysis['symbol_distribution'] = symbol_stats
        analysis['exchange_distribution'] = exchange_stats
        analysis['trading_status_distribution'] = trading_status_stats
        analysis['limit_price_statistics'] = limit_stats
        
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
        for trading_info_dict in trading_info_dicts:
            all_fields.update(trading_info_dict.keys())
        
        analysis['available_fields'] = sorted(list(all_fields))
        
        # 价格相关字段分析
        price_fields = []
        volume_fields = []
        limit_fields = []
        
        for field in all_fields:
            field_lower = field.lower()
            if any(keyword in field_lower for keyword in ['price', 'close', 'open', 'high', 'low']):
                price_fields.append(field)
            elif any(keyword in field_lower for keyword in ['volume', 'amount', 'turnover']):
                volume_fields.append(field)
            elif any(keyword in field_lower for keyword in ['limit', 'upper', 'lower']):
                limit_fields.append(field)
        
        field_categories = {}
        if price_fields:
            field_categories['price_fields'] = price_fields
        if volume_fields:
            field_categories['volume_fields'] = volume_fields
        if limit_fields:
            field_categories['limit_fields'] = limit_fields
        
        if field_categories:
            analysis['field_categories'] = field_categories
        
        # 市场表现分析
        if numeric_stats:
            market_performance = {}
            
            # 涨跌幅分析
            if 'change_pct' in numeric_stats:
                change_stats = numeric_stats['change_pct']
                market_performance['change_percentage'] = {
                    'avg_change': change_stats.get('avg', 0),
                    'max_gain': change_stats.get('max', 0),
                    'max_loss': change_stats.get('min', 0)
                }
            
            # 成交量分析
            volume_field = None
            for field in ['volume', 'vol', 'trade_volume']:
                if field in numeric_stats:
                    volume_field = field
                    break
            
            if volume_field:
                volume_stats = numeric_stats[volume_field]
                market_performance['volume_analysis'] = {
                    'avg_volume': volume_stats.get('avg', 0),
                    'max_volume': volume_stats.get('max', 0),
                    'min_volume': volume_stats.get('min', 0)
                }
            
            if market_performance:
                analysis['market_performance'] = market_performance
    
    return analysis

def save_results(trading_info_list, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if trading_info_list:
        # 转换为字典列表
        trading_info_dicts = []
        for trading_info in trading_info_list:
            trading_info_dict = convert_trading_info_to_dict(trading_info)
            if trading_info_dict:
                trading_info_dicts.append(trading_info_dict)
        
        if trading_info_dicts:
            # JSON格式
            json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(trading_info_dicts, f, ensure_ascii=False, indent=2, default=str)
            print(f"数据已保存到: {json_file}")
            
            # CSV格式
            csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
            df = pd.DataFrame(trading_info_dicts)
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

def test_stk_get_multi_symbols_trading_info():
    """测试stk_get_multi_symbols_trading_info API"""
    print("=" * 60)
    print("测试 stk_get_multi_symbols_trading_info API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '获取少量股票交易信息',
            'params': {
                'symbols': ['SHSE.600000', 'SHSE.600036', 'SZSE.000001'],
                'date': '2023-12-29'
            }
        },
        {
            'name': '获取银行股交易信息',
            'params': {
                'symbols': ['SHSE.600000', 'SHSE.600036', 'SHSE.601398', 'SHSE.601939', 'SHSE.601988'],
                'date': '2023-12-29'
            }
        },
        {
            'name': '获取科技股交易信息',
            'params': {
                'symbols': ['SZSE.000002', 'SHSE.600519', 'SZSE.300059', 'SZSE.300750', 'SHSE.688981'],
                'date': '2023-12-29'
            }
        },
        {
            'name': '获取不同交易所股票信息',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001', 'SZSE.300001', 'SHSE.688001'],
                'date': '2023-12-29'
            }
        },
        {
            'name': '获取更多股票交易信息',
            'params': {
                'symbols': [
                    'SHSE.600000', 'SHSE.600036', 'SHSE.600519', 'SHSE.601398',
                    'SZSE.000001', 'SZSE.000002', 'SZSE.300059', 'SZSE.300750'
                ],
                'date': '2023-12-29'
            }
        },
        {
            'name': '获取指定日期交易信息',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001'],
                'date': '2023-11-30'
            }
        },
        {
            'name': '获取最近交易日信息',
            'params': {
                'symbols': ['SHSE.600000', 'SHSE.600036', 'SZSE.000001'],
                'date': '2024-01-02'
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '测试单只股票',
            'params': {
                'symbols': ['SHSE.600000'],
                'date': '2023-12-29'
            }
        },
        {
            'name': '测试不存在的股票',
            'params': {
                'symbols': ['SHSE.999999', 'SZSE.999999'],
                'date': '2023-12-29'
            }
        },
        {
            'name': '测试混合存在和不存在的股票',
            'params': {
                'symbols': ['SHSE.600000', 'SHSE.999999', 'SZSE.000001'],
                'date': '2023-12-29'
            }
        },
        {
            'name': '测试无效日期格式',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001'],
                'date': 'invalid_date'
            }
        },
        {
            'name': '测试未来日期',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001'],
                'date': '2025-12-31'
            }
        },
        {
            'name': '测试很早的历史日期',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001'],
                'date': '1990-01-01'
            }
        },
        {
            'name': '测试周末日期',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001'],
                'date': '2023-12-30'  # 周六
            }
        },
        {
            'name': '测试节假日日期',
            'params': {
                'symbols': ['SHSE.600000', 'SZSE.000001'],
                'date': '2023-10-01'  # 国庆节
            }
        },
        {
            'name': '测试空股票列表',
            'params': {
                'symbols': [],
                'date': '2023-12-29'
            }
        },
        {
            'name': '测试无效股票代码格式',
            'params': {
                'symbols': ['600000', 'invalid_symbol'],
                'date': '2023-12-29'
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
            result = stk_get_multi_symbols_trading_info(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 处理结果
            trading_info_list = []
            if result:
                if isinstance(result, list):
                    trading_info_list = result
                else:
                    trading_info_list = [result]
            
            # 分析数据
            analysis = analyze_multi_symbols_trading_info(
                trading_info_list, 
                case['params'].get('symbols', []), 
                case['params'].get('date', '')
            )
            analysis['api_call_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"✓ 成功获取数据")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 记录数量: {len(trading_info_list)}")
            
            if analysis.get('basic_stats'):
                stats = analysis['basic_stats']
                symbols = stats.get('symbols', [])
                print(f"  - 查询股票: {len(symbols)}只")
                print(f"  - 查询日期: {stats.get('date', '')}")
            
            if analysis.get('symbol_distribution'):
                symbol_dist = analysis['symbol_distribution']
                print(f"  - 成功获取数据的股票: {len(symbol_dist)}只")
                for symbol, count in list(symbol_dist.items())[:5]:
                    print(f"    {symbol}: {count} 条记录")
                if len(symbol_dist) > 5:
                    print(f"    ... 还有 {len(symbol_dist) - 5} 只股票")
            
            if analysis.get('exchange_distribution'):
                exchange_dist = analysis['exchange_distribution']
                print(f"  - 交易所分布:")
                for exchange, count in exchange_dist.items():
                    print(f"    {exchange}: {count} 只股票")
            
            if analysis.get('trading_status_distribution'):
                status_dist = analysis['trading_status_distribution']
                print(f"  - 交易状态分布:")
                for status, count in status_dist.items():
                    print(f"    {status}: {count} 只股票")
            
            if analysis.get('limit_price_statistics'):
                limit_stats = analysis['limit_price_statistics']
                print(f"  - 涨跌停统计:")
                print(f"    涨停: {limit_stats.get('up_limit', 0)} 只")
                print(f"    跌停: {limit_stats.get('down_limit', 0)} 只")
                print(f"    正常: {limit_stats.get('normal', 0)} 只")
            
            if analysis.get('field_categories'):
                categories = analysis['field_categories']
                print(f"  - 字段分类:")
                for category, fields in categories.items():
                    print(f"    {category}: {len(fields)} 个字段")
            
            if analysis.get('market_performance'):
                performance = analysis['market_performance']
                print(f"  - 市场表现:")
                if 'change_percentage' in performance:
                    change = performance['change_percentage']
                    print(f"    平均涨跌幅: {change.get('avg_change', 0):.2f}%")
                    print(f"    最大涨幅: {change.get('max_gain', 0):.2f}%")
                    print(f"    最大跌幅: {change.get('max_loss', 0):.2f}%")
            
            if analysis.get('available_fields'):
                fields = analysis['available_fields']
                print(f"  - 可用字段: {', '.join(fields[:8])}")
                if len(fields) > 8:
                    print(f"    ... 还有 {len(fields) - 8} 个字段")
            
            # 显示部分数据示例
            if len(trading_info_list) > 0:
                print(f"  - 数据示例（前3条）:")
                for j, trading_info in enumerate(trading_info_list[:3]):
                    trading_info_dict = convert_trading_info_to_dict(trading_info)
                    symbol = trading_info_dict.get('symbol', 'N/A')
                    price = trading_info_dict.get('price', 'N/A') or trading_info_dict.get('close', 'N/A')
                    print(f"    {j+1}. {symbol} - 价格: {price}")
                if len(trading_info_list) > 3:
                    print(f"    ... 还有 {len(trading_info_list) - 3} 条记录")
            
            # 保存结果
            if len(trading_info_list) > 0:
                filename_prefix = f"multi_symbols_trading_info_case_{i}_{case['name'].replace(' ', '_')}"
                save_results(trading_info_list, analysis, filename_prefix)
            
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
            filename_prefix = f"multi_symbols_trading_info_error_case_{i}"
            save_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("stk_get_multi_symbols_trading_info API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_stk_get_multi_symbols_trading_info()