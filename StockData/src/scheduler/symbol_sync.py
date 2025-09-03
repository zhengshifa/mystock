"""
标的基本信息同步服务
负责定时同步标的基本信息到数据库
"""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
from ..services.gm_service import GMService
from ..database import mongodb_client
from ..config import settings


class SymbolSyncService:
    """标的基本信息同步服务"""
    
    def __init__(self):
        """初始化同步服务"""
        self.logger = logging.getLogger(__name__)
        self.gm_service = GMService()
    
    async def sync_all_symbol_infos(self) -> bool:
        """
        同步所有标的基本信息
        
        Returns:
            bool: 同步是否成功
        """
        try:
            self.logger.info("开始同步所有标的基本信息")
            
            # 定义要同步的证券类型
            symbol_types = [
                {'sec_type1': 1010, 'sec_type2': 101001, 'name': 'A股'},
                {'sec_type1': 1010, 'sec_type2': 101002, 'name': 'B股'},
                {'sec_type1': 1010, 'sec_type2': 101003, 'name': '存托凭证'},
                {'sec_type1': 1020, 'sec_type2': 102001, 'name': 'ETF'},
                {'sec_type1': 1020, 'sec_type2': 102002, 'name': 'LOF'},
                {'sec_type1': 1030, 'sec_type2': 103001, 'name': '可转债'},
                {'sec_type1': 1040, 'sec_type2': 104001, 'name': '股指期货'},
                {'sec_type1': 1040, 'sec_type2': 104003, 'name': '商品期货'},
                {'sec_type1': 1050, 'sec_type2': 105001, 'name': '股票期权'},
                {'sec_type1': 1060, 'sec_type2': 106001, 'name': '股票指数'},
            ]
            
            total_synced = 0
            total_errors = 0
            
            for symbol_type in symbol_types:
                try:
                    self.logger.info(f"开始同步 {symbol_type['name']} 标的基本信息")
                    
                    # 获取标的基本信息
                    symbol_infos = self.gm_service.get_symbol_infos(
                        sec_type1=symbol_type['sec_type1'],
                        sec_type2=symbol_type['sec_type2']
                    )
                    
                    if symbol_infos:
                        # 保存到数据库
                        success = await mongodb_client.save_symbol_infos(symbol_infos)
                        if success:
                            total_synced += len(symbol_infos)
                            self.logger.info(f"成功同步 {symbol_type['name']} {len(symbol_infos)} 条记录")
                        else:
                            total_errors += 1
                            self.logger.error(f"保存 {symbol_type['name']} 标的基本信息到数据库失败")
                    else:
                        self.logger.warning(f"未获取到 {symbol_type['name']} 标的基本信息")
                        
                except Exception as e:
                    total_errors += 1
                    self.logger.error(f"同步 {symbol_type['name']} 标的基本信息失败: {e}")
            
            # 记录同步结果
            if total_errors == 0:
                self.logger.info(f"标的基本信息同步完成，共同步 {total_synced} 条记录")
                return True
            else:
                self.logger.error(f"标的基本信息同步完成，成功 {total_synced} 条，失败 {total_errors} 个类型")
                return False
                
        except Exception as e:
            self.logger.error(f"同步标的基本信息失败: {e}")
            return False
    
    async def sync_specific_symbol_type(self, sec_type1: int, sec_type2: Optional[int] = None, 
                                      exchanges: Optional[List[str]] = None) -> bool:
        """
        同步指定类型的标的基本信息
        
        Args:
            sec_type1: 证券大类
            sec_type2: 证券细类（可选）
            exchanges: 交易所列表（可选）
            
        Returns:
            bool: 同步是否成功
        """
        try:
            self.logger.info(f"开始同步指定类型标的基本信息: sec_type1={sec_type1}, sec_type2={sec_type2}")
            
            # 获取标的基本信息
            symbol_infos = self.gm_service.get_symbol_infos(
                sec_type1=sec_type1,
                sec_type2=sec_type2,
                exchanges=exchanges
            )
            
            if symbol_infos:
                # 保存到数据库
                success = await mongodb_client.save_symbol_infos(symbol_infos)
                if success:
                    self.logger.info(f"成功同步 {len(symbol_infos)} 条标的基本信息")
                    return True
                else:
                    self.logger.error("保存标的基本信息到数据库失败")
                    return False
            else:
                self.logger.warning("未获取到标的基本信息")
                return False
                
        except Exception as e:
            self.logger.error(f"同步指定类型标的基本信息失败: {e}")
            return False
    
    async def sync_stock_symbols(self) -> bool:
        """
        同步股票标的基本信息
        
        Returns:
            bool: 同步是否成功
        """
        return await self.sync_specific_symbol_type(sec_type1=1010, sec_type2=101001)
    
    async def sync_fund_symbols(self) -> bool:
        """
        同步基金标的基本信息
        
        Returns:
            bool: 同步是否成功
        """
        success_etf = await self.sync_specific_symbol_type(sec_type1=1020, sec_type2=102001)
        success_lof = await self.sync_specific_symbol_type(sec_type1=1020, sec_type2=102002)
        return success_etf and success_lof
    
    async def sync_bond_symbols(self) -> bool:
        """
        同步债券标的基本信息
        
        Returns:
            bool: 同步是否成功
        """
        return await self.sync_specific_symbol_type(sec_type1=1030, sec_type2=103001)
    
    async def sync_future_symbols(self) -> bool:
        """
        同步期货标的基本信息
        
        Returns:
            bool: 同步是否成功
        """
        success_stock_future = await self.sync_specific_symbol_type(sec_type1=1040, sec_type2=104001)
        success_commodity_future = await self.sync_specific_symbol_type(sec_type1=1040, sec_type2=104003)
        return success_stock_future and success_commodity_future
    
    async def sync_option_symbols(self) -> bool:
        """
        同步期权标的基本信息
        
        Returns:
            bool: 同步是否成功
        """
        return await self.sync_specific_symbol_type(sec_type1=1050, sec_type2=105001)
    
    async def sync_index_symbols(self) -> bool:
        """
        同步指数标的基本信息
        
        Returns:
            bool: 同步是否成功
        """
        return await self.sync_specific_symbol_type(sec_type1=1060, sec_type2=106001)
    
    async def get_sync_status(self) -> Dict:
        """
        获取同步状态
        
        Returns:
            Dict: 同步状态信息
        """
        try:
            # 获取数据库中的统计信息
            stats = await mongodb_client.get_symbol_info_statistics()
            
            return {
                'last_sync_time': datetime.now().isoformat(),
                'database_stats': stats,
                'service_status': 'running'
            }
            
        except Exception as e:
            self.logger.error(f"获取同步状态失败: {e}")
            return {
                'last_sync_time': None,
                'database_stats': None,
                'service_status': 'error',
                'error': str(e)
            }
