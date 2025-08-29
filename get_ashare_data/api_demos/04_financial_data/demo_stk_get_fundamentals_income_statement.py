#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo for gm.stk_get_fundamentals_income_statement() API
测试获取股票利润表数据的API接口

主要功能:
1. 测试单个股票的利润表查询
2. 测试多个股票的批量查询
3. 测试不同时间段的查询
4. 测试边界情况和异常处理
5. 数据结构分析和保存
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import gm
except ImportError:
    print("请先安装gm库: pip install gm")
    sys.exit(1)

def init_api():
    """初始化API连接"""
    try:
        # 这里需要替换为实际的token
        # gm.set_token('your_token_here')
        print("API初始化成功")
        return True
    except Exception as e:
        print(f"API初始化失败: {e}")
        return False

def income_statement_to_dict(income_obj):
    """将利润表对象转换为字典"""
    if income_obj is None:
        return None
    
    # 获取对象的所有属性
    result = {}
    for attr in dir(income_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(income_obj, attr)
                if not callable(value):
                    result[attr] = value
            except:
                continue
    
    return result

def analyze_income_statement_structure(data_list):
    """分析利润表数据结构"""
    if not data_list:
        return {"error": "数据为空"}
    
    analysis = {
        "total_records": len(data_list),
        "fields": set(),
        "sample_data": data_list[0] if data_list else None,
        "symbols": set(),
        "pub_dates": set(),
        "report_dates": set(),
        "revenue_stats": {"min": None, "max": None, "avg": None},
        "net_profit_stats": {"min": None, "max": None, "avg": None}
    }
    
    revenues = []
    net_profits = []
    
    for item in data_list:
        if isinstance(item, dict):
            analysis["fields"].update(item.keys())
            if 'symbol' in item:
                analysis["symbols"].add(item['symbol'])
            if 'pub_date' in item:
                analysis["pub_dates"].add(str(item['pub_date']))
            if 'end_date' in item:
                analysis["report_dates"].add(str(item['end_date']))
            
            # 收集营业收入和净利润数据
            if 'total_revenue' in item and item['total_revenue'] is not None:
                try:
                    revenues.append(float(item['total_revenue']))
                except:
                    pass
            
            if 'net_profit' in item and item['net_profit'] is not None:
                try:
                    net_profits.append(float(item['net_profit']))
                except:
                    pass
    
    # 计算统计信息
    if revenues:
        analysis["revenue_stats"] = {
            "min": min(revenues),
            "max": max(revenues),
            "avg": sum(revenues) / len(revenues)
        }
    
    if net_profits:
        analysis["net_profit_stats"] = {
            "min": min(net_profits),
            "max": max(net_profits),
            "avg": sum(net_profits) / len(net_profits)
        }
    
    # 转换set为list以便JSON序列化
    analysis["fields"] = sorted(list(analysis["fields"]))
    analysis["symbols"] = sorted(list(analysis["symbols"]))
    analysis["pub_dates"] = sorted(list(analysis["pub_dates"]))
    analysis["report_dates"] = sorted(list(analysis["report_dates"]))
    
    return analysis

def save_results(data, filename_prefix, analysis=None):
    """保存结果到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存JSON格式
    json_filename = f"{filename_prefix}_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "data": data,
            "analysis": analysis,
            "timestamp": timestamp,
            "total_records": len(data) if isinstance(data, list) else 1
        }, f, ensure_ascii=False, indent=2, default=str)
    
    # 保存CSV格式（如果数据是列表）
    if isinstance(data, list) and data:
        try:
            df = pd.DataFrame(data)
            csv_filename = f"{filename_prefix}_{timestamp}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"数据已保存到: {json_filename} 和 {csv_filename}")
        except Exception as e:
            print(f"保存CSV失败: {e}，仅保存JSON格式")
            print(f"数据已保存到: {json_filename}")
    else:
        print(f"数据已保存到: {json_filename}")

def test_single_stock_income_statement():
    """测试单个股票的利润表查询"""
    print("\n=== 测试单个股票利润表查询 ===")
    
    # 测试平安银行的利润表
    symbol = 'SZSE.000001'
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbol}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_income_statement(
            symbols=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"返回数据类型: {type(result)}")
        print(f"返回数据长度: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = income_statement_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = income_statement_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 显示前几条数据的关键字段
            print("\n前3条数据的关键信息:")
            for i, item in enumerate(data_list[:3]):
                print(f"  记录{i+1}: 股票={item.get('symbol', 'N/A')}, "
                      f"报告期={item.get('end_date', 'N/A')}, "
                      f"营业收入={item.get('total_revenue', 'N/A')}, "
                      f"净利润={item.get('net_profit', 'N/A')}")
        
        # 分析数据结构
        analysis = analyze_income_statement_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，{len(analysis['fields'])}个字段")
        
        # 保存结果
        save_results(data_list, "single_stock_income_statement", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_multiple_stocks_income_statement():
    """测试多个股票的利润表查询"""
    print("\n=== 测试多个股票利润表查询 ===")
    
    # 测试多个知名股票
    symbols = ['SZSE.000001', 'SZSE.000002', 'SHSE.600000', 'SHSE.600036']
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbols}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_income_statement(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"返回数据类型: {type(result)}")
        print(f"返回数据长度: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = income_statement_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = income_statement_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 按股票分组统计
            symbol_stats = {}
            for item in data_list:
                symbol = item.get('symbol', 'Unknown')
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {'count': 0, 'total_revenue': [], 'net_profit': []}
                symbol_stats[symbol]['count'] += 1
                
                # 收集财务指标
                if 'total_revenue' in item and item['total_revenue'] is not None:
                    try:
                        symbol_stats[symbol]['total_revenue'].append(float(item['total_revenue']))
                    except:
                        pass
                
                if 'net_profit' in item and item['net_profit'] is not None:
                    try:
                        symbol_stats[symbol]['net_profit'].append(float(item['net_profit']))
                    except:
                        pass
            
            print("\n各股票数据统计:")
            for symbol, stats in symbol_stats.items():
                avg_revenue = sum(stats['total_revenue']) / len(stats['total_revenue']) if stats['total_revenue'] else 0
                avg_profit = sum(stats['net_profit']) / len(stats['net_profit']) if stats['net_profit'] else 0
                print(f"  {symbol}: {stats['count']}条记录, 平均营收={avg_revenue:.2f}, 平均净利润={avg_profit:.2f}")
        
        # 分析数据结构
        analysis = analyze_income_statement_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，覆盖{len(analysis['symbols'])}只股票")
        
        # 保存结果
        save_results(data_list, "multiple_stocks_income_statement", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_quarterly_vs_annual_data():
    """测试季度vs年度数据对比"""
    print("\n=== 测试季度vs年度数据对比 ===")
    
    symbol = 'SHSE.600036'  # 招商银行
    
    test_periods = [
        ('2024-01-01', '2024-03-31', '2024Q1'),
        ('2024-01-01', '2024-06-30', '2024H1'),
        ('2024-01-01', '2024-09-30', '2024Q3'),
        ('2024-01-01', '2024-12-31', '2024全年')
    ]
    
    all_results = {}
    
    for start_date, end_date, period_name in test_periods:
        try:
            print(f"\n查询{period_name}数据: {start_date} 到 {end_date}")
            
            result = gm.stk_get_fundamentals_income_statement(
                symbols=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = income_statement_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = income_statement_to_dict(result)
                if dict_item:
                    data_list.append(dict_item)
            
            print(f"  获取到{len(data_list)}条记录")
            
            # 显示关键财务指标
            if data_list:
                latest_data = data_list[-1]  # 最新的数据
                print(f"  最新数据: 营业收入={latest_data.get('total_revenue', 'N/A')}, "
                      f"净利润={latest_data.get('net_profit', 'N/A')}, "
                      f"毛利率={latest_data.get('gross_profit_margin', 'N/A')}")
            
            all_results[period_name] = data_list
            
            time.sleep(0.1)  # 避免请求过快
            
        except Exception as e:
            print(f"  查询{period_name}失败: {e}")
            all_results[period_name] = []
    
    # 保存所有结果
    save_results(all_results, "quarterly_vs_annual_income_statement")
    
    return all_results

def test_high_performance_stocks():
    """测试高业绩股票的利润表数据"""
    print("\n=== 测试高业绩股票利润表数据 ===")
    
    # 选择一些知名的高业绩股票
    high_performance_stocks = [
        'SHSE.600519',  # 贵州茅台
        'SZSE.000858',  # 五粮液
        'SHSE.600036',  # 招商银行
        'SZSE.000002',  # 万科A
        'SHSE.600000'   # 浦发银行
    ]
    
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询高业绩股票: {high_performance_stocks}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_income_statement(
            symbols=high_performance_stocks,
            start_date=start_date,
            end_date=end_date
        )
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = income_statement_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = income_statement_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"获取到{len(data_list)}条记录")
        
        if data_list:
            # 分析各股票的盈利能力
            print("\n各股票盈利能力分析:")
            symbol_performance = {}
            
            for item in data_list:
                symbol = item.get('symbol', 'Unknown')
                if symbol not in symbol_performance:
                    symbol_performance[symbol] = []
                
                # 收集关键指标
                performance_data = {
                    'end_date': item.get('end_date'),
                    'total_revenue': item.get('total_revenue'),
                    'net_profit': item.get('net_profit'),
                    'gross_profit_margin': item.get('gross_profit_margin'),
                    'net_profit_margin': item.get('net_profit_margin')
                }
                symbol_performance[symbol].append(performance_data)
            
            # 显示每只股票的最新业绩
            for symbol, performances in symbol_performance.items():
                if performances:
                    latest = max(performances, key=lambda x: x.get('end_date', '') or '')
                    print(f"  {symbol}: 营收={latest.get('total_revenue', 'N/A')}, "
                          f"净利润={latest.get('net_profit', 'N/A')}, "
                          f"净利率={latest.get('net_profit_margin', 'N/A')}%")
        
        # 分析数据结构
        analysis = analyze_income_statement_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录")
        print(f"营业收入统计: 最小={analysis['revenue_stats']['min']}, 最大={analysis['revenue_stats']['max']}, 平均={analysis['revenue_stats']['avg']}")
        print(f"净利润统计: 最小={analysis['net_profit_stats']['min']}, 最大={analysis['net_profit_stats']['max']}, 平均={analysis['net_profit_stats']['avg']}")
        
        # 保存结果
        save_results(data_list, "high_performance_stocks_income_statement", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_edge_cases():
    """测试边界情况和异常处理"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的股票代码',
            'symbols': 'SZSE.999999',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        },
        {
            'name': '未来日期',
            'symbols': 'SZSE.000001',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'symbols': 'SZSE.000001',
            'start_date': '1990-01-01',
            'end_date': '1990-12-31'
        },
        {
            'name': '单季度查询',
            'symbols': 'SZSE.000001',
            'start_date': '2024-03-31',
            'end_date': '2024-03-31'
        },
        {
            'name': '错误的股票代码格式',
            'symbols': '000001',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
    ]
    
    results = {}
    
    for case in test_cases:
        try:
            print(f"\n测试: {case['name']}")
            print(f"  参数: symbols={case['symbols']}, start_date={case['start_date']}, end_date={case['end_date']}")
            
            result = gm.stk_get_fundamentals_income_statement(
                symbols=case['symbols'],
                start_date=case['start_date'],
                end_date=case['end_date']
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = income_statement_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = income_statement_to_dict(result)
                if dict_item:
                    data_list.append(dict_item)
            
            print(f"  结果: 成功，获取{len(data_list)}条记录")
            results[case['name']] = {
                'status': 'success',
                'data_count': len(data_list),
                'data': data_list
            }
            
        except Exception as e:
            print(f"  结果: 失败 - {e}")
            results[case['name']] = {
                'status': 'error',
                'error': str(e),
                'data': []
            }
        
        time.sleep(0.1)  # 避免请求过快
    
    # 保存结果
    save_results(results, "edge_cases_income_statement")
    
    return results

def main():
    """主函数"""
    print("开始测试 gm.stk_get_fundamentals_income_statement() API")
    print("=" * 60)
    
    # 初始化API
    if not init_api():
        print("API初始化失败，退出测试")
        return
    
    try:
        # 执行各项测试
        test_single_stock_income_statement()
        test_multiple_stocks_income_statement()
        test_quarterly_vs_annual_data()
        test_high_performance_stocks()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("\n测试总结:")
        print("1. 单个股票利润表查询测试")
        print("2. 多个股票批量查询测试")
        print("3. 季度vs年度数据对比测试")
        print("4. 高业绩股票利润表数据测试")
        print("5. 边界情况和异常处理测试")
        print("\n所有结果已保存到对应的JSON和CSV文件中")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()