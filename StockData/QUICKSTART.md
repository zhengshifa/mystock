# 快速启动指南

## 🚀 5分钟快速启动

### 1. 环境准备
```bash
# 确保已安装uv
pip install uv

# 克隆项目后进入目录
cd StockData
```

### 2. 安装依赖
```bash
# 创建虚拟环境并安装依赖
uv sync
```

### 3. 配置环境变量
```bash
# 复制配置文件
copy config.env.example .env

# 编辑.env文件，配置以下参数：
# - GM_TOKEN: 掘金量化API Token
# - GM_USERNAME: 掘金量化用户名
# - MONGODB_URI: MongoDB连接URI
# - MONGODB_USERNAME: MongoDB用户名
# - MONGODB_PASSWORD: MongoDB密码
```

### 4. 测试运行
```bash
# 测试Tick数据收集
uv run python main.py --mode once --type tick

# 测试不同频率的K线数据收集
uv run python main.py --mode once --type 60s    # 1分钟K线
uv run python main.py --mode once --type 300s   # 5分钟K线
uv run python main.py --mode once --type 900s   # 15分钟K线
uv run python main.py --mode once --type 1d     # 日线数据

# 测试新的同步功能
uv run python main.py --mode once --type realtime  # 实时数据同步
uv run python main.py --mode once --type all       # 全量数据同步
```

### 5. 启动守护进程
```bash
# 使用Python启动
uv run python main.py --mode daemon

# 或使用Windows启动脚本
start.bat
```

## 🔧 常见问题解决

### MongoDB连接失败
- 确保MongoDB服务已启动
- 检查用户名密码是否正确
- 确认使用admin数据库进行认证

### 掘金量化连接失败
- 检查Token和用户名是否正确
- 确认网络连接和代理设置
- 查看掘金量化SDK文档

### 依赖安装失败
```bash
# 清理并重新安装
uv sync --reinstall
```

## 📊 数据查看

### MongoDB数据查看
```bash
# 连接到MongoDB
mongosh

# 查看数据库
use stock_data

# 查看集合
show collections

# 查看Tick数据
db.tick.find().limit(5)

# 查看不同频率的K线数据
db.60s.find().limit(5)      # 1分钟K线
db.300s.find().limit(5)     # 5分钟K线
db.900s.find().limit(5)     # 15分钟K线
db.1d.find().limit(5)       # 日线数据
```

## 🎯 下一步

1. **配置真实数据源**: 更新掘金量化API调用
2. **自定义股票列表**: 修改`src/scheduler/data_scheduler.py`中的股票列表
3. **调整调度策略**: 修改定时任务频率
4. **添加数据导出**: 实现数据导出功能
5. **监控告警**: 添加异常监控和告警机制

## 📞 技术支持

如遇问题，请：
1. 查看日志文件: `logs/stock_collector.log`
2. 运行测试: `uv run pytest tests/ -v`
3. 检查配置: 确认`.env`文件配置正确
