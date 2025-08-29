#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_stk_shares_change() 获取股本变动信息
功能：测试 gm.get_stk_shares_change() API的各种用法
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

def stk_shares_change_to_dict(shares_change):
    """将stk_shares_change对象转换为字典格式"""
    if shares_change is None:
        return None
    
    try:
        change_dict = {}
        
        # 常见的stk_shares_change属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'change_date', 'announcement_date', 'effective_date', 'record_date',
            'change_type', 'change_reason', 'change_description',
            'pre_total_shares', 'post_total_shares', 'change_shares',
            'pre_float_shares', 'post_float_shares', 'float_change_shares',
            'pre_restricted_shares', 'post_restricted_shares', 'restricted_change_shares',
            'pre_state_shares', 'post_state_shares', 'state_change_shares',
            'pre_legal_person_shares', 'post_legal_person_shares', 'legal_person_change_shares',
            'pre_individual_shares', 'post_individual_shares', 'individual_change_shares',
            'pre_foreign_shares', 'post_foreign_shares', 'foreign_change_shares',
            'change_ratio', 'change_factor', 'price_adjustment_factor',
            'volume_adjustment_factor', 'market_cap_before', 'market_cap_after',
            'share_price_before', 'share_price_after', 'currency',
            'board_resolution_date', 'shareholder_meeting_date', 'regulatory_approval_date',
            'implementation_date', 'completion_date', 'registration_date',
            'change_method', 'change_source', 'related_announcement',
            'created_at', 'updated_at', 'data_source', 'status'
        ]
        
        for attr in attributes:
            if hasattr(shares_change, attr):
                value = getattr(shares_change, attr)
                # 处理日期时间类型
                if attr in ['change_date', 'announcement_date', 'effective_date', 'record_date',
                           'board_resolution_date', 'shareholder_meeting_date', 'regulatory_approval_date',
                           'implementation_date', 'completion_date', 'registration_date',
                           'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            change_dict[attr] = value.strftime('%Y-%m-%d')
                        else:
                            change_dict[attr] = str(value)
                    except:
                        change_dict[attr] = str(value)
                else:
                    change_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not change_dict:
            change_dict = {'raw_data': str(shares_change)}
        
        return change_dict
        
    except Exception as e:
        return {'error': f'Failed to convert stk_shares_change: {e}', 'raw_data': str(shares_change)}

def test_get_stk_shares_change_major_stocks():
    """测试主要股票的股本变动信息查询"""
    print("\n=== 测试主要股票的股本变动信息查询 ===")
    
    # 测试主要股票（选择一些可能有股本变动历史的股票）
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
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的股本变动信息...")
            print(f"  查询时间范围: {start_date} 到 {end_date}")
            
            # 获取股本变动信息
            shares_change = gm.get_stk_shares_change(
                symbol=stock_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if shares_change is not None:
                # 转换为字典列表
                change_list = []
                if hasattr(shares_change, '__iter__') and not isinstance(shares_change, str):
                    for change in shares_change:
                        change_dict = stk_shares_change_to_dict(change)
                        if change_dict:
                            change_list.append(change_dict)
                else:
                    change_dict = stk_shares_change_to_dict(shares_change)
                    if change_dict:
                        change_list.append(change_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'changes': change_list,
                    'count': len(change_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(change_list)} 条股本变动记录")
                
                # 分析股本变动信息
                if change_list:
                    print(f"  股本变动详情:")
                    total_share_change = 0
                    change_types = {}
                    
                    for i, change in enumerate(change_list[:5]):  # 显示前5条
                        change_date = change.get('change_date')
                        announcement_date = change.get('announcement_date')
                        effective_date = change.get('effective_date')
                        change_type = change.get('change_type')
                        change_reason = change.get('change_reason')
                        change_description = change.get('change_description')
                        
                        pre_total_shares = change.get('pre_total_shares')
                        post_total_shares = change.get('post_total_shares')
                        change_shares = change.get('change_shares')
                        change_ratio = change.get('change_ratio')
                        
                        pre_float_shares = change.get('pre_float_shares')
                        post_float_shares = change.get('post_float_shares')
                        float_change_shares = change.get('float_change_shares')
                        
                        print(f"    变动 {i+1}:")
                        if change_date:
                            print(f"      变动日期: {change_date}")
                        if announcement_date:
                            print(f"      公告日期: {announcement_date}")
                        if effective_date:
                            print(f"      生效日期: {effective_date}")
                        if change_type:
                            print(f"      变动类型: {change_type}")
                            change_types[change_type] = change_types.get(change_type, 0) + 1
                        if change_reason:
                            print(f"      变动原因: {change_reason}")
                        if change_description:
                            print(f"      变动描述: {change_description}")
                        
                        # 显示股本变化
                        if pre_total_shares is not None and post_total_shares is not None:
                            if isinstance(pre_total_shares, (int, float)) and isinstance(post_total_shares, (int, float)):
                                print(f"      总股本变化: {pre_total_shares:,.0f} -> {post_total_shares:,.0f}")
                                share_change = post_total_shares - pre_total_shares
                                total_share_change += share_change
                                if pre_total_shares > 0:
                                    change_pct = share_change / pre_total_shares * 100
                                    print(f"      总股本变动: {share_change:,.0f} ({change_pct:+.2f}%)")
                        
                        if change_shares is not None:
                            if isinstance(change_shares, (int, float)):
                                print(f"      变动股数: {change_shares:,.0f}")
                            else:
                                print(f"      变动股数: {change_shares}")
                        
                        if change_ratio is not None:
                            print(f"      变动比例: {change_ratio}")
                        
                        # 显示流通股变化
                        if pre_float_shares is not None and post_float_shares is not None:
                            if isinstance(pre_float_shares, (int, float)) and isinstance(post_float_shares, (int, float)):
                                print(f"      流通股变化: {pre_float_shares:,.0f} -> {post_float_shares:,.0f}")
                                if pre_float_shares > 0:
                                    float_change_pct = (post_float_shares - pre_float_shares) / pre_float_shares * 100
                                    print(f"      流通股变动: {float_change_pct:+.2f}%")
                        
                        if float_change_shares is not None:
                            if isinstance(float_change_shares, (int, float)):
                                print(f"      流通股变动数: {float_change_shares:,.0f}")
                        
                        # 显示限售股变化
                        pre_restricted = change.get('pre_restricted_shares')
                        post_restricted = change.get('post_restricted_shares')
                        restricted_change = change.get('restricted_change_shares')
                        
                        if pre_restricted is not None and post_restricted is not None:
                            if isinstance(pre_restricted, (int, float)) and isinstance(post_restricted, (int, float)):
                                print(f"      限售股变化: {pre_restricted:,.0f} -> {post_restricted:,.0f}")
                        
                        if restricted_change is not None:
                            if isinstance(restricted_change, (int, float)):
                                print(f"      限售股变动数: {restricted_change:,.0f}")
                        
                        # 显示市值变化
                        market_cap_before = change.get('market_cap_before')
                        market_cap_after = change.get('market_cap_after')
                        
                        if market_cap_before is not None and market_cap_after is not None:
                            if isinstance(market_cap_before, (int, float)) and isinstance(market_cap_after, (int, float)):
                                print(f"      市值变化: {market_cap_before:,.0f} -> {market_cap_after:,.0f}")
                                if market_cap_before > 0:
                                    market_cap_change_pct = (market_cap_after - market_cap_before) / market_cap_before * 100
                                    print(f"      市值变动: {market_cap_change_pct:+.2f}%")
                        
                        # 显示调整因子
                        price_adj_factor = change.get('price_adjustment_factor')
                        volume_adj_factor = change.get('volume_adjustment_factor')
                        
                        if price_adj_factor is not None or volume_adj_factor is not None:
                            print(f"      调整因子:")
                            if price_adj_factor is not None:
                                print(f"        价格调整: {price_adj_factor}")
                            if volume_adj_factor is not None:
                                print(f"        成交量调整: {volume_adj_factor}")
                    
                    if len(change_list) > 5:
                        print(f"    ... 还有 {len(change_list) - 5} 条股本变动记录")
                    
                    # 统计变动类型
                    if change_types:
                        print(f"  变动类型统计: {dict(change_types)}")
                    
                    # 统计变动年份
                    change_years = {}
                    for change in change_list:
                        change_date = change.get('change_date')
                        if change_date:
                            try:
                                year = change_date[:4] if isinstance(change_date, str) and len(change_date) >= 4 else '未知'
                                change_years[year] = change_years.get(year, 0) + 1
                            except:
                                change_years['未知'] = change_years.get('未知', 0) + 1
                    
                    if change_years:
                        print(f"  变动年份分布: {dict(sorted(change_years.items()))}")
                    
                    # 计算总股本变化
                    if total_share_change != 0:
                        print(f"  累计股本变动: {total_share_change:,.0f}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'changes': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无股本变动数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'changes': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_stk_shares_change_different_periods():
    """测试不同时间段的股本变动信息查询"""
    print("\n=== 测试不同时间段的股本变动信息查询 ===")
    
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
                'total_changes': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            for stock_info in test_symbols:
                try:
                    print(f"  查询 {stock_info['name']} ({stock_info['symbol']})...")
                    
                    # 获取股本变动信息
                    shares_change = gm.get_stk_shares_change(
                        symbol=stock_info['symbol'],
                        start_date=period_info['start_date'],
                        end_date=period_info['end_date']
                    )
                    
                    if shares_change is not None:
                        # 转换为字典列表
                        change_list = []
                        if hasattr(shares_change, '__iter__') and not isinstance(shares_change, str):
                            for change in shares_change:
                                change_dict = stk_shares_change_to_dict(change)
                                if change_dict:
                                    change_list.append(change_dict)
                        else:
                            change_dict = stk_shares_change_to_dict(shares_change)
                            if change_dict:
                                change_list.append(change_dict)
                        
                        stock_result = {
                            'symbol': stock_info['symbol'],
                            'name': stock_info['name'],
                            'changes': change_list,
                            'count': len(change_list),
                            'success': True,
                            'error': None
                        }
                        
                        print(f"    获取到 {len(change_list)} 条股本变动记录")
                        period_result['total_changes'] += len(change_list)
                        
                        # 显示股本变动摘要
                        if change_list:
                            for change in change_list:
                                change_date = change.get('change_date')
                                change_type = change.get('change_type')
                                change_reason = change.get('change_reason')
                                pre_total = change.get('pre_total_shares')
                                post_total = change.get('post_total_shares')
                                
                                summary_parts = []
                                if change_date:
                                    summary_parts.append(f"日期: {change_date}")
                                if change_type:
                                    summary_parts.append(f"类型: {change_type}")
                                if change_reason:
                                    summary_parts.append(f"原因: {change_reason}")
                                if isinstance(pre_total, (int, float)) and isinstance(post_total, (int, float)):
                                    summary_parts.append(f"股本: {pre_total:,.0f} -> {post_total:,.0f}")
                                
                                print(f"      {', '.join(summary_parts)}")
                        
                    else:
                        stock_result = {
                            'symbol': stock_info['symbol'],
                            'name': stock_info['name'],
                            'changes': [],
                            'count': 0,
                            'success': False,
                            'error': 'No data returned'
                        }
                        print(f"    无股本变动数据")
                    
                    period_result['stocks'].append(stock_result)
                    
                except Exception as e:
                    print(f"    查询失败: {e}")
                    period_result['stocks'].append({
                        'symbol': stock_info['symbol'],
                        'name': stock_info['name'],
                        'changes': [],
                        'count': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            print(f"  时间段总变动数: {period_result['total_changes']}")
            results.append(period_result)
            
        except Exception as e:
            print(f"  时间段查询失败: {e}")
            results.append({
                'period_name': period_info['name'],
                'start_date': period_info['start_date'],
                'end_date': period_info['end_date'],
                'stocks': [],
                'total_changes': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
    
    return results

def test_get_stk_shares_change_by_type():
    """测试按变动类型查询股本变动"""
    print("\n=== 测试按变动类型查询股本变动 ===")
    
    # 选择一些可能有不同类型股本变动的股票
    test_stocks = [
        {'symbol': 'SHSE.600000', 'name': '浦发银行'},
        {'symbol': 'SHSE.600036', 'name': '招商银行'},
        {'symbol': 'SHSE.600519', 'name': '贵州茅台'},
        {'symbol': 'SZSE.000002', 'name': '万科A'},
        {'symbol': 'SZSE.000858', 'name': '五粮液'},
        {'symbol': 'SZSE.002415', 'name': '海康威视'},
        {'symbol': 'SZSE.300059', 'name': '东方财富'},
        {'symbol': 'SZSE.300750', 'name': '宁德时代'}
    ]
    
    results = []
    
    # 查询时间范围（最近10年）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=10*365)).strftime('%Y-%m-%d')
    
    # 统计信息
    all_change_types = {}
    all_change_reasons = {}
    total_change_records = 0
    
    for stock_info in test_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的股本变动信息...")
            
            # 获取股本变动信息
            shares_change = gm.get_stk_shares_change(
                symbol=stock_info['symbol'],
                start_date=start_date,
                end_date=end_date
            )
            
            if shares_change is not None:
                # 转换为字典列表
                change_list = []
                if hasattr(shares_change, '__iter__') and not isinstance(shares_change, str):
                    for change in shares_change:
                        change_dict = stk_shares_change_to_dict(change)
                        if change_dict:
                            change_list.append(change_dict)
                else:
                    change_dict = stk_shares_change_to_dict(shares_change)
                    if change_dict:
                        change_list.append(change_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'changes': change_list,
                    'count': len(change_list),
                    'change_types': {},
                    'change_reasons': {},
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(change_list)} 条股本变动记录")
                total_change_records += len(change_list)
                
                # 分析变动类型和原因
                if change_list:
                    stock_change_types = {}
                    stock_change_reasons = {}
                    
                    for change in change_list:
                        change_type = change.get('change_type')
                        change_reason = change.get('change_reason')
                        change_date = change.get('change_date')
                        pre_total = change.get('pre_total_shares')
                        post_total = change.get('post_total_shares')
                        
                        # 统计变动类型
                        if change_type:
                            stock_change_types[change_type] = stock_change_types.get(change_type, 0) + 1
                            all_change_types[change_type] = all_change_types.get(change_type, 0) + 1
                        
                        # 统计变动原因
                        if change_reason:
                            stock_change_reasons[change_reason] = stock_change_reasons.get(change_reason, 0) + 1
                            all_change_reasons[change_reason] = all_change_reasons.get(change_reason, 0) + 1
                        
                        # 显示变动详情
                        print(f"    变动: {change_date or '未知日期'} - {change_type or '未知类型'} - {change_reason or '未知原因'}")
                        if isinstance(pre_total, (int, float)) and isinstance(post_total, (int, float)):
                            change_amount = post_total - pre_total
                            change_pct = (change_amount / pre_total * 100) if pre_total > 0 else 0
                            print(f"      股本变化: {pre_total:,.0f} -> {post_total:,.0f} ({change_amount:+,.0f}, {change_pct:+.2f}%)")
                    
                    result['change_types'] = stock_change_types
                    result['change_reasons'] = stock_change_reasons
                    
                    if stock_change_types:
                        print(f"  变动类型统计: {dict(stock_change_types)}")
                    if stock_change_reasons:
                        print(f"  变动原因统计: {dict(stock_change_reasons)}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'changes': [],
                    'count': 0,
                    'change_types': {},
                    'change_reasons': {},
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无股本变动数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'changes': [],
                'count': 0,
                'change_types': {},
                'change_reasons': {},
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    # 添加统计摘要
    summary_result = {
        'summary_type': 'change_type_statistics',
        'total_stocks': len(test_stocks),
        'total_change_records': total_change_records,
        'all_change_types': dict(sorted(all_change_types.items(), key=lambda x: x[1], reverse=True)),
        'all_change_reasons': dict(sorted(all_change_reasons.items(), key=lambda x: x[1], reverse=True)),
        'top_change_types': dict(list(sorted(all_change_types.items(), key=lambda x: x[1], reverse=True))[:10]),
        'top_change_reasons': dict(list(sorted(all_change_reasons.items(), key=lambda x: x[1], reverse=True))[:10]),
        'timestamp': datetime.now().isoformat()
    }
    
    results.append(summary_result)
    
    # 显示统计摘要
    print(f"\n=== 股本变动类型统计摘要 ===")
    print(f"测试股票数: {summary_result['total_stocks']}")
    print(f"总变动记录数: {summary_result['total_change_records']}")
    print(f"变动类型数: {len(all_change_types)}")
    print(f"变动原因数: {len(all_change_reasons)}")
    
    if summary_result['top_change_types']:
        print(f"\n前10名变动类型:")
        for i, (change_type, count) in enumerate(summary_result['top_change_types'].items()):
            print(f"  {i+1}. {change_type}: {count} 次")
    
    if summary_result['top_change_reasons']:
        print(f"\n前10名变动原因:")
        for i, (change_reason, count) in enumerate(summary_result['top_change_reasons'].items()):
            print(f"  {i+1}. {change_reason}: {count} 次")
    
    return results

def test_get_stk_shares_change_edge_cases():
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
            
            # 获取股本变动信息
            shares_change = gm.get_stk_shares_change(
                symbol=test_case['symbol'],
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            
            if shares_change is not None:
                # 转换为字典列表
                change_list = []
                if hasattr(shares_change, '__iter__') and not isinstance(shares_change, str):
                    for change in shares_change:
                        change_dict = stk_shares_change_to_dict(change)
                        if change_dict:
                            change_list.append(change_dict)
                else:
                    change_dict = stk_shares_change_to_dict(shares_change)
                    if change_dict:
                        change_list.append(change_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'changes': change_list,
                    'count': len(change_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(change_list)} 条股本变动记录")
                
                if change_list:
                    print(f"  股本变动信息:")
                    for i, change in enumerate(change_list[:3]):
                        change_date = change.get('change_date')
                        change_type = change.get('change_type')
                        change_reason = change.get('change_reason')
                        pre_total = change.get('pre_total_shares')
                        post_total = change.get('post_total_shares')
                        
                        print(f"    记录 {i+1}:")
                        if change_date:
                            print(f"      变动日期: {change_date}")
                        if change_type:
                            print(f"      变动类型: {change_type}")
                        if change_reason:
                            print(f"      变动原因: {change_reason}")
                        if isinstance(pre_total, (int, float)) and isinstance(post_total, (int, float)):
                            print(f"      股本变化: {pre_total:,.0f} -> {post_total:,.0f}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'start_date': test_case['start_date'],
                    'end_date': test_case['end_date'],
                    'changes': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无股本变动数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'symbol': test_case['symbol'],
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'changes': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_stk_shares_change_data(results):
    """分析股本变动数据结构"""
    print("\n=== 股本变动数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_change_records = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_change_records
        
        if isinstance(data, dict):
            if 'changes' in data:
                changes = data['changes']
                if isinstance(changes, list):
                    total_change_records += len(changes)
                    for change in changes:
                        if isinstance(change, dict):
                            for field in change.keys():
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
        print(f"发现的股本变动字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的股本变动字段")
    
    print(f"\n总股本变动记录数: {total_change_records}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_change_records': total_change_records
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_stk_shares_change()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_stk_shares_change function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平股本变动数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'changes' in data:
                    # 这是一个包含changes的结果
                    base_info = {k: v for k, v in data.items() if k != 'changes'}
                    changes = data['changes']
                    
                    if isinstance(changes, list):
                        for i, change in enumerate(changes):
                            flat_result = base_info.copy()
                            flat_result['change_index'] = i
                            if isinstance(change, dict):
                                for key, value in change.items():
                                    flat_result[f'change_{key}'] = value
                            flattened_results.append(flat_result)
                    elif changes:
                        flat_result = base_info.copy()
                        if isinstance(changes, dict):
                            for key, value in changes.items():
                                flat_result[f'change_{key}'] = value
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
    print("GM API get_stk_shares_change() 功能测试")
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
        
        # 测试1: 主要股票的股本变动信息查询
        major_results = test_get_stk_shares_change_major_stocks()
        save_results(major_results, 'get_stk_shares_change_major')
        all_results.append(major_results)
        
        # 测试2: 不同时间段的股本变动信息查询
        period_results = test_get_stk_shares_change_different_periods()
        save_results(period_results, 'get_stk_shares_change_periods')
        all_results.append(period_results)
        
        # 测试3: 按变动类型查询股本变动
        type_results = test_get_stk_shares_change_by_type()
        save_results(type_results, 'get_stk_shares_change_by_type')
        all_results.append(type_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_stk_shares_change_edge_cases()
        save_results(edge_results, 'get_stk_shares_change_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_stk_shares_change_data(all_results)
        
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
        print(f"主要股票测试: {major_success}/{major_total} 成功, {major_data} 条股本变动记录")
        
        period_success, period_total, period_data = count_success_and_data(period_results)
        print(f"不同时间段测试: {period_success}/{period_total} 成功, {period_data} 条股本变动记录")
        
        type_success, type_total, type_data = count_success_and_data(type_results)
        print(f"按类型测试: {type_success}/{type_total} 成功, {type_data} 条股本变动记录")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 条股本变动记录")
        
        # 总体统计
        total_tests = major_total + period_total + type_total + edge_total
        total_success = major_success + period_success + type_success + edge_success
        total_data_count = major_data + period_data + type_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总股本变动记录数: {total_data_count}")
        
        # 数据结构统计
        print(f"\n股本变动数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_stk_shares_change() API测试完成！")

if __name__ == "__main__":
    main()