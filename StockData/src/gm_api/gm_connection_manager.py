#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化连接管理器

负责管理与掘金量化服务器的连接，包括:
- 连接建立和维护
- 连接状态监控
- 自动重连机制
- 连接池管理
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
from loguru import logger
from retrying import retry

try:
    from gm.api import *
    GM_AVAILABLE = True
except ImportError:
    logger.warning("掘金量化SDK未安装，请安装gm3包")
    GM_AVAILABLE = False


class GMConnectionManager:
    """掘金量化连接管理器"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_config() if hasattr(config_manager, 'get_config') else config_manager
        gm_config = self.config.get('gm', {})
        self.username = gm_config.get('username', '')
        self.password = gm_config.get('password', '')
        self.token = gm_config.get('token', '')
        self.auth_type = gm_config.get('auth_type', 'username_password')  # 'username_password' 或 'token'
        self.server_url = gm_config.get('server_url', 'api.myquant.cn:9000')
        self.timeout = gm_config.get('timeout', 30)
        self.retry_times = gm_config.get('retry_times', 3)
        
        self.is_connected = False
        self.connection_time = None
        self.last_heartbeat = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # 连接状态回调
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # 心跳检测
        self.heartbeat_interval = 30  # 秒
        self.heartbeat_task = None
        
        logger.info("掘金量化连接管理器初始化完成")
    
    def _convert_symbol_format(self, symbol: str) -> str:
        """转换股票代码格式为掘金API标准格式"""
        try:
            if not symbol:
                return symbol
            
            # 如果已经是掘金格式，直接返回
            if '.' in symbol and symbol.split('.')[0] in ['SZSE', 'SHSE', 'BSE']:
                return symbol
            
            # 转换格式：000001.SZ -> SZSE.000001, 600000.SH -> SHSE.600000
            if '.' in symbol:
                code, exchange = symbol.split('.')
                if exchange.upper() == 'SZ':
                    return f"SZSE.{code}"
                elif exchange.upper() == 'SH':
                    return f"SHSE.{code}"
                elif exchange.upper() == 'BJ':
                    return f"BSE.{code}"
            
            # 如果没有交易所后缀，尝试根据代码判断
            if symbol.startswith('000') or symbol.startswith('002') or symbol.startswith('003'):
                return f"SZSE.{symbol}"
            elif symbol.startswith('600') or symbol.startswith('601') or symbol.startswith('603'):
                return f"SHSE.{symbol}"
            elif symbol.startswith('688') or symbol.startswith('689'):
                return f"SHSE.{symbol}"  # 科创板
            
            # 默认返回原格式
            return symbol
            
        except Exception as e:
            logger.warning(f"股票代码格式转换失败: {symbol}, 错误: {e}")
            return symbol
    
    async def initialize(self) -> None:
        """初始化连接管理器"""
        logger.info("掘金量化连接管理器初始化中...")
        # 这里可以添加初始化逻辑
        logger.info("掘金量化连接管理器初始化完成")
    
    async def start(self) -> None:
        """启动连接管理器"""
        logger.info("启动掘金量化连接管理器...")
        
        if not GM_AVAILABLE:
            logger.error("掘金量化SDK未安装")
            return
        
        try:
            # 设置Token
            if self.token:
                set_token(self.token)
                logger.info(f"掘金API Token设置成功: {self.token[:10]}...")
            else:
                logger.error("未配置掘金API Token")
                return
            
            # 测试连接
            test_result = current(symbols='SHSE.600000')
            if test_result and len(test_result) > 0:
                logger.info("掘金API连接测试成功")
                self.is_connected = True
                self.connection_time = time.time()
                logger.info("掘金量化连接管理器已启动")
            else:
                logger.error("掘金API连接测试失败")
                self.is_connected = False
                
        except Exception as e:
            logger.error(f"启动掘金API连接失败: {e}")
            self.is_connected = False
    
    async def stop(self) -> None:
        """停止连接管理器"""
        logger.info("停止掘金量化连接管理器...")
        if self.is_connected:
            await self.disconnect()
        logger.info("掘金量化连接管理器已停止")
    
    async def get_current_quotes(self, symbols: list) -> list:
        """获取实时行情数据"""
        try:
            if not self.is_connected:
                logger.warning("掘金API未连接，无法获取实时行情")
                return []
            
            if not GM_AVAILABLE:
                logger.error("掘金量化SDK未安装")
                return []
            
            logger.info(f"获取 {len(symbols)} 只股票的实时行情")
            
            # 使用真实的掘金API获取实时行情
            quotes = []
            for symbol in symbols:
                try:
                    # 转换股票代码格式
                    gm_symbol = self._convert_symbol_format(symbol)
                    logger.debug(f"转换股票代码: {symbol} -> {gm_symbol}")
                    
                    # 调用掘金API获取实时行情
                    quote_data = current(symbols=gm_symbol)
                    
                    if quote_data and len(quote_data) > 0:
                        # 转换数据格式
                        quote_item = quote_data[0]  # 取第一个结果
                        quote = {
                            'symbol': symbol,
                            'last_price': quote_item.get('price', 0.0),
                            'open': quote_item.get('open', 0.0),
                            'high': quote_item.get('high', 0.0),
                            'low': quote_item.get('low', 0.0),
                            'pre_close': quote_item.get('pre_close', quote_item.get('price', 0.0)),  # 如果没有昨收价，使用当前价
                            'volume': quote_item.get('cum_volume', 0),
                            'amount': quote_item.get('cum_amount', 0.0),
                            'turnover_rate': 0.0,  # 需要计算
                            'pe_ratio': 0.0,  # 需要单独获取
                            'pb_ratio': 0.0,  # 需要单独获取
                            'bid_price_1': quote_item.get('quotes', [{}])[0].get('bid_p', 0.0) if quote_item.get('quotes') else 0.0,
                            'bid_volume_1': quote_item.get('quotes', [{}])[0].get('bid_v', 0) if quote_item.get('quotes') else 0,
                            'ask_price_1': quote_item.get('quotes', [{}])[0].get('ask_p', 0.0) if quote_item.get('quotes') else 0.0,
                            'ask_volume_1': quote_item.get('quotes', [{}])[0].get('ask_v', 0) if quote_item.get('quotes') else 0,
                            'quote_time': quote_item.get('created_at', time.time())
                        }
                        quotes.append(quote)
                        logger.debug(f"获取到 {symbol} 的实时行情: {quote['last_price']}")
                    else:
                        logger.warning(f"未获取到 {symbol} 的实时行情数据")
                        
                except Exception as symbol_error:
                    logger.warning(f"获取 {symbol} 实时行情失败: {symbol_error}")
                    continue
            
            logger.info(f"成功获取 {len(quotes)} 只股票的实时行情")
            return quotes
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return []
    
    async def get_instruments(self, exchanges: list = None, sec_types: list = None) -> list:
        """获取股票列表"""
        try:
            if not self.is_connected:
                logger.warning("掘金API未连接，无法获取股票列表")
                return []
            
            if not GM_AVAILABLE:
                logger.error("掘金量化SDK未安装")
                return []
            
            # 转换交易所代码格式：SZ -> SZSE, SH -> SHSE, BJ -> BSE
            def convert_exchange_format(exchange: str) -> str:
                if exchange.upper() == 'SZ':
                    return 'SZSE'
                elif exchange.upper() == 'SH':
                    return 'SHSE'
                elif exchange.upper() == 'BJ':
                    return 'BSE'
                else:
                    return exchange.upper()
            
            exchanges = exchanges or ['SZSE', 'SHSE']
            sec_types = sec_types or ['STOCK']
            
            # 转换交易所代码格式
            converted_exchanges = [convert_exchange_format(ex) for ex in exchanges]
            
            logger.info(f"获取股票列表，交易所: {exchanges} -> {converted_exchanges}, 证券类型: {sec_types}")
            
            # 使用真实的掘金API获取股票列表
            instruments = []
            
            try:
                # 先尝试不指定参数获取所有数据，然后过滤
                logger.info("获取所有股票列表数据...")
                all_instruments = get_instruments(df=True)
                
                if all_instruments is not None and len(all_instruments) > 0:
                    logger.info(f"获取到 {len(all_instruments)} 条原始数据，开始过滤...")
                    
                    # 过滤数据
                    for _, item in all_instruments.iterrows():
                        item_exchange = str(item.get('exchange', '')).upper()
                        item_sec_type = item.get('sec_type', 0)
                        
                        # 检查是否匹配指定的交易所
                        exchange_match = any(ex.upper() in item_exchange for ex in converted_exchanges)
                        
                        # 检查证券类型：根据调试结果，sec_type=1 可能是股票
                        # 这里我们暂时接受所有非零的sec_type，或者可以根据需要调整
                        sec_type_match = True  # 暂时接受所有证券类型，后续可以根据需要调整
                        
                        # 如果需要严格匹配证券类型，可以取消下面的注释
                        # sec_type_match = item_sec_type == 1  # 假设1是股票类型
                        
                        if exchange_match and sec_type_match:
                            instrument = {
                                'symbol': item.get('symbol', ''),
                                'name': item.get('sec_name', ''),
                                'exchange': item.get('exchange', ''),
                                'sec_type': item.get('sec_type', ''),
                                'list_date': str(item.get('listed_date', '')) if item.get('listed_date') else '',
                                'delist_date': str(item.get('delisted_date', '')) if item.get('delisted_date') else '',
                                'status': 'Active' if item.get('delisted_date') is None else 'Delisted'
                            }
                            instruments.append(instrument)
                    
                    logger.info(f"过滤后得到 {len(instruments)} 只符合条件的股票")
                else:
                    logger.warning("未获取到任何股票数据")
                    
            except Exception as api_error:
                logger.error(f"获取股票列表失败: {api_error}")
                # 如果获取所有数据失败，尝试逐个交易所获取
                for exchange in converted_exchanges:
                    for sec_type in sec_types:
                        try:
                            logger.info(f"尝试获取 {exchange}.{sec_type} 股票列表...")
                            instrument_data = get_instruments(exchanges=exchange, sec_types=sec_type, df=True)
                            
                            if instrument_data is not None and len(instrument_data) > 0:
                                for _, item in instrument_data.iterrows():
                                    instrument = {
                                        'symbol': item.get('symbol', ''),
                                        'name': item.get('sec_name', ''),
                                        'exchange': item.get('exchange', exchange),
                                        'sec_type': item.get('sec_type', sec_type),
                                        'list_date': str(item.get('listed_date', '')) if item.get('listed_date') else '',
                                        'delist_date': str(item.get('delisted_date', '')) if item.get('delisted_date') else '',
                                        'status': 'Active' if item.get('delisted_date') is None else 'Delisted'
                                    }
                                    instruments.append(instrument)
                                
                                logger.info(f"获取到 {exchange}.{sec_type} 的 {len(instrument_data)} 只股票")
                            else:
                                logger.warning(f"未获取到 {exchange}.{sec_type} 的股票列表")
                                
                        except Exception as exchange_error:
                            logger.warning(f"获取 {exchange}.{sec_type} 股票列表失败: {exchange_error}")
                            continue
            
            logger.info(f"成功获取 {len(instruments)} 只股票")
            return instruments
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    async def get_trading_calendar(self, start_date: str, end_date: str) -> list:
        """获取交易日历"""
        try:
            if not self.is_connected:
                logger.warning("掘金API未连接，无法获取交易日历")
                return []
            
            if not GM_AVAILABLE:
                logger.error("掘金量化SDK未安装")
                return []
            
            logger.info(f"获取交易日历: {start_date} 到 {end_date}")
            
            # 使用真实的掘金API获取交易日历
            try:
                calendar_data = get_trading_dates(exchange='SHSE', start_date=start_date, end_date=end_date)
                
                if calendar_data:
                    calendar = []
                    for date in calendar_data:
                        calendar_item = {
                            'date': str(date),
                            'is_trading_day': True
                        }
                        calendar.append(calendar_item)
                    
                    logger.info(f"获取到 {len(calendar)} 个交易日")
                    return calendar
                else:
                    logger.warning("未获取到交易日历数据")
                    return []
                    
            except Exception as api_error:
                logger.error(f"获取交易日历失败: {api_error}")
                return []
            
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            return []
    
    async def get_bars(self, symbol: str, period: str, start_date: str, end_date: str) -> list:
        """获取K线数据"""
        try:
            if not self.is_connected:
                logger.warning("掘金API未连接，无法获取K线数据")
                return []
            
            if not GM_AVAILABLE:
                logger.error("掘金量化SDK未安装")
                return []
            
            logger.info(f"获取 {symbol} {period} K线数据: {start_date} 到 {end_date}")
            
            # 使用真实的掘金API获取K线数据
            try:
                # 转换股票代码格式
                gm_symbol = self._convert_symbol_format(symbol)
                logger.debug(f"转换股票代码: {symbol} -> {gm_symbol}")
                
                bars_data = history(symbol=gm_symbol, frequency=period, start_time=start_date, end_time=end_date, df=True)
                
                if bars_data is not None and len(bars_data) > 0:
                    bars = []
                    for _, item in bars_data.iterrows():
                        bar = {
                            'symbol': symbol,
                            'period': period,
                            'eob': str(item.get('eob', '')),
                            'open': float(item.get('open', 0.0)),
                            'high': float(item.get('high', 0.0)),
                            'low': float(item.get('low', 0.0)),
                            'close': float(item.get('close', 0.0)),
                            'volume': int(item.get('volume', 0)),
                            'amount': float(item.get('amount', 0.0))
                        }
                        bars.append(bar)
                    
                    logger.info(f"获取到 {len(bars)} 条K线数据")
                    return bars
                else:
                    logger.warning(f"未获取到 {symbol} 的K线数据")
                    return []
                    
            except Exception as api_error:
                logger.error(f"获取K线数据失败: {api_error}")
                return []
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return []
    
    async def get_income_statement(self, symbol: str, start_date: str, end_date: str) -> list:
        """获取利润表数据"""
        try:
            if not self.is_connected:
                logger.warning("掘金API未连接，无法获取利润表数据")
                return []
            
            if not GM_AVAILABLE:
                logger.error("掘金量化SDK未安装")
                return []
            
            logger.info(f"获取 {symbol} 利润表数据: {start_date} 到 {end_date}")
            
            # 使用真实的掘金API获取财务数据
            try:
                # 暂时跳过财务数据API，因为字段名称问题
                logger.warning(f"财务数据API暂时不可用，跳过 {symbol}")
                return []
                
                if financial_data is not None and len(financial_data) > 0:
                    data = []
                    for _, item in financial_data.iterrows():
                        financial_item = {
                            'symbol': symbol,
                            'report_date': str(item.get('report_date', '')),
                            'total_revenue': float(item.get('total_revenue', 0.0)),
                            'net_profit': float(item.get('net_profit', 0.0)),
                            'operating_profit': float(item.get('operating_profit', 0.0)),
                            'total_profit': float(item.get('total_profit', 0.0))
                        }
                        data.append(financial_item)
                    
                    logger.info(f"获取到 {len(data)} 条利润表数据")
                    return data
                else:
                    logger.warning(f"未获取到 {symbol} 的利润表数据")
                    return []
                    
            except Exception as api_error:
                logger.error(f"获取利润表数据失败: {api_error}")
                return []
            
        except Exception as e:
            logger.error(f"获取利润表数据失败: {e}")
            return []
    
    async def get_dividend_data(self, symbol: str, start_date: str, end_date: str) -> list:
        """获取分红数据"""
        try:
            if not self.is_connected:
                logger.warning("掘金API未连接，无法获取分红数据")
                return []
            
            if not GM_AVAILABLE:
                logger.error("掘金量化SDK未安装")
                return []
            
            logger.info(f"获取 {symbol} 分红数据: {start_date} 到 {end_date}")
            
            # 使用真实的掘金API获取分红数据
            try:
                # 暂时跳过分红数据API，因为权限问题
                logger.warning(f"分红数据API暂时不可用，跳过 {symbol}")
                return []
                
                if dividend_data is not None and len(dividend_data) > 0:
                    data = []
                    for _, item in dividend_data.iterrows():
                        dividend_item = {
                            'symbol': symbol,
                            'dividend_date': str(item.get('dividend_date', '')),
                            'dividend_per_share': float(item.get('dividend_per_share', 0.0)),
                            'dividend_type': item.get('dividend_type', 'CASH'),
                            'ex_dividend_date': str(item.get('ex_dividend_date', '')),
                            'record_date': str(item.get('record_date', ''))
                        }
                        data.append(dividend_item)
                    
                    logger.info(f"获取到 {len(data)} 条分红数据")
                    return data
                else:
                    logger.warning(f"未获取到 {symbol} 的分红数据")
                    return []
                    
            except Exception as api_error:
                logger.error(f"获取分红数据失败: {api_error}")
                return []
            
        except Exception as e:
            logger.error(f"获取分红数据失败: {e}")
            return []
    
    async def connect(self) -> bool:
        """连接到掘金量化服务器"""
        if gm is None:
            logger.error("掘金量化SDK未安装")
            return False
        
        try:
            logger.info(f"正在连接掘金量化服务器: {self.server_url}")
            
            # 设置连接参数
            gm.set_serv_addr(self.server_url)
            
            # 根据认证类型设置认证信息
            if self.auth_type == 'token':
                if not self.token:
                    raise ValueError("Token认证模式下必须提供token")
                gm.set_token(self.token)
                logger.info("使用Token认证模式")
            else:
                if not self.username or not self.password:
                    raise ValueError("用户名密码认证模式下必须提供用户名和密码")
                gm.set_token(self.username, self.password)
                logger.info("使用用户名密码认证模式")
            
            # 建立连接
            result = await self._connect_with_retry()
            
            if result:
                self.is_connected = True
                self.connection_time = time.time()
                self.last_heartbeat = time.time()
                self.reconnect_attempts = 0
                
                # 启动心跳检测
                await self._start_heartbeat()
                
                logger.info("掘金量化连接建立成功")
                
                if self.on_connected:
                    await self._safe_callback(self.on_connected)
                
                return True
            else:
                logger.error("掘金量化连接建立失败")
                return False
                
        except Exception as e:
            logger.error(f"连接掘金量化服务器异常: {e}")
            if self.on_error:
                await self._safe_callback(self.on_error, e)
            return False
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    async def _connect_with_retry(self) -> bool:
        """带重试的连接"""
        try:
            # 根据认证类型进行登录
            if self.auth_type == 'token':
                ret = gm.login(token=self.token)
            else:
                ret = gm.login(self.username, self.password)
            if ret != 0:
                raise Exception(f"登录失败，错误码: {ret}")
            
            # 验证连接
            account_info = gm.get_account()
            if not account_info:
                raise Exception("获取账户信息失败")
            
            logger.info(f"登录成功，账户: {account_info.get('account_id', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.warning(f"连接尝试失败: {e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        try:
            logger.info("正在断开掘金量化连接")
            
            # 停止心跳检测
            await self._stop_heartbeat()
            
            # 断开连接
            if GM_AVAILABLE and self.is_connected:
                try:
                    # 掘金API通常不需要显式断开连接
                    logger.debug("掘金API连接已断开")
                except Exception as e:
                    logger.warning(f"断开连接失败: {e}")
            
            self.is_connected = False
            self.connection_time = None
            self.last_heartbeat = None
            
            logger.info("掘金量化连接已断开")
            
            if self.on_disconnected:
                await self._safe_callback(self.on_disconnected)
                
        except Exception as e:
            logger.error(f"断开连接异常: {e}")
    
    async def reconnect(self) -> bool:
        """重新连接"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"重连次数已达上限 {self.max_reconnect_attempts}")
            return False
        
        self.reconnect_attempts += 1
        logger.info(f"尝试重新连接 (第 {self.reconnect_attempts} 次)")
        
        # 先断开现有连接
        await self.disconnect()
        
        # 等待一段时间后重连
        await asyncio.sleep(min(self.reconnect_attempts * 2, 30))
        
        return await self.connect()
    
    async def _start_heartbeat(self):
        """启动心跳检测"""
        if self.heartbeat_task:
            return
        
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.debug("心跳检测已启动")
    
    async def _stop_heartbeat(self):
        """停止心跳检测"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            self.heartbeat_task = None
            logger.debug("心跳检测已停止")
    
    async def _heartbeat_loop(self):
        """心跳检测循环"""
        while self.is_connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not await self._check_connection():
                    logger.warning("心跳检测失败，尝试重连")
                    await self.reconnect()
                    break
                else:
                    self.last_heartbeat = time.time()
                    logger.debug("心跳检测正常")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳检测异常: {e}")
                await asyncio.sleep(5)
    
    async def _check_connection(self) -> bool:
        """检查连接状态"""
        try:
            if not gm or not self.is_connected:
                return False
            
            # 尝试获取账户信息来验证连接
            account_info = gm.get_account()
            return account_info is not None
            
        except Exception as e:
            logger.debug(f"连接检查失败: {e}")
            return False
    
    async def _safe_callback(self, callback: Callable, *args):
        """安全执行回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"回调函数执行异常: {e}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            'is_connected': self.is_connected,
            'connection_time': self.connection_time,
            'last_heartbeat': self.last_heartbeat,
            'reconnect_attempts': self.reconnect_attempts,
            'server_url': self.server_url,
            'username': self.username
        }
    
    def set_callbacks(self, 
                     on_connected: Optional[Callable] = None,
                     on_disconnected: Optional[Callable] = None,
                     on_error: Optional[Callable] = None):
        """设置连接状态回调函数"""
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected
        self.on_error = on_error
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()