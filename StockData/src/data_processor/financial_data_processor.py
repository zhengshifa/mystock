#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据处理器

处理财务数据相关信息，包括:
- 财务报表数据(利润表、资产负债表、现金流量表)
- 财务指标数据
- 分红数据
- 股本变动数据
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

from .base_processor import BaseDataProcessor, DataProcessingError
from ..database import DataType, FinancialDataRepository, DividendDataRepository, ShareChangeDataRepository
from ..database.models import FinancialData, DividendData, ShareChangeData, FinancialDataType


class FinancialDataProcessor(BaseDataProcessor):
    """财务数据处理器"""
    
    @property
    def data_type(self) -> DataType:
        return DataType.FINANCIAL_DATA
    
    @property
    def processor_name(self) -> str:
        return "财务数据处理器"
    
    def __init__(self, gm_client, repository_manager, config):
        super().__init__(gm_client, repository_manager, config)
        
        # 获取相关仓库
        self.financial_data_repo = repository_manager.get_repository(DataType.FINANCIAL_DATA)
        self.dividend_data_repo = repository_manager.get_repository(DataType.DIVIDEND_DATA)
        self.share_change_repo = repository_manager.get_repository(DataType.SHARE_CHANGE_DATA)
        
        # 处理器特定配置
        self.symbols = config.get('symbols', [])  # 要处理的股票代码列表
        self.financial_data_types = config.get('financial_data_types', [
            'income_statement', 'balance_sheet', 'cash_flow', 'financial_indicator'
        ])  # 财务数据类型
        self.report_periods = config.get('report_periods', ['Q1', 'Q2', 'Q3', 'Q4'])  # 报告期
        self.years_back = config.get('years_back', 5)  # 获取多少年的历史数据
        
        logger.info(f"财务数据处理器初始化完成，股票数量: {len(self.symbols)}, 数据类型: {self.financial_data_types}")
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取财务数据"""
        try:
            data_subtype = kwargs.get('data_subtype', 'financial_data')
            
            if data_subtype == 'financial_data':
                return await self._fetch_financial_data(**kwargs)
            elif data_subtype == 'dividend_data':
                return await self._fetch_dividend_data(**kwargs)
            elif data_subtype == 'share_change_data':
                return await self._fetch_share_change_data(**kwargs)
            else:
                raise DataProcessingError(f"不支持的数据子类型: {data_subtype}")
                
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            raise
    
    async def _fetch_financial_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取财务报表数据"""
        try:
            symbols = kwargs.get('symbols', self.symbols)
            data_type = kwargs.get('financial_data_type', 'income_statement')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            if not symbols:
                logger.warning("未指定股票代码，跳过财务数据获取")
                return []
            
            if not start_date or not end_date:
                # 优先使用配置中的开始日期，否则使用默认的years_back
                end_date = datetime.now().date()
                config_start_date = self.config.get('sync', {}).get('historical_sync', {}).get('start_date')
                if config_start_date:
                    start_date = config_start_date
                else:
                    start_date = end_date - timedelta(days=365 * self.years_back)
                    start_date = start_date.strftime('%Y-%m-%d')
                end_date = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"获取 {len(symbols)} 只股票的 {data_type} 数据: {start_date} 到 {end_date}")
            
            all_financial_data = []
            
            # 分批获取，避免单次请求过多数据
            for symbol in symbols:
                try:
                    if data_type == 'income_statement':
                        data = await self.gm_client.get_income_statement(
                            symbol=symbol,
                            start_date=start_date,
                            end_date=end_date
                        )
                    elif data_type == 'balance_sheet':
                        data = await self.gm_client.get_balance_sheet(
                            symbol=symbol,
                            start_date=start_date,
                            end_date=end_date
                        )
                    elif data_type == 'cash_flow':
                        data = await self.gm_client.get_cash_flow(
                            symbol=symbol,
                            start_date=start_date,
                            end_date=end_date
                        )
                    elif data_type == 'financial_indicator':
                        data = await self.gm_client.get_financial_indicator(
                            symbol=symbol,
                            start_date=start_date,
                            end_date=end_date
                        )
                    else:
                        logger.warning(f"不支持的财务数据类型: {data_type}")
                        continue
                    
                    if data:
                        # 为每条数据添加股票代码和数据类型信息
                        for item in data:
                            item['symbol'] = symbol
                            item['data_type'] = data_type
                        
                        all_financial_data.extend(data)
                        logger.debug(f"获取到 {symbol} 的 {len(data)} 条 {data_type} 数据")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} {data_type} 数据失败: {e}")
                    continue
            
            logger.info(f"总共获取到 {len(all_financial_data)} 条财务数据")
            return all_financial_data
            
        except Exception as e:
            logger.error(f"获取财务报表数据失败: {e}")
            raise
    
    async def _fetch_dividend_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取分红数据"""
        try:
            symbols = kwargs.get('symbols', self.symbols)
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            if not symbols:
                logger.warning("未指定股票代码，跳过分红数据获取")
                return []
            
            if not start_date or not end_date:
                # 优先使用配置中的开始日期，否则使用默认的years_back
                end_date = datetime.now().date()
                config_start_date = self.config.get('sync', {}).get('historical_sync', {}).get('start_date')
                if config_start_date:
                    start_date = config_start_date
                else:
                    start_date = end_date - timedelta(days=365 * self.years_back)
                    start_date = start_date.strftime('%Y-%m-%d')
                end_date = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"获取 {len(symbols)} 只股票的分红数据: {start_date} 到 {end_date}")
            
            all_dividend_data = []
            
            # 分批获取
            for symbol in symbols:
                try:
                    data = await self.gm_client.get_dividend_data(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if data:
                        # 为每条数据添加股票代码信息
                        for item in data:
                            item['symbol'] = symbol
                        
                        all_dividend_data.extend(data)
                        logger.debug(f"获取到 {symbol} 的 {len(data)} 条分红数据")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} 分红数据失败: {e}")
                    continue
            
            logger.info(f"总共获取到 {len(all_dividend_data)} 条分红数据")
            return all_dividend_data
            
        except Exception as e:
            logger.error(f"获取分红数据失败: {e}")
            raise
    
    async def _fetch_share_change_data(self, **kwargs) -> List[Dict[str, Any]]:
        """获取股本变动数据"""
        try:
            symbols = kwargs.get('symbols', self.symbols)
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            if not symbols:
                logger.warning("未指定股票代码，跳过股本变动数据获取")
                return []
            
            if not start_date or not end_date:
                # 优先使用配置中的开始日期，否则使用默认的years_back
                end_date = datetime.now().date()
                config_start_date = self.config.get('sync', {}).get('historical_sync', {}).get('start_date')
                if config_start_date:
                    start_date = config_start_date
                else:
                    start_date = end_date - timedelta(days=365 * self.years_back)
                    start_date = start_date.strftime('%Y-%m-%d')
                end_date = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"获取 {len(symbols)} 只股票的股本变动数据: {start_date} 到 {end_date}")
            
            all_share_change_data = []
            
            # 分批获取
            for symbol in symbols:
                try:
                    data = await self.gm_client.get_share_change_data(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if data:
                        # 为每条数据添加股票代码信息
                        for item in data:
                            item['symbol'] = symbol
                        
                        all_share_change_data.extend(data)
                        logger.debug(f"获取到 {symbol} 的 {len(data)} 条股本变动数据")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} 股本变动数据失败: {e}")
                    continue
            
            logger.info(f"总共获取到 {len(all_share_change_data)} 条股本变动数据")
            return all_share_change_data
            
        except Exception as e:
            logger.error(f"获取股本变动数据失败: {e}")
            raise
    
    async def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理财务数据"""
        try:
            if not raw_data:
                return []
            
            # 判断数据类型并分别处理
            first_item = raw_data[0]
            
            if 'data_type' in first_item and first_item['data_type'] in self.financial_data_types:
                # 财务报表数据
                return await self._process_financial_data(raw_data)
            elif 'dividend_date' in first_item or 'cash_dividend' in first_item:
                # 分红数据
                return await self._process_dividend_data(raw_data)
            elif 'change_date' in first_item or 'total_shares' in first_item:
                # 股本变动数据
                return await self._process_share_change_data(raw_data)
            else:
                logger.warning(f"未知的财务数据格式: {first_item.keys()}")
                return []
                
        except Exception as e:
            logger.error(f"处理财务数据失败: {e}")
            raise
    
    async def _process_financial_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理财务报表数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'data_type': self._parse_financial_data_type(item.get('data_type')),
                        'report_date': self._format_datetime(item.get('report_date')),
                        'report_period': self._clean_string_data(item.get('report_period')),
                        'pub_date': self._format_datetime(item.get('pub_date')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 处理财务数据字段（根据数据类型不同，字段会有所不同）
                    financial_fields = self._extract_financial_fields(item)
                    processed_item.update(financial_fields)
                    
                    # 验证必要字段
                    if (processed_item['symbol'] and processed_item['data_type'] and 
                        processed_item['report_date']):
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"财务数据缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理财务数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条财务数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理财务报表数据失败: {e}")
            raise
    
    async def _process_dividend_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理分红数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'dividend_date': self._format_datetime(item.get('dividend_date')),
                        'ex_dividend_date': self._format_datetime(item.get('ex_dividend_date')),
                        'record_date': self._format_datetime(item.get('record_date')),
                        'cash_dividend': self._clean_numeric_data(item.get('cash_dividend')),
                        'stock_dividend': self._clean_numeric_data(item.get('stock_dividend')),
                        'dividend_ratio': self._clean_numeric_data(item.get('dividend_ratio')),
                        'dividend_yield': self._clean_numeric_data(item.get('dividend_yield')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 验证必要字段
                    if processed_item['symbol'] and processed_item['dividend_date']:
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"分红数据缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理分红数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条分红数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理分红数据失败: {e}")
            raise
    
    async def _process_share_change_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理股本变动数据"""
        try:
            processed_data = []
            
            for item in raw_data:
                try:
                    # 数据清洗和转换
                    processed_item = {
                        'symbol': self._clean_string_data(item.get('symbol')),
                        'change_date': self._format_datetime(item.get('change_date')),
                        'total_shares': self._clean_numeric_data(item.get('total_shares')),
                        'float_shares': self._clean_numeric_data(item.get('float_shares')),
                        'restricted_shares': self._clean_numeric_data(item.get('restricted_shares')),
                        'change_reason': self._clean_string_data(item.get('change_reason')),
                        'change_amount': self._clean_numeric_data(item.get('change_amount')),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 验证必要字段
                    if processed_item['symbol'] and processed_item['change_date']:
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"股本变动数据缺少必要字段: {item}")
                        
                except Exception as e:
                    logger.warning(f"处理股本变动数据项失败: {item}, 错误: {e}")
                    continue
            
            logger.info(f"成功处理 {len(processed_data)} 条股本变动数据")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理股本变动数据失败: {e}")
            raise
    
    async def save_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存财务数据"""
        try:
            if not processed_data:
                return True
            
            # 判断数据类型并分别保存
            first_item = processed_data[0]
            
            if 'data_type' in first_item and 'report_date' in first_item:
                # 财务报表数据
                return await self._save_financial_data(processed_data)
            elif 'dividend_date' in first_item:
                # 分红数据
                return await self._save_dividend_data(processed_data)
            elif 'change_date' in first_item and 'total_shares' in first_item:
                # 股本变动数据
                return await self._save_share_change_data(processed_data)
            else:
                logger.error(f"未知的财务数据格式，无法保存: {first_item.keys()}")
                return False
                
        except Exception as e:
            logger.error(f"保存财务数据失败: {e}")
            return False
    
    async def _save_financial_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存财务报表数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建FinancialData模型实例
                        financial_data = FinancialData(**item)
                        
                        # 财务数据通常是更新或插入操作
                        result = await self.financial_data_repo.save_or_update(
                            financial_data,
                            filter_dict={
                                'symbol': item['symbol'],
                                'data_type': item['data_type'],
                                'report_date': item['report_date']
                            }
                        )
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存财务数据失败: {item.get('symbol')} {item.get('report_date')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"财务数据保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存财务报表数据失败: {e}")
            return False
    
    async def _save_dividend_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存分红数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建DividendData模型实例
                        dividend_data = DividendData(**item)
                        
                        # 分红数据通常是更新或插入操作
                        result = await self.dividend_data_repo.save_or_update(
                            dividend_data,
                            filter_dict={
                                'symbol': item['symbol'],
                                'dividend_date': item['dividend_date']
                            }
                        )
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存分红数据失败: {item.get('symbol')} {item.get('dividend_date')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"分红数据保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存分红数据失败: {e}")
            return False
    
    async def _save_share_change_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """保存股本变动数据"""
        try:
            success_count = 0
            error_count = 0
            
            # 批量处理
            for i in range(0, len(processed_data), self.batch_size):
                batch = processed_data[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # 创建ShareChangeData模型实例
                        share_change_data = ShareChangeData(**item)
                        
                        # 股本变动数据通常是更新或插入操作
                        result = await self.share_change_repo.save_or_update(
                            share_change_data,
                            filter_dict={
                                'symbol': item['symbol'],
                                'change_date': item['change_date']
                            }
                        )
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.warning(f"保存股本变动数据失败: {item.get('symbol')} {item.get('change_date')}, 错误: {e}")
                        error_count += 1
                        continue
                
                # 批次间短暂休息
                if i + self.batch_size < len(processed_data):
                    await asyncio.sleep(0.1)
            
            logger.info(f"股本变动数据保存完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"保存股本变动数据失败: {e}")
            return False
    
    def _parse_financial_data_type(self, data_type_str: str) -> FinancialDataType:
        """解析财务数据类型"""
        try:
            if not data_type_str:
                return FinancialDataType.INCOME_STATEMENT  # 默认利润表
            
            data_type_str = data_type_str.lower().strip()
            
            if data_type_str in ['income_statement', 'income', 'profit']:
                return FinancialDataType.INCOME_STATEMENT
            elif data_type_str in ['balance_sheet', 'balance', 'bs']:
                return FinancialDataType.BALANCE_SHEET
            elif data_type_str in ['cash_flow', 'cashflow', 'cf']:
                return FinancialDataType.CASH_FLOW
            elif data_type_str in ['financial_indicator', 'indicator', 'fi']:
                return FinancialDataType.FINANCIAL_INDICATOR
            else:
                logger.warning(f"未知财务数据类型: {data_type_str}, 使用默认值 INCOME_STATEMENT")
                return FinancialDataType.INCOME_STATEMENT
                
        except Exception:
            return FinancialDataType.INCOME_STATEMENT
    
    def _extract_financial_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """提取财务字段"""
        try:
            financial_fields = {}
            
            # 定义需要提取的财务字段
            numeric_fields = [
                'total_revenue', 'operating_revenue', 'net_profit', 'gross_profit',
                'operating_profit', 'total_assets', 'total_liabilities', 'shareholders_equity',
                'current_assets', 'current_liabilities', 'cash_and_equivalents',
                'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow',
                'eps', 'roe', 'roa', 'debt_to_equity', 'current_ratio', 'quick_ratio',
                'gross_margin', 'operating_margin', 'net_margin', 'pe_ratio', 'pb_ratio'
            ]
            
            # 提取数值字段
            for field in numeric_fields:
                if field in item:
                    financial_fields[field] = self._clean_numeric_data(item[field])
            
            return financial_fields
            
        except Exception as e:
            logger.warning(f"提取财务字段失败: {e}")
            return {}
    
    def _validate_data_item(self, item: Dict[str, Any]) -> bool:
        """验证数据项"""
        try:
            # 财务数据验证
            if 'data_type' in item and 'report_date' in item:
                return bool(item.get('symbol') and item.get('data_type') and item.get('report_date'))
            
            # 分红数据验证
            elif 'dividend_date' in item:
                return bool(item.get('symbol') and item.get('dividend_date'))
            
            # 股本变动数据验证
            elif 'change_date' in item:
                return bool(item.get('symbol') and item.get('change_date'))
            
            return False
            
        except Exception:
            return False
    
    # ==================== 特定功能方法 ====================
    
    async def update_financial_data(self, symbols: Optional[List[str]] = None, 
                                   data_type: str = 'income_statement',
                                   start_date: Optional[str] = None, 
                                   end_date: Optional[str] = None) -> bool:
        """更新财务数据"""
        try:
            return await self.run(
                data_subtype='financial_data',
                symbols=symbols or self.symbols,
                financial_data_type=data_type,
                start_date=start_date,
                end_date=end_date
            )
            
        except Exception as e:
            logger.error(f"更新财务数据失败: {e}")
            return False
    
    async def update_dividend_data(self, symbols: Optional[List[str]] = None,
                                  start_date: Optional[str] = None, 
                                  end_date: Optional[str] = None) -> bool:
        """更新分红数据"""
        try:
            return await self.run(
                data_subtype='dividend_data',
                symbols=symbols or self.symbols,
                start_date=start_date,
                end_date=end_date
            )
            
        except Exception as e:
            logger.error(f"更新分红数据失败: {e}")
            return False
    
    async def update_share_change_data(self, symbols: Optional[List[str]] = None,
                                      start_date: Optional[str] = None, 
                                      end_date: Optional[str] = None) -> bool:
        """更新股本变动数据"""
        try:
            return await self.run(
                data_subtype='share_change_data',
                symbols=symbols or self.symbols,
                start_date=start_date,
                end_date=end_date
            )
            
        except Exception as e:
            logger.error(f"更新股本变动数据失败: {e}")
            return False
    
    async def get_latest_financial_data(self, symbol: str, data_type: str = 'income_statement') -> Optional[Dict[str, Any]]:
        """获取最新财务数据"""
        try:
            filter_dict = {
                'symbol': symbol,
                'data_type': self._parse_financial_data_type(data_type)
            }
            
            # 按报告日期降序排列，获取最新的一条
            financial_data = await self.financial_data_repo.find_one(
                filter_dict, 
                sort=[('report_date', -1)]
            )
            
            return financial_data.to_dict() if financial_data else None
            
        except Exception as e:
            logger.error(f"获取最新财务数据失败: {e}")
            return None
    
    async def get_dividend_history(self, symbol: str, years: int = 5) -> List[Dict[str, Any]]:
        """获取分红历史"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365 * years)
            
            filter_dict = {
                'symbol': symbol,
                'dividend_date': {
                    '$gte': start_date.strftime('%Y-%m-%d'),
                    '$lte': end_date.strftime('%Y-%m-%d')
                }
            }
            
            dividend_data = await self.dividend_data_repo.find_many(
                filter_dict,
                sort=[('dividend_date', -1)]
            )
            
            return [data.to_dict() for data in dividend_data] if dividend_data else []
            
        except Exception as e:
            logger.error(f"获取分红历史失败: {e}")
            return []