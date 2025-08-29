#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo for gm.stk_get_fundamentals_cash_flow() API
测试获取股票现金流量表数据的API接口

主要功能:
1. 测试单个股票的现金流量表查询
2. 测试多个股票的批量查询
3. 测试不同时间段的查询
4. 测试现金流分析和对比
5. 测试边界情况和异常处理
6. 数据结构分析和保存
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

def cash_flow_to_dict(cash_flow_obj):
    """将现金流量表对象转换为字典"""
    if cash_flow_obj is None:
        return None
    
    # 获取对象的所有属性
    result = {}
    for attr in dir(cash_flow_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(cash_flow_obj, attr)
                if not callable(value):
                    result[attr] = value
            except:
                continue
    
    return result

def analyze_cash_flow_structure(data_list):
    """分析现金流量表数据结构"""
    if not data_list:
        return {"error": "数据为空"}
    
    analysis = {
        "total_records": len(data_list),
        "fields": set(),
        "sample_data": data_list[0] if data_list else None,
        "symbols": set(),
        "pub_dates": set(),
        "report_dates": set(),
        "operating_cash_flow_stats": {"min": None, "max": None, "avg": None},
        "investing_cash_flow_stats": {"min": None, "max": None, "avg": None},
        "financing_cash_flow_stats": {"min": None, "max": None, "avg": None},
        "free_cash_flow_stats": {"min": None, "max": None, "avg": None}
    }
    
    operating_flows = []
    investing_flows = []
    financing_flows = []
    free_flows = []
    
    for item in data_list:
        if isinstance(item, dict):
            analysis["fields"].update(item.keys())
            if 'symbol' in item:
                analysis["symbols"].add(item['symbol'])
            if 'pub_date' in item:
                analysis["pub_dates"].add(str(item['pub_date']))
            if 'end_date' in item:
                analysis["report_dates"].add(str(item['end_date']))
            
            # 收集现金流数据
            if 'net_operate_cash_flow' in item and item['net_operate_cash_flow'] is not None:
                try:
                    operating_flows.append(float(item['net_operate_cash_flow']))
                except:
                    pass
            
            if 'net_invest_cash_flow' in item and item['net_invest_cash_flow'] is not None:
                try:
                    investing_flows.append(float(item['net_invest_cash_flow']))
                except:
                    pass
            
            if 'net_finance_cash_flow' in item and item['net_finance_cash_flow'] is not None:
                try:
                    financing_flows.append(float(item['net_finance_cash_flow']))
                except:
                    pass
            
            if 'free_cash_flow' in item and item['free_cash_flow'] is not None:
                try:
                    free_flows.append(float(item['free_cash_flow']))
                except:
                    pass
    
    # 计算统计信息
    if operating_flows:
        analysis["operating_cash_flow_stats"] = {
            "min": min(operating_flows),
            "max": max(operating_flows),
            "avg": sum(operating_flows) / len(operating_flows)
        }
    
    if investing_flows:
        analysis["investing_cash_flow_stats"] = {
            "min": min(investing_flows),
            "max": max(investing_flows),
            "avg": sum(investing_flows) / len(investing_flows)
        }
    
    if financing_flows:
        analysis["financing_cash_flow_stats"] = {
            "min": min(financing_flows),
            "max": max(financing_flows),
            "avg": sum(financing_flows) / len(financing_flows)
        }
    
    if free_flows:
        analysis["free_cash_flow_stats"] = {
            "min": min(free_flows),
            "max": max(free_flows),
            "avg": sum(free_flows) / len(free_flows)
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

def test_single_stock_cash_flow():
    """测试单个股票的现金流量表查询"""
    print("\n=== 测试单个股票现金流量表查询 ===")
    
    # 测试平安银行的现金流量表
    symbol = 'SZSE.000001'
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbol}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_cash_flow(
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
                dict_item = cash_flow_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = cash_flow_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 显示前几条数据的关键字段
            print("\n前3条数据的关键信息:")
            for i, item in enumerate(data_list[:3]):
                print(f"  记录{i+1}: 股票={item.get('symbol', 'N/A')}, "
                      f"报告期={item.get('end_date', 'N/A')}, "
                      f"经营现金流={item.get('net_operate_cash_flow', 'N/A')}, "
                      f"自由现金流={item.get('free_cash_flow', 'N/A')}")
        
        # 分析数据结构
        analysis = analyze_cash_flow_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，{len(analysis['fields'])}个字段")
        
        # 保存结果
        save_results(data_list, "single_stock_cash_flow", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_multiple_stocks_cash_flow():
    """测试多个股票的现金流量表查询"""
    print("\n=== 测试多个股票现金流量表查询 ===")
    
    # 测试多个不同行业的股票
    symbols = [
        'SZSE.000001',  # 平安银行 - 银行业
        'SHSE.600519',  # 贵州茅台 - 白酒业
        'SZSE.000858',  # 五粮液 - 白酒业
        'SHSE.600036',  # 招商银行 - 银行业
        'SZSE.000002'   # 万科A - 房地产业
    ]
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbols}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_cash_flow(
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
                dict_item = cash_flow_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = cash_flow_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 按股票分组统计现金流情况
            symbol_cash_flow = {}
            for item in data_list:
                symbol = item.get('symbol', 'Unknown')
                if symbol not in symbol_cash_flow:
                    symbol_cash_flow[symbol] = {
                        'count': 0,
                        'operating_flows': [],
                        'investing_flows': [],
                        'financing_flows': [],
                        'free_flows': []
                    }
                
                symbol_cash_flow[symbol]['count'] += 1
                
                # 收集现金流数据
                for flow_type, field_name in [
                    ('operating_flows', 'net_operate_cash_flow'),
                    ('investing_flows', 'net_invest_cash_flow'),
                    ('financing_flows', 'net_finance_cash_flow'),
                    ('free_flows', 'free_cash_flow')
                ]:
                    if field_name in item and item[field_name] is not None:
                        try:
                            symbol_cash_flow[symbol][flow_type].append(float(item[field_name]))
                        except:
                            pass
            
            print("\n各股票现金流统计:")
            for symbol, flows in symbol_cash_flow.items():
                avg_operating = sum(flows['operating_flows']) / len(flows['operating_flows']) if flows['operating_flows'] else 0
                avg_free = sum(flows['free_flows']) / len(flows['free_flows']) if flows['free_flows'] else 0
                print(f"  {symbol}: {flows['count']}条记录, 平均经营现金流={avg_operating:.2f}, 平均自由现金流={avg_free:.2f}")
        
        # 分析数据结构
        analysis = analyze_cash_flow_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，覆盖{len(analysis['symbols'])}只股票")
        
        # 保存结果
        save_results(data_list, "multiple_stocks_cash_flow", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_cash_flow_analysis():
    """测试现金流分析和对比"""
    print("\n=== 测试现金流分析和对比 ===")
    
    # 选择几个现金流表现不同的公司进行对比
    symbols = [
        'SHSE.600519',  # 贵州茅台 - 现金流通常很好
        'SZSE.000002',  # 万科A - 房地产，现金流波动大
        'SHSE.600036'   # 招商银行 - 银行业现金流特点
    ]
    
    start_date = '2022-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbols}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_cash_flow(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = cash_flow_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = cash_flow_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"获取到{len(data_list)}条记录")
        
        if data_list:
            # 按股票和年份分析现金流趋势
            print("\n现金流趋势分析:")
            
            # 按股票分组
            symbol_data = {}
            for item in data_list:
                symbol = item.get('symbol', 'Unknown')
                end_date = item.get('end_date', '')
                
                if symbol not in symbol_data:
                    symbol_data[symbol] = []
                
                symbol_data[symbol].append({
                    'end_date': end_date,
                    'operating_flow': item.get('net_operate_cash_flow'),
                    'investing_flow': item.get('net_invest_cash_flow'),
                    'financing_flow': item.get('net_finance_cash_flow'),
                    'free_flow': item.get('free_cash_flow')
                })
            
            # 分析每个股票的现金流特征
            for symbol, records in symbol_data.items():
                print(f"\n  {symbol}:")
                
                # 按日期排序
                records.sort(key=lambda x: x['end_date'] or '')
                
                # 计算现金流稳定性
                operating_flows = [r['operating_flow'] for r in records if r['operating_flow'] is not None]
                free_flows = [r['free_flow'] for r in records if r['free_flow'] is not None]
                
                if operating_flows:
                    avg_operating = sum(operating_flows) / len(operating_flows)
                    print(f"    平均经营现金流: {avg_operating:.2f}")
                    
                    # 计算现金流稳定性（标准差）
                    if len(operating_flows) > 1:
                        variance = sum((x - avg_operating) ** 2 for x in operating_flows) / len(operating_flows)
                        std_dev = variance ** 0.5
                        stability = std_dev / abs(avg_operating) if avg_operating != 0 else float('inf')
                        print(f"    经营现金流稳定性系数: {stability:.2f} (越小越稳定)")
                
                if free_flows:
                    avg_free = sum(free_flows) / len(free_flows)
                    print(f"    平均自由现金流: {avg_free:.2f}")
                
                # 显示最近几期数据
                print(f"    最近3期数据:")
                for record in records[-3:]:
                    print(f"      {record['end_date']}: 经营={record['operating_flow']}, 自由={record['free_flow']}")
        
        # 保存结果
        save_results(data_list, "cash_flow_analysis")
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_seasonal_cash_flow_patterns():
    """测试季节性现金流模式"""
    print("\n=== 测试季节性现金流模式 ===")
    
    # 选择一个有明显季节性的行业股票
    symbol = 'SHSE.600519'  # 贵州茅台，白酒行业有季节性特征
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbol}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_cash_flow(
            symbols=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        # 转换为字典列表
        data_list = []
        if isinstance(result, list):
            for item in result:
                dict_item = cash_flow_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = cash_flow_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"获取到{len(data_list)}条记录")
        
        if data_list:
            # 按季度分析现金流模式
            print("\n季度现金流模式分析:")
            
            quarterly_data = {}
            for item in data_list:
                end_date = item.get('end_date', '')
                if end_date:
                    # 提取季度信息
                    if '03-31' in end_date:
                        quarter = 'Q1'
                    elif '06-30' in end_date:
                        quarter = 'Q2'
                    elif '09-30' in end_date:
                        quarter = 'Q3'
                    elif '12-31' in end_date:
                        quarter = 'Q4'
                    else:
                        quarter = 'Other'
                    
                    if quarter not in quarterly_data:
                        quarterly_data[quarter] = []
                    
                    quarterly_data[quarter].append({
                        'end_date': end_date,
                        'operating_flow': item.get('net_operate_cash_flow'),
                        'free_flow': item.get('free_cash_flow')
                    })
            
            # 分析各季度的现金流特征
            for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                if quarter in quarterly_data:
                    records = quarterly_data[quarter]
                    operating_flows = [r['operating_flow'] for r in records if r['operating_flow'] is not None]
                    
                    if operating_flows:
                        avg_flow = sum(operating_flows) / len(operating_flows)
                        print(f"  {quarter}: 平均经营现金流={avg_flow:.2f}, 数据点={len(operating_flows)}个")
                        
                        # 显示具体数据
                        for record in records:
                            print(f"    {record['end_date']}: {record['operating_flow']}")
        
        # 保存结果
        save_results(data_list, "seasonal_cash_flow_patterns")
        
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
            'name': '空字符串股票代码',
            'symbols': '',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
    ]
    
    results = {}
    
    for case in test_cases:
        try:
            print(f"\n测试: {case['name']}")
            print(f"  参数: symbols={case['symbols']}, start_date={case['start_date']}, end_date={case['end_date']}")
            
            result = gm.stk_get_fundamentals_cash_flow(
                symbols=case['symbols'],
                start_date=case['start_date'],
                end_date=case['end_date']
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = cash_flow_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = cash_flow_to_dict(result)
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
    save_results(results, "edge_cases_cash_flow")
    
    return results

def main():
    """主函数"""
    print("开始测试 gm.stk_get_fundamentals_cash_flow() API")
    print("=" * 60)
    
    # 初始化API
    if not init_api():
        print("API初始化失败，退出测试")
        return
    
    try:
        # 执行各项测试
        test_single_stock_cash_flow()
        test_multiple_stocks_cash_flow()
        test_cash_flow_analysis()
        test_seasonal_cash_flow_patterns()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("\n测试总结:")
        print("1. 单个股票现金流量表查询测试")
        print("2. 多个股票批量查询测试")
        print("3. 现金流分析和对比测试")
        print("4. 季节性现金流模式测试")
        print("5. 边界情况和异常处理测试")
        print("\n所有结果已保存到对应的JSON和CSV文件中")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()