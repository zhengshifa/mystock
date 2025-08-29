#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK 期权数据查询测试demo

本demo测试以下期权数据相关接口：
1. option_calculate_delta - 计算期权Delta值
2. option_calculate_gamma - 计算期权Gamma值
3. option_calculate_theta - 计算期权Theta值
4. option_calculate_vega - 计算期权Vega值
5. option_calculate_rho - 计算期权Rho值
6. option_calculate_iv - 计算期权隐含波动率
7. option_calculate_price - 计算期权理论价格
8. get_instruments - 查询期权合约信息

注意：运行前需要配置有效的token，且需要期权数据权限
"""

import gm
from gm.api import *
import json
import pandas as pd
import os
import math
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

def test_options_data():
    """
    测试期权数据查询和计算接口
    """
    results = {
        'test_info': {
            'test_name': '期权数据查询和计算测试',
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': '测试期权希腊字母计算、隐含波动率、理论价格等功能'
        },
        'tests': []
    }
    
    # ============================================================
    # 测试1: 查询期权合约信息
    # ============================================================
    print("\n=== 测试1: 查询期权合约信息 ===")
    
    # 查询上证50ETF期权
    exchanges = ['SHSE', 'SZSE', 'CFFEX', 'SHFE', 'DCE', 'CZCE']
    option_instruments = []
    
    for exchange in exchanges:
        print(f"\n测试1.{exchanges.index(exchange)+1}: 查询 {exchange} 期权合约")
        try:
            instruments = get_instruments(
                exchanges=[exchange],
                sec_types=[SEC_TYPE_OPTION],
                df=False
            )
            
            test_result = {
                'test_name': f'查询{exchange}期权合约',
                'function': 'get_instruments',
                'params': {
                    'exchanges': [exchange],
                    'sec_types': [SEC_TYPE_OPTION],
                    'df': False
                },
                'status': 'success' if instruments else 'no_data',
                'result_count': len(instruments) if instruments else 0,
                'sample_data': instruments[:3] if instruments and len(instruments) > 0 else None
            }
            
            if instruments:
                print(f"  ✓ 成功获取 {len(instruments)} 个期权合约")
                if len(instruments) > 0:
                    print(f"  示例合约: {instruments[0]['symbol']}")
                    option_instruments.extend(instruments[:10])  # 保存前10个用于后续测试
            else:
                print(f"  ⚠ 未获取到期权合约")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            test_result = {
                'test_name': f'查询{exchange}期权合约',
                'function': 'get_instruments',
                'params': {
                    'exchanges': [exchange],
                    'sec_types': [SEC_TYPE_OPTION],
                    'df': False
                },
                'status': 'error',
                'error': str(e)
            }
        
        results['tests'].append(test_result)
    
    # 保存期权合约信息到CSV
    if option_instruments:
        df = pd.DataFrame(option_instruments)
        csv_filename = "option_instruments.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n期权合约信息已保存到: {csv_filename}")
    
    # ============================================================
    # 测试2: 期权希腊字母计算
    # ============================================================
    print("\n\n=== 测试2: 期权希腊字母计算 ===")
    
    # 使用模拟参数进行计算测试
    test_params = {
        'underlying_price': 3.0,      # 标的价格
        'strike_price': 3.0,          # 行权价
        'risk_free_rate': 0.03,       # 无风险利率
        'dividend_yield': 0.02,       # 股息率
        'volatility': 0.25,           # 波动率
        'time_to_expiry': 0.25,       # 到期时间（年）
        'option_type': 'call'         # 期权类型
    }
    
    # 测试Delta计算
    print(f"\n测试2.1: 计算期权Delta值")
    try:
        delta = option_calculate_delta(
            s=test_params['underlying_price'],
            k=test_params['strike_price'],
            v=test_params['volatility'],
            t=test_params['time_to_expiry'],
            call_or_put='C' if test_params['option_type'] == 'call' else 'P',
            r=test_params['risk_free_rate']
        )
        
        test_result = {
            'test_name': '计算期权Delta值',
            'function': 'option_calculate_delta',
            'params': test_params,
            'status': 'success',
            'result': delta
        }
        
        print(f"  ✓ Delta计算成功: {delta}")
        
    except Exception as e:
        print(f"  ✗ Delta计算失败: {e}")
        test_result = {
            'test_name': '计算期权Delta值',
            'function': 'option_calculate_delta',
            'params': test_params,
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # 测试Gamma计算
    print(f"\n测试2.2: 计算期权Gamma值")
    try:
        gamma = option_calculate_gamma(
            s=test_params['underlying_price'],
            k=test_params['strike_price'],
            v=test_params['volatility'],
            t=test_params['time_to_expiry'],
            call_or_put='C' if test_params['option_type'] == 'call' else 'P',
            r=test_params['risk_free_rate']
        )
        
        test_result = {
            'test_name': '计算期权Gamma值',
            'function': 'option_calculate_gamma',
            'params': test_params,
            'status': 'success',
            'result': gamma
        }
        
        print(f"  ✓ Gamma计算成功: {gamma}")
        
    except Exception as e:
        print(f"  ✗ Gamma计算失败: {e}")
        test_result = {
            'test_name': '计算期权Gamma值',
            'function': 'option_calculate_gamma',
            'params': test_params,
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # 测试Theta计算
    print(f"\n测试2.3: 计算期权Theta值")
    try:
        theta = option_calculate_theta(
            s=test_params['underlying_price'],
            k=test_params['strike_price'],
            v=test_params['volatility'],
            t=test_params['time_to_expiry'],
            call_or_put='C' if test_params['option_type'] == 'call' else 'P',
            r=test_params['risk_free_rate']
        )
        
        test_result = {
            'test_name': '计算期权Theta值',
            'function': 'option_calculate_theta',
            'params': test_params,
            'status': 'success',
            'result': theta
        }
        
        print(f"  ✓ Theta计算成功: {theta}")
        
    except Exception as e:
        print(f"  ✗ Theta计算失败: {e}")
        test_result = {
            'test_name': '计算期权Theta值',
            'function': 'option_calculate_theta',
            'params': test_params,
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # 测试Vega计算
    print(f"\n测试2.4: 计算期权Vega值")
    try:
        vega = option_calculate_vega(
            s=test_params['underlying_price'],
            k=test_params['strike_price'],
            v=test_params['volatility'],
            t=test_params['time_to_expiry'],
            call_or_put='C' if test_params['option_type'] == 'call' else 'P',
            r=test_params['risk_free_rate']
        )
        
        test_result = {
            'test_name': '计算期权Vega值',
            'function': 'option_calculate_vega',
            'params': test_params,
            'status': 'success',
            'result': vega
        }
        
        print(f"  ✓ Vega计算成功: {vega}")
        
    except Exception as e:
        print(f"  ✗ Vega计算失败: {e}")
        test_result = {
            'test_name': '计算期权Vega值',
            'function': 'option_calculate_vega',
            'params': test_params,
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # 测试Rho计算
    print(f"\n测试2.5: 计算期权Rho值")
    try:
        rho = option_calculate_rho(
            s=test_params['underlying_price'],
            k=test_params['strike_price'],
            v=test_params['volatility'],
            t=test_params['time_to_expiry'],
            call_or_put='C' if test_params['option_type'] == 'call' else 'P',
            r=test_params['risk_free_rate']
        )
        
        test_result = {
            'test_name': '计算期权Rho值',
            'function': 'option_calculate_rho',
            'params': test_params,
            'status': 'success',
            'result': rho
        }
        
        print(f"  ✓ Rho计算成功: {rho}")
        
    except Exception as e:
        print(f"  ✗ Rho计算失败: {e}")
        test_result = {
            'test_name': '计算期权Rho值',
            'function': 'option_calculate_rho',
            'params': test_params,
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试3: 期权隐含波动率计算
    # ============================================================
    print("\n\n=== 测试3: 期权隐含波动率计算 ===")
    
    iv_params = {
        'underlying_price': 3.0,      # 标的价格
        'strike_price': 3.0,          # 行权价
        'risk_free_rate': 0.03,       # 无风险利率
        'dividend_yield': 0.02,       # 股息率
        'time_to_expiry': 0.25,       # 到期时间（年）
        'option_type': 'call',        # 期权类型
        'option_price': 0.15          # 期权市场价格
    }
    
    print(f"\n测试3.1: 计算期权隐含波动率")
    try:
        iv = option_calculate_iv(
            p=iv_params['option_price'],
            s=iv_params['underlying_price'],
            k=iv_params['strike_price'],
            t=iv_params['time_to_expiry'],
            call_or_put='C' if iv_params['option_type'] == 'call' else 'P',
            r=iv_params['risk_free_rate']
        )
        
        test_result = {
            'test_name': '计算期权隐含波动率',
            'function': 'option_calculate_iv',
            'params': iv_params,
            'status': 'success',
            'result': iv
        }
        
        print(f"  ✓ 隐含波动率计算成功: {iv}")
        
    except Exception as e:
        print(f"  ✗ 隐含波动率计算失败: {e}")
        test_result = {
            'test_name': '计算期权隐含波动率',
            'function': 'option_calculate_iv',
            'params': iv_params,
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试4: 期权理论价格计算
    # ============================================================
    print("\n\n=== 测试4: 期权理论价格计算 ===")
    
    print(f"\n测试4.1: 计算期权理论价格")
    try:
        price = option_calculate_price(
            s=test_params['underlying_price'],
            k=test_params['strike_price'],
            v=test_params['volatility'],
            t=test_params['time_to_expiry'],
            call_or_put='C' if test_params['option_type'] == 'call' else 'P',
            r=test_params['risk_free_rate']
        )
        
        test_result = {
            'test_name': '计算期权理论价格',
            'function': 'option_calculate_price',
            'params': test_params,
            'status': 'success',
            'result': price
        }
        
        print(f"  ✓ 理论价格计算成功: {price}")
        
    except Exception as e:
        print(f"  ✗ 理论价格计算失败: {e}")
        test_result = {
            'test_name': '计算期权理论价格',
            'function': 'option_calculate_price',
            'params': test_params,
            'status': 'error',
            'error': str(e)
        }
    
    results['tests'].append(test_result)
    
    # ============================================================
    # 测试5: 批量计算不同参数下的期权指标
    # ============================================================
    print("\n\n=== 测试5: 批量计算不同参数下的期权指标 ===")
    
    print(f"\n测试5.1: 不同行权价下的期权指标")
    
    strike_prices = [2.8, 2.9, 3.0, 3.1, 3.2]
    batch_results = []
    
    for strike in strike_prices:
        try:
            # 计算各项指标
            delta = option_calculate_delta(
                s=3.0,
                k=strike,
                v=0.25,
                t=0.25,
                call_or_put='C',
                r=0.03
            )
            
            gamma = option_calculate_gamma(
                s=3.0,
                k=strike,
                v=0.25,
                t=0.25,
                call_or_put='C',
                r=0.03
            )
            
            price = option_calculate_price(
                s=3.0,
                k=strike,
                v=0.25,
                t=0.25,
                call_or_put='C',
                r=0.03
            )
            
            batch_result = {
                'strike_price': strike,
                'delta': delta,
                'gamma': gamma,
                'theoretical_price': price
            }
            
            batch_results.append(batch_result)
            print(f"  行权价 {strike}: Delta={delta:.4f}, Gamma={gamma:.4f}, 价格={price:.4f}")
            
        except Exception as e:
            print(f"  行权价 {strike} 计算失败: {e}")
    
    test_result = {
        'test_name': '不同行权价下的期权指标批量计算',
        'function': 'batch_option_calculation',
        'params': {
            'underlying_price': 3.0,
            'strike_prices': strike_prices,
            'risk_free_rate': 0.03,
            'dividend_yield': 0.02,
            'volatility': 0.25,
            'time_to_expiry': 0.25,
            'option_type': 'call'
        },
        'status': 'success' if batch_results else 'error',
        'result_count': len(batch_results),
        'result': batch_results
    }
    
    results['tests'].append(test_result)
    
    # 保存批量计算结果到CSV
    if batch_results:
        df = pd.DataFrame(batch_results)
        csv_filename = "option_batch_calculation.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n批量计算结果已保存到: {csv_filename}")
    
    return results

def main():
    """
    主函数
    """
    print("掘金量化 GM SDK 期权数据查询和计算测试")
    print("=" * 60)
    
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
    print("- 期权数据功能需要相应的数据权限")
    print("- 本测试包含期权合约查询和希腊字母计算")
    print("- 计算功能使用模拟参数进行测试")
    
    # 运行测试
    try:
        results = test_options_data()
        
        # 保存结果到JSON文件
        output_file = 'demo_12_options_data_results.json'
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