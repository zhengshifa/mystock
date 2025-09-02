# MyStock API 文档

本文档详细描述了 MyStock 股票数据同步系统的所有 API 接口。

## 目录

- [同步管理器 API](#同步管理器-api)
- [调度系统 API](#调度系统-api)
- [配置管理器 API](#配置管理器-api)
- [数据库操作 API](#数据库操作-api)
- [掘金API客户端](#掘金api客户端)
- [数据处理器 API](#数据处理器-api)
- [工具类 API](#工具类-api)

## 同步管理器 API

### SyncManager

股票数据同步的核心管理器。

#### 初始化

```python
from src.sync.sync_manager import SyncManager
from src.config_manager import ConfigManager

config_manager = ConfigManager()
sync_manager = SyncManager(config_manager)
```

#### 方法

##### `start_realtime_sync(symbols: List[str] = None) -> None`

启动实时数据同步。

**参数:**
- `symbols` (List[str], 可选): 要同步的股票代码列表，默认使用配置中的股票列表

**示例:**
```python
# 同步指定股票
sync_manager.start_realtime_sync(["000001.SZ", "600000.SH"])

# 同步配置中的所有股票
sync_manager.start_realtime_sync()
```

##### `stop_realtime_sync() -> None`

停止实时数据同步。

**示例:**
```python
sync_manager.stop_realtime_sync()
```

##### `sync_historical_data(symbols: List[str], start_date: str, end_date: str, data_types: List[str] = None) -> Dict[str, Any]`

同步历史数据。

**参数:**
- `symbols` (List[str]): 股票代码列表
- `start_date` (str): 开始日期，格式: "YYYY-MM-DD"
- `end_date` (str): 结束日期，格式: "YYYY-MM-DD"
- `data_types` (List[str], 可选): 数据类型列表，默认: ["basic", "kline", "financial"]

**返回:**
- Dict[str, Any]: 同步结果统计

**示例:**
```python
result = sync_manager.sync_historical_data(
    symbols=["000001.SZ", "600000.SH"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    data_types=["basic", "kline"]
)
print(f"同步完成: {result['total_records']} 条记录")
```

##### `sync_incremental_data(symbols: List[str] = None, lookback_days: int = 7) -> Dict[str, Any]`

执行增量数据同步。

**参数:**
- `symbols` (List[str], 可选): 股票代码列表
- `lookback_days` (int): 回溯天数，默认7天

**返回:**
- Dict[str, Any]: 同步结果统计

**示例:**
```python
result = sync_manager.sync_incremental_data(
    symbols=["000001.SZ"],
    lookback_days=3
)
```

##### `get_sync_status() -> Dict[str, Any]`

获取同步状态信息。

**返回:**
- Dict[str, Any]: 同步状态信息

**示例:**
```python
status = sync_manager.get_sync_status()
print(f"实时同步状态: {status['realtime']['status']}")
print(f"最后同步时间: {status['last_sync_time']}")
```

##### `get_sync_statistics() -> Dict[str, Any]`

获取同步统计信息。

**返回:**
- Dict[str, Any]: 统计信息

**示例:**
```python
stats = sync_manager.get_sync_statistics()
print(f"总同步记录数: {stats['total_records']}")
print(f"成功率: {stats['success_rate']}%")
```

## 调度系统 API

### TaskScheduler

任务调度器，支持定时任务和周期性任务。

#### 初始化

```python
from src.scheduler import TaskScheduler, ScheduledTask
from datetime import timedelta

scheduler = TaskScheduler(max_workers=10)
```

#### 方法

##### `add_task(task: ScheduledTask) -> str`

添加调度任务。

**参数:**
- `task` (ScheduledTask): 任务对象

**返回:**
- str: 任务ID

**示例:**
```python
task = ScheduledTask(
    name="daily_sync",
    func=sync_manager.sync_daily_data,
    interval=timedelta(hours=24),
    enabled=True,
    max_retries=3
)

task_id = scheduler.add_task(task)
```

##### `remove_task(task_id: str) -> bool`

移除任务。

**参数:**
- `task_id` (str): 任务ID

**返回:**
- bool: 是否成功移除

##### `start() -> None`

启动调度器。

##### `stop() -> None`

停止调度器。

##### `get_task_status(task_id: str) -> TaskStatus`

获取任务状态。

**参数:**
- `task_id` (str): 任务ID

**返回:**
- TaskStatus: 任务状态枚举

### CronScheduler

Cron表达式调度器。

#### 初始化

```python
from src.scheduler import CronScheduler, CronJob

cron_scheduler = CronScheduler()
```

#### 方法

##### `add_job(job: CronJob) -> str`

添加Cron任务。

**参数:**
- `job` (CronJob): Cron任务对象

**返回:**
- str: 任务ID

**示例:**
```python
# 每个交易日9:00执行
job = CronJob(
    name="market_open_sync",
    func=sync_manager.sync_market_data,
    cron_expression="0 9 * * 1-5",
    enabled=True
)

job_id = cron_scheduler.add_job(job)
```

### JobManager

作业管理器，支持作业队列和批处理。

#### 初始化

```python
from src.scheduler import JobManager, Job, JobType

job_manager = JobManager()
```

#### 方法

##### `submit_job(job: Job) -> str`

提交作业。

**参数:**
- `job` (Job): 作业对象

**返回:**
- str: 作业ID

**示例:**
```python
job = Job(
    name="sync_stock_data",
    job_type=JobType.DATA_SYNC,
    func=sync_manager.sync_historical_data,
    args=(["000001.SZ"], "2023-01-01", "2023-12-31"),
    priority=1
)

job_id = job_manager.submit_job(job)
```

### TaskMonitor

任务监控器，提供性能监控和告警功能。

#### 初始化

```python
from src.scheduler import TaskMonitor

monitor = TaskMonitor()
```

#### 方法

##### `check_health() -> HealthStatus`

检查系统健康状态。

**返回:**
- HealthStatus: 健康状态对象

**示例:**
```python
health = monitor.check_health()
print(f"系统状态: {health.status}")
print(f"CPU使用率: {health.cpu_usage}%")
print(f"内存使用率: {health.memory_usage}%")
```

##### `get_metrics(task_id: str = None) -> TaskMetrics`

获取任务指标。

**参数:**
- `task_id` (str, 可选): 任务ID，为空时返回全局指标

**返回:**
- TaskMetrics: 任务指标对象

## 配置管理器 API

### ConfigManager

配置管理器，支持多环境配置、动态更新和验证。

#### 初始化

```python
from src.config_manager import ConfigManager, ConfigManagerOptions

options = ConfigManagerOptions(
    config_dir="./config",
    env_prefix="MYSTOCK_",
    auto_reload=True
)

config_manager = ConfigManager(options)
```

#### 方法

##### `load_config(config_path: Union[str, Path], namespace: str = "default") -> Dict[str, Any]`

加载配置文件。

**参数:**
- `config_path` (Union[str, Path]): 配置文件路径
- `namespace` (str): 命名空间

**返回:**
- Dict[str, Any]: 配置字典

**示例:**
```python
config = config_manager.load_config("config.json", "production")
```

##### `get(key: str, default: Any = None, namespace: str = "default") -> Any`

获取配置值。

**参数:**
- `key` (str): 配置键，支持点分隔的嵌套键
- `default` (Any): 默认值
- `namespace` (str): 命名空间

**返回:**
- Any: 配置值

**示例:**
```python
db_host = config_manager.get("database.host", "localhost")
api_timeout = config_manager.get("gm_api.timeout", 30)
```

##### `set(key: str, value: Any, namespace: str = "default", persist: bool = False) -> None`

设置配置值。

**参数:**
- `key` (str): 配置键
- `value` (Any): 配置值
- `namespace` (str): 命名空间
- `persist` (bool): 是否持久化到文件

**示例:**
```python
config_manager.set("database.port", 27018, persist=True)
```

##### `validate_config(namespace: str = "default") -> ValidationResult`

验证配置。

**参数:**
- `namespace` (str): 命名空间

**返回:**
- ValidationResult: 验证结果

**示例:**
```python
result = config_manager.validate_config("production")
if not result.is_valid:
    print(f"配置验证失败: {result.errors}")
```

## 数据库操作 API

### DatabaseManager

数据库管理器，封装MongoDB操作。

#### 初始化

```python
from src.database import DatabaseManager

db_manager = DatabaseManager(config_manager)
```

#### 方法

##### `connect() -> None`

连接数据库。

##### `disconnect() -> None`

断开数据库连接。

##### `insert_one(collection: str, document: Dict[str, Any]) -> str`

插入单个文档。

**参数:**
- `collection` (str): 集合名称
- `document` (Dict[str, Any]): 文档数据

**返回:**
- str: 文档ID

**示例:**
```python
doc_id = db_manager.insert_one("stocks", {
    "symbol": "000001.SZ",
    "name": "平安银行",
    "market": "深交所"
})
```

##### `insert_many(collection: str, documents: List[Dict[str, Any]]) -> List[str]`

批量插入文档。

**参数:**
- `collection` (str): 集合名称
- `documents` (List[Dict[str, Any]]): 文档列表

**返回:**
- List[str]: 文档ID列表

##### `find_one(collection: str, filter_dict: Dict[str, Any] = None) -> Optional[Dict[str, Any]]`

查找单个文档。

**参数:**
- `collection` (str): 集合名称
- `filter_dict` (Dict[str, Any]): 查询条件

**返回:**
- Optional[Dict[str, Any]]: 文档数据或None

**示例:**
```python
stock = db_manager.find_one("stocks", {"symbol": "000001.SZ"})
if stock:
    print(f"股票名称: {stock['name']}")
```

##### `find_many(collection: str, filter_dict: Dict[str, Any] = None, limit: int = None) -> List[Dict[str, Any]]`

查找多个文档。

**参数:**
- `collection` (str): 集合名称
- `filter_dict` (Dict[str, Any]): 查询条件
- `limit` (int): 限制数量

**返回:**
- List[Dict[str, Any]]: 文档列表

##### `update_one(collection: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> bool`

更新单个文档。

**参数:**
- `collection` (str): 集合名称
- `filter_dict` (Dict[str, Any]): 查询条件
- `update_dict` (Dict[str, Any]): 更新数据

**返回:**
- bool: 是否成功更新

**示例:**
```python
success = db_manager.update_one(
    "stocks",
    {"symbol": "000001.SZ"},
    {"$set": {"last_updated": datetime.now()}}
)
```

##### `delete_one(collection: str, filter_dict: Dict[str, Any]) -> bool`

删除单个文档。

**参数:**
- `collection` (str): 集合名称
- `filter_dict` (Dict[str, Any]): 查询条件

**返回:**
- bool: 是否成功删除

## 掘金API客户端

### GMAPIClient

掘金量化API客户端。

#### 初始化

```python
from src.gm_api import GMAPIClient

client = GMAPIClient(config_manager)
```

#### 方法

##### `get_instruments(exchanges: List[str] = None) -> List[Dict[str, Any]]`

获取股票列表。

**参数:**
- `exchanges` (List[str], 可选): 交易所列表

**返回:**
- List[Dict[str, Any]]: 股票信息列表

**示例:**
```python
# 获取沪深股票
stocks = client.get_instruments(["SHSE", "SZSE"])
for stock in stocks:
    print(f"{stock['symbol']}: {stock['sec_name']}")
```

##### `get_history_data(symbol: str, start_date: str, end_date: str, frequency: str = "1d") -> List[Dict[str, Any]]`

获取历史K线数据。

**参数:**
- `symbol` (str): 股票代码
- `start_date` (str): 开始日期
- `end_date` (str): 结束日期
- `frequency` (str): 频率，默认"1d"

**返回:**
- List[Dict[str, Any]]: K线数据列表

**示例:**
```python
klines = client.get_history_data(
    "000001.SZ",
    "2023-01-01",
    "2023-12-31",
    "1d"
)
```

##### `get_realtime_data(symbols: List[str]) -> List[Dict[str, Any]]`

获取实时数据。

**参数:**
- `symbols` (List[str]): 股票代码列表

**返回:**
- List[Dict[str, Any]]: 实时数据列表

**示例:**
```python
realtime_data = client.get_realtime_data(["000001.SZ", "600000.SH"])
for data in realtime_data:
    print(f"{data['symbol']}: {data['price']}")
```

##### `get_financial_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]`

获取财务数据。

**参数:**
- `symbol` (str): 股票代码
- `start_date` (str): 开始日期
- `end_date` (str): 结束日期

**返回:**
- List[Dict[str, Any]]: 财务数据列表

## 数据处理器 API

### BaseProcessor

数据处理器基类。

#### 方法

##### `process(data: Any) -> Any`

处理数据的抽象方法。

**参数:**
- `data` (Any): 输入数据

**返回:**
- Any: 处理后的数据

### StockProcessor

股票基础信息处理器。

#### 初始化

```python
from src.data_processor import StockProcessor

processor = StockProcessor()
```

#### 方法

##### `process_stock_info(raw_data: Dict[str, Any]) -> Dict[str, Any]`

处理股票基础信息。

**参数:**
- `raw_data` (Dict[str, Any]): 原始数据

**返回:**
- Dict[str, Any]: 处理后的股票信息

### KlineProcessor

K线数据处理器。

#### 方法

##### `process_kline_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]`

处理K线数据。

**参数:**
- `raw_data` (List[Dict[str, Any]]): 原始K线数据

**返回:**
- List[Dict[str, Any]]: 处理后的K线数据

**示例:**
```python
from src.data_processor import KlineProcessor

processor = KlineProcessor()
processed_klines = processor.process_kline_data(raw_klines)
```

## 工具类 API

### TimeUtils

时间工具类。

#### 方法

##### `now(timezone_name: str = 'CST') -> datetime`

获取当前时间。

**参数:**
- `timezone_name` (str): 时区名称

**返回:**
- datetime: 当前时间

**示例:**
```python
from src.utils import TimeUtils

current_time = TimeUtils.now('CST')
print(f"当前时间: {current_time}")
```

##### `is_trading_time(dt: datetime, market: str = 'A股') -> bool`

判断是否为交易时间。

**参数:**
- `dt` (datetime): 时间对象
- `market` (str): 市场名称

**返回:**
- bool: 是否为交易时间

**示例:**
```python
from datetime import datetime
from src.utils import TimeUtils

now = datetime.now()
is_trading = TimeUtils.is_trading_time(now, 'A股')
print(f"当前是否为交易时间: {is_trading}")
```

##### `get_trading_days_between(start_date: Union[str, date], end_date: Union[str, date]) -> List[date]`

获取两个日期之间的交易日。

**参数:**
- `start_date` (Union[str, date]): 开始日期
- `end_date` (Union[str, date]): 结束日期

**返回:**
- List[date]: 交易日列表

### DataValidator

数据验证器。

#### 方法

##### `validate_symbol(symbol: str) -> Tuple[str, str]`

验证股票代码。

**参数:**
- `symbol` (str): 股票代码

**返回:**
- Tuple[str, str]: (股票类型, 交易所)

**示例:**
```python
from src.utils import DataValidator

stock_type, exchange = DataValidator.validate_symbol("000001.SZ")
print(f"股票类型: {stock_type}, 交易所: {exchange}")
```

##### `validate_date_range(start_date: str, end_date: str) -> bool`

验证日期范围。

**参数:**
- `start_date` (str): 开始日期
- `end_date` (str): 结束日期

**返回:**
- bool: 是否有效

### Logger

日志工具。

#### 方法

##### `get_logger(name: str, level: str = 'INFO') -> logging.Logger`

获取日志器。

**参数:**
- `name` (str): 日志器名称
- `level` (str): 日志级别

**返回:**
- logging.Logger: 日志器对象

**示例:**
```python
from src.utils import get_logger

logger = get_logger("MyApp", "DEBUG")
logger.info("应用启动")
logger.error("发生错误")
```

## 异常处理

### 异常类型

- `ValidationError`: 数据验证异常
- `SymbolValidationError`: 股票代码验证异常
- `DateValidationError`: 日期验证异常
- `DataFormatError`: 数据格式异常
- `ConfigValidationError`: 配置验证异常
- `DatabaseError`: 数据库操作异常
- `APIError`: API调用异常
- `SyncError`: 数据同步异常

### 异常处理示例

```python
from src.utils.exceptions import ValidationError, APIError

try:
    sync_manager.sync_historical_data(
        symbols=["INVALID.CODE"],
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
except ValidationError as e:
    print(f"数据验证错误: {e.message}")
    print(f"错误字段: {e.field}")
except APIError as e:
    print(f"API调用错误: {e.message}")
    print(f"错误代码: {e.error_code}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 最佳实践

### 1. 错误处理

```python
# 使用上下文管理器
with sync_manager:
    sync_manager.start_realtime_sync()
    # 自动清理资源

# 异常重试
from src.utils.retry import retry_on_exception

@retry_on_exception(max_retries=3, delay=1)
def sync_with_retry():
    return sync_manager.sync_historical_data(...)
```

### 2. 配置管理

```python
# 使用环境变量覆盖配置
config_manager.load_config("config.json")
config_manager.set("database.host", os.getenv("DB_HOST", "localhost"))

# 配置验证
result = config_manager.validate_config()
if not result.is_valid:
    raise ConfigValidationError(f"配置无效: {result.errors}")
```

### 3. 性能优化

```python
# 批量操作
batch_size = config_manager.get("sync.batch_size", 1000)
for batch in chunks(symbols, batch_size):
    sync_manager.sync_batch_data(batch)

# 异步处理
import asyncio

async def async_sync():
    tasks = []
    for symbol in symbols:
        task = asyncio.create_task(sync_manager.sync_symbol_data(symbol))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

### 4. 监控和告警

```python
# 添加性能监控
monitor = TaskMonitor()
monitor.add_alert_rule(AlertRule(
    name="high_cpu_usage",
    condition=lambda metrics: metrics.cpu_usage > 80,
    level=AlertLevel.WARNING
))

# 自定义告警处理
def email_alert_handler(alert):
    send_email(
        to="admin@example.com",
        subject=f"系统告警: {alert.message}",
        body=f"告警级别: {alert.level}\n时间: {alert.timestamp}"
    )

monitor.add_alert_handler(email_alert_handler)
```

---

更多详细信息请参考源代码注释和示例代码。