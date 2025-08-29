#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo for gm.stk_get_fundamentals_balance_sheet() API
测试获取股票资产负债表数据的API接口

主要功能:
1. 测试单个股票的资产负债表查询
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

def balance_sheet_to_dict(balance_sheet_obj):
    """将资产负债表对象转换为字典"""
    if balance_sheet_obj is None:
        return None
    
    # 获取对象的所有属性
    result = {}
    for attr in dir(balance_sheet_obj):
        if not attr.startswith('_'):
            try:
                value = getattr(balance_sheet_obj, attr)
                if not callable(value):
                    result[attr] = value
            except:
                continue
    
    return result

def analyze_balance_sheet_structure(data_list):
    """分析资产负债表数据结构"""
    if not data_list:
        return {"error": "数据为空"}
    
    analysis = {
        "total_records": len(data_list),
        "fields": set(),
        "sample_data": data_list[0] if data_list else None,
        "symbols": set(),
        "pub_dates": set(),
        "report_dates": set()
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

def test_single_stock_balance_sheet():
    """测试单个股票的资产负债表查询"""
    print("\n=== 测试单个股票资产负债表查询 ===")
    
    # 测试平安银行的资产负债表
    symbol = 'SZSE.000001'
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbol}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_balance_sheet(
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
                dict_item = balance_sheet_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = balance_sheet_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 显示前几条数据的关键字段
            print("\n前3条数据的关键信息:")
            for i, item in enumerate(data_list[:3]):
                print(f"  记录{i+1}: 股票={item.get('symbol', 'N/A')}, "
                      f"报告期={item.get('end_date', 'N/A')}, "
                      f"总资产={item.get('total_assets', 'N/A')}, "
                      f"总负债={item.get('total_liab', 'N/A')}")
        
        # 分析数据结构
        analysis = analyze_balance_sheet_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，{len(analysis['fields'])}个字段")
        
        # 保存结果
        save_results(data_list, "single_stock_balance_sheet", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_multiple_stocks_balance_sheet():
    """测试多个股票的资产负债表查询"""
    print("\n=== 测试多个股票资产负债表查询 ===")
    
    # 测试多个知名股票
    symbols = ['SZSE.000001', 'SZSE.000002', 'SHSE.600000', 'SHSE.600036']
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    try:
        print(f"查询股票: {symbols}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 调用API
        result = gm.stk_get_fundamentals_balance_sheet(
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
                dict_item = balance_sheet_to_dict(item)
                if dict_item:
                    data_list.append(dict_item)
        else:
            dict_item = balance_sheet_to_dict(result)
            if dict_item:
                data_list.append(dict_item)
        
        print(f"转换后数据条数: {len(data_list)}")
        
        if data_list:
            # 按股票分组统计
            symbol_stats = {}
            for item in data_list:
                symbol = item.get('symbol', 'Unknown')
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = 0
                symbol_stats[symbol] += 1
            
            print("\n各股票数据条数:")
            for symbol, count in symbol_stats.items():
                print(f"  {symbol}: {count}条")
        
        # 分析数据结构
        analysis = analyze_balance_sheet_structure(data_list)
        print(f"\n数据分析: 共{analysis['total_records']}条记录，覆盖{len(analysis['symbols'])}只股票")
        
        # 保存结果
        save_results(data_list, "multiple_stocks_balance_sheet", analysis)
        
        return data_list
        
    except Exception as e:
        print(f"查询失败: {e}")
        return []

def test_different_time_periods():
    """测试不同时间段的查询"""
    print("\n=== 测试不同时间段查询 ===")
    
    symbol = 'SHSE.600036'  # 招商银行
    test_periods = [
        ('2024-01-01', '2024-12-31', '2024年度'),
        ('2023-01-01', '2023-12-31', '2023年度'),
        ('2022-01-01', '2024-12-31', '2022-2024三年')
    ]
    
    all_results = {}
    
    for start_date, end_date, period_name in test_periods:
        try:
            print(f"\n查询{period_name}数据: {start_date} 到 {end_date}")
            
            result = gm.stk_get_fundamentals_balance_sheet(
                symbols=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = balance_sheet_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = balance_sheet_to_dict(result)
                if dict_item:
                    data_list.append(dict_item)
            
            print(f"  获取到{len(data_list)}条记录")
            all_results[period_name] = data_list
            
            time.sleep(0.1)  # 避免请求过快
            
        except Exception as e:
            print(f"  查询{period_name}失败: {e}")
            all_results[period_name] = []
    
    # 保存所有结果
    save_results(all_results, "different_periods_balance_sheet")
    
    return all_results

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
            'name': '错误的日期格式',
            'symbols': 'SZSE.000001',
            'start_date': '2024/01/01',
            'end_date': '2024/12/31'
        }
    ]
    
    results = {}
    
    for case in test_cases:
        try:
            print(f"\n测试: {case['name']}")
            print(f"  参数: symbols={case['symbols']}, start_date={case['start_date']}, end_date={case['end_date']}")
            
            result = gm.stk_get_fundamentals_balance_sheet(
                symbols=case['symbols'],
                start_date=case['start_date'],
                end_date=case['end_date']
            )
            
            # 转换为字典列表
            data_list = []
            if isinstance(result, list):
                for item in result:
                    dict_item = balance_sheet_to_dict(item)
                    if dict_item:
                        data_list.append(dict_item)
            else:
                dict_item = balance_sheet_to_dict(result)
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
    save_results(results, "edge_cases_balance_sheet")
    
    return results

def main():
    """主函数"""
    print("开始测试 gm.stk_get_fundamentals_balance_sheet() API")
    print("=" * 60)
    
    # 初始化API
    if not init_api():
        print("API初始化失败，退出测试")
        return
    
    try:
        # 执行各项测试
        test_single_stock_balance_sheet()
        test_multiple_stocks_balance_sheet()
        test_different_time_periods()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("\n测试总结:")
        print("1. 单个股票资产负债表查询测试")
        print("2. 多个股票批量查询测试")
        print("3. 不同时间段查询测试")
        print("4. 边界情况和异常处理测试")
        print("\n所有结果已保存到对应的JSON和CSV文件中")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()