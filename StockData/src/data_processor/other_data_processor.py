#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
其他数据处理器

处理其他类型的股票数据，包括:
- 指数成分股数据
- 行业分类数据
- 概念板块数据
- 股票基本信息更新
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

from .base_processor import BaseDataProcessor, DataProcessingError
from ..database import DataType, IndexConstituentRepository, StockInfoRepository
from ..database.models import IndexConstituent, StockInfo, Exchange, SecType


class OtherDataProcessor(BaseDataProcessor):
    """其他数据处理器"""
    
    @property
    def data_type(self) -> DataType:
        return DataType.OTHER_DATA
    
    @property
    def processor_name(self) -> str:
        return "其他数据处理器"
    
    def __init__(self, gm_client, repository_manager, config):
        super().__init__(gm_client, repository_manager, config)
        
        # 获取相关仓库
        self.index_constituent_repo = repository_manager.get_repository(IndexConstituentRepository)
        self.stock_info_repo = repository_manager.get_repository(StockInfoRepository)
        
        # 处理器特定配置
        self.index_symbols = config.get('index_symbols', [
            'SHSE.000001',  # 上证指数
            'SZSE.399001',  # 深证成指
            'SZSE.399006',  # 创业板指
            'SHSE.000300',  # 沪深300
            'SHSE.000905',  # 中证500
            'SHSE.000852'   # 中证1000
        ])  # 要处理的指数代码列表
        
        self.industries = config.get('industries', [])  # 行业分类
        self.concepts = config.get('concepts', [])  # 概念板块
        
        logger.info(f"其他数据处理器初始化完成，指数数量: {len(self.index_symbols)}")
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取其他数据"""
        try:
            data_subtype = kwargs.get('data_subtype', 'index_constituent')
            
            if data_subtype == 'index_constituent':
                return await self._fetch_index_constituent_data(**kwargs)
            elif data_subtype == 'stock_info_update':
                return await self._fetch_stock_info_update(**kwargs)
            elif data_subtype == 'industry_data':
                return await self._fetch_industry_data(**kwargs)
            elif data_subtype == 'concept_data':
                return await self._fetch_concept_data(**kwargs)
            else:
                raise DataProcessingError(f"不支持的数据子类型: {data_subtype}")
                
        except Exception as e:
            logger.error(f"获取其他数据失败: {e}")
            raise
    
    async def _fetch_index_constituent_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取指数成分股数据"""
        try:
            index_symbols = kwargs.get('index_symbols', self.index_symbols)
            date = kwargs.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            if not index_symbols:
                logger.warning("未指定指数代码，跳过指数成分股数据获取")
                return []
            
            logger.info(f"获取 {len(index_symbols)} 个指数的成分股数据: {date}")
            
            all_constituent_data = []
            
            # 分批获取每个指数的成分股
            for index_symbol in index_symbols:
                try:
                    data = await self.gm_client.get_index_constituents(
                        index_symbol=index_symbol,
                        date=date
                    )
                    
                    if data:
                        # 为每条数据添加指数代码和日期信息
                        for item in data:
                            item['index_symbol'] = index_symbol
                            item['date'] = date
                        
                        all_constituent_data.extend(data)
                        logger.debug(f"获取到 {index_symbol} 的 {len(data)} 只成分股")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    logger.warning(f"获取 {index_symbol} 成分股数据失败: {e}")
                    continue
            
            logger.info(f"总共获取到 {len(all_constituent_data)} 条指数成分股数据")
            return all_constituent_data
            
        except Exception as e:
            logger.error(f"获取指数成分股数据失败: {e}")
            raise
    
    async def _fetch_stock_info_update(self, **kwargs) -> List[Dict[str, Any]]:
        """获取股票基本信息更新"""
        try:
            symbols = kwargs.get('symbols', [])
            
            if not symbols:
                # 如果没有指定股票，获取所有活跃股票的更新信息
                symbols = await self._get_active_symbols()
            
            if not symbols:
                logger.warning("未找到需要更新的股票代码")
                return []
            
            logger.info(f"获取 {len(symbols)} 只股票的基本信息更新")
            
            all_stock_info = []
            
            # 分批获取股票基本信息
            for i in range(0, len(symbols), 100):  # 每次处理100只股票
                batch_symbols = symbols[i:i + 100]
                
                try:
                    data = await self.gm_client.get_instruments(
                        symbols=batch_symbols
                    )
                    
                    if data:
                        all_stock_info.extend(data)
                        logger.debug(f"获取到 {len(data)} 只股票的基本信息")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"获取股票基本信息失败: {batch_symbols[:5]}..., 错误: {e}")
                    continue
            
            logger.info(f"总共获取到 {len(all_stock_info)} 条股票基本信息")
            return all_stock_info
            
        except Exception as e:
            logger.error(f"获取股票基本信息更新失败: {e}")
            raise
    
    async def _fetch_industry_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取行业分类数据"""
        try:
            # 这里可以根据实际API接口实现行业分类数据获取
            logger.info("获取行业分类数据")
            
            # 示例实现，实际需要根据掘金量化API调整
            industry_data = await self.gm_client.get_industry_data()
            
            if industry_data:
                logger.info(f"获取到 {len(industry_data)} 条行业分类数据")
                return industry_data
            else:
                logger.warning("未获取到行业分类数据")
                return []
                
        except Exception as e:
            logger.error(f"获取行业分类数据失败: {e}")
            raise
    
    async def _fetch_concept_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取概念板块数据"""
        try:
            # 这里可以根据实际API接口实现概念板块数据获取
            logger.info("获取概念板块数据")
            
            # 示例实现，实际需要根据掘金量化API调整
            concept_data = await self.gm_client.get_concept_data()
            
            if concept_data:
                logger.info(f"获取到 {len(concept_data)} 条概念板块数据")
                return concept_data
            else:
                logger.warning("未获取到概念板块数据")
                return []
                
        except Exception as e:
            logger.error(f"获取概念板块数据失败: {e}")
            raise
    
    async def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理其他数据"""
        try:
            if not raw_data:
                return []
            
            # 判断数据类型并分别处理
            first_item = raw_data[0]
            
            if 'index_symbol' in first_item and 'symbol' in first_item:
                # 指数成分股数据
                return await self._process_index_constituent_data(raw_data)
            elif 'sec_type' in first_item and 'exchange' in first_item:
                # 股票基本信息数据
                return await self._process_stock_info_data(raw_data)
            elif 'industry_code' in first_item or 'industry_name' in first_item:
                # 行业分类数据
                return await self._process_industry_data(raw_data)
            elif 'concept_code' in first_item or 'concept_name' in first_item:
                # 概念板块数据
                return await self._process_concept_data(raw_data)
            else:
                logger.warning(f"未知的其他数据格式: {first_item.keys()}")
                return []
                
        except Exception as e:
            logger.error(f"处理其他数据失败: {e}")
            raise
    
    async def _process_index_constituent_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理指数成分股数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'index_symbol': self._clean_string_data(item.get('index_symbol')),
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'date': self._format_date(item.get('date')),
                        'weight': self._clean_numeric_data(item.get('weight')),
                        'shares': self._clean_numeric_data(item.get('shares')),
                        'market_cap': self._clean_numeric_data(item.get('market_cap')),
                        'in_date': self._format_date(item.get('in_date')),
                        'out_date': self._format_date(item.get('out_date')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 验证必要字段
                    if (processed_item['index_symbol'] and processed_item['symbol'] and 
                        processed_item['date']):
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"指数成分股数据缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理指数成分股数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条指数成分股数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理指数成分股数据失败: {e}")
            raise
    
    async def _process_stock_info_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理股票基本信息数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'sec_name': self._clean_string_data(item.get('sec_name')),
                        'sec_type': self._parse_sec_type(item.get('sec_type')),
                        'exchange': self._parse_exchange(item.get('exchange')),
                        'list_date': self._format_date(item.get('list_date')),
                        'delist_date': self._format_date(item.get('delist_date')),
                        'is_active': bool(item.get('is_active', True)),
                        'industry': self._clean_string_data(item.get('industry')),
                        'concept': self._clean_string_data(item.get('concept')),
                        'market_cap': self._clean_numeric_data(item.get('market_cap')),
                        'total_shares': self._clean_numeric_data(item.get('total_shares')),
                        'float_shares': self._clean_numeric_data(item.get('float_shares')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 验证必要字段
                    if (processed_item['symbol'] and processed_item['sec_name'] and 
                        processed_item['sec_type'] and processed_item['exchange']):
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"股票基本信息缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理股票基本信息项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条股票基本信息")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理股票基本信息失败: {e}")
            raise
    
    async def _process_industry_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理行业分类数据"""
        try:
            # 这里可以根据实际需求实现行业分类数据处理
            logger.info(f"处理 {len(raw_data)} 条行业分类数据")
            return raw_data
            
        except Exception as e:
            logger.error(f"处理行业分类数据失败: {e}")
            raise
    
    async def _process_concept_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理概念板块数据"""
        try:
            # 这里可以根据实际需求实现概念板块数据处理
            logger.info(f"处理 {len(raw_data)} 条概念板块数据")
            return raw_data
            
        except Exception as e:
            logger.error(f"处理概念板块数据失败: {e}")
            raise
    
    async def save_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存其他数据"""
        try:
            if not processed_data:
                return True
            
            # 判断数据类型并分别保存
            first_item = processed_data[0]
            
            if 'index_symbol' in first_item and 'symbol' in first_item:
                # 指数成分股数据
                return await self._save_index_constituent_data(processed_data)
            elif 'sec_type' in first_item and 'exchange' in first_item:
                # 股票基本信息数据
                return await self._save_stock_info_data(processed_data)
            else:
                logger.warning(f"未知的其他数据格式，暂不保存: {first_item.keys()}")
                return True  # 暂时返回True，避免影响其他处理
                
        except Exception as e:
            logger.error(f"保存其他数据失败: {e}")
            return False
    
    async def _save_index_constituent_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存指数成分股数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建IndexConstituent模型实例
                        index_constituent = IndexConstituent(**item)
                        
                        # 指数成分股数据通常是更新或插入操作
                        result = await self.index_constituent_repo.save_or_update(
                            index_constituent,
                            filter_dict={
                                'index_symbol': item['index_symbol'],
                                'symbol': item['symbol'],
                                'date': item['date']
                            }
                        )
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存指数成分股数据失败: {item.get('index_symbol')} {item.get('symbol')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"指数成分股数据保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存指数成分股数据失败: {e}")
            return False
    
    async def _save_stock_info_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存股票基本信息数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建StockInfo模型实例
                        stock_info = StockInfo(**item)
                        
                        # 股票基本信息通常是更新或插入操作
                        result = await self.stock_info_repo.save_or_update(
                            stock_info,
                            filter_dict={'symbol': item['symbol']}
                        )
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存股票基本信息失败: {item.get('symbol')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"股票基本信息保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存股票基本信息失败: {e}")
            return False
    
    def _parse_sec_type(self, sec_type_str: str) -> SecType:
        """解析证券类型"""
        try:
            if not sec_type_str:
                return SecType.STOCK  # 默认股票
            
            sec_type_str = sec_type_str.upper().strip()
            
            if sec_type_str in ['STOCK', 'STK', 'CS']:
                return SecType.STOCK
            elif sec_type_str in ['INDEX', 'IDX']:
                return SecType.INDEX
            elif sec_type_str in ['FUND', 'FD']:
                return SecType.FUND
            elif sec_type_str in ['BOND', 'BD']:
                return SecType.BOND
            elif sec_type_str in ['FUTURE', 'FUT']:
                return SecType.FUTURE
            elif sec_type_str in ['OPTION', 'OPT']:
                return SecType.OPTION
            else:
                logger.warning(f"未知证券类型: {sec_type_str}, 使用默认值 STOCK")
                return SecType.STOCK
                
        except Exception:
            return SecType.STOCK
    
    def _parse_exchange(self, exchange_str: str) -> Exchange:
        """解析交易所"""
        try:
            if not exchange_str:
                return Exchange.SHSE  # 默认上交所
            
            exchange_str = exchange_str.upper().strip()
            
            if exchange_str in ['SHSE', 'SH', 'SSE']:
                return Exchange.SHSE
            elif exchange_str in ['SZSE', 'SZ']:
                return Exchange.SZSE
            elif exchange_str in ['BSE', 'BJ']:
                return Exchange.BSE
            else:
                logger.warning(f"未知交易所: {exchange_str}, 使用默认值 SHSE")
                return Exchange.SHSE
                
        except Exception:
            return Exchange.SHSE
    
    def _validate_data_item(self, item: Dict[str, Any]) -> bool:
        """验证数据项"""
        try:
            # 指数成分股数据验证
            if 'index_symbol' in item and 'symbol' in item:
                return bool(item.get('index_symbol') and item.get('symbol') and item.get('date'))
            
            # 股票基本信息验证
            elif 'sec_type' in item and 'exchange' in item:
                return bool(item.get('symbol') and item.get('sec_name'))
            
            return False
            
        except Exception:
            return False
    
    async def _get_active_symbols(self) -> List[str]:
        """获取活跃股票代码列表"""
        try:
            # 从数据库获取活跃股票列表
            active_stocks = await self.stock_info_repo.find_many(
                {'is_active': True},
                projection={'symbol': 1}
            )
            
            return [stock.symbol for stock in active_stocks] if active_stocks else []
            
        except Exception as e:
            logger.error(f"获取活跃股票代码失败: {e}")
            return []
    
    # ==================== 特定功能方法 ====================
    
    async def update_index_constituents(self, index_symbols: Optional[List[str]] = None,
                                       date: Optional[str] = None) -> bool:
        """更新指数成分股"""
        try:
            return await self.run(
                data_subtype='index_constituent',
                index_symbols=index_symbols or self.index_symbols,
                date=date or datetime.now().strftime('%Y-%m-%d')
            )
            
        except Exception as e:
            logger.error(f"更新指数成分股失败: {e}")
            return False
    
    async def update_stock_info(self, symbols: Optional[List[str]] = None) -> bool:
        """更新股票基本信息"""
        try:
            return await self.run(
                data_subtype='stock_info_update',
                symbols=symbols
            )
            
        except Exception as e:
            logger.error(f"更新股票基本信息失败: {e}")
            return False
    
    async def get_index_constituents(self, index_symbol: str, 
                                   date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取指数成分股"""
        try:
            filter_dict = {
                'index_symbol': index_symbol,
                'date': date or datetime.now().strftime('%Y-%m-%d')
            }
            
            constituents = await self.index_constituent_repo.find_many(
                filter_dict,
                sort=[('weight', -1)]  # 按权重降序排列
            )
            
            return [constituent.to_dict() for constituent in constituents] if constituents else []
            
        except Exception as e:
            logger.error(f"获取指数成分股失败: {e}")
            return []
    
    async def get_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            stock_info = await self.stock_info_repo.find_one({'symbol': symbol})
            return stock_info.to_dict() if stock_info else None
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            return None