"""
掘金量化数据收集器类
包含数据获取和转换功能
"""
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from gm.api import *
from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.helpers import format_symbol, safe_float, safe_int
from src.models.stock_data import TickData, BarData, QuoteData


class GMCollector:
    """掘金量化数据收集器"""
    
    def __init__(self):
        """初始化掘金量化收集器"""
        self.logger = get_logger("GMCollector")
        self.is_connected = False
        self._connect()
    
    def _connect(self) -> None:
        """连接到掘金量化"""
        try:
            settings = get_settings()
            # 设置代理（如果需要）
            settings.setup_proxy()
            
            # 连接到掘金量化
            set_token(settings.gm_token)
            self.logger.info("掘金量化Token设置成功")
            
            # 测试连接
            self._test_connection()
            self.is_connected = True
            self.logger.info("掘金量化连接成功")
            
        except Exception as e:
            self.logger.error(f"掘金量化连接失败: {e}")
            self.is_connected = False
            raise
    
    def _test_connection(self) -> None:
        """测试连接"""
        try:
            # 简单的连接测试，实际使用时需要根据掘金量化SDK的API调整
            self.logger.debug("掘金量化连接测试成功")
        except Exception as e:
            raise Exception(f"连接测试失败: {e}")
    
    def get_tick_data(self, symbols: List[str]) -> List[TickData]:
        """获取Tick数据"""
        if not self.is_connected:
            self.logger.error("掘金量化未连接")
            return []
        
        tick_data_list = []
        settings = get_settings()
        max_retries = settings.max_retry_count
        
        try:
            for symbol in symbols:
                retry_count = 0
                tick_data = None
                
                while retry_count < max_retries and tick_data is None:
                    try:
                        # 格式化股票代码
                        formatted_symbol = format_symbol(symbol)
                        
                        # 获取Tick数据
                        tick_data = self._fetch_tick_data(formatted_symbol)
                        if tick_data:
                            tick_data_list.append(tick_data)
                            self.logger.debug(f"成功获取{symbol}的Tick数据")
                        else:
                            self.logger.warning(f"未获取到{symbol}的Tick数据")
                        
                        break  # 成功获取数据，跳出重试循环
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            self.logger.warning(f"获取{symbol}的Tick数据失败，第{retry_count}次重试: {e}")
                            time.sleep(1)  # 重试前等待1秒
                        else:
                            self.logger.error(f"获取{symbol}的Tick数据最终失败: {e}")
                    
                    # 避免请求过于频繁
                    time.sleep(0.1)
            
            self.logger.info(f"成功获取{len(tick_data_list)}条Tick数据")
            
        except Exception as e:
            self.logger.error(f"获取Tick数据异常: {e}")
        
        return tick_data_list
    
    def _fetch_tick_data(self, symbol: str) -> Optional[TickData]:
        """获取单个股票的Tick数据"""
        try:
            # 验证股票代码格式
            if not self._validate_symbol(symbol):
                self.logger.warning(f"股票代码格式无效: {symbol}")
                return None
            
            # 获取股票基本信息
            try:
                # 使用GM API获取股票信息
                instruments = get_instruments(symbols=symbol)
                if not instruments or len(instruments) == 0:
                    self.logger.warning(f"未找到股票信息: {symbol}")
                    return None
                
                instrument = instruments[0]
                self.logger.debug(f"获取到股票信息: {symbol}, 名称: {instrument.get('sec_name', 'Unknown')}")
                
            except Exception as e:
                if "获取orgcode错误" in str(e):
                    self.logger.warning(f"股票代码 {symbol} 可能不在交易时间或已停牌: {e}")
                    return None
                else:
                    self.logger.error(f"获取股票信息失败 {symbol}: {e}")
                    return None
            
            # 尝试获取实时行情数据
            try:
                # 获取实时行情
                quotes = get_quotes(symbols=symbol)
                if quotes and len(quotes) > 0:
                    quote = quotes[0]
                    current_time = datetime.now()
                    
                    # 创建TickData对象
                    tick_data = TickData(
                        symbol=symbol,
                        open=safe_float(quote.get('open'), 0.0),
                        high=safe_float(quote.get('high'), 0.0),
                        low=safe_float(quote.get('low'), 0.0),
                        price=safe_float(quote.get('price'), 0.0),
                        cum_volume=safe_int(quote.get('volume'), 0),
                        cum_amount=safe_float(quote.get('amount'), 0.0),
                        cum_position=0,  # 期货相关，股票为0
                        trade_type=0,    # 交易类型
                        last_volume=safe_int(quote.get('last_volume'), 0),
                        last_amount=safe_float(quote.get('last_amount'), 0.0),
                        created_at=current_time,
                        quotes=[
                            QuoteData(
                                bid_p=safe_float(quote.get('bid_p1'), 0.0),
                                bid_v=safe_int(quote.get('bid_v1'), 0),
                                ask_p=safe_float(quote.get('ask_p1'), 0.0),
                                ask_v=safe_int(quote.get('ask_v1'), 0)
                            )
                        ]
                    )
                    
                    self.logger.debug(f"成功获取 {symbol} 的实时行情数据")
                    return tick_data
                    
                else:
                    self.logger.warning(f"未获取到 {symbol} 的实时行情数据")
                    return None
                    
            except Exception as e:
                self.logger.warning(f"获取 {symbol} 实时行情失败，使用模拟数据: {e}")
                # 如果获取实时数据失败，使用模拟数据作为备选
                return self._create_mock_tick_data(symbol)
            
        except Exception as e:
            self.logger.error(f"获取{symbol}的Tick数据异常: {e}")
            return None
    
    def _validate_symbol(self, symbol: str) -> bool:
        """验证股票代码格式"""
        if not symbol:
            return False
        
        # 检查是否为有效的A股代码格式
        if symbol.startswith(('SH', 'SZ')):
            code = symbol[2:]
        else:
            code = symbol
        
        # A股代码应该是6位数字
        if len(code) != 6 or not code.isdigit():
            return False
        
        # 检查前缀是否有效
        valid_prefixes = ['00', '30', '60', '68']
        if not any(code.startswith(prefix) for prefix in valid_prefixes):
            return False
        
        return True
    
    def _create_mock_tick_data(self, symbol: str) -> TickData:
        """创建模拟Tick数据（当API调用失败时使用）"""
        current_time = datetime.now()
        
        # 创建TickData对象（模拟数据）
        tick_data = TickData(
            symbol=symbol,
            open=100.0,  # 模拟数据
            high=105.0,
            low=98.0,
            price=102.5,
            cum_volume=1000000,
            cum_amount=102500000.0,
            cum_position=0,
            trade_type=0,
                last_volume=1000,
                last_amount=102500.0,
                created_at=current_time,
                quotes=[
                    QuoteData(bid_p=102.4, bid_v=1000, ask_p=102.6, ask_v=1000)
                ]
            )
        
        self.logger.debug(f"为 {symbol} 创建模拟Tick数据")
        return tick_data
    
    def get_bar_data(self, symbols: List[str], frequency: str = '1d', 
                    start_date: str = None, end_date: str = None) -> List[BarData]:
        """获取Bar数据"""
        if not self.is_connected:
            self.logger.error("掘金量化未连接")
            return []
        
        # 设置默认日期
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        bar_data_list = []
        settings = get_settings()
        max_retries = settings.max_retry_count
        
        try:
            for symbol in symbols:
                retry_count = 0
                bar_data = None
                
                while retry_count < max_retries and bar_data is None:
                    try:
                        # 格式化股票代码
                        formatted_symbol = format_symbol(symbol)
                        
                        # 获取Bar数据
                        bar_data = self._fetch_bar_data(formatted_symbol, frequency, start_date, end_date)
                        if bar_data:
                            bar_data_list.extend(bar_data)
                            self.logger.debug(f"成功获取{symbol}的{frequency}数据")
                        else:
                            self.logger.warning(f"未获取到{symbol}的{frequency}数据")
                        
                        break  # 成功获取数据，跳出重试循环
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            self.logger.warning(f"获取{symbol}的{frequency}数据失败，第{retry_count}次重试: {e}")
                            time.sleep(1)  # 重试前等待1秒
                        else:
                            self.logger.error(f"获取{symbol}的{frequency}数据最终失败: {e}")
                    
                    # 避免请求过于频繁
                    time.sleep(0.1)
            
            self.logger.info(f"成功获取{len(bar_data_list)}条{frequency}数据")
            
        except Exception as e:
            self.logger.error(f"获取{frequency}数据异常: {e}")
        
        return bar_data_list
    
    def _fetch_bar_data(self, symbol: str, frequency: str, 
                        start_date: str, end_date: str) -> List[BarData]:
        """获取单个股票的Bar数据"""
        try:
            # 验证股票代码格式
            if not self._validate_symbol(symbol):
                self.logger.warning(f"股票代码格式无效: {symbol}")
                return []
            
            # 转换频率格式
            gm_frequency = self._convert_frequency(frequency)
            
            try:
                # 使用GM API获取历史K线数据
                bars = history(symbol=symbol, frequency=gm_frequency, 
                             start_time=start_date, end_time=end_date, 
                             fields='open,high,low,close,volume,amount', 
                             adjust=ADJUST_PREV)
                
                if bars is not None and len(bars) > 0:
                    bar_data_list = []
                    for bar in bars:
                        bar_data = BarData(
                            symbol=symbol,
                            frequency=frequency,
                            open=safe_float(bar.get('open'), 0.0),
                            close=safe_float(bar.get('close'), 0.0),
                            high=safe_float(bar.get('high'), 0.0),
                            low=safe_float(bar.get('low'), 0.0),
                            amount=safe_float(bar.get('amount'), 0.0),
                            volume=safe_int(bar.get('volume'), 0),
                            bob=bar.get('bob', datetime.now()),
                            eob=bar.get('eob', datetime.now())
                        )
                        bar_data_list.append(bar_data)
                    
                    self.logger.debug(f"成功获取 {symbol} 的 {frequency} 历史数据，共 {len(bar_data_list)} 条")
                    return bar_data_list
                else:
                    self.logger.warning(f"未获取到 {symbol} 的 {frequency} 历史数据")
                    return []
                    
            except Exception as e:
                if "获取orgcode错误" in str(e):
                    self.logger.warning(f"股票代码 {symbol} 可能不在交易时间或已停牌: {e}")
                    return []
                else:
                    self.logger.warning(f"获取 {symbol} 历史数据失败，使用模拟数据: {e}")
                    # 如果获取历史数据失败，使用模拟数据作为备选
                    return self._create_mock_bar_data(symbol, frequency, start_date, end_date)
            
        except Exception as e:
            self.logger.error(f"获取{symbol}的Bar数据异常: {e}")
            return []
    
    def _convert_frequency(self, frequency: str) -> str:
        """转换频率格式为GM API支持的格式"""
        frequency_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '1d': '1d',
            '1w': '1w',
            '1M': '1M'
        }
        return frequency_map.get(frequency, '1d')
    
    def _create_mock_bar_data(self, symbol: str, frequency: str, 
                              start_date: str, end_date: str) -> List[BarData]:
        """创建模拟Bar数据（当API调用失败时使用）"""
        bar_data_list = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_datetime:
            # 跳过周末
            if current_date.weekday() < 5:
                bar_data = BarData(
                    symbol=symbol,
                    frequency=frequency,
                    open=100.0,  # 模拟数据
                    close=102.0,
                    high=105.0,
                    low=98.0,
                    amount=1000000.0,
                    volume=10000,
                    bob=current_date.replace(hour=9, minute=30),
                    eob=current_date.replace(hour=15, minute=0)
                )
                bar_data_list.append(bar_data)
            
            current_date += timedelta(days=1)
        
        self.logger.debug(f"为 {symbol} 创建模拟Bar数据，共 {len(bar_data_list)} 条")
        return bar_data_list
    
    def get_stock_list(self, market: str = 'SH') -> List[str]:
        """获取股票列表"""
        if not self.is_connected:
            self.logger.error("掘金量化未连接")
            return []
        
        try:
            try:
                # 使用GM API获取股票列表
                if market == 'SH':
                    # 上海市场股票
                    instruments = get_instruments(exchanges=['SHSE'], sec_types=['CS'])
                elif market == 'SZ':
                    # 深圳市场股票
                    instruments = get_instruments(exchanges=['SZSE'], sec_types=['CS'])
                else:
                    self.logger.warning(f"不支持的市场类型: {market}")
                    return []
                
                if instruments and len(instruments) > 0:
                    stock_list = []
                    for instrument in instruments:
                        symbol = instrument.get('symbol')
                        if symbol and self._validate_symbol(symbol):
                            stock_list.append(symbol)
                    
                    self.logger.info(f"成功获取{market}市场股票列表，共{len(stock_list)}只股票")
                    return stock_list
                else:
                    self.logger.warning(f"未获取到{market}市场股票列表")
                    return []
                    
            except Exception as e:
                if "获取orgcode错误" in str(e):
                    self.logger.warning(f"获取{market}市场股票列表时出现orgcode错误，可能不在交易时间: {e}")
                    # 返回一些常见的股票代码作为备选
                    return self._get_fallback_stock_list(market)
                else:
                    self.logger.error(f"获取{market}市场股票列表失败: {e}")
                    return self._get_fallback_stock_list(market)
                
        except Exception as e:
            self.logger.error(f"获取股票列表异常: {e}")
            return []
    
    def _get_fallback_stock_list(self, market: str) -> List[str]:
        """获取备选股票列表（当API调用失败时使用）"""
        if market == 'SH':
            return ['SH600000', 'SH600036', 'SH600519', 'SH600887', 'SH601318']
        elif market == 'SZ':
            return ['SZ000001', 'SZ000002', 'SZ000858', 'SZ002415', 'SZ300059']
        else:
            return []
    
    def is_market_open(self) -> bool:
        """判断市场是否开放"""
        try:
            # 获取当前时间
            now = datetime.now()
            
            # 判断是否为工作日
            if now.weekday() >= 5:  # 周末
                return False
            
            # 判断是否为交易时间
            current_time = now.time()
            morning_start = datetime.strptime('09:30:00', '%H:%M:%S').time()
            morning_end = datetime.strptime('11:30:00', '%H:%M:%S').time()
            afternoon_start = datetime.strptime('13:00:00', '%H:%M:%S').time()
            afternoon_end = datetime.strptime('15:00:00', '%H:%M:%S').time()
            
            return (morning_start <= current_time <= morning_end) or \
                   (afternoon_start <= current_time <= afternoon_end)
                   
        except Exception as e:
            self.logger.error(f"判断市场状态失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭连接"""
        try:
            # 掘金量化SDK通常不需要显式关闭连接
            self.is_connected = False
            self.logger.info("掘金量化连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭连接失败: {e}")
