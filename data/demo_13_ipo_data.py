#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK 新股申购数据查询测试demo

本demo测试以下新股申购相关接口：
1. ipo_get_instruments - 查询新股申购标的
2. ipo_get_quota - 查询新股申购额度
3. ipo_get_lot_info - 查询新股申购配号信息
4. ipo_get_match_number - 查询新股申购中签号码

注意：运行前需要配置有效的token，且需要新股申购数据权限
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

def test_ipo_data():
    """
    测试新股申购数据查询接口
    """
    results = {
        'test_info': {
            'test_name': '新股申购数据查询测试',
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': '测试新股申购标的、额度、配号、中签号码等数据查询功能'
        },
        'tests': []
    }
    
    # 时间范围
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    # ============================================================
    # 测试1: 查询新股申购标的
    # ============================================================
    print("\n=== 测试1: 查询新股申购标的 ===")
    
    print(f"\n测试1.1: 查询新股申购标的列表")
    try:
        result = ipo_get_instruments(
            sec_type='stock',  # 查询股票类型的新股申购
            df=False
        )
        
        test_result = {
            'test_name': '查询新股申购标的列表',
            'function': 'ipo_get_instruments',
            'params': {
                'sec_type': 'stock',
                'df': False
            },
            'status': 'success' if result else 'no_data',
            'result_count': len(result) if result else 0,
            'sample_data': result[:5] if result and len(result) > 0 else None,
            'result': result[:50] if result and len(result) > 50 else result  # 限制结果大小
        }
        
        if result:
            print(f"  ✓ 成功获取 {len(result)} 个新股申购标的")
            if len(result) > 0:
                print(f"  示例数据: {result[0]}")
                
                # 保存到CSV
                df = pd.DataFrame(result)
                csv_filename = "ipo_instruments.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  数据已保存到: {csv_filename}")
                
                # 提取一些股票代码用于后续测试
                sample_symbols = [item.get('symbol', '') for item in result[:5] if item.get('symbol')]
                print(f"  提取样本股票代码: {sample_symbols}")
        else:
            print(f"  ⚠ 未获取到新股申购标的")
            sample_symbols = []
            
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        test_result = {
            'test_name': '查询新股申购标的列表',
            'function': 'ipo_get_instruments',
            'params': {},
            'status': 'error',
            'error': str(e)
        }
        sample_symbols = []
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试2: 查询新股申购额度
    # ============================================================
    print("\n\n=== 测试2: 查询新股申购额度 ===")
    
    print(f"\n测试2.1: 查询新股申购额度信息")
    try:
        result = ipo_get_quota()
        
        test_result = {
            'test_name': '查询新股申购额度信息',
            'function': 'ipo_get_quota',
            'params': {},
            'status': 'success' if result else 'no_data',
            'result_count': len(result) if result else 0,
            'sample_data': result[:5] if result and len(result) > 0 else None,
            'result': result[:50] if result and len(result) > 50 else result  # 限制结果大小
        }
        
        if result:
            print(f"  ✓ 成功获取 {len(result)} 条新股申购额度信息")
            if len(result) > 0:
                print(f"  示例数据: {result[0]}")
                
                # 保存到CSV
                df = pd.DataFrame(result)
                csv_filename = "ipo_quota.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  数据已保存到: {csv_filename}")
        else:
            print(f"  ⚠ 未获取到新股申购额度信息")
            
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        test_result = {
            'test_name': '查询新股申购额度信息',
            'function': 'ipo_get_quota',
            'params': {},
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试3: 查询新股申购配号信息
    # ============================================================
    print("\n\n=== 测试3: 查询新股申购配号信息 ===")
    
    # 如果有样本股票代码，则查询具体股票的配号信息
    if sample_symbols:
        for i, symbol in enumerate(sample_symbols[:3], 1):  # 只测试前3个
            print(f"\n测试3.{i}: 查询 {symbol} 新股申购配号信息")
            try:
                result = ipo_get_lot_info(
                    start_time=start_date,
                    end_time=end_date,
                    df=False
                )
                
                test_result = {
                    'test_name': f'查询{symbol}新股申购配号信息',
                    'function': 'ipo_get_lot_info',
                    'params': {
                        'start_time': start_date,
                        'end_time': end_date,
                        'df': False
                    },
                    'status': 'success' if result else 'no_data',
                    'result_count': len(result) if result else 0,
                    'sample_data': result[:3] if result and len(result) > 0 else None,
                    'result': result
                }
                
                if result:
                    print(f"  ✓ 成功获取 {len(result)} 条配号信息")
                    if len(result) > 0:
                        print(f"  示例数据: {result[0]}")
                else:
                    print(f"  ⚠ 未获取到配号信息")
                    
            except Exception as e:
                print(f"  ✗ 测试失败: {e}")
                test_result = {
                    'test_name': f'查询{symbol}新股申购配号信息',
                    'function': 'ipo_get_lot_info',
                    'params': {
                        'start_time': start_date,
                        'end_time': end_date,
                        'df': False
                    },
                    'status': 'error',
                    'error': str(e)
                }
            
            results['tests'].append(test_result)
    else:
        # 如果没有样本股票，则尝试查询所有配号信息
        print(f"\n测试3.1: 查询所有新股申购配号信息")
        try:
            result = ipo_get_lot_info(
            start_time=start_date,
            end_time=end_date,
            df=False
        )
            
            test_result = {
                'test_name': '查询所有新股申购配号信息',
                'function': 'ipo_get_lot_info',
                'params': {
                    'start_time': start_date,
                    'end_time': end_date,
                    'df': False
                },
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:5] if result and len(result) > 0 else None,
                'result': result[:50] if result and len(result) > 50 else result
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条配号信息")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    df = pd.DataFrame(result)
                    csv_filename = "ipo_lot_info.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到配号信息")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': '查询所有新股申购配号信息',
                'function': 'ipo_get_lot_info',
                'params': {
                    'start_time': start_date,
                    'end_time': end_date,
                    'df': False
                },
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    # ============================================================
    # 测试4: 查询新股申购中签号码
    # ============================================================
    print("\n\n=== 测试4: 查询新股申购中签号码 ===")
    
    # 如果有样本股票代码，则查询具体股票的中签号码
    if sample_symbols:
        for i, symbol in enumerate(sample_symbols[:3], 1):  # 只测试前3个
            print(f"\n测试4.{i}: 查询 {symbol} 新股申购中签号码")
            try:
                result = ipo_get_match_number(
                    start_time=start_date,
                    end_time=end_date,
                    df=False
                )
                
                test_result = {
                    'test_name': f'查询{symbol}新股申购中签号码',
                    'function': 'ipo_get_match_number',
                    'params': {
                        'symbol': symbol,
                        'start_date': start_date,
                        'end_date': end_date,
                        'df': False
                    },
                    'status': 'success' if result else 'no_data',
                    'result_count': len(result) if result else 0,
                    'sample_data': result[:3] if result and len(result) > 0 else None,
                    'result': result
                }
                
                if result:
                    print(f"  ✓ 成功获取 {len(result)} 条中签号码")
                    if len(result) > 0:
                        print(f"  示例数据: {result[0]}")
                else:
                    print(f"  ⚠ 未获取到中签号码")
                    
            except Exception as e:
                print(f"  ✗ 测试失败: {e}")
                test_result = {
                    'test_name': f'查询{symbol}新股申购中签号码',
                    'function': 'ipo_get_match_number',
                    'params': {
                        'symbol': symbol,
                        'start_date': start_date,
                        'end_date': end_date,
                        'df': False
                    },
                    'status': 'error',
                    'error': str(e)
                }
            
            results['tests'].append(test_result)
    else:
        # 如果没有样本股票，则尝试查询所有中签号码
        print(f"\n测试4.1: 查询所有新股申购中签号码")
        try:
            result = ipo_get_match_number(
            start_time=start_date,
            end_time=end_date,
            df=False
        )
            
            test_result = {
                'test_name': '查询所有新股申购中签号码',
                'function': 'ipo_get_match_number',
                'params': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'df': False
                },
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:5] if result and len(result) > 0 else None,
                'result': result[:50] if result and len(result) > 50 else result
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条中签号码")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    df = pd.DataFrame(result)
                    csv_filename = "ipo_match_number.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到中签号码")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': '查询所有新股申购中签号码',
                'function': 'ipo_get_match_number',
                'params': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'df': False
                },
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    # ============================================================
    # 测试5: 查询最近的新股申购信息（缩短时间范围）
    # ============================================================
    print("\n\n=== 测试5: 查询最近的新股申购信息 ===")
    
    recent_start = '2024-01-01'
    recent_end = '2024-12-31'
    
    print(f"\n测试5.1: 查询最近的新股申购标的")
    try:
        result = ipo_get_instruments(
            start_date=recent_start,
            end_date=recent_end,
            df=False
        )
        
        test_result = {
            'test_name': '查询最近的新股申购标的',
            'function': 'ipo_get_instruments',
            'params': {
                'start_date': recent_start,
                'end_date': recent_end,
                'df': False
            },
            'status': 'success' if result else 'no_data',
            'result_count': len(result) if result else 0,
            'sample_data': result[:5] if result and len(result) > 0 else None,
            'result': result[:20] if result and len(result) > 20 else result
        }
        
        if result:
            print(f"  ✓ 成功获取 {len(result)} 个最近的新股申购标的")
            if len(result) > 0:
                print(f"  示例数据: {result[0]}")
                
                # 保存到CSV
                df = pd.DataFrame(result)
                csv_filename = "recent_ipo_instruments.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  数据已保存到: {csv_filename}")
        else:
            print(f"  ⚠ 未获取到最近的新股申购标的")
            
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        test_result = {
            'test_name': '查询最近的新股申购标的',
            'function': 'ipo_get_instruments',
            'params': {
                'start_date': recent_start,
                'end_date': recent_end,
                'df': False
            },
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    return results

def main():
    """
    主函数
    """
    print("掘金量化 GM SDK 新股申购数据查询测试")
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
    print("- 新股申购数据功能需要相应的数据权限")
    print("- 本测试查询新股申购标的、额度、配号、中签号码等信息")
    print("- 如果没有相关数据，可能是因为时间范围内没有新股申购")
    
    # 运行测试
    try:
        results = test_ipo_data()
        
        # 保存结果到JSON文件
        output_file = 'demo_13_ipo_data_results.json'
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