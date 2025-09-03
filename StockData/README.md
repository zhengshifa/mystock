# 掘金量化SDK接口测试项目

## 项目简介

这是一个用于测试掘金量化SDK接口的Python项目，主要测试`current`和`history`两个核心接口的功能。

## 项目结构

```
stockdata-v3/
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
│   └── __init__.py
├── tests/                 # 测试目录
├── docs/                  # 文档目录
├── test_gm_api.py         # 基础API测试脚本
├── advanced_test.py       # 高级功能测试脚本
├── config.env             # 环境配置文件
├── pyproject.toml         # 项目配置
└── README.md              # 项目说明
```

## 功能特性

### 1. 数据模型
- **Tick模型**: 实时行情快照数据，包含买卖档位信息
- **Bar模型**: 历史K线数据，支持多种时间频率

### 2. 接口测试
- **current接口**: 查询当前行情快照
- **history接口**: 查询历史行情数据

### 3. 调度系统
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

### 4. 运行测试

#### 基础API测试
```bash
uv run python test_gm_api.py
```

#### 高级功能测试
```bash
uv run python advanced_test.py
```

#### 调度系统测试
```bash
uv run python test_scheduler.py
```

#### 多频率功能测试
```bash
uv run python test_multi_frequency.py
```

#### 启动调度器
```bash
uv run python start_scheduler.py
```

#### 数据查询工具
```bash
uv run python query_data.py
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
6. 调度器默认在交易时间内运行实时同步
7. 历史数据同步每日定时执行，避免重复同步

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
REALTIME_SYNC_START=09:30
REALTIME_SYNC_END=15:00

# 数据频率配置
ENABLED_FREQUENCIES=60s,300s,900s,1800s,3600s,1d
SYNC_FREQUENCY_60S=true
SYNC_FREQUENCY_300S=true
SYNC_FREQUENCY_900S=true
SYNC_FREQUENCY_1800S=true
SYNC_FREQUENCY_3600S=true
SYNC_FREQUENCY_1D=true
```

### 调度任务说明
1. **每日历史数据同步**: 每天09:30执行，增量同步所有频率的历史数据
2. **实时数据同步**: 每30秒执行一次，仅在交易时间内运行，同步Tick和分钟级数据
3. **分钟数据同步**: 每5分钟执行一次，同步所有分钟级频率的K线数据
4. **健康检查**: 每分钟执行一次，检查系统状态

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
