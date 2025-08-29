#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK - 板块和成分股查询测试Demo
测试 get_sector, get_index_constituents, get_etf_constituents 等函数
"""

import json
import pandas as pd
import os
from datetime import datetime, timedelta
from gm.api import *

def configure_token():
    """
    配置GM SDK的token
    支持多种配置方式：
    1. 直接设置token
    2. 从配置文件读取
    3. 从环境变量读取
    """
    
    # 方法1: 直接设置token（不推荐，仅用于测试）
    # set_token('your_token_here')
    
    # 方法2: 从配置文件读取（推荐）
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
    
    # 方法3: 从环境变量读取
    token = os.getenv('GM_TOKEN')
    if token:
        set_token(token)
        print("已从环境变量 GM_TOKEN 读取token")
        return True
    
    print("警告: 未找到有效的token配置")
    print("请通过以下方式之一配置token:")
    print("1. 创建 gm_config.json 文件并设置token")
    print("2. 设置环境变量 GM_TOKEN")
    print("3. 在代码中直接调用 set_token('your_token')")
    return False

def test_sector_constituents():
    """测试板块和成分股查询"""
    print("=" * 60)
    print("板块和成分股查询测试Demo")
    print("=" * 60)
    
    results = {}
    
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试 get_sector 函数
    print("\n" + "=" * 40)
    print("1. 测试 get_sector 函数")
    print("=" * 40)
    
    sector_results = {}
    
    # 测试不同板块分类
    sector_test_cases = [
        {'code': 'sw_l1', 'name': '申万一级行业'},
        {'code': 'sw_l2', 'name': '申万二级行业'},
        {'code': 'sw_l3', 'name': '申万三级行业'},
        {'code': 'zjh', 'name': '证监会行业分类'},
        {'code': 'concept', 'name': '概念板块'},
        {'code': 'area', 'name': '地域板块'},
    ]
    
    for case in sector_test_cases:
        try:
            print(f"\n测试: {case['name']}")
            
            sector_data = get_sector(
                code=case['code']
            )
            
            if sector_data is not None and len(sector_data) > 0:
                # 转换为DataFrame以便处理
                if isinstance(sector_data, list):
                    sector_df = pd.DataFrame(sector_data)
                else:
                    sector_df = sector_data
                
                sector_results[case['name']] = {
                    'code': case['code'],
                    'count': len(sector_df),
                    'columns': list(sector_df.columns),
                    'sample_data': sector_df.head(5).to_dict('records'),
                    'data_types': {col: str(sector_df[col].dtype) for col in sector_df.columns}
                }
                print(f"    ✓ 获取到 {len(sector_df)} 个板块")
                print(f"    ✓ 列名: {list(sector_df.columns)}")
                if 'sector_name' in sector_df.columns:
                    print(f"    ✓ 样本板块: {sector_df['sector_name'].head(3).tolist()}")
                
                # 保存到CSV
                csv_filename = f"sector_{case['name']}.csv"
                sector_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                sector_results[case['name']] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            sector_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['sector_test'] = sector_results
    
    # 2. 测试特定板块的成分股查询
    print("\n" + "=" * 40)
    print("2. 测试特定板块成分股查询")
    print("=" * 40)
    
    sector_constituents_results = {}
    
    # 测试一些知名板块的成分股
    sector_constituents_cases = [
        {'sector': '801010', 'name': '申万农林牧渔'},
        {'sector': '801020', 'name': '申万采掘'},
        {'sector': '801030', 'name': '申万化工'},
        {'sector': '801040', 'name': '申万钢铁'},
        {'sector': '801050', 'name': '申万有色金属'},
        {'sector': '801080', 'name': '申万电子'},
        {'sector': '801110', 'name': '申万家用电器'},
        {'sector': '801120', 'name': '申万食品饮料'},
        {'sector': '801150', 'name': '申万医药生物'},
        {'sector': '801160', 'name': '申万公用事业'},
        {'sector': '801170', 'name': '申万交通运输'},
        {'sector': '801180', 'name': '申万房地产'},
        {'sector': '801200', 'name': '申万商业贸易'},
        {'sector': '801210', 'name': '申万休闲服务'},
        {'sector': '801230', 'name': '申万银行'},
        {'sector': '801710', 'name': '申万建筑材料'},
        {'sector': '801720', 'name': '申万建筑装饰'},
        {'sector': '801730', 'name': '申万电气设备'},
        {'sector': '801740', 'name': '申万国防军工'},
        {'sector': '801750', 'name': '申万计算机'},
        {'sector': '801760', 'name': '申万传媒'},
        {'sector': '801770', 'name': '申万通信'},
        {'sector': '801780', 'name': '申万银行'},
        {'sector': '801790', 'name': '申万非银金融'},
        {'sector': '801880', 'name': '申万汽车'},
        {'sector': '801890', 'name': '申万机械设备'},
    ]
    
    # 只测试前5个板块，避免过多请求
    for case in sector_constituents_cases[:5]:
        try:
            print(f"\n测试: {case['name']} 成分股")
            
            constituents = get_sector(
                code='sw_l1',
                symbol=case['sector']
            )
            
            if constituents is not None and len(constituents) > 0:
                # 转换为DataFrame以便处理
                if isinstance(constituents, list):
                    constituents_df = pd.DataFrame(constituents)
                else:
                    constituents_df = constituents
                
                sector_constituents_results[case['name']] = {
                    'sector_code': case['sector'],
                    'count': len(constituents_df),
                    'columns': list(constituents_df.columns),
                    'sample_constituents': constituents_df.head(10).to_dict('records') if len(constituents_df) >= 10 else constituents_df.to_dict('records')
                }
                print(f"    ✓ 获取到 {len(constituents_df)} 只成分股")
                if 'symbol' in constituents_df.columns:
                    print(f"    ✓ 样本成分股: {constituents_df['symbol'].head(5).tolist()}")
                
                # 保存到CSV
                csv_filename = f"constituents_{case['name']}.csv"
                constituents_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                sector_constituents_results[case['name']] = {'error': '无数据返回'}
                print(f"    ✗ 无数据返回")
                
        except Exception as e:
            sector_constituents_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['sector_constituents_test'] = sector_constituents_results
    
    # 3. 测试指数成分股查询
    print("\n" + "=" * 40)
    print("3. 测试指数成分股查询")
    print("=" * 40)
    
    index_constituents_results = {}
    
    # 测试主要指数的成分股
    index_test_cases = [
        {'symbol': 'SHSE.000001', 'name': '上证指数'},
        {'symbol': 'SZSE.399001', 'name': '深证成指'},
        {'symbol': 'SZSE.399006', 'name': '创业板指'},
        {'symbol': 'SHSE.000016', 'name': '上证50'},
        {'symbol': 'SHSE.000300', 'name': '沪深300'},
        {'symbol': 'SHSE.000905', 'name': '中证500'},
        {'symbol': 'SZSE.399905', 'name': '中证500'},
    ]
    
    for case in index_test_cases:
        try:
            print(f"\n测试: {case['name']} 成分股")
            
            # 尝试使用 get_index_constituents 函数
            try:
                constituents = get_index_constituents(
                    index=case['symbol']
                )
            except:
                # 如果没有该函数，尝试其他方法
                constituents = None
            
            if constituents is not None and len(constituents) > 0:
                # 转换为DataFrame以便处理
                if isinstance(constituents, list):
                    constituents_df = pd.DataFrame(constituents)
                else:
                    constituents_df = constituents
                
                index_constituents_results[case['name']] = {
                    'index_symbol': case['symbol'],
                    'count': len(constituents_df),
                    'columns': list(constituents_df.columns),
                    'sample_constituents': constituents_df.head(10).to_dict('records') if len(constituents_df) >= 10 else constituents_df.to_dict('records')
                }
                print(f"    ✓ 获取到 {len(constituents_df)} 只成分股")
                if 'symbol' in constituents_df.columns:
                    print(f"    ✓ 样本成分股: {constituents_df['symbol'].head(5).tolist()}")
                
                # 保存到CSV
                csv_filename = f"index_constituents_{case['name']}.csv"
                constituents_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                index_constituents_results[case['name']] = {'error': '无数据返回或函数不存在'}
                print(f"    ✗ 无数据返回或函数不存在")
                
        except Exception as e:
            index_constituents_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['index_constituents_test'] = index_constituents_results
    
    # 4. 测试ETF成分股查询
    print("\n" + "=" * 40)
    print("4. 测试ETF成分股查询")
    print("=" * 40)
    
    etf_constituents_results = {}
    
    # 测试主要ETF的成分股
    etf_test_cases = [
        {'symbol': 'SHSE.510300', 'name': '沪深300ETF'},
        {'symbol': 'SHSE.510500', 'name': '中证500ETF'},
        {'symbol': 'SHSE.510050', 'name': '上证50ETF'},
        {'symbol': 'SZSE.159919', 'name': '沪深300ETF'},
        {'symbol': 'SZSE.159915', 'name': '创业板ETF'},
    ]
    
    for case in etf_test_cases:
        try:
            print(f"\n测试: {case['name']} 成分股")
            
            # 使用 get_etf_constituents 函数
            try:
                constituents = get_etf_constituents(
                    symbol=case['symbol']
                )
            except:
                # 如果没有该函数，跳过
                constituents = None
            
            if constituents is not None and len(constituents) > 0:
                # 转换为DataFrame以便处理
                if isinstance(constituents, list):
                    constituents_df = pd.DataFrame(constituents)
                else:
                    constituents_df = constituents
                
                etf_constituents_results[case['name']] = {
                    'etf_symbol': case['symbol'],
                    'count': len(constituents_df),
                    'columns': list(constituents_df.columns),
                    'sample_constituents': constituents_df.head(10).to_dict('records') if len(constituents_df) >= 10 else constituents_df.to_dict('records')
                }
                print(f"    ✓ 获取到 {len(constituents_df)} 只成分股")
                if 'symbol' in constituents_df.columns:
                    print(f"    ✓ 样本成分股: {constituents_df['symbol'].head(5).tolist()}")
                
                # 保存到CSV
                csv_filename = f"etf_constituents_{case['name']}.csv"
                constituents_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"    ✓ 数据已保存到: {csv_filename}")
                
            else:
                etf_constituents_results[case['name']] = {'error': '无数据返回或函数不存在'}
                print(f"    ✗ 无数据返回或函数不存在")
                
        except Exception as e:
            etf_constituents_results[case['name']] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['etf_constituents_test'] = etf_constituents_results
    
    # 5. 测试概念板块查询
    print("\n" + "=" * 40)
    print("5. 测试概念板块查询")
    print("=" * 40)
    
    concept_results = {}
    
    try:
        print(f"\n查询概念板块...")
        
        concept_data = get_sector(
            code='concept'
        )
        
        if concept_data is not None and len(concept_data) > 0:
            # 转换为DataFrame以便处理
            if isinstance(concept_data, list):
                concept_df = pd.DataFrame(concept_data)
            else:
                concept_df = concept_data
            
            concept_results = {
                'count': len(concept_df),
                'columns': list(concept_df.columns),
                'sample_concepts': concept_df.head(20).to_dict('records') if len(concept_df) >= 20 else concept_df.to_dict('records')
            }
            print(f"    ✓ 获取到 {len(concept_df)} 个概念板块")
            if 'sector_name' in concept_df.columns:
                print(f"    ✓ 样本概念: {concept_df['sector_name'].head(10).tolist()}")
            
            # 保存到CSV
            concept_df.to_csv('concept_sectors.csv', index=False, encoding='utf-8-sig')
            print(f"    ✓ 数据已保存到: concept_sectors.csv")
            
        else:
            concept_results = {'error': '无数据返回'}
            print(f"    ✗ 无数据返回")
            
    except Exception as e:
        concept_results = {'error': str(e)}
        print(f"    ✗ 概念板块查询错误: {e}")
    
    results['concept_test'] = concept_results
    
    # 6. 测试地域板块查询
    print("\n" + "=" * 40)
    print("6. 测试地域板块查询")
    print("=" * 40)
    
    area_results = {}
    
    try:
        print(f"\n查询地域板块...")
        
        area_data = get_sector(
            code='area'
        )
        
        if area_data is not None and len(area_data) > 0:
            # 转换为DataFrame以便处理
            if isinstance(area_data, list):
                area_df = pd.DataFrame(area_data)
            else:
                area_df = area_data
            
            area_results = {
                'count': len(area_df),
                'columns': list(area_df.columns),
                'sample_areas': area_df.head(20).to_dict('records') if len(area_df) >= 20 else area_df.to_dict('records')
            }
            print(f"    ✓ 获取到 {len(area_df)} 个地域板块")
            if 'sector_name' in area_df.columns:
                print(f"    ✓ 样本地域: {area_df['sector_name'].head(10).tolist()}")
            
            # 保存到CSV
            area_df.to_csv('area_sectors.csv', index=False, encoding='utf-8-sig')
            print(f"    ✓ 数据已保存到: area_sectors.csv")
            
        else:
            area_results = {'error': '无数据返回'}
            print(f"    ✗ 无数据返回")
            
    except Exception as e:
        area_results = {'error': str(e)}
        print(f"    ✗ 地域板块查询错误: {e}")
    
    results['area_test'] = area_results
    
    # 保存测试结果
    with open('demo_5_sector_constituents_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("板块和成分股查询测试完成！")
    print("详细结果已保存到: demo_5_sector_constituents_results.json")
    print("CSV数据文件已保存到当前目录")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    try:
        # 配置token
        if not configure_token():
            print("\n请先配置有效的token后再运行测试")
            exit(1)
        
        # 测试token有效性
        try:
            test_dates = get_trading_dates('SHSE', '2024-01-01', '2024-01-05')
            if not test_dates:
                print("Token验证失败，请检查token是否有效")
                exit(1)
            print("Token验证成功")
        except Exception as e:
            print(f"Token验证失败: {e}")
            exit(1)
        
        # 运行测试
        test_results = test_sector_constituents()
        
        # 打印总结
        print("\n测试总结:")
        
        if 'sector_test' in test_results:
            total_sectors = len(test_results['sector_test'])
            successful_sectors = sum(1 for data in test_results['sector_test'].values() if 'error' not in data)
            print(f"get_sector函数测试: {successful_sectors}/{total_sectors} 成功")
        
        if 'sector_constituents_test' in test_results:
            total_constituents = len(test_results['sector_constituents_test'])
            successful_constituents = sum(1 for data in test_results['sector_constituents_test'].values() if 'error' not in data)
            print(f"板块成分股查询测试: {successful_constituents}/{total_constituents} 成功")
        
        if 'index_constituents_test' in test_results:
            total_index = len(test_results['index_constituents_test'])
            successful_index = sum(1 for data in test_results['index_constituents_test'].values() if 'error' not in data)
            print(f"指数成分股查询测试: {successful_index}/{total_index} 成功")
        
        if 'etf_constituents_test' in test_results:
            total_etf = len(test_results['etf_constituents_test'])
            successful_etf = sum(1 for data in test_results['etf_constituents_test'].values() if 'error' not in data)
            print(f"ETF成分股查询测试: {successful_etf}/{total_etf} 成功")
        
        concept_success = 'error' not in test_results.get('concept_test', {'error': 'not tested'})
        print(f"概念板块查询测试: {'成功' if concept_success else '失败'}")
        
        area_success = 'error' not in test_results.get('area_test', {'error': 'not tested'})
        print(f"地域板块查询测试: {'成功' if area_success else '失败'}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()