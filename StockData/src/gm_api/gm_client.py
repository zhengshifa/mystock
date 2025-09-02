#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化客户端

提供掘金量化API的统一接口，包括:
- 连接管理
- 数据获取
- 错误处理
- 限流控制
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
from asyncio_throttle import Throttler

from .gm_connection_manager import GMConnectionManager
from .gm_data_fetcher import GMDataFetcher

try:
    import gm
except ImportError:
    logger.warning("掘金量化SDK未安装，请安装gm3包")
    gm = None


class GMClient:
    """掘金量化客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gm_config = config.get('gm', {})
        self.rate_limit_config = config.get('system', {}).get('rate_limit', {})
        
        # 初始化连接管理器
        self.connection_manager = GMConnectionManager(self.gm_config)
        
        # 初始化数据获取器
        self.data_fetcher = GMDataFetcher(self.gm_config)
        
        # 初始化限流器
        requests_per_second = self.rate_limit_config.get('requests_per_second', 10)
        burst_size = self.rate_limit_config.get('burst_size', 20)
        self.throttler = Throttler(rate_limit=requests_per_second, period=1.0)
        
        # 状态信息
        self.is_initialized = False
        self.last_error = None
        
        logger.info("掘金量化客户端初始化完成")
    
    async def initialize(self) -> bool:
        """初始化客户端"""
        try:
            logger.info("正在初始化掘金量化客户端")
            
            # 建立连接
            if not await self.connection_manager.connect():
                raise Exception("连接掘金量化服务器失败")
            
            # 初始化数据获取器
            await self.data_fetcher.initialize()
            
            self.is_initialized = True
            logger.info("掘金量化客户端初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"掘金量化客户端初始化失败: {e}")
            self.last_error = str(e)
            return False
    
    async def shutdown(self):
        """关闭客户端"""
        try:
            logger.info("正在关闭掘金量化客户端")
            
            # 关闭数据获取器
            await self.data_fetcher.shutdown()
            
            # 断开连接
            await self.connection_manager.disconnect()
            
            self.is_initialized = False
            logger.info("掘金量化客户端已关闭")
            
        except Exception as e:
            logger.error(f"关闭掘金量化客户端异常: {e}")
    
    async def _ensure_connected(self) -> bool:
        """确保连接可用"""
        if not self.is_initialized:
            return await self.initialize()
        
        if not self.connection_manager.is_connected:
            return await self.connection_manager.reconnect()
        
        return True
    
    async def _throttled_request(self, func, *args, **kwargs):
        """带限流的请求"""
        async with self.throttler:
            return await func(*args, **kwargs)
    
    # ==================== 基础数据接口 ====================
    
    async def get_stock_info(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取股票基本信息"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_stock_info, symbols
        )
    
    async def get_trading_calendar(self, 
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取交易日历"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_trading_calendar, start_date, end_date
        )
    
    # ==================== 行情数据接口 ====================
    
    async def get_realtime_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """获取实时行情"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_realtime_quotes, symbols
        )
    
    async def get_tick_data(self, 
                           symbol: str,
                           start_time: str,
                           end_time: str) -> List[Dict[str, Any]]:
        """获取逐笔数据"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_tick_data, symbol, start_time, end_time
        )
    
    async def get_bar_data(self, 
                          symbol: str,
                          period: str,
                          start_time: str,
                          end_time: str) -> List[Dict[str, Any]]:
        """获取K线数据"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_bar_data, symbol, period, start_time, end_time
        )
    
    # ==================== 财务数据接口 ====================
    
    async def get_financial_data(self, 
                               symbols: List[str],
                               data_type: str,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取财务数据"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_financial_data, symbols, data_type, start_date, end_date
        )
    
    async def get_income_statement(self, 
                                 symbols: List[str],
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取利润表"""
        return await self.get_financial_data(symbols, 'income_statement', start_date, end_date)
    
    async def get_balance_sheet(self, 
                              symbols: List[str],
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取资产负债表"""
        return await self.get_financial_data(symbols, 'balance_sheet', start_date, end_date)
    
    async def get_cash_flow(self, 
                          symbols: List[str],
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取现金流量表"""
        return await self.get_financial_data(symbols, 'cash_flow', start_date, end_date)
    
    async def get_financial_indicator(self, 
                                    symbols: List[str],
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取财务指标"""
        return await self.get_financial_data(symbols, 'financial_indicator', start_date, end_date)
    
    # ==================== 其他数据接口 ====================
    
    async def get_dividend_data(self, 
                              symbols: List[str],
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取分红数据"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_dividend_data, symbols, start_date, end_date
        )
    
    async def get_share_change_data(self, 
                                  symbols: List[str],
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取股本变动数据"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_share_change_data, symbols, start_date, end_date
        )
    
    async def get_index_constituent(self, 
                                  index_symbol: str,
                                  date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取指数成分股"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        return await self._throttled_request(
            self.data_fetcher.get_index_constituent, index_symbol, date
        )
    
    # ==================== 批量数据接口 ====================
    
    async def get_batch_data(self, 
                           data_requests: List[Dict[str, Any]],
                           batch_size: int = 100) -> List[Dict[str, Any]]:
        """批量获取数据"""
        if not await self._ensure_connected():
            raise Exception("连接不可用")
        
        results = []
        
        for i in range(0, len(data_requests), batch_size):
            batch = data_requests[i:i + batch_size]
            
            batch_results = await self._throttled_request(
                self.data_fetcher.get_batch_data, batch
            )
            
            results.extend(batch_results)
            
            # 批次间延迟
            if i + batch_size < len(data_requests):
                await asyncio.sleep(0.1)
        
        return results
    
    # ==================== 状态和监控接口 ====================
    
    def get_client_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        connection_info = self.connection_manager.get_connection_info()
        
        return {
            'is_initialized': self.is_initialized,
            'connection_info': connection_info,
            'last_error': self.last_error,
            'throttler_info': {
                'rate_limit': self.throttler.rate_limit,
                'period': self.throttler.period
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查连接状态
            connection_ok = await self._ensure_connected()
            
            # 尝试获取简单数据
            test_data = None
            if connection_ok:
                try:
                    test_data = await self.get_trading_calendar(
                        start_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                        end_date=datetime.now().strftime('%Y-%m-%d')
                    )
                except Exception as e:
                    logger.warning(f"健康检查数据获取失败: {e}")
            
            return {
                'status': 'healthy' if connection_ok and test_data is not None else 'unhealthy',
                'connection_ok': connection_ok,
                'data_access_ok': test_data is not None,
                'timestamp': datetime.now().isoformat(),
                'client_status': self.get_client_status()
            }
            
        except Exception as e:
            logger.error(f"健康检查异常: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # ==================== 上下文管理器 ====================
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.shutdown()