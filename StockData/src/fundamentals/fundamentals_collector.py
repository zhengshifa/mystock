#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本面数据采集器

功能：
1. 采集股票基本面数据（资产负债表、利润表、现金流量表）
2. 数据存储到MongoDB
3. 支持批量采集和单只股票采集
4. 提供数据验证和错误处理
5. 支持数据清理和索引管理
6. 提供统一的基本面数据获取和存储接口
"""

import logging
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 修复配置和日志导入
try:
    from config import config
    from utils.log_manager import get_logger
except ImportError as e:
    print(f"配置模块导入失败: {e}")
    print("请确保config模块正确配置")
    sys.exit(1)

from utils.database import DatabaseManager
from utils.gm_client import GMClient
from models import BalanceSheet, IncomeStatement, CashFlowStatement, FundamentalsData, FinancialIndicator
from src.services.data_model_service import data_model_service

# 获取日志记录器
logger = get_logger(__name__)


class FundamentalsDataCollector:
    """基本面数据采集器
    
    提供统一的基本面数据获取和存储接口，支持：
    - 资产负债表、利润表、现金流量表数据采集
    - 批量数据处理和优化
    - 数据存储和查询
    - 数据生命周期管理
    - 索引优化
    """
    
    def __init__(self, gm_config=None, mongo_config=None):
        """初始化采集器
        
        Args:
            gm_config: 掘金配置，如果为None则使用默认配置
            mongo_config: MongoDB配置，如果为None则使用默认配置
        """
        self.db_manager = None
        self.gm_client = GMClient(gm_config)
        self.data_config = config.data
        
        # 基于实际测试验证的有效字段配置
        # 测试结果: 资产负债表15个有效字段(41.7%成功率), 现金流量表4个有效字段(22.2%成功率)
        self.valid_fields = {
            'balance': {
                'fields': [
                    'cash_bal_cb',  # 现金及存放中央银行款项
                    'mny_cptl',     # 货币资金
                    'bal_clr',      # 结算备付金
                    'ppay',         # 预付款项
                    'note_rcv',     # 应收票据
                    'acct_rcv',     # 应收账款
                    'oth_rcv',      # 其他应收款
                    'oth_cur_ast',  # 其他流动资产
                    'fix_ast',      # 固定资产
                    'acct_pay',     # 应付账款
                    'tax_pay',      # 应交税费
                    'int_pay',      # 应付利息
                    'oth_pay',      # 其他应付款
                    'paid_in_cptl', # 实收资本
                    'cptl_rsv'      # 资本公积
                ],
                'fields_str': 'cash_bal_cb,mny_cptl,bal_clr,ppay,note_rcv,acct_rcv,oth_rcv,oth_cur_ast,fix_ast,acct_pay,tax_pay,int_pay,oth_pay,paid_in_cptl,cptl_rsv'
            },
            'income': {
                'fields': [
                    # 利润表字段暂时为空，需要进一步研究正确的字段名
                    # 可以通过custom_fields参数传入自定义字段
                ],
                'fields_str': ''
            },
            'cashflow': {
                'fields': [
                    'net_cf_oper',  # 经营活动产生的现金流量净额
                    'cash_pay_tax', # 支付的各项税费
                    'net_cf_inv',   # 投资活动产生的现金流量净额
                    'net_cf_fin'    # 筹资活动产生的现金流量净额
                ],
                'fields_str': 'net_cf_oper,cash_pay_tax,net_cf_inv,net_cf_fin'
            }
        }
        
        self._init_connections()
    
    def _init_connections(self):
        """初始化数据库和GM SDK连接"""
        try:
            # 初始化数据库连接
            self.db_manager = DatabaseManager()
            
            if not self.db_manager.connect():
                raise ConnectionError("数据库连接失败")
            
            logger.info("数据库连接成功")
            
            # 初始化GM SDK连接
            if not self.gm_client.connect():
                raise ConnectionError("GM SDK连接失败")
            
            logger.info("GM SDK连接成功")
            
        except Exception as e:
            logger.error(f"初始化连接失败: {e}")
            raise
    
    def initialize(self) -> bool:
        """初始化采集器（兼容性方法）
        
        Returns:
            初始化是否成功
        """
        try:
            return (self.db_manager is not None and 
                   self.gm_client.is_connected if hasattr(self.gm_client, 'is_connected') else True)
        except Exception as e:
            logger.error(f"检查初始化状态失败: {e}")
            return False
    
    def collect_fundamentals_data(self, symbols: List[str], 
                                start_date: str = None, 
                                end_date: str = None,
                                rpt_type: int = 0,
                                data_type: int = 0,
                                save_to_db: bool = True) -> Dict[str, Any]:
        """采集基本面数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期，格式：'2023-01-01'
            end_date: 结束日期，格式：'2023-12-31'
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
            save_to_db: 是否保存到数据库
        
        Returns:
            采集结果统计
        """
        logger.info(f"开始采集基本面数据，股票数量: {len(symbols)}")
        
        # 设置默认日期范围（最近一年）
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'total_records': 0,
            'failed_symbols': [],
            'data': {
                'balance': [],
                'income': [],
                'cashflow': []
            }
        }
        
        try:
            # 分批处理股票代码，避免单次请求过多
            batch_size = 10
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]
                logger.info(f"处理批次 {i//batch_size + 1}，股票: {batch_symbols}")
                
                try:
                    # 获取基本面数据（使用验证过的有效字段）
                    fundamentals_data = {'balance': [], 'income': [], 'cashflow': []}
                    
                    # 获取资产负债表数据
                    if self.valid_fields['balance']['fields']:
                        balance_data = self.gm_client.get_fundamentals_balance(
                            symbols=batch_symbols,
                            start_date=start_date,
                            end_date=end_date,
                            fields=self.valid_fields['balance']['fields_str'],
                            rpt_type=rpt_type,
                            data_type=data_type
                        )
                        if balance_data:
                            fundamentals_data['balance'] = balance_data
                    
                    # 获取利润表数据（暂时跳过，因为没有有效字段）
                    if self.valid_fields['income']['fields']:
                        income_data = self.gm_client.get_fundamentals_income(
                            symbols=batch_symbols,
                            start_date=start_date,
                            end_date=end_date,
                            fields=self.valid_fields['income']['fields_str'],
                            rpt_type=rpt_type,
                            data_type=data_type
                        )
                        if income_data:
                            fundamentals_data['income'] = income_data
                    
                    # 获取现金流量表数据
                    if self.valid_fields['cashflow']['fields']:
                        cashflow_data = self.gm_client.get_fundamentals_cashflow(
                            symbols=batch_symbols,
                            start_date=start_date,
                            end_date=end_date,
                            fields=self.valid_fields['cashflow']['fields_str'],
                            rpt_type=rpt_type,
                            data_type=data_type
                        )
                        if cashflow_data:
                            fundamentals_data['cashflow'] = cashflow_data
                    
                    # 合并数据
                    for table_type in ['balance', 'income', 'cashflow']:
                        if fundamentals_data[table_type]:
                            results['data'][table_type].extend(fundamentals_data[table_type])
                    
                    # 保存到数据库
                    if save_to_db:
                        saved_count = self._save_fundamentals_data(fundamentals_data)
                        results['total_records'] += saved_count
                    
                    results['success_count'] += len(batch_symbols)
                    
                    # 避免请求过于频繁
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"批次处理失败 {batch_symbols}: {e}")
                    results['failed_count'] += len(batch_symbols)
                    results['failed_symbols'].extend(batch_symbols)
            
            logger.info(f"基本面数据采集完成，成功: {results['success_count']}, 失败: {results['failed_count']}")
            
        except Exception as e:
            logger.error(f"采集基本面数据失败: {e}")
            raise
        
        return results
    
    def get_balance_sheet_data(self, symbols: List[str], start_date: str = None, 
                               end_date: str = None, custom_fields: str = None,
                               rpt_type: int = 0, data_type: int = 0) -> List[Dict[str, Any]]:
        """获取资产负债表数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            custom_fields: 自定义字段，如果不提供则使用默认有效字段
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
        
        Returns:
            资产负债表数据列表
        """
        fields = custom_fields or self.valid_fields['balance']['fields_str']
        if not fields:
            logger.warning("资产负债表暂无有效字段配置")
            return []
        
        return self.gm_client.get_fundamentals_balance(
            symbols=symbols,
            fields=fields,
            start_date=start_date,
            end_date=end_date,
            rpt_type=rpt_type,
            data_type=data_type
        )
    
    def get_income_statement_data(self, symbols: List[str], start_date: str = None, 
                                  end_date: str = None, custom_fields: str = None,
                                  rpt_type: int = 0, data_type: int = 0) -> List[Dict[str, Any]]:
        """获取利润表数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            custom_fields: 自定义字段
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
        
        Returns:
            利润表数据列表
        """
        if not custom_fields:
            logger.warning("利润表暂无已验证的有效字段，请提供custom_fields参数")
            return []
        
        return self.gm_client.get_fundamentals_income(
            symbols=symbols,
            fields=custom_fields,
            start_date=start_date,
            end_date=end_date,
            rpt_type=rpt_type,
            data_type=data_type
        )
    
    def get_cashflow_statement_data(self, symbols: List[str], start_date: str = None, 
                                    end_date: str = None, custom_fields: str = None,
                                    rpt_type: int = 0, data_type: int = 0) -> List[Dict[str, Any]]:
        """获取现金流量表数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            custom_fields: 自定义字段，如果不提供则使用默认有效字段
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
        
        Returns:
            现金流量表数据列表
        """
        fields = custom_fields or self.valid_fields['cashflow']['fields_str']
        if not fields:
            logger.warning("现金流量表暂无有效字段配置")
            return []
        
        return self.gm_client.get_fundamentals_cashflow(
            symbols=symbols,
            fields=fields,
            start_date=start_date,
            end_date=end_date,
            rpt_type=rpt_type,
            data_type=data_type
        )
    
    def get_all_fundamentals_data(self, symbols: List[str], start_date: str = None, 
                                  end_date: str = None, rpt_type: int = 0, 
                                  data_type: int = 0) -> Dict[str, List[Dict[str, Any]]]:
        """获取完整的基本面数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
        
        Returns:
            包含三张表数据的字典
        """
        result = {
            'balance': self.get_balance_sheet_data(symbols, start_date, end_date, 
                                                 rpt_type=rpt_type, data_type=data_type),
            'income': self.get_income_statement_data(symbols, start_date, end_date, 
                                                   custom_fields="", rpt_type=rpt_type, data_type=data_type),
            'cashflow': self.get_cashflow_statement_data(symbols, start_date, end_date, 
                                                       rpt_type=rpt_type, data_type=data_type)
        }
        
        logger.info(f"获取基本面数据完成: 资产负债表{len(result['balance'])}条, "
                   f"利润表{len(result['income'])}条, 现金流量表{len(result['cashflow'])}条")
        
        return result
    
    def save_fundamentals_data(self, data: Dict[str, List[Dict[str, Any]]], 
                               collection_prefix: str = 'fundamentals') -> bool:
        """保存基本面数据到MongoDB（兼容性方法）
        
        Args:
            data: 基本面数据字典
            collection_prefix: 集合名前缀
        
        Returns:
            是否保存成功
        """
        try:
            saved_count = self._save_fundamentals_data(data)
            return saved_count > 0
        except Exception as e:
            logger.error(f"保存基本面数据失败: {e}")
            return False
    
    def collect_and_save(self, symbols: List[str], start_date: str = None, 
                         end_date: str = None, collection_prefix: str = 'fundamentals',
                         rpt_type: int = 0, data_type: int = 0) -> bool:
        """采集并保存基本面数据（兼容性方法）
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            collection_prefix: 集合名前缀
            rpt_type: 报告类型 0-合并报表 1-母公司报表
            data_type: 数据类型 0-原始数据 1-单季度数据
        
        Returns:
            是否成功
        """
        try:
            logger.info(f"开始采集基本面数据: {symbols}")
            
            # 获取数据
            data = self.get_all_fundamentals_data(symbols, start_date, end_date, 
                                                rpt_type, data_type)
            
            # 保存数据
            if self.save_fundamentals_data(data, collection_prefix):
                logger.info("基本面数据采集和保存完成")
                return True
            else:
                logger.error("基本面数据保存失败")
                return False
        except Exception as e:
            logger.error(f"采集基本面数据失败: {e}")
            return False
    
    def _save_fundamentals_data(self, data: Dict[str, List[Dict[str, Any]]]) -> int:
        """保存基本面数据到数据库
        
        Args:
            data: 基本面数据字典
        
        Returns:
            保存的记录数
        """
        total_saved = 0
        
        try:
            # 保存资产负债表数据
            if data['balance']:
                # 转换为数据模型
                balance_models = self._convert_to_models(data['balance'], 'balance')
                collection = self.db_manager.get_collection(self.data_config.fundamentals_balance_collection)
                saved_count = self._save_batch_data(collection, data['balance'])
                total_saved += saved_count
                logger.info(f"保存资产负债表数据: {saved_count}条 (模型验证通过: {len(balance_models)}条)")
            
            # 保存利润表数据
            if data['income']:
                # 转换为数据模型
                income_models = self._convert_to_models(data['income'], 'income')
                collection = self.db_manager.get_collection(self.data_config.fundamentals_income_collection)
                saved_count = self._save_batch_data(collection, data['income'])
                total_saved += saved_count
                logger.info(f"保存利润表数据: {saved_count}条 (模型验证通过: {len(income_models)}条)")
            
            # 保存现金流量表数据
            if data['cashflow']:
                # 转换为数据模型
                cashflow_models = self._convert_to_models(data['cashflow'], 'cashflow')
                collection = self.db_manager.get_collection(self.data_config.fundamentals_cashflow_collection)
                saved_count = self._save_batch_data(collection, data['cashflow'])
                total_saved += saved_count
                logger.info(f"保存现金流量表数据: {saved_count}条 (模型验证通过: {len(cashflow_models)}条)")
            
        except Exception as e:
            logger.error(f"保存基本面数据失败: {e}")
            raise
        
        return total_saved
    
    def _convert_to_models(self, raw_data: List[Dict[str, Any]], data_type: str) -> List:
        """将原始数据转换为数据模型
        
        Args:
            raw_data: 原始数据列表
            data_type: 数据类型 ('balance', 'income', 'cashflow')
        
        Returns:
            数据模型列表
        """
        models = []
        
        for record in raw_data:
            try:
                if data_type == 'balance':
                    model = data_model_service.create_balance_sheet(record)
                elif data_type == 'income':
                    model = data_model_service.create_income_statement(record)
                elif data_type == 'cashflow':
                    model = data_model_service.create_cash_flow_statement(record)
                else:
                    continue
                
                if model:
                    models.append(model)
                    
            except Exception as e:
                logger.error(f"转换数据模型失败: {e}")
                continue
        
        return models
    
    def _save_batch_data(self, collection, data: List[Dict[str, Any]]) -> int:
        """批量保存数据到指定集合
        
        Args:
            collection: MongoDB集合对象
            data: 要保存的数据列表
        
        Returns:
            实际保存的记录数
        """
        if not data:
            return 0
        
        try:
            # 使用upsert模式，避免重复数据
            saved_count = 0
            for record in data:
                # 构建查询条件（股票代码 + 报告日期 + 报告类型）
                query = {
                    'symbol': record['symbol'],
                    'end_date': record['end_date'],
                    'rpt_type': record['rpt_type'],
                    'data_type': record['data_type']
                }
                
                # 更新或插入数据
                result = collection.update_one(
                    query,
                    {'$set': record},
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    saved_count += 1
            
            return saved_count
            
        except Exception as e:
            logger.error(f"批量保存数据失败: {e}")
            return 0
    
    def get_latest_fundamentals(self, symbol: str, 
                              table_type: str = 'all') -> Dict[str, Any]:
        """获取股票最新的基本面数据
        
        Args:
            symbol: 股票代码
            table_type: 表类型 'balance'/'income'/'cashflow'/'all'
        
        Returns:
            最新基本面数据
        """
        result = {}
        
        try:
            if table_type in ['balance', 'all']:
                collection = self.db_manager.get_collection(self.data_config.fundamentals_balance_collection)
                latest_balance = collection.find_one(
                    {'symbol': symbol},
                    sort=[('end_date', -1)]
                )
                result['balance'] = latest_balance
            
            if table_type in ['income', 'all']:
                collection = self.db_manager.get_collection(self.data_config.fundamentals_income_collection)
                latest_income = collection.find_one(
                    {'symbol': symbol},
                    sort=[('end_date', -1)]
                )
                result['income'] = latest_income
            
            if table_type in ['cashflow', 'all']:
                collection = self.db_manager.get_collection(self.data_config.fundamentals_cashflow_collection)
                latest_cashflow = collection.find_one(
                    {'symbol': symbol},
                    sort=[('end_date', -1)]
                )
                result['cashflow'] = latest_cashflow
            
        except Exception as e:
            logger.error(f"获取最新基本面数据失败 {symbol}: {e}")
        
        return result
    
    def get_valid_fields(self) -> Dict[str, List[str]]:
        """获取已验证的有效字段列表
        
        Returns:
            有效字段字典
        """
        return {k: v['fields'] for k, v in self.valid_fields.items()}
    
    def cleanup_old_data(self, days_to_keep: int = None):
        """清理过期的基本面数据
        
        Args:
            days_to_keep: 保留天数，默认使用配置文件设置
        """
        if days_to_keep is None:
            days_to_keep = self.data_config.fundamentals_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            # 清理各个基本面数据集合
            collections = [
                self.data_config.fundamentals_balance_collection,
                self.data_config.fundamentals_income_collection,
                self.data_config.fundamentals_cashflow_collection
            ]
            
            total_deleted = 0
            for collection_name in collections:
                deleted_count = self.db_manager.delete_old_data(
                    collection_name, 
                    cutoff_date
                )
                total_deleted += deleted_count
                logger.info(f"清理{collection_name}过期数据: {deleted_count}条")
            
            logger.info(f"基本面数据清理完成，共删除{total_deleted}条记录")
            
        except Exception as e:
            logger.error(f"清理基本面数据失败: {e}")
    
    def create_indexes(self):
        """创建数据库索引以提高查询性能"""
        try:
            collections = [
                self.data_config.fundamentals_balance_collection,
                self.data_config.fundamentals_income_collection,
                self.data_config.fundamentals_cashflow_collection
            ]
            
            for collection_name in collections:
                # 创建复合索引
                indexes = [
                    [('symbol', 1), ('end_date', -1)],  # 股票代码 + 报告日期
                    [('symbol', 1), ('pub_date', -1)],  # 股票代码 + 发布日期
                    [('end_date', -1)],  # 报告日期
                    [('created_at', -1)]  # 创建时间
                ]
                
                for index in indexes:
                    self.db_manager.create_index(collection_name, index)
                
                logger.info(f"为{collection_name}创建索引完成")
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
    
    def disconnect(self):
        """断开连接（兼容性方法）"""
        try:
            if self.db_manager:
                self.db_manager.disconnect()
            if self.gm_client and hasattr(self.gm_client, 'is_connected'):
                self.gm_client.disconnect()
            logger.info("基本面数据采集器已断开连接")
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        try:
            if self.db_manager:
                self.db_manager.disconnect()
            if self.gm_client and hasattr(self.gm_client, 'is_connected'):
                self.gm_client.disconnect()
        except Exception as e:
            logger.error(f"关闭连接失败: {e}")


# 创建全局实例
fundamentals_collector = FundamentalsDataCollector()


if __name__ == "__main__":
    # 测试代码
    try:
        from config import config
        
        # 从配置文件读取测试股票代码
        test_symbols = config.scheduler.stock_symbols or ['SHSE.600000', 'SZSE.000001']  # 默认测试股票
        
        print(f"使用配置的股票代码: {test_symbols}")
        print(f"MongoDB配置: {config.mongodb.connection_string}")
        print(f"GM SDK配置: {config.gm_sdk.token[:10]}...")
        
        with FundamentalsDataCollector() as collector:
            # 创建索引
            collector.create_indexes()
            
            # 采集基本面数据
            results = collector.collect_fundamentals_data(
                symbols=test_symbols,
                start_date='2023-01-01',
                end_date='2023-12-31'
            )
            
            print(f"采集结果: {results}")
            
            # 获取最新数据
            for symbol in test_symbols:
                latest_data = collector.get_latest_fundamentals(symbol)
                print(f"{symbol}最新基本面数据: {latest_data}")
            
            # 显示有效字段
            valid_fields = collector.get_valid_fields()
            print("\n=== 已验证的有效字段 ===")
            for table, fields in valid_fields.items():
                print(f"{table}: {fields}")
                
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
