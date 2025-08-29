#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_stk_split() 获取股票拆分信息
功能：测试 gm.get_stk_split() API的各种用法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import gmtrade as gm
import pandas as pd
import json
from datetime import datetime, timedelta
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

def stk_split_to_dict(stk_split):
    """将stk_split对象转换为字典格式"""
    if stk_split is None:
        return None
    
    try:
        split_dict = {}
        
        # 常见的stk_split属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'split_date', 'ex_date', 'record_date', 'pay_date',
            'split_ratio', 'split_from', 'split_to', 'split_type',
            'split_reason', 'announcement_date', 'board_date',
            'shareholder_meeting_date', 'effective_date',
            'pre_split_shares', 'post_split_shares', 'split_factor',
            'currency', 'market_cap_before', 'market_cap_after',
            'price_adjustment_factor', 'volume_adjustment_factor',
            'created_at', 'updated_at', 'data_source', 'status'
        ]
        
        for attr in attributes:
            if hasattr(stk_split, attr):
                value = getattr(stk_split, attr)
                # 处理日期时间类型
                if attr in ['split_date', 'ex_date', 'record_date', 'pay_date', 
                           'announcement_date', 'board_date', 'shareholder_meeting_date', 
                           'effective_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            split_dict[attr] = value.strftime('%Y-%m-%d')
                        else:
                            split_dict[attr] = str(value)
                    except:
                        split_dict[attr] = str(value)
                else:
                    split_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not split_dict:
            split_dict = {'raw_data': str(stk_split)}
        
        return split_dict
        
    except Exception as e:
        return {'error': f'Failed to convert stk_split: {e}', 'raw_data': str(stk_split)}

def test_get_stk_split_major_stocks():
    """测试主要股票的拆分信息查询"""
    print("\n=== 测试主要股票的拆分信息查询 ===")
    
    # 测试主要股票（选择一些可能有拆分历史的股票）
    major_stocks = [
        {'symbol': 'SHSE.600000', 'name': '浦发银行'},
        {'symbol': 'SHSE.600036', 'name': '招商银行'},
        {'symbol': 'SHSE.600519', 'name': '贵州茅台'},
        {'symbol': 'SHSE.600887', 'name': '伊利股份'},
        {'symbol': 'SHSE.601318', 'name': '中国平安'},
        {'symbol': 'SZSE.000001', 'name': '平安银行'},
        {'symbol': 'SZSE.000002', 'name': '万科A'},
        {'symbol': 'SZSE.000858', 'name': '五粮液'},
        {'symbol': 'SZSE.002415', 'name': '海康威视'},
        {'symbol': 'SZSE.300059', 'name': '东方财富'}
    ]
    
    results = []
    
    # 查询时间范围（最近5年）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    
    for stock_info in major_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的拆分信息...")
            print(f"  查询时间范围: {start_date} 到 {end_date}")
            
            # 获取拆分信息
            stk_split = gm.get_stk_split(
                symbol=stock_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if stk_split is not None:
                # 转换为字典列表
                split_list = []
                if hasattr(stk_split, '__iter__') and not isinstance(stk_split, str):
                    for split in stk_split:
                        split_dict = stk_split_to_dict(split)
                        if split_dict:
                            split_list.append(split_dict)
                else:
                    split_dict = stk_split_to_dict(stk_split)
                    if split_dict:
                        split_list.append(split_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'splits': split_list,
                    'count': len(split_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(split_list)} 条拆分记录")
                
                # 分析拆分信息
                if split_list:
                    print(f"  拆分详情:")
                    for i, split in enumerate(split_list[:5]):  # 显示前5条
                        split_date = split.get('split_date')
                        ex_date = split.get('ex_date')
                        split_ratio = split.get('split_ratio')
                        split_from = split.get('split_from')
                        split_to = split.get('split_to')
                        split_type = split.get('split_type')
                        split_reason = split.get('split_reason')
                        
                        print(f"    拆分 {i+1}:")
                        if split_date:
                            print(f"      拆分日期: {split_date}")
                        if ex_date:
                            print(f"      除权日期: {ex_date}")
                        if split_ratio is not None:
                            print(f"      拆分比例: {split_ratio}")
                        if split_from is not None and split_to is not None:
                            print(f"      拆分方案: {split_from} 拆 {split_to}")
                        if split_type:
                            print(f"      拆分类型: {split_type}")
                        if split_reason:
                            print(f"      拆分原因: {split_reason}")
                        
                        # 计算拆分倍数
                        if isinstance(split_from, (int, float)) and isinstance(split_to, (int, float)) and split_from > 0:
                            split_multiple = split_to / split_from
                            print(f"      拆分倍数: {split_multiple:.2f}x")
                        
                        # 显示股本变化
                        pre_split_shares = split.get('pre_split_shares')
                        post_split_shares = split.get('post_split_shares')
                        
                        if pre_split_shares is not None and post_split_shares is not None:
                            if isinstance(pre_split_shares, (int, float)) and isinstance(post_split_shares, (int, float)):
                                print(f"      股本变化: {pre_split_shares:,.0f} -> {post_split_shares:,.0f}")
                                if pre_split_shares > 0:
                                    change_ratio = (post_split_shares - pre_split_shares) / pre_split_shares * 100
                                    print(f"      股本增长: {change_ratio:.2f}%")
                        
                        # 显示价格调整因子
                        price_adj_factor = split.get('price_adjustment_factor')
                        volume_adj_factor = split.get('volume_adjustment_factor')
                        
                        if price_adj_factor is not None or volume_adj_factor is not None:
                            print(f"      调整因子:")
                            if price_adj_factor is not None:
                                print(f"        价格调整: {price_adj_factor}")
                            if volume_adj_factor is not None:
                                print(f"        成交量调整: {volume_adj_factor}")
                    
                    if len(split_list) > 5:
                        print(f"    ... 还有 {len(split_list) - 5} 条拆分记录")
                    
                    # 统计拆分类型
                    split_types = {}
                    for split in split_list:
                        split_type = split.get('split_type', '未知')
                        split_types[split_type] = split_types.get(split_type, 0) + 1
                    
                    if split_types:
                        print(f"  拆分类型统计: {dict(split_types)}")
                    
                    # 统计拆分年份
                    split_years = {}
                    for split in split_list:
                        split_date = split.get('split_date')
                        if split_date:
                            try:
                                year = split_date[:4] if isinstance(split_date, str) and len(split_date) >= 4 else '未知'
                                split_years[year] = split_years.get(year, 0) + 1
                            except:
                                split_years['未知'] = split_years.get('未知', 0) + 1
                    
                    if split_years:
                        print(f"  拆分年份分布: {dict(sorted(split_years.items()))}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'splits': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无拆分数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'splits': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_stk_split_different_periods():
    """测试不同时间段的拆分信息查询"""
    print("\n=== 测试不同时间段的拆分信息查询 ===")
    
    # 测试不同的时间段
    test_periods = [
        {
            'name': '最近1年',
            'start_date': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '最近3年',
            'start_date': (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '最近5年',
            'start_date': (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '2020-2023年',
            'start_date': '2020-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '2015-2019年',
            'start_date': '2015-01-01',
            'end_date': '2019-12-31'
        },
        {
            'name': '2010-2014年',
            'start_date': '2010-01-01',
            'end_date': '2014-12-31'
        },
        {
            'name': '2005-2009年',
            'start_date': '2005-01-01',
            'end_date': '2009-12-31'
        }
    ]
    
    results = []
    
    # 选择几个有代表性的股票
    test_symbols = [
        {'symbol': 'SHSE.600519', 'name': '贵州茅台'},
        {'symbol': 'SZSE.000002', 'name': '万科A'},
        {'symbol': 'SZSE.000858', 'name': '五粮液'}
    ]
    
    for period_info in test_periods:
        try:
            print(f"\n测试时间段: {period_info['name']} ({period_info['start_date']} 到 {period_info['end_date']})")
            
            period_result = {
                'period_name': period_info['name'],
                'start_date': period_info['start_date'],
                'end_date': period_info['end_date'],
                'stocks': [],
                'total_splits': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            for stock_info in test_symbols:
                try:
                    print(f"  查询 {stock_info['name']} ({stock_info['symbol']})...")
                    
                    # 获取拆分信息
                    stk_split = gm.get_stk_split(
                        symbol=stock_info['symbol'],
                        start_date=period_info['start_date'],
                        end_date=period_info['end_date']
                    )
                    
                    if stk_split is not None:
                        # 转换为字典列表
                        split_list = []
                        if hasattr(stk_split, '__iter__') and not isinstance(stk_split, str):
                            for split in stk_split:
                                split_dict = stk_split_to_dict(split)
                                if split_dict:
                                    split_list.append(split_dict)
                        else:
                            split_dict = stk_split_to_dict(stk_split)
                            if split_dict:
                                split_list.append(split_dict)
                        
                        stock_result = {
                            'symbol': stock_info['symbol'],
                            'name': stock_info['name'],
                            'splits': split_list,
                            'count': len(split_list),
                            'success': True,
                            'error': None
                        }
                        
                        print(f"    获取到 {len(split_list)} 条拆分记录")
                        period_result['total_splits'] += len(split_list)
                        
                        # 显示拆分摘要
                        if split_list:
                            for split in split_list:
                                split_date = split.get('split_date')
                                split_from = split.get('split_from')
                                split_to = split.get('split_to')
                                split_type = split.get('split_type')
                                
                                summary_parts = []
                                if split_date:
                                    summary_parts.append(f"日期: {split_date}")
                                if split_from is not None and split_to is not None:
                                    summary_parts.append(f"方案: {split_from}拆{split_to}")
                                if split_type:
                                    summary_parts.append(f"类型: {split_type}")
                                
                                print(f"      {', '.join(summary_parts)}")
                        
                    else:
                        stock_result = {
                            'symbol': stock_info['symbol'],
                            'name': stock_info['name'],
                            'splits': [],
                            'count': 0,
                            'success': False,
                            'error': 'No data returned'
                        }
                        print(f"    无拆分数据")
                    
                    period_result['stocks'].append(stock_result)
                    
                except Exception as e:
                    print(f"    查询失败: {e}")
                    period_result['stocks'].append({
                        'symbol': stock_info['symbol'],
                        'name': stock_info['name'],
                        'splits': [],
                        'count': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            print(f"  时间段总拆分数: {period_result['total_splits']}")
            results.append(period_result)
            
        except Exception as e:
            print(f"  时间段查询失败: {e}")
            results.append({
                'period_name': period_info['name'],
                'start_date': period_info['start_date'],
                'end_date': period_info['end_date'],
                'stocks': [],
                'total_splits': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
    
    return results

def test_get_stk_split_single_date():
    """测试单日拆分信息查询"""
    print("\n=== 测试单日拆分信息查询 ===")
    
    # 测试一些可能有拆分的特定日期
    test_dates = [
        '2023-06-15',  # 随机选择的日期
        '2022-12-31',  # 年末
        '2022-06-30',  # 年中
        '2021-12-31',  # 年末
        '2020-12-31',  # 年末
        '2019-06-30',  # 年中
        '2018-12-31',  # 年末
    ]
    
    results = []
    
    # 选择一些股票进行测试
    test_symbols = [
        {'symbol': 'SHSE.600519', 'name': '贵州茅台'},
        {'symbol': 'SZSE.000002', 'name': '万科A'},
        {'symbol': 'SZSE.000858', 'name': '五粮液'},
        {'symbol': 'SHSE.600036', 'name': '招商银行'}
    ]
    
    for test_date in test_dates:
        try:
            print(f"\n测试日期: {test_date}")
            
            date_result = {
                'test_date': test_date,
                'stocks': [],
                'total_splits': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            for stock_info in test_symbols:
                try:
                    print(f"  查询 {stock_info['name']} ({stock_info['symbol']})...")
                    
                    # 获取单日拆分信息
                    stk_split = gm.get_stk_split(
                        symbol=stock_info['symbol'],
                        start_date=test_date,
                        end_date=test_date
                    )
                    
                    if stk_split is not None:
                        # 转换为字典列表
                        split_list = []
                        if hasattr(stk_split, '__iter__') and not isinstance(stk_split, str):
                            for split in stk_split:
                                split_dict = stk_split_to_dict(split)
                                if split_dict:
                                    split_list.append(split_dict)
                        else:
                            split_dict = stk_split_to_dict(stk_split)
                            if split_dict:
                                split_list.append(split_dict)
                        
                        stock_result = {
                            'symbol': stock_info['symbol'],
                            'name': stock_info['name'],
                            'splits': split_list,
                            'count': len(split_list),
                            'success': True,
                            'error': None
                        }
                        
                        if split_list:
                            print(f"    发现 {len(split_list)} 条拆分记录")
                            date_result['total_splits'] += len(split_list)
                            
                            # 显示拆分详情
                            for split in split_list:
                                split_date = split.get('split_date')
                                ex_date = split.get('ex_date')
                                split_from = split.get('split_from')
                                split_to = split.get('split_to')
                                split_type = split.get('split_type')
                                
                                details = []
                                if split_date:
                                    details.append(f"拆分日: {split_date}")
                                if ex_date:
                                    details.append(f"除权日: {ex_date}")
                                if split_from is not None and split_to is not None:
                                    details.append(f"方案: {split_from}拆{split_to}")
                                if split_type:
                                    details.append(f"类型: {split_type}")
                                
                                print(f"      {', '.join(details)}")
                        else:
                            print(f"    无拆分记录")
                        
                    else:
                        stock_result = {
                            'symbol': stock_info['symbol'],
                            'name': stock_info['name'],
                            'splits': [],
                            'count': 0,
                            'success': False,
                            'error': 'No data returned'
                        }
                        print(f"    无拆分数据")
                    
                    date_result['stocks'].append(stock_result)
                    
                except Exception as e:
                    print(f"    查询失败: {e}")
                    date_result['stocks'].append({
                        'symbol': stock_info['symbol'],
                        'name': stock_info['name'],
                        'splits': [],
                        'count': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            print(f"  当日总拆分数: {date_result['total_splits']}")
            results.append(date_result)
            
        except Exception as e:
            print(f"  日期查询失败: {e}")
            results.append({
                'test_date': test_date,
                'stocks': [],
                'total_splits': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
    
    return results

def test_get_stk_split_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的股票代码',
            'symbol': 'INVALID.123456',
            'start_date': '2020-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '未来日期范围',
            'symbol': 'SHSE.600000',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'symbol': 'SHSE.600000',
            'start_date': '1990-01-01',
            'end_date': '1995-12-31'
        },
        {
            'name': '开始日期晚于结束日期',
            'symbol': 'SHSE.600000',
            'start_date': '2023-12-31',
            'end_date': '2023-01-01'
        },
        {
            'name': '相同的开始和结束日期',
            'symbol': 'SHSE.600000',
            'start_date': '2023-06-15',
            'end_date': '2023-06-15'
        },
        {
            'name': '空字符串股票代码',
            'symbol': '',
            'start_date': '2020-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '格式错误的股票代码',
            'symbol': '600000',  # 缺少交易所前缀
            'start_date': '2020-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '格式错误的日期',
            'symbol': 'SHSE.600000',
            'start_date': '2023-13-01',  # 不存在的月份
            'end_date': '2023-12-31'
        },
        {
            'name': '非常长的时间范围',
            'symbol': 'SHSE.600000',
            'start_date': '1990-01-01',
            'end_date': '2023-12-31'
        },
        {
            'name': '已退市股票',
            'symbol': 'SHSE.600001',  # 假设的退市股票
            'start_date': '2010-01-01',
            'end_date': '2020-12-31'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']}...")
            print(f"  股票代码: {test_case['symbol']}")
            print(f"  时间范围: {test_case['start_date']} 到 {test_case['end_date']}")
            
            # 获取拆分信息
            stk_split = gm.get_stk_split(
                symbol=test_case['symbol'],
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if stk_split is not None:
                # 转换为字典列表
                split_list = []
                if hasattr(stk_split, '__iter__') and not isinstance(stk_split, str):
                    for split in stk_split:
                        split_dict = stk_split_to_dict(split)
                        if split_dict:
                            split_list.append(split_dict)
                else:
                    split_dict = stk_split_to_dict(stk_split)
                    if split_dict:
                        split_list.append(split_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'splits': split_list,
                    'count': len(split_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(split_list)} 条拆分记录")
                
                if split_list:
                    print(f"  拆分信息:")
                    for i, split in enumerate(split_list[:3]):
                        split_date = split.get('split_date')
                        split_from = split.get('split_from')
                        split_to = split.get('split_to')
                        split_type = split.get('split_type')
                        split_reason = split.get('split_reason')
                        
                        print(f"    记录 {i+1}:")
                        if split_date:
                            print(f"      拆分日期: {split_date}")
                        if split_from is not None and split_to is not None:
                            print(f"      拆分方案: {split_from} 拆 {split_to}")
                        if split_type:
                            print(f"      拆分类型: {split_type}")
                        if split_reason:
                            print(f"      拆分原因: {split_reason}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'splits': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无拆分数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'symbol': test_case['symbol'],
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'splits': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_stk_split_data(results):
    """分析拆分数据结构"""
    print("\n=== 拆分数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_split_records = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_split_records
        
        if isinstance(data, dict):
            if 'splits' in data:
                splits = data['splits']
                if isinstance(splits, list):
                    total_split_records += len(splits)
                    for split in splits:
                        if isinstance(split, dict):
                            for field in split.keys():
                                all_fields.add(field)
                                field_counts[field] = field_counts.get(field, 0) + 1
            else:
                # 递归处理嵌套字典
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        collect_fields_from_results(value)
        elif isinstance(data, list):
            for item in data:
                collect_fields_from_results(item)
    
    # 分析所有结果
    for result_set in results:
        collect_fields_from_results(result_set)
    
    if all_fields:
        print(f"发现的拆分字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的拆分字段")
    
    print(f"\n总拆分记录数: {total_split_records}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_split_records': total_split_records
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_stk_split()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_stk_split function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平拆分数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'splits' in data:
                    # 这是一个包含splits的结果
                    base_info = {k: v for k, v in data.items() if k != 'splits'}
                    splits = data['splits']
                    
                    if isinstance(splits, list):
                        for i, split in enumerate(splits):
                            flat_result = base_info.copy()
                            flat_result['split_index'] = i
                            if isinstance(split, dict):
                                for key, value in split.items():
                                    flat_result[f'split_{key}'] = value
                            flattened_results.append(flat_result)
                    elif splits:
                        flat_result = base_info.copy()
                        if isinstance(splits, dict):
                            for key, value in splits.items():
                                flat_result[f'split_{key}'] = value
                        flattened_results.append(flat_result)
                    else:
                        flattened_results.append(base_info)
                else:
                    # 递归处理嵌套字典
                    for key, value in data.items():
                        if isinstance(value, (dict, list)):
                            flatten_results(value, f"{prefix}{key}_")
            elif isinstance(data, list):
                for item in data:
                    flatten_results(item, prefix)
        
        # 展平所有结果
        for result_set in results:
            flatten_results(result_set)
        
        if flattened_results:
            csv_filename = f"{filename_prefix}_results_{timestamp}.csv"
            df = pd.DataFrame(flattened_results)
            df.to_csv(csv_filename, encoding='utf-8-sig', index=False)
            print(f"结果已保存到: {csv_filename}")
            
    except Exception as e:
        print(f"保存CSV文件失败: {e}")

def main():
    """主函数"""
    print("GM API get_stk_split() 功能测试")
    print("=" * 60)
    
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
        all_results = []
        
        # 测试1: 主要股票的拆分信息查询
        major_results = test_get_stk_split_major_stocks()
        save_results(major_results, 'get_stk_split_major')
        all_results.append(major_results)
        
        # 测试2: 不同时间段的拆分信息查询
        period_results = test_get_stk_split_different_periods()
        save_results(period_results, 'get_stk_split_periods')
        all_results.append(period_results)
        
        # 测试3: 单日拆分信息查询
        single_date_results = test_get_stk_split_single_date()
        save_results(single_date_results, 'get_stk_split_single_date')
        all_results.append(single_date_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_stk_split_edge_cases()
        save_results(edge_results, 'get_stk_split_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_stk_split_data(all_results)
        
        # 汇总统计
        print("\n=== 测试汇总 ===")
        
        # 统计各测试结果
        def count_success_and_data(results):
            success_count = 0
            total_count = 0
            data_count = 0
            
            def count_recursive(data):
                nonlocal success_count, total_count, data_count
                
                if isinstance(data, dict):
                    if 'success' in data and 'count' in data:
                        total_count += 1
                        if data['success']:
                            success_count += 1
                        data_count += data.get('count', 0)
                    else:
                        for value in data.values():
                            if isinstance(value, (dict, list)):
                                count_recursive(value)
                elif isinstance(data, list):
                    for item in data:
                        count_recursive(item)
            
            count_recursive(results)
            return success_count, total_count, data_count
        
        major_success, major_total, major_data = count_success_and_data(major_results)
        print(f"主要股票测试: {major_success}/{major_total} 成功, {major_data} 条拆分记录")
        
        period_success, period_total, period_data = count_success_and_data(period_results)
        print(f"不同时间段测试: {period_success}/{period_total} 成功, {period_data} 条拆分记录")
        
        single_success, single_total, single_data = count_success_and_data(single_date_results)
        print(f"单日查询测试: {single_success}/{single_total} 成功, {single_data} 条拆分记录")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 条拆分记录")
        
        # 总体统计
        total_tests = major_total + period_total + single_total + edge_total
        total_success = major_success + period_success + single_success + edge_success
        total_data_count = major_data + period_data + single_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总拆分记录数: {total_data_count}")
        
        # 数据结构统计
        print(f"\n拆分数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_stk_split() API测试完成！")

if __name__ == "__main__":
    main()