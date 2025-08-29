#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: get_previous_n_trading_dates
获取前N个交易日

功能说明:
- 获取指定日期前N个交易日的日期列表
- 支持不同交易所的交易日历
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
OUTPUT_DIR = 'output/previous_trading_dates_data'

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

def analyze_trading_dates(dates_list, reference_date, n_days):
    """分析交易日期数据"""
    if not dates_list:
        return {}
    
    analysis = {
        'basic_stats': {
            'total_dates': len(dates_list),
            'requested_days': n_days,
            'reference_date': reference_date,
            'date_range': {
                'start': min(dates_list) if dates_list else '',
                'end': max(dates_list) if dates_list else ''
            }
        }
    }
    
    if dates_list:
        # 日期连续性分析
        sorted_dates = sorted(dates_list)
        date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in sorted_dates]
        
        # 计算日期间隔
        intervals = []
        for i in range(1, len(date_objects)):
            interval = (date_objects[i] - date_objects[i-1]).days
            intervals.append(interval)
        
        if intervals:
            analysis['date_intervals'] = {
                'min_interval': min(intervals),
                'max_interval': max(intervals),
                'avg_interval': round(sum(intervals) / len(intervals), 2),
                'most_common_interval': max(set(intervals), key=intervals.count)
            }
        
        # 按星期几统计
        weekday_stats = {}
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for date_obj in date_objects:
            weekday = date_obj.weekday()
            weekday_name = weekday_names[weekday]
            weekday_stats[weekday_name] = weekday_stats.get(weekday_name, 0) + 1
        
        analysis['weekday_distribution'] = weekday_stats
        
        # 按月份统计
        month_stats = {}
        for date_obj in date_objects:
            month = date_obj.strftime('%Y-%m')
            month_stats[month] = month_stats.get(month, 0) + 1
        
        analysis['monthly_distribution'] = month_stats
        
        # 计算与参考日期的实际天数差
        if reference_date:
            try:
                ref_date_obj = datetime.strptime(reference_date, '%Y-%m-%d')
                if date_objects:
                    earliest_date = min(date_objects)
                    latest_date = max(date_objects)
                    
                    analysis['date_span_analysis'] = {
                        'days_from_reference_to_earliest': (ref_date_obj - earliest_date).days,
                        'days_from_reference_to_latest': (ref_date_obj - latest_date).days,
                        'total_calendar_days_span': (latest_date - earliest_date).days + 1
                    }
            except:
                pass
    
    return analysis

def save_results(dates_list, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if dates_list:
        # JSON格式
        json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dates_list, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到: {json_file}")
        
        # CSV格式
        csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
        df = pd.DataFrame({'trading_date': dates_list})
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"数据已保存到: {csv_file}")
        
        # TXT格式（每行一个日期）
        txt_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            for date in dates_list:
                f.write(f"{date}\n")
        print(f"数据已保存到: {txt_file}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

def test_get_previous_n_trading_dates():
    """测试get_previous_n_trading_dates API"""
    print("=" * 60)
    print("测试 get_previous_n_trading_dates API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '获取前5个交易日',
            'params': {
                'date': '2024-01-15',
                'n': 5
            }
        },
        {
            'name': '获取前10个交易日',
            'params': {
                'date': '2024-01-15',
                'n': 10
            }
        },
        {
            'name': '获取前20个交易日',
            'params': {
                'date': '2024-01-15',
                'n': 20
            }
        },
        {
            'name': '获取前1个交易日',
            'params': {
                'date': '2024-01-15',
                'n': 1
            }
        },
        {
            'name': '获取前50个交易日',
            'params': {
                'date': '2024-06-15',
                'n': 50
            }
        },
        {
            'name': '指定深交所交易日历',
            'params': {
                'date': '2024-01-15',
                'n': 10,
                'exchange': 'SZSE'
            }
        },
        {
            'name': '指定上交所交易日历',
            'params': {
                'date': '2024-01-15',
                'n': 10,
                'exchange': 'SHSE'
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '测试n=0的情况',
            'params': {
                'date': '2024-01-15',
                'n': 0
            }
        },
        {
            'name': '测试负数n的情况',
            'params': {
                'date': '2024-01-15',
                'n': -5
            }
        },
        {
            'name': '测试很大的n值',
            'params': {
                'date': '2024-01-15',
                'n': 1000
            }
        },
        {
            'name': '测试无效日期格式',
            'params': {
                'date': 'invalid_date',
                'n': 5
            }
        },
        {
            'name': '测试未来日期',
            'params': {
                'date': '2025-12-31',
                'n': 5
            }
        },
        {
            'name': '测试很早的历史日期',
            'params': {
                'date': '1990-01-01',
                'n': 5
            }
        },
        {
            'name': '测试周末日期',
            'params': {
                'date': '2024-01-13',  # 周六
                'n': 5
            }
        },
        {
            'name': '测试节假日日期',
            'params': {
                'date': '2024-01-01',  # 元旦
                'n': 5
            }
        },
        {
            'name': '测试不存在的交易所',
            'params': {
                'date': '2024-01-15',
                'n': 5,
                'exchange': 'INVALID_EXCHANGE'
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
            result = get_previous_n_trading_dates(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 处理结果
            dates_list = []
            if result:
                if isinstance(result, list):
                    dates_list = result
                else:
                    dates_list = [result]
            
            # 分析数据
            analysis = analyze_trading_dates(
                dates_list, 
                case['params'].get('date', ''), 
                case['params'].get('n', 0)
            )
            analysis['api_call_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"✓ 成功获取数据")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 交易日数量: {len(dates_list)}")
            
            if analysis.get('basic_stats'):
                stats = analysis['basic_stats']
                print(f"  - 请求天数: {stats.get('requested_days', 0)}")
                print(f"  - 参考日期: {stats.get('reference_date', '')}")
                if stats.get('date_range'):
                    print(f"  - 日期范围: {stats['date_range'].get('start', '')} ~ {stats['date_range'].get('end', '')}")
            
            if analysis.get('date_intervals'):
                intervals = analysis['date_intervals']
                print(f"  - 平均间隔: {intervals.get('avg_interval', 0)} 天")
                print(f"  - 最常见间隔: {intervals.get('most_common_interval', 0)} 天")
            
            if analysis.get('weekday_distribution'):
                weekday_dist = analysis['weekday_distribution']
                print(f"  - 星期分布:")
                for weekday, count in weekday_dist.items():
                    print(f"    {weekday}: {count}")
            
            # 显示部分日期示例
            if len(dates_list) > 0:
                print(f"  - 日期示例（前10个）:")
                for date in dates_list[:10]:
                    print(f"    {date}")
                if len(dates_list) > 10:
                    print(f"    ... 还有 {len(dates_list) - 10} 个日期")
            
            # 保存结果
            if len(dates_list) > 0:
                filename_prefix = f"previous_trading_dates_case_{i}_{case['name'].replace(' ', '_')}"
                save_results(dates_list, analysis, filename_prefix)
            
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
            filename_prefix = f"previous_trading_dates_error_case_{i}"
            save_results([], error_analysis, filename_prefix)
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("get_previous_n_trading_dates API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_get_previous_n_trading_dates()