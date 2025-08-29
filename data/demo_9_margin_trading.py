#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK 融资融券数据查询测试demo

本demo测试以下融资融券相关接口：
1. credit_get_borrowable_instruments - 查询可融券标的股票列表
2. credit_get_borrowable_instruments_positions - 查询券商融券账户头寸
3. credit_get_cash - 查询融资融券资金
4. credit_get_collateral_instruments - 查询担保证券列表
5. credit_get_contracts - 查询融资融券合约
6. credit_buying_on_margin - 融资买入
7. credit_selling_short - 融券卖出
8. credit_repay_cash_directly - 直接还款
9. credit_repay_stock_directly - 直接还券

注意：运行前需要配置有效的token，且需要有融资融券权限
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

def test_margin_trading_data():
    """
    测试融资融券数据查询接口
    """
    results = {
        'test_info': {
            'test_name': '融资融券数据查询测试',
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': '测试融资融券相关数据查询功能'
        },
        'tests': []
    }
    
    # ============================================================
    # 测试1: 查询可融券标的股票列表
    # ============================================================
    print("\n=== 测试1: 查询可融券标的股票列表 ===")
    
    test_cases = [
        {
            'name': '查询可融券标的股票列表（券商自有）',
            'function': 'credit_get_borrowable_instruments',
            'params': {
                'position_src': 1,  # 1: 券商自有
                'df': False
            }
        },
        {
            'name': '查询可融券标的股票列表（专项资管）',
            'function': 'credit_get_borrowable_instruments',
            'params': {
                'position_src': 2,  # 2: 专项资管
                'df': False
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试1.{i}: {case['name']}")
        try:
            if case['function'] == 'credit_get_borrowable_instruments':
                result = credit_get_borrowable_instruments(**case['params'])
            
            test_result = {
                'test_name': case['name'],
                'function': case['function'],
                'params': case['params'],
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:3] if result and len(result) > 0 else None,
                'result': result
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条可融券标的数据")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    if isinstance(result, list) and len(result) > 0:
                        df = pd.DataFrame(result)
                        csv_filename = f"borrowable_instruments_{case['name'].replace(' ', '_').replace('（', '_').replace('）', '')}.csv"
                        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                        print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到数据")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': case['name'],
                'function': case['function'],
                'params': case['params'],
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    # ============================================================
    # 测试2: 查询券商融券账户头寸
    # ============================================================
    print("\n\n=== 测试2: 查询券商融券账户头寸 ===")
    
    test_cases = [
        {
            'name': '查询券商自有融券头寸',
            'function': 'credit_get_borrowable_instruments_positions',
            'params': {
                'position_src': 1,  # 1: 券商自有
                'df': False
            }
        },
        {
            'name': '查询专项资管融券头寸',
            'function': 'credit_get_borrowable_instruments_positions',
            'params': {
                'position_src': 2,  # 2: 专项资管
                'df': False
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试2.{i}: {case['name']}")
        try:
            if case['function'] == 'credit_get_borrowable_instruments_positions':
                result = credit_get_borrowable_instruments_positions(**case['params'])
            
            test_result = {
                'test_name': case['name'],
                'function': case['function'],
                'params': case['params'],
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:3] if result and len(result) > 0 else None,
                'result': result
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条融券头寸数据")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    if isinstance(result, list) and len(result) > 0:
                        df = pd.DataFrame(result)
                        csv_filename = f"borrowable_positions_{case['name'].replace(' ', '_')}.csv"
                        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                        print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到数据")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': case['name'],
                'function': case['function'],
                'params': case['params'],
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    # ============================================================
    # 测试3: 查询融资融券资金
    # ============================================================
    print("\n\n=== 测试3: 查询融资融券资金 ===")
    
    print(f"\n测试3.1: 查询融资融券资金")
    try:
        result = credit_get_cash()
        
        test_result = {
            'test_name': '查询融资融券资金',
            'function': 'credit_get_cash',
            'params': {},
            'status': 'success' if result else 'no_data',
            'result': result
        }
        
        if result:
            print(f"  ✓ 成功获取融资融券资金信息")
            print(f"  资金信息: {result}")
        else:
            print(f"  ⚠ 未获取到资金信息")
            
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        test_result = {
            'test_name': '查询融资融券资金',
            'function': 'credit_get_cash',
            'params': {},
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试4: 查询担保证券列表
    # ============================================================
    print("\n\n=== 测试4: 查询担保证券列表 ===")
    
    print(f"\n测试4.1: 查询担保证券列表")
    try:
        result = credit_get_collateral_instruments(df=False)
        
        test_result = {
            'test_name': '查询担保证券列表',
            'function': 'credit_get_collateral_instruments',
            'params': {'df': False},
            'status': 'success' if result else 'no_data',
            'result_count': len(result) if result else 0,
            'sample_data': result[:3] if result and len(result) > 0 else None,
            'result': result
        }
        
        if result:
            print(f"  ✓ 成功获取 {len(result)} 条担保证券数据")
            if len(result) > 0:
                print(f"  示例数据: {result[0]}")
                
                # 保存到CSV
                if isinstance(result, list) and len(result) > 0:
                    df = pd.DataFrame(result)
                    csv_filename = "collateral_instruments.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  数据已保存到: {csv_filename}")
        else:
            print(f"  ⚠ 未获取到数据")
            
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        test_result = {
            'test_name': '查询担保证券列表',
            'function': 'credit_get_collateral_instruments',
            'params': {'df': False},
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试5: 查询融资融券合约
    # ============================================================
    print("\n\n=== 测试5: 查询融资融券合约 ===")
    
    test_cases = [
        {
            'name': '查询融资合约',
            'function': 'credit_get_contracts',
            'params': {
                'position_src': 1,  # 1: 券商自有
                'df': False
            }
        },
        {
            'name': '查询融券合约',
            'function': 'credit_get_contracts',
            'params': {
                'position_src': 2,  # 2: 专项资管
                'df': False
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试5.{i}: {case['name']}")
        try:
            if case['function'] == 'credit_get_contracts':
                result = credit_get_contracts(**case['params'])
            
            test_result = {
                'test_name': case['name'],
                'function': case['function'],
                'params': case['params'],
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:3] if result and len(result) > 0 else None,
                'result': result
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条合约数据")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    if isinstance(result, list) and len(result) > 0:
                        df = pd.DataFrame(result)
                        csv_filename = f"credit_contracts_{case['name'].replace(' ', '_')}.csv"
                        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                        print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到数据")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': case['name'],
                'function': case['function'],
                'params': case['params'],
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    # ============================================================
    # 测试6: 融资融券交易接口（仅测试接口可用性，不实际下单）
    # ============================================================
    print("\n\n=== 测试6: 融资融券交易接口测试 ===")
    print("注意：以下测试仅验证接口可用性，不会实际执行交易")
    
    # 这些接口需要实际的交易权限，这里只测试接口是否存在
    trading_functions = [
        'credit_buying_on_margin',
        'credit_selling_short', 
        'credit_repay_cash_directly',
        'credit_repay_stock_directly'
    ]
    
    for func_name in trading_functions:
        print(f"\n测试6.x: 检查 {func_name} 接口")
        try:
            # 检查函数是否存在
            func = globals().get(func_name)
            if func and callable(func):
                print(f"  ✓ {func_name} 接口可用")
                test_result = {
                    'test_name': f'检查{func_name}接口',
                    'function': func_name,
                    'status': 'interface_available',
                    'note': '接口存在但未实际调用（需要交易权限）'
                }
            else:
                print(f"  ✗ {func_name} 接口不存在")
                test_result = {
                    'test_name': f'检查{func_name}接口',
                    'function': func_name,
                    'status': 'interface_not_found'
                }
        except Exception as e:
            print(f"  ✗ 检查 {func_name} 失败: {e}")
            test_result = {
                'test_name': f'检查{func_name}接口',
                'function': func_name,
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    return results

def main():
    """
    主函数
    """
    print("掘金量化 GM SDK 融资融券数据查询测试")
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
    
    print("\n重要提示：")
    print("- 融资融券功能需要相应的交易权限")
    print("- 本测试主要验证数据查询接口")
    print("- 交易相关接口仅检查可用性，不实际执行交易")
    
    # 运行测试
    try:
        results = test_margin_trading_data()
        
        # 保存结果到JSON文件
        output_file = 'demo_9_margin_trading_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n\n测试完成！结果已保存到: {output_file}")
        
        # 统计测试结果
        total_tests = len(results['tests'])
        success_tests = len([t for t in results['tests'] if t['status'] == 'success'])
        error_tests = len([t for t in results['tests'] if t['status'] == 'error'])
        no_data_tests = len([t for t in results['tests'] if t['status'] == 'no_data'])
        interface_tests = len([t for t in results['tests'] if t['status'] == 'interface_available'])
        
        print(f"\n测试统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  成功: {success_tests}")
        print(f"  接口可用: {interface_tests}")
        print(f"  无数据: {no_data_tests}")
        print(f"  失败: {error_tests}")
        print(f"  成功率: {(success_tests + interface_tests)/total_tests*100:.1f}%")
        
    except Exception as e:
        print(f"测试运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()