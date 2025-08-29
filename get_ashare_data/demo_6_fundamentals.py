#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK - 财务数据查询测试Demo
测试 get_fundamentals, get_fundamentals_n 等函数
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

def test_fundamentals():
    """测试财务数据查询"""
    print("=" * 60)
    print("财务数据查询测试Demo")
    print("=" * 60)
    
    results = {}
    
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试 get_fundamentals 函数 - 基本财务数据
    print("\n" + "=" * 40)
    print("1. 测试 get_fundamentals 函数 - 基本财务数据")
    print("=" * 40)
    
    fundamentals_results = {}
    
    # 测试不同类型的财务数据
    fundamentals_test_cases = [
        {
            'table': 'trading_derivative_indicator',
            'symbols': ['SHSE.600036', 'SHSE.600000', 'SZSE.000001'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'name': '交易衍生指标'
        },
        {
            'table': 'financial_indicator',
            'symbols': ['SHSE.600036', 'SHSE.600000', 'SZSE.000001'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'name': '财务指标'
        },
        {
            'table': 'income_statement',
            'symbols': ['SHSE.600036', 'SHSE.600000', 'SZSE.000001'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'name': '利润表'
        },
        {
            'table': 'balance_sheet',
            'symbols': ['SHSE.600036', 'SHSE.600000', 'SZSE.000001'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'name': '资产负债表'
        },
        {
            'table': 'cash_flow_statement',
            'symbols': ['SHSE.600036', 'SHSE.600000', 'SZSE.000001'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'name': '现金流量表'
        }
    ]
    
    for case in fundamentals_test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            # 使用新的财务数据函数 - 注意这些函数只支持单个股票查询
            fundamentals_data_list = []
            try:
                for symbol in case['symbols']:
                    if case['table'] == 'trading_derivative_indicator':
                        data = stk_get_daily_valuation(
                            symbol=symbol,
                            fields=None,
                            start_date=case['start_date'],
                            end_date=case['end_date'],
                            df=True
                        )
                    elif case['table'] == 'financial_indicator':
                        data = stk_get_finance_deriv(
                            symbol=symbol,
                            fields=None,
                            start_date=case['start_date'],
                            end_date=case['end_date'],
                            df=True
                        )
                    elif case['table'] == 'income_statement':
                        data = stk_get_fundamentals_income(
                            symbol=symbol,
                            fields=None,
                            start_date=case['start_date'],
                            end_date=case['end_date'],
                            df=True
                        )
                    elif case['table'] == 'balance_sheet':
                        data = stk_get_fundamentals_balance(
                            symbol=symbol,
                            fields=None,
                            start_date=case['start_date'],
                            end_date=case['end_date'],
                            df=True
                        )
                    elif case['table'] == 'cash_flow_statement':
                        data = stk_get_fundamentals_cashflow(
                            symbol=symbol,
                            fields=None,
                            start_date=case['start_date'],
                            end_date=case['end_date'],
                            df=True
                        )
                    else:
                        data = None
                    
                    if data is not None and not data.empty:
                        fundamentals_data_list.append(data)
                
                # 合并所有股票的数据
                if fundamentals_data_list:
                    fundamentals_data = pd.concat(fundamentals_data_list, ignore_index=True)
                else:
                    fundamentals_data = None
                    
            except Exception as e:
                print(f"    ✗ 新财务函数调用失败: {e}")
                fundamentals_data = None
            
            if fundamentals_data is not None and not fundamentals_data.empty:
                fundamentals_results[case['name']] = {
                    'table': case['table'],
                    'symbols': case['symbols'],
                    'count': len(fundamentals_data),
                    'columns': list(fundamentals_data.columns),
                    'sample_data': fundamentals_data.head(3).to_dict('records'),
                    'data_types': {col: str(fundamentals_data[col].dtype) for col in fundamentals_data.columns}
                }
                print(f"    ✓ 获取到 {len(fundamentals_data)} 条财务数据")
                print(f"    ✓ 列名: {list(fundamentals_data.columns)[:10]}...")
                
                # 保存到CSV
                csv_filename = f"fundamentals_{case['name']}.csv"
                fundamentals_data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                fundamentals_results[case['name']] = {'error': '无数据返回或函数不存在'}
                print(f"    ✗ 无数据返回或函数不存在")
                
        except Exception as e:
            fundamentals_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['fundamentals_test'] = fundamentals_results
    
    # 2. 测试单个股票的详细财务数据
    print("\n" + "=" * 40)
    print("2. 测试单个股票详细财务数据")
    print("=" * 40)
    
    single_stock_results = {}
    
    # 测试招商银行的详细财务数据
    test_symbol = 'SHSE.600036'  # 招商银行
    
    single_stock_test_cases = [
        {
            'table': 'trading_derivative_indicator',
            'fields': ['PETTM', 'PBLF', 'PCTTM', 'PSTTM'],
            'name': '估值指标'
        },
        {
            'table': 'financial_indicator',
            'fields': ['ROE', 'ROA', 'ROIC', 'gross_profit_margin'],
            'name': '盈利能力指标'
        },
        {
            'table': 'income_statement',
            'fields': ['total_operating_revenue', 'net_profit', 'basic_eps'],
            'name': '利润表关键指标'
        },
        {
            'table': 'balance_sheet',
            'fields': ['total_assets', 'total_equity', 'total_liab'],
            'name': '资产负债表关键指标'
        },
        {
            'table': 'cash_flow_statement',
            'fields': ['net_operate_cash_flow', 'net_invest_cash_flow', 'net_finance_cash_flow'],
            'name': '现金流量表关键指标'
        }
    ]
    
    for case in single_stock_test_cases:
        try:
            print(f"\n测试: {test_symbol} {case['name']}")
            
            # 使用新的财务数据函数
            try:
                if case['table'] == 'trading_derivative_indicator':
                    stock_data = stk_get_daily_valuation(
                        symbol=test_symbol,
                        fields=case['fields'],
                        start_date='2022-01-01',
                        end_date='2023-12-31',
                        df=True
                    )
                elif case['table'] == 'financial_indicator':
                    stock_data = stk_get_finance_deriv(
                        symbol=test_symbol,
                        fields=case['fields'],
                        start_date='2022-01-01',
                        end_date='2023-12-31',
                        df=True
                    )
                elif case['table'] == 'income_statement':
                    stock_data = stk_get_fundamentals_income(
                        symbol=test_symbol,
                        fields=case['fields'],
                        start_date='2022-01-01',
                        end_date='2023-12-31',
                        df=True
                    )
                elif case['table'] == 'balance_sheet':
                    stock_data = stk_get_fundamentals_balance(
                        symbol=test_symbol,
                        fields=case['fields'],
                        start_date='2022-01-01',
                        end_date='2023-12-31',
                        df=True
                    )
                elif case['table'] == 'cash_flow_statement':
                    stock_data = stk_get_fundamentals_cashflow(
                        symbol=test_symbol,
                        fields=case['fields'],
                        start_date='2022-01-01',
                        end_date='2023-12-31',
                        df=True
                    )
                else:
                    stock_data = None
            except Exception as e:
                print(f"    ✗ 新财务函数调用失败: {e}")
                stock_data = None
            
            if stock_data is not None and not stock_data.empty:
                single_stock_results[case['name']] = {
                    'symbol': test_symbol,
                    'table': case['table'],
                    'fields': case['fields'],
                    'count': len(stock_data),
                    'columns': list(stock_data.columns),
                    'sample_data': stock_data.head(5).to_dict('records'),
                    'latest_data': stock_data.tail(1).to_dict('records') if len(stock_data) > 0 else None
                }
                print(f"    ✓ 获取到 {len(stock_data)} 条数据")
                print(f"    ✓ 可用字段: {list(stock_data.columns)}")
                
                # 保存到CSV
                csv_filename = f"single_stock_{case['name']}_{test_symbol.replace('.', '_')}.csv"
                stock_data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                single_stock_results[case['name']] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            single_stock_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['single_stock_test'] = single_stock_results
    
    # 3. 测试多个股票的对比分析
    print("\n" + "=" * 40)
    print("3. 测试多个股票对比分析")
    print("=" * 40)
    
    comparison_results = {}
    
    # 银行股对比分析
    bank_symbols = ['SHSE.600036', 'SHSE.600000', 'SZSE.000001', 'SHSE.601166', 'SHSE.601328']
    bank_names = ['招商银行', '浦发银行', '平安银行', '兴业银行', '交通银行']
    
    comparison_test_cases = [
        {
            'table': 'trading_derivative_indicator',
            'fields': ['PETTM', 'PBLF'],
            'name': '银行股估值对比'
        },
        {
            'table': 'financial_indicator',
            'fields': ['ROE', 'ROA'],
            'name': '银行股盈利能力对比'
        }
    ]
    
    for case in comparison_test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            # 使用新的财务数据函数 - 循环处理多个股票
            comparison_data_list = []
            try:
                for symbol in bank_symbols:
                    if case['table'] == 'trading_derivative_indicator':
                        data = stk_get_daily_valuation(
                            symbol=symbol,
                            fields=case['fields'],
                            start_date='2023-01-01',
                            end_date='2023-12-31',
                            df=True
                        )
                    elif case['table'] == 'financial_indicator':
                        data = stk_get_finance_deriv(
                            symbol=symbol,
                            fields=case['fields'],
                            start_date='2023-01-01',
                            end_date='2023-12-31',
                            df=True
                        )
                    else:
                        data = None
                    
                    if data is not None and not data.empty:
                        comparison_data_list.append(data)
                
                # 合并所有股票的数据
                if comparison_data_list:
                    comparison_data = pd.concat(comparison_data_list, ignore_index=True)
                else:
                    comparison_data = None
                    
            except Exception as e:
                print(f"    ✗ 新财务函数调用失败: {e}")
                comparison_data = None
            
            if comparison_data is not None and not comparison_data.empty:
                comparison_results[case['name']] = {
                    'symbols': bank_symbols,
                    'table': case['table'],
                    'fields': case['fields'],
                    'count': len(comparison_data),
                    'columns': list(comparison_data.columns),
                    'sample_data': comparison_data.head(10).to_dict('records')
                }
                print(f"    ✓ 获取到 {len(comparison_data)} 条对比数据")
                print(f"    ✓ 涉及股票: {len(comparison_data['symbol'].unique()) if 'symbol' in comparison_data.columns else 'N/A'} 只")
                
                # 保存到CSV
                csv_filename = f"comparison_{case['name']}.csv"
                comparison_data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                comparison_results[case['name']] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            comparison_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['comparison_test'] = comparison_results
    
    # 4. 测试基金相关财务数据
    print("\n" + "=" * 40)
    print("4. 测试基金相关财务数据")
    print("=" * 40)
    
    fund_results = {}
    
    # 测试基金相关函数
    fund_test_cases = [
        {
            'symbols': ['SHSE.510300', 'SHSE.510500', 'SHSE.510050'],
            'function': 'fnd_get_net_value',
            'name': 'ETF净值数据'
        },
        {
            'symbols': ['SHSE.510300', 'SHSE.510500', 'SHSE.510050'],
            'function': 'fnd_get_dividend',
            'name': 'ETF分红数据'
        }
    ]
    
    for case in fund_test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            # 尝试使用相应的基金函数
            try:
                if case['function'] == 'fnd_get_net_value':
                    fund_data = fnd_get_net_value(
                        fund=case['symbols'][0],  # 使用第一个基金代码
                        start_date='2023-01-01',
                        end_date='2023-12-31'
                    )
                elif case['function'] == 'fnd_get_dividend':
                    fund_data = fnd_get_dividend(
                        fund=case['symbols'][0],  # 使用第一个基金代码
                        start_date='2023-01-01',
                        end_date='2023-12-31'
                    )
                else:
                    fund_data = None
            except Exception as e:
                print(f"    ✗ {case['function']} 调用失败: {e}")
                fund_data = None
            
            if fund_data is not None and not fund_data.empty:
                fund_results[case['name']] = {
                    'function': case['function'],
                    'symbols': case['symbols'],
                    'count': len(fund_data),
                    'columns': list(fund_data.columns),
                    'sample_data': fund_data.head(5).to_dict('records')
                }
                print(f"    ✓ 获取到 {len(fund_data)} 条基金数据")
                print(f"    ✓ 列名: {list(fund_data.columns)}")
                
                # 保存到CSV
                csv_filename = f"fund_{case['name']}.csv"
                fund_data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                fund_results[case['name']] = {'error': '无数据返回或函数不存在'}
                print(f"    ✗ 无数据返回或函数不存在")
                
        except Exception as e:
            fund_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['fund_test'] = fund_results
    
    # 5. 测试财务数据的时间序列分析
    print("\n" + "=" * 40)
    print("5. 测试财务数据时间序列分析")
    print("=" * 40)
    
    timeseries_results = {}
    
    # 测试招商银行近5年的关键财务指标趋势
    try:
        print(f"\n测试: 招商银行近5年财务指标趋势")
        
        # 使用新的财务数据函数获取多年数据
        try:
            timeseries_data = stk_get_finance_deriv(
                symbol='SHSE.600036',
                fields='ROE,ROA',  # 使用基本的财务指标
                start_date='2019-01-01',
                end_date='2023-12-31',
                df=True
            )
        except Exception as e:
            print(f"    ✗ 新财务函数调用失败: {e}")
            timeseries_data = None
        
        if timeseries_data is not None and not timeseries_data.empty:
            timeseries_results['招商银行财务趋势'] = {
                'symbol': 'SHSE.600036',
                'period': '2019-2023',
                'count': len(timeseries_data),
                'columns': list(timeseries_data.columns),
                'yearly_data': timeseries_data.to_dict('records')
            }
            print(f"    ✓ 获取到 {len(timeseries_data)} 条时间序列数据")
            
            # 保存到CSV
            timeseries_data.to_csv('timeseries_cmb_financials.csv', index=False, encoding='utf-8-sig')
            print(f"    ✓ 数据已保存到: timeseries_cmb_financials.csv")
            
        else:
            timeseries_results['招商银行财务趋势'] = {'error': '无数据返回'}
            print(f"    ✗ 无数据返回")
            
    except Exception as e:
        timeseries_results['招商银行财务趋势'] = {'error': str(e)}
        print(f"    ✗ 错误: {e}")
    
    results['timeseries_test'] = timeseries_results
    
    # 保存测试结果
    with open('demo_6_fundamentals_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("财务数据查询测试完成！")
    print("详细结果已保存到: demo_6_fundamentals_results.json")
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
        test_results = test_fundamentals()
        
        # 打印总结
        print("\n测试总结:")
        
        if 'fundamentals_test' in test_results:
            total_fundamentals = len(test_results['fundamentals_test'])
            successful_fundamentals = sum(1 for data in test_results['fundamentals_test'].values() if 'error' not in data)
            print(f"get_fundamentals函数测试: {successful_fundamentals}/{total_fundamentals} 成功")
        
        if 'single_stock_test' in test_results:
            total_single = len(test_results['single_stock_test'])
            successful_single = sum(1 for data in test_results['single_stock_test'].values() if 'error' not in data)
            print(f"单股票财务数据测试: {successful_single}/{total_single} 成功")
        
        if 'comparison_test' in test_results:
            total_comparison = len(test_results['comparison_test'])
            successful_comparison = sum(1 for data in test_results['comparison_test'].values() if 'error' not in data)
            print(f"多股票对比分析测试: {successful_comparison}/{total_comparison} 成功")
        
        if 'fund_test' in test_results:
            total_fund = len(test_results['fund_test'])
            successful_fund = sum(1 for data in test_results['fund_test'].values() if 'error' not in data)
            print(f"基金财务数据测试: {successful_fund}/{total_fund} 成功")
        
        timeseries_success = 'error' not in test_results.get('timeseries_test', {'error': 'not tested'})
        print(f"时间序列分析测试: {'成功' if timeseries_success else '失败'}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()