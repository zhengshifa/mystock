# 掘金量化 GM SDK 数据接口测试项目

本项目包含了掘金量化 GM SDK 的完整数据接口探索和测试代码。

## 📋 项目结构

```
├── explore_gm_sdk.py              # SDK接口探索脚本
├── gm_api_functions.json          # 发现的205个API函数详情
├── gm_complete_exploration.json   # 完整的SDK结构信息
├── demo_1_history_data.py         # 历史行情数据测试
├── demo_2_realtime_data.py        # 实时行情数据测试
├── demo_3_basic_info.py           # 基础信息查询测试
├── demo_4_trading_calendar.py     # 交易日历查询测试
├── demo_5_sector_constituents.py  # 板块和成分股查询测试
├── demo_6_fundamentals.py         # 财务数据查询测试
├── demo_7_dragon_tiger_list.py    # 龙虎榜数据查询测试
├── demo_8_technical_indicators.py # 技术指标计算测试
├── demo_9_margin_trading.py       # 融资融券数据查询测试
├── demo_10_dividend_split.py      # 分红配股数据查询测试
├── demo_11_shareholder_data.py    # 股东数据查询测试
├── demo_12_options_data.py        # 期权数据查询测试
├── demo_13_ipo_data.py            # 新股申购数据查询测试
├── run_all_demos.py               # 批量运行所有demo
├── token_config_example.py        # Token配置示例
├── gm_config_template.json        # 配置文件模板
└── README.md                      # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install gm
pip install pandas
```

### 2. 配置Token

**重要：在运行任何demo之前，必须先配置有效的掘金量化API Token！**

#### 方法1：直接在代码中设置

```python
from gm.api import set_token
set_token('your_actual_token_here')
```

#### 方法2：使用配置文件（推荐）

1. 复制 `gm_config_template.json` 为 `gm_config.json`
2. 在 `gm_config.json` 中填入你的实际token：

```json
{
  "token": "your_actual_token_here"
}
```

#### 方法3：使用环境变量

```bash
# Windows
set GM_TOKEN=your_actual_token_here

# Linux/Mac
export GM_TOKEN=your_actual_token_here
```

### 3. 获取Token

1. 访问 [掘金量化官网](https://www.myquant.cn/)
2. 注册并登录账户
3. 进入个人中心或API管理页面
4. 申请或查看你的API Token
5. 复制Token并按上述方法配置

### 4. 运行测试

#### 运行单个demo

```bash
python demo_1_history_data.py
```

#### 批量运行所有demo

```bash
python run_all_demos.py
```

## 📊 数据接口分类

### 历史数据接口
- `history()` - 获取历史K线数据
- `history_n()` - 获取最近N条历史数据

### 实时数据接口
- `current()` - 获取实时行情快照
- `current_price()` - 获取实时价格

### 基础信息接口
- `get_instruments()` - 获取交易标的信息
- `get_symbol_infos()` - 获取标的详细信息
- `get_symbols()` - 获取交易日标的列表

### 交易日历接口
- `get_trading_dates()` - 获取交易日期
- `get_next_trading_date()` / `get_previous_trading_date()` - 获取下一个/上一个交易日

### 板块成分股接口
- `get_sector()` - 获取板块分类信息
- `get_index_constituents()` - 获取指数成分股
- `get_etf_constituents()` - 获取ETF成分股

### 财务数据接口
- `get_fundamentals()` - 获取财务基本面数据
- `fnd_get_nav()` - 获取基金净值
- `fnd_get_dividend()` - 获取分红信息

### 龙虎榜数据接口
- `stk_abnor_change_stocks()` - 获取龙虎榜股票列表
- `stk_abnor_change_detail()` - 获取龙虎榜营业部明细

### 技术指标计算
- 简单移动平均线 (SMA)
- 指数移动平均线 (EMA)
- MACD指标
- 相对强弱指数 (RSI)
- 布林带 (Bollinger Bands)
- KDJ指标
- 成交量平衡指标 (OBV)
- 成交量加权平均价格 (VWAP)

### 融资融券数据接口
- `credit_get_borrowable_instruments()` - 获取可融资标的
- `credit_get_cash()` - 获取融资融券资金信息
- `credit_get_collateral_instruments()` - 获取担保品信息
- `credit_get_contracts()` - 获取融资融券合约信息

### 分红配股数据接口
- `stk_get_dividend()` - 获取股票分红信息
- `stk_get_ration()` - 获取股票配股信息
- `stk_get_share_change()` - 获取股本变动信息
- `stk_get_adj_factor()` - 获取复权因子

### 股东数据接口
- `stk_get_top_shareholder()` - 获取十大股东信息
- `stk_get_shareholder_num()` - 获取股东户数信息
- `stk_hk_inst_holding_info()` - 获取港股通机构持股信息
- `stk_quota_shszhk_infos()` - 获取沪深港通额度信息

### 期权数据接口
- `option_calculate_delta()` - 计算期权Delta
- `option_calculate_gamma()` - 计算期权Gamma
- `option_calculate_theta()` - 计算期权Theta
- `option_calculate_vega()` - 计算期权Vega
- `option_calculate_rho()` - 计算期权Rho
- `option_calculate_iv()` - 计算隐含波动率
- `option_calculate_price()` - 计算期权理论价格

### 新股申购数据接口
- `ipo_get_instruments()` - 获取新股申购标的
- `ipo_get_quota()` - 获取新股申购额度
- `ipo_get_lot_info()` - 获取新股申购配号信息
- `ipo_get_match_number()` - 获取新股申购中签号码

## 📁 输出文件

每个demo运行后会生成：
- JSON格式的详细结果文件
- CSV格式的数据文件
- 汇总报告

## ⚠️ 注意事项

1. **Token安全**：请妥善保管你的API Token，不要在公开代码中硬编码
2. **调用限制**：Token可能有使用期限和调用次数限制
3. **网络连接**：确保网络连接正常，API调用需要访问掘金量化服务器
4. **数据权限**：不同的账户类型可能有不同的数据访问权限

## 🔧 故障排除

### 常见错误

1. **"错误或无效的token"**
   - 检查token是否正确配置
   - 确认token是否有效且未过期
   - 联系掘金量化客服确认账户状态

2. **网络连接错误**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试使用代理（如果需要）

3. **数据权限错误**
   - 确认账户是否有相应数据的访问权限
   - 联系掘金量化客服升级账户权限

## 📞 支持

- 掘金量化官网：https://www.myquant.cn/
- 官方文档：https://www.myquant.cn/docs/
- 客服支持：通过官网联系客服

## 📄 许可证

本项目仅用于学习和测试目的，请遵守掘金量化的服务条款和API使用规范。