#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo for gm.stk_get_fundamentals_indicator() API
测试获取股票财务指标数据的API接口

主要功能:
1. 测试单个股票的财务指标查询
2. 测试多个股票的批量查询
3. 测试不同时间段的查询
4. 测试财务指标分析和对比
5. 测试行业对比分析
6. 测试边界情况和异常处理
7. 数据结构分析和保存
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

def indicator_to_dict(indicator_obj):
    """将财务指标对象转换为字典"""
    if indicator_obj is None:
        return None
    
    # 获取对象的所有属性
    result = {}
    for attr in dir(indicator_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(indicator_obj, attr)
                if not callable(value):
                    result[attr] = value
            except:
                continue
    
    return result

def analyze_indicator_structure(data_list):
    """分析财务指标数据结构"""
    if not data_list:
        return {"error": "数据为空"}
    
    analysis = {
        "total_records": len(data_list),
        "fields": set(),
        "sample_data": data_list[0] if data_list else None,
        "symbols": set(),
        "pub_dates": set(),
        "report_dates": set(),
        "key_indicators": {
            "roe_stats": {"min": None, "max": None, "avg": None},
            "roa_stats": {"min": None, "max": None, "avg": None},
            "pe_ratio_stats": {"min": None, "max": None, "avg": None},
            "pb_ratio_stats": {"min": None, "max": None, "avg": None},
            "debt_ratio_stats": {"min": None, "max": None, "avg": None}
        }
    }
    
    # 收集各种指标数据
    indicators_data = {
        'roe': [],
        'roa': [],
        'pe_ratio': [],
        'pb_ratio': [],
        'debt_ratio': []
    }
    
    for item in data_list:
        if isinstance(item, dict):
            analysis["fields"].update(item.keys())
            if 'symbol' in item:
                analysis["symbols"].add(item['symbol'])
            if 'pub_date' in item:
                analysis["pub_dates"].add(str(item['pub_date']))
            if 'end_date' in item:
                analysis["report_dates"].add(str(item['end_date']))
            
            # 收集关键财务指标
            indicator_mappings = {
                'roe': ['roe', 'return_on_equity'],
                'roa': ['roa', 'return_on_assets'],
                'pe_ratio': ['pe_ratio', 'pe_ttm'],
                'pb_ratio': ['pb_ratio', 'pb'],
                'debt_ratio': ['debt_ratio', 'debt_to_assets']
            }
            
            for key, possible_fields in indicator_mappings.items():
                for field in possible_fields:
                    if field in item and item[field] is not None:
                        try:
                            value = float(item[field])
                            if not (value == float('inf') or value == float('-inf') or value != value):  # 排除无穷大和NaN
                                indicators_data[key].append(value)
                            break
                        except:
                            continue
    
    # 计算统计信息
    for key, values in indicators_data.items():
        if values:
            analysis["key_indicators"][f"{key}_stats"] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
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

def test_single_stock_indicator():
    """测试单个股票的财务指标查询"""
    print("\n=== 测试单个股票财务指标查询 ===")
    
    # 测试平安银行的财务指标
    symbol = 'SZSE.000001'
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbol}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_indicator(
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
                dict_item = indicator_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = indicator_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 显示前几条数据的关键字段
            print("\n前3条数据的关键指标:")
            for i, item in enumerate(data_list[:3]):
                roe = item.get('roe') or item.get('return_on_equity', 'N/A')
                roa = item.get('roa') or item.get('return_on_assets', 'N/A')
                pe = item.get('pe_ratio') or item.get('pe_ttm', 'N/A')
                pb = item.get('pb_ratio') or item.get('pb', 'N/A')
                
                print(f"  记录{i+1}: 股票={item.get('symbol', 'N/A')}, "
                      f"报告期={item.get('end_date', 'N/A')}, "
                      f"ROE={roe}, ROA={roa}, PE={pe}, PB={pb}")
        
        # 分析数据结构
        analysis = analyze_indicator_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，{len(analysis['fields'])}个字段")
        
        # 保存结果
        save_results(data_list, "single_stock_indicator", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_multiple_stocks_indicator():
    """测试多个股票的财务指标查询"""
    print("\n=== 测试多个股票财务指标查询 ===")
    
    # 测试多个不同行业的优质股票
    symbols = [
        'SHSE.600519',  # 贵州茅台 - 白酒
        'SZSE.000858',  # 五粮液 - 白酒
        'SHSE.600036',  # 招商银行 - 银行
        'SZSE.000001',  # 平安银行 - 银行
        'SZSE.000002'   # 万科A - 房地产
    ]
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbols}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_indicator(
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
                dict_item = indicator_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = indicator_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 按股票分组统计财务指标
            symbol_indicators = {}
            for item in data_list:
                symbol = item.get('symbol', 'Unknown')
                if symbol not in symbol_indicators:
                    symbol_indicators[symbol] = {
                        'count': 0,
                        'roe_values': [],
                        'roa_values': [],
                        'pe_values': [],
                        'pb_values': []
                    }
                
                symbol_indicators[symbol]['count'] += 1
                
                # 收集关键指标
                roe = item.get('roe') or item.get('return_on_equity')
                roa = item.get('roa') or item.get('return_on_assets')
                pe = item.get('pe_ratio') or item.get('pe_ttm')
                pb = item.get('pb_ratio') or item.get('pb')
                
                for value, key in [(roe, 'roe_values'), (roa, 'roa_values'), (pe, 'pe_values'), (pb, 'pb_values')]:
                    if value is not None:
                        try:
                            float_val = float(value)
                            if not (float_val == float('inf') or float_val == float('-inf') or float_val != float_val):
                                symbol_indicators[symbol][key].append(float_val)
                        except:
                            pass
            
            print("\n各股票财务指标统计:")
            for symbol, indicators in symbol_indicators.items():
                avg_roe = sum(indicators['roe_values']) / len(indicators['roe_values']) if indicators['roe_values'] else 0
                avg_roa = sum(indicators['roa_values']) / len(indicators['roa_values']) if indicators['roa_values'] else 0
                avg_pe = sum(indicators['pe_values']) / len(indicators['pe_values']) if indicators['pe_values'] else 0
                avg_pb = sum(indicators['pb_values']) / len(indicators['pb_values']) if indicators['pb_values'] else 0
                
                print(f"  {symbol}: {indicators['count']}条记录")
                print(f"    平均ROE={avg_roe:.2f}%, 平均ROA={avg_roa:.2f}%, 平均PE={avg_pe:.2f}, 平均PB={avg_pb:.2f}")
        
        # 分析数据结构
        analysis = analyze_indicator_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，覆盖{len(analysis['symbols'])}只股票")
        
        # 保存结果
        save_results(data_list, "multiple_stocks_indicator", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_industry_comparison():
    """测试行业对比分析"""
    print("\n=== 测试行业对比分析 ===")
    
    # 按行业分组的股票
    industry_stocks = {
        '银行业': ['SHSE.600036', 'SZSE.000001', 'SHSE.600000'],
        '白酒业': ['SHSE.600519', 'SZSE.000858', 'SHSE.600809'],
        '房地产': ['SZSE.000002', 'SHSE.600048', 'SZSE.000069']
    }
    
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    industry_results = {}
    
    for industry, stocks in industry_stocks.items():
        try:
            print(f"\n查询{industry}股票: {stocks}")
            
            # 调用API
            result = gm.stk_get_fundamentals_indicator(
                symbols=stocks,
                start_date=start_date,
                end_date=end_date
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = indicator_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = indicator_to_dict(result)
                if dict_item:
                    data_list.append(dict_item)
            
            print(f"  获取到{len(data_list)}条记录")
            
            # 计算行业平均指标
            if data_list:
                industry_indicators = {
                    'roe_values': [],
                    'roa_values': [],
                    'pe_values': [],
                    'pb_values': [],
                    'debt_ratio_values': []
                }
                
                for item in data_list:
                    # 收集各项指标
                    indicators = {
                        'roe_values': item.get('roe') or item.get('return_on_equity'),
                        'roa_values': item.get('roa') or item.get('return_on_assets'),
                        'pe_values': item.get('pe_ratio') or item.get('pe_ttm'),
                        'pb_values': item.get('pb_ratio') or item.get('pb'),
                        'debt_ratio_values': item.get('debt_ratio') or item.get('debt_to_assets')
                    }
                    
                    for key, value in indicators.items():
                        if value is not None:
                            try:
                                float_val = float(value)
                                if not (float_val == float('inf') or float_val == float('-inf') or float_val != float_val):
                                    industry_indicators[key].append(float_val)
                            except:
                                pass
                
                # 计算行业平均值
                industry_avg = {}
                for key, values in industry_indicators.items():
                    if values:
                        industry_avg[key.replace('_values', '_avg')] = sum(values) / len(values)
                        industry_avg[key.replace('_values', '_count')] = len(values)
                    else:
                        industry_avg[key.replace('_values', '_avg')] = 0
                        industry_avg[key.replace('_values', '_count')] = 0
                
                print(f"  {industry}平均指标:")
                print(f"    ROE: {industry_avg.get('roe_avg', 0):.2f}% ({industry_avg.get('roe_count', 0)}个数据点)")
                print(f"    ROA: {industry_avg.get('roa_avg', 0):.2f}% ({industry_avg.get('roa_count', 0)}个数据点)")
                print(f"    PE: {industry_avg.get('pe_avg', 0):.2f} ({industry_avg.get('pe_count', 0)}个数据点)")
                print(f"    PB: {industry_avg.get('pb_avg', 0):.2f} ({industry_avg.get('pb_count', 0)}个数据点)")
                
                industry_results[industry] = {
                    'data': data_list,
                    'averages': industry_avg,
                    'stock_count': len(stocks),
                    'record_count': len(data_list)
                }
            
            time.sleep(0.2)  # 避免请求过快
            
        except Exception as e:
            print(f"  查询{industry}失败: {e}")
            industry_results[industry] = {'error': str(e)}
    
    # 行业对比总结
    print("\n=== 行业对比总结 ===")
    for industry, result in industry_results.items():
        if 'averages' in result:
            avg = result['averages']
            print(f"{industry}: ROE={avg.get('roe_avg', 0):.2f}%, ROA={avg.get('roa_avg', 0):.2f}%, PE={avg.get('pe_avg', 0):.2f}, PB={avg.get('pb_avg', 0):.2f}")
    
    # 保存结果
    save_results(industry_results, "industry_comparison_indicator")
    
    return industry_results

def test_financial_health_analysis():
    """测试财务健康度分析"""
    print("\n=== 测试财务健康度分析 ===")
    
    # 选择一些代表性股票进行财务健康度分析
    symbols = [
        'SHSE.600519',  # 贵州茅台 - 通常财务很健康
        'SZSE.000002',  # 万科A - 房地产，负债较高
        'SHSE.600036'   # 招商银行 - 银行业特殊性
    ]
    
    start_date = '2022-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbols}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_indicator(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = indicator_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = indicator_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"获取到{len(data_list)}条记录")
        
        if data_list:
            # 按股票分析财务健康度
            print("\n财务健康度分析:")
            
            symbol_health = {}
            for item in data_list:
                symbol = item.get('symbol', 'Unknown')
                if symbol not in symbol_health:
                    symbol_health[symbol] = []
                
                # 收集健康度相关指标
                health_indicators = {
                    'end_date': item.get('end_date'),
                    'roe': item.get('roe') or item.get('return_on_equity'),
                    'roa': item.get('roa') or item.get('return_on_assets'),
                    'debt_ratio': item.get('debt_ratio') or item.get('debt_to_assets'),
                    'current_ratio': item.get('current_ratio'),
                    'quick_ratio': item.get('quick_ratio'),
                    'gross_profit_margin': item.get('gross_profit_margin'),
                    'net_profit_margin': item.get('net_profit_margin')
                }
                
                symbol_health[symbol].append(health_indicators)
            
            # 分析每个股票的财务健康度
            for symbol, records in symbol_health.items():
                print(f"\n  {symbol}:")
                
                # 按日期排序
                records.sort(key=lambda x: x['end_date'] or '')
                
                # 计算平均指标
                indicators_sum = {}
                indicators_count = {}
                
                for record in records:
                    for key, value in record.items():
                        if key != 'end_date' and value is not None:
                            try:
                                float_val = float(value)
                                if not (float_val == float('inf') or float_val == float('-inf') or float_val != float_val):
                                    if key not in indicators_sum:
                                        indicators_sum[key] = 0
                                        indicators_count[key] = 0
                                    indicators_sum[key] += float_val
                                    indicators_count[key] += 1
                            except:
                                pass
                
                # 计算平均值并评估健康度
                health_score = 0
                max_score = 0
                
                for key, total in indicators_sum.items():
                    if indicators_count[key] > 0:
                        avg_value = total / indicators_count[key]
                        print(f"    平均{key}: {avg_value:.2f}")
                        
                        # 简单的健康度评分（这里只是示例）
                        if key == 'roe' and avg_value > 10:
                            health_score += 1
                        elif key == 'roa' and avg_value > 5:
                            health_score += 1
                        elif key == 'debt_ratio' and avg_value < 60:
                            health_score += 1
                        elif key == 'current_ratio' and avg_value > 1:
                            health_score += 1
                        elif key == 'net_profit_margin' and avg_value > 10:
                            health_score += 1
                        
                        max_score += 1
                
                if max_score > 0:
                    health_percentage = (health_score / max_score) * 100
                    print(f"    财务健康度评分: {health_score}/{max_score} ({health_percentage:.1f}%)")
                
                # 显示最近趋势
                if len(records) >= 2:
                    latest = records[-1]
                    previous = records[-2]
                    print(f"    最新数据 ({latest['end_date']}): ROE={latest['roe']}, 负债率={latest['debt_ratio']}")
                    print(f"    上期数据 ({previous['end_date']}): ROE={previous['roe']}, 负债率={previous['debt_ratio']}")
        
        # 保存结果
        save_results(data_list, "financial_health_analysis")
        
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
            'name': '单日查询',
            'symbols': 'SZSE.000001',
            'start_date': '2024-03-31',
            'end_date': '2024-03-31'
        },
        {
            'name': '大量股票查询',
            'symbols': ['SZSE.000001', 'SZSE.000002', 'SHSE.600000', 'SHSE.600036', 'SHSE.600519', 'SZSE.000858'],
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
    ]
    
    results = {}
    
    for case in test_cases:
        try:
            print(f"\n测试: {case['name']}")
            print(f"  参数: symbols={case['symbols']}, start_date={case['start_date']}, end_date={case['end_date']}")
            
            result = gm.stk_get_fundamentals_indicator(
                symbols=case['symbols'],
                start_date=case['start_date'],
                end_date=case['end_date']
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = indicator_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = indicator_to_dict(result)
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
    save_results(results, "edge_cases_indicator")
    
    return results

def main():
    """主函数"""
    print("开始测试 gm.stk_get_fundamentals_indicator() API")
    print("=" * 60)
    
    # 初始化API
    if not init_api():
        print("API初始化失败，退出测试")
        return
    
    try:
        # 执行各项测试
        test_single_stock_indicator()
        test_multiple_stocks_indicator()
        test_industry_comparison()
        test_financial_health_analysis()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("\n测试总结:")
        print("1. 单个股票财务指标查询测试")
        print("2. 多个股票批量查询测试")
        print("3. 行业对比分析测试")
        print("4. 财务健康度分析测试")
        print("5. 边界情况和异常处理测试")
        print("\n所有结果已保存到对应的JSON和CSV文件中")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()