#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资金流数据查询演示

本脚本演示如何使用GM SDK获取资金流数据，包括：
1. stk_get_money_flow - 查询个股资金流数据
2. 主力资金流向分析
3. 北向资金流向分析（通过沪深港通数据）
4. 资金流数据的统计分析

资金流数据是技术分析中的重要指标，用于判断资金的流入流出情况
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from gm.api import *
import os

# ============================================================
# Token配置 - 从配置文件读取
# ============================================================

def configure_token():
    """
    配置GM SDK的token
    支持多种配置方式：
    1. 从配置文件读取（推荐）
    2. 从环境变量读取
    3. 直接设置token
    """
    
    # 方法1: 从配置文件读取（推荐）
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
    
    # 方法2: 从环境变量读取
    token = os.getenv('GM_TOKEN')
    if token:
        set_token(token)
        print("已从环境变量 GM_TOKEN 读取token")
        return True
    
    # 方法3: 直接设置token（备用）
    set_token('d5791ecb0f33260e9fd719227c36f5c28b42e11c')
    print("使用默认token")
    return True

def test_stock_money_flow():
    """
    测试个股资金流数据
    """
    print("\n=== 测试 stk_get_money_flow 函数 - 获取个股资金流数据 ===")
    
    test_results = []
    
    # 热门股票列表
    popular_stocks = [
        'SHSE.600519',  # 贵州茅台
        'SHSE.600036',  # 招商银行
        'SZSE.000858',  # 五粮液
        'SZSE.300750',  # 宁德时代
        'SHSE.600000',  # 浦发银行
        'SZSE.002415',  # 海康威视
        'SHSE.601318',  # 中国平安
        'SZSE.000002'   # 万科A
    ]
    
    # 获取最近的交易日
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 测试用例
        test_cases = [
            {
                'symbols': popular_stocks[:3],
                'trade_date': end_date,
                'name': '获取热门股票当日资金流数据'
            },
            {
                'symbols': popular_stocks[3:6],
                'trade_date': end_date,
                'name': '获取科技股资金流数据'
            },
            {
                'symbols': popular_stocks[6:8],
                'trade_date': end_date,
                'name': '获取金融股资金流数据'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试{i}: {case['name']}")
            
            all_money_flow_data = []
            
            for symbol in case['symbols']:
                try:
                    result = stk_get_money_flow(
                        symbols=[symbol],
                        trade_date=case['trade_date']
                    )
                    
                    if result:
                        all_money_flow_data.extend(result)
                        print(f"  ✓ {symbol}: 成功获取资金流数据")
                        
                        # 显示资金流详情
                        for data in result:
                            net_amount = data.get('net_amount_main', 0)
                            net_amount_large = data.get('net_amount_large', 0)
                            net_amount_medium = data.get('net_amount_medium', 0)
                            net_amount_small = data.get('net_amount_small', 0)
                            
                            print(f"    主力净流入: {net_amount:,.0f}万元")
                            print(f"    大单净流入: {net_amount_large:,.0f}万元")
                            print(f"    中单净流入: {net_amount_medium:,.0f}万元")
                            print(f"    小单净流入: {net_amount_small:,.0f}万元")
                    else:
                        print(f"  ✗ {symbol}: 无资金流数据")
                        
                except Exception as e:
                    print(f"  ✗ {symbol}: 错误 - {e}")
            
            test_result = {
                'test_name': case['name'],
                'function': 'stk_get_money_flow',
                'symbols': case['symbols'],
                'trade_date': case['trade_date'],
                'status': 'success' if all_money_flow_data else 'no_data',
                'result_count': len(all_money_flow_data),
                'sample_data': all_money_flow_data[:3] if all_money_flow_data else None
            }
            
            # 保存为CSV
            if all_money_flow_data:
                df = pd.DataFrame(all_money_flow_data)
                csv_filename = f"money_flow_{case['name'].replace(' ', '_').replace('（', '_').replace('）', '')}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  ✓ 数据已保存到 {csv_filename}")
                
                # 资金流统计分析
                analyze_money_flow_data(df, case['name'])
            
            test_results.append(test_result)
            
    except Exception as e:
        print(f"  ✗ 获取交易日期错误: {e}")
        test_results.append({
            'function': 'stk_get_money_flow',
            'status': 'error',
            'error': f'获取交易日期错误: {e}'
        })
    
    return test_results

def analyze_money_flow_data(df, test_name):
    """
    分析资金流数据
    """
    print(f"\n  === {test_name} 资金流分析 ===")
    
    if df.empty:
        print("  无数据可分析")
        return
    
    try:
        # 主力资金净流入统计
        if 'net_amount_main' in df.columns:
            main_inflow = df['net_amount_main'].sum()
            main_inflow_positive = df[df['net_amount_main'] > 0]['net_amount_main'].sum()
            main_inflow_negative = df[df['net_amount_main'] < 0]['net_amount_main'].sum()
            
            print(f"  主力资金总净流入: {main_inflow:,.0f}万元")
            print(f"  主力资金流入: {main_inflow_positive:,.0f}万元")
            print(f"  主力资金流出: {main_inflow_negative:,.0f}万元")
        
        # 大中小单资金流向统计
        flow_types = ['large', 'medium', 'small']
        flow_names = ['大单', '中单', '小单']
        
        for flow_type, flow_name in zip(flow_types, flow_names):
            col_name = f'net_amount_{flow_type}'
            if col_name in df.columns:
                net_flow = df[col_name].sum()
                print(f"  {flow_name}净流入: {net_flow:,.0f}万元")
        
        # 资金流入流出股票数量统计
        if 'net_amount_main' in df.columns:
            inflow_count = len(df[df['net_amount_main'] > 0])
            outflow_count = len(df[df['net_amount_main'] < 0])
            neutral_count = len(df[df['net_amount_main'] == 0])
            
            print(f"  主力资金净流入股票数: {inflow_count}")
            print(f"  主力资金净流出股票数: {outflow_count}")
            print(f"  主力资金持平股票数: {neutral_count}")
        
        # 资金流排行榜
        if 'net_amount_main' in df.columns and 'symbol' in df.columns:
            print(f"\n  === 主力资金流入排行榜 ===")
            top_inflow = df.nlargest(3, 'net_amount_main')[['symbol', 'net_amount_main']]
            for idx, row in top_inflow.iterrows():
                print(f"  {row['symbol']}: {row['net_amount_main']:,.0f}万元")
            
            print(f"\n  === 主力资金流出排行榜 ===")
            top_outflow = df.nsmallest(3, 'net_amount_main')[['symbol', 'net_amount_main']]
            for idx, row in top_outflow.iterrows():
                print(f"  {row['symbol']}: {row['net_amount_main']:,.0f}万元")
        
    except Exception as e:
        print(f"  ✗ 资金流分析错误: {e}")

def test_market_money_flow_summary():
    """
    测试市场整体资金流概况
    """
    print("\n=== 市场整体资金流概况分析 ===")
    
    test_results = []
    
    # 选择代表性股票进行市场分析
    market_samples = {
        '大盘蓝筹': ['SHSE.600519', 'SHSE.600036', 'SHSE.601318', 'SHSE.600000', 'SHSE.601166'],
        '科技成长': ['SZSE.300750', 'SZSE.002415', 'SZSE.300059', 'SZSE.002594', 'SZSE.300142'],
        '消费白马': ['SZSE.000858', 'SZSE.000568', 'SZSE.002304', 'SHSE.600887', 'SHSE.603288']
    }
    
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        market_summary = {}
        
        for sector_name, symbols in market_samples.items():
            print(f"\n分析{sector_name}板块资金流...")
            
            sector_data = []
            
            for symbol in symbols:
                try:
                    result = stk_get_money_flow(
                        symbols=[symbol],
                        trade_date=end_date
                    )
                    
                    if result:
                        sector_data.extend(result)
                        
                except Exception as e:
                    print(f"  ✗ {symbol}: {e}")
            
            if sector_data:
                df = pd.DataFrame(sector_data)
                
                # 计算板块资金流汇总
                sector_summary = {
                    'sector': sector_name,
                    'stock_count': len(df),
                    'main_net_inflow': df['net_amount_main'].sum() if 'net_amount_main' in df.columns else 0,
                    'large_net_inflow': df['net_amount_large'].sum() if 'net_amount_large' in df.columns else 0,
                    'medium_net_inflow': df['net_amount_medium'].sum() if 'net_amount_medium' in df.columns else 0,
                    'small_net_inflow': df['net_amount_small'].sum() if 'net_amount_small' in df.columns else 0,
                    'inflow_stocks': len(df[df['net_amount_main'] > 0]) if 'net_amount_main' in df.columns else 0,
                    'outflow_stocks': len(df[df['net_amount_main'] < 0]) if 'net_amount_main' in df.columns else 0
                }
                
                market_summary[sector_name] = sector_summary
                
                print(f"  {sector_name}主力净流入: {sector_summary['main_net_inflow']:,.0f}万元")
                print(f"  净流入股票数: {sector_summary['inflow_stocks']}/{sector_summary['stock_count']}")
                
                # 保存板块数据
                csv_filename = f"money_flow_{sector_name}_summary.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  ✓ {sector_name}数据已保存到 {csv_filename}")
        
        # 生成市场资金流总结报告
        if market_summary:
            generate_market_flow_report(market_summary)
        
        test_result = {
            'test_name': '市场整体资金流概况',
            'function': 'market_money_flow_analysis',
            'status': 'success' if market_summary else 'no_data',
            'sectors_analyzed': len(market_summary),
            'summary': market_summary
        }
        
        test_results.append(test_result)
        
    except Exception as e:
        print(f"  ✗ 市场资金流分析错误: {e}")
        test_results.append({
            'function': 'market_money_flow_analysis',
            'status': 'error',
            'error': str(e)
        })
    
    return test_results

def generate_market_flow_report(market_summary):
    """
    生成市场资金流报告
    """
    print("\n=== 市场资金流总结报告 ===")
    
    # 计算市场总体情况
    total_main_inflow = sum(data['main_net_inflow'] for data in market_summary.values())
    total_inflow_stocks = sum(data['inflow_stocks'] for data in market_summary.values())
    total_outflow_stocks = sum(data['outflow_stocks'] for data in market_summary.values())
    total_stocks = sum(data['stock_count'] for data in market_summary.values())
    
    print(f"样本股票总数: {total_stocks}")
    print(f"主力资金总净流入: {total_main_inflow:,.0f}万元")
    print(f"净流入股票数: {total_inflow_stocks}")
    print(f"净流出股票数: {total_outflow_stocks}")
    print(f"资金净流入比例: {total_inflow_stocks/total_stocks*100:.1f}%")
    
    # 板块资金流排行
    print("\n=== 板块主力资金流排行 ===")
    sorted_sectors = sorted(market_summary.items(), key=lambda x: x[1]['main_net_inflow'], reverse=True)
    
    for sector, data in sorted_sectors:
        flow_direction = "流入" if data['main_net_inflow'] > 0 else "流出"
        print(f"{sector}: {data['main_net_inflow']:,.0f}万元 ({flow_direction})")
    
    # 保存报告
    report_df = pd.DataFrame(market_summary).T
    report_df.to_csv('market_money_flow_report.csv', encoding='utf-8-sig')
    print("\n✓ 市场资金流报告已保存到 market_money_flow_report.csv")

def test_money_flow_indicators():
    """
    测试资金流相关指标计算
    """
    print("\n=== 资金流指标计算演示 ===")
    
    test_results = []
    
    # 选择几只代表性股票
    test_symbols = ['SHSE.600519', 'SHSE.600036', 'SZSE.000858']
    
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        for symbol in test_symbols:
            print(f"\n分析 {symbol} 资金流指标...")
            
            try:
                result = stk_get_money_flow(
                    symbols=[symbol],
                    trade_date=end_date
                )
                
                if result and len(result) > 0:
                    data = result[0]
                    
                    # 计算资金流指标
                    indicators = calculate_money_flow_indicators(data)
                    
                    print(f"  === {symbol} 资金流指标 ===")
                    for indicator, value in indicators.items():
                        print(f"  {indicator}: {value}")
                    
                    test_result = {
                        'symbol': symbol,
                        'function': 'money_flow_indicators',
                        'status': 'success',
                        'indicators': indicators
                    }
                else:
                    print(f"  ✗ {symbol}: 无资金流数据")
                    test_result = {
                        'symbol': symbol,
                        'function': 'money_flow_indicators',
                        'status': 'no_data'
                    }
                
            except Exception as e:
                print(f"  ✗ {symbol}: 错误 - {e}")
                test_result = {
                    'symbol': symbol,
                    'function': 'money_flow_indicators',
                    'status': 'error',
                    'error': str(e)
                }
            
            test_results.append(test_result)
    
    except Exception as e:
        print(f"  ✗ 资金流指标计算错误: {e}")
        test_results.append({
            'function': 'money_flow_indicators',
            'status': 'error',
            'error': str(e)
        })
    
    return test_results

def calculate_money_flow_indicators(data):
    """
    计算资金流相关指标
    """
    indicators = {}
    
    try:
        # 获取各类资金流数据
        main_flow = data.get('net_amount_main', 0)
        large_flow = data.get('net_amount_large', 0)
        medium_flow = data.get('net_amount_medium', 0)
        small_flow = data.get('net_amount_small', 0)
        
        # 总成交额
        total_amount = data.get('amount', 0)
        
        # 计算资金流指标
        indicators['主力净流入(万元)'] = f"{main_flow:,.0f}"
        indicators['大单净流入(万元)'] = f"{large_flow:,.0f}"
        indicators['中单净流入(万元)'] = f"{medium_flow:,.0f}"
        indicators['小单净流入(万元)'] = f"{small_flow:,.0f}"
        
        # 资金流入流出比例
        if total_amount > 0:
            indicators['主力资金流入比例(%)'] = f"{(main_flow / total_amount * 100):.2f}"
        
        # 资金流强度
        total_net_flow = abs(main_flow) + abs(large_flow) + abs(medium_flow) + abs(small_flow)
        if total_net_flow > 0:
            indicators['主力资金占比(%)'] = f"{(abs(main_flow) / total_net_flow * 100):.2f}"
        
        # 资金流方向判断
        if main_flow > 0:
            indicators['主力资金方向'] = "净流入"
        elif main_flow < 0:
            indicators['主力资金方向'] = "净流出"
        else:
            indicators['主力资金方向'] = "持平"
        
        # 资金流强度等级
        if abs(main_flow) >= 10000:
            indicators['资金流强度'] = "强"
        elif abs(main_flow) >= 5000:
            indicators['资金流强度'] = "中"
        elif abs(main_flow) >= 1000:
            indicators['资金流强度'] = "弱"
        else:
            indicators['资金流强度'] = "微弱"
        
    except Exception as e:
        indicators['计算错误'] = str(e)
    
    return indicators

def main():
    """
    主函数
    """
    print("开始测试GM SDK 资金流数据查询功能...")
    print("=" * 60)
    
    # 配置token
    if not configure_token():
        print("Token配置失败，退出测试")
        return
    
    # 存储所有测试结果
    all_results = {
        'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {}
    }
    
    try:
        # 测试个股资金流数据
        stock_flow_results = test_stock_money_flow()
        all_results['tests']['stock_money_flow'] = stock_flow_results
        
        # 测试市场整体资金流概况
        market_flow_results = test_market_money_flow_summary()
        all_results['tests']['market_money_flow'] = market_flow_results
        
        # 测试资金流指标计算
        indicators_results = test_money_flow_indicators()
        all_results['tests']['money_flow_indicators'] = indicators_results
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        all_results['error'] = str(e)
    
    # 保存测试结果
    with open('money_flow_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n=== 测试总结 ===")
    print(f"测试时间: {all_results['test_time']}")
    
    if 'tests' in all_results:
        for test_type, results in all_results['tests'].items():
            if isinstance(results, list):
                total_tests = len(results)
                successful_tests = sum(1 for result in results if result.get('status') == 'success')
                print(f"{test_type}测试: {successful_tests}/{total_tests} 成功")
    
    print("\n✓ 测试结果已保存到 money_flow_test_results.json")
    print("✓ CSV数据文件已保存到当前目录")
    print("\n资金流数据说明:")
    print("- 主力资金: 大于等于50万元的成交单")
    print("- 大单资金: 大于等于20万元的成交单")
    print("- 中单资金: 5万元到20万元之间的成交单")
    print("- 小单资金: 小于5万元的成交单")
    print("- 净流入 = 流入资金 - 流出资金")

if __name__ == '__main__':
    main()