#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型服务
提供各种数据模型的创建、验证和转换功能
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import ValidationError

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models import (
    StockQuote, BidAskQuote, BalanceSheet, IncomeStatement, 
    CashFlowStatement, Tick, Bar, QuoteLevel, FullStockData
)
from utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class DataModelService:
    """数据模型服务 - 负责数据模型的创建、验证和转换"""
    
    def __init__(self):
        """初始化数据模型服务"""
        self.logger = logger
    
    def create_stock_quote(self, data: Dict[str, Any]) -> Optional[StockQuote]:
        """创建股票报价数据模型
        
        Args:
            data: 原始数据字典
        
        Returns:
            StockQuote模型实例，如果创建失败则返回None
        """
        try:
            # 数据预处理和字段映射
            processed_data = self._process_stock_quote_data(data)
            
            # 创建模型实例
            quote = StockQuote(**processed_data)
            return quote
            
        except ValidationError as e:
            logger.error(f"创建StockQuote模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建StockQuote模型时发生异常: {e}")
            return None
    
    def create_bid_ask_quote(self, data: Dict[str, Any]) -> Optional[BidAskQuote]:
        """创建买卖盘口数据模型
        
        Args:
            data: 原始数据字典
        
        Returns:
            BidAskQuote模型实例，如果创建失败则返回None
        """
        try:
            # 数据预处理和字段映射
            processed_data = self._process_bid_ask_data(data)
            
            # 创建模型实例
            quote = BidAskQuote(**processed_data)
            return quote
            
        except ValidationError as e:
            logger.error(f"创建BidAskQuote模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建BidAskQuote模型时发生异常: {e}")
            return None
    
    def create_balance_sheet(self, data: Dict[str, Any]) -> Optional[BalanceSheet]:
        """创建资产负债表数据模型
        
        Args:
            data: 原始数据字典
        
        Returns:
            BalanceSheet模型实例，如果创建失败则返回None
        """
        try:
            # 数据预处理和字段映射
            processed_data = self._process_balance_sheet_data(data)
            
            # 创建模型实例
            balance_sheet = BalanceSheet(**processed_data)
            return balance_sheet
            
        except ValidationError as e:
            logger.error(f"创建BalanceSheet模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建BalanceSheet模型时发生异常: {e}")
            return None
    
    def create_income_statement(self, data: Dict[str, Any]) -> Optional[IncomeStatement]:
        """创建利润表数据模型
        
        Args:
            data: 原始数据字典
        
        Returns:
            IncomeStatement模型实例，如果创建失败则返回None
        """
        try:
            # 数据预处理和字段映射
            processed_data = self._process_income_statement_data(data)
            
            # 创建模型实例
            income_statement = IncomeStatement(**processed_data)
            return income_statement
            
        except ValidationError as e:
            logger.error(f"创建IncomeStatement模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建IncomeStatement模型时发生异常: {e}")
            return None
    
    def create_cash_flow_statement(self, data: Dict[str, Any]) -> Optional[CashFlowStatement]:
        """创建现金流量表数据模型
        
        Args:
            data: 原始数据字典
        
        Returns:
            CashFlowStatement模型实例，如果创建失败则返回None
        """
        try:
            # 数据预处理和字段映射
            processed_data = self._process_cash_flow_statement_data(data)
            
            # 创建模型实例
            cash_flow_statement = CashFlowStatement(**processed_data)
            return cash_flow_statement
            
        except ValidationError as e:
            logger.error(f"创建CashFlowStatement模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建CashFlowStatement模型时发生异常: {e}")
            return None
    
    def create_tick(self, data: Dict[str, Any]) -> Optional[Tick]:
        """创建Tick数据模型
        
        Args:
            data: 原始数据字典
        
        Returns:
            Tick模型实例，如果创建失败则返回None
        """
        try:
            # 数据预处理和字段映射
            processed_data = self._process_tick_data(data)
            
            # 创建模型实例
            tick = Tick(**processed_data)
            return tick
            
        except ValidationError as e:
            logger.error(f"创建Tick模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建Tick模型时发生异常: {e}")
            return None
    
    def create_bar(self, data: Dict[str, Any]) -> Optional[Bar]:
        """创建Bar数据模型
        
        Args:
            data: 原始数据字典
        
        Returns:
            Bar模型实例，如果创建失败则返回None
        """
        try:
            # 数据预处理和字段映射
            processed_data = self._process_bar_data(data)
            
            # 创建模型实例
            bar = Bar(**processed_data)
            return bar
            
        except ValidationError as e:
            logger.error(f"创建Bar模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建Bar模型时发生异常: {e}")
            return None
    
    def create_full_stock_data(self, data: Dict[str, Any]) -> Optional[FullStockData]:
        """创建完整股票数据模型
        
        Args:
            data: 原始数据字典
        
        Returns:
            FullStockData模型实例，如果创建失败则返回None
        """
        try:
            # 数据预处理和字段映射
            processed_data = self._process_full_stock_data(data)
            
            # 创建模型实例
            full_stock_data = FullStockData(**processed_data)
            return full_stock_data
            
        except ValidationError as e:
            logger.error(f"创建FullStockData模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建FullStockData模型时发生异常: {e}")
            return None
    
    def validate_model(self, model_instance) -> bool:
        """验证数据模型是否有效
        
        Args:
            model_instance: 数据模型实例
        
        Returns:
            是否有效
        """
        try:
            if hasattr(model_instance, 'model_validate'):
                # Pydantic v2
                model_instance.model_validate(model_instance.dict())
            else:
                # Pydantic v1
                model_instance.validate(model_instance.dict())
            return True
        except Exception as e:
            logger.error(f"模型验证失败: {e}")
            return False
    
    def convert_to_dict(self, model_instance) -> Optional[Dict[str, Any]]:
        """将数据模型转换为字典
        
        Args:
            model_instance: 数据模型实例
        
        Returns:
            字典数据，如果转换失败则返回None
        """
        try:
            if hasattr(model_instance, 'model_dump'):
                # Pydantic v2
                return model_instance.model_dump()
            else:
                # Pydantic v1
                return model_instance.dict()
        except Exception as e:
            logger.error(f"模型转换为字典失败: {e}")
            return None
    
    def _process_stock_quote_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理股票报价数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            处理后的数据字典
        """
        processed = {}
        
        # 基础字段映射
        field_mapping = {
            'symbol': 'symbol',
            'price': 'price',
            'change': 'change',
            'change_pct': 'change_pct',
            'volume': 'volume',
            'amount': 'amount',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'prev_close': 'prev_close',
            'timestamp': 'timestamp'
        }
        
        for source_field, target_field in field_mapping.items():
            if source_field in data and data[source_field] is not None:
                processed[target_field] = data[source_field]
        
        # 添加默认值
        if 'timestamp' not in processed:
            processed['timestamp'] = datetime.now()
        
        return processed
    
    def _process_bid_ask_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理买卖盘口数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            处理后的数据字典
        """
        processed = {}
        
        # 基础字段映射
        field_mapping = {
            'bid_p': 'bid_price',
            'bid_v': 'bid_volume',
            'ask_p': 'ask_price',
            'ask_v': 'ask_volume',
            'level': 'level'
        }
        
        for source_field, target_field in field_mapping.items():
            if source_field in data and data[source_field] is not None:
                processed[target_field] = data[source_field]
        
        # 添加默认值
        if 'level' not in processed:
            processed['level'] = 1
        
        return processed
    
    def _process_balance_sheet_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理资产负债表数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            处理后的数据字典
        """
        processed = {}
        
        # 基础字段映射
        field_mapping = {
            'symbol': 'symbol',
            'end_date': 'end_date',
            'pub_date': 'pub_date',
            'rpt_type': 'rpt_type',
            'data_type': 'data_type',
            'cash_bal_cb': 'cash_bal_cb',
            'mny_cptl': 'mny_cptl',
            'bal_clr': 'bal_clr',
            'ppay': 'ppay',
            'note_rcv': 'note_rcv',
            'acct_rcv': 'acct_rcv',
            'oth_rcv': 'oth_rcv',
            'oth_cur_ast': 'oth_cur_ast',
            'fix_ast': 'fix_ast',
            'acct_pay': 'acct_pay',
            'tax_pay': 'tax_pay',
            'int_pay': 'int_pay',
            'oth_pay': 'oth_pay',
            'paid_in_cptl': 'paid_in_cptl',
            'cptl_rsv': 'cptl_rsv'
        }
        
        for source_field, target_field in field_mapping.items():
            if source_field in data and data[source_field] is not None:
                processed[target_field] = data[source_field]
        
        # 添加默认值
        if 'created_at' not in processed:
            processed['created_at'] = datetime.now()
        
        return processed
    
    def _process_income_statement_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理利润表数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            处理后的数据字典
        """
        processed = {}
        
        # 基础字段映射
        field_mapping = {
            'symbol': 'symbol',
            'end_date': 'end_date',
            'pub_date': 'pub_date',
            'rpt_type': 'rpt_type',
            'data_type': 'data_type'
        }
        
        for source_field, target_field in field_mapping.items():
            if source_field in data and data[source_field] is not None:
                processed[target_field] = data[source_field]
        
        # 添加默认值
        if 'created_at' not in processed:
            processed['created_at'] = datetime.now()
        
        return processed
    
    def _process_cash_flow_statement_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理现金流量表数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            处理后的数据字典
        """
        processed = {}
        
        # 基础字段映射
        field_mapping = {
            'symbol': 'symbol',
            'end_date': 'end_date',
            'pub_date': 'pub_date',
            'rpt_type': 'rpt_type',
            'data_type': 'data_type',
            'net_cf_oper': 'net_cf_oper',
            'cash_pay_tax': 'cash_pay_tax',
            'net_cf_inv': 'net_cf_inv',
            'net_cf_fin': 'net_cf_fin'
        }
        
        for source_field, target_field in field_mapping.items():
            if source_field in data and data[source_field] is not None:
                processed[target_field] = data[source_field]
        
        # 添加默认值
        if 'created_at' not in processed:
            processed['created_at'] = datetime.now()
        
        return processed
    
    def _process_tick_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Tick数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            处理后的数据字典
        """
        processed = {}
        
        # 基础字段映射
        field_mapping = {
            'symbol': 'symbol',
            'price': 'price',
            'volume': 'volume',
            'amount': 'amount',
            'timestamp': 'timestamp',
            'bid_p': 'bid_price',
            'ask_p': 'ask_price',
            'bid_v': 'bid_volume',
            'ask_v': 'ask_volume'
        }
        
        for source_field, target_field in field_mapping.items():
            if source_field in data and data[source_field] is not None:
                processed[target_field] = data[source_field]
        
        # 添加默认值
        if 'timestamp' not in processed:
            processed['timestamp'] = datetime.now()
        
        return processed
    
    def _process_bar_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Bar数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            处理后的数据字典
        """
        processed = {}
        
        # 基础字段映射
        field_mapping = {
            'symbol': 'symbol',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'amount': 'amount',
            'bob': 'bob',
            'eob': 'eob',
            'frequency': 'frequency'
        }
        
        for source_field, target_field in field_mapping.items():
            if source_field in data and data[source_field] is not None:
                processed[target_field] = data[source_field]
        
        # 添加默认值
        if 'frequency' not in processed:
            processed['frequency'] = '1d'
        
        return processed
    
    def _process_full_stock_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理完整股票数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            处理后的数据字典
        """
        processed = {}
        
        # 基础字段映射
        field_mapping = {
            'symbol': 'symbol',
            'price': 'price',
            'change': 'change',
            'change_pct': 'change_pct',
            'volume': 'volume',
            'amount': 'amount',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'prev_close': 'prev_close',
            'timestamp': 'timestamp'
        }
        
        for source_field, target_field in field_mapping.items():
            if source_field in data and data[source_field] is not None:
                processed[target_field] = data[source_field]
        
        # 处理买卖盘口数据
        if 'quotes' in data and data['quotes']:
            processed['quotes'] = []
            for quote_data in data['quotes']:
                quote = self.create_bid_ask_quote(quote_data)
                if quote:
                    processed['quotes'].append(quote)
        
        # 添加默认值
        if 'timestamp' not in processed:
            processed['timestamp'] = datetime.now()
        
        return processed


# 创建全局实例
data_model_service = DataModelService()


if __name__ == "__main__":
    """测试数据模型服务"""
    service = DataModelService()
    
    print("🚀 数据模型服务测试")
    print("=" * 50)
    
    # 测试创建各种模型
    test_data = {
        'symbol': 'SZSE.000001',
        'price': 10.50,
        'change': 0.25,
        'change_pct': 2.44,
        'volume': 1000000,
        'amount': 10500000
    }
    
    # 测试创建股票报价模型
    print("\n1️⃣ 测试创建股票报价模型...")
    stock_quote = service.create_stock_quote(test_data)
    if stock_quote:
        print(f"✅ 成功创建StockQuote模型: {stock_quote.symbol}, 价格: {stock_quote.price}")
        print(f"   涨跌幅: {stock_quote.change_pct}%")
    else:
        print("❌ 创建StockQuote模型失败")
    
    # 测试创建买卖盘口模型
    print("\n2️⃣ 测试创建买卖盘口模型...")
    bid_ask_data = {
        'bid_p': 10.49,
        'bid_v': 50000,
        'ask_p': 10.51,
        'ask_v': 45000,
        'level': 1
    }
    bid_ask_quote = service.create_bid_ask_quote(bid_ask_data)
    if bid_ask_quote:
        print(f"✅ 成功创建BidAskQuote模型: 买价{bid_ask_quote.bid_price}, 卖价{bid_ask_quote.ask_price}")
        print(f"   买量: {bid_ask_quote.bid_volume}, 卖量: {bid_ask_quote.ask_volume}")
    else:
        print("❌ 创建BidAskQuote模型失败")
    
    # 测试模型验证
    print("\n3️⃣ 测试模型验证...")
    if stock_quote and service.validate_model(stock_quote):
        print("✅ StockQuote模型验证通过")
    else:
        print("❌ StockQuote模型验证失败")
    
    # 测试模型转换
    print("\n4️⃣ 测试模型转换...")
    if stock_quote:
        dict_data = service.convert_to_dict(stock_quote)
        if dict_data:
            print(f"✅ 模型转换成功: {dict_data}")
        else:
            print("❌ 模型转换失败")
    
    print("\n🎉 数据模型服务测试完成！")
