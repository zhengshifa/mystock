#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_stk_bonus() 获取股票送股信息
功能：测试 gm.get_stk_bonus() API的各种用法
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

def stk_bonus_to_dict(stk_bonus):
    """将stk_bonus对象转换为字典格式"""
    if stk_bonus is None:
        return None
    
    try:
        bonus_dict = {}
        
        # 常见的stk_bonus属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'bonus_date', 'ex_date', 'record_date', 'pay_date',
            'bonus_ratio', 'bonus_shares', 'bonus_per_share',
            'announcement_date', 'board_date', 'shareholder_meeting_date',
            'effective_date', 'bonus_type', 'bonus_reason',
            'pre_bonus_shares', 'post_bonus_shares', 'bonus_factor',
            'currency', 'market_cap_before', 'market_cap_after',
            'price_adjustment_factor', 'volume_adjustment_factor',
            'total_bonus_amount', 'bonus_source', 'tax_rate',
            'created_at', 'updated_at', 'data_source', 'status'
        ]
        
        for attr in attributes:
            if hasattr(stk_bonus, attr):
                value = getattr(stk_bonus, attr)
                # 处理日期时间类型
                if attr in ['bonus_date', 'ex_date', 'record_date', 'pay_date', 
                           'announcement_date', 'board_date', 'shareholder_meeting_date', 
                           'effective_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            bonus_dict[attr] = value.strftime('%Y-%m-%d')
                        else:
                            bonus_dict[attr] = str(value)
                    except:
                        bonus_dict[attr] = str(value)
                else:
                    bonus_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not bonus_dict:
            bonus_dict = {'raw_data': str(stk_bonus)}
        
        return bonus_dict
        
    except Exception as e:
        return {'error': f'Failed to convert stk_bonus: {e}', 'raw_data': str(stk_bonus)}

def test_get_stk_bonus_major_stocks():
    """测试主要股票的送股信息查询"""
    print("\n=== 测试主要股票的送股信息查询 ===")
    
    # 测试主要股票（选择一些可能有送股历史的股票）
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
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的送股信息...")
            print(f"  查询时间范围: {start_date} 到 {end_date}")
            
            # 获取送股信息
            stk_bonus = gm.get_stk_bonus(
                symbol=stock_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if stk_bonus is not None:
                # 转换为字典列表
                bonus_list = []
                if hasattr(stk_bonus, '__iter__') and not isinstance(stk_bonus, str):
                    for bonus in stk_bonus:
                        bonus_dict = stk_bonus_to_dict(bonus)
                        if bonus_dict:
                            bonus_list.append(bonus_dict)
                else:
                    bonus_dict = stk_bonus_to_dict(stk_bonus)
                    if bonus_dict:
                        bonus_list.append(bonus_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'bonuses': bonus_list,
                    'count': len(bonus_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(bonus_list)} 条送股记录")
                
                # 分析送股信息
                if bonus_list:
                    print(f"  送股详情:")
                    total_bonus_ratio = 0
                    for i, bonus in enumerate(bonus_list[:5]):  # 显示前5条
                        bonus_date = bonus.get('bonus_date')
                        ex_date = bonus.get('ex_date')
                        record_date = bonus.get('record_date')
                        pay_date = bonus.get('pay_date')
                        bonus_ratio = bonus.get('bonus_ratio')
                        bonus_shares = bonus.get('bonus_shares')
                        bonus_per_share = bonus.get('bonus_per_share')
                        bonus_type = bonus.get('bonus_type')
                        bonus_reason = bonus.get('bonus_reason')
                        
                        print(f"    送股 {i+1}:")
                        if bonus_date:
                            print(f"      送股日期: {bonus_date}")
                        if ex_date:
                            print(f"      除权日期: {ex_date}")
                        if record_date:
                            print(f"      登记日期: {record_date}")
                        if pay_date:
                            print(f"      派发日期: {pay_date}")
                        if bonus_ratio is not None:
                            print(f"      送股比例: {bonus_ratio}")
                            if isinstance(bonus_ratio, (int, float)):
                                total_bonus_ratio += bonus_ratio
                        if bonus_shares is not None:
                            print(f"      送股数量: {bonus_shares:,}" if isinstance(bonus_shares, (int, float)) else f"      送股数量: {bonus_shares}")
                        if bonus_per_share is not None:
                            print(f"      每股送股: {bonus_per_share}")
                        if bonus_type:
                            print(f"      送股类型: {bonus_type}")
                        if bonus_reason:
                            print(f"      送股原因: {bonus_reason}")
                        
                        # 显示股本变化
                        pre_bonus_shares = bonus.get('pre_bonus_shares')
                        post_bonus_shares = bonus.get('post_bonus_shares')
                        
                        if pre_bonus_shares is not None and post_bonus_shares is not None:
                            if isinstance(pre_bonus_shares, (int, float)) and isinstance(post_bonus_shares, (int, float)):
                                print(f"      股本变化: {pre_bonus_shares:,.0f} -> {post_bonus_shares:,.0f}")
                                if pre_bonus_shares > 0:
                                    change_ratio = (post_bonus_shares - pre_bonus_shares) / pre_bonus_shares * 100
                                    print(f"      股本增长: {change_ratio:.2f}%")
                        
                        # 显示调整因子
                        price_adj_factor = bonus.get('price_adjustment_factor')
                        volume_adj_factor = bonus.get('volume_adjustment_factor')
                        
                        if price_adj_factor is not None or volume_adj_factor is not None:
                            print(f"      调整因子:")
                            if price_adj_factor is not None:
                                print(f"        价格调整: {price_adj_factor}")
                            if volume_adj_factor is not None:
                                print(f"        成交量调整: {volume_adj_factor}")
                        
                        # 显示送股金额
                        total_bonus_amount = bonus.get('total_bonus_amount')
                        if total_bonus_amount is not None:
                            if isinstance(total_bonus_amount, (int, float)):
                                print(f"      送股总额: {total_bonus_amount:,.2f}")
                            else:
                                print(f"      送股总额: {total_bonus_amount}")
                    
                    if len(bonus_list) > 5:
                        print(f"    ... 还有 {len(bonus_list) - 5} 条送股记录")
                    
                    # 统计送股类型
                    bonus_types = {}
                    for bonus in bonus_list:
                        bonus_type = bonus.get('bonus_type', '未知')
                        bonus_types[bonus_type] = bonus_types.get(bonus_type, 0) + 1
                    
                    if bonus_types:
                        print(f"  送股类型统计: {dict(bonus_types)}")
                    
                    # 统计送股年份
                    bonus_years = {}
                    for bonus in bonus_list:
                        bonus_date = bonus.get('bonus_date')
                        if bonus_date:
                            try:
                                year = bonus_date[:4] if isinstance(bonus_date, str) and len(bonus_date) >= 4 else '未知'
                                bonus_years[year] = bonus_years.get(year, 0) + 1
                            except:
                                bonus_years['未知'] = bonus_years.get('未知', 0) + 1
                    
                    if bonus_years:
                        print(f"  送股年份分布: {dict(sorted(bonus_years.items()))}")
                    
                    # 计算总送股比例
                    if total_bonus_ratio > 0:
                        print(f"  累计送股比例: {total_bonus_ratio:.4f}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'bonuses': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无送股数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'bonuses': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_stk_bonus_different_periods():
    """测试不同时间段的送股信息查询"""
    print("\n=== 测试不同时间段的送股信息查询 ===")
    
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
                'total_bonuses': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            for stock_info in test_symbols:
                try:
                    print(f"  查询 {stock_info['name']} ({stock_info['symbol']})...")
                    
                    # 获取送股信息
                    stk_bonus = gm.get_stk_bonus(
                        symbol=stock_info['symbol'],
                        start_date=period_info['start_date'],
                        end_date=period_info['end_date']
                    )
                    
                    if stk_bonus is not None:
                        # 转换为字典列表
                        bonus_list = []
                        if hasattr(stk_bonus, '__iter__') and not isinstance(stk_bonus, str):
                            for bonus in stk_bonus:
                                bonus_dict = stk_bonus_to_dict(bonus)
                                if bonus_dict:
                                    bonus_list.append(bonus_dict)
                        else:
                            bonus_dict = stk_bonus_to_dict(stk_bonus)
                            if bonus_dict:
                                bonus_list.append(bonus_dict)
                        
                        stock_result = {
                            'symbol': stock_info['symbol'],
                            'name': stock_info['name'],
                            'bonuses': bonus_list,
                            'count': len(bonus_list),
                            'success': True,
                            'error': None
                        }
                        
                        print(f"    获取到 {len(bonus_list)} 条送股记录")
                        period_result['total_bonuses'] += len(bonus_list)
                        
                        # 显示送股摘要
                        if bonus_list:
                            for bonus in bonus_list:
                                bonus_date = bonus.get('bonus_date')
                                bonus_ratio = bonus.get('bonus_ratio')
                                bonus_per_share = bonus.get('bonus_per_share')
                                bonus_type = bonus.get('bonus_type')
                                
                                summary_parts = []
                                if bonus_date:
                                    summary_parts.append(f"日期: {bonus_date}")
                                if bonus_ratio is not None:
                                    summary_parts.append(f"比例: {bonus_ratio}")
                                if bonus_per_share is not None:
                                    summary_parts.append(f"每股: {bonus_per_share}")
                                if bonus_type:
                                    summary_parts.append(f"类型: {bonus_type}")
                                
                                print(f"      {', '.join(summary_parts)}")
                        
                    else:
                        stock_result = {
                            'symbol': stock_info['symbol'],
                            'name': stock_info['name'],
                            'bonuses': [],
                            'count': 0,
                            'success': False,
                            'error': 'No data returned'
                        }
                        print(f"    无送股数据")
                    
                    period_result['stocks'].append(stock_result)
                    
                except Exception as e:
                    print(f"    查询失败: {e}")
                    period_result['stocks'].append({
                        'symbol': stock_info['symbol'],
                        'name': stock_info['name'],
                        'bonuses': [],
                        'count': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            print(f"  时间段总送股数: {period_result['total_bonuses']}")
            results.append(period_result)
            
        except Exception as e:
            print(f"  时间段查询失败: {e}")
            results.append({
                'period_name': period_info['name'],
                'start_date': period_info['start_date'],
                'end_date': period_info['end_date'],
                'stocks': [],
                'total_bonuses': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
    
    return results

def test_get_stk_bonus_high_bonus_stocks():
    """测试高送股股票查询"""
    print("\n=== 测试高送股股票查询 ===")
    
    # 选择一些可能有高送股的股票（通常是成长股或科技股）
    high_bonus_stocks = [
        {'symbol': 'SZSE.300059', 'name': '东方财富'},
        {'symbol': 'SZSE.300750', 'name': '宁德时代'},
        {'symbol': 'SZSE.002415', 'name': '海康威视'},
        {'symbol': 'SZSE.300142', 'name': '沃森生物'},
        {'symbol': 'SZSE.300033', 'name': '同花顺'},
        {'symbol': 'SHSE.688981', 'name': '中芯国际'},
        {'symbol': 'SHSE.688036', 'name': '传音控股'},
        {'symbol': 'SZSE.002594', 'name': '比亚迪'},
        {'symbol': 'SZSE.300014', 'name': '亿纬锂能'},
        {'symbol': 'SZSE.300760', 'name': '迈瑞医疗'}
    ]
    
    results = []
    
    # 查询时间范围（最近3年）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
    
    # 统计信息
    total_bonus_records = 0
    high_bonus_records = []  # 高送股记录（送股比例 > 0.5）
    
    for stock_info in high_bonus_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的送股信息...")
            
            # 获取送股信息
            stk_bonus = gm.get_stk_bonus(
                symbol=stock_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if stk_bonus is not None:
                # 转换为字典列表
                bonus_list = []
                if hasattr(stk_bonus, '__iter__') and not isinstance(stk_bonus, str):
                    for bonus in stk_bonus:
                        bonus_dict = stk_bonus_to_dict(bonus)
                        if bonus_dict:
                            bonus_list.append(bonus_dict)
                else:
                    bonus_dict = stk_bonus_to_dict(stk_bonus)
                    if bonus_dict:
                        bonus_list.append(bonus_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'bonuses': bonus_list,
                    'count': len(bonus_list),
                    'high_bonus_count': 0,
                    'max_bonus_ratio': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(bonus_list)} 条送股记录")
                total_bonus_records += len(bonus_list)
                
                # 分析高送股记录
                if bonus_list:
                    max_ratio = 0
                    high_count = 0
                    
                    for bonus in bonus_list:
                        bonus_date = bonus.get('bonus_date')
                        bonus_ratio = bonus.get('bonus_ratio')
                        bonus_per_share = bonus.get('bonus_per_share')
                        bonus_shares = bonus.get('bonus_shares')
                        
                        # 判断是否为高送股
                        is_high_bonus = False
                        if isinstance(bonus_ratio, (int, float)) and bonus_ratio > 0.5:
                            is_high_bonus = True
                            max_ratio = max(max_ratio, bonus_ratio)
                        elif isinstance(bonus_per_share, (int, float)) and bonus_per_share > 0.5:
                            is_high_bonus = True
                            max_ratio = max(max_ratio, bonus_per_share)
                        
                        if is_high_bonus:
                            high_count += 1
                            high_bonus_records.append({
                                'symbol': stock_info['symbol'],
                                'name': stock_info['name'],
                                'bonus_date': bonus_date,
                                'bonus_ratio': bonus_ratio,
                                'bonus_per_share': bonus_per_share,
                                'bonus_shares': bonus_shares
                            })
                            
                            print(f"    高送股记录: 日期 {bonus_date}, 比例 {bonus_ratio}, 每股 {bonus_per_share}")
                    
                    result['high_bonus_count'] = high_count
                    result['max_bonus_ratio'] = max_ratio
                    
                    if high_count > 0:
                        print(f"  发现 {high_count} 条高送股记录，最高比例: {max_ratio}")
                    else:
                        print(f"  未发现高送股记录")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'bonuses': [],
                    'count': 0,
                    'high_bonus_count': 0,
                    'max_bonus_ratio': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无送股数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'bonuses': [],
                'count': 0,
                'high_bonus_count': 0,
                'max_bonus_ratio': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    # 添加统计摘要
    summary_result = {
        'summary_type': 'high_bonus_statistics',
        'total_stocks': len(high_bonus_stocks),
        'total_bonus_records': total_bonus_records,
        'high_bonus_records': len(high_bonus_records),
        'high_bonus_stocks': len([r for r in results if r.get('high_bonus_count', 0) > 0]),
        'top_high_bonus_records': sorted(high_bonus_records, 
                                       key=lambda x: x.get('bonus_ratio', 0) or x.get('bonus_per_share', 0), 
                                       reverse=True)[:10],
        'timestamp': datetime.now().isoformat()
    }
    
    results.append(summary_result)
    
    # 显示统计摘要
    print(f"\n=== 高送股统计摘要 ===")
    print(f"测试股票数: {summary_result['total_stocks']}")
    print(f"总送股记录数: {summary_result['total_bonus_records']}")
    print(f"高送股记录数: {summary_result['high_bonus_records']}")
    print(f"有高送股的股票数: {summary_result['high_bonus_stocks']}")
    
    if summary_result['top_high_bonus_records']:
        print(f"\n前10名高送股记录:")
        for i, record in enumerate(summary_result['top_high_bonus_records'][:10]):
            ratio = record.get('bonus_ratio') or record.get('bonus_per_share', 0)
            print(f"  {i+1}. {record['name']} ({record['bonus_date']}): {ratio}")
    
    return results

def test_get_stk_bonus_edge_cases():
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
            
            # 获取送股信息
            stk_bonus = gm.get_stk_bonus(
                symbol=test_case['symbol'],
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if stk_bonus is not None:
                # 转换为字典列表
                bonus_list = []
                if hasattr(stk_bonus, '__iter__') and not isinstance(stk_bonus, str):
                    for bonus in stk_bonus:
                        bonus_dict = stk_bonus_to_dict(bonus)
                        if bonus_dict:
                            bonus_list.append(bonus_dict)
                else:
                    bonus_dict = stk_bonus_to_dict(stk_bonus)
                    if bonus_dict:
                        bonus_list.append(bonus_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'bonuses': bonus_list,
                    'count': len(bonus_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(bonus_list)} 条送股记录")
                
                if bonus_list:
                    print(f"  送股信息:")
                    for i, bonus in enumerate(bonus_list[:3]):
                        bonus_date = bonus.get('bonus_date')
                        bonus_ratio = bonus.get('bonus_ratio')
                        bonus_per_share = bonus.get('bonus_per_share')
                        bonus_type = bonus.get('bonus_type')
                        bonus_reason = bonus.get('bonus_reason')
                        
                        print(f"    记录 {i+1}:")
                        if bonus_date:
                            print(f"      送股日期: {bonus_date}")
                        if bonus_ratio is not None:
                            print(f"      送股比例: {bonus_ratio}")
                        if bonus_per_share is not None:
                            print(f"      每股送股: {bonus_per_share}")
                        if bonus_type:
                            print(f"      送股类型: {bonus_type}")
                        if bonus_reason:
                            print(f"      送股原因: {bonus_reason}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'bonuses': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无送股数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'symbol': test_case['symbol'],
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'bonuses': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_stk_bonus_data(results):
    """分析送股数据结构"""
    print("\n=== 送股数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_bonus_records = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_bonus_records
        
        if isinstance(data, dict):
            if 'bonuses' in data:
                bonuses = data['bonuses']
                if isinstance(bonuses, list):
                    total_bonus_records += len(bonuses)
                    for bonus in bonuses:
                        if isinstance(bonus, dict):
                            for field in bonus.keys():
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
        print(f"发现的送股字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的送股字段")
    
    print(f"\n总送股记录数: {total_bonus_records}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_bonus_records': total_bonus_records
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_stk_bonus()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_stk_bonus function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平送股数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'bonuses' in data:
                    # 这是一个包含bonuses的结果
                    base_info = {k: v for k, v in data.items() if k != 'bonuses'}
                    bonuses = data['bonuses']
                    
                    if isinstance(bonuses, list):
                        for i, bonus in enumerate(bonuses):
                            flat_result = base_info.copy()
                            flat_result['bonus_index'] = i
                            if isinstance(bonus, dict):
                                for key, value in bonus.items():
                                    flat_result[f'bonus_{key}'] = value
                            flattened_results.append(flat_result)
                    elif bonuses:
                        flat_result = base_info.copy()
                        if isinstance(bonuses, dict):
                            for key, value in bonuses.items():
                                flat_result[f'bonus_{key}'] = value
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
    print("GM API get_stk_bonus() 功能测试")
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
        
        # 测试1: 主要股票的送股信息查询
        major_results = test_get_stk_bonus_major_stocks()
        save_results(major_results, 'get_stk_bonus_major')
        all_results.append(major_results)
        
        # 测试2: 不同时间段的送股信息查询
        period_results = test_get_stk_bonus_different_periods()
        save_results(period_results, 'get_stk_bonus_periods')
        all_results.append(period_results)
        
        # 测试3: 高送股股票查询
        high_bonus_results = test_get_stk_bonus_high_bonus_stocks()
        save_results(high_bonus_results, 'get_stk_bonus_high_bonus')
        all_results.append(high_bonus_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_stk_bonus_edge_cases()
        save_results(edge_results, 'get_stk_bonus_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_stk_bonus_data(all_results)
        
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
        print(f"主要股票测试: {major_success}/{major_total} 成功, {major_data} 条送股记录")
        
        period_success, period_total, period_data = count_success_and_data(period_results)
        print(f"不同时间段测试: {period_success}/{period_total} 成功, {period_data} 条送股记录")
        
        high_success, high_total, high_data = count_success_and_data(high_bonus_results)
        print(f"高送股测试: {high_success}/{high_total} 成功, {high_data} 条送股记录")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 条送股记录")
        
        # 总体统计
        total_tests = major_total + period_total + high_total + edge_total
        total_success = major_success + period_success + high_success + edge_success
        total_data_count = major_data + period_data + high_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总送股记录数: {total_data_count}")
        
        # 数据结构统计
        print(f"\n送股数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_stk_bonus() API测试完成！")

if __name__ == "__main__":
    main()