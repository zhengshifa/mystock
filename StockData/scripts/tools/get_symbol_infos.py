#!/usr/bin/env python3
"""
标的基本信息查询脚本
基于掘金量化API的get_symbol_infos接口查询标的基本信息
"""
import asyncio
import logging
import sys
from typing import List, Dict, Optional, Union
from datetime import datetime
import pandas as pd

# 添加项目根目录到Python路径
import os
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services import GMService
from src.config import settings
from src.database import mongodb_client
from src.models.symbol_info import SymbolInfo


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def print_symbol_info(symbol_info: Dict):
    """
    打印单个标的基本信息
    
    Args:
        symbol_info: 标的基本信息字典
    """
    print(f"标的代码: {symbol_info.get('symbol', 'N/A')}")
    print(f"证券名称: {symbol_info.get('sec_name', 'N/A')}")
    print(f"证券简称: {symbol_info.get('sec_abbr', 'N/A')}")
    print(f"交易所: {symbol_info.get('exchange', 'N/A')}")
    print(f"证券代码: {symbol_info.get('sec_id', 'N/A')}")
    print(f"证券大类: {symbol_info.get('sec_type1', 'N/A')}")
    print(f"证券细类: {symbol_info.get('sec_type2', 'N/A')}")
    print(f"板块: {symbol_info.get('board', 'N/A')}")
    print(f"最小变动单位: {symbol_info.get('price_tick', 'N/A')}")
    print(f"交易制度: {symbol_info.get('trade_n', 'N/A')} (0=T+0, 1=T+1, 2=T+2)")
    
    # 处理日期字段
    listed_date = symbol_info.get('listed_date')
    if listed_date:
        if isinstance(listed_date, datetime):
            print(f"上市日期: {listed_date.strftime('%Y-%m-%d')}")
        else:
            print(f"上市日期: {listed_date}")
    else:
        print("上市日期: N/A")
    
    delisted_date = symbol_info.get('delisted_date')
    if delisted_date:
        if isinstance(delisted_date, datetime):
            print(f"退市日期: {delisted_date.strftime('%Y-%m-%d')}")
        else:
            print(f"退市日期: {delisted_date}")
    else:
        print("退市日期: N/A")
    
    # 期货/期权特有字段
    underlying_symbol = symbol_info.get('underlying_symbol')
    if underlying_symbol:
        print(f"标的资产: {underlying_symbol}")
    
    option_type = symbol_info.get('option_type')
    if option_type:
        print(f"行权方式: {option_type} (E=欧式, A=美式)")
    
    call_or_put = symbol_info.get('call_or_put')
    if call_or_put:
        print(f"合约类型: {call_or_put} (C=Call, P=Put)")
    
    # 可转债特有字段
    conversion_start_date = symbol_info.get('conversion_start_date')
    if conversion_start_date:
        if isinstance(conversion_start_date, datetime):
            print(f"转股开始日期: {conversion_start_date.strftime('%Y-%m-%d')}")
        else:
            print(f"转股开始日期: {conversion_start_date}")
    
    print("-" * 60)


def print_symbol_info_table(symbol_infos: List[Dict]):
    """
    以表格形式打印标的基本信息
    
    Args:
        symbol_infos: 标的基本信息列表
    """
    if not symbol_infos:
        print("未找到标的基本信息")
        return
    
    print(f"\n找到 {len(symbol_infos)} 个标的:")
    print("=" * 120)
    print(f"{'标的代码':<15} {'证券名称':<20} {'交易所':<8} {'证券代码':<10} {'证券大类':<8} {'证券细类':<10} {'上市日期':<12}")
    print("=" * 120)
    
    for info in symbol_infos:
        symbol = info.get('symbol', 'N/A')
        sec_name = info.get('sec_name', 'N/A')
        exchange = info.get('exchange', 'N/A')
        sec_id = info.get('sec_id', 'N/A')
        sec_type1 = info.get('sec_type1', 'N/A')
        sec_type2 = info.get('sec_type2', 'N/A')
        
        listed_date = info.get('listed_date')
        if listed_date and isinstance(listed_date, datetime):
            listed_str = listed_date.strftime('%Y-%m-%d')
        else:
            listed_str = str(listed_date) if listed_date else 'N/A'
        
        print(f"{symbol:<15} {sec_name:<20} {exchange:<8} {sec_id:<10} {sec_type1:<8} {sec_type2:<10} {listed_str:<12}")
    
    print("=" * 120)


def get_sec_type_name(sec_type1: int, sec_type2: Optional[int] = None) -> str:
    """
    获取证券类型名称
    
    Args:
        sec_type1: 证券大类
        sec_type2: 证券细类
        
    Returns:
        str: 证券类型名称
    """
    type1_names = {
        1010: "股票",
        1020: "基金", 
        1030: "债券",
        1040: "期货",
        1050: "期权",
        1060: "指数",
        1070: "板块"
    }
    
    type2_names = {
        # 股票
        101001: "A股",
        101002: "B股", 
        101003: "存托凭证",
        # 基金
        102001: "ETF",
        102002: "LOF",
        102005: "FOF",
        102009: "基础设施REITs",
        # 债券
        103001: "可转债",
        103003: "国债",
        103006: "企业债",
        103008: "回购",
        # 期货
        104001: "股指期货",
        104003: "商品期货",
        104006: "国债期货",
        # 期权
        105001: "股票期权",
        105002: "指数期权",
        105003: "商品期权",
        # 指数
        106001: "股票指数",
        106002: "基金指数",
        106003: "债券指数",
        106004: "期货指数",
        # 板块
        107001: "概念板块"
    }
    
    type1_name = type1_names.get(sec_type1, f"未知类型({sec_type1})")
    if sec_type2:
        type2_name = type2_names.get(sec_type2, f"未知细类({sec_type2})")
        return f"{type1_name} - {type2_name}"
    else:
        return type1_name


def query_stock_symbols(gm_service: GMService, sec_type2: Optional[int] = None, exchanges: Optional[str] = None, symbols: Optional[str] = None):
    """查询股票标的基本信息"""
    print(f"\n查询股票标的基本信息...")
    print(f"证券细类: {get_sec_type_name(1010, sec_type2)}")
    if exchanges:
        print(f"交易所: {exchanges}")
    if symbols:
        print(f"指定标的: {symbols}")
    
    try:
        symbol_infos = gm_service.get_symbol_infos(
            sec_type1=1010,
            sec_type2=sec_type2,
            exchanges=exchanges,
            symbols=symbols
        )
        
        if symbol_infos:
            print_symbol_info_table(symbol_infos)
        else:
            print("未找到符合条件的股票标的")
            
    except Exception as e:
        print(f"查询股票标的信息失败: {e}")


def query_fund_symbols(gm_service: GMService, sec_type2: Optional[int] = None, exchanges: Optional[str] = None, symbols: Optional[str] = None):
    """查询基金标的基本信息"""
    print(f"\n查询基金标的基本信息...")
    print(f"证券细类: {get_sec_type_name(1020, sec_type2)}")
    if exchanges:
        print(f"交易所: {exchanges}")
    if symbols:
        print(f"指定标的: {symbols}")
    
    try:
        symbol_infos = gm_service.get_symbol_infos(
            sec_type1=1020,
            sec_type2=sec_type2,
            exchanges=exchanges,
            symbols=symbols
        )
        
        if symbol_infos:
            print_symbol_info_table(symbol_infos)
        else:
            print("未找到符合条件的基金标的")
            
    except Exception as e:
        print(f"查询基金标的信息失败: {e}")


def query_bond_symbols(gm_service: GMService, sec_type2: Optional[int] = None, exchanges: Optional[str] = None, symbols: Optional[str] = None):
    """查询债券标的基本信息"""
    print(f"\n查询债券标的基本信息...")
    print(f"证券细类: {get_sec_type_name(1030, sec_type2)}")
    if exchanges:
        print(f"交易所: {exchanges}")
    if symbols:
        print(f"指定标的: {symbols}")
    
    try:
        symbol_infos = gm_service.get_symbol_infos(
            sec_type1=1030,
            sec_type2=sec_type2,
            exchanges=exchanges,
            symbols=symbols
        )
        
        if symbol_infos:
            print_symbol_info_table(symbol_infos)
        else:
            print("未找到符合条件的债券标的")
            
    except Exception as e:
        print(f"查询债券标的信息失败: {e}")


def query_future_symbols(gm_service: GMService, sec_type2: Optional[int] = None, exchanges: Optional[str] = None, symbols: Optional[str] = None):
    """查询期货标的基本信息"""
    print(f"\n查询期货标的基本信息...")
    print(f"证券细类: {get_sec_type_name(1040, sec_type2)}")
    if exchanges:
        print(f"交易所: {exchanges}")
    if symbols:
        print(f"指定标的: {symbols}")
    
    try:
        symbol_infos = gm_service.get_symbol_infos(
            sec_type1=1040,
            sec_type2=sec_type2,
            exchanges=exchanges,
            symbols=symbols
        )
        
        if symbol_infos:
            print_symbol_info_table(symbol_infos)
        else:
            print("未找到符合条件的期货标的")
            
    except Exception as e:
        print(f"查询期货标的信息失败: {e}")


def query_option_symbols(gm_service: GMService, sec_type2: Optional[int] = None, exchanges: Optional[str] = None, symbols: Optional[str] = None):
    """查询期权标的基本信息"""
    print(f"\n查询期权标的基本信息...")
    print(f"证券细类: {get_sec_type_name(1050, sec_type2)}")
    if exchanges:
        print(f"交易所: {exchanges}")
    if symbols:
        print(f"指定标的: {symbols}")
    
    try:
        symbol_infos = gm_service.get_symbol_infos(
            sec_type1=1050,
            sec_type2=sec_type2,
            exchanges=exchanges,
            symbols=symbols
        )
        
        if symbol_infos:
            print_symbol_info_table(symbol_infos)
        else:
            print("未找到符合条件的期权标的")
            
    except Exception as e:
        print(f"查询期权标的信息失败: {e}")


def query_index_symbols(gm_service: GMService, sec_type2: Optional[int] = None, exchanges: Optional[str] = None, symbols: Optional[str] = None):
    """查询指数标的基本信息"""
    print(f"\n查询指数标的基本信息...")
    print(f"证券细类: {get_sec_type_name(1060, sec_type2)}")
    if exchanges:
        print(f"交易所: {exchanges}")
    if symbols:
        print(f"指定标的: {symbols}")
    
    try:
        symbol_infos = gm_service.get_symbol_infos(
            sec_type1=1060,
            sec_type2=sec_type2,
            exchanges=exchanges,
            symbols=symbols
        )
        
        if symbol_infos:
            print_symbol_info_table(symbol_infos)
        else:
            print("未找到符合条件的指数标的")
            
    except Exception as e:
        print(f"查询指数标的信息失败: {e}")


def query_specific_symbols(gm_service: GMService, symbols: str):
    """查询指定标的基本信息"""
    print(f"\n查询指定标的基本信息: {symbols}")
    
    try:
        # 先尝试查询股票
        symbol_infos = gm_service.get_symbol_infos(
            sec_type1=1010,
            symbols=symbols
        )
        
        if symbol_infos:
            print("股票信息:")
            print_symbol_info_table(symbol_infos)
        else:
            print("未找到股票信息，尝试查询其他类型...")
            
            # 尝试查询基金
            symbol_infos = gm_service.get_symbol_infos(
                sec_type1=1020,
                symbols=symbols
            )
            
            if symbol_infos:
                print("基金信息:")
                print_symbol_info_table(symbol_infos)
            else:
                print("未找到指定标的的信息")
            
    except Exception as e:
        print(f"查询指定标的信息失败: {e}")


def export_to_csv(symbol_infos: List[Dict], filename: str):
    """
    导出标的基本信息到CSV文件
    
    Args:
        symbol_infos: 标的基本信息列表
        filename: 输出文件名
    """
    try:
        df = pd.DataFrame(symbol_infos)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ 数据已导出到: {filename}")
    except Exception as e:
        print(f"❌ 导出CSV失败: {e}")


async def save_to_database(symbol_infos: List[Dict]) -> bool:
    """
    保存标的基本信息到数据库
    
    Args:
        symbol_infos: 标的基本信息列表
        
    Returns:
        bool: 保存是否成功
    """
    try:
        if not symbol_infos:
            print("没有数据需要保存")
            return True
        
        # 转换为SymbolInfo对象
        symbol_info_objects = []
        for info in symbol_infos:
            try:
                symbol_info = SymbolInfo.from_dict(info)
                symbol_info_objects.append(symbol_info.to_mongo_dict())
            except Exception as e:
                print(f"⚠️  转换标的 {info.get('symbol', 'Unknown')} 数据失败: {e}")
                continue
        
        if not symbol_info_objects:
            print("❌ 没有有效的数据可以保存")
            return False
        
        # 保存到数据库
        success = await mongodb_client.save_symbol_infos(symbol_info_objects)
        
        if success:
            print(f"✅ 成功保存 {len(symbol_info_objects)} 条标的基本信息到数据库")
        else:
            print("❌ 保存到数据库失败")
        
        return success
        
    except Exception as e:
        print(f"❌ 保存到数据库失败: {e}")
        return False


async def query_from_database(sec_type1: Optional[int] = None, 
                            sec_type2: Optional[int] = None,
                            exchange: Optional[str] = None,
                            limit: int = 100) -> List[Dict]:
    """
    从数据库查询标的基本信息
    
    Args:
        sec_type1: 证券品种大类
        sec_type2: 证券品种细类
        exchange: 交易所代码
        limit: 限制数量
        
    Returns:
        List[Dict]: 标的基本信息列表
    """
    try:
        results = await mongodb_client.get_symbol_infos(
            sec_type1=sec_type1,
            sec_type2=sec_type2,
            exchange=exchange,
            limit=limit
        )
        
        if results:
            print(f"✅ 从数据库查询到 {len(results)} 条标的基本信息")
        else:
            print("📭 数据库中没有找到符合条件的标的基本信息")
        
        return results
        
    except Exception as e:
        print(f"❌ 从数据库查询失败: {e}")
        return []


async def show_database_statistics():
    """显示数据库统计信息"""
    try:
        stats = await mongodb_client.get_symbol_info_statistics()
        
        if not stats:
            print("❌ 获取数据库统计信息失败")
            return
        
        print("\n📊 数据库统计信息:")
        print("=" * 50)
        print(f"总数量: {stats.get('total_count', 0):,} 条")
        
        # 按证券大类统计
        type1_stats = stats.get('type1_statistics', [])
        if type1_stats:
            print("\n按证券大类统计:")
            for stat in type1_stats:
                sec_type1 = stat.get('sec_type1', 0)
                count = stat.get('count', 0)
                type_name = get_sec_type_name(sec_type1)
                print(f"  {type_name}: {count:,} 条")
        
        # 按交易所统计
        exchange_stats = stats.get('exchange_statistics', [])
        if exchange_stats:
            print("\n按交易所统计:")
            for stat in exchange_stats:
                exchange = stat.get('exchange', 'Unknown')
                count = stat.get('count', 0)
                print(f"  {exchange}: {count:,} 条")
        
        # 最新更新时间
        latest_update = stats.get('latest_update')
        latest_symbol = stats.get('latest_symbol')
        if latest_update and latest_symbol:
            print(f"\n最新更新: {latest_symbol} - {latest_update.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 获取数据库统计信息失败: {e}")


async def main():
    """主函数"""
    print("标的基本信息查询工具")
    print("=" * 60)
    
    # 设置日志
    setup_logging()
    
    # 创建GM服务实例
    gm_service = GMService()
    
    try:
        # 测试连接
        if not gm_service.test_connection():
            print("❌ 掘金量化API连接失败")
            return
        
        print("✅ 掘金量化API连接成功")
        
        # 连接数据库
        connected = await mongodb_client.connect()
        if not connected:
            print("❌ 数据库连接失败，将无法使用数据库功能")
        else:
            print("✅ 数据库连接成功")
        
        while True:
            print("\n" + "=" * 60)
            print("请选择操作类型:")
            print("📊 API查询:")
            print("1. 查询股票 (A股)")
            print("2. 查询股票 (B股)")
            print("3. 查询股票 (存托凭证)")
            print("4. 查询基金 (ETF)")
            print("5. 查询基金 (LOF)")
            print("6. 查询债券 (可转债)")
            print("7. 查询期货 (股指期货)")
            print("8. 查询期货 (商品期货)")
            print("9. 查询期权 (股票期权)")
            print("10. 查询指数 (股票指数)")
            print("11. 查询指定标的")
            print("12. 自定义查询")
            print("💾 数据库操作:")
            print("13. 从数据库查询")
            print("14. 数据库统计")
            print("15. 退出")
            print("=" * 60)
            
            choice = input("请输入选择 (1-15): ").strip()
            
            if choice == '1':
                # 查询A股
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1010,
                    sec_type2=101001,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    
                    # 询问是否保存到数据库
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的股票标的")
                
            elif choice == '2':
                # 查询B股
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1010,
                    sec_type2=101002,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的股票标的")
                
            elif choice == '3':
                # 查询存托凭证
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1010,
                    sec_type2=101003,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的股票标的")
                
            elif choice == '4':
                # 查询ETF
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1020,
                    sec_type2=102001,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的基金标的")
                
            elif choice == '5':
                # 查询LOF
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1020,
                    sec_type2=102002,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的基金标的")
                
            elif choice == '6':
                # 查询可转债
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1030,
                    sec_type2=103001,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的债券标的")
                
            elif choice == '7':
                # 查询股指期货
                exchanges = input("请输入交易所 (CFFEX，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1040,
                    sec_type2=104001,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的期货标的")
                
            elif choice == '8':
                # 查询商品期货
                exchanges = input("请输入交易所 (SHFE/DCE/CZCE/INE/GFEX，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1040,
                    sec_type2=104003,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的期货标的")
                
            elif choice == '9':
                # 查询股票期权
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1050,
                    sec_type2=105001,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的期权标的")
                
            elif choice == '10':
                # 查询股票指数
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                symbol_infos = gm_service.get_symbol_infos(
                    sec_type1=1060,
                    sec_type2=106001,
                    exchanges=exchanges
                )
                if symbol_infos:
                    print_symbol_info_table(symbol_infos)
                    if connected:
                        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            await save_to_database(symbol_infos)
                else:
                    print("未找到符合条件的指数标的")
                
            elif choice == '11':
                # 查询指定标的
                symbols = input("请输入标的代码 (如: SHSE.600008,SZSE.000002): ").strip()
                if symbols:
                    symbol_infos = gm_service.get_symbol_infos(
                        sec_type1=1010,
                        symbols=symbols
                    )
                    if symbol_infos:
                        print_symbol_info_table(symbol_infos)
                        if connected:
                            save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                            if save_choice == 'y':
                                await save_to_database(symbol_infos)
                    else:
                        print("未找到指定标的的信息")
                else:
                    print("请输入有效的标的代码")
                    
            elif choice == '12':
                # 自定义查询
                print("\n自定义查询参数:")
                sec_type1 = input("证券大类 (1010=股票, 1020=基金, 1030=债券, 1040=期货, 1050=期权, 1060=指数): ").strip()
                sec_type2 = input("证券细类 (可选，留空表示不限制): ").strip()
                exchanges = input("交易所 (可选，多个用逗号分隔): ").strip()
                symbols = input("标的代码 (可选，多个用逗号分隔): ").strip()
                
                try:
                    sec_type1 = int(sec_type1) if sec_type1 else 1010
                    sec_type2 = int(sec_type2) if sec_type2 else None
                    exchanges = exchanges if exchanges else None
                    symbols = symbols if symbols else None
                    
                    print(f"\n查询参数: sec_type1={sec_type1}, sec_type2={sec_type2}, exchanges={exchanges}, symbols={symbols}")
                    
                    symbol_infos = gm_service.get_symbol_infos(
                        sec_type1=sec_type1,
                        sec_type2=sec_type2,
                        exchanges=exchanges,
                        symbols=symbols
                    )
                    
                    if symbol_infos:
                        print_symbol_info_table(symbol_infos)
                        
                        # 询问是否保存到数据库
                        if connected:
                            save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                            if save_choice == 'y':
                                await save_to_database(symbol_infos)
                        
                        # 询问是否导出
                        export = input("\n是否导出到CSV文件? (y/n): ").strip().lower()
                        if export == 'y':
                            filename = input("请输入文件名 (默认: symbol_infos.csv): ").strip()
                            filename = filename if filename else "symbol_infos.csv"
                            export_to_csv(symbol_infos, filename)
                    else:
                        print("未找到符合条件的标的")
                        
                except ValueError:
                    print("❌ 参数格式错误，请输入有效的数字")
                    
            elif choice == '13':
                # 从数据库查询
                if not connected:
                    print("❌ 数据库未连接，无法查询")
                    continue
                
                print("\n从数据库查询标的基本信息:")
                sec_type1 = input("证券大类 (1010=股票, 1020=基金, 1030=债券, 1040=期货, 1050=期权, 1060=指数，留空表示全部): ").strip()
                sec_type2 = input("证券细类 (可选，留空表示不限制): ").strip()
                exchange = input("交易所 (可选，留空表示全部): ").strip()
                limit = input("限制数量 (默认: 100): ").strip()
                
                try:
                    sec_type1 = int(sec_type1) if sec_type1 else None
                    sec_type2 = int(sec_type2) if sec_type2 else None
                    exchange = exchange if exchange else None
                    limit = int(limit) if limit.isdigit() else 100
                    
                    symbol_infos = await query_from_database(
                        sec_type1=sec_type1,
                        sec_type2=sec_type2,
                        exchange=exchange,
                        limit=limit
                    )
                    
                    if symbol_infos:
                        print_symbol_info_table(symbol_infos)
                        
                        # 询问是否导出
                        export = input("\n是否导出到CSV文件? (y/n): ").strip().lower()
                        if export == 'y':
                            filename = input("请输入文件名 (默认: db_symbol_infos.csv): ").strip()
                            filename = filename if filename else "db_symbol_infos.csv"
                            export_to_csv(symbol_infos, filename)
                    
                except ValueError:
                    print("❌ 参数格式错误，请输入有效的数字")
                    
            elif choice == '14':
                # 数据库统计
                if not connected:
                    print("❌ 数据库未连接，无法获取统计信息")
                    continue
                
                await show_database_statistics()
                    
            elif choice == '15':
                print("退出程序")
                break
                
            else:
                print("❌ 无效选择，请重新输入")
    
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"❌ 程序异常: {e}")
    finally:
        # 断开数据库连接
        if connected:
            try:
                await mongodb_client.disconnect()
                print("✅ 数据库连接已断开")
            except Exception as e:
                print(f"⚠️ 断开数据库连接时出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())
