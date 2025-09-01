# 增量同步功能使用说明

## 🎯 功能概述

现在你的股票数据收集器支持两种运行模式：

1. **实时调度模式** (`--mode scheduler`) - 默认模式，持续运行并定时收集数据
2. **增量同步模式** (`--mode sync`) - 一次性同步指定时间范围的历史数据

## 🚀 增量同步模式

### 基本用法

```bash
# 同步最近30天的1分钟K线数据
uv run python main.py --mode sync --frequency 1m --start-date 2024-01-01

# 同步指定股票的历史数据
uv run python main.py --mode sync --frequency 1d --start-date 2024-01-01 --symbols SH600000,SH600036

# 强制重新同步（覆盖已有数据）
uv run python main.py --mode sync --frequency 1h --start-date 2024-01-01 --force
```

### 支持的参数

| 参数 | 说明 | 必需 | 示例 |
|------|------|------|------|
| `--mode` | 运行模式 | 是 | `sync` |
| `--frequency` | 数据频率 | 是 | `1m`, `5m`, `15m`, `1h`, `1d` |
| `--start-date` | 开始日期 | 是 | `2024-01-01` |
| `--end-date` | 结束日期 | 否 | `2024-01-31` (默认为今天) |
| `--symbols` | 股票代码列表 | 否 | `SH600000,SH600036` (默认使用配置文件中的股票) |
| `--force` | 强制重新同步 | 否 | 无参数，添加即启用 |

### 数据频率说明

- **`1m`** - 1分钟K线数据
- **`5m`** - 5分钟K线数据  
- **`15m`** - 15分钟K线数据
- **`1h`** - 1小时K线数据
- **`1d`** - 日线数据

## 📊 使用场景

### 1. 补充历史数据
```bash
# 补充2024年1月的1分钟K线数据
uv run python main.py --mode sync --frequency 1m --start-date 2024-01-01 --end-date 2024-01-31
```

### 2. 同步特定股票
```bash
# 只同步贵州茅台和招商银行的历史数据
uv run python main.py --mode sync --frequency 1d --start-date 2024-01-01 --symbols SH600519,SH600036
```

### 3. 数据修复
```bash
# 强制重新同步某段时间的数据（修复数据问题）
uv run python main.py --mode sync --frequency 1h --start-date 2024-01-01 --end-date 2024-01-15 --force
```

### 4. 批量数据收集
```bash
# 收集最近3个月的所有频率数据
uv run python main.py --mode sync --frequency 1m --start-date 2023-11-01
uv run python main.py --mode sync --frequency 5m --start-date 2023-11-01
uv run python main.py --mode sync --frequency 15m --start-date 2023-11-01
uv run python main.py --mode sync --frequency 1h --start-date 2023-11-01
uv run python main.py --mode sync --frequency 1d --start-date 2023-11-01
```

## 🔧 高级功能

### 1. 数据完整性检查
增量同步管理器会自动检查数据完整性：
- 计算期望的数据条数
- 检查数据库中已有的数据
- 只同步缺失的部分
- 避免重复同步

### 2. 断点续传
- 记录同步任务状态
- 支持查看同步进度
- 失败任务可以恢复（功能开发中）

### 3. 智能批处理
- 自动分批处理大量数据
- 避免内存溢出
- 支持自定义批处理大小

## 📋 同步状态管理

### 查看同步状态
```bash
# 查看所有同步任务状态
python incremental_sync.py status

# 查看特定同步任务状态
python incremental_sync.py status --sync-id sync_1d_2024-01-01_2024-01-31_1234567890
```

### 清理同步状态
```bash
# 清理7天前的同步状态记录
python incremental_sync.py cleanup --days 7
```

## ⚠️ 注意事项

### 1. 数据量估算
不同频率的数据量差异很大：
- **1分钟数据**: 每天约240条记录
- **5分钟数据**: 每天约48条记录  
- **15分钟数据**: 每天约16条记录
- **1小时数据**: 每天约4条记录
- **日线数据**: 每天1条记录

### 2. 网络和API限制
- GM API有调用频率限制
- 大量数据同步需要较长时间
- 建议在非交易时间进行大批量同步

### 3. 存储空间
- 确保MongoDB有足够存储空间
- 1分钟数据占用空间较大
- 建议定期清理过期数据

## 🎯 最佳实践

### 1. 同步策略
```bash
# 推荐：先同步低频数据，再同步高频数据
uv run python main.py --mode sync --frequency 1d --start-date 2024-01-01
uv run python main.py --mode sync --frequency 1h --start-date 2024-01-01
uv run python main.py --mode sync --frequency 15m --start-date 2024-01-01
uv run python main.py --mode sync --frequency 5m --start-date 2024-01-01
uv run python main.py --mode sync --frequency 1m --start-date 2024-01-01
```

### 2. 时间选择
- **日线数据**: 可以在任何时间同步
- **分钟级数据**: 建议在非交易时间同步
- **大批量同步**: 建议在夜间或周末进行

### 3. 监控和日志
- 查看日志文件了解同步进度
- 监控MongoDB存储空间
- 定期检查数据完整性

## 🔍 故障排除

### 常见问题

1. **同步失败**
   - 检查网络连接
   - 验证GM API配置
   - 查看错误日志

2. **数据不完整**
   - 使用 `--force` 强制重新同步
   - 检查数据完整性
   - 验证时间范围设置

3. **内存不足**
   - 减少批处理大小
   - 分批同步数据
   - 增加系统内存

### 日志分析
```bash
# 查看同步日志
tail -f logs/stock_collector.log | grep "IncrementalSyncManager"
```

## 📈 性能优化

### 1. 并行同步
- 不同频率可以并行同步
- 不同股票可以分批同步
- 避免同时启动过多同步任务

### 2. 资源管理
- 监控CPU和内存使用
- 调整批处理大小
- 合理设置同步间隔

### 3. 缓存策略
- 利用MongoDB索引优化查询
- 避免重复数据检查
- 使用增量更新策略

## 🎉 总结

增量同步功能为你提供了：

✅ **灵活的数据同步** - 支持任意时间范围
✅ **智能的数据管理** - 自动检查完整性，避免重复
✅ **高效的批处理** - 支持大量数据快速同步
✅ **完整的监控** - 实时查看同步状态和进度
✅ **简单的操作** - 命令行一键启动同步

现在你可以轻松地：
1. 补充历史数据
2. 修复数据问题  
3. 同步特定股票
4. 批量收集数据
5. 监控同步进度

使用 `uv run python main.py --mode sync --help` 查看详细帮助信息！
