# 掘金量化SDK接口测试项目

## 项目简介

这是一个用于测试掘金量化SDK接口的Python项目，主要测试`current`和`history`两个核心接口的功能。项目默认以调度模式运行，实现免交互的自动化数据同步。

## 项目结构

```
StockData/
├── src/                    # 源代码目录
│   ├── config/            # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py    # 配置管理
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── tick.py        # Tick数据模型
│   │   └── bar.py         # Bar数据模型
│   ├── services/          # 服务层
│   │   ├── __init__.py
│   │   └── gm_service.py  # 掘金量化服务
│   ├── database/          # 数据库模块
│   │   ├── __init__.py
│   │   └── mongodb_client.py  # MongoDB客户端
│   ├── scheduler/         # 调度模块
│   │   ├── __init__.py
│   │   ├── scheduler_service.py  # 调度服务
│   │   └── data_sync.py   # 数据同步服务
│   └── __init__.py
├── scripts/               # 脚本工具包
│   ├── tests/            # 测试脚本
│   │   ├── test_gm_api.py         # API测试
│   │   ├── test_scheduler.py      # 调度器测试
│   │   ├── test_multi_frequency.py # 多频率测试
│   │   └── advanced_test.py       # 高级测试
│   ├── tools/            # 工具脚本
│   │   ├── query_data.py          # 数据查询工具
│   │   └── start_scheduler.py     # 调度器工具
│   └── README.md         # 脚本说明
├── logs/                 # 日志目录
│   ├── stock_data_app.log        # 主应用日志
│   ├── gm_test.log              # API测试日志
│   ├── scheduler_test.log        # 调度器测试日志
│   ├── multi_frequency_test.log  # 多频率测试日志
│   ├── scheduler.log             # 调度器运行日志
│   └── README.md                 # 日志说明
├── main.py               # 主应用入口
├── start.py              # 统一启动脚本
├── config.env            # 环境配置文件
├── requirements.txt      # 依赖配置
└── README.md             # 项目说明
```

## 功能特性

### 1. 数据模型
- **Tick模型**: 实时行情快照数据，包含买卖档位信息
- **Bar模型**: 历史K线数据，支持多种时间频率

### 2. 接口测试
- **current接口**: 查询当前行情快照
- **history接口**: 查询历史行情数据

### 3. 调度系统
- **免交互启动**: 默认以调度模式运行，无需人工干预
- **定时任务调度**: 使用APScheduler实现定时数据同步
- **增量数据同步**: 智能识别最新数据，避免重复同步
- **实时数据获取**: 交易时间内定期获取实时行情
- **MongoDB持久化**: 异步数据存储和查询
- **多频率支持**: 支持60s, 300s, 900s, 1800s, 3600s, 1d等多种频率

### 4. 高级功能
- 多股票对比分析
- 技术指标计算
- 错误处理测试
- 数据格式转换
- 数据查询工具

## 安装和使用

### 1. 环境要求
- Python 3.8+
- uv包管理器

### 2. 安装依赖
```bash
uv sync
```

### 3. 配置设置
编辑`config.env`文件，设置您的掘金量化Token：
```
GM_TOKEN=your_token_here
```

### 4. 运行程序

#### 使用统一启动脚本（推荐）
```bash
# 调度模式（默认，免交互）
uv run python start.py

# 交互模式
uv run python start.py interactive

# 调度模式（明确指定）
uv run python start.py scheduler

# 测试模式
uv run python start.py test

# 同步模式
uv run python start.py sync

# 查询模式
uv run python start.py query

# 自动模式
uv run python start.py auto
```

#### 运行测试脚本
```bash
# API测试
uv run python start.py test-api

# 调度器测试
uv run python start.py test-scheduler

# 多频率测试
uv run python start.py test-multi

# 高级测试
uv run python start.py test-advanced
```

#### 运行工具脚本
```bash
# 数据查询工具
uv run python start.py query-tool

# 调度器工具
uv run python start.py scheduler-tool
```

#### 直接运行主程序
```bash
# 交互模式
uv run python main.py

# 调度模式
uv run python main.py scheduler

# 测试模式
uv run python main.py test
```

#### 直接运行脚本（不推荐）
```bash
# 测试脚本
uv run python scripts/tests/test_gm_api.py
uv run python scripts/tests/test_scheduler.py
uv run python scripts/tests/test_multi_frequency.py
uv run python scripts/tests/advanced_test.py

# 工具脚本
uv run python scripts/tools/query_data.py
uv run python scripts/tools/start_scheduler.py
```

## 测试结果

### current接口测试结果
✅ **连接测试成功**
- 成功获取实时行情数据
- 支持单个和多个股票查询
- 支持指定字段查询
- 正确处理买卖档位数据

### history接口测试结果
✅ **历史数据查询成功**
- 成功获取日线数据
- 支持DataFrame格式返回
- 正确处理时间范围查询
- 支持多种频率查询

### 高级功能测试结果
✅ **数据分析功能正常**
- 多股票对比分析
- 技术指标计算（MA5, MA10, 波动率）
- 涨跌统计
- 错误处理机制

### 调度系统测试结果
✅ **调度系统功能正常**
- MongoDB连接和索引创建成功
- 历史数据增量同步正常
- 实时数据同步正常
- 调度器任务执行正常
- 数据持久化存储成功

### 多频率功能测试结果
✅ **多频率功能正常**
- 支持6种频率：60s, 300s, 900s, 1800s, 3600s, 1d
- 每种频率独立集合存储
- 多频率数据同步正常
- 频率数据统计功能正常
- 查询工具支持多频率查询

## 数据示例

### 实时行情数据
```
股票代码: SZSE.000001
最新价: 11.75
开盘价: 11.98
最高价: 12.01
最低价: 11.74
成交量: 136,723,249
成交额: 1,619,322,977.46
```

### 历史数据统计
```
数据条数: 22
最高价: 12.53
最低价: 11.84
平均收盘价: 12.21
总成交量: 2,947,178,987
```

## 技术特点

1. **模块化设计**: 清晰的代码结构，便于维护和扩展
2. **类型注解**: 完整的类型提示，提高代码可读性
3. **错误处理**: 完善的异常处理机制
4. **日志记录**: 详细的日志输出，便于调试
5. **配置管理**: 环境变量配置，支持不同环境部署

## 注意事项

1. 确保Token有效且有足够的API调用权限
2. 股票代码格式需要正确（如：SZSE.000001）
3. 时间范围查询不能超过数据可用范围
4. 分钟线数据在非交易时间可能返回空结果
5. 确保MongoDB服务正在运行
6. **默认启动模式**: 直接运行 `uv run python start.py` 将启动调度系统，无需交互
7. **交易时间配置**: 可通过配置文件自定义交易时间，默认(09:30-11:30, 13:00-15:00)，非交易时间自动跳过实时同步
8. **增量同步策略**: 开盘前(08:30)和收盘后(15:30)执行增量同步，确保数据完整性
9. 历史数据同步每日定时执行，避免重复同步
10. 如需交互模式，请使用 `uv run python start.py interactive`

## 调度系统配置

### 环境变量配置
```bash
# MongoDB配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=StockData
MONGODB_COLLECTION_TICK=tick_data
MONGODB_COLLECTION_BAR_60S=bar_60s
MONGODB_COLLECTION_BAR_300S=bar_300s
MONGODB_COLLECTION_BAR_900S=bar_900s
MONGODB_COLLECTION_BAR_1800S=bar_1800s
MONGODB_COLLECTION_BAR_3600S=bar_3600s
MONGODB_COLLECTION_BAR_1D=bar_1d

# 调度配置
SCHEDULER_ENABLED=true
SYNC_INTERVAL_MINUTES=5
REALTIME_INTERVAL_SECONDS=30
HISTORY_SYNC_TIME=09:30

# 交易时间配置（用户可自定义）
TRADING_MORNING_START=09:30
TRADING_MORNING_END=11:30
TRADING_AFTERNOON_START=13:00
TRADING_AFTERNOON_END=15:00

# 增量同步配置
PRE_MARKET_SYNC_TIME=08:30
POST_MARKET_SYNC_TIME=15:30
INCREMENTAL_SYNC_ENABLED=true

# 数据频率配置
ENABLED_FREQUENCIES=60s,300s,900s,1800s,3600s,1d
SYNC_FREQUENCY_60S=true
SYNC_FREQUENCY_300S=true
SYNC_FREQUENCY_900S=true
SYNC_FREQUENCY_1800S=true
SYNC_FREQUENCY_3600S=true
SYNC_FREQUENCY_1D=true
```

### 交易时间配置说明

系统支持用户自定义交易时间，通过修改 `config.env` 文件中的以下配置项：

```bash
# 交易时间配置（用户可自定义）
TRADING_MORNING_START=09:30    # 上午交易开始时间
TRADING_MORNING_END=11:30      # 上午交易结束时间
TRADING_AFTERNOON_START=13:00  # 下午交易开始时间
TRADING_AFTERNOON_END=15:00    # 下午交易结束时间
```

**配置示例**：
- **A股市场**：09:30-11:30, 13:00-15:00（默认）
- **港股市场**：09:30-12:00, 13:00-16:00
- **美股市场**：21:30-04:00（次日）
- **自定义时间**：根据实际需求调整

**注意事项**：
- 时间格式必须为 `HH:MM`（24小时制）
- 修改配置后需要重启系统生效
- 周末自动跳过所有交易相关任务

### 调度任务说明
1. **每日历史数据同步**: 每天09:30执行，增量同步所有频率的历史数据
2. **开盘前增量同步**: 每天08:30执行，同步前一日的数据，确保开盘前数据完整
3. **收盘后增量同步**: 每天15:30执行，同步当日的数据，确保收盘后数据完整
4. **实时数据同步**: 每30秒执行一次，仅在交易时间内运行，同步Tick和分钟级数据
5. **分钟数据同步**: 每5分钟执行一次，仅在交易时间内运行，同步所有分钟级频率的K线数据
6. **健康检查**: 每分钟执行一次，检查系统状态

### 交易时间优化
- **可配置交易时间**: 支持用户自定义交易时间，通过配置文件灵活调整
- **精确交易时间判断**: 支持上午和下午两个交易时段，默认(09:30-11:30, 13:00-15:00)
- **非交易时间跳过**: 实时同步和分钟数据同步仅在交易时间内执行，节省资源
- **增量同步策略**: 开盘前和收盘后进行增量同步，确保数据完整性

### 多频率数据说明
- **60s**: 1分钟K线数据，存储到bar_60s集合
- **300s**: 5分钟K线数据，存储到bar_300s集合
- **900s**: 15分钟K线数据，存储到bar_900s集合
- **1800s**: 30分钟K线数据，存储到bar_1800s集合
- **3600s**: 1小时K线数据，存储到bar_3600s集合
- **1d**: 日K线数据，存储到bar_1d集合
- **tick**: 实时行情数据，存储到tick_data集合

## 扩展功能

项目支持以下扩展：
- 添加更多技术指标计算
- 实现数据可视化
- 添加数据存储功能
- 实现实时数据监控
- 添加策略回测功能
- 支持更多数据源
- 添加数据导出功能
- 实现Web管理界面

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目Issues: [GitHub Issues]
- 邮箱: admin@example.com
