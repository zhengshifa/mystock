# 股票数据收集器

使用掘金量化SDK获取股票数据并存储到MongoDB的数据收集系统。

## 功能特性

- 🚀 **掘金量化集成**: 使用掘金量化SDK获取实时股票数据
- 🗄️ **MongoDB存储**: 支持多种股票数据类型的存储和管理
- ⏰ **定时调度**: 自动定时收集数据，支持自定义调度策略
- 🔄 **增量入库**: 智能去重，避免重复数据
- 📊 **多种数据类型**: 支持Tick、Bar、日线等多种数据格式
- 🛡️ **错误处理**: 完善的异常处理和重试机制
- 📝 **日志记录**: 详细的日志记录和监控
- ⚙️ **配置管理**: 统一的环境变量配置管理

## 项目结构

```
StockData/
├── src/                    # 源代码目录
│   ├── config/            # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py    # 配置类
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   └── stock_data.py  # 股票数据模型
│   ├── database/          # 数据库模块
│   │   ├── __init__.py
│   │   └── mongodb_client.py  # MongoDB客户端
│   ├── collectors/        # 数据收集器
│   │   ├── __init__.py
│   │   └── gm_collector.py    # 掘金量化收集器
│   ├── scheduler/         # 定时调度
│   │   ├── __init__.py
│   │   └── data_scheduler.py  # 数据调度器
│   └── utils/             # 工具模块
│       ├── __init__.py
│       ├── logger.py      # 日志配置
│       └── helpers.py     # 辅助函数
├── tests/                 # 测试目录
│   ├── __init__.py
│   └── test_models.py     # 模型测试
├── logs/                  # 日志目录
├── data/                  # 数据目录
├── config/                # 配置目录
├── main.py                # 主程序入口
├── pyproject.toml         # 项目配置
├── config.env.example     # 环境变量示例
└── README.md              # 项目说明
```

## 安装要求

- Python 3.8+
- MongoDB 4.0+
- 掘金量化账户和API Token

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd StockData

# 使用uv管理Python环境
uv venv
uv activate

# 安装依赖
uv pip install -e .
```

### 2. 配置环境变量

复制环境变量示例文件并配置：

```bash
cp config.env.example .env
```

编辑 `.env` 文件，配置以下参数：

```env
# 掘金量化配置
GM_TOKEN=your_gm_token_here
GM_USERNAME=your_gm_username_here

# MongoDB配置
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=stock_data
MONGODB_USERNAME=your_mongodb_username
MONGODB_PASSWORD=your_mongodb_password

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/stock_collector.log

# 数据收集配置
COLLECTION_INTERVAL=60
MAX_RETRY_COUNT=3
BATCH_SIZE=1000
```

### 3. 运行程序

#### 守护进程模式（推荐）

```bash
uv run python main.py --mode daemon
```

#### 运行一次模式

```bash
# 收集Tick数据
uv run python main.py --mode once --type tick

# 收集Bar数据
uv run python main.py --mode once --type bar

# 收集日线数据
uv run python main.py --mode once --type daily
```

## 配置说明

### 掘金量化配置

- `GM_TOKEN`: 掘金量化API Token
- `GM_USERNAME`: 掘金量化用户名

### MongoDB配置

- `MONGODB_URI`: MongoDB连接URI
- `MONGODB_DATABASE`: 数据库名称
- `MONGODB_USERNAME`: 数据库用户名（可选）
- `MONGODB_PASSWORD`: 数据库密码（可选）

### 数据收集配置

- `COLLECTION_INTERVAL`: 数据收集间隔（秒）
- `MAX_RETRY_COUNT`: 最大重试次数
- `BATCH_SIZE`: 批量处理大小

### 代理配置

如果遇到网络问题，可以配置代理：

```env
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

## 数据类型

### Tick数据

实时行情快照数据，包含：
- 股票代码、价格、成交量等基本信息
- 买卖档数据（5档或10档）
- 时间戳和创建时间

### Bar数据

K线数据，支持多种频率：
- 1分钟、5分钟、15分钟
- 日线、周线、月线
- 开盘价、收盘价、最高价、最低价、成交量、成交额

## 定时任务

系统自动设置以下定时任务：

- **实时数据同步**: 交易时间每30秒执行一次，同步Tick数据和1分钟K线数据
- **定时全量同步**: 
  - 09:00: 开盘前全量同步所有数据
  - 12:00: 午盘前全量同步所有数据
  - 15:05: 收盘后全量同步所有数据
- **市场状态检查**: 每5分钟执行一次

### 数据同步策略

- **增量同步**: 实时数据每30秒同步，支持去重和增量入库
- **全量同步**: 在关键时间点进行全量数据同步，确保数据完整性
- **智能去重**: 基于数据哈希值自动去重，避免重复数据

## 去重机制

系统使用数据哈希值进行去重：

1. **Tick数据**: 基于股票代码、价格、时间、成交量生成哈希，存储在`tick`集合
2. **K线数据**: 基于股票代码、时间、OHLC数据生成哈希，按频率分别存储：
   - `60s`集合: 1分钟K线数据
   - `300s`集合: 5分钟K线数据
   - `900s`集合: 15分钟K线数据
   - `1d`集合: 日线数据
3. **MongoDB索引**: 在每个集合的`data_hash`字段上创建唯一索引

## 日志系统

使用loguru进行日志管理：

- **控制台输出**: 彩色格式化日志
- **文件输出**: 自动轮转和压缩
- **日志级别**: 支持DEBUG、INFO、WARNING、ERROR
- **日志格式**: 包含时间、级别、模块、函数、行号等信息

## 测试

运行测试：

```bash
uv run pytest tests/
```

## 故障排除

### 常见问题

1. **掘金量化连接失败**
   - 检查Token和用户名是否正确
   - 确认网络连接和代理设置

2. **MongoDB连接失败**
   - 检查MongoDB服务是否启动
   - 验证连接字符串和认证信息

3. **数据收集失败**
   - 检查是否为交易时间
   - 查看日志了解具体错误信息

### 日志查看

```bash
# 查看实时日志
tail -f logs/stock_collector.log

# 查看错误日志
grep ERROR logs/stock_collector.log
```

## 开发说明

### 添加新的数据类型

1. 在`src/models/stock_data.py`中定义新的数据模型
2. 在`src/collectors/gm_collector.py`中实现数据获取逻辑
3. 在`src/database/mongodb_client.py`中添加存储方法
4. 在`src/scheduler/data_scheduler.py`中添加调度任务

### 自定义调度策略

```python
from src.scheduler.data_scheduler import DataScheduler

scheduler = DataScheduler()

# 添加自定义任务
def custom_task():
    print("执行自定义任务")

scheduler.add_custom_task(custom_task, 'minutes')
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至：[your-email@example.com]
