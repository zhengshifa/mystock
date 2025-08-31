#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本面数据模型
定义财务报表相关的所有数据结构
"""

from pydantic import Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from .base import TimestampedModel, IdentifiableModel, AppBaseModel


class BalanceSheet(TimestampedModel):
    """资产负债表数据模型"""
    
    symbol: str = Field(..., description="股票代码")
    end_date: Optional[str] = Field("", description="报告期末")
    pub_date: str = Field(..., description="发布日期")
    rpt_type: int = Field(0, description="报告类型 0-合并报表 1-母公司报表")
    data_type: int = Field(0, description="数据类型 0-原始数据 1-单季度数据")
    
    # 流动资产
    cash_bal_cb: Optional[float] = Field(None, description="现金及存放中央银行款项")
    mny_cptl: Optional[float] = Field(None, description="货币资金")
    bal_clr: Optional[float] = Field(None, description="结算备付金")
    ppay: Optional[float] = Field(None, description="预付款项")
    note_rcv: Optional[float] = Field(None, description="应收票据")
    acct_rcv: Optional[float] = Field(None, description="应收账款")
    oth_rcv: Optional[float] = Field(None, description="其他应收款")
    oth_cur_ast: Optional[float] = Field(None, description="其他流动资产")
    
    # 非流动资产
    fix_ast: Optional[float] = Field(None, description="固定资产")
    oth_ast: Optional[float] = Field(None, description="其他资产")
    
    # 流动负债
    acct_pay: Optional[float] = Field(None, description="应付账款")
    tax_pay: Optional[float] = Field(None, description="应交税费")
    int_pay: Optional[float] = Field(None, description="应付利息")
    oth_pay: Optional[float] = Field(None, description="其他应付款")
    oth_liab: Optional[float] = Field(None, description="其他负债")
    
    # 所有者权益
    paid_in_cptl: Optional[float] = Field(None, description="实收资本")
    cptl_rsv: Optional[float] = Field(None, description="资本公积")
    
    # 计算字段
    total_assets: Optional[float] = Field(None, description="总资产")
    total_liabilities: Optional[float] = Field(None, description="总负债")
    net_assets: Optional[float] = Field(None, description="净资产")
    
    @field_validator('end_date', 'pub_date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        if not v:  # 允许空字符串或None
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('日期格式必须为YYYY-MM-DD')
    
    @field_validator('rpt_type')
    @classmethod
    def validate_rpt_type(cls, v):
        """验证报告类型"""
        # 扩展允许的报告类型值
        if v not in [0, 1, 6, 9, 12]:  # 0-合并报表 1-母公司报表 6-半年报 9-三季度报 12-年报
            raise ValueError('报告类型必须为0(合并报表)、1(母公司报表)、6(半年报)、9(三季度报)或12(年报)')
        return v
    
    @field_validator('data_type')
    @classmethod
    def validate_data_type(cls, v):
        """验证数据类型"""
        # 扩展允许的数据类型值
        if v not in [0, 1, 100]:  # 0-原始数据 1-单季度数据 100-其他类型
            raise ValueError('数据类型必须为0(原始数据)、1(单季度数据)或100(其他类型)')
        return v


class IncomeStatement(TimestampedModel):
    """利润表数据模型"""
    
    symbol: str = Field(..., description="股票代码")
    end_date: Optional[str] = Field("", description="报告期末")
    pub_date: str = Field(..., description="发布日期")
    rpt_type: int = Field(0, description="报告类型 0-合并报表 1-母公司报表")
    data_type: int = Field(0, description="数据类型 0-原始数据 1-单季度数据")
    
    # 营业收入
    revenue: Optional[float] = Field(None, description="营业收入")
    operating_revenue: Optional[float] = Field(None, description="营业总收入")
    
    # 营业成本
    cost_of_revenue: Optional[float] = Field(None, description="营业成本")
    operating_cost: Optional[float] = Field(None, description="营业总成本")
    
    # 营业利润
    operating_profit: Optional[float] = Field(None, description="营业利润")
    gross_profit: Optional[float] = Field(None, description="毛利润")
    
    # 利润总额
    total_profit: Optional[float] = Field(None, description="利润总额")
    net_profit: Optional[float] = Field(None, description="净利润")
    
    # 每股指标
    eps: Optional[float] = Field(None, description="每股收益")
    diluted_eps: Optional[float] = Field(None, description="稀释每股收益")
    
    @field_validator('end_date', 'pub_date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        if not v:  # 允许空字符串或None
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('日期格式必须为YYYY-MM-DD')
    
    @field_validator('rpt_type')
    @classmethod
    def validate_rpt_type(cls, v):
        """验证报告类型"""
        # 扩展允许的报告类型值
        if v not in [0, 1, 6, 9, 12]:  # 0-合并报表 1-母公司报表 6-半年报 9-三季度报 12-年报
            raise ValueError('报告类型必须为0(合并报表)、1(母公司报表)、6(半年报)、9(三季度报)或12(年报)')
        return v
    
    @field_validator('data_type')
    @classmethod
    def validate_data_type(cls, v):
        """验证数据类型"""
        # 扩展允许的数据类型值
        if v not in [0, 1, 100]:  # 0-原始数据 1-单季度数据 100-其他类型
            raise ValueError('数据类型必须为0(原始数据)、1(单季度数据)或100(其他类型)')
        return v


class CashFlowStatement(TimestampedModel):
    """现金流量表数据模型"""
    
    symbol: str = Field(..., description="股票代码")
    end_date: Optional[str] = Field("", description="报告期末")
    pub_date: str = Field(..., description="发布日期")
    rpt_type: int = Field(0, description="报告类型 0-合并报表 1-母公司报表")
    data_type: int = Field(0, description="数据类型 0-原始数据 1-单季度数据")
    
    # 经营活动现金流量
    net_cf_oper: Optional[float] = Field(None, description="经营活动产生的现金流量净额")
    cash_pay_tax: Optional[float] = Field(None, description="支付的各项税费")
    
    # 投资活动现金流量
    net_cf_inv: Optional[float] = Field(None, description="投资活动产生的现金流量净额")
    
    # 筹资活动现金流量
    net_cf_fin: Optional[float] = Field(None, description="筹资活动产生的现金流量净额")
    
    # 现金及现金等价物
    cash_equivalents: Optional[float] = Field(None, description="现金及现金等价物净增加额")
    
    @field_validator('end_date', 'pub_date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        if not v:  # 允许空字符串或None
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('日期格式必须为YYYY-MM-DD')
    
    @field_validator('rpt_type')
    @classmethod
    def validate_rpt_type(cls, v):
        """验证报告类型"""
        # 扩展允许的报告类型值
        if v not in [0, 1, 6, 9, 12]:  # 0-合并报表 1-母公司报表 6-半年报 9-三季度报 12-年报
            raise ValueError('报告类型必须为0(合并报表)、1(母公司报表)、6(半年报)、9(三季度报)或12(年报)')
        return v
    
    @field_validator('data_type')
    @classmethod
    def validate_data_type(cls, v):
        """验证数据类型"""
        # 扩展允许的数据类型值
        if v not in [0, 1, 100]:  # 0-原始数据 1-单季度数据 100-其他类型
            raise ValueError('数据类型必须为0(原始数据)、1(单季度数据)或100(其他类型)')
        return v


class FundamentalsData(AppBaseModel):
    """基本面数据集合模型"""
    
    symbol: str = Field(..., description="股票代码")
    report_date: str = Field(..., description="报告日期")
    
    # 三张表数据
    balance_sheet: Optional[BalanceSheet] = Field(None, description="资产负债表")
    income_statement: Optional[IncomeStatement] = Field(None, description="利润表")
    cash_flow_statement: Optional[CashFlowStatement] = Field(None, description="现金流量表")
    
    # 财务指标
    financial_ratios: Optional[Dict[str, float]] = Field(
        default_factory=dict, 
        description="财务比率"
    )
    
    @field_validator('report_date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('日期格式必须为YYYY-MM-DD')
    
    def calculate_financial_ratios(self) -> Dict[str, float]:
        """计算财务比率"""
        ratios = {}
        
        if self.balance_sheet:
            bs = self.balance_sheet
            if bs.total_assets and bs.total_assets > 0:
                if bs.net_assets:
                    ratios['debt_to_equity'] = (bs.total_assets - bs.net_assets) / bs.net_assets
                if bs.acct_rcv:
                    ratios['receivables_turnover'] = bs.acct_rcv / bs.total_assets
        
        if self.income_statement:
            is_stmt = self.income_statement
            if is_stmt.revenue and is_stmt.revenue > 0:
                if is_stmt.net_profit:
                    ratios['net_profit_margin'] = is_stmt.net_profit / is_stmt.revenue
                if is_stmt.gross_profit:
                    ratios['gross_profit_margin'] = is_stmt.gross_profit / is_stmt.revenue
        
        return ratios


class FinancialIndicator(AppBaseModel):
    """财务指标模型"""
    
    symbol: str = Field(..., description="股票代码")
    date: str = Field(..., description="指标日期")
    
    # 估值指标
    pe_ratio: Optional[float] = Field(None, description="市盈率", ge=0)
    pb_ratio: Optional[float] = Field(None, description="市净率", ge=0)
    ps_ratio: Optional[float] = Field(None, description="市销率", ge=0)
    pcf_ratio: Optional[float] = Field(None, description="市现率", ge=0)
    
    # 盈利能力指标
    roe: Optional[float] = Field(None, description="净资产收益率(%)", ge=-100, le=100)
    roa: Optional[float] = Field(None, description="总资产收益率(%)", ge=-100, le=100)
    gross_margin: Optional[float] = Field(None, description="毛利率(%)", ge=-100, le=100)
    net_margin: Optional[float] = Field(None, description="净利率(%)", ge=-100, le=100)
    
    # 成长性指标
    revenue_growth: Optional[float] = Field(None, description="营收增长率(%)", ge=-1000, le=1000)
    profit_growth: Optional[float] = Field(None, description="净利润增长率(%)", ge=-1000, le=1000)
    
    # 运营能力指标
    asset_turnover: Optional[float] = Field(None, description="总资产周转率", ge=0)
    inventory_turnover: Optional[float] = Field(None, description="存货周转率", ge=0)
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('日期格式必须为YYYY-MM-DD')
    
    @field_validator('pe_ratio', 'pb_ratio', 'ps_ratio', 'pcf_ratio')
    @classmethod
    def validate_positive_ratios(cls, v):
        """验证比率为正数"""
        if v is not None and v < 0:
            raise ValueError('估值比率不能为负数')
        return v


class FundamentalsScreeningCriteria(AppBaseModel):
    """基本面数据筛选条件模型"""
    
    # 财务指标条件
    min_pe_ratio: Optional[float] = Field(None, description="最小市盈率", ge=0)
    max_pe_ratio: Optional[float] = Field(None, description="最大市盈率", ge=0)
    min_pb_ratio: Optional[float] = Field(None, description="最小市净率", ge=0)
    max_pb_ratio: Optional[float] = Field(None, description="最大市净率", ge=0)
    
    # 盈利能力条件
    min_roe: Optional[float] = Field(None, description="最小净资产收益率(%)", ge=-100)
    max_roe: Optional[float] = Field(None, description="最大净资产收益率(%)", le=100)
    min_gross_margin: Optional[float] = Field(None, description="最小毛利率(%)", ge=-100)
    max_gross_margin: Optional[float] = Field(None, description="最大毛利率(%)", le=100)
    
    # 成长性条件
    min_revenue_growth: Optional[float] = Field(None, description="最小营收增长率(%)", ge=-1000)
    max_revenue_growth: Optional[float] = Field(None, description="最大营收增长率(%)", le=1000)
    min_profit_growth: Optional[float] = Field(None, description="最小净利润增长率(%)", ge=-1000)
    max_profit_growth: Optional[float] = Field(None, description="最大净利润增长率(%)", le=1000)
    
    # 报告类型条件
    rpt_types: Optional[List[int]] = Field(None, description="指定报告类型")
    data_types: Optional[List[int]] = Field(None, description="指定数据类型")
    
    @field_validator('max_pe_ratio')
    @classmethod
    def max_pe_must_be_higher_than_min(cls, v, info):
        """验证最大市盈率必须高于最小市盈率"""
        if v is not None and 'min_pe_ratio' in info.data and info.data['min_pe_ratio'] is not None:
            if v <= info.data['min_pe_ratio']:
                raise ValueError('最大市盈率必须高于最小市盈率')
        return v
    
    @field_validator('max_pb_ratio')
    @classmethod
    def max_pb_must_be_higher_than_min(cls, v, info):
        """验证最大市净率必须高于最小市净率"""
        if v is not None and 'min_pb_ratio' in info.data and info.data['min_pb_ratio'] is not None:
            if v <= info.data['min_pb_ratio']:
                raise ValueError('最大市净率必须高于最小市净率')
        return v
