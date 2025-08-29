#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
行业数据查询演示

本脚本演示如何使用GM SDK获取行业相关数据，包括：
1. stk_get_industry_category - 查询行业分类信息
2. stk_get_industry_constituents - 查询行业成分股
3. stk_get_symbol_industry - 查询股票所属行业
4. stk_get_sector_category - 查询板块分类信息
5. stk_get_sector_constituents - 查询板块成分股
6. stk_get_symbol_sector - 查询股票所属板块

行业数据是基本面分析的重要组成部分，用于行业比较和投资决策
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

def test_industry_category():
    """
    测试行业分类查询
    """
    print("\n=== 测试 stk_get_industry_category 函数 - 获取行业分类信息 ===")
    
    test_results = []
    
    try:
        # 获取所有行业分类
        result = stk_get_industry_category()
        
        if result:
            print(f"✓ 成功获取行业分类数据，共 {len(result)} 个行业")
            
            # 转换为DataFrame
            df = pd.DataFrame(result)
            
            # 显示前几个行业分类
            print("\n前10个行业分类:")
            for i, industry in enumerate(result[:10]):
                industry_code = industry.get('industry_code', 'N/A')
                industry_name = industry.get('industry_name', 'N/A')
                parent_code = industry.get('parent_industry_code', 'N/A')
                level = industry.get('industry_level', 'N/A')
                print(f"  {i+1}. {industry_name} ({industry_code}) - 级别:{level} - 父级:{parent_code}")
            
            # 按级别统计
            if 'industry_level' in df.columns:
                level_counts = df['industry_level'].value_counts().sort_index()
                print("\n按级别统计:")
                for level, count in level_counts.items():
                    print(f"  级别 {level}: {count} 个行业")
            
            # 保存为CSV
            csv_filename = "industry_categories.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"\n✓ 行业分类数据已保存到 {csv_filename}")
            
            test_result = {
                'test_name': '行业分类查询',
                'function': 'stk_get_industry_category',
                'status': 'success',
                'result_count': len(result),
                'sample_data': result[:5]
            }
        else:
            print("✗ 未获取到行业分类数据")
            test_result = {
                'test_name': '行业分类查询',
                'function': 'stk_get_industry_category',
                'status': 'no_data'
            }
            
    except Exception as e:
        print(f"✗ 获取行业分类数据错误: {e}")
        test_result = {
            'test_name': '行业分类查询',
            'function': 'stk_get_industry_category',
            'status': 'error',
            'error': str(e)
        }
    
    test_results.append(test_result)
    return test_results

def test_industry_constituents():
    """
    测试行业成分股查询
    """
    print("\n=== 测试 stk_get_industry_constituents 函数 - 获取行业成分股 ===")
    
    test_results = []
    
    # 热门行业代码（这些需要根据实际的行业分类代码调整）
    popular_industries = [
        '801010',  # 石油石化
        '801020',  # 煤炭
        '801030',  # 有色金属
        '801040',  # 钢铁
        '801050',  # 基础化工
        '801080',  # 电子
        '801110',  # 家用电器
        '801120',  # 食品饮料
        '801130',  # 纺织服装
        '801140',  # 轻工制造
        '801150',  # 医药生物
        '801160',  # 公用事业
        '801170',  # 交通运输
        '801180',  # 房地产
        '801200',  # 商业贸易
        '801210',  # 休闲服务
        '801230',  # 银行
        '801710',  # 建筑材料
        '801720',  # 建筑装饰
        '801730',  # 电气设备
        '801740',  # 国防军工
        '801750',  # 计算机
        '801760',  # 传媒
        '801770',  # 通信
        '801780',  # 汽车
        '801790',  # 机械设备
    ]
    
    try:
        # 测试几个主要行业
        test_industries = popular_industries[:5]  # 测试前5个行业
        
        for industry_code in test_industries:
            print(f"\n查询行业 {industry_code} 的成分股...")
            
            try:
                result = stk_get_industry_constituents(
                    industry_code=industry_code
                )
                
                if result:
                    print(f"  ✓ 行业 {industry_code}: 成功获取 {len(result)} 只成分股")
                    
                    # 显示前几只股票
                    print(f"  前5只成分股:")
                    for i, stock in enumerate(result[:5]):
                        symbol = stock.get('symbol', 'N/A')
                        sec_name = stock.get('sec_name', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name}")
                    
                    # 保存为CSV
                    df = pd.DataFrame(result)
                    csv_filename = f"industry_{industry_code}_constituents.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  ✓ 数据已保存到 {csv_filename}")
                    
                    test_result = {
                        'industry_code': industry_code,
                        'function': 'stk_get_industry_constituents',
                        'status': 'success',
                        'constituent_count': len(result),
                        'sample_stocks': result[:3]
                    }
                else:
                    print(f"  ✗ 行业 {industry_code}: 无成分股数据")
                    test_result = {
                        'industry_code': industry_code,
                        'function': 'stk_get_industry_constituents',
                        'status': 'no_data'
                    }
                    
            except Exception as e:
                print(f"  ✗ 行业 {industry_code}: 错误 - {e}")
                test_result = {
                    'industry_code': industry_code,
                    'function': 'stk_get_industry_constituents',
                    'status': 'error',
                    'error': str(e)
                }
            
            test_results.append(test_result)
            
    except Exception as e:
        print(f"✗ 行业成分股查询错误: {e}")
        test_results.append({
            'function': 'stk_get_industry_constituents',
            'status': 'error',
            'error': str(e)
        })
    
    return test_results

def test_symbol_industry():
    """
    测试股票所属行业查询
    """
    print("\n=== 测试 stk_get_symbol_industry 函数 - 获取股票所属行业 ===")
    
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
        'SZSE.000002',  # 万科A
        'SHSE.601166',  # 兴业银行
        'SZSE.000001'   # 平安银行
    ]
    
    try:
        all_industry_data = []
        
        for symbol in popular_stocks:
            print(f"\n查询 {symbol} 的所属行业...")
            
            try:
                result = stk_get_symbol_industry(
                    symbols=[symbol]
                )
                
                if result:
                    all_industry_data.extend(result)
                    
                    for data in result:
                        industry_code = data.get('industry_code', 'N/A')
                        industry_name = data.get('industry_name', 'N/A')
                        level = data.get('industry_level', 'N/A')
                        print(f"  ✓ {symbol}: {industry_name} ({industry_code}) - 级别:{level}")
                else:
                    print(f"  ✗ {symbol}: 无行业数据")
                    
            except Exception as e:
                print(f"  ✗ {symbol}: 错误 - {e}")
        
        if all_industry_data:
            # 保存所有数据
            df = pd.DataFrame(all_industry_data)
            csv_filename = "stocks_industry_mapping.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"\n✓ 股票行业映射数据已保存到 {csv_filename}")
            
            # 行业分布统计
            analyze_industry_distribution(df)
            
            test_result = {
                'test_name': '股票所属行业查询',
                'function': 'stk_get_symbol_industry',
                'status': 'success',
                'symbols_count': len(popular_stocks),
                'result_count': len(all_industry_data),
                'sample_data': all_industry_data[:5]
            }
        else:
            test_result = {
                'test_name': '股票所属行业查询',
                'function': 'stk_get_symbol_industry',
                'status': 'no_data'
            }
            
    except Exception as e:
        print(f"✗ 股票所属行业查询错误: {e}")
        test_result = {
            'test_name': '股票所属行业查询',
            'function': 'stk_get_symbol_industry',
            'status': 'error',
            'error': str(e)
        }
    
    test_results.append(test_result)
    return test_results

def analyze_industry_distribution(df):
    """
    分析行业分布
    """
    print("\n=== 行业分布分析 ===")
    
    try:
        if 'industry_name' in df.columns:
            industry_counts = df['industry_name'].value_counts()
            print("\n行业分布统计:")
            for industry, count in industry_counts.head(10).items():
                print(f"  {industry}: {count} 只股票")
        
        if 'industry_level' in df.columns:
            level_counts = df['industry_level'].value_counts().sort_index()
            print("\n按行业级别统计:")
            for level, count in level_counts.items():
                print(f"  级别 {level}: {count} 条记录")
                
    except Exception as e:
        print(f"✗ 行业分布分析错误: {e}")

def test_sector_data():
    """
    测试板块相关数据查询
    """
    print("\n=== 测试板块数据查询功能 ===")
    
    test_results = []
    
    # 测试板块分类
    print("\n--- 测试板块分类查询 ---")
    try:
        sector_categories = stk_get_sector_category()
        
        if sector_categories:
            print(f"✓ 成功获取板块分类数据，共 {len(sector_categories)} 个板块")
            
            # 显示前几个板块
            print("\n前10个板块分类:")
            for i, sector in enumerate(sector_categories[:10]):
                sector_code = sector.get('sector_code', 'N/A')
                sector_name = sector.get('sector_name', 'N/A')
                print(f"  {i+1}. {sector_name} ({sector_code})")
            
            # 保存板块分类数据
            df_sectors = pd.DataFrame(sector_categories)
            df_sectors.to_csv('sector_categories.csv', index=False, encoding='utf-8-sig')
            print(f"\n✓ 板块分类数据已保存到 sector_categories.csv")
            
            test_results.append({
                'test_name': '板块分类查询',
                'function': 'stk_get_sector_category',
                'status': 'success',
                'result_count': len(sector_categories)
            })
        else:
            print("✗ 未获取到板块分类数据")
            test_results.append({
                'test_name': '板块分类查询',
                'function': 'stk_get_sector_category',
                'status': 'no_data'
            })
            
    except Exception as e:
        print(f"✗ 板块分类查询错误: {e}")
        test_results.append({
            'test_name': '板块分类查询',
            'function': 'stk_get_sector_category',
            'status': 'error',
            'error': str(e)
        })
    
    # 测试股票所属板块
    print("\n--- 测试股票所属板块查询 ---")
    try:
        test_symbols = ['SHSE.600519', 'SHSE.600036', 'SZSE.000858']
        all_sector_data = []
        
        for symbol in test_symbols:
            try:
                result = stk_get_symbol_sector(symbols=[symbol])
                
                if result:
                    all_sector_data.extend(result)
                    
                    for data in result:
                        sector_code = data.get('sector_code', 'N/A')
                        sector_name = data.get('sector_name', 'N/A')
                        print(f"  ✓ {symbol}: {sector_name} ({sector_code})")
                else:
                    print(f"  ✗ {symbol}: 无板块数据")
                    
            except Exception as e:
                print(f"  ✗ {symbol}: 错误 - {e}")
        
        if all_sector_data:
            df_symbol_sectors = pd.DataFrame(all_sector_data)
            df_symbol_sectors.to_csv('stocks_sector_mapping.csv', index=False, encoding='utf-8-sig')
            print(f"\n✓ 股票板块映射数据已保存到 stocks_sector_mapping.csv")
            
            test_results.append({
                'test_name': '股票所属板块查询',
                'function': 'stk_get_symbol_sector',
                'status': 'success',
                'result_count': len(all_sector_data)
            })
        else:
            test_results.append({
                'test_name': '股票所属板块查询',
                'function': 'stk_get_symbol_sector',
                'status': 'no_data'
            })
            
    except Exception as e:
        print(f"✗ 股票所属板块查询错误: {e}")
        test_results.append({
            'test_name': '股票所属板块查询',
            'function': 'stk_get_symbol_sector',
            'status': 'error',
            'error': str(e)
        })
    
    return test_results

def test_comprehensive_industry_analysis():
    """
    综合行业分析
    """
    print("\n=== 综合行业分析 ===")
    
    test_results = []
    
    try:
        # 选择几个代表性行业进行深度分析
        target_industries = ['801120', '801230', '801080']  # 食品饮料、银行、电子
        industry_names = ['食品饮料', '银行', '电子']
        
        comprehensive_data = []
        
        for industry_code, industry_name in zip(target_industries, industry_names):
            print(f"\n分析 {industry_name} 行业 ({industry_code})...")
            
            try:
                # 获取行业成分股
                constituents = stk_get_industry_constituents(industry_code=industry_code)
                
                if constituents:
                    print(f"  ✓ {industry_name}: 共 {len(constituents)} 只成分股")
                    
                    # 分析行业数据
                    industry_analysis = {
                        'industry_code': industry_code,
                        'industry_name': industry_name,
                        'constituent_count': len(constituents),
                        'constituents': constituents[:10]  # 保存前10只股票
                    }
                    
                    comprehensive_data.append(industry_analysis)
                    
                    # 显示代表性股票
                    print(f"  代表性股票:")
                    for i, stock in enumerate(constituents[:5]):
                        symbol = stock.get('symbol', 'N/A')
                        sec_name = stock.get('sec_name', 'N/A')
                        print(f"    {i+1}. {symbol} - {sec_name}")
                else:
                    print(f"  ✗ {industry_name}: 无成分股数据")
                    
            except Exception as e:
                print(f"  ✗ {industry_name}: 错误 - {e}")
        
        # 生成综合分析报告
        if comprehensive_data:
            generate_industry_report(comprehensive_data)
            
            test_result = {
                'test_name': '综合行业分析',
                'function': 'comprehensive_industry_analysis',
                'status': 'success',
                'industries_analyzed': len(comprehensive_data),
                'analysis_data': comprehensive_data
            }
        else:
            test_result = {
                'test_name': '综合行业分析',
                'function': 'comprehensive_industry_analysis',
                'status': 'no_data'
            }
            
    except Exception as e:
        print(f"✗ 综合行业分析错误: {e}")
        test_result = {
            'test_name': '综合行业分析',
            'function': 'comprehensive_industry_analysis',
            'status': 'error',
            'error': str(e)
        }
    
    test_results.append(test_result)
    return test_results

def generate_industry_report(comprehensive_data):
    """
    生成行业分析报告
    """
    print("\n=== 行业分析报告 ===")
    
    try:
        total_stocks = sum(data['constituent_count'] for data in comprehensive_data)
        
        print(f"分析行业数量: {len(comprehensive_data)}")
        print(f"涉及股票总数: {total_stocks}")
        
        print("\n各行业成分股数量:")
        for data in comprehensive_data:
            industry_name = data['industry_name']
            count = data['constituent_count']
            percentage = (count / total_stocks * 100) if total_stocks > 0 else 0
            print(f"  {industry_name}: {count} 只股票 ({percentage:.1f}%)")
        
        # 保存报告数据
        report_df = pd.DataFrame([
            {
                'industry_code': data['industry_code'],
                'industry_name': data['industry_name'],
                'constituent_count': data['constituent_count']
            }
            for data in comprehensive_data
        ])
        
        report_df.to_csv('industry_analysis_report.csv', index=False, encoding='utf-8-sig')
        print("\n✓ 行业分析报告已保存到 industry_analysis_report.csv")
        
    except Exception as e:
        print(f"✗ 生成行业报告错误: {e}")

def main():
    """
    主函数
    """
    print("开始测试GM SDK 行业数据查询功能...")
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
        # 测试行业分类查询
        industry_category_results = test_industry_category()
        all_results['tests']['industry_category'] = industry_category_results
        
        # 测试行业成分股查询
        industry_constituents_results = test_industry_constituents()
        all_results['tests']['industry_constituents'] = industry_constituents_results
        
        # 测试股票所属行业查询
        symbol_industry_results = test_symbol_industry()
        all_results['tests']['symbol_industry'] = symbol_industry_results
        
        # 测试板块数据查询
        sector_data_results = test_sector_data()
        all_results['tests']['sector_data'] = sector_data_results
        
        # 综合行业分析
        comprehensive_results = test_comprehensive_industry_analysis()
        all_results['tests']['comprehensive_analysis'] = comprehensive_results
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        all_results['error'] = str(e)
    
    # 保存测试结果
    with open('industry_data_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n=== 测试总结 ===")
    print(f"测试时间: {all_results['test_time']}")
    
    if 'tests' in all_results:
        for test_type, results in all_results['tests'].items():
            if isinstance(results, list):
                total_tests = len(results)
                successful_tests = sum(1 for result in results if result.get('status') == 'success')
                print(f"{test_type}测试: {successful_tests}/{total_tests} 成功")
    
    print("\n✓ 测试结果已保存到 industry_data_test_results.json")
    print("✓ CSV数据文件已保存到当前目录")
    print("\n行业数据说明:")
    print("- 行业分类采用申万行业分类标准")
    print("- 行业级别: 1级为一级行业，2级为二级行业，3级为三级行业")
    print("- 板块分类包含概念板块、地域板块等")
    print("- 成分股数据会根据市场变化定期调整")

if __name__ == '__main__':
    main()