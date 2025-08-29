# GM API接口分析报告

## 现有Demo文件API接口覆盖情况

### 1. 历史数据类 (Historical Data)
- **demo_1_history_data.py**: `gm.history()`
- **demo_4_trading_calendar.py**: `gm.get_trading_dates()`

### 2. 实时数据类 (Real-time Data)
- **demo_2_realtime_data.py**: `gm.current()`
- **demo_14_tick_data.py**: `gm.last_tick()`, `gm.get_history_l2orders()`
- **demo_17_market_depth.py**: `gm.get_history_bars_l2()`

### 3. 基础信息类 (Basic Information)
- **demo_3_basic_info.py**: `gm.get_instruments()`
- **demo_5_sector_constituents.py**: `gm.get_constituents()`
- **demo_16_industry_data.py**: `gm.stk_get_industry_category()`

### 4. 财务数据类 (Financial Data)
- **demo_6_fundamentals.py**: `gm.stk_get_fundamentals_*` 系列函数
- **demo_10_dividend_split.py**: 分红送股相关API
- **demo_11_shareholder_data.py**: `gm.stk_get_top_shareholder()`

### 5. 市场数据类 (Market Data)
- **demo_7_dragon_tiger_list.py**: 龙虎榜相关API
- **demo_15_money_flow.py**: `gm.stk_get_money_flow()`

### 6. 技术分析类 (Technical Analysis)
- **demo_8_technical_indicators.py**: 技术指标相关API

### 7. 融资融券类 (Margin Trading)
- **demo_9_margin_trading.py**: `gm.credit_get_borrowable_instruments()`

### 8. 期权数据类 (Options Data)
- **demo_12_options_data.py**: `gm.option_calculate_delta()` 等期权相关API

### 9. IPO数据类 (IPO Data)
- **demo_13_ipo_data.py**: `gm.ipo_get_instruments()`

### 10. 港股通数据类 (HK Connect)
- **demo_18_hk_connect.py**: `gm.stk_quota_shszhk_infos()`

## 总结

当前18个demo文件覆盖了约30-40个API接口，但GM SDK总共有205个API接口。
需要为剩余的160+个API接口创建独立的demo文件。

## 下一步计划

1. 按功能分类整理所有205个API接口
2. 为每个API接口创建独立的demo文件
3. 创建批量测试脚本验证所有demo的功能