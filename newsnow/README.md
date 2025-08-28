# NewsNow 调度器

> 新闻数据自动获取调度器 - 定时获取各新闻源数据并持久化到MongoDB数据库

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- Node.js 18+
- pnpm
- MongoDB

### 2. 安装依赖

```bash
pnpm install
```

### 3. 配置环境

复制环境配置文件：
```bash
cp example.env.scheduler .env.scheduler
```

根据需要修改 `.env.scheduler` 中的配置项。

### 4. 启动调度器

#### 方式一：使用启动脚本（推荐）
```bash
# Windows
start.bat

# PowerShell
.\start.ps1
```

#### 方式二：使用pnpm命令
```bash
# 定时模式（持续运行）
pnpm start

# 单次运行（测试用）
pnpm start:once
```

## 📋 可用命令

| 命令 | 说明 |
|------|------|
| `pnpm start` | 启动定时调度器 |
| `pnpm start:once` | 运行单次数据获取 |
| `pnpm cleanup` | 执行数据清理 |
| `pnpm cleanup:stats` | 查看数据库统计 |
| `pnpm test` | 运行功能测试 |
| `pnpm status` | 检查项目状态 |
| `pnpm build` | 构建项目 |

## 🔧 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MONGODB_URI` | MongoDB连接URI | `mongodb://localhost:27017/newsnow` |
| `FETCH_INTERVAL` | 获取间隔（毫秒） | `300000` (5分钟) |
| `MAX_NEWS_PER_SOURCE` | 每个源最大新闻数 | `50` |
| `LOG_LEVEL` | 日志级别 | `info` |

### 不同环境的默认配置

- **开发环境**: 1分钟间隔，详细日志
- **生产环境**: 10分钟间隔，标准日志

## 📊 支持的新闻源

调度器自动支持40+个新闻源，包括：
- 36kr、百度、哔哩哔哩、参考消息
- GitHub、Hacker News、掘金、知乎
- 微博、今日头条、V2EX等

## 🗄️ 数据库结构

### news 集合

```typescript
interface NewsItem {
  _id: ObjectId
  title: string           // 新闻标题
  link: string            // 新闻链接
  sourceId: string        // 新闻源ID
  description?: string    // 新闻描述
  image?: string          // 新闻图片
  author?: string         // 作者
  publishedAt?: Date      // 发布时间
  fetchedAt: Date         // 获取时间
  createdAt: Date         // 创建时间
}
```

## 📁 项目结构

```
newsnow-scheduler/
├── scripts/              # 脚本文件
│   ├── scheduler.ts      # 主调度器
│   ├── cleanup.ts        # 数据清理
│   ├── config.ts         # 配置管理
│   ├── test.ts           # 功能测试
│   └── status.ts         # 状态检查
├── server/               # 服务器端代码
│   ├── sources/          # 新闻源实现
│   ├── database/         # 数据库相关
│   └── utils/            # 工具函数
├── shared/               # 共享类型和常量
├── logs/                 # 日志目录
└── package.json          # 项目配置
```

## 🧪 测试和验证

### 运行功能测试
```bash
pnpm test
```

### 检查项目状态
```bash
pnpm status
```

### 查看数据库统计
```bash
pnpm cleanup:stats
```

## 📝 监控和维护

### 日志监控
调度器输出详细的日志信息，包括：
- 数据获取状态
- 成功/失败统计
- 错误详情
- 性能指标

### 数据清理
建议定期运行数据清理：
```bash
# 每天凌晨2点运行
0 2 * * * cd /path/to/newsnow-scheduler && pnpm cleanup
```

## 🚨 故障排除

### 常见问题

1. **MongoDB连接失败**
   - 检查MongoDB服务是否运行
   - 验证连接URI是否正确

2. **数据获取失败**
   - 检查网络连接
   - 验证代理设置

3. **依赖问题**
   - 运行 `pnpm install` 重新安装
   - 检查Node.js版本

### 调试模式
```bash
NODE_ENV=development LOG_LEVEL=debug pnpm start
```

## 📚 详细文档

更多详细信息请查看 [README.scheduler.md](./README.scheduler.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。
