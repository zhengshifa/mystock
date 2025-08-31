# NewsNow Scheduler

新闻数据自动获取调度器 - 定时获取各新闻源数据并持久化到MongoDB

## 项目简介

NewsNow Scheduler 是一个自动化新闻数据获取系统，能够定时从各种新闻源获取最新资讯并将数据持久化存储到MongoDB数据库中。

## 功能特性

- 🔄 定时任务调度，自动获取新闻数据
- 📰 支持多种新闻源（如Hacker News等）
- 🗄️ MongoDB数据持久化存储
- 🛠️ 可扩展的新闻源插件架构
- 📊 完善的日志记录和错误处理
- ⚙️ 灵活的配置管理

## 安装要求

- Python >= 3.11
- MongoDB数据库

## 快速开始

### 1. 安装依赖

使用uv管理项目环境：

```bash
uv sync
```

### 2. 配置环境

创建`.env`文件并配置必要的环境变量：

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=newsnow
```

### 3. 运行程序

```bash
uv run python main.py
```

或使用CLI命令：

```bash
uv run newsnow
```

## 项目结构

```
newsnow_py/
├── cli.py              # 命令行接口
├── main.py             # 主程序入口
├── config/             # 配置模块
├── core/               # 核心调度器
├── database/           # 数据库模块
├── sources/            # 新闻源模块
├── utils/              # 工具模块
└── requirements.txt    # 依赖列表
```

## 开发

### 安装开发依赖

```bash
uv sync --extra dev
```

### 代码格式化

```bash
uv run black .
uv run isort .
```

### 运行测试

```bash
uv run pytest
```

### 类型检查

```bash
uv run mypy .
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

- Email: orongxing@gmail.com
- 项目维护者: NewsNow Team