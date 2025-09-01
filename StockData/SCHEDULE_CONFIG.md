# 定时任务配置说明

## 📅 定时任务概览

本系统采用智能定时任务策略，确保数据的实时性和完整性：

### 1. 实时数据同步
- **执行频率**: 交易时间每30秒
- **同步内容**: 
  - Tick数据（实时逐笔交易）
  - 1分钟K线数据
- **特点**: 增量同步，支持去重

### 2. 定时全量同步
- **09:00**: 开盘前全量同步
  - 确保开盘前数据完整性
  - 同步所有数据类型
- **12:00**: 午盘前全量同步
  - 午盘前数据检查
  - 补充上午遗漏数据
- **15:05**: 收盘后全量同步
  - 收盘后数据汇总
  - 确保当日数据完整

### 3. 市场状态监控
- **执行频率**: 每5分钟
- **功能**: 监控市场开放状态

## ⚙️ 配置说明

### 调度器配置
```python
# 实时数据同步（交易时间每30秒）
schedule.every(30).seconds.do(self._sync_realtime_data)

# 定时全量同步
schedule.every().day.at("09:00").do(self._sync_all_data)
schedule.every().day.at("12:00").do(self._sync_all_data)
schedule.every().day.at("15:05").do(self._sync_all_data)

# 市场状态检查
schedule.every(5).minutes.do(self._check_market_status)
```

### 交易时间判断
系统自动判断是否为交易时间：
- 工作日（周一至周五）
- 交易时段：09:30-11:30, 13:00-15:00
- 非交易时间自动跳过数据同步

## 🔄 数据同步策略

### 增量同步
- **实时数据**: 每30秒同步，基于哈希值去重
- **数据源**: 掘金量化SDK
- **存储**: MongoDB，支持批量插入

### 全量同步
- **执行时机**: 关键时间点
- **同步范围**: 所有数据类型
- **数据源**: 掘金量化SDK
- **存储**: 按频率分别存储到不同集合

## 📊 数据类型支持

### 实时同步数据类型
1. **Tick数据**: 实时逐笔交易数据
2. **1分钟K线**: 实时K线数据

### 全量同步数据类型
1. **Tick数据**: 实时数据
2. **K线数据**: 
   - 60s: 1分钟K线
   - 300s: 5分钟K线
   - 900s: 15分钟K线
   - 1d: 日线数据

## 🚀 使用方法

### 启动守护进程（推荐）
```bash
uv run python main.py --mode daemon
```

### 手动执行同步
```bash
# 实时数据同步
uv run python main.py --mode once --type realtime

# 全量数据同步
uv run python main.py --mode once --type all

# 特定数据类型同步
uv run python main.py --mode once --type tick
uv run python main.py --mode once --type 60s
```

## 📈 性能优化

### 批量处理
- 支持批量数据插入
- 可配置批量大小
- 失败时自动降级为单条插入

### 去重机制
- 基于数据哈希值去重
- MongoDB唯一索引支持
- 避免重复数据入库

### 错误处理
- 完善的异常处理机制
- 自动重试机制
- 详细的日志记录

## 🔧 自定义配置

### 修改同步频率
```python
# 修改实时同步频率（秒）
schedule.every(60).seconds.do(self._sync_realtime_data)

# 修改全量同步时间
schedule.every().day.at("10:00").do(self._sync_all_data)
```

### 添加新的同步任务
```python
def custom_sync_task():
    # 自定义同步逻辑
    pass

# 添加到调度器
schedule.every(1).hours.do(custom_sync_task)
```

## 📝 监控和日志

### 日志记录
- 所有同步操作都有详细日志
- 支持不同日志级别
- 自动日志轮转和压缩

### 性能监控
- 同步成功率统计
- 数据量统计
- 执行时间监控

## 🎯 最佳实践

1. **生产环境**: 使用守护进程模式，确保24小时运行
2. **数据完整性**: 定期检查全量同步日志
3. **性能监控**: 关注同步成功率和执行时间
4. **错误处理**: 及时处理同步失败的情况
5. **备份策略**: 定期备份MongoDB数据
