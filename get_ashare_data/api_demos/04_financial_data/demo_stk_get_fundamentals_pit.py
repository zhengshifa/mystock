#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo for gm.stk_get_fundamentals_pit() API
测试获取股票财务数据时点数据的API接口（Point In Time）

主要功能:
1. 测试单个股票的时点财务数据查询
2. 测试多个股票的批量查询
3. 测试不同时间点的查询
4. 测试不同财务报表类型的查询
5. 测试时点数据的历史回溯
6. 测试边界情况和异常处理
7. 数据结构分析和保存

注意: PIT数据反映的是在特定时点投资者能够获得的财务数据，
考虑了数据发布的时间延迟，更接近实际投资决策时的信息状态。
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

def pit_data_to_dict(pit_obj):
    """将PIT财务数据对象转换为字典"""
    if pit_obj is None:
        return None
    
    # 获取对象的所有属性
    result = {}
    for attr in dir(pit_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(pit_obj, attr)
                if not callable(value):
                    result[attr] = value
            except:
                continue
    
    return result

def analyze_pit_structure(data_list):
    """分析PIT财务数据结构"""
    if not data_list:
        return {"error": "数据为空"}
    
    analysis = {
        "total_records": len(data_list),
        "fields": set(),
        "sample_data": data_list[0] if data_list else None,
        "symbols": set(),
        "pit_dates": set(),
        "report_dates": set(),
        "report_types": set(),
        "data_sources": set(),
        "key_metrics": {
            "revenue_stats": {"min": None, "max": None, "avg": None},
            "net_income_stats": {"min": None, "max": None, "avg": None},
            "total_assets_stats": {"min": None, "max": None, "avg": None},
            "total_equity_stats": {"min": None, "max": None, "avg": None}
        }
    }
    
    # 收集各种指标数据
    metrics_data = {
        'revenue': [],
        'net_income': [],
        'total_assets': [],
        'total_equity': []
    }
    
    for item in data_list:
        if isinstance(item, dict):
            analysis["fields"].update(item.keys())
            if 'symbol' in item:
                analysis["symbols"].add(item['symbol'])
            if 'pit_date' in item:
                analysis["pit_dates"].add(str(item['pit_date']))
            if 'end_date' in item:
                analysis["report_dates"].add(str(item['end_date']))
            if 'report_type' in item:
                analysis["report_types"].add(str(item['report_type']))
            if 'data_source' in item:
                analysis["data_sources"].add(str(item['data_source']))
            
            # 收集关键财务指标
            metric_mappings = {
                'revenue': ['revenue', 'total_revenue', 'operating_revenue'],
                'net_income': ['net_income', 'net_profit', 'profit_after_tax'],
                'total_assets': ['total_assets', 'total_asset'],
                'total_equity': ['total_equity', 'total_shareholders_equity', 'shareholders_equity']
            }
            
            for key, possible_fields in metric_mappings.items():
                for field in possible_fields:
                    if field in item and item[field] is not None:
                        try:
                            value = float(item[field])
                            if not (value == float('inf') or value == float('-inf') or value != value):  # 排除无穷大和NaN
                                metrics_data[key].append(value)
                            break
                        except:
                            continue
    
    # 计算统计信息
    for key, values in metrics_data.items():
        if values:
            analysis["key_metrics"][f"{key}_stats"] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
            }
    
    # 转换set为list以便JSON序列化
    analysis["fields"] = sorted(list(analysis["fields"]))
    analysis["symbols"] = sorted(list(analysis["symbols"]))
    analysis["pit_dates"] = sorted(list(analysis["pit_dates"]))
    analysis["report_dates"] = sorted(list(analysis["report_dates"]))
    analysis["report_types"] = sorted(list(analysis["report_types"]))
    analysis["data_sources"] = sorted(list(analysis["data_sources"]))
    
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

def test_single_stock_pit():
    """测试单个股票的PIT财务数据查询"""
    print("\n=== 测试单个股票PIT财务数据查询 ===")
    
    # 测试平安银行的PIT数据
    symbol = 'SZSE.000001'
    pit_date = '2024-06-30'  # 查询时点
    count = 8  # 获取最近8个报告期的数据
    
    try:
        print(f"查询股票: {symbol}")
        print(f"查询时点: {pit_date}")
        print(f"获取数量: {count}个报告期")
        
        # 调用API
        result = gm.stk_get_fundamentals_pit(
            symbols=symbol,
            pit_date=pit_date,
            count=count
        )
        
        print(f"返回数据类型: {type(result)}")
        print(f"返回数据长度: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = pit_data_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = pit_data_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 显示前几条数据的关键字段
            print("\n前5条数据的关键指标:")
            for i, item in enumerate(data_list[:5]):
                revenue = item.get('revenue') or item.get('total_revenue') or item.get('operating_revenue', 'N/A')
                net_income = item.get('net_income') or item.get('net_profit', 'N/A')
                total_assets = item.get('total_assets') or item.get('total_asset', 'N/A')
                
                print(f"  记录{i+1}: 股票={item.get('symbol', 'N/A')}, "
                      f"报告期={item.get('end_date', 'N/A')}, "
                      f"PIT日期={item.get('pit_date', 'N/A')}, "
                      f"营收={revenue}, 净利润={net_income}")
                print(f"          总资产={total_assets}, "
                      f"报告类型={item.get('report_type', 'N/A')}")
        
        # 分析数据结构
        analysis = analyze_pit_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，{len(analysis['fields'])}个字段")
        print(f"报告类型: {analysis['report_types']}")
        print(f"数据来源: {analysis['data_sources']}")
        
        # 保存结果
        save_results(data_list, "single_stock_pit", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_multiple_stocks_pit():
    """测试多个股票的PIT财务数据查询"""
    print("\n=== 测试多个股票PIT财务数据查询 ===")
    
    # 测试多个不同行业的股票
    symbols = [
        'SHSE.600519',  # 贵州茅台
        'SZSE.000858',  # 五粮液
        'SHSE.600036',  # 招商银行
        'SZSE.000002'   # 万科A
    ]
    pit_date = '2024-09-30'  # 查询时点
    count = 4  # 获取最近4个报告期的数据
    
    try:
        print(f"查询股票: {symbols}")
        print(f"查询时点: {pit_date}")
        print(f"获取数量: {count}个报告期")
        
        # 调用API
        result = gm.stk_get_fundamentals_pit(
            symbols=symbols,
            pit_date=pit_date,
            count=count
        )
        
        print(f"返回数据类型: {type(result)}")
        print(f"返回数据长度: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = pit_data_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = pit_data_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 按股票分组统计
            symbol_data = {}
            for item in data_list:
                symbol = item.get('symbol', 'Unknown')
                if symbol not in symbol_data:
                    symbol_data[symbol] = {
                        'count': 0,
                        'latest_revenue': None,
                        'latest_net_income': None,
                        'latest_report_date': None,
                        'report_types': set()
                    }
                
                symbol_data[symbol]['count'] += 1
                
                # 记录报告类型
                if 'report_type' in item:
                    symbol_data[symbol]['report_types'].add(str(item['report_type']))
                
                # 找到最新的数据（按报告期）
                report_date = item.get('end_date')
                if report_date and (symbol_data[symbol]['latest_report_date'] is None or 
                                  report_date > symbol_data[symbol]['latest_report_date']):
                    symbol_data[symbol]['latest_report_date'] = report_date
                    symbol_data[symbol]['latest_revenue'] = (item.get('revenue') or 
                                                           item.get('total_revenue') or 
                                                           item.get('operating_revenue'))
                    symbol_data[symbol]['latest_net_income'] = (item.get('net_income') or 
                                                              item.get('net_profit'))
            
            print("\n各股票PIT数据统计:")
            for symbol, data in symbol_data.items():
                data['report_types'] = list(data['report_types'])
                print(f"  {symbol}: {data['count']}条记录")
                print(f"    最新报告期: {data['latest_report_date']}")
                print(f"    最新营收: {data['latest_revenue']}")
                print(f"    最新净利润: {data['latest_net_income']}")
                print(f"    报告类型: {data['report_types']}")
        
        # 分析数据结构
        analysis = analyze_pit_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，覆盖{len(analysis['symbols'])}只股票")
        
        # 保存结果
        save_results(data_list, "multiple_stocks_pit", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_time_series_pit():
    """测试不同时点的PIT数据查询"""
    print("\n=== 测试不同时点PIT数据查询 ===")
    
    # 测试同一股票在不同时点的PIT数据
    symbol = 'SHSE.600519'  # 贵州茅台
    pit_dates = [
        '2023-12-31',  # 年末
        '2024-03-31',  # 一季度末
        '2024-06-30',  # 半年末
        '2024-09-30'   # 三季度末
    ]
    count = 4  # 每个时点获取4个报告期
    
    time_series_results = {}
    
    for pit_date in pit_dates:
        try:
            print(f"\n查询时点: {pit_date}")
            
            # 调用API
            result = gm.stk_get_fundamentals_pit(
                symbols=symbol,
                pit_date=pit_date,
                count=count
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = pit_data_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = pit_data_to_dict(result)
                if dict_item:
                    data_list.append(dict_item)
            
            print(f"  获取到{len(data_list)}条记录")
            
            # 分析该时点的数据
            if data_list:
                # 按报告期排序
                data_list.sort(key=lambda x: x.get('end_date', ''), reverse=True)
                
                print(f"  可获得的报告期:")
                for i, item in enumerate(data_list[:3]):  # 显示前3个
                    revenue = item.get('revenue') or item.get('total_revenue') or item.get('operating_revenue')
                    net_income = item.get('net_income') or item.get('net_profit')
                    print(f"    {i+1}. {item.get('end_date')}: 营收={revenue}, 净利润={net_income}")
                
                time_series_results[pit_date] = {
                    'data_count': len(data_list),
                    'data': data_list,
                    'latest_report_date': data_list[0].get('end_date') if data_list else None
                }
            else:
                time_series_results[pit_date] = {
                    'data_count': 0,
                    'data': [],
                    'latest_report_date': None
                }
            
            time.sleep(0.2)  # 避免请求过快
            
        except Exception as e:
            print(f"  查询失败: {e}")
            time_series_results[pit_date] = {'error': str(e)}
    
    # 时点对比分析
    print("\n=== 时点对比分析 ===")
    for pit_date, result in time_series_results.items():
        if 'data_count' in result:
            print(f"{pit_date}: 可获得{result['data_count']}个报告期数据，最新报告期={result['latest_report_date']}")
        else:
            print(f"{pit_date}: 查询失败")
    
    # 保存结果
    save_results(time_series_results, "time_series_pit")
    
    return time_series_results

def test_report_type_analysis():
    """测试不同报告类型的分析"""
    print("\n=== 测试报告类型分析 ===")
    
    # 选择一个有完整财务数据的股票
    symbol = 'SHSE.600036'  # 招商银行
    pit_date = '2024-10-31'  # 查询时点
    count = 12  # 获取更多报告期以包含不同类型
    
    try:
        print(f"查询股票: {symbol}")
        print(f"查询时点: {pit_date}")
        print(f"获取数量: {count}个报告期")
        
        # 调用API
        result = gm.stk_get_fundamentals_pit(
            symbols=symbol,
            pit_date=pit_date,
            count=count
        )
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = pit_data_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = pit_data_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"获取到{len(data_list)}条记录")
        
        if data_list:
            # 按报告类型分组
            report_type_data = {}
            for item in data_list:
                report_type = item.get('report_type', 'Unknown')
                if report_type not in report_type_data:
                    report_type_data[report_type] = []
                report_type_data[report_type].append(item)
            
            print("\n按报告类型分析:")
            for report_type, items in report_type_data.items():
                print(f"\n  {report_type} ({len(items)}条记录):")
                
                # 按报告期排序
                items.sort(key=lambda x: x.get('end_date', ''), reverse=True)
                
                for i, item in enumerate(items[:3]):  # 显示前3条
                    revenue = item.get('revenue') or item.get('total_revenue') or item.get('operating_revenue')
                    net_income = item.get('net_income') or item.get('net_profit')
                    print(f"    {i+1}. 报告期={item.get('end_date')}, PIT日期={item.get('pit_date')}")
                    print(f"       营收={revenue}, 净利润={net_income}")
            
            # 分析年报vs季报的数据完整性
            print("\n报告类型数据完整性分析:")
            for report_type, items in report_type_data.items():
                if items:
                    sample_item = items[0]
                    field_count = len([k for k, v in sample_item.items() if v is not None])
                    print(f"  {report_type}: 平均字段数={field_count}")
        
        # 保存结果
        save_results(data_list, "report_type_analysis")
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_pit_vs_regular_comparison():
    """测试PIT数据与常规财务数据的对比"""
    print("\n=== 测试PIT数据与常规财务数据对比 ===")
    
    symbol = 'SZSE.000002'  # 万科A
    pit_date = '2024-05-01'  # 查询时点（年报发布后）
    count = 4
    
    try:
        print(f"查询股票: {symbol}")
        print(f"PIT查询时点: {pit_date}")
        
        # 获取PIT数据
        pit_result = gm.stk_get_fundamentals_pit(
            symbols=symbol,
            pit_date=pit_date,
            count=count
        )
        
        # 转换PIT数据
        pit_data_list = []
        if isinstance(pit_result, list):
            for item in pit_result:
                dict_item = pit_data_to_dict(item)
                if dict_item:
                    pit_data_list.append(dict_item)
        else:
            dict_item = pit_data_to_dict(pit_result)
            if dict_item:
                pit_data_list.append(dict_item)
        
        print(f"PIT数据: 获取到{len(pit_data_list)}条记录")
        
        # 获取常规财务数据进行对比（如果API可用）
        try:
            # 这里假设有常规的财务数据API可以对比
            # regular_result = gm.stk_get_fundamentals_balance_sheet(
            #     symbols=symbol,
            #     start_date='2023-01-01',
            #     end_date='2024-12-31'
            # )
            print("注意: 常规财务数据对比需要其他API支持")
        except:
            pass
        
        if pit_data_list:
            print("\nPIT数据特点分析:")
            
            # 按报告期排序
            pit_data_list.sort(key=lambda x: x.get('end_date', ''), reverse=True)
            
            for i, item in enumerate(pit_data_list[:3]):
                print(f"\n  记录{i+1}:")
                print(f"    报告期: {item.get('end_date')}")
                print(f"    PIT日期: {item.get('pit_date')}")
                print(f"    发布日期: {item.get('pub_date', 'N/A')}")
                print(f"    数据来源: {item.get('data_source', 'N/A')}")
                
                # 计算PIT日期与报告期的时间差
                try:
                    if item.get('pit_date') and item.get('end_date'):
                        pit_dt = datetime.strptime(str(item['pit_date'])[:10], '%Y-%m-%d')
                        end_dt = datetime.strptime(str(item['end_date'])[:10], '%Y-%m-%d')
                        time_diff = (pit_dt - end_dt).days
                        print(f"    时间差: {time_diff}天（PIT日期晚于报告期）")
                except:
                    print(f"    时间差: 无法计算")
        
        # 保存结果
        comparison_result = {
            'pit_data': pit_data_list,
            'pit_date': pit_date,
            'symbol': symbol,
            'analysis': 'PIT数据反映了在特定时点投资者能够获得的财务信息'
        }
        
        save_results(comparison_result, "pit_vs_regular_comparison")
        
        return comparison_result
        
    except Exception as e:
        print(f"查询失败: {e}")
        return {}

def test_edge_cases():
    """测试边界情况和异常处理"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的股票代码',
            'symbols': 'SZSE.999999',
            'pit_date': '2024-06-30',
            'count': 4
        },
        {
            'name': '未来的PIT日期',
            'symbols': 'SZSE.000001',
            'pit_date': '2025-12-31',
            'count': 4
        },
        {
            'name': '很久以前的PIT日期',
            'symbols': 'SZSE.000001',
            'pit_date': '2000-01-01',
            'count': 4
        },
        {
            'name': '获取大量历史数据',
            'symbols': 'SHSE.600519',
            'pit_date': '2024-06-30',
            'count': 20
        },
        {
            'name': '获取单个报告期',
            'symbols': 'SHSE.600036',
            'pit_date': '2024-06-30',
            'count': 1
        },
        {
            'name': '多股票大量数据',
            'symbols': ['SZSE.000001', 'SZSE.000002', 'SHSE.600519'],
            'pit_date': '2024-06-30',
            'count': 8
        }
    ]
    
    results = {}
    
    for case in test_cases:
        try:
            print(f"\n测试: {case['name']}")
            print(f"  参数: symbols={case['symbols']}, pit_date={case['pit_date']}, count={case['count']}")
            
            result = gm.stk_get_fundamentals_pit(
                symbols=case['symbols'],
                pit_date=case['pit_date'],
                count=case['count']
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = pit_data_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = pit_data_to_dict(result)
                if dict_item:
                    data_list.append(dict_item)
            
            print(f"  结果: 成功，获取{len(data_list)}条记录")
            
            # 简单统计
            if data_list:
                symbols_found = set(item.get('symbol') for item in data_list)
                report_dates = set(item.get('end_date') for item in data_list)
                print(f"  涉及股票: {len(symbols_found)}只")
                print(f"  报告期数: {len(report_dates)}个")
            
            results[case['name']] = {
                'status': 'success',
                'data_count': len(data_list),
                'symbols_count': len(set(item.get('symbol') for item in data_list)) if data_list else 0,
                'data': data_list[:5]  # 只保存前5条以节省空间
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
    save_results(results, "edge_cases_pit")
    
    return results

def main():
    """主函数"""
    print("开始测试 gm.stk_get_fundamentals_pit() API")
    print("=" * 60)
    
    # 初始化API
    if not init_api():
        print("API初始化失败，退出测试")
        return
    
    try:
        # 执行各项测试
        test_single_stock_pit()
        test_multiple_stocks_pit()
        test_time_series_pit()
        test_report_type_analysis()
        test_pit_vs_regular_comparison()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("\n测试总结:")
        print("1. 单个股票PIT财务数据查询测试")
        print("2. 多个股票批量PIT数据查询测试")
        print("3. 不同时点PIT数据查询测试")
        print("4. 报告类型分析测试")
        print("5. PIT数据与常规数据对比测试")
        print("6. 边界情况和异常处理测试")
        print("\n所有结果已保存到对应的JSON和CSV文件中")
        print("\nPIT数据说明:")
        print("- PIT (Point In Time) 数据反映特定时点投资者能获得的财务信息")
        print("- 考虑了财务报告的发布时间延迟")
        print("- 更接近实际投资决策时的信息状态")
        print("- 适用于回测和历史分析")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()