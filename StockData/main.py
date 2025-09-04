#!/usr/bin/env python3
"""
股票数据同步系统主入口
整合所有功能模块，提供统一的命令行界面
"""
import asyncio
import logging
import signal
import sys
from typing import Optional, List
from datetime import datetime

# 导入项目模块
from src.config import settings
from src.services import GMService
from src.database import mongodb_client
from src.scheduler import SchedulerService, DataSyncService


class StockDataApp:
    """股票数据同步系统主应用"""
    
    def __init__(self):
        """初始化应用"""
        self.logger = logging.getLogger(__name__)
        self.gm_service = GMService()
        self.scheduler_service = SchedulerService()
        self.data_sync_service = DataSyncService()
        self.running = False
    
    def setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=getattr(logging, settings.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/stock_data_app.log', encoding='utf-8')
            ]
        )
        self.logger.info("日志系统初始化完成")
    
    async def initialize(self) -> bool:
        """
        初始化应用组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("开始初始化应用组件...")
            
            # 验证配置
            if not settings.validate():
                self.logger.error("配置验证失败")
                return False
            
            # 连接数据库
            connected = await mongodb_client.connect()
            if not connected:
                self.logger.error("数据库连接失败")
                return False
            
            # 测试掘金量化连接
            if not self.gm_service.test_connection():
                self.logger.warning("掘金量化API连接失败，但应用将继续启动")
                # 不返回False，允许应用继续启动
            
            self.logger.info("应用组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            return False
    
    async def start_scheduler(self):
        """启动调度系统"""
        try:
            self.logger.info("启动调度系统...")
            await self.scheduler_service.start_scheduler()
            self.running = True
            self.logger.info("调度系统启动成功")
        except Exception as e:
            self.logger.error(f"启动调度系统失败: {e}")
            raise
    
    def stop_scheduler(self):
        """停止调度系统"""
        if self.running:
            self.logger.info("停止调度系统...")
            self.scheduler_service.stop_scheduler()
            self.running = False
            self.logger.info("调度系统已停止")
    
    async def test_api_connection(self):
        """测试API连接"""
        print("\n" + "="*60)
        print("测试掘金量化API连接")
        print("="*60)
        
        try:
            # 测试连接
            if self.gm_service.test_connection():
                print("✅ 掘金量化API连接正常")
                
                # 获取测试数据
                if settings.is_all_symbols_mode():
                    test_symbol = 'SZSE.000001'  # 使用默认测试股票
                else:
                    test_symbol = settings.test_symbols[0]
                current_data = self.gm_service.get_current_data(symbols=test_symbol)
                
                if current_data:
                    tick = current_data[0]
                    print(f"✅ 成功获取 {test_symbol} 实时数据:")
                    print(f"   最新价: {tick.price}")
                    print(f"   成交量: {tick.cum_volume:,}")
                    print(f"   成交额: {tick.cum_amount:,.2f}")
                else:
                    print("⚠️  未获取到实时数据")
            else:
                print("❌ 掘金量化API连接失败")
                
        except Exception as e:
            print(f"❌ API连接测试失败: {e}")
    
    async def test_database_connection(self):
        """测试数据库连接"""
        print("\n" + "="*60)
        print("测试MongoDB数据库连接")
        print("="*60)
        
        try:
            # 健康检查
            if await mongodb_client.health_check():
                print("✅ MongoDB数据库连接正常")
                
                # 获取数据统计
                statistics = await mongodb_client.get_frequency_statistics()
                
                print("📊 数据库统计信息:")
                for freq, stats in statistics.items():
                    count = stats.get('count', 0)
                    latest_time = stats.get('latest_time')
                    if latest_time:
                        print(f"   {freq}: {count:,} 条 (最新: {latest_time})")
                    else:
                        print(f"   {freq}: {count:,} 条")
            else:
                print("❌ MongoDB数据库连接失败")
                
        except Exception as e:
            print(f"❌ 数据库连接测试失败: {e}")
    
    async def manual_sync_data(self):
        """手动同步数据"""
        print("\n" + "="*60)
        print("手动数据同步")
        print("="*60)
        
        try:
            # 获取要同步的股票列表
            if settings.is_all_symbols_mode():
                print("全部股票模式：从数据库获取所有A股列表...")
                from src.database import mongodb_client
                symbols = await mongodb_client.get_all_stock_symbols()
                if not symbols:
                    print("❌ 未获取到股票列表，请先同步标的基本信息")
                    return
                print(f"获取到 {len(symbols)} 个股票，开始同步...")
            else:
                symbols = settings.test_symbols
                print(f"指定股票模式：同步 {len(symbols)} 个股票")
                print(f"同步股票: {', '.join(symbols)}")
            
            # 同步所有频率数据
            print("开始同步所有频率数据...")
            results = await self.data_sync_service.sync_all_frequencies(symbols)
            
            print("同步结果:")
            for frequency, freq_results in results.items():
                success_count = sum(1 for success in freq_results.values() if success)
                total_count = len(freq_results)
                print(f"   {frequency}: {success_count}/{total_count} 成功")
            
            # 同步实时数据
            print("\n开始同步实时数据...")
            realtime_results = await self.data_sync_service.sync_realtime_data(symbols)
            success_count = sum(1 for success in realtime_results.values() if success)
            total_count = len(realtime_results)
            print(f"   实时数据: {success_count}/{total_count} 成功")
            
        except Exception as e:
            print(f"❌ 手动同步失败: {e}")
    
    async def query_data(self):
        """查询数据"""
        print("\n" + "="*60)
        print("数据查询")
        print("="*60)
        
        try:
            # 获取数据统计
            statistics = await mongodb_client.get_frequency_statistics()
            
            print("📊 数据统计:")
            for freq, stats in statistics.items():
                count = stats.get('count', 0)
                latest_time = stats.get('latest_time')
                latest_symbol = stats.get('latest_symbol')
                
                if latest_time and latest_symbol:
                    print(f"   {freq}: {count:,} 条 (最新: {latest_symbol} - {latest_time})")
                else:
                    print(f"   {freq}: {count:,} 条")
            
            # 查询最近的同步日志
            print("\n📋 最近同步记录:")
            sync_history = await mongodb_client.get_sync_history(limit=10)
            
            if sync_history:
                print(f"{'股票代码':<15} {'操作类型':<12} {'状态':<8} {'记录数':<8} {'时间':<20}")
                print("-" * 80)
                
                for record in sync_history:
                    print(f"{record['symbol']:<15} {record['operation_type']:<12} "
                          f"{record['status']:<8} {record['record_count']:<8} "
                          f"{record['sync_time'].strftime('%m-%d %H:%M:%S'):<20}")
            else:
                print("   暂无同步记录")
                
        except Exception as e:
            print(f"❌ 数据查询失败: {e}")
    
    async def query_symbol_infos(self):
        """查询标的基本信息"""
        print("\n" + "="*60)
        print("标的基本信息查询")
        print("="*60)
        
        try:
            # 显示查询选项
            print("请选择查询类型:")
            print("1. 查询A股股票")
            print("2. 查询ETF基金")
            print("3. 查询可转债")
            print("4. 查询股指期货")
            print("5. 查询指定标的")
            print("6. 返回主菜单")
            
            choice = input("请输入选择 (1-6): ").strip()
            
            if choice == '1':
                # 查询A股
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                await self._query_stock_symbols(sec_type2=101001, exchanges=exchanges)
                
            elif choice == '2':
                # 查询ETF
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                await self._query_fund_symbols(sec_type2=102001, exchanges=exchanges)
                
            elif choice == '3':
                # 查询可转债
                exchanges = input("请输入交易所 (SHSE/SZSE，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                await self._query_bond_symbols(sec_type2=103001, exchanges=exchanges)
                
            elif choice == '4':
                # 查询股指期货
                exchanges = input("请输入交易所 (CFFEX，留空表示全部): ").strip()
                exchanges = exchanges if exchanges else None
                await self._query_future_symbols(sec_type2=104001, exchanges=exchanges)
                
            elif choice == '5':
                # 查询指定标的
                symbols = input("请输入标的代码 (如: SHSE.600008,SZSE.000002): ").strip()
                if symbols:
                    await self._query_specific_symbols(symbols)
                else:
                    print("请输入有效的标的代码")
                    
            elif choice == '6':
                return
            else:
                print("❌ 无效选择")
                
        except Exception as e:
            print(f"❌ 查询标的基本信息失败: {e}")
    
    async def _query_stock_symbols(self, sec_type2: int = None, exchanges: str = None):
        """查询股票标的基本信息"""
        try:
            symbol_infos = self.gm_service.get_symbol_infos(
                sec_type1=1010,
                sec_type2=sec_type2,
                exchanges=exchanges
            )
            
            if symbol_infos:
                print(f"\n找到 {len(symbol_infos)} 个股票标的:")
                print("=" * 100)
                print(f"{'标的代码':<15} {'证券名称':<20} {'交易所':<8} {'证券代码':<10} {'上市日期':<12}")
                print("=" * 100)
                
                for info in symbol_infos[:20]:  # 只显示前20个
                    symbol = info.get('symbol', 'N/A')
                    sec_name = info.get('sec_name', 'N/A')
                    exchange = info.get('exchange', 'N/A')
                    sec_id = info.get('sec_id', 'N/A')
                    listed_date = info.get('listed_date')
                    
                    if listed_date and hasattr(listed_date, 'strftime'):
                        listed_str = listed_date.strftime('%Y-%m-%d')
                    else:
                        listed_str = str(listed_date) if listed_date else 'N/A'
                    
                    print(f"{symbol:<15} {sec_name:<20} {exchange:<8} {sec_id:<10} {listed_str:<12}")
                
                if len(symbol_infos) > 20:
                    print(f"... 还有 {len(symbol_infos) - 20} 个标的")
                    
            else:
                print("未找到符合条件的股票标的")
                
        except Exception as e:
            print(f"查询股票标的信息失败: {e}")
    
    async def _query_fund_symbols(self, sec_type2: int = None, exchanges: str = None):
        """查询基金标的基本信息"""
        try:
            symbol_infos = self.gm_service.get_symbol_infos(
                sec_type1=1020,
                sec_type2=sec_type2,
                exchanges=exchanges
            )
            
            if symbol_infos:
                print(f"\n找到 {len(symbol_infos)} 个基金标的:")
                print("=" * 100)
                print(f"{'标的代码':<15} {'基金名称':<20} {'交易所':<8} {'基金代码':<10} {'上市日期':<12}")
                print("=" * 100)
                
                for info in symbol_infos[:20]:  # 只显示前20个
                    symbol = info.get('symbol', 'N/A')
                    sec_name = info.get('sec_name', 'N/A')
                    exchange = info.get('exchange', 'N/A')
                    sec_id = info.get('sec_id', 'N/A')
                    listed_date = info.get('listed_date')
                    
                    if listed_date and hasattr(listed_date, 'strftime'):
                        listed_str = listed_date.strftime('%Y-%m-%d')
                    else:
                        listed_str = str(listed_date) if listed_date else 'N/A'
                    
                    print(f"{symbol:<15} {sec_name:<20} {exchange:<8} {sec_id:<10} {listed_str:<12}")
                
                if len(symbol_infos) > 20:
                    print(f"... 还有 {len(symbol_infos) - 20} 个标的")
                    
            else:
                print("未找到符合条件的基金标的")
                
        except Exception as e:
            print(f"查询基金标的信息失败: {e}")
    
    async def _query_bond_symbols(self, sec_type2: int = None, exchanges: str = None):
        """查询债券标的基本信息"""
        try:
            symbol_infos = self.gm_service.get_symbol_infos(
                sec_type1=1030,
                sec_type2=sec_type2,
                exchanges=exchanges
            )
            
            if symbol_infos:
                print(f"\n找到 {len(symbol_infos)} 个债券标的:")
                print("=" * 100)
                print(f"{'标的代码':<15} {'债券名称':<20} {'交易所':<8} {'债券代码':<10} {'上市日期':<12}")
                print("=" * 100)
                
                for info in symbol_infos[:20]:  # 只显示前20个
                    symbol = info.get('symbol', 'N/A')
                    sec_name = info.get('sec_name', 'N/A')
                    exchange = info.get('exchange', 'N/A')
                    sec_id = info.get('sec_id', 'N/A')
                    listed_date = info.get('listed_date')
                    
                    if listed_date and hasattr(listed_date, 'strftime'):
                        listed_str = listed_date.strftime('%Y-%m-%d')
                    else:
                        listed_str = str(listed_date) if listed_date else 'N/A'
                    
                    print(f"{symbol:<15} {sec_name:<20} {exchange:<8} {sec_id:<10} {listed_str:<12}")
                
                if len(symbol_infos) > 20:
                    print(f"... 还有 {len(symbol_infos) - 20} 个标的")
                    
            else:
                print("未找到符合条件的债券标的")
                
        except Exception as e:
            print(f"查询债券标的信息失败: {e}")
    
    async def _query_future_symbols(self, sec_type2: int = None, exchanges: str = None):
        """查询期货标的基本信息"""
        try:
            symbol_infos = self.gm_service.get_symbol_infos(
                sec_type1=1040,
                sec_type2=sec_type2,
                exchanges=exchanges
            )
            
            if symbol_infos:
                print(f"\n找到 {len(symbol_infos)} 个期货标的:")
                print("=" * 100)
                print(f"{'标的代码':<15} {'期货名称':<20} {'交易所':<8} {'合约代码':<10} {'挂牌日期':<12}")
                print("=" * 100)
                
                for info in symbol_infos[:20]:  # 只显示前20个
                    symbol = info.get('symbol', 'N/A')
                    sec_name = info.get('sec_name', 'N/A')
                    exchange = info.get('exchange', 'N/A')
                    sec_id = info.get('sec_id', 'N/A')
                    listed_date = info.get('listed_date')
                    
                    if listed_date and hasattr(listed_date, 'strftime'):
                        listed_str = listed_date.strftime('%Y-%m-%d')
                    else:
                        listed_str = str(listed_date) if listed_date else 'N/A'
                    
                    print(f"{symbol:<15} {sec_name:<20} {exchange:<8} {sec_id:<10} {listed_str:<12}")
                
                if len(symbol_infos) > 20:
                    print(f"... 还有 {len(symbol_infos) - 20} 个标的")
                    
            else:
                print("未找到符合条件的期货标的")
                
        except Exception as e:
            print(f"查询期货标的信息失败: {e}")
    
    async def _query_specific_symbols(self, symbols: str):
        """查询指定标的基本信息"""
        try:
            # 先尝试查询股票
            symbol_infos = self.gm_service.get_symbol_infos(
                sec_type1=1010,
                symbols=symbols
            )
            
            if symbol_infos:
                print("股票信息:")
                for info in symbol_infos:
                    print(f"标的代码: {info.get('symbol', 'N/A')}")
                    print(f"证券名称: {info.get('sec_name', 'N/A')}")
                    print(f"交易所: {info.get('exchange', 'N/A')}")
                    print(f"证券代码: {info.get('sec_id', 'N/A')}")
                    print(f"最小变动单位: {info.get('price_tick', 'N/A')}")
                    print(f"交易制度: {info.get('trade_n', 'N/A')} (0=T+0, 1=T+1, 2=T+2)")
                    
                    listed_date = info.get('listed_date')
                    if listed_date and hasattr(listed_date, 'strftime'):
                        print(f"上市日期: {listed_date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"上市日期: {listed_date}")
                    
                    print("-" * 50)
            else:
                print("未找到指定标的的信息")
                
        except Exception as e:
            print(f"查询指定标的信息失败: {e}")
    
    async def manual_sync_symbol_infos(self):
        """手动同步标的基本信息"""
        print("\n" + "="*50)
        print("手动同步标的基本信息")
        print("="*50)
        
        try:
            print("选择同步类型:")
            print("1. 同步所有类型标的基本信息")
            print("2. 只同步股票标的基本信息")
            print("3. 只同步基金标的基本信息")
            print("4. 只同步债券标的基本信息")
            print("5. 只同步期货标的基本信息")
            print("6. 只同步期权标的基本信息")
            print("7. 只同步指数标的基本信息")
            
            choice = input("请选择 (1-7): ").strip()
            
            if choice == '1':
                print("开始同步所有类型标的基本信息...")
                success = await self.scheduler_service.sync_symbol_infos_manual(sync_all_types=True)
                if success:
                    print("✅ 所有类型标的基本信息同步完成")
                else:
                    print("❌ 所有类型标的基本信息同步失败")
            elif choice == '2':
                print("开始同步股票标的基本信息...")
                success = await self.scheduler_service.sync_symbol_infos_manual(sync_all_types=False)
                if success:
                    print("✅ 股票标的基本信息同步完成")
                else:
                    print("❌ 股票标的基本信息同步失败")
            elif choice == '3':
                print("开始同步基金标的基本信息...")
                success = await self.scheduler_service.symbol_sync_service.sync_fund_symbols()
                if success:
                    print("✅ 基金标的基本信息同步完成")
                else:
                    print("❌ 基金标的基本信息同步失败")
            elif choice == '4':
                print("开始同步债券标的基本信息...")
                success = await self.scheduler_service.symbol_sync_service.sync_bond_symbols()
                if success:
                    print("✅ 债券标的基本信息同步完成")
                else:
                    print("❌ 债券标的基本信息同步失败")
            elif choice == '5':
                print("开始同步期货标的基本信息...")
                success = await self.scheduler_service.symbol_sync_service.sync_future_symbols()
                if success:
                    print("✅ 期货标的基本信息同步完成")
                else:
                    print("❌ 期货标的基本信息同步失败")
            elif choice == '6':
                print("开始同步期权标的基本信息...")
                success = await self.scheduler_service.symbol_sync_service.sync_option_symbols()
                if success:
                    print("✅ 期权标的基本信息同步完成")
                else:
                    print("❌ 期权标的基本信息同步失败")
            elif choice == '7':
                print("开始同步指数标的基本信息...")
                success = await self.scheduler_service.symbol_sync_service.sync_index_symbols()
                if success:
                    print("✅ 指数标的基本信息同步完成")
                else:
                    print("❌ 指数标的基本信息同步失败")
            else:
                print("❌ 无效选择")
                
        except Exception as e:
            print(f"❌ 手动同步标的基本信息失败: {e}")
    
    async def get_system_status(self):
        """获取系统状态"""
        print("\n" + "="*60)
        print("系统状态")
        print("="*60)
        
        try:
            # 调度器状态
            job_status = self.scheduler_service.get_job_status()
            print(f"调度器运行状态: {'运行中' if job_status.get('scheduler_running') else '已停止'}")
            print(f"注册任务数量: {job_status.get('job_count', 0)}")
            
            # 同步状态
            sync_status = await self.data_sync_service.get_sync_status()
            print(f"实时同步状态: {'运行中' if sync_status.get('is_running') else '已停止'}")
            print(f"交易时间状态: {'是' if sync_status.get('is_trading_time') else '否'}")
            
            # 数据库状态
            db_healthy = await mongodb_client.health_check()
            print(f"数据库状态: {'正常' if db_healthy else '异常'}")
            
            # 配置信息
            print(f"\n配置信息:")
            if settings.is_all_symbols_mode():
                print(f"  监控模式: 全部股票模式")
                print(f"  股票数量: 从数据库动态获取")
            else:
                print(f"  监控模式: 指定股票模式")
                print(f"  监控股票: {', '.join(settings.test_symbols)}")
            print(f"  同步间隔: {settings.sync_interval_minutes} 分钟")
            print(f"  实时间隔: {settings.realtime_interval_seconds} 秒")
            print(f"  启用频率: {', '.join(settings.enabled_frequencies)}")
            
        except Exception as e:
            print(f"❌ 获取系统状态失败: {e}")
    
    async def run_interactive_mode(self):
        """运行交互模式"""
        while True:
            print("\n" + "="*60)
            print("股票数据同步系统 - 主菜单")
            print("="*60)
            print("1. 测试API连接")
            print("2. 测试数据库连接")
            print("3. 手动同步数据")
            print("4. 查询数据统计")
            print("5. 查询标的基本信息")
            print("6. 手动同步标的基本信息")
            print("7. 查看系统状态")
            print("8. 启动调度系统")
            print("9. 停止调度系统")
            print("10. 退出程序")
            print("="*60)
            
            try:
                choice = input("请选择操作 (1-10): ").strip()
                
                if choice == '1':
                    await self.test_api_connection()
                elif choice == '2':
                    await self.test_database_connection()
                elif choice == '3':
                    await self.manual_sync_data()
                elif choice == '4':
                    await self.query_data()
                elif choice == '5':
                    await self.query_symbol_infos()
                elif choice == '6':
                    await self.manual_sync_symbol_infos()
                elif choice == '7':
                    await self.get_system_status()
                elif choice == '8':
                    if not self.running:
                        await self.start_scheduler()
                        print("✅ 调度系统已启动")
                    else:
                        print("⚠️  调度系统已在运行中")
                elif choice == '9':
                    if self.running:
                        self.stop_scheduler()
                        print("✅ 调度系统已停止")
                    else:
                        print("⚠️  调度系统未运行")
                elif choice == '10':
                    print("退出程序...")
                    break
                else:
                    print("❌ 无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n用户中断，退出程序...")
                break
            except Exception as e:
                print(f"❌ 操作失败: {e}")
                self.logger.error(f"操作失败: {e}")
    
    async def run_scheduler_mode(self):
        """运行调度模式"""
        try:
            print("\n" + "="*60)
            print("启动调度模式")
            print("="*60)
            
            # 启动调度系统
            await self.start_scheduler()
            
            # 打印状态信息
            if settings.is_all_symbols_mode():
                print(f"监控模式: 全部股票模式")
                print(f"股票数量: 从数据库动态获取")
            else:
                print(f"监控模式: 指定股票模式")
                print(f"监控股票: {', '.join(settings.test_symbols)}")
            print(f"同步间隔: {settings.sync_interval_minutes} 分钟")
            print(f"实时间隔: {settings.realtime_interval_seconds} 秒")
            print(f"历史同步时间: {settings.history_sync_time}")
            print(f"交易时间: 上午 {settings.trading_morning_start}-{settings.trading_morning_end}, 下午 {settings.trading_afternoon_start}-{settings.trading_afternoon_end}")
            print(f"MongoDB数据库: {settings.mongodb_database}")
            print("="*60)
            print("调度系统正在运行，按 Ctrl+C 停止")
            print("="*60)
            
            # 保持运行
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n收到停止信号，正在关闭...")
        finally:
            self.stop_scheduler()
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("开始清理资源...")
            
            # 停止调度系统
            self.stop_scheduler()
            
            # 断开数据库连接
            await mongodb_client.disconnect()
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")


def signal_handler(signum, frame):
    """信号处理器"""
    print("\n收到停止信号，正在关闭...")
    sys.exit(0)


async def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建应用实例
    app = StockDataApp()
    
    try:
        # 设置日志
        app.setup_logging()
        
        # 初始化应用
        if not await app.initialize():
            print("❌ 应用初始化失败!")
            return
        
        print("✅ 应用初始化成功!")
        
        # 检查命令行参数
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode == 'scheduler':
                # 调度模式
                await app.run_scheduler_mode()
            elif mode == 'test':
                # 测试模式
                await app.test_api_connection()
                await app.test_database_connection()
                await app.get_system_status()
            elif mode == 'sync':
                # 同步模式
                await app.manual_sync_data()
            elif mode == 'query':
                # 查询模式
                await app.query_data()
            elif mode == 'symbols':
                # 标的基本信息查询模式
                await app.query_symbol_infos()
            else:
                print(f"❌ 未知模式: {mode}")
                print("可用模式: scheduler, test, sync, query, symbols")
        else:
            # 交互模式
            await app.run_interactive_mode()
    
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        app.logger.error(f"程序异常: {e}")
    
    finally:
        # 清理资源
        await app.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"程序异常退出: {e}")
        logging.error(f"程序异常退出: {e}")
