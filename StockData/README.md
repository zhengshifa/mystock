# MyStock 股票数据同步系统

一个基于掘金量化API和MongoDB的股票数据同步系统，支持实时数据获取、历史数据同步、智能调度和配置管理。

## 🚀 功能特性

### 核心功能
- **多市场支持**: 支持A股、港股、美股等多个市场的数据获取
- **实时数据同步**: 30秒间隔的实时数据更新
- **历史数据回补**: 智能的历史数据增量同步
- **数据类型丰富**: 支持股票基本信息、K线数据、财务数据、分红数据等

### 技术特性
- **高性能**: 基于异步编程和批量处理
- **高可靠**: 完善的错误处理和重试机制
- **易扩展**: 模块化设计，支持自定义数据处理器
- **智能调度**: 支持定时任务、Cron表达式和动态调度
- **配置管理**: 支持多环境配置、动态更新和验证
- **日志系统**: 完整的日志记录和监控

## 📋 系统要求

- Python 3.8+
- MongoDB 4.4+
- 掘金量化API账户

## 🛠️ 安装部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd mystock-v2/mystock/StockData
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境

#### 创建配置文件
```bash
cp config/config.example.json config/config.json
```

#### 编辑配置文件
```json
{
  "database": {
    "host": "localhost",
    "port": 27017,
    "name": "mystock",
    "username": "your_username",
    "password": "your_password"
  },
  "gm_api": {
    "token": "your_gm_token_here",
    "timeout": 30,
    "retry_count": 3
  },
  "sync": {
    "interval": 30,
    "batch_size": 1000,
    "enabled": true
  },
  "logging": {
    "level": "INFO",
    "file": "./logs/mystock.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

#### 环境变量配置
```bash
# 掘金量化认证配置
export GM_AUTH_TYPE="token"  # 认证类型: username_password 或 token
export GM_TOKEN="your_gm_token_here"  # Token认证时使用
export GM_USERNAME="your_gm_username"  # 用户名密码认证时使用
export GM_PASSWORD="your_gm_password"  # 用户名密码认证时使用

# 数据库配置
export MONGO_HOST="localhost"
export MONGO_PORT="27017"
export MONGO_USERNAME="admin"
export MONGO_PASSWORD="your_db_password"
export MONGO_DATABASE="stock_data"
export MONGO_AUTH_SOURCE="admin"

# 系统配置
export ENVIRONMENT="production"
export DEBUG="false"
export LOG_LEVEL="INFO"
```

### 4. 初始化数据库
```bash
python -m src.database.init_db
```

## 🎯 快速开始

### 基础使用

```python
from src.sync.sync_manager import SyncManager
from src.config_manager import create_config_manager

# 创建配置管理器
config_manager = create_config_manager("./config")
config_manager.load_config("config.json")

# 创建同步管理器
sync_manager = SyncManager(config_manager)

# 启动实时数据同步
sync_manager.start_realtime_sync()

# 同步历史数据
sync_manager.sync_historical_data(
    symbols=["000001.SZ", "600000.SH"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

### 使用调度系统

```python
from src.scheduler import TaskScheduler, ScheduledTask
from datetime import timedelta

# 创建调度器
scheduler = TaskScheduler()

# 添加定时任务
task = ScheduledTask(
    name="daily_sync",
    func=sync_manager.sync_daily_data,
    interval=timedelta(hours=24),
    enabled=True
)

scheduler.add_task(task)
scheduler.start()
```

### 使用Cron调度

```python
from src.scheduler import CronScheduler, CronJob

# 创建Cron调度器
cron_scheduler = CronScheduler()

# 添加Cron任务 (每个交易日9:00执行)
cron_job = CronJob(
    name="market_open_sync",
    func=sync_manager.sync_market_data,
    cron_expression="0 9 * * 1-5",  # 周一到周五9点
    enabled=True
)

cron_scheduler.add_job(cron_job)
cron_scheduler.start()
```

## 📚 详细文档

### 模块说明

#### 1. 数据库模块 (`src/database/`)
- **connection.py**: MongoDB连接管理
- **models.py**: 数据模型定义
- **operations.py**: 数据库操作封装

#### 2. 掘金API模块 (`src/gm_api/`)
- **client.py**: API客户端封装
- **data_fetcher.py**: 数据获取器
- **rate_limiter.py**: 请求限流器

#### 3. 数据处理模块 (`src/data_processor/`)
- **base_processor.py**: 处理器基类
- **stock_processor.py**: 股票数据处理器
- **kline_processor.py**: K线数据处理器
- **financial_processor.py**: 财务数据处理器

#### 4. 同步模块 (`src/sync/`)
- **sync_manager.py**: 同步管理器
- **realtime_sync.py**: 实时同步
- **historical_sync.py**: 历史同步
- **incremental_sync.py**: 增量同步

#### 5. 调度模块 (`src/scheduler/`)
- **task_scheduler.py**: 任务调度器
- **job_manager.py**: 作业管理器
- **cron_scheduler.py**: Cron调度器
- **task_monitor.py**: 任务监控器

#### 6. 配置管理模块 (`src/config_manager/`)
- **config_manager.py**: 配置管理器
- **config_loader.py**: 配置加载器
- **config_validator.py**: 配置验证器
- **environment_config.py**: 环境配置
- **dynamic_config.py**: 动态配置

#### 7. 工具模块 (`src/utils/`)
- **logger.py**: 日志工具
- **time_utils.py**: 时间工具
- **validators.py**: 数据验证
- **exceptions.py**: 异常定义

### API参考

#### 同步管理器 API

```python
class SyncManager:
    def __init__(self, config_manager: ConfigManager)
    
    # 实时同步
    def start_realtime_sync(self, symbols: List[str] = None) -> None
    def stop_realtime_sync(self) -> None
    
    # 历史同步
    def sync_historical_data(self, symbols: List[str], 
                           start_date: str, end_date: str) -> None
    
    # 增量同步
    def sync_incremental_data(self, symbols: List[str] = None) -> None
    
    # 状态查询
    def get_sync_status(self) -> Dict[str, Any]
    def get_sync_statistics(self) -> Dict[str, Any]
```

#### 调度器 API

```python
class TaskScheduler:
    def __init__(self, max_workers: int = 10)
    
    # 任务管理
    def add_task(self, task: ScheduledTask) -> str
    def remove_task(self, task_id: str) -> bool
    def enable_task(self, task_id: str) -> bool
    def disable_task(self, task_id: str) -> bool
    
    # 调度控制
    def start(self) -> None
    def stop(self) -> None
    def pause(self) -> None
    def resume(self) -> None
    
    # 状态查询
    def get_task_status(self, task_id: str) -> TaskStatus
    def list_tasks(self) -> List[ScheduledTask]
    def get_statistics(self) -> Dict[str, Any]
```

#### 配置管理器 API

```python
class ConfigManager:
    def __init__(self, options: ConfigManagerOptions = None)
    
    # 配置加载
    def load_config(self, config_path: Union[str, Path], 
                   namespace: str = "default") -> Dict[str, Any]
    
    # 配置操作
    def get(self, key: str, default: Any = None, 
           namespace: str = "default") -> Any
    def set(self, key: str, value: Any, namespace: str = "default", 
           persist: bool = False) -> None
    
    # 配置管理
    def save_config(self, namespace: str = "default") -> None
    def reload(self, namespace: str = "default") -> None
    def validate_config(self, namespace: str = "default") -> ValidationResult
```

## 🔧 配置说明

### 主配置文件结构

```json
{
  "database": {
    "host": "数据库主机",
    "port": "数据库端口",
    "name": "数据库名称",
    "username": "用户名",
    "password": "密码",
    "auth_source": "认证数据库",
    "replica_set": "副本集名称",
    "ssl": false,
    "connection_timeout": 5000,
    "server_selection_timeout": 5000
  },
  "gm_api": {
    "token": "掘金API令牌",
    "base_url": "API基础URL",
    "timeout": 30,
    "retry_count": 3,
    "retry_delay": 1,
    "rate_limit": {
      "requests_per_second": 10,
      "burst_size": 20
    }
  },
  "sync": {
    "realtime": {
      "enabled": true,
      "interval": 30,
      "batch_size": 1000,
      "symbols": ["000001.SZ", "600000.SH"]
    },
    "historical": {
      "enabled": true,
      "batch_size": 5000,
      "parallel_workers": 4,
      "start_date": "2020-01-01"
    },
    "incremental": {
      "enabled": true,
      "check_interval": 3600,
      "lookback_days": 7
    }
  },
  "scheduler": {
    "enabled": true,
    "max_workers": 10,
    "task_timeout": 3600,
    "retry_count": 3,
    "monitor": {
      "enabled": true,
      "alert_threshold": 0.8,
      "health_check_interval": 60
    }
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
      "file": {
        "enabled": true,
        "filename": "./logs/mystock.log",
        "max_size": "10MB",
        "backup_count": 5,
        "encoding": "utf-8"
      },
      "console": {
        "enabled": true,
        "level": "INFO"
      }
    }
  }
}
```

### 环境变量配置

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| **掘金量化认证** | | |
| `GM_AUTH_TYPE` | 认证类型 (username_password/token) | username_password |
| `GM_TOKEN` | 掘金API令牌 (Token认证时使用) | 无 |
| `GM_USERNAME` | 掘金用户名 (用户名密码认证时使用) | 无 |
| `GM_PASSWORD` | 掘金密码 (用户名密码认证时使用) | 无 |
| **数据库配置** | | |
| `MONGO_HOST` | MongoDB主机 | localhost |
| `MONGO_PORT` | MongoDB端口 | 27017 |
| `MONGO_USERNAME` | MongoDB用户名 | admin |
| `MONGO_PASSWORD` | MongoDB密码 | 无 |
| `MONGO_DATABASE` | 数据库名称 | stock_data |
| `MONGO_AUTH_SOURCE` | 认证数据库 | admin |
| **系统配置** | | |
| `ENVIRONMENT` | 运行环境 | development |
| `DEBUG` | 调试模式 | false |
| `LOG_LEVEL` | 日志级别 | INFO |
| `API_RATE_LIMIT` | API限流 | 10 |
| `API_TIMEOUT` | API超时时间(秒) | 30 |
| `REALTIME_SYNC_INTERVAL` | 实时同步间隔(秒) | 30 |
| `HISTORY_BATCH_SIZE` | 历史数据批处理大小 | 1000 |

## 📊 监控和运维

### 日志监控

系统提供完整的日志记录，包括：
- 数据同步日志
- API调用日志
- 错误和异常日志
- 性能监控日志

### 健康检查

```python
from src.scheduler import TaskMonitor

# 创建任务监控器
monitor = TaskMonitor()

# 检查系统健康状态
health_status = monitor.check_health()
print(f"系统健康状态: {health_status.status}")

# 获取性能指标
metrics = monitor.get_metrics()
print(f"任务成功率: {metrics.success_rate}")
print(f"平均执行时间: {metrics.avg_execution_time}")
```

### 告警配置

```python
# 添加自定义告警处理器
def custom_alert_handler(alert):
    # 发送邮件、短信或其他通知
    print(f"告警: {alert.message}")

monitor.add_alert_handler(custom_alert_handler)
```

## 🚨 故障排除

### 常见问题

#### 1. 数据库连接失败
```
Error: MongoDB connection failed
```
**解决方案**:
- 检查MongoDB服务是否启动
- 验证连接配置是否正确
- 检查网络连接和防火墙设置

#### 2. API调用失败
```
Error: GM API request failed
```
**解决方案**:
- 检查API令牌是否有效
- 验证网络连接
- 检查API调用频率是否超限

#### 3. 数据同步异常
```
Error: Data sync failed
```
**解决方案**:
- 检查股票代码格式是否正确
- 验证日期范围是否合理
- 查看详细错误日志

### 调试模式

```python
# 启用调试模式
config_manager.set("logging.level", "DEBUG")
config_manager.set("gm_api.debug", True)
```

### 性能优化

1. **批处理大小调优**
   ```json
   {
     "sync": {
       "batch_size": 2000  // 根据系统性能调整
     }
   }
   ```

2. **并发工作线程**
   ```json
   {
     "sync": {
       "parallel_workers": 8  // 根据CPU核心数调整
     }
   }
   ```

3. **数据库连接池**
   ```json
   {
     "database": {
       "max_pool_size": 100,
       "min_pool_size": 10
     }
   }
   ```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果您遇到问题或需要帮助，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索 [Issues](../../issues)
3. 创建新的 [Issue](../../issues/new)

## 🔄 更新日志

### v2.0.0 (2024-01-XX)
- ✨ 新增配置管理模块
- ✨ 新增智能调度系统
- ✨ 新增任务监控和告警
- 🐛 修复数据同步异常问题
- 🚀 性能优化和稳定性提升

### v1.0.0 (2023-XX-XX)
- 🎉 初始版本发布
- ✨ 基础数据同步功能
- ✨ 掘金API集成
- ✨ MongoDB数据存储

---

**MyStock 股票数据同步系统** - 让股票数据管理更简单、更高效！