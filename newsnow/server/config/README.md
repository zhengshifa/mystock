# 代理配置说明

## 概述

本项目支持智能代理功能，当网络请求失败达到指定次数后，会自动切换到代理模式进行请求。

## 配置文件

### 代理配置模块

位置：`server/config/proxy.ts`

该模块提供了代理配置的接口定义和默认配置，支持从环境变量读取配置。

### 环境变量配置

在 `.env.server` 文件中添加以下配置项：

```env
# 代理配置
# 是否启用代理（true/false）
PROXY_ENABLED=true
# 代理服务器地址
PROXY_URL=http://127.0.0.1:7890
# 最大重试次数（失败多少次后切换到代理模式）
PROXY_MAX_RETRIES=3
# 普通请求超时时间（毫秒）
PROXY_NORMAL_TIMEOUT=10000
# 代理请求超时时间（毫秒）
PROXY_TIMEOUT=15000
```

## 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `PROXY_ENABLED` | boolean | `true` | 是否启用代理功能 |
| `PROXY_URL` | string | `http://127.0.0.1:7890` | 代理服务器地址 |
| `PROXY_MAX_RETRIES` | number | `3` | 最大重试次数，超过后切换到代理模式 |
| `PROXY_NORMAL_TIMEOUT` | number | `10000` | 普通请求超时时间（毫秒） |
| `PROXY_TIMEOUT` | number | `15000` | 代理请求超时时间（毫秒） |

## 工作原理

1. **正常模式**：首先尝试直接请求
2. **失败记录**：记录每个URL的失败次数
3. **智能切换**：当失败次数达到 `PROXY_MAX_RETRIES` 时，自动切换到代理模式
4. **成功重置**：请求成功后重置该URL的失败计数

## 使用示例

```typescript
import { myFetch } from '../utils/fetch'

// 自动处理重试和代理切换
const response = await myFetch('https://api.example.com/data')
```

## 常见代理服务器

- **Clash**: `http://127.0.0.1:7890`
- **V2Ray**: `http://127.0.0.1:10809`
- **Shadowsocks**: `http://127.0.0.1:1080`

## 注意事项

1. 确保代理服务器正在运行
2. 代理地址格式为 `http://host:port`
3. 在生产环境中建议关闭代理或使用企业级代理
4. 代理配置变更后需要重启服务器