# 调度配置管理架构说明

## 概述

本项目已经成功将调度时间、频率等配置从代码中解耦出来，创建了一个完整的配置管理架构。现在所有的调度配置都可以通过配置文件进行管理，无需修改代码。

## 架构组件

### 1. 配置模型层 (`src/config/scheduler_config.py`)

#### 核心类
- **`TaskSchedule`**: 单个任务的调度配置模型
- **`DataCollectionConfig`**: 数据收集配置模型
- **`SchedulerConfig`**: 调度器总配置模型
- **`SchedulerConfigManager`**: 配置管理器

#### 配置项包括
- 任务调度配置（时间、频率、启用状态）
- 数据收集配置（间隔、频率、股票列表）
- 交易时间配置
- 调度器运行参数

### 2. YAML配置加载器 (`src/config/yaml_loader.py`)

#### 功能特性
- 支持YAML格式配置文件
- 配置缓存机制
- 支持点分隔的键路径访问
- 配置文件验证和重载

### 3. 配置管理工具 (`src/config/config_manager.py`)

#### 主要功能
- 动态更新配置
- 股票代码管理
- 任务调度管理
- 配置导入导出
- 实时配置重载

### 4. 命令行管理工具 (`config_manager.py`)

#### 交互式功能
- 查看当前配置
- 管理股票代码
- 管理任务调度
- 管理数据收集
- 管理交易时间
- 配置导入导出

## 配置文件结构

### 主配置文件: `config/scheduler_config.yaml`

```yaml
# 数据收集配置
data_collection:
  realtime_tick_interval: 30      # Tick数据收集间隔(秒)
  realtime_bar_interval: 60       # Bar数据收集间隔(秒)
  daily_sync_times:               # 每日同步时间点
    - "09:00"
    - "12:00"
    - "15:05"
  supported_frequencies:          # 支持的数据频率
    - "60s"
    - "300s"
    - "900s"
    - "1d"
  default_sh_symbols:            # 上海市场股票代码
    - "600000"
    - "600036"
  default_sz_symbols:            # 深圳市场股票代码
    - "000001"
    - "000002"
  trading_hours:                  # 交易时间配置
    morning: ["09:30", "11:30"]
    afternoon: ["13:00", "15:00"]

# 任务调度配置
tasks:
  - name: "实时数据同步"
    enabled: true
    interval_type: "seconds"
    interval_value: 30
    description: "交易时间每30秒同步实时数据"

# 调度器运行配置
scheduler:
  sleep_interval: 1
  exception_wait: 5
  max_retry_count: 3
```

## 使用方法

### 1. 启动配置管理工具

```bash
# 使用uv运行
uv run python config_manager.py
```

### 2. 动态调整配置

#### 添加股票代码
```python
from src.config.config_manager import get_config_manager

config_manager = get_config_manager()
config_manager.add_stock_symbol("SH", "600519")
```

#### 修改任务间隔
```python
config_manager.update_task_schedule("实时数据同步", interval_value=60)
```

#### 更新交易时间
```python
new_trading_hours = {
    "morning": ["09:00", "11:30"],
    "afternoon": ["13:00", "15:30"]
}
config_manager.update_trading_hours(new_trading_hours)
```

### 3. 配置重载

```python
# 重新加载配置文件
config_manager.reload_config()

# 调度器重新加载配置
scheduler.reload_config()
```

## 配置热更新

### 1. 自动配置重载
调度器支持运行时重新加载配置，无需重启程序：

```python
# 在调度器中
def reload_config(self) -> bool:
    if self.scheduler_config.reload_config():
        # 更新股票列表
        self.default_symbols = self.scheduler_config.get_stock_symbols()
        return True
    return False
```

### 2. 配置变更通知
当配置文件发生变化时，可以通过以下方式通知系统：

```python
# 监听配置文件变化
import time
import os

def watch_config_file(config_file):
    last_modified = os.path.getmtime(config_file)
    while True:
        time.sleep(5)  # 每5秒检查一次
        current_modified = os.path.getmtime(config_file)
        if current_modified > last_modified:
            print("配置文件已更新，正在重新加载...")
            config_manager.reload_config()
            last_modified = current_modified
```

## 配置验证

### 1. 数据类型验证
使用Pydantic模型确保配置数据的类型安全：

```python
class TaskSchedule(BaseModel):
    name: str
    enabled: bool
    interval_type: str
    interval_value: int
    at_time: Optional[str] = None
```

### 2. 业务规则验证
在配置管理器中添加业务逻辑验证：

```python
def validate_stock_symbol(self, symbol: str) -> bool:
    """验证股票代码格式"""
    if len(symbol) != 6 or not symbol.isdigit():
        return False
    
    valid_prefixes = ['00', '30', '60', '68']
    if not any(symbol.startswith(prefix) for prefix in valid_prefixes):
        return False
    
    return True
```

## 配置备份与恢复

### 1. 配置导出
```python
# 导出当前配置到JSON文件
config_manager.export_config("backup_config.json")
```

### 2. 配置导入
```python
# 从JSON文件导入配置
config_manager.import_config("backup_config.json")
```

### 3. 版本控制
建议将配置文件纳入版本控制：

```bash
# 添加到git
git add config/scheduler_config.yaml
git commit -m "更新调度配置"

# 创建配置分支
git checkout -b config/feature/new-schedule
```

## 性能优化

### 1. 配置缓存
YAML加载器实现了配置缓存机制，避免重复读取文件：

```python
# 检查缓存
if cache_key in self.config_cache:
    return self.config_cache[cache_key]

# 缓存配置
self.config_cache[cache_key] = config_data
```

### 2. 延迟初始化
配置管理器使用延迟初始化模式：

```python
# 全局配置实例 - 延迟初始化
scheduler_config_manager = None

def get_scheduler_config() -> SchedulerConfigManager:
    global scheduler_config_manager
    if scheduler_config_manager is None:
        scheduler_config_manager = SchedulerConfigManager()
    return scheduler_config_manager
```

## 错误处理

### 1. 配置加载失败
当配置文件加载失败时，系统会自动使用默认配置：

```python
def _load_config(self) -> SchedulerConfig:
    try:
        yaml_config = self.yaml_loader.load_config(self.config_file)
        if yaml_config:
            return self._convert_yaml_to_config(yaml_config)
    except Exception as e:
        print(f"从YAML文件加载配置失败，使用默认配置: {e}")
    
    # 使用默认配置
    return self._load_default_config()
```

### 2. 配置验证失败
配置验证失败时会记录详细错误信息：

```python
try:
    config = self.scheduler_config.get_config()
    return config.dict()
except Exception as e:
    self.logger.error(f"获取当前配置失败: {e}")
    return {}
```

## 扩展性

### 1. 添加新的配置项
在配置模型中添加新字段：

```python
class DataCollectionConfig(BaseModel):
    # 现有配置...
    
    # 新增配置
    enable_alerting: bool = Field(True, description="是否启用告警")
    alert_threshold: float = Field(0.8, description="告警阈值")
```

### 2. 添加新的任务类型
在任务配置中添加新的任务：

```yaml
tasks:
  # 现有任务...
  
  - name: "数据质量检查"
    enabled: true
    interval_type: "hours"
    interval_value: 1
    description: "每小时检查数据质量"
```

## 最佳实践

### 1. 配置文件管理
- 使用有意义的配置项名称
- 添加详细的注释说明
- 定期备份配置文件
- 使用版本控制管理配置变更

### 2. 配置更新策略
- 在非交易时间更新配置
- 更新后验证配置有效性
- 保留配置更新历史记录
- 实现配置回滚机制

### 3. 监控与告警
- 监控配置文件变化
- 记录配置更新操作
- 配置异常时发送告警
- 定期检查配置一致性

## 总结

通过这次重构，我们成功实现了：

1. **配置解耦**: 所有调度相关配置都从代码中分离出来
2. **动态配置**: 支持运行时修改配置，无需重启程序
3. **配置管理**: 提供了完整的配置管理工具和命令行界面
4. **配置验证**: 使用Pydantic确保配置数据的类型安全
5. **配置持久化**: 支持配置的导入导出和版本控制
6. **扩展性**: 架构设计支持轻松添加新的配置项和功能

这种架构使得系统更加灵活、可维护，并且为未来的功能扩展奠定了良好的基础。
