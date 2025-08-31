# 并发配置说明

## 概述

NewsNow Python 版本支持并发获取新闻数据，可以显著提高数据获取效率。

## 并发配置参数

### 核心参数

- **MAX_CONCURRENT_SOURCES**: 最大并发新闻源数量 (默认: 10)
- **BATCH_SIZE**: 批处理大小，每批处理的新闻源数量 (默认: 5)
- **BATCH_DELAY**: 批次间延迟时间，单位秒 (默认: 1)

### 配置示例

在 `.env` 文件中添加以下配置：

```bash
# 并发配置
MAX_CONCURRENT_SOURCES=15
BATCH_SIZE=8
BATCH_DELAY=2
```

## 并发策略

### 1. 分批处理
- 将所有新闻源按 `BATCH_SIZE` 分组
- 每组内最多 `MAX_CONCURRENT_SOURCES` 个并发任务
- 批次间有 `BATCH_DELAY` 秒的延迟

### 2. 信号量控制
- 使用 `asyncio.Semaphore` 控制并发数量
- 避免同时启动过多网络请求
- 防止对目标网站造成过大压力

### 3. 错误处理
- 每个新闻源独立处理，单个失败不影响其他
- 支持重试机制
- 详细的错误日志记录

## 性能优化建议

### 网络友好型配置
```bash
MAX_CONCURRENT_SOURCES=8
BATCH_SIZE=4
BATCH_DELAY=2
```

### 高性能配置
```bash
MAX_CONCURRENT_SOURCES=20
BATCH_SIZE=10
BATCH_DELAY=0.5
```

### 平衡型配置 (推荐)
```bash
MAX_CONCURRENT_SOURCES=12
BATCH_SIZE=6
BATCH_DELAY=1
```

## 监控和调试

### 日志输出
```
开始并发获取，最大并发数: 12，批处理大小: 6
数据获取完成 - 成功: 25, 失败: 4, 总条目: 156, 耗时: 45.23秒
```

### 性能指标
- 成功源数量
- 失败源数量
- 总获取条目数
- 总耗时

## 注意事项

1. **网络限制**: 过高的并发数可能导致网络拥塞
2. **目标网站**: 某些网站可能有访问频率限制
3. **系统资源**: 并发数过高可能消耗过多内存和CPU
4. **代理使用**: 使用代理时建议降低并发数

## 故障排除

### 常见问题

1. **HTTP 429 (Too Many Requests)**
   - 降低 `MAX_CONCURRENT_SOURCES`
   - 增加 `BATCH_DELAY`

2. **连接超时**
   - 检查网络连接
   - 调整 `REQUEST_TIMEOUT`

3. **内存使用过高**
   - 降低 `BATCH_SIZE`
   - 减少 `MAX_CONCURRENT_SOURCES`
