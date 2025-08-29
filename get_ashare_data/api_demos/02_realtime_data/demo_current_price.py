#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: current_price() 实时价格查询
功能：测试 gm.current_price() API的各种用法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import gmtrade as gm
import pandas as pd
import json
from datetime import datetime
import time

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'gm_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None

def init_gm_api(config):
    """初始化GM API"""
    try:
        # 设置token
        gm.set_token(config['token'])
        
        # 设置服务地址
        gm.set_serv_addr(config['md_addr'])
        
        print("GM API初始化成功")
        return True
    except Exception as e:
        print(f"GM API初始化失败: {e}")
        return False

def test_current_price_single():
    """测试单个股票的实时价格"""
    print("\n=== 测试单个股票实时价格 ===")
    
    test_symbols = [
        'SZSE.000001',  # 平安银行
        'SHSE.600000',  # 浦发银行
        'SZSE.000002',  # 万科A
        'SHSE.600036',  # 招商银行
        'SHSE.000001'   # 上证指数
    ]
    
    results = []
    
    for symbol in test_symbols:
        try:
            print(f"\n查询 {symbol} 的实时价格...")
            
            # 获取实时价格
            price_data = gm.current_price(symbol)
            
            if price_data is not None:
                result = {
                    'symbol': symbol,
                    'price': price_data,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                print(f"  价格: {price_data}")
            else:
                result = {
                    'symbol': symbol,
                    'price': None,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无数据返回")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': symbol,
                'price': None,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_current_price_multiple():
    """测试多个股票的实时价格"""
    print("\n=== 测试多个股票实时价格 ===")
    
    symbols = [
        'SZSE.000001',  # 平安银行
        'SHSE.600000',  # 浦发银行
        'SZSE.000002',  # 万科A
        'SHSE.600036',  # 招商银行
        'SHSE.600519'   # 贵州茅台
    ]
    
    results = []
    
    try:
        print(f"\n批量查询 {len(symbols)} 个股票的实时价格...")
        
        # 批量获取实时价格
        for symbol in symbols:
            try:
                price_data = gm.current_price(symbol)
                
                result = {
                    'symbol': symbol,
                    'price': price_data,
                    'timestamp': datetime.now().isoformat(),
                    'success': price_data is not None,
                    'error': None if price_data is not None else 'No data returned'
                }
                
                print(f"  {symbol}: {price_data}")
                results.append(result)
                
            except Exception as e:
                print(f"  {symbol}: 查询失败 - {e}")
                results.append({
                    'symbol': symbol,
                    'price': None,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
        
    except Exception as e:
        print(f"批量查询失败: {e}")
        return [{
            'symbols': symbols,
            'prices': None,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': str(e)
        }]
    
    return results

def test_current_price_different_markets():
    """测试不同市场的实时价格"""
    print("\n=== 测试不同市场实时价格 ===")
    
    market_symbols = {
        '沪市股票': ['SHSE.600000', 'SHSE.600036', 'SHSE.600519'],
        '深市股票': ['SZSE.000001', 'SZSE.000002', 'SZSE.300015'],
        '指数': ['SHSE.000001', 'SZSE.399001', 'SZSE.399006'],
        '创业板': ['SZSE.300001', 'SZSE.300059', 'SZSE.300124']
    }
    
    all_results = {}
    
    for market_name, symbols in market_symbols.items():
        print(f"\n测试 {market_name}:")
        market_results = []
        
        for symbol in symbols:
            try:
                price_data = gm.current_price(symbol)
                
                result = {
                    'symbol': symbol,
                    'price': price_data,
                    'timestamp': datetime.now().isoformat(),
                    'success': price_data is not None,
                    'error': None if price_data is not None else 'No data returned'
                }
                
                print(f"  {symbol}: {price_data}")
                market_results.append(result)
                
            except Exception as e:
                print(f"  {symbol}: 查询失败 - {e}")
                market_results.append({
                    'symbol': symbol,
                    'price': None,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
        
        all_results[market_name] = market_results
    
    return all_results

def test_current_price_monitoring():
    """测试实时价格监控（连续获取）"""
    print("\n=== 测试实时价格监控 ===")
    
    symbol = 'SZSE.000001'  # 平安银行
    monitoring_duration = 30  # 监控30秒
    interval = 5  # 每5秒获取一次
    
    print(f"监控 {symbol} 的价格变化，持续 {monitoring_duration} 秒，每 {interval} 秒获取一次")
    
    results = []
    start_time = time.time()
    
    while time.time() - start_time < monitoring_duration:
        try:
            current_time = datetime.now()
            price_data = gm.current_price(symbol)
            
            result = {
                'symbol': symbol,
                'price': price_data,
                'timestamp': current_time.isoformat(),
                'elapsed_seconds': round(time.time() - start_time, 1),
                'success': price_data is not None,
                'error': None if price_data is not None else 'No data returned'
            }
            
            print(f"  {current_time.strftime('%H:%M:%S')} - {symbol}: {price_data}")
            results.append(result)
            
        except Exception as e:
            print(f"  {datetime.now().strftime('%H:%M:%S')} - 查询失败: {e}")
            results.append({
                'symbol': symbol,
                'price': None,
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': round(time.time() - start_time, 1),
                'success': False,
                'error': str(e)
            })
        
        time.sleep(interval)
    
    return results

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.current_price()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API current_price function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 如果结果是列表且包含字典，尝试保存为CSV
    try:
        if isinstance(results, list) and results and isinstance(results[0], dict):
            csv_filename = f"{filename_prefix}_results_{timestamp}.csv"
            df = pd.DataFrame(results)
            df.to_csv(csv_filename, encoding='utf-8-sig', index=False)
            print(f"结果已保存到: {csv_filename}")
        elif isinstance(results, dict):
            # 如果是嵌套字典，展平后保存
            flattened_results = []
            for market, market_results in results.items():
                for result in market_results:
                    result['market'] = market
                    flattened_results.append(result)
            
            if flattened_results:
                csv_filename = f"{filename_prefix}_results_{timestamp}.csv"
                df = pd.DataFrame(flattened_results)
                df.to_csv(csv_filename, encoding='utf-8-sig', index=False)
                print(f"结果已保存到: {csv_filename}")
    except Exception as e:
        print(f"保存CSV文件失败: {e}")

def main():
    """主函数"""
    print("GM API current_price() 功能测试")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    if not config:
        print("无法加载配置文件，退出测试")
        return
    
    # 初始化API
    if not init_gm_api(config):
        print("API初始化失败，退出测试")
        return
    
    try:
        # 测试1: 单个股票实时价格
        single_results = test_current_price_single()
        save_results(single_results, 'current_price_single')
        
        # 测试2: 多个股票实时价格
        multiple_results = test_current_price_multiple()
        save_results(multiple_results, 'current_price_multiple')
        
        # 测试3: 不同市场实时价格
        market_results = test_current_price_different_markets()
        save_results(market_results, 'current_price_markets')
        
        # 测试4: 实时价格监控
        print("\n即将开始价格监控测试...")
        monitoring_results = test_current_price_monitoring()
        save_results(monitoring_results, 'current_price_monitoring')
        
        # 汇总统计
        print("\n=== 测试汇总 ===")
        
        # 统计单个测试结果
        single_success = sum(1 for r in single_results if r['success'])
        print(f"单个股票测试: {single_success}/{len(single_results)} 成功")
        
        # 统计多个测试结果
        multiple_success = sum(1 for r in multiple_results if r['success'])
        print(f"多个股票测试: {multiple_success}/{len(multiple_results)} 成功")
        
        # 统计市场测试结果
        market_total = sum(len(results) for results in market_results.values())
        market_success = sum(sum(1 for r in results if r['success']) for results in market_results.values())
        print(f"不同市场测试: {market_success}/{market_total} 成功")
        
        # 统计监控测试结果
        monitoring_success = sum(1 for r in monitoring_results if r['success'])
        print(f"价格监控测试: {monitoring_success}/{len(monitoring_results)} 成功")
        
        # 总体统计
        total_tests = len(single_results) + len(multiple_results) + market_total + len(monitoring_results)
        total_success = single_success + multiple_success + market_success + monitoring_success
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\ncurrent_price() API测试完成！")

if __name__ == "__main__":
    main()