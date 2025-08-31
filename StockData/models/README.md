# 数据模型层 (Data Models Layer)

## 概述

数据模型层为整个股票数据项目提供了统一、类型安全的数据结构定义。使用Pydantic框架构建，确保数据验证、序列化和反序列化的可靠性。

## 架构设计

### 基础模型类

- **`AppBaseModel`**: 所有模型的基类，提供通用功能
- **`TimestampedModel`**: 带时间戳的模型基类
- **`IdentifiableModel`**: 可识别的模型基类

### 核心功能

- **数据验证**: 自动验证字段类型、范围和业务规则
- **序列化**: 支持字典和JSON格式的转换
- **类型安全**: 完整的类型注解和IDE支持
- **文档化**: 每个字段都有详细的中文描述

## 模型分类

### 1. 股票数据模型 (`models/stock.py`)

#### 基础行情数据
- **`StockQuote`**: 股票基础行情数据
- **`BidAskQuote`**: 买卖盘口数据
- **`FullStockData`**: 完整股票数据（包含行情和盘口）

#### 历史数据
- **`StockKlineData`**: K线数据模型
- **`StockTickData`**: 逐笔数据模型

#### 基础信息
- **`StockBasicInfo`**: 股票基本信息
- **`StockScreeningCriteria`**: 股票筛选条件

### 2. 基本面数据模型 (`models/fundamentals.py`)

#### 财务报表
- **`BalanceSheet`**: 资产负债表
- **`IncomeStatement`**: 利润表
- **`CashFlowStatement`**: 现金流量表

#### 财务指标
- **`FinancialIndicator`**: 财务指标模型
- **`FundamentalsData`**: 基本面数据集合
- **`FundamentalsScreeningCriteria`**: 基本面筛选条件

### 3. 市场数据模型 (`models/market.py`)

#### 市场状态
- **`MarketStatus`**: 市场状态枚举
- **`TradingSession`**: 交易时段
- **`MarketSchedule`**: 市场交易时间表

#### 市场数据
- **`MarketData`**: 市场统计数据
- **`MarketIndex`**: 市场指数
- **`MarketAlert`**: 市场预警
- **`MarketNews`**: 市场新闻

## 使用方法

### 基本使用

```python
from models import StockQuote, BalanceSheet, MarketData

# 创建股票行情数据
quote = StockQuote(
    symbol="SHSE.600000",
    open=10.50,
    high=10.80,
    low=10.45,
    price=10.60,
    pre_close=10.50,
    cum_volume=1000000,
    cum_amount=10600000.0
)

# 数据会自动计算涨跌额和涨跌幅
print(f"涨跌额: {quote.change}")
print(f"涨跌幅: {quote.change_pct}%")
```

### 数据验证

```python
from models import StockBasicInfo

try:
    # 有效的股票代码
    info = StockBasicInfo(
        symbol="SHSE.600000",
        name="浦发银行",
        exchange="SHSE",
        market="主板"
    )
    print("✓ 验证通过")
except ValueError as e:
    print(f"✗ 验证失败: {e}")
```

### 序列化

```python
from models import StockQuote

# 创建数据
quote = StockQuote(
    symbol="SHSE.600000",
    open=10.50,
    high=10.80,
    low=10.45,
    price=10.60,
    pre_close=10.50,
    cum_volume=1000000,
    cum_amount=10600000.0
)

# 转换为字典
data_dict = quote.to_dict()

# 转换为JSON
json_str = quote.to_json()

# 从字典恢复
restored = StockQuote.from_dict(data_dict)

# 从JSON恢复
restored_from_json = StockQuote.from_json(json_str)
```

### 筛选条件

```python
from models import StockScreeningCriteria, FundamentalsScreeningCriteria

# 股票筛选条件
stock_criteria = StockScreeningCriteria(
    min_price=5.0,
    max_price=50.0,
    min_change_pct=-10.0,
    max_change_pct=10.0,
    exchanges=["SHSE", "SZSE"]
)

# 基本面筛选条件
fundamental_criteria = FundamentalsScreeningCriteria(
    min_pe_ratio=5.0,
    max_pe_ratio=30.0,
    min_roe=8.0,
    max_roe=25.0
)
```

## 数据验证规则

### 股票代码格式
- 必须以 `SHSE.` 或 `SZSE.` 开头
- 或者以 `.SH` 或 `.SZ` 结尾
- 总长度至少6位

### 价格字段
- 所有价格字段必须 ≥ 0
- 最高价必须 ≥ 开盘价、最低价、收盘价
- 最低价必须 ≤ 开盘价、最高价、收盘价

### 日期格式
- 所有日期字段必须为 `YYYY-MM-DD` 格式
- 自动验证日期有效性

### 财务指标
- 市盈率、市净率等估值指标必须 ≥ 0
- 收益率等百分比指标有合理范围限制

## 扩展指南

### 添加新模型

1. 在相应的模块文件中定义新类
2. 继承适当的基类（`AppBaseModel`、`TimestampedModel` 或 `IdentifiableModel`）
3. 使用 `Field` 定义字段，包含描述和验证规则
4. 在 `models/__init__.py` 中添加导入和导出
5. 更新 `__all__` 列表

### 添加验证器

```python
from pydantic import field_validator

class MyModel(AppBaseModel):
    field1: str
    field2: int
    
    @field_validator('field2')
    @classmethod
    def validate_field2(cls, v):
        if v < 0:
            raise ValueError('字段2不能为负数')
        return v
```

### 添加计算字段

```python
from pydantic import computed_field

class MyModel(AppBaseModel):
    field1: float
    field2: float
    
    @computed_field
    @property
    def computed_field(self) -> float:
        return self.field1 + self.field2
```

## 测试

运行测试脚本验证所有模型功能：

```bash
uv run python test_models.py
```

运行使用示例：

```bash
uv run python examples/model_usage_examples.py
```

## 依赖

- **Pydantic**: 数据验证和序列化框架
- **Python 3.12+**: 支持现代类型注解特性

## 注意事项

1. **性能**: 大量数据验证可能影响性能，建议在生产环境中适当调整验证级别
2. **内存**: 大型数据集序列化时注意内存使用
3. **兼容性**: 模型变更时注意向后兼容性
4. **文档**: 新增字段时务必添加清晰的中文描述

## 贡献

欢迎提交Issue和Pull Request来改进数据模型层。请确保：

1. 遵循现有的代码风格
2. 添加适当的测试用例
3. 更新相关文档
4. 所有测试通过
