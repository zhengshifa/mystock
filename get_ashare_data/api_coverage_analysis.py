#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API接口覆盖情况分析脚本

本脚本用于分析当前已创建的demo文件覆盖了哪些API接口，
以及还有哪些API接口没有被覆盖，需要补充demo文件。

作者: Assistant
创建时间: 2024-01-XX
"""

import os
import json
import re
from typing import List, Dict, Set
from pathlib import Path


def load_all_api_functions() -> List[Dict]:
    """
    加载所有GM API函数列表
    
    Returns:
        List[Dict]: API函数信息列表
    """
    try:
        with open('gm_api_functions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载API函数列表失败: {e}")
        return []


def scan_demo_files() -> Dict[str, List[str]]:
    """
    扫描所有demo文件，提取其中使用的API接口
    
    Returns:
        Dict[str, List[str]]: {demo文件路径: [使用的API接口列表]}
    """
    demo_api_usage = {}
    api_demos_dir = Path('api_demos')
    
    if not api_demos_dir.exists():
        print("api_demos目录不存在")
        return {}
    
    # 递归扫描所有.py文件
    for py_file in api_demos_dir.rglob('*.py'):
        if py_file.name == 'batch_test_runner.py':
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 提取gm.xxx()调用
            gm_calls = re.findall(r'gm\.([a-zA-Z_][a-zA-Z0-9_]*)', content)
            
            # 提取直接的API调用（如果有from gm.api import *）
            direct_calls = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            
            # 合并并去重
            all_calls = list(set(gm_calls + direct_calls))
            
            # 过滤掉明显不是API的调用
            filtered_calls = []
            for call in all_calls:
                if not call.startswith('_') and call not in [
                    'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set',
                    'range', 'enumerate', 'zip', 'open', 'json', 'pd', 'DataFrame',
                    'datetime', 'timedelta', 'os', 'sys', 'time', 'sleep', 'Path',
                    'load_config', 'save_results', 'init_gm_api', 'main', 'test_',
                    'analyze_', 'convert_', 'format_', 'get_', 'create_', 'update_',
                    'Exception', 'ValueError', 'KeyError', 'TypeError', 'ImportError'
                ]:
                    filtered_calls.append(call)
            
            if filtered_calls:
                demo_api_usage[str(py_file)] = filtered_calls
                
        except Exception as e:
            print(f"扫描文件 {py_file} 失败: {e}")
    
    return demo_api_usage


def analyze_api_coverage(all_apis: List[Dict], demo_usage: Dict[str, List[str]]) -> Dict:
    """
    分析API覆盖情况
    
    Args:
        all_apis: 所有API函数列表
        demo_usage: demo文件API使用情况
    
    Returns:
        Dict: 分析结果
    """
    # 提取所有API函数名
    all_api_names = {api['name'] for api in all_apis}
    
    # 提取已覆盖的API
    covered_apis = set()
    for apis in demo_usage.values():
        covered_apis.update(apis)
    
    # 过滤出真正的GM API
    covered_gm_apis = covered_apis.intersection(all_api_names)
    
    # 未覆盖的API
    uncovered_apis = all_api_names - covered_gm_apis
    
    # 按功能分类未覆盖的API
    uncovered_by_category = categorize_apis(uncovered_apis, all_apis)
    
    return {
        'total_apis': len(all_api_names),
        'covered_apis': len(covered_gm_apis),
        'uncovered_apis': len(uncovered_apis),
        'coverage_rate': len(covered_gm_apis) / len(all_api_names) * 100,
        'covered_api_list': sorted(covered_gm_apis),
        'uncovered_api_list': sorted(uncovered_apis),
        'uncovered_by_category': uncovered_by_category,
        'demo_usage': demo_usage
    }


def categorize_apis(api_names: Set[str], all_apis: List[Dict]) -> Dict[str, List[str]]:
    """
    按功能分类API接口
    
    Args:
        api_names: API名称集合
        all_apis: 所有API信息
    
    Returns:
        Dict[str, List[str]]: 按类别分组的API
    """
    categories = {
        '历史数据': [],
        '实时数据': [],
        '基础信息': [],
        '财务数据': [],
        '期权数据': [],
        '期货数据': [],
        '基金数据': [],
        '债券数据': [],
        '融资融券': [],
        '交易委托': [],
        '账户查询': [],
        '订阅管理': [],
        '系统设置': [],
        '其他': []
    }
    
    # 创建API名称到信息的映射
    api_info_map = {api['name']: api for api in all_apis}
    
    for api_name in api_names:
        if api_name not in api_info_map:
            continue
            
        api_info = api_info_map[api_name]
        doc = api_info.get('doc', '').lower()
        
        # 根据API名称和文档进行分类
        if any(keyword in api_name.lower() for keyword in ['history', 'get_history']):
            categories['历史数据'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['current', 'last_tick', 'subscribe', 'unsubscribe']):
            categories['实时数据'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['get_instruments', 'get_symbols', 'get_trading']):
            categories['基础信息'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['stk_get_fundamentals', 'stk_get_finance']):
            categories['财务数据'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['option_']):
            categories['期权数据'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['fut_']):
            categories['期货数据'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['fnd_', 'fund_']):
            categories['基金数据'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['bnd_', 'bond_']):
            categories['债券数据'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['credit_']):
            categories['融资融券'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['order_', 'algo_']):
            categories['交易委托'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['get_cash', 'get_position', 'get_orders']):
            categories['账户查询'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['subscribe', 'unsubscribe']):
            categories['订阅管理'].append(api_name)
        elif any(keyword in api_name.lower() for keyword in ['set_', 'schedule', 'timer']):
            categories['系统设置'].append(api_name)
        else:
            categories['其他'].append(api_name)
    
    # 移除空分类
    return {k: v for k, v in categories.items() if v}


def generate_report(analysis_result: Dict) -> str:
    """
    生成分析报告
    
    Args:
        analysis_result: 分析结果
    
    Returns:
        str: 报告内容
    """
    report = []
    report.append("# GM API接口覆盖情况分析报告")
    report.append("")
    report.append(f"## 总体情况")
    report.append(f"- 总API接口数: {analysis_result['total_apis']}")
    report.append(f"- 已覆盖接口数: {analysis_result['covered_apis']}")
    report.append(f"- 未覆盖接口数: {analysis_result['uncovered_apis']}")
    report.append(f"- 覆盖率: {analysis_result['coverage_rate']:.1f}%")
    report.append("")
    
    report.append("## 未覆盖的API接口（按功能分类）")
    report.append("")
    
    for category, apis in analysis_result['uncovered_by_category'].items():
        report.append(f"### {category} ({len(apis)}个)")
        for api in sorted(apis):
            report.append(f"- `{api}`")
        report.append("")
    
    report.append("## 已覆盖的API接口")
    report.append("")
    for api in analysis_result['covered_api_list']:
        report.append(f"- `{api}`")
    report.append("")
    
    report.append("## Demo文件API使用情况")
    report.append("")
    for demo_file, apis in analysis_result['demo_usage'].items():
        report.append(f"### {demo_file}")
        for api in sorted(apis):
            if api in analysis_result['covered_api_list']:
                report.append(f"- `{api}` ✓")
            else:
                report.append(f"- `{api}` (非GM API)")
        report.append("")
    
    return "\n".join(report)


def main():
    """
    主函数
    """
    print("开始分析GM API接口覆盖情况...")
    
    # 加载所有API函数
    all_apis = load_all_api_functions()
    if not all_apis:
        print("无法加载API函数列表，退出分析")
        return
    
    print(f"加载了 {len(all_apis)} 个API函数")
    
    # 扫描demo文件
    demo_usage = scan_demo_files()
    print(f"扫描了 {len(demo_usage)} 个demo文件")
    
    # 分析覆盖情况
    analysis_result = analyze_api_coverage(all_apis, demo_usage)
    
    # 生成报告
    report = generate_report(analysis_result)
    
    # 保存报告
    with open('api_coverage_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存详细数据
    with open('api_coverage_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    
    print("\n=== 分析结果 ===")
    print(f"总API接口数: {analysis_result['total_apis']}")
    print(f"已覆盖接口数: {analysis_result['covered_apis']}")
    print(f"未覆盖接口数: {analysis_result['uncovered_apis']}")
    print(f"覆盖率: {analysis_result['coverage_rate']:.1f}%")
    
    print("\n=== 未覆盖的API接口（按功能分类） ===")
    for category, apis in analysis_result['uncovered_by_category'].items():
        print(f"{category}: {len(apis)}个")
        for api in sorted(apis)[:5]:  # 只显示前5个
            print(f"  - {api}")
        if len(apis) > 5:
            print(f"  ... 还有{len(apis)-5}个")
    
    print("\n详细报告已保存到:")
    print("- api_coverage_report.md")
    print("- api_coverage_analysis.json")


if __name__ == '__main__':
    main()