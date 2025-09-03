"""
掘金量化SDK服务类
封装掘金量化的API调用
"""
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime
import gm.api as gm
from ..config import settings
from ..models import Tick, Bar


class GMService:
    """掘金量化服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.logger = logging.getLogger(__name__)
        self._setup_gm()
    
    def _setup_gm(self) -> None:
        """
        设置掘金量化SDK
        """
        try:
            # 设置token
            gm.set_token(settings.gm_token)
            self.logger.info("掘金量化SDK初始化成功")
        except Exception as e:
            self.logger.error(f"掘金量化SDK初始化失败: {e}")
            raise
    
    def get_current_data(self, 
                        symbols: Union[str, List[str]], 
                        fields: str = '', 
                        include_call_auction: bool = False) -> List[Tick]:
        """
        查询当前行情快照
        
        Args:
            symbols: 查询代码，支持字符串或列表格式
            fields: 查询字段，默认所有字段
            include_call_auction: 是否支持集合竞价
            
        Returns:
            List[Tick]: Tick对象列表
        """
        try:
            self.logger.info(f"查询当前行情: {symbols}")
            
            # 调用掘金量化API
            raw_data = gm.current(
                symbols=symbols,
                fields=fields,
                include_call_auction=include_call_auction
            )
            
            # 转换为Tick对象
            tick_list = []
            for data in raw_data:
                tick = Tick.from_dict(data)
                tick_list.append(tick)
            
            self.logger.info(f"成功获取 {len(tick_list)} 条当前行情数据")
            return tick_list
            
        except Exception as e:
            self.logger.error(f"获取当前行情失败: {e}")
            raise
    
    def get_history_data(self,
                        symbol: Union[str, List[str]],
                        frequency: str = '1d',
                        start_time: Union[str, datetime] = None,
                        end_time: Union[str, datetime] = None,
                        fields: Optional[str] = None,
                        skip_suspended: bool = True,
                        fill_missing: Optional[str] = None,
                        adjust: int = 0,
                        adjust_end_time: str = '',
                        df: bool = False) -> Union[List[Bar], List[Dict]]:
        """
        查询历史行情数据
        
        Args:
            symbol: 标的代码
            frequency: 频率
            start_time: 开始时间
            end_time: 结束时间
            fields: 指定返回对象字段
            skip_suspended: 是否跳过停牌数据
            fill_missing: 填充缺失数据
            adjust: 复权类型
            adjust_end_time: 复权基点时间
            df: 是否返回DataFrame格式
            
        Returns:
            Union[List[Bar], List[Dict]]: Bar对象列表或原始数据列表
        """
        try:
            # 使用默认时间范围
            if start_time is None:
                start_time = settings.start_date
            if end_time is None:
                end_time = settings.end_date
            
            self.logger.info(f"查询历史行情: {symbol}, 频率: {frequency}, 时间范围: {start_time} - {end_time}")
            
            # 调用掘金量化API
            raw_data = gm.history(
                symbol=symbol,
                frequency=frequency,
                start_time=start_time,
                end_time=end_time,
                fields=fields,
                skip_suspended=skip_suspended,
                fill_missing=fill_missing,
                adjust=adjust,
                adjust_end_time=adjust_end_time,
                df=df
            )
            
            if df:
                # 如果返回DataFrame，直接返回
                self.logger.info(f"成功获取历史行情DataFrame，形状: {raw_data.shape}")
                return raw_data
            else:
                # 转换为Bar对象
                bar_list = []
                for data in raw_data:
                    bar = Bar.from_dict(data)
                    bar_list.append(bar)
                
                self.logger.info(f"成功获取 {len(bar_list)} 条历史行情数据")
                return bar_list
                
        except Exception as e:
            self.logger.error(f"获取历史行情失败: {e}")
            raise
    
    def get_symbol_infos(self, 
                        sec_type1: int, 
                        sec_type2: Optional[int] = None, 
                        exchanges: Optional[Union[str, List[str]]] = None, 
                        symbols: Optional[Union[str, List[str]]] = None, 
                        df: bool = False) -> Union[List[Dict], 'DataFrame']:
        """
        查询标的基本信息
        
        Args:
            sec_type1: 证券品种大类，必填
            sec_type2: 证券品种细类，可选
            exchanges: 交易所代码，可选
            symbols: 标的代码，可选
            df: 是否返回DataFrame格式，默认False返回字典格式
            
        Returns:
            Union[List[Dict], DataFrame]: 标的基本信息列表或DataFrame
        """
        try:
            self.logger.info(f"查询标的基本信息: sec_type1={sec_type1}, sec_type2={sec_type2}, exchanges={exchanges}, symbols={symbols}")
            
            # 调用掘金量化API
            raw_data = gm.get_symbol_infos(
                sec_type1=sec_type1,
                sec_type2=sec_type2,
                exchanges=exchanges,
                symbols=symbols,
                df=df
            )
            
            if df:
                self.logger.info(f"成功获取标的基本信息DataFrame，形状: {raw_data.shape}")
            else:
                self.logger.info(f"成功获取 {len(raw_data)} 条标的基本信息")
            
            return raw_data
            
        except Exception as e:
            self.logger.error(f"获取标的基本信息失败: {e}")
            raise

    def test_connection(self) -> bool:
        """
        测试连接是否正常
        
        Returns:
            bool: 连接是否正常
        """
        try:
            # 尝试获取一个简单的当前行情数据
            test_symbol = settings.test_symbols[0] if settings.test_symbols else 'SZSE.000001'
            data = self.get_current_data(symbols=test_symbol)
            
            if data and len(data) > 0:
                self.logger.info("连接测试成功")
                return True
            else:
                self.logger.warning("连接测试失败：未获取到数据")
                return False
                
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False
