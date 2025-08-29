#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK - 基础信息查询测试Demo
测试 get_instruments, get_symbol_infos, get_symbols 等函数
"""

import json
import pandas as pd
import os
from datetime import datetime, timedelta
from gm.api import *

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

def test_basic_info():
    """测试基础信息查询"""
    print("=" * 60)
    print("基础信息查询测试Demo")
    print("=" * 60)
    
    results = {}
    
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试 get_instruments 函数
    print("\n" + "=" * 40)
    print("1. 测试 get_instruments 函数")
    print("=" * 40)
    
    instruments_results = {}
    
    # 测试不同交易所和证券类型
    test_cases = [
        {'exchanges': ['SHSE'], 'sec_types': [1], 'name': '上交所股票'},  # 股票
        {'exchanges': ['SZSE'], 'sec_types': [1], 'name': '深交所股票'},  # 股票
        {'exchanges': ['SHSE'], 'sec_types': [2], 'name': '上交所基金'},  # 基金
        {'exchanges': ['SZSE'], 'sec_types': [2], 'name': '深交所基金'},  # 基金
        {'exchanges': ['SHSE', 'SZSE'], 'sec_types': [1], 'name': '沪深股票'},  # 沪深股票
    ]
    
    for case in test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            instruments = get_instruments(
                exchanges=case['exchanges'],
                sec_types=case['sec_types']
            )
            
            if instruments is not None and len(instruments) > 0:
                instruments_results[case['name']] = {
                    'count': len(instruments),
                    'sample_data': instruments[:5] if len(instruments) >= 5 else instruments,
                    'exchanges': case['exchanges'],
                    'sec_types': case['sec_types']
                }
                print(f"    ✓ 获取到 {len(instruments)} 个标的")
                print(f"    ✓ 样本数据: {instruments[:3]}")
                
                # 保存到CSV
                df = pd.DataFrame([{'symbol': inst} for inst in instruments])
                csv_filename = f"instruments_{case['name'].replace('/', '_')}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                instruments_results[case['name']] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            instruments_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['instruments_test'] = instruments_results
    
    # 2. 测试 get_symbol_infos 函数
    print("\n" + "=" * 40)
    print("2. 测试 get_symbol_infos 函数")
    print("=" * 40)
    
    symbol_infos_results = {}
    
    # 测试不同证券类型的基本信息
    info_test_cases = [
        {'sec_type1': 1, 'sec_type2': 0, 'exchanges': ['SHSE'], 'name': '上交所股票信息'},
        {'sec_type1': 1, 'sec_type2': 0, 'exchanges': ['SZSE'], 'name': '深交所股票信息'},
        {'sec_type1': 2, 'sec_type2': 0, 'exchanges': ['SHSE'], 'name': '上交所基金信息'},
    ]
    
    for case in info_test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            # 获取基本信息（DataFrame格式）
            try:
                # 尝试不同的参数组合
                symbol_infos = get_symbol_infos(
                    sec_type1=case['sec_type1'],
                    df=True
                )
                
                # 如果没有数据，尝试不使用df参数
                if symbol_infos is None or (hasattr(symbol_infos, 'empty') and symbol_infos.empty) or (isinstance(symbol_infos, list) and len(symbol_infos) == 0):
                    symbol_infos = get_symbol_infos(
                        sec_type1=case['sec_type1']
                    )
                    if symbol_infos:
                        symbol_infos = pd.DataFrame(symbol_infos)
                
                # 检查数据是否有效
                has_data = False
                if symbol_infos is not None:
                    if hasattr(symbol_infos, 'empty'):
                        has_data = not symbol_infos.empty
                    elif isinstance(symbol_infos, list):
                        has_data = len(symbol_infos) > 0
                        if has_data:
                            symbol_infos = pd.DataFrame(symbol_infos)
                    else:
                        has_data = True
                
                if has_data:
                    symbol_infos_results[case['name']] = {
                        'count': len(symbol_infos),
                        'columns': list(symbol_infos.columns),
                        'sample_data': symbol_infos.head(3).to_dict('records'),
                        'data_types': {col: str(symbol_infos[col].dtype) for col in symbol_infos.columns}
                    }
                    print(f"    ✓ 获取到 {len(symbol_infos)} 个标的信息")
                    print(f"    ✓ 列名: {list(symbol_infos.columns)}")
                    print(f"    ✓ 样本数据: {symbol_infos.iloc[0]['symbol'] if 'symbol' in symbol_infos.columns else '无symbol列'}")
                    
                    # 保存到CSV
                    csv_filename = f"symbol_infos_{case['name'].replace('/', '_')}.csv"
                    symbol_infos.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"    ✓ 数据已保存到: {csv_filename}")
                    
                else:
                    symbol_infos_results[case['name']] = {'error': '无数据返回'}
                    print(f"    ✗ 无数据返回")
                    
            except Exception as e:
                symbol_infos_results[case['name']] = {'error': str(e)}
                print(f"    ✗ 查询错误: {e}")
                
        except Exception as e:
            symbol_infos_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['symbol_infos_test'] = symbol_infos_results
    
    # 3. 测试 get_symbols 函数
    print("\n" + "=" * 40)
    print("3. 测试 get_symbols 函数")
    print("=" * 40)
    
    symbols_results = {}
    
    # 测试特定交易日的交易信息
    symbols_test_cases = [
        {'sec_type1': 1, 'exchanges': ['SHSE'], 'name': '上交所股票交易信息'},
        {'sec_type1': 1, 'exchanges': ['SZSE'], 'name': '深交所股票交易信息'},
    ]
    
    for case in symbols_test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            # 获取交易信息（DataFrame格式）
            try:
                # 使用最近的交易日
                trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                symbols_data = get_symbols(
                    sec_type1=case['sec_type1'],
                    trade_date=trade_date,
                    df=True
                )
                
                # 如果没有数据，尝试不使用df参数
                if symbols_data is None or (hasattr(symbols_data, 'empty') and symbols_data.empty) or (isinstance(symbols_data, list) and len(symbols_data) == 0):
                    symbols_data = get_symbols(
                        sec_type1=case['sec_type1'],
                        trade_date=trade_date
                    )
                    if symbols_data:
                        symbols_data = pd.DataFrame(symbols_data)
                
                # 如果还是没有数据，尝试不使用trade_date参数
                if symbols_data is None or (hasattr(symbols_data, 'empty') and symbols_data.empty) or (isinstance(symbols_data, list) and len(symbols_data) == 0):
                    symbols_data = get_symbols(
                        sec_type1=case['sec_type1'],
                        df=True
                    )
                
                # 检查数据是否有效
                has_data = False
                if symbols_data is not None:
                    if hasattr(symbols_data, 'empty'):
                        has_data = not symbols_data.empty
                    elif isinstance(symbols_data, list):
                        has_data = len(symbols_data) > 0
                        if has_data:
                            symbols_data = pd.DataFrame(symbols_data)
                    else:
                        has_data = True
                
                if has_data:
                    symbols_results[case['name']] = {
                        'count': len(symbols_data),
                        'columns': list(symbols_data.columns),
                        'sample_data': symbols_data.head(3).to_dict('records'),
                        'trading_symbols': len(symbols_data[symbols_data.get('is_suspended', True) == False]) if 'is_suspended' in symbols_data.columns else 'N/A'
                    }
                    print(f"    ✓ 获取到 {len(symbols_data)} 个标的交易信息")
                    print(f"    ✓ 列名: {list(symbols_data.columns)}")
                    
                    # 保存到CSV
                    csv_filename = f"symbols_{case['name'].replace('/', '_')}.csv"
                    symbols_data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"    ✓ 数据已保存到: {csv_filename}")
                    
                else:
                    symbols_results[case['name']] = {'error': '无数据返回'}
                    print(f"    ✗ 无数据返回")
                    
            except Exception as e:
                symbols_results[case['name']] = {'error': str(e)}
                print(f"    ✗ 查询错误: {e}")
                
        except Exception as e:
            symbols_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['symbols_test'] = symbols_results
    
    # 4. 测试特定标的的详细信息
    print("\n" + "=" * 40)
    print("4. 测试特定标的详细信息")
    print("=" * 40)
    
    specific_symbols = [
        'SHSE.600036',  # 招商银行
        'SZSE.000001',  # 平安银行
        'SHSE.600000',  # 浦发银行
        'SHSE.510300',  # 沪深300ETF
    ]
    
    specific_results = {}
    
    for symbol in specific_symbols:
        try:
            print(f"\n查询 {symbol} 的详细信息...")
            
            # 尝试不同的参数组合
            try:
                symbol_info = get_symbol_infos(
                    symbols=[symbol],
                    sec_type1=1,
                    df=True
                )
                
                # 如果没有数据，尝试不使用df参数
                if symbol_info is None or (hasattr(symbol_info, 'empty') and symbol_info.empty) or (isinstance(symbol_info, list) and len(symbol_info) == 0):
                    symbol_info = get_symbol_infos(
                        symbols=[symbol],
                        sec_type1=1
                    )
                    if symbol_info:
                        symbol_info = pd.DataFrame(symbol_info)
                
                # 如果还是没有数据，尝试使用默认的sec_type1=1
                if symbol_info is None or (hasattr(symbol_info, 'empty') and symbol_info.empty) or (isinstance(symbol_info, list) and len(symbol_info) == 0):
                    symbol_info = get_symbol_infos(
                        symbols=[symbol],
                        sec_type1=1,
                        df=True
                    )
                
                # 检查数据是否有效
                has_data = False
                if symbol_info is not None:
                    if hasattr(symbol_info, 'empty'):
                        has_data = not symbol_info.empty
                    elif isinstance(symbol_info, list):
                        has_data = len(symbol_info) > 0
                        if has_data:
                            symbol_info = pd.DataFrame(symbol_info)
                    else:
                        has_data = True
                
                if has_data:
                    info_dict = symbol_info.iloc[0].to_dict()
                    specific_results[symbol] = {
                        'basic_info': info_dict,
                        'available_fields': list(symbol_info.columns)
                    }
                    
                    print(f"    ✓ 标的名称: {info_dict.get('sec_name', 'N/A')}")
                    print(f"    ✓ 交易所: {info_dict.get('exchange', 'N/A')}")
                    print(f"    ✓ 证券类型: {info_dict.get('sec_type', 'N/A')}")
                    print(f"    ✓ 上市日期: {info_dict.get('listed_date', 'N/A')}")
                    
                else:
                    specific_results[symbol] = {'error': '无数据返回'}
                    print(f"    ✗ 无数据返回")
                    
            except Exception as e:
                specific_results[symbol] = {'error': str(e)}
                print(f"    ✗ 查询错误: {e}")
                
        except Exception as e:
            specific_results[symbol] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['specific_symbols_test'] = specific_results
    
    # 5. 测试品种信息查询 (暂时跳过，该函数存在超时问题)
    print("\n" + "=" * 40)
    print("5. 测试品种信息查询 (跳过)")
    print("=" * 40)
    
    results['variety_infos_test'] = {'error': '跳过测试 - get_varietyinfos函数存在超时问题'}
    print(f"    ⚠ 跳过测试 - get_varietyinfos函数存在超时问题")
    
    # 注释掉的原始代码:
    # try:
    #     print(f"\n查询品种信息...")
    #     variety_infos = get_varietyinfos(df=True)
    #     if variety_infos is not None and not variety_infos.empty:
    #         results['variety_infos_test'] = {
    #             'count': len(variety_infos),
    #             'columns': list(variety_infos.columns),
    #             'sample_data': variety_infos.head(5).to_dict('records')
    #         }
    #         print(f"    ✓ 获取到 {len(variety_infos)} 个品种信息")
    #         variety_infos.to_csv('variety_infos.csv', index=False, encoding='utf-8-sig')
    #         print(f"    ✓ 数据已保存到: variety_infos.csv")
    #     else:
    #         results['variety_infos_test'] = {'error': '无数据返回'}
    #         print(f"    ✗ 无数据返回")
    # except Exception as e:
    #     results['variety_infos_test'] = {'error': str(e)}
    #     print(f"    ✗ 品种信息查询错误: {e}")
    
    # 保存测试结果
    with open('demo_3_basic_info_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("基础信息查询测试完成！")
    print("详细结果已保存到: demo_3_basic_info_results.json")
    print("CSV数据文件已保存到当前目录")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    try:
        # 配置token
        if not configure_token():
            print("\n请先配置有效的token后再运行测试")
            exit(1)
        
        # 测试token有效性
        try:
            test_dates = get_trading_dates('SHSE', '2024-01-01', '2024-01-05')
            if not test_dates:
                print("Token验证失败，请检查token是否有效")
                exit(1)
            print("Token验证成功")
        except Exception as e:
            print(f"Token验证失败: {e}")
            exit(1)
        
        # 运行测试
        test_results = test_basic_info()
        
        # 打印总结
        print("\n测试总结:")
        
        if 'instruments_test' in test_results:
            total_instruments = len(test_results['instruments_test'])
            successful_instruments = sum(1 for data in test_results['instruments_test'].values() if 'error' not in data)
            print(f"get_instruments函数测试: {successful_instruments}/{total_instruments} 成功")
        
        if 'symbol_infos_test' in test_results:
            total_infos = len(test_results['symbol_infos_test'])
            successful_infos = sum(1 for data in test_results['symbol_infos_test'].values() if 'error' not in data)
            print(f"get_symbol_infos函数测试: {successful_infos}/{total_infos} 成功")
        
        if 'symbols_test' in test_results:
            total_symbols = len(test_results['symbols_test'])
            successful_symbols = sum(1 for data in test_results['symbols_test'].values() if 'error' not in data)
            print(f"get_symbols函数测试: {successful_symbols}/{total_symbols} 成功")
        
        if 'specific_symbols_test' in test_results:
            total_specific = len(test_results['specific_symbols_test'])
            successful_specific = sum(1 for data in test_results['specific_symbols_test'].values() if 'error' not in data)
            print(f"特定标的查询测试: {successful_specific}/{total_specific} 成功")
        
        variety_success = 'error' not in test_results.get('variety_infos_test', {'error': 'not tested'})
        print(f"品种信息查询测试: {'成功' if variety_success else '失败'}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()