#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK 股东数据查询测试demo

本demo测试以下股东数据相关接口：
1. stk_get_top_shareholder - 查询十大股东数据
2. stk_get_shareholder_num - 查询股东户数数据
3. stk_hk_inst_holding_info - 查询港股通机构持股信息
4. stk_hk_inst_holding_detail_info - 查询港股通机构持股明细
5. stk_quota_shszhk_infos - 查询沪深港通额度信息

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

def test_shareholder_data():
    """
    测试股东数据查询接口
    """
    results = {
        'test_info': {
            'test_name': '股东数据查询测试',
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': '测试十大股东、股东户数、港股通持股等数据查询功能'
        },
        'tests': []
    }
    
    # 测试股票列表
    test_symbols = [
        'SHSE.600000',  # 浦发银行
        'SHSE.600036',  # 招商银行
        'SZSE.000001',  # 平安银行
        'SZSE.000002',  # 万科A
        'SHSE.600519'   # 贵州茅台
    ]
    
    # 港股通股票
    hk_symbols = [
        'HKEX.00700',   # 腾讯控股
        'HKEX.00941',   # 中国移动
        'HKEX.01398',   # 工商银行
        'HKEX.00939',   # 建设银行
        'HKEX.03988'    # 中国银行
    ]
    
    # 时间范围
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    # ============================================================
    # 测试1: 查询十大股东数据
    # ============================================================
    print("\n=== 测试1: 查询十大股东数据 ===")
    
    for i, symbol in enumerate(test_symbols, 1):
        print(f"\n测试1.{i}: 查询 {symbol} 十大股东数据")
        try:
            result = stk_get_top_shareholder(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                df=False
            )
            
            test_result = {
                'test_name': f'查询{symbol}十大股东数据',
                'function': 'stk_get_top_shareholder',
                'params': {
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date,
                    'df': False
                },
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:3] if result and len(result) > 0 else None,
                'result': result[:20] if result and len(result) > 20 else result  # 限制结果大小
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条十大股东数据")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    df = pd.DataFrame(result)
                    csv_filename = f"top_shareholder_{symbol.replace('.', '_')}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到十大股东数据")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': f'查询{symbol}十大股东数据',
                'function': 'stk_get_top_shareholder',
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
    
    # ============================================================
    # 测试2: 查询股东户数数据
    # ============================================================
    print("\n\n=== 测试2: 查询股东户数数据 ===")
    
    for i, symbol in enumerate(test_symbols, 1):
        print(f"\n测试2.{i}: 查询 {symbol} 股东户数数据")
        try:
            result = stk_get_shareholder_num(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                df=False
            )
            
            test_result = {
                'test_name': f'查询{symbol}股东户数数据',
                'function': 'stk_get_shareholder_num',
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
                print(f"  ✓ 成功获取 {len(result)} 条股东户数数据")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
            else:
                print(f"  ⚠ 未获取到股东户数数据")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': f'查询{symbol}股东户数数据',
                'function': 'stk_get_shareholder_num',
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
    
    # 汇总所有股东户数数据并保存到CSV
    all_shareholder_num_data = []
    for test in results['tests'][-len(test_symbols):]:
        if test['status'] == 'success' and test.get('result'):
            all_shareholder_num_data.extend(test['result'])
    
    if all_shareholder_num_data:
        df = pd.DataFrame(all_shareholder_num_data)
        csv_filename = "shareholder_num_data.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n所有股东户数数据已保存到: {csv_filename}")
    
    # ============================================================
    # 测试3: 查询港股通机构持股信息
    # ============================================================
    print("\n\n=== 测试3: 查询港股通机构持股信息 ===")
    
    # 测试港股通机构持股信息（不需要指定具体股票）
    print(f"\n测试3.1: 查询港股通机构持股信息")
    try:
        result = stk_hk_inst_holding_info(
            start_date='2024-01-01',
            end_date='2024-03-31',
            df=False
        )
        
        test_result = {
            'test_name': '查询港股通机构持股信息',
            'function': 'stk_hk_inst_holding_info',
            'params': {
                'start_date': '2024-01-01',
                'end_date': '2024-03-31',
                'df': False
            },
            'status': 'success' if result else 'no_data',
            'result_count': len(result) if result else 0,
            'sample_data': result[:3] if result and len(result) > 0 else None,
            'result': result[:50] if result and len(result) > 50 else result  # 限制结果大小
        }
        
        if result:
            print(f"  ✓ 成功获取 {len(result)} 条港股通机构持股信息")
            if len(result) > 0:
                print(f"  示例数据: {result[0]}")
                
                # 保存到CSV
                df = pd.DataFrame(result)
                csv_filename = "hk_inst_holding_info.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  数据已保存到: {csv_filename}")
        else:
            print(f"  ⚠ 未获取到港股通机构持股信息")
            
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        test_result = {
            'test_name': '查询港股通机构持股信息',
            'function': 'stk_hk_inst_holding_info',
            'params': {
                'start_date': '2024-01-01',
                'end_date': '2024-03-31',
                'df': False
            },
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试4: 查询港股通机构持股明细
    # ============================================================
    print("\n\n=== 测试4: 查询港股通机构持股明细 ===")
    
    for i, symbol in enumerate(hk_symbols[:3], 1):  # 只测试前3个港股
        print(f"\n测试4.{i}: 查询 {symbol} 港股通机构持股明细")
        try:
            result = stk_hk_inst_holding_detail_info(
                symbols=[symbol],
                trade_date='2024-03-31',
                df=False
            )
            
            test_result = {
                'test_name': f'查询{symbol}港股通机构持股明细',
                'function': 'stk_hk_inst_holding_detail_info',
                'params': {
                    'symbols': [symbol],
                    'trade_date': '2024-03-31',
                    'df': False
                },
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:3] if result and len(result) > 0 else None,
                'result': result[:20] if result and len(result) > 20 else result  # 限制结果大小
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条港股通机构持股明细")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    df = pd.DataFrame(result)
                    csv_filename = f"hk_inst_holding_detail_{symbol.replace('.', '_')}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到港股通机构持股明细")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': f'查询{symbol}港股通机构持股明细',
                'function': 'stk_hk_inst_holding_detail_info',
                'params': {
                    'symbols': [symbol],
                    'trade_date': '2024-03-31',
                    'df': False
                },
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    # ============================================================
    # 测试5: 查询沪深港通额度信息
    # ============================================================
    print("\n\n=== 测试5: 查询沪深港通额度信息 ===")
    
    print(f"\n测试5.1: 查询沪深港通额度信息")
    try:
        result = stk_quota_shszhk_infos(
            start_date='2024-01-01',
            end_date='2024-03-31',
            df=False
        )
        
        test_result = {
            'test_name': '查询沪深港通额度信息',
            'function': 'stk_quota_shszhk_infos',
            'params': {
                'start_date': '2024-01-01',
                'end_date': '2024-03-31',
                'df': False
            },
            'status': 'success' if result else 'no_data',
            'result_count': len(result) if result else 0,
            'sample_data': result[:3] if result and len(result) > 0 else None,
            'result': result
        }
        
        if result:
            print(f"  ✓ 成功获取 {len(result)} 条沪深港通额度信息")
            if len(result) > 0:
                print(f"  示例数据: {result[0]}")
                
                # 保存到CSV
                df = pd.DataFrame(result)
                csv_filename = "shszhk_quota_info.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  数据已保存到: {csv_filename}")
        else:
            print(f"  ⚠ 未获取到沪深港通额度信息")
            
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        test_result = {
            'test_name': '查询沪深港通额度信息',
            'function': 'stk_quota_shszhk_infos',
            'params': {
                'start_date': '2024-01-01',
                'end_date': '2024-03-31',
                'df': False
            },
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试6: 查询资金流向数据（补充测试）
    # ============================================================
    print("\n\n=== 测试6: 查询资金流向数据 ===")
    
    for i, symbol in enumerate(test_symbols[:2], 1):  # 只测试前2个股票
        print(f"\n测试6.{i}: 查询 {symbol} 资金流向数据")
        try:
            result = stk_get_money_flow(
                symbols=[symbol],
                trade_date='2024-03-31'
            )
            
            test_result = {
                'test_name': f'查询{symbol}资金流向数据',
                'function': 'stk_get_money_flow',
                'params': {
                    'symbols': [symbol],
                    'trade_date': '2024-03-31'
                },
                'status': 'success' if result else 'no_data',
                'result_count': len(result) if result else 0,
                'sample_data': result[:3] if result and len(result) > 0 else None,
                'result': result[:20] if result and len(result) > 20 else result  # 限制结果大小
            }
            
            if result:
                print(f"  ✓ 成功获取 {len(result)} 条资金流向数据")
                if len(result) > 0:
                    print(f"  示例数据: {result[0]}")
                    
                    # 保存到CSV
                    df = pd.DataFrame(result)
                    csv_filename = f"money_flow_{symbol.replace('.', '_')}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  数据已保存到: {csv_filename}")
            else:
                print(f"  ⚠ 未获取到资金流向数据")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': f'查询{symbol}资金流向数据',
                'function': 'stk_get_money_flow',
                'params': {
                    'symbols': [symbol],
                    'trade_date': '2024-03-31'
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
    print("掘金量化 GM SDK 股东数据查询测试")
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
    
    print("\n测试说明：")
    print("- 测试十大股东数据查询")
    print("- 测试股东户数数据查询")
    print("- 测试港股通机构持股信息查询")
    print("- 测试港股通机构持股明细查询")
    print("- 测试沪深港通额度信息查询")
    print("- 测试资金流向数据查询")
    
    # 运行测试
    try:
        results = test_shareholder_data()
        
        # 保存结果到JSON文件
        output_file = 'demo_11_shareholder_data_results.json'
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