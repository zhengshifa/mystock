# 掘金量化API配置说明

## 🔑 API配置要求

要使用掘金量化SDK获取真实股票数据，您需要：

### 1. 掘金量化账户
- 注册掘金量化账户：https://www.myquant.cn/
- 完成实名认证
- 获取API访问权限

### 2. 必要的配置信息
```env
# .env文件中的配置
GM_TOKEN=your_gm_token_here          # 掘金量化API Token
GM_USERNAME=your_gm_username_here    # 掘金量化用户名
```

## 📡 API接口说明

### 当前使用的API接口

#### Tick数据获取
```python
# 当前使用模拟数据，需要替换为真实API调用
def _fetch_tick_data(self, symbol: str) -> Optional[TickData]:
    # 需要实现的真实API调用：
    # 1. 获取实时行情数据
    # 2. 获取逐笔交易数据
    # 3. 获取买卖档数据
    pass
```

#### K线数据获取
```python
# 当前使用模拟数据，需要替换为真实API调用
def _fetch_bar_data(self, symbol: str, frequency: str, 
                    start_date: str, end_date: str) -> List[BarData]:
    # 需要实现的真实API调用：
    # 1. 获取历史K线数据
    # 2. 根据频率获取不同时间周期的数据
    pass
```

## 🛠️ 实现真实API调用

### 1. 修改 `src/collectors/gm_collector.py`

#### Tick数据获取示例
```python
def _fetch_tick_data(self, symbol: str) -> Optional[TickData]:
    """获取单个股票的Tick数据"""
    try:
        # 获取实时行情数据
        # 使用掘金量化的真实API
        from gm.api import get_instruments, get_ticks
        
        # 获取股票基本信息
        instrument_info = get_instruments(symbols=[symbol])
        if not instrument_info:
            self.logger.warning(f"未找到股票信息: {symbol}")
            return None
        
        # 获取实时Tick数据
        ticks = get_ticks(symbols=[symbol], count=1)
        if not ticks:
            self.logger.warning(f"未获取到{symbol}的Tick数据")
            return None
        
        tick = ticks[0]  # 获取最新的Tick数据
        
        # 创建TickData对象
        tick_data = TickData(
            symbol=symbol,
            open=tick.get('open', 0.0),
            high=tick.get('high', 0.0),
            low=tick.get('low', 0.0),
            price=tick.get('price', 0.0),
            cum_volume=tick.get('cum_volume', 0),
            cum_amount=tick.get('cum_amount', 0.0),
            cum_position=tick.get('cum_position', 0),
            trade_type=tick.get('trade_type', 0),
            last_volume=tick.get('last_volume', 0),
            last_amount=tick.get('last_amount', 0.0),
            created_at=datetime.fromtimestamp(tick.get('created_at', 0)),
            quotes=[
                QuoteData(
                    bid_p=tick.get('bid_p', 0.0),
                    bid_v=tick.get('bid_v', 0),
                    ask_p=tick.get('ask_p', 0.0),
                    ask_v=tick.get('ask_v', 0)
                )
            ]
        )
        
        return tick_data
        
    except Exception as e:
        self.logger.error(f"获取{symbol}的Tick数据异常: {e}")
        return None
```

#### K线数据获取示例
```python
def _fetch_bar_data(self, symbol: str, frequency: str, 
                    start_date: str, end_date: str) -> List[BarData]:
    """获取单个股票的Bar数据"""
    try:
        # 使用掘金量化的真实API
        from gm.api import history
        
        # 获取历史K线数据
        bars = history(
            symbol=symbol,
            frequency=frequency,
            start_time=start_date,
            end_time=end_date,
            fields='open,high,low,close,volume,amount,created_at'
        )
        
        if bars.empty:
            self.logger.warning(f"未获取到{symbol}的{frequency}数据")
            return []
        
        bar_data_list = []
        for _, bar in bars.iterrows():
            bar_data = BarData(
                symbol=symbol,
                frequency=frequency,
                open=bar.get('open', 0.0),
                close=bar.get('close', 0.0),
                high=bar.get('high', 0.0),
                low=bar.get('low', 0.0),
                amount=bar.get('amount', 0.0),
                volume=bar.get('volume', 0),
                bob=bar.get('created_at', datetime.now()),
                eob=bar.get('created_at', datetime.now())
            )
            bar_data_list.append(bar_data)
        
        return bar_data_list
        
    except Exception as e:
        self.logger.error(f"获取{symbol}的{frequency}数据异常: {e}")
        return []
```

### 2. 常用掘金量化API接口

#### 基础接口
```python
from gm.api import *

# 设置Token
set_token('your_token_here')

# 获取股票列表
instruments = get_instruments(exchanges=['SHSE', 'SZSE'])

# 获取实时行情
quotes = get_quotes(symbols=['SH600000', 'SZ000001'])

# 获取历史数据
bars = history(symbol='SH600000', frequency='1d', count=100)

# 获取Tick数据
ticks = get_ticks(symbols=['SH600000'], count=1000)
```

#### 数据字段说明
- **Tick数据字段**: `open`, `high`, `low`, `price`, `volume`, `amount`, `created_at`
- **K线数据字段**: `open`, `high`, `low`, `close`, `volume`, `amount`, `created_at`
- **频率参数**: `'1m'`, `'5m'`, `'15m'`, `'1d'`, `'1w'`, `'1M'`

## ⚠️ 注意事项

### 1. API限制
- 掘金量化API有调用频率限制
- 免费账户有数据量限制
- 某些数据需要付费订阅

### 2. 错误处理
- 网络异常时自动重试
- API限制时等待后重试
- 记录详细的错误日志

### 3. 数据质量
- 验证数据的完整性
- 检查数据的时间戳
- 处理异常数据值

## 🔧 故障排除

### 常见错误及解决方案

#### 1. Token无效
```
错误: Authentication failed
解决: 检查Token是否正确，是否已过期
```

#### 2. 权限不足
```
错误: Insufficient permissions
解决: 升级账户权限或联系客服
```

#### 3. 频率限制
```
错误: Rate limit exceeded
解决: 降低请求频率，增加重试间隔
```

#### 4. 网络问题
```
错误: Connection timeout
解决: 检查网络连接，配置代理
```

## 📞 技术支持

### 掘金量化官方支持
- 官方文档: https://www.myquant.cn/docs
- 技术支持: support@myquant.cn
- 开发者社区: https://www.myquant.cn/community

### 项目相关支持
- 查看日志文件: `logs/stock_collector.log`
- 运行测试: `uv run pytest tests/ -v`
- 检查配置: 确认`.env`文件配置正确

## 🚀 下一步

1. **获取API权限**: 注册掘金量化账户并获取Token
2. **替换模拟数据**: 将上述示例代码替换到收集器中
3. **测试API调用**: 验证数据获取是否正常
4. **优化性能**: 调整请求频率和批量大小
5. **监控运行**: 观察数据收集的稳定性和准确性
