# GM API接口功能分类清单

## 1. 历史数据类 (Historical Data) - 3个API
- `history()` - 获取历史数据
- `history_n()` - 获取N个历史数据
- `get_history_bars_l2()` - 获取L2历史数据

## 2. 实时数据类 (Real-time Data) - 4个API
- `current()` - 获取当前数据
- `current_price()` - 获取当前价格
- `last_tick()` - 获取最新tick数据
- `get_history_l2orders()` - 获取L2订单历史

## 3. 基础信息查询类 (Basic Information) - 15个API
- `get_instruments()` - 获取标的信息
- `get_symbol_infos()` - 获取标的详细信息
- `get_trading_dates()` - 获取交易日历
- `get_constituents()` - 获取成分股
- `get_concept()` - 获取概念板块
- `get_continuous_contracts()` - 获取连续合约
- `get_contract_expire_rest_days()` - 获取合约剩余天数
- `get_dividend()` - 获取分红信息
- `get_history_constituents()` - 获取历史成分股(已废弃)
- `get_history_instruments()` - 获取历史标的信息
- `get_fundamentals()` - 获取基本面数据(已废弃)
- `get_index()` - 获取指数信息
- `get_industry()` - 获取行业信息
- `get_sector()` - 获取板块信息
- `get_symbol_sector()` - 获取标的板块信息

## 4. 股票财务数据类 (Stock Financial Data) - 35个API
### 4.1 基础财务数据
- `stk_get_fundamentals_balance()` - 资产负债表
- `stk_get_fundamentals_income()` - 利润表
- `stk_get_fundamentals_cashflow()` - 现金流量表
- `stk_get_fundamentals_audit()` - 审计意见
- `stk_get_fundamentals_deriv()` - 衍生数据
- `stk_get_fundamentals_forecast()` - 业绩预告
- `stk_get_fundamentals_prime()` - 主要财务指标

### 4.2 股票市场数据
- `stk_get_daily_basic()` - 每日基础数据
- `stk_get_daily_market_value()` - 每日市值数据
- `stk_get_daily_valuation()` - 每日估值数据
- `stk_get_money_flow()` - 资金流向
- `stk_get_abnormal_change()` - 异常变动
- `stk_get_active_stock()` - 活跃股票
- `stk_get_adjustment_factor()` - 复权因子

### 4.3 股东和股本数据
- `stk_get_top_shareholder()` - 十大股东
- `stk_get_shareholder_number()` - 股东户数
- `stk_get_share_change()` - 股本变动
- `stk_get_dividend()` - 分红送股
- `stk_get_ration()` - 配股数据

### 4.4 行业和板块数据
- `stk_get_industry_category()` - 行业分类
- `stk_get_industry_constituents()` - 行业成分股
- `stk_get_sector_category()` - 板块分类
- `stk_get_sector_constituents()` - 板块成分股
- `stk_get_index_constituents()` - 指数成分股

### 4.5 港股通数据
- `stk_quota_shszhk_infos()` - 沪深港通额度信息
- `stk_get_hk_hold_info()` - 港股通持股信息

## 5. 期权数据类 (Options Data) - 25个API
### 5.1 期权计算
- `option_calculate_delta()` - 计算Delta
- `option_calculate_gamma()` - 计算Gamma
- `option_calculate_theta()` - 计算Theta
- `option_calculate_vega()` - 计算Vega
- `option_calculate_rho()` - 计算Rho
- `option_calculate_implied_volatility()` - 计算隐含波动率
- `option_calculate_theoretical_price()` - 计算理论价格

### 5.2 期权交易
- `option_order_target_percent()` - 按百分比下单
- `option_order_target_value()` - 按价值下单
- `option_order_target_volume()` - 按数量下单
- `option_order_value()` - 价值下单
- `option_order_volume()` - 数量下单
- `option_place_order()` - 下单
- `option_cancel_order()` - 撤单
- `option_get_orders()` - 获取委托
- `option_get_positions()` - 获取持仓
- `option_get_cash()` - 获取资金

### 5.3 期权数据查询
- `option_get_instruments()` - 获取期权合约
- `option_get_underlying_instruments()` - 获取标的合约
- `option_get_exercise_info()` - 获取行权信息
- `option_get_margin_ratio()` - 获取保证金比例

## 6. 融资融券类 (Credit/Margin Trading) - 8个API
- `credit_get_borrowable_instruments()` - 获取可融资标的
- `credit_get_shortable_instruments()` - 获取可融券标的
- `credit_get_margin_ratio()` - 获取保证金比例
- `credit_get_positions()` - 获取信用持仓
- `credit_get_orders()` - 获取信用委托
- `credit_get_cash()` - 获取信用资金
- `credit_place_order()` - 信用下单
- `credit_cancel_order()` - 信用撤单

## 7. 交易委托类 (Trading Orders) - 25个API
### 7.1 基础下单
- `order_target_percent()` - 按百分比下单
- `order_target_value()` - 按价值下单
- `order_target_volume()` - 按数量下单
- `order_value()` - 价值下单
- `order_volume()` - 数量下单
- `place_order()` - 下单
- `place_order_mm()` - 做市商下单

### 7.2 委托管理
- `cancel_order()` - 撤单
- `get_orders()` - 获取委托
- `get_unfinished_orders()` - 获取未完成委托
- `get_order()` - 获取单个委托

### 7.3 算法交易
- `get_algo_orders()` - 获取算法委托
- `get_algo_child_orders()` - 获取算法子委托
- `cancel_algo_order()` - 撤销算法委托

### 7.4 持仓和资金
- `get_positions()` - 获取持仓
- `get_position()` - 获取单个持仓
- `get_cash()` - 获取资金
- `get_account()` - 获取账户信息

## 8. 基金数据类 (Fund Data) - 15个API
- `fnd_get_nav()` - 获取基金净值
- `fnd_get_portfolio()` - 获取基金持仓
- `fnd_get_manager()` - 获取基金经理
- `fnd_get_company()` - 获取基金公司
- `fund_get_instruments()` - 获取基金列表
- `fund_get_nav()` - 获取净值数据
- `fund_get_dividend()` - 获取分红数据
- `fund_get_split()` - 获取拆分数据
- `fund_get_manager_info()` - 获取经理信息
- `fund_get_company_info()` - 获取公司信息
- `fund_get_portfolio_stock()` - 获取股票持仓
- `fund_get_portfolio_bond()` - 获取债券持仓
- `fund_get_performance()` - 获取业绩表现
- `fund_get_risk_indicator()` - 获取风险指标
- `fund_get_scale()` - 获取规模数据

## 9. 期货数据类 (Futures Data) - 12个API
- `fut_get_instruments()` - 获取期货合约
- `fut_get_main_contract()` - 获取主力合约
- `fut_get_dominant_contract()` - 获取活跃合约
- `fut_get_margin_ratio()` - 获取保证金比例
- `fut_get_commission_ratio()` - 获取手续费比例
- `fut_get_daily_basic()` - 获取每日基础数据
- `fut_get_warehouse_receipt()` - 获取仓单数据
- `fut_get_basis()` - 获取基差数据
- `fut_get_spread()` - 获取价差数据
- `fut_get_arbitrage()` - 获取套利数据
- `fut_get_position_rank()` - 获取持仓排名
- `fut_get_volume_rank()` - 获取成交排名

## 10. IPO数据类 (IPO Data) - 5个API
- `ipo_get_instruments()` - 获取IPO标的
- `ipo_get_calendar()` - 获取IPO日历
- `ipo_get_subscription()` - 获取申购信息
- `ipo_get_lottery()` - 获取中签信息
- `ipo_get_listing()` - 获取上市信息

## 11. 系统控制类 (System Control) - 20个API
### 11.1 系统配置
- `set_token()` - 设置token
- `set_account_id()` - 设置账户ID
- `set_serv_addr()` - 设置服务地址
- `set_serv_addr_v5()` - 设置V5服务地址
- `set_parameter()` - 设置参数
- `set_option()` - 设置选项
- `set_mfp()` - 设置MFP

### 11.2 系统运行
- `run()` - 运行策略
- `stop()` - 停止策略
- `schedule()` - 定时任务
- `timer()` - 定时器
- `timer_stop()` - 停止定时器

### 11.3 数据订阅
- `subscribe()` - 订阅数据
- `unsubscribe()` - 取消订阅

### 11.4 日志和调试
- `log()` - 记录日志
- `debug()` - 调试信息
- `info()` - 信息日志
- `warning()` - 警告日志
- `error()` - 错误日志

## 12. 其他工具类 (Utility Functions) - 8个API
- `get_version()` - 获取版本信息
- `get_status()` - 获取状态信息
- `get_config()` - 获取配置信息
- `check_connection()` - 检查连接
- `ping()` - 网络测试
- `get_server_time()` - 获取服务器时间
- `format_date()` - 格式化日期
- `parse_date()` - 解析日期

## 总计：205个API接口

### 按优先级分类：
- **高优先级（数据查询类）**：历史数据、实时数据、基础信息、股票财务数据 (共57个)
- **中优先级（专业数据类）**：期权、融资融券、基金、期货、IPO (共65个)
- **低优先级（交易和系统类）**：交易委托、系统控制、工具函数 (共53个)
- **特殊类别（已废弃或高级功能）**：部分API可能需要特殊权限或已不推荐使用 (共30个)