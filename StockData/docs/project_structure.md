# 股票数据采集系统 - 项目结构说明

## 重构概述

本项目已从原有的单体架构重构为模块化架构，按数据类型和功能职责进行清晰分离，提高了代码的可维护性和可扩展性。

## 新的目录结构

```
src/
├── __init__.py                 # 模块初始化文件
├── main.py                     # 主入口文件，整合所有模块
├── market_data/                # 市场数据模块
│   ├── __init__.py
│   ├── tick_collector.py       # Tick数据采集器
│   ├── bar_collector.py        # Bar数据采集器
│   └── market_analyzer.py      # 市场数据分析器
├── fundamentals/               # 基本面数据模块
│   ├── __init__.py
│   └── fundamentals_collector.py # 基本面数据采集器
├── realtime/                   # 实时数据模块
│   ├── __init__.py
│   └── realtime_collector.py   # 实时数据采集器
├── scheduler/                  # 调度器模块
│   ├── __init__.py
│   └── scheduler.py            # 任务调度器
└── services/                   # 服务模块
    ├── __init__.py
    └── data_model_service.py   # 数据模型服务
```

## 模块说明

### 1. 市场数据模块 (`market_data/`)

**功能**: 处理Tick数据、Bar数据等市场行情数据

- **`tick_collector.py`**: Tick数据采集器
  - 获取历史Tick数据
  - 多标的Tick数据采集
  - Tick数据存储到MongoDB
  
- **`bar_collector.py`**: Bar数据采集器
  - 获取各种频率的Bar数据
  - 多频率数据采集
  - 按频率分别存储到不同集合
  
- **`market_analyzer.py`**: 市场数据分析器
  - Tick数据分析
  - Bar数据分析
  - 技术指标计算（RSI、SMA等）
  - 市场报告生成

### 2. 基本面数据模块 (`fundamentals/`)

**功能**: 处理财务报表等基本面数据

- **`fundamentals_collector.py`**: 基本面数据采集器
  - 资产负债表数据采集
  - 利润表数据采集
  - 现金流量表数据采集
  - 数据验证和清理
  - 索引管理

### 3. 实时数据模块 (`realtime/`)

**功能**: 处理实时行情数据

- **`realtime_collector.py`**: 实时数据采集器
  - 实时行情数据获取
  - 买卖盘口数据处理
  - 市场概览生成
  - 实时数据存储

### 4. 调度器模块 (`scheduler/`)

**功能**: 管理和调度各种数据采集任务

- **`scheduler.py`**: 任务调度器
  - 定时任务管理
  - 手动任务执行
  - 数据接口统一管理
  - 任务状态监控

### 5. 服务模块 (`services/`)

**功能**: 提供核心服务功能

- **`data_model_service.py`**: 数据模型服务
  - 各种数据模型的创建
  - 数据验证和转换
  - 模型实例管理

### 6. 主入口模块 (`main.py`)

**功能**: 系统主控制器，整合所有模块

- 统一的命令行接口
- 系统初始化和状态管理
- 任务执行控制
- 演示程序

## 重构优势

### 1. 清晰的职责分离
- 每个模块专注于特定类型的数据处理
- 避免了功能重叠和代码重复
- 便于单独测试和维护

### 2. 模块化设计
- 模块间通过明确的接口进行交互
- 支持独立开发和部署
- 便于功能扩展和定制

### 3. 统一的接口管理
- `StockDataInterface` 统一管理所有采集器
- 提供一致的数据采集接口
- 简化了调度器的实现

### 4. 更好的可维护性
- 代码结构清晰，易于理解
- 模块化设计便于问题定位
- 支持增量重构和优化

## 使用方法

### 1. 运行演示程序
```bash
uv run python src/main.py --task demo
```

### 2. 启动自动调度器
```bash
uv run python src/main.py --task scheduler
```

### 3. 执行特定任务
```bash
# 采集Tick数据
uv run python src/main.py --task tick --symbols SZSE.000001 SZSE.000002

# 采集Bar数据
uv run python src/main.py --task bar --symbols SHSE.600000 --frequencies 1d 1h

# 采集基本面数据
uv run python src/main.py --task fundamentals --symbols SZSE.000001

# 采集实时数据
uv run python src/main.py --task realtime --symbols SZSE.000001

# 采集所有类型数据
uv run python src/main.py --task all --symbols SZSE.000001
```

### 4. 编程接口使用
```python
from src import StockDataSystem

# 创建系统实例
system = StockDataSystem()
system.initialize()

# 执行数据采集任务
result = system.run_collection_task('tick', ['SZSE.000001'])
print(result)

# 启动调度器
system.start_scheduler()
```

## 配置说明

系统配置仍然使用原有的配置文件结构，主要配置项包括：

- **股票代码列表**: `config.scheduler.stock_symbols`
- **数据库连接**: `config.mongodb.*`
- **GM SDK配置**: `config.gm_sdk.*`
- **数据保留策略**: `config.data.*`

## 迁移指南

### 从旧版本迁移

1. **导入路径更新**:
   ```python
   # 旧版本
   from src.current_data import FullStockDataCollector
   from src.tick_data_service import TickDataCollector
   
   # 新版本
   from src.market_data import TickDataCollector
   from src.realtime import RealtimeDataCollector
   ```

2. **类名更新**:
   ```python
   # 旧版本
   collector = FullStockDataCollector()
   
   # 新版本
   collector = TickDataCollector()  # 或 RealtimeDataCollector()
   ```

3. **方法调用更新**:
   ```python
   # 旧版本
   collector.collect_and_save_tick_data(...)
   
   # 新版本
   collector.collect_and_save_tick_data(...)  # 方法名保持不变
   ```

## 扩展开发

### 添加新的数据类型模块

1. 在 `src/` 下创建新的模块目录
2. 实现相应的采集器类
3. 在 `src/__init__.py` 中导入新模块
4. 在 `StockDataInterface` 中集成新采集器

### 添加新的分析功能

1. 在相应的模块中添加分析方法
2. 或创建新的分析器模块
3. 在调度器中集成新的分析任务

## 注意事项

1. **依赖管理**: 确保使用 `uv` 管理Python环境
2. **配置检查**: 运行前检查配置文件是否正确
3. **数据库连接**: 确保MongoDB服务正常运行
4. **GM SDK**: 确保GM SDK配置正确且有有效token
5. **日志监控**: 关注日志输出，及时发现问题

## 版本信息

- **当前版本**: 2.0.0
- **重构日期**: 2024年
- **架构**: 模块化架构
- **兼容性**: 向后兼容，支持渐进式迁移
