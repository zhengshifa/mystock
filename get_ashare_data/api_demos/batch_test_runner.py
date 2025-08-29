#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量测试运行器

本脚本用于批量运行所有API demo测试，并生成测试报告。
支持以下功能：
1. 自动发现所有demo文件
2. 并行或串行运行测试
3. 生成详细的测试报告
4. 按类别统计测试结果
5. 识别失败和最慢的测试
6. 支持超时控制
7. 生成HTML格式报告

作者: Assistant
创建时间: 2024-01-XX
"""

import os
import sys
import json
import subprocess
import time
import argparse
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def get_python_executable():
    """获取虚拟环境的Python可执行文件路径"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    venv_python = os.path.join(base_dir, '.venv', 'Scripts', 'python.exe')
    
    if os.path.exists(venv_python):
        return venv_python
    else:
        return sys.executable

def find_all_demo_files():
    """查找所有demo文件"""
    demo_files = []
    api_demos_dir = os.path.dirname(__file__)
    
    # 遍历所有子目录
    for root, dirs, files in os.walk(api_demos_dir):
        for file in files:
            if file.startswith('demo_') and file.endswith('.py'):
                demo_path = os.path.join(root, file)
                relative_path = os.path.relpath(demo_path, api_demos_dir)
                demo_files.append({
                    'file_path': demo_path,
                    'relative_path': relative_path,
                    'category': os.path.basename(root),
                    'demo_name': file[:-3]  # 去掉.py扩展名
                })
    
    return demo_files

def run_single_demo(demo_info, python_exe):
    """运行单个demo文件"""
    print(f"\n运行: {demo_info['relative_path']}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        # 运行demo文件
        result = subprocess.run(
            [python_exe, demo_info['file_path']],
            capture_output=True,
            text=True,
            timeout=300,  # 5分钟超时
            cwd=os.path.dirname(demo_info['file_path'])
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 分析运行结果
        success = result.returncode == 0
        
        # 检查是否有数据文件生成
        demo_dir = os.path.dirname(demo_info['file_path'])
        csv_files = [f for f in os.listdir(demo_dir) if f.endswith('.csv')]
        json_files = [f for f in os.listdir(demo_dir) if f.endswith('.json') and 'results' in f]
        
        # 统计数据获取情况
        data_acquired = len(csv_files) > 0 or len(json_files) > 0
        data_count = 0
        
        # 尝试从CSV文件统计数据条数
        for csv_file in csv_files:
            try:
                csv_path = os.path.join(demo_dir, csv_file)
                df = pd.read_csv(csv_path)
                data_count += len(df)
            except:
                pass
        
        # 尝试从JSON结果文件获取数据统计
        for json_file in json_files:
            try:
                json_path = os.path.join(demo_dir, json_file)
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    data_count += extract_data_count_from_json(json_data)
            except:
                pass
        
        result_info = {
            'demo_name': demo_info['demo_name'],
            'category': demo_info['category'],
            'relative_path': demo_info['relative_path'],
            'success': success,
            'execution_time': round(execution_time, 2),
            'return_code': result.returncode,
            'data_acquired': data_acquired,
            'data_count': data_count,
            'csv_files': len(csv_files),
            'json_files': len(json_files),
            'stdout_length': len(result.stdout),
            'stderr_length': len(result.stderr),
            'error_message': result.stderr if result.stderr else None,
            'timestamp': datetime.now().isoformat()
        }
        
        # 显示运行结果
        if success:
            print(f"✓ 运行成功 ({execution_time:.1f}秒)")
            if data_acquired:
                print(f"  数据获取: ✓ ({data_count} 条数据, {len(csv_files)} CSV文件)")
            else:
                print(f"  数据获取: ✗ (无数据文件生成)")
        else:
            print(f"✗ 运行失败 (返回码: {result.returncode})")
            if result.stderr:
                print(f"  错误信息: {result.stderr[:200]}..." if len(result.stderr) > 200 else f"  错误信息: {result.stderr}")
        
        return result_info
        
    except subprocess.TimeoutExpired:
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✗ 运行超时 ({execution_time:.1f}秒)")
        
        return {
            'demo_name': demo_info['demo_name'],
            'category': demo_info['category'],
            'relative_path': demo_info['relative_path'],
            'success': False,
            'execution_time': round(execution_time, 2),
            'return_code': -1,
            'data_acquired': False,
            'data_count': 0,
            'csv_files': 0,
            'json_files': 0,
            'error_message': 'Execution timeout (300s)',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✗ 运行异常: {str(e)}")
        
        return {
            'demo_name': demo_info['demo_name'],
            'category': demo_info['category'],
            'relative_path': demo_info['relative_path'],
            'success': False,
            'execution_time': round(execution_time, 2),
            'return_code': -2,
            'data_acquired': False,
            'data_count': 0,
            'csv_files': 0,
            'json_files': 0,
            'error_message': str(e),
            'timestamp': datetime.now().isoformat()
        }

def extract_data_count_from_json(data, path=""):
    """递归提取JSON中的数据计数"""
    total_count = 0
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'data_count' and isinstance(value, (int, float)):
                total_count += int(value)
            elif isinstance(value, (dict, list)):
                total_count += extract_data_count_from_json(value, f"{path}.{key}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                total_count += extract_data_count_from_json(item, f"{path}[{i}]")
    
    return total_count

def generate_test_report(results):
    """生成测试报告"""
    print("\n" + "=" * 80)
    print("API Demo 批量测试报告")
    print("=" * 80)
    
    # 总体统计
    total_demos = len(results)
    successful_demos = sum(1 for r in results if r['success'])
    data_acquired_demos = sum(1 for r in results if r['data_acquired'])
    total_data_count = sum(r['data_count'] for r in results)
    total_execution_time = sum(r['execution_time'] for r in results)
    
    print(f"\n总体统计:")
    print(f"  总demo数量: {total_demos}")
    print(f"  运行成功: {successful_demos} ({successful_demos/total_demos*100:.1f}%)")
    print(f"  数据获取成功: {data_acquired_demos} ({data_acquired_demos/total_demos*100:.1f}%)")
    print(f"  总数据条数: {total_data_count:,}")
    print(f"  总执行时间: {total_execution_time:.1f}秒")
    
    # 按分类统计
    categories = {}
    for result in results:
        category = result['category']
        if category not in categories:
            categories[category] = {
                'total': 0,
                'success': 0,
                'data_acquired': 0,
                'data_count': 0
            }
        
        categories[category]['total'] += 1
        if result['success']:
            categories[category]['success'] += 1
        if result['data_acquired']:
            categories[category]['data_acquired'] += 1
        categories[category]['data_count'] += result['data_count']
    
    print(f"\n按分类统计:")
    for category, stats in categories.items():
        success_rate = stats['success'] / stats['total'] * 100
        data_rate = stats['data_acquired'] / stats['total'] * 100
        print(f"  {category}:")
        print(f"    运行成功率: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        print(f"    数据获取率: {stats['data_acquired']}/{stats['total']} ({data_rate:.1f}%)")
        print(f"    数据条数: {stats['data_count']:,}")
    
    # 失败的demo
    failed_demos = [r for r in results if not r['success']]
    if failed_demos:
        print(f"\n运行失败的Demo ({len(failed_demos)}个):")
        for demo in failed_demos:
            print(f"  ✗ {demo['relative_path']}")
            if demo['error_message']:
                error_msg = demo['error_message'][:100] + "..." if len(demo['error_message']) > 100 else demo['error_message']
                print(f"    错误: {error_msg}")
    
    # 无数据获取的demo
    no_data_demos = [r for r in results if r['success'] and not r['data_acquired']]
    if no_data_demos:
        print(f"\n运行成功但无数据获取的Demo ({len(no_data_demos)}个):")
        for demo in no_data_demos:
            print(f"  ⚠ {demo['relative_path']}")
    
    return {
        'total_demos': total_demos,
        'successful_demos': successful_demos,
        'data_acquired_demos': data_acquired_demos,
        'total_data_count': total_data_count,
        'categories': categories,
        'failed_demos': len(failed_demos),
        'no_data_demos': len(no_data_demos)
    }

def main():
    """主函数"""
    print("GM API Demo 批量测试工具")
    print("=" * 60)
    
    # 获取Python可执行文件
    python_exe = get_python_executable()
    print(f"使用Python: {python_exe}")
    
    # 查找所有demo文件
    demo_files = find_all_demo_files()
    print(f"找到 {len(demo_files)} 个demo文件")
    
    if not demo_files:
        print("未找到任何demo文件！")
        return
    
    # 显示将要测试的demo
    print("\n将要测试的Demo:")
    for demo in demo_files:
        print(f"  - {demo['relative_path']} ({demo['category']})")
    
    input("\n按Enter键开始测试...")
    
    # 运行所有demo
    results = []
    start_time = time.time()
    
    for i, demo in enumerate(demo_files, 1):
        print(f"\n[{i}/{len(demo_files)}] ", end="")
        result = run_single_demo(demo, python_exe)
        results.append(result)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 生成报告
    summary = generate_test_report(results)
    
    # 保存详细结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存详细结果JSON
    detailed_results_file = f"api_demo_test_results_{timestamp}.json"
    with open(detailed_results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': round(total_time, 2),
                **summary
            },
            'detailed_results': results
        }, f, ensure_ascii=False, indent=2)
    
    # 保存CSV报告
    csv_results_file = f"api_demo_test_report_{timestamp}.csv"
    df = pd.DataFrame(results)
    df.to_csv(csv_results_file, encoding='utf-8-sig', index=False)
    
    print(f"\n=" * 80)
    print(f"测试完成！总耗时: {total_time:.1f}秒")
    print(f"详细结果已保存到:")
    print(f"  - {detailed_results_file}")
    print(f"  - {csv_results_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()