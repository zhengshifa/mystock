#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK 龙虎榜数据查询测试demo

本demo测试以下龙虎榜相关接口：
1. stk_abnor_change_stocks - 查询龙虎榜股票数据
2. stk_abnor_change_detail - 查询龙虎榜营业部数据

注意：运行前需要配置有效的token
"""

import gm
from gm.api import *
import json
import pandas as pd
import os
from datetime import datetime, timedelta

# ============================================================
# Token配置 - 请在运行前配置有效的token
# ============================================================

def configure_token():
    """
    配置GM SDK的token
    支持多种配置方式：
    1. 直接设置token
    2. 从配置文件读取
    3. 从环境变量读取
    """
    
    # 方法1: 直接设置token（不推荐，仅用于测试）
    # set_token('your_token_here')
    
    # 方法2: 从配置文件读取（推荐）
    config_file = 'gm_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'token' in config and config['token']:
                    set_token(config['token'])
                    print(f"已从配置文件 {config_file} 读取token")
                    return True
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    
    # 方法3: 从环境变量读取
    token = os.getenv('GM_TOKEN')
    if token:
        set_token(token)
        print("已从环境变量 GM_TOKEN 读取token")
        return True
    
    print("警告: 未找到有效的token配置")
    print("请通过以下方式之一配置token:")
    print("1. 创建 gm_config.json 文件并设置token")
    print("2. 设置环境变量 GM_TOKEN")
    print("3. 在代码中直接调用 set_token('your_token')")
    return False

def test_dragon_tiger_list():
    """
    测试龙虎榜数据查询接口
    """
    results = {
        'test_info': {
            'test_name': '龙虎榜数据查询测试',
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': '测试龙虎榜股票数据和营业部明细数据查询功能'
        },
        'tests': []
    }
    
    # 获取最近的交易日
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        trading_dates = get_trading_dates('SHSE', start_date, end_date)
        if trading_dates:
            latest_trade_date = trading_dates[-1]
        else:
            latest_trade_date = '2024-01-15'  # 备用日期
    except Exception as e:
        print(f"获取交易日期失败: {e}")
        latest_trade_date = '2024-01-15'  # 备用日期
    
    print(f"使用交易日期: {latest_trade_date}")
    
    # ============================================================
    # 测试1: 查询龙虎榜股票数据
    # ============================================================
    print("\n=== 测试1: 查询龙虎榜股票数据 ===")
    
    test_cases = [
        {
            'name': '查询指定日期龙虎榜股票（所有类型）',
            'params': {
                'trade_date': latest_trade_date,
                'df': False
            }
        },
        {
            'name': '查询指定日期龙虎榜股票（涨跌幅偏离值达7%的证券）',
            'params': {
                'change_types': [1],  # 1: 涨跌幅偏离值达7%的证券
                'trade_date': latest_trade_date,
                'df': False
            }
        },
        {
            'name': '查询指定日期龙虎榜股票（换手率达20%的证券）',
            'params': {
                'change_types': [2],  # 2: 换手率达20%的证券
                'trade_date': latest_trade_date,
                'df': False
            }
        },
        {
            'name': '查询指定股票龙虎榜数据',
            'params': {
                'symbols': ['SHSE.000001', 'SZSE.000002'],
                'trade_date': latest_trade_date,
                'df': False
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试1.{i}: {case['name']}")
        try:
            result = stk_abnor_change_stocks(**case['params'])
            
            test_result = {
                'test_name': case['name'],
                'function': 'stk_abnor_change_stocks',
                'params': case['params'],
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:3] if result and len(result) > 0 else None,
                'result': result
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条龙虎榜股票数据")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    if isinstance(result, list) and len(result) > 0:
                        df = pd.DataFrame(result)
                        csv_filename = f"dragon_tiger_stocks_{case['name'].replace(' ', '_').replace('（', '_').replace('）', '')}.csv"
                        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                        print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到数据")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': case['name'],
                'function': 'stk_abnor_change_stocks',
                'params': case['params'],
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    # ============================================================
    # 测试2: 查询龙虎榜营业部数据
    # ============================================================
    print("\n\n=== 测试2: 查询龙虎榜营业部数据 ===")
    
    test_cases = [
        {
            'name': '查询指定日期龙虎榜营业部数据（所有类型）',
            'params': {
                'trade_date': latest_trade_date,
                'df': False
            }
        },
        {
            'name': '查询指定日期龙虎榜营业部数据（涨跌幅偏离值达7%）',
            'params': {
                'change_types': [1],
                'trade_date': latest_trade_date,
                'df': False
            }
        },
        {
            'name': '查询指定股票龙虎榜营业部数据',
            'params': {
                'symbols': ['SHSE.000001', 'SZSE.000002'],
                'trade_date': latest_trade_date,
                'df': False
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试2.{i}: {case['name']}")
        try:
            result = stk_abnor_change_detail(**case['params'])
            
            test_result = {
                'test_name': case['name'],
                'function': 'stk_abnor_change_detail',
                'params': case['params'],
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:3] if result and len(result) > 0 else None,
                'result': result
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条龙虎榜营业部数据")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    if isinstance(result, list) and len(result) > 0:
                        df = pd.DataFrame(result)
                        csv_filename = f"dragon_tiger_detail_{case['name'].replace(' ', '_').replace('（', '_').replace('）', '')}.csv"
                        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                        print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到数据")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': case['name'],
                'function': 'stk_abnor_change_detail',
                'params': case['params'],
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    return results

def main():
    """
    主函数
    """
    print("掘金量化 GM SDK 龙虎榜数据查询测试")
    print("=" * 50)
    
    # 配置token
    if not configure_token():
        print("\n请先配置有效的token后再运行测试")
        return
    
    # 测试token有效性
    try:
        test_dates = get_trading_dates('SHSE', '2024-01-01', '2024-01-05')
        if not test_dates:
            print("Token验证失败，请检查token是否有效")
            return
        print("Token验证成功")
    except Exception as e:
        print(f"Token验证失败: {e}")
        return
    
    # 运行测试
    try:
        results = test_dragon_tiger_list()
        
        # 保存结果到JSON文件
        output_file = 'demo_7_dragon_tiger_list_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n\n测试完成！结果已保存到: {output_file}")
        
        # 统计测试结果
        total_tests = len(results['tests'])
        success_tests = len([t for t in results['tests'] if t['status'] == 'success'])
        error_tests = len([t for t in results['tests'] if t['status'] == 'error'])
        no_data_tests = len([t for t in results['tests'] if t['status'] == 'no_data'])
        
        print(f"\n测试统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  成功: {success_tests}")
        print(f"  无数据: {no_data_tests}")
        print(f"  失败: {error_tests}")
        print(f"  成功率: {success_tests/total_tests*100:.1f}%")
        
    except Exception as e:
        print(f"测试运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()