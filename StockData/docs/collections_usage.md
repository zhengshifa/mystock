# 数据集合使用说明

## 概述

本项目使用MongoDB存储股票数据，按照数据类型和频率分别存储到不同的集合中，确保数据组织清晰、查询高效。

## 集合结构

### 1. Tick数据集合
- **集合名称**: `tick_data_1m`
- **数据类型**: 1分钟级别的Tick数据
- **数据内容**: 包含价格、成交量、买卖盘、时间戳等详细信息
- **存储策略**: 按标的代码和时间进行去重存储

### 2. Bar数据集合（按频率分）
- **5分钟**: `bar_data_5m` - 5分钟K线数据
- **15分钟**: `bar_data_15m` - 15分钟K线数据  
- **1小时**: `bar_data_1h` - 1小时K线数据
- **1天**: `bar_data_1d` - 日K线数据

## 数据字段说明

### Tick数据字段 (tick_data_1m)
```json
{
  "symbol": "SZSE.000001",           // 标的代码
  "price": 12.34,                    // 最新价格
  "last_volume": 1000,               // 最新成交量
  "last_amount": 12340.0,            // 最新成交额
  "created_at": "2024-12-01T09:30:00", // 创建时间
  "saved_at": "2024-12-01T09:30:05",   // 保存时间
  "quotes": [                         // 买卖盘数据
    {
      "bid_p": 12.33,                // 买价
      "bid_v": 500,                  // 买量
      "ask_p": 12.35,                // 卖价
      "ask_v": 300                   // 卖量
    }
  ]
}
```

### Bar数据字段 (bar_data_5m, bar_data_15m, bar_data_1h, bar_data_1d)
```json
{
  "symbol": "SZSE.000001",           // 标的代码
  "frequency": "5m",                 // 频率标识
  "bob": "2024-12-01T09:30:00",     // 开始时间
  "eob": "2024-12-01T09:35:00",     // 结束时间
  "open": 12.30,                     // 开盘价
  "high": 12.40,                     // 最高价
  "low": 12.25,                      // 最低价
  "close": 12.35,                    // 收盘价
  "volume": 50000,                   // 成交量
  "amount": 617500.0,                // 成交额
  "saved_at": "2024-12-01T09:35:05" // 保存时间
}
```

## 使用方法

### 1. 运行数据采集

```bash
# 运行主要的tick数据服务
uv run python src/tick_data_service.py

# 运行专门的集合演示脚本
uv run python src/collection_demo.py
```

### 2. 数据存储流程

1. **Tick数据采集**: 自动存储到 `tick_data_1m` 集合
2. **Bar数据采集**: 根据频率自动存储到对应集合
   - 1分钟数据 → `tick_data_1m`
   - 5分钟数据 → `bar_data_5m`
   - 15分钟数据 → `bar_data_15m`
   - 1小时数据 → `bar_data_1h`
   - 1天数据 → `bar_data_1d`

### 3. 数据查询示例

#### 查询Tick数据
```python
from src.tick_data_service import TickDataCollector

collector = TickDataCollector()

# 查询1分钟Tick数据
ticks = collector.db_manager.find_many(
    'tick_data_1m',
    {'symbol': 'SZSE.000001'},
    limit=100,
    sort_field='created_at',
    sort_order=-1
)
```

#### 查询Bar数据
```python
# 查询5分钟Bar数据
bars_5m = collector.db_manager.find_many(
    'bar_data_5m',
    {'symbol': 'SZSE.000001'},
    limit=50,
    sort_field='eob',
    sort_order=-1
)

# 查询15分钟Bar数据
bars_15m = collector.db_manager.find_many(
    'bar_data_15m',
    {'symbol': 'SZSE.000001'},
    limit=50,
    sort_field='eob',
    sort_order=-1
)

# 查询1小时Bar数据
bars_1h = collector.db_manager.find_many(
    'bar_data_1h',
    {'symbol': 'SZSE.000001'},
    limit=24,
    sort_field='eob',
    sort_order=-1
)

# 查询日线数据
bars_1d = collector.db_manager.find_many(
    'bar_data_1d',
    {'symbol': 'SZSE.000001'},
    limit=30,
    sort_field='eob',
    sort_order=-1
)
```

## 集合管理

### 1. 创建索引
为了提高查询性能，建议为常用字段创建索引：

```python
# 为标的代码创建索引
collector.db_manager.create_index('tick_data_1m', [('symbol', 1)])
collector.db_manager.create_index('bar_data_5m', [('symbol', 1), ('eob', -1)])
collector.db_manager.create_index('bar_data_15m', [('symbol', 1), ('eob', -1)])
collector.db_manager.create_index('bar_data_1h', [('symbol', 1), ('eob', -1)])
collector.db_manager.create_index('bar_data_1d', [('symbol', 1), ('eob', -1)])
```

### 2. 数据清理
定期清理过期数据以节省存储空间：

```python
# 清理30天前的Tick数据
collector.db_manager.delete_old_data('tick_data_1m', 30)

# 清理90天前的分钟级数据
collector.db_manager.delete_old_data('bar_data_5m', 90)
collector.db_manager.delete_old_data('bar_data_15m', 90)

# 清理1年前的日线数据
collector.db_manager.delete_old_data('bar_data_1d', 365)
```

## 性能优化建议

1. **索引策略**: 为常用查询字段创建复合索引
2. **数据分片**: 对于大量数据，考虑按时间或标的进行分片
3. **查询优化**: 使用投影查询只返回需要的字段
4. **批量操作**: 对于大量数据插入，使用批量操作提高性能

## 监控和维护

1. **数据量监控**: 定期检查各集合的数据量
2. **性能监控**: 监控查询响应时间和索引使用情况
3. **存储监控**: 监控磁盘空间使用情况
4. **日志分析**: 查看logs目录下的日志文件，了解系统运行状态

## 故障排除

### 常见问题

1. **连接失败**: 检查MongoDB服务状态和连接配置
2. **数据重复**: 检查upsert操作的查询条件是否正确
3. **性能下降**: 检查索引是否创建，查询是否使用了索引
4. **存储空间不足**: 定期清理过期数据，监控磁盘使用情况

### 日志文件位置
- 主程序日志: `logs/app.log`
- 错误日志: `logs/error.log`
- 调度器日志: `logs/scheduler.log`
- 数据服务日志: `logs/src.tick_data_service.log`

## 总结

通过合理的集合设计，本项目实现了：
- ✅ 数据分类清晰，便于管理和查询
- ✅ 支持多种频率的数据存储
- ✅ 自动去重和更新机制
- ✅ 灵活的查询接口
- ✅ 完整的监控和日志系统

这种设计既保证了数据的完整性，又提供了高效的查询性能，适合股票数据的长期存储和分析需求。
