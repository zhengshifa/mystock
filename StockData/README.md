# 股票数据采集系统

## 项目概述

这是一个专业的股票数据采集系统，采用模块化架构设计，支持多种数据类型的高效采集、存储和分析。

## 🚀 最新更新

**版本 2.0.0** - 重大重构完成！
- ✅ 采用模块化架构，按数据类型清晰分离
- ✅ 重构后的代码结构更加清晰和易维护
- ✅ 统一的接口管理，简化了系统使用
- ✅ 支持增量扩展和定制开发

## 🏗️ 项目架构

```
src/
├── market_data/          # 市场数据模块 (Tick/Bar数据)
├── fundamentals/         # 基本面数据模块 (财务报表)
├── realtime/            # 实时数据模块 (实时行情)
├── scheduler/           # 调度器模块 (任务管理)
├── services/            # 服务模块 (核心服务)
└── main.py              # 主入口文件
```

## ✨ 主要功能

### 📊 数据采集
- **Tick数据**: 高精度分笔数据采集
- **Bar数据**: 多频率K线数据 (1m, 5m, 15m, 30m, 1h, 1d)
- **基本面数据**: 资产负债表、利润表、现金流量表
- **实时数据**: 实时行情、买卖盘口数据

### 🔧 系统特性
- **模块化设计**: 清晰的职责分离，便于维护和扩展
- **统一接口**: 通过 `StockDataInterface` 统一管理所有采集器
- **智能调度**: 支持定时任务和手动任务执行
- **数据验证**: 完整的数据模型验证和转换
- **错误处理**: 完善的异常处理和日志记录

### 📈 数据分析
- **技术指标**: RSI、SMA等常用技术指标计算
- **市场分析**: 价格、成交量、波动性分析
- **报告生成**: 自动生成市场数据报告

## 🚀 快速开始

### 环境要求
- Python 3.8+
- MongoDB 4.0+
- GM SDK (掘金量化)
- 网络连接（用于数据采集）

### 安装依赖
```bash
# 使用uv管理Python环境
uv sync

# 或者使用pip
pip install -r requirements.txt
```

### 系统初始化
```bash
# 首次运行，检查系统状态
uv run python src/main.py --task status

# 查看帮助信息
uv run python src/main.py --help
```

### 基本使用

#### 1. 🎯 运行演示程序（推荐新手）
```bash
# 运行完整演示，包括实时数据、Bar数据、基本面数据采集
uv run python src/main.py --task demo

# 演示特定模块功能
uv run python src/main.py --task demo --module market_data
uv run python src/main.py --task demo --module fundamentals
```

#### 2. ⏰ 启动自动调度器
```bash
# 启动定时任务调度器（后台运行）
uv run python src/main.py --task scheduler

# 启动调度器并指定股票代码
uv run python src/main.py --task scheduler --symbols SZSE.000001,SHSE.600000

# 启动调度器并指定配置文件
uv run python src/main.py --task scheduler --config custom_config.yaml
```

#### 3. 🔍 执行特定数据采集任务

##### 实时数据采集
```bash
# 采集单个股票实时数据
uv run python src/main.py --task realtime --symbols SZSE.000001

# 采集多个股票实时数据
uv run python src/main.py --task realtime --symbols SZSE.000001,SHSE.600000,SZSE.000002

# 采集实时数据并保存到指定集合
uv run python src/main.py --task realtime --symbols SZSE.000001 --collection market_quotes
```

##### Bar数据采集
```bash
# 采集日线数据
uv run python src/main.py --task bar --symbols SHSE.600000 --frequencies 1d

# 采集多频率数据
uv run python src/main.py --task bar --symbols SHSE.600000 --frequencies 1d 1h 30m 15m 5m

# 采集指定时间范围的数据
uv run python src/main.py --task bar --symbols SHSE.600000 --start-time "2024-01-01" --end-time "2024-01-31" --frequencies 1d
```

##### Tick数据采集
```bash
# 采集最近一天的Tick数据
uv run python src/main.py --task tick --symbols SZSE.000001 --start-time "2024-01-01 09:30:00" --end-time "2024-01-01 15:00:00"

# 采集指定时间范围的Tick数据
uv run python src/main.py --task tick --symbols SZSE.000001 --start-time "2024-01-01 09:30:00" --end-time "2024-01-01 11:30:00"

# 批量采集多个股票的Tick数据
uv run python src/main.py --task tick --symbols SZSE.000001,SZSE.000002 --start-time "2024-01-01 09:30:00" --end-time "2024-01-01 15:00:00"
```

##### 基本面数据采集
```bash
# 采集单个股票基本面数据
uv run python src/main.py --task fundamentals --symbols SZSE.000001

# 采集多个股票基本面数据
uv run python src/main.py --task fundamentals --symbols SZSE.000001,SHSE.600000

# 采集指定时间范围的基本面数据
uv run python src/main.py --task fundamentals --symbols SZSE.000001 --start-date "2023-01-01" --end-date "2024-01-01"
```

##### 批量数据采集
```bash
# 采集所有类型数据
uv run python src/main.py --task all --symbols SZSE.000001

# 采集指定类型组合
uv run python src/main.py --task all --symbols SZSE.000001 --types tick,bar,fundamentals

# 批量采集多个股票的所有数据
uv run python src/main.py --task all --symbols SZSE.000001,SZSE.000002,SHSE.600000
```

#### 4. 💻 编程接口使用

##### 基本用法
```python
from src import StockDataSystem

# 创建系统实例
system = StockDataSystem()

# 初始化系统
system.initialize()

# 执行数据采集任务
result = system.run_collection_task('realtime', ['SZSE.000001'])
print(f"采集结果: {result}")

# 启动调度器
system.start_scheduler()
```

##### 高级用法
```python
from src import StockDataInterface, TaskScheduler

# 直接使用数据接口
interface = StockDataInterface()

# 采集所有类型数据
results = interface.collect_all_data(
    symbols=['SZSE.000001', 'SHSE.600000'],
    start_time='2024-01-01 09:30:00',
    end_time='2024-01-01 15:00:00',
    save_to_db=True
)

# 使用调度器
scheduler = TaskScheduler()
scheduler.run_manual_task('tick', ['SZSE.000001'])
```

##### 自定义数据采集
```python
from src.market_data import TickDataCollector, BarDataCollector
from src.fundamentals import FundamentalsDataCollector

# 创建自定义采集器
tick_collector = TickDataCollector()
bar_collector = BarDataCollector()
fundamentals_collector = FundamentalsDataCollector()

# 自定义采集逻辑
tick_data = tick_collector.get_history_tick_data(
    symbol='SZSE.000001',
    start_time='2024-01-01 09:30:00',
    end_time='2024-01-01 15:00:00'
)

# 保存数据
tick_collector.save_tick_data(tick_data, collection_name='custom_tick_data')
```

#### 5. 📊 数据查询和分析

##### 查询历史数据
```python
from src.market_data import MarketDataAnalyzer

# 创建分析器
analyzer = MarketDataAnalyzer()

# 分析Tick数据
analysis_result = analyzer.analyze_tick_data(tick_data)
print(f"分析结果: {analysis_result}")

# 计算技术指标
rsi_values = analyzer._calculate_rsi(price_data)
```

##### 数据库查询
```python
from utils import get_db_manager

# 获取数据库管理器
db_manager = get_db_manager()

# 查询Tick数据
tick_data = db_manager.find_data(
    collection_name='tick_data_1m',
    query={'symbol': 'SZSE.000001'},
    limit=1000
)

# 查询Bar数据
bar_data = db_manager.find_data(
    collection_name='bar_data_1d',
    query={'symbol': 'SHSE.600000', 'date': {'$gte': '2024-01-01'}}
)
```

## 📁 项目结构

```
StockData/
├── src/                          # 源代码目录
│   ├── __init__.py              # 模块初始化
│   ├── main.py                  # 主入口文件
│   ├── market_data/             # 市场数据模块
│   │   ├── __init__.py
│   │   ├── tick_collector.py    # Tick数据采集器
│   │   ├── bar_collector.py     # Bar数据采集器
│   │   └── market_analyzer.py   # 市场数据分析器
│   ├── fundamentals/            # 基本面数据模块
│   │   ├── __init__.py
│   │   └── fundamentals_collector.py
│   ├── realtime/                # 实时数据模块
│   │   ├── __init__.py
│   │   └── realtime_collector.py
│   ├── scheduler/               # 调度器模块
│   │   ├── __init__.py
│   │   └── scheduler.py
│   └── services/                # 服务模块
│       ├── __init__.py
│       └── data_model_service.py
├── config/                      # 配置文件
├── models/                      # 数据模型
├── utils/                       # 工具模块
├── docs/                        # 文档
├── logs/                        # 日志文件
├── pyproject.toml              # 项目配置
└── README.md                   # 项目说明
```

## 🔧 配置说明

### 主要配置项
- **股票代码列表**: `config.scheduler.stock_symbols`
- **数据库连接**: `config.mongodb.*`
- **GM SDK配置**: `config.gm_sdk.*`
- **数据保留策略**: `config.data.*`

### 环境变量
系统支持 `.env` 文件配置环境变量，包括：
- 数据库连接字符串
- GM SDK Token
- 日志级别等

## 📊 数据存储

### MongoDB集合结构
- `tick_data_1m`: 1分钟Tick数据
- `bar_data_1d`: 日线数据
- `bar_data_1h`: 小时线数据
- `bar_data_30m`: 30分钟线数据
- `bar_data_15m`: 15分钟线数据
- `bar_data_5m`: 5分钟线数据
- `fundamentals_balance`: 资产负债表数据
- `fundamentals_income`: 利润表数据
- `fundamentals_cashflow`: 现金流量表数据
- `current_quotes`: 实时行情数据

## 🚀 扩展开发

### 添加新的数据类型模块
1. 在 `src/` 下创建新的模块目录
2. 实现相应的采集器类
3. 在 `src/__init__.py` 中导入新模块
4. 在 `StockDataInterface` 中集成新采集器

### 添加新的分析功能
1. 在相应的模块中添加分析方法
2. 或创建新的分析器模块
3. 在调度器中集成新的分析任务

## 📝 使用示例

### 🕐 定时任务配置
系统内置了完整的定时任务配置，自动适应交易时间：

#### 交易日任务
- **9:15** - 开盘前任务：获取最新基本面数据、补充Bar数据
- **9:30** - 市场开盘任务：开始实时数据采集
- **13:00** - 午盘前任务：生成上午市场概览报告
- **15:00** - 市场收盘任务：采集收盘数据、整理当日Bar数据
- **15:30** - 盘后数据整理任务：生成市场分析报告、技术指标计算

#### 非交易日任务
- **20:00** - 每日基本面数据采集任务：更新财务报表数据
- **周日 02:00** - 每周历史数据补充任务：补充历史Tick和Bar数据

### 🎯 实际使用场景

#### 场景1：新手用户快速上手
```bash
# 1. 检查系统状态
uv run python src/main.py --task status

# 2. 运行演示程序，了解系统功能
uv run python src/main.py --task demo

# 3. 采集几只股票的实时数据
uv run python src/main.py --task realtime --symbols SZSE.000001,SHSE.600000

# 4. 启动自动调度器，让系统自动运行
uv run python src/main.py --task scheduler
```

#### 场景2：数据分析师批量采集
```bash
# 1. 批量采集多只股票的历史数据
uv run python src/main.py --task all --symbols SZSE.000001,SZSE.000002,SHSE.600000,SHSE.600036

# 2. 采集指定时间范围的高频数据
uv run python src/main.py --task tick --symbols SZSE.000001 --start-time "2024-01-01 09:30:00" --end-time "2024-01-01 15:00:00"

# 3. 采集多频率K线数据用于技术分析
uv run python src/main.py --task bar --symbols SHSE.600000 --frequencies 1d 1h 30m 15m 5m --start-time "2024-01-01" --end-time "2024-01-31"
```

#### 场景3：量化交易策略开发
```bash
# 1. 采集策略所需的历史数据
uv run python src/main.py --task tick --symbols SZSE.000001 --start-time "2023-01-01 09:30:00" --end-time "2024-01-01 15:00:00"

# 2. 实时监控市场数据
uv run python src/main.py --task realtime --symbols SZSE.000001,SHSE.600000 --collection strategy_monitor

# 3. 定期更新基本面数据
uv run python src/main.py --task fundamentals --symbols SZSE.000001,SHSE.600000
```

#### 场景4：系统管理员运维
```bash
# 1. 检查系统运行状态
uv run python src/main.py --task status

# 2. 手动执行数据补充任务
uv run python src/main.py --task all --symbols SZSE.000001 --start-time "2024-01-01" --end-time "2024-01-31"

# 3. 启动调度器并监控日志
uv run python src/main.py --task scheduler > scheduler.log 2>&1 &
tail -f scheduler.log
```

### 🔧 高级配置示例

#### 自定义配置文件
```yaml
# custom_config.yaml
scheduler:
  stock_symbols:
    - SZSE.000001
    - SHSE.600000
    - SZSE.000002
  
  task_schedule:
    market_open: "09:30"
    market_close: "15:00"
    data_collection_interval: 60  # 秒
    
  data_retention:
    tick_data_days: 30
    bar_data_days: 365
    fundamentals_data_years: 5
```

#### 环境变量配置
```bash
# .env 文件
MONGODB_URI=mongodb://localhost:27017/stockdata
GM_SDK_TOKEN=your_token_here
LOG_LEVEL=INFO
DATA_COLLECTION_INTERVAL=60
MAX_CONCURRENT_TASKS=4
```

### 📊 数据采集监控

#### 实时监控命令
```bash
# 监控数据采集状态
watch -n 5 'uv run python src/main.py --task status'

# 查看日志文件
tail -f logs/app.log
tail -f logs/scheduler.log
tail -f logs/error.log
```

#### 性能优化建议
```bash
# 1. 调整并发数量（根据系统性能）
export MAX_CONCURRENT_TASKS=8

# 2. 批量采集减少API调用
uv run python src/main.py --task all --symbols SZSE.000001,SZSE.000002,SHSE.600000

# 3. 使用增量更新减少重复数据
uv run python src/main.py --task bar --symbols SHSE.600000 --incremental --last-update "2024-01-01"
```

## 🔍 故障排除

### 🚨 常见问题及解决方案

#### 1. 数据库连接问题
```bash
# 问题：MongoDB连接失败
# 解决方案：
# 1. 检查MongoDB服务状态
sudo systemctl status mongod  # Linux
brew services list | grep mongodb  # macOS
net start MongoDB  # Windows

# 2. 检查连接配置
cat config/mongodb.yaml

# 3. 测试连接
mongo --host localhost --port 27017
```

#### 2. GM SDK连接问题
```bash
# 问题：GM SDK Token无效或连接失败
# 解决方案：
# 1. 检查Token配置
cat config/gm_sdk.yaml

# 2. 验证Token有效性
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.gm.com/v1/status

# 3. 检查网络连接
ping api.gm.com
```

#### 3. 数据采集失败
```bash
# 问题：数据采集返回空结果
# 解决方案：
# 1. 检查股票代码格式
# 正确格式：SZSE.000001, SHSE.600000
# 错误格式：000001, 600000

# 2. 检查交易时间
# 交易时间：9:30-11:30, 13:00-15:00
# 非交易时间采集历史数据

# 3. 检查API限制
uv run python src/main.py --task status
```

#### 4. 系统性能问题
```bash
# 问题：内存不足或响应缓慢
# 解决方案：
# 1. 调整批处理大小
export BATCH_SIZE=1000

# 2. 减少并发任务数
export MAX_CONCURRENT_TASKS=2

# 3. 监控系统资源
htop  # Linux/macOS
taskmgr  # Windows
```

### 📋 日志查看和分析

#### 日志文件位置
```bash
logs/
├── app.log              # 应用主日志
├── error.log            # 错误日志
├── scheduler.log        # 调度器日志
├── market_data.log      # 市场数据日志
├── fundamentals.log     # 基本面数据日志
└── realtime.log         # 实时数据日志
```

#### 日志查看命令
```bash
# 实时查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 搜索特定错误
grep "ERROR" logs/app.log | tail -20

# 查看调度器状态
tail -f logs/scheduler.log

# 按时间过滤日志
grep "2024-01-01" logs/app.log
```

#### 日志级别配置
```python
# 在config/logging.yaml中配置
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file_rotation: true
  max_file_size: 100MB
  backup_count: 5
```

### 🔧 系统诊断工具

#### 系统状态检查
```bash
# 检查系统整体状态
uv run python src/main.py --task status

# 检查数据库连接
uv run python src/main.py --task status --check-db

# 检查GM SDK连接
uv run python src/main.py --task status --check-api

# 检查数据完整性
uv run python src/main.py --task status --check-data
```

#### 性能测试
```bash
# 测试数据采集性能
time uv run python src/main.py --task realtime --symbols SZSE.000001

# 测试数据库写入性能
uv run python src/main.py --task performance-test --symbols SZSE.000001

# 测试并发性能
uv run python src/main.py --task concurrent-test --symbols SZSE.000001,SZSE.000002,SHSE.600000
```

### 📊 监控和告警

#### 系统监控指标
```bash
# 数据采集成功率
uv run python src/main.py --task metrics --metric collection_success_rate

# 系统响应时间
uv run python src/main.py --task metrics --metric response_time

# 数据库连接状态
uv run python src/main.py --task metrics --metric db_connection_status

# API调用频率
uv run python src/main.py --task metrics --metric api_call_frequency
```

#### 告警配置
```yaml
# config/alerts.yaml
alerts:
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: your_email@gmail.com
    password: your_app_password
  
  webhook:
    enabled: true
    url: https://hooks.slack.com/services/YOUR_WEBHOOK
    
  thresholds:
    collection_failure_rate: 0.1  # 10%
    response_time_ms: 5000        # 5秒
    db_connection_failures: 3     # 3次
```

## 📚 文档

- [项目结构说明](docs/project_structure.md) - 详细的模块架构说明
- [API文档](docs/api_reference.md) - 完整的API接口文档
- [配置指南](docs/configuration.md) - 系统配置详细说明
- [开发指南](docs/development.md) - 扩展开发指南

## 🚀 快速参考

### 📋 常用命令速查

| 任务类型 | 命令示例 | 说明 |
|---------|---------|------|
| **系统状态** | `uv run python src/main.py --task status` | 检查系统运行状态 |
| **演示程序** | `uv run python src/main.py --task demo` | 运行完整功能演示 |
| **启动调度器** | `uv run python src/main.py --task scheduler` | 启动自动任务调度 |
| **实时数据** | `uv run python src/main.py --task realtime --symbols SZSE.000001` | 采集实时行情数据 |
| **Bar数据** | `uv run python src/main.py --task bar --symbols SHSE.600000 --frequencies 1d 1h` | 采集K线数据 |
| **Tick数据** | `uv run python src/main.py --task tick --symbols SZSE.000001 --start-time "2024-01-01 09:30:00"` | 采集分笔数据 |
| **基本面数据** | `uv run python src/main.py --task fundamentals --symbols SZSE.000001` | 采集财务报表数据 |
| **批量采集** | `uv run python src/main.py --task all --symbols SZSE.000001,SZSE.000002` | 采集所有类型数据 |

### 🔧 常用参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--task` | 任务类型 | `demo`, `scheduler`, `realtime`, `bar`, `tick`, `fundamentals`, `all` |
| `--symbols` | 股票代码列表 | `SZSE.000001,SHSE.600000` |
| `--frequencies` | Bar数据频率 | `1d`, `1h`, `30m`, `15m`, `5m` |
| `--start-time` | 开始时间 | `"2024-01-01 09:30:00"` |
| `--end-time` | 结束时间 | `"2024-01-01 15:00:00"` |
| `--start-date` | 开始日期 | `"2024-01-01"` |
| `--end-date` | 结束日期 | `"2024-01-31"` |
| `--collection` | 集合名称 | `market_quotes`, `custom_data` |

### 📊 数据格式说明

| 数据类型 | 集合名称 | 数据格式 |
|---------|---------|----------|
| **Tick数据** | `tick_data_1m` | 分笔成交记录 |
| **Bar数据** | `bar_data_1d`, `bar_data_1h` | OHLCV K线数据 |
| **基本面数据** | `fundamentals_balance`, `fundamentals_income` | 财务报表数据 |
| **实时数据** | `current_quotes` | 实时行情快照 |

### ⏰ 定时任务时间表

| 时间 | 任务类型 | 说明 |
|------|---------|------|
| **09:15** | 开盘前准备 | 基本面数据、Bar数据更新 |
| **09:30** | 市场开盘 | 开始实时数据采集 |
| **13:00** | 午盘前 | 上午市场概览报告 |
| **15:00** | 市场收盘 | 收盘数据采集、整理 |
| **15:30** | 盘后整理 | 市场分析报告生成 |
| **20:00** | 基本面更新 | 财务报表数据更新 |
| **周日 02:00** | 历史数据补充 | 历史数据补充和整理 |

## 🤝 贡献指南

欢迎提交Issue和Pull Request！在贡献代码前，请确保：
1. 代码符合项目编码规范
2. 添加适当的测试用例
3. 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 [Issue](../../issues)
- 发送邮件至项目维护者

---

**注意**: 本项目仅供学习和研究使用，请遵守相关法律法规和平台使用条款。