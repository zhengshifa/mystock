#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GM SDK API Demo: get_trading_session
获取交易时段信息

功能说明:
- 获取指定交易所的交易时段信息
- 支持不同交易所的交易时段查询
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
OUTPUT_DIR = 'output/trading_session_data'

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

def convert_trading_session_to_dict(session_obj):
    """将交易时段对象转换为字典"""
    if not session_obj:
        return {}
    
    session_dict = {}
    
    # 获取对象的所有属性
    for attr in dir(session_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(session_obj, attr)
                if not callable(value):
                    session_dict[attr] = value
            except:
                pass
    
    return session_dict

def analyze_trading_session(session_data, exchange):
    """分析交易时段数据"""
    if not session_data:
        return {}
    
    analysis = {
        'basic_info': {
            'exchange': exchange,
            'total_attributes': len(session_data),
            'data_timestamp': datetime.now().isoformat()
        }
    }
    
    # 分析时间相关的属性
    time_attributes = []
    session_attributes = []
    other_attributes = []
    
    for key, value in session_data.items():
        if 'time' in key.lower() or 'session' in key.lower():
            if 'time' in key.lower():
                time_attributes.append({'key': key, 'value': value})
            else:
                session_attributes.append({'key': key, 'value': value})
        else:
            other_attributes.append({'key': key, 'value': value})
    
    if time_attributes:
        analysis['time_attributes'] = time_attributes
    
    if session_attributes:
        analysis['session_attributes'] = session_attributes
    
    if other_attributes:
        analysis['other_attributes'] = other_attributes
    
    # 尝试解析交易时段
    trading_periods = []
    for key, value in session_data.items():
        if isinstance(value, str) and ':' in str(value):
            # 可能是时间格式
            try:
                # 尝试解析时间格式
                if '-' in str(value) and ':' in str(value):
                    # 可能是时间段格式，如 "09:30-11:30"
                    trading_periods.append({
                        'period_name': key,
                        'time_range': value
                    })
            except:
                pass
    
    if trading_periods:
        analysis['trading_periods'] = trading_periods
        
        # 计算总交易时长
        total_minutes = 0
        for period in trading_periods:
            try:
                time_range = period['time_range']
                if '-' in time_range:
                    start_time, end_time = time_range.split('-')
                    start_hour, start_min = map(int, start_time.split(':'))
                    end_hour, end_min = map(int, end_time.split(':'))
                    
                    start_minutes = start_hour * 60 + start_min
                    end_minutes = end_hour * 60 + end_min
                    
                    if end_minutes > start_minutes:
                        period_minutes = end_minutes - start_minutes
                        total_minutes += period_minutes
                        period['duration_minutes'] = period_minutes
            except:
                pass
        
        if total_minutes > 0:
            analysis['trading_time_summary'] = {
                'total_trading_minutes': total_minutes,
                'total_trading_hours': round(total_minutes / 60, 2),
                'number_of_periods': len(trading_periods)
            }
    
    return analysis

def save_results(session_data, analysis, filename_prefix):
    """保存结果到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存原始数据
    if session_data:
        # JSON格式
        json_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"数据已保存到: {json_file}")
        
        # CSV格式
        try:
            csv_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_data_{timestamp}.csv')
            df = pd.DataFrame([session_data])
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"数据已保存到: {csv_file}")
        except Exception as e:
            print(f"保存CSV文件失败: {e}")
    
    # 保存分析结果
    analysis_file = os.path.join(OUTPUT_DIR, f'{filename_prefix}_analysis_{timestamp}.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    print(f"分析结果已保存到: {analysis_file}")

def test_get_trading_session():
    """测试get_trading_session API"""
    print("=" * 60)
    print("测试 get_trading_session API")
    print("=" * 60)
    
    if not init_gm_api():
        return
    
    # 测试用例
    test_cases = [
        {
            'name': '获取上交所交易时段',
            'params': {
                'exchange': 'SHSE'
            }
        },
        {
            'name': '获取深交所交易时段',
            'params': {
                'exchange': 'SZSE'
            }
        },
        {
            'name': '获取中金所交易时段',
            'params': {
                'exchange': 'CFFEX'
            }
        },
        {
            'name': '获取大商所交易时段',
            'params': {
                'exchange': 'DCE'
            }
        },
        {
            'name': '获取郑商所交易时段',
            'params': {
                'exchange': 'CZCE'
            }
        },
        {
            'name': '获取上期所交易时段',
            'params': {
                'exchange': 'SHFE'
            }
        },
        {
            'name': '获取上海国际能源交易中心交易时段',
            'params': {
                'exchange': 'INE'
            }
        }
    ]
    
    # 边界测试用例
    edge_cases = [
        {
            'name': '测试不存在的交易所',
            'params': {
                'exchange': 'INVALID_EXCHANGE'
            }
        },
        {
            'name': '测试空字符串交易所',
            'params': {
                'exchange': ''
            }
        },
        {
            'name': '测试None交易所',
            'params': {
                'exchange': None
            }
        },
        {
            'name': '测试小写交易所代码',
            'params': {
                'exchange': 'shse'
            }
        },
        {
            'name': '测试混合大小写交易所代码',
            'params': {
                'exchange': 'ShSe'
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
            result = get_trading_session(**case['params'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 处理结果
            session_data = {}
            if result:
                session_data = convert_trading_session_to_dict(result)
            
            # 分析数据
            analysis = analyze_trading_session(
                session_data, 
                case['params'].get('exchange', '')
            )
            analysis['api_call_info'] = {
                'duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'parameters': case['params']
            }
            
            print(f"✓ 成功获取数据")
            print(f"  - 耗时: {duration:.3f}秒")
            print(f"  - 属性数量: {len(session_data)}")
            
            if analysis.get('basic_info'):
                basic_info = analysis['basic_info']
                print(f"  - 交易所: {basic_info.get('exchange', '')}")
                print(f"  - 总属性数: {basic_info.get('total_attributes', 0)}")
            
            # 显示交易时段信息
            if analysis.get('trading_periods'):
                periods = analysis['trading_periods']
                print(f"  - 交易时段:")
                for period in periods:
                    duration_info = f" ({period['duration_minutes']}分钟)" if 'duration_minutes' in period else ""
                    print(f"    {period['period_name']}: {period['time_range']}{duration_info}")
            
            if analysis.get('trading_time_summary'):
                summary = analysis['trading_time_summary']
                print(f"  - 交易时间汇总:")
                print(f"    总交易时长: {summary.get('total_trading_hours', 0)} 小时")
                print(f"    交易时段数: {summary.get('number_of_periods', 0)}")
            
            # 显示时间相关属性
            if analysis.get('time_attributes'):
                time_attrs = analysis['time_attributes']
                print(f"  - 时间相关属性:")
                for attr in time_attrs[:5]:  # 只显示前5个
                    print(f"    {attr['key']}: {attr['value']}")
                if len(time_attrs) > 5:
                    print(f"    ... 还有 {len(time_attrs) - 5} 个时间属性")
            
            # 显示会话相关属性
            if analysis.get('session_attributes'):
                session_attrs = analysis['session_attributes']
                print(f"  - 会话相关属性:")
                for attr in session_attrs[:5]:  # 只显示前5个
                    print(f"    {attr['key']}: {attr['value']}")
                if len(session_attrs) > 5:
                    print(f"    ... 还有 {len(session_attrs) - 5} 个会话属性")
            
            # 显示部分原始数据
            if session_data:
                print(f"  - 原始数据示例（前5个属性）:")
                count = 0
                for key, value in session_data.items():
                    if count >= 5:
                        break
                    print(f"    {key}: {value}")
                    count += 1
                if len(session_data) > 5:
                    print(f"    ... 还有 {len(session_data) - 5} 个属性")
            
            # 保存结果
            if session_data:
                filename_prefix = f"trading_session_case_{i}_{case['name'].replace(' ', '_')}"
                save_results(session_data, analysis, filename_prefix)
            
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
            filename_prefix = f"trading_session_error_case_{i}"
            save_results({}, error_analysis, filename_prefix)
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("get_trading_session API 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_get_trading_session()