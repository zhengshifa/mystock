# MongoDB 数据库架构设计

## 概述

本文档定义了 NewsNow 项目的 MongoDB 数据库架构，用于替换现有的 SQLite 数据库。

## 数据库设计原则

1. **性能优化**: 合理设计索引，优化查询性能
2. **数据一致性**: 确保数据完整性和一致性
3. **扩展性**: 支持水平扩展和分片
4. **安全性**: 实现访问控制和数据加密

## 集合(Collections)设计

### 1. cache 集合

**用途**: 存储新闻源的缓存数据

**文档结构**:
```typescript
interface CacheDocument {
  _id: string;           // 使用 sourceId 作为主键
  sourceId: string;      // 新闻源ID (如: "weibo", "zhihu")
  data: NewsItem[];      // 新闻项目数组
  updated: Date;         // 最后更新时间
  createdAt: Date;       // 创建时间
  updatedAt: Date;       // 文档更新时间
}
```

**索引设计**:
```javascript
// 主键索引 (自动创建)
{ "_id": 1 }

// 复合索引：按源ID和更新时间查询
{ "sourceId": 1, "updated": -1 }

// TTL索引：自动清理过期缓存 (7天)
{ "updatedAt": 1 }, { expireAfterSeconds: 604800 }
```

### 2. news_items 集合 (可选扩展)

**用途**: 存储历史新闻数据，用于分析和搜索

**文档结构**:
```typescript
interface NewsItemDocument {
  _id: ObjectId;         // MongoDB 自动生成的ID
  sourceId: string;      // 新闻源ID
  itemId: string;        // 新闻项目ID
  title: string;         // 新闻标题
  url: string;           // 新闻链接
  mobileUrl?: string;    // 移动端链接
  pubDate?: Date;        // 发布时间
  extra?: {              // 额外信息
    hover?: string;
    date?: Date;
    info?: string;
    diff?: number;
    icon?: string | { url: string; scale: number; };
  };
  createdAt: Date;       // 记录创建时间
  tags?: string[];       // 标签数组
}
```

**索引设计**:
```javascript
// 复合唯一索引：防止重复新闻
{ "sourceId": 1, "itemId": 1 }, { unique: true }

// 发布时间索引
{ "pubDate": -1 }

// 新闻源索引
{ "sourceId": 1 }

// 文本搜索索引
{ "title": "text", "url": "text" }

// TTL索引：自动清理旧新闻 (30天)
{ "createdAt": 1 }, { expireAfterSeconds: 2592000 }
```

## 数据迁移策略

### 从 SQLite 迁移到 MongoDB

1. **cache 表迁移**:
   - 读取 SQLite cache 表数据
   - 解析 JSON 数据字段
   - 转换时间戳为 Date 对象
   - 批量插入 MongoDB cache 集合

## 性能优化建议

1. **连接池配置**:
   - 最小连接数: 5
   - 最大连接数: 50
   - 连接超时: 30秒

2. **查询优化**:
   - 使用投影减少数据传输
   - 合理使用聚合管道
   - 避免全表扫描

3. **缓存策略**:
   - 应用层缓存热点数据
   - 使用 MongoDB 内置缓存
   - 设置合理的 TTL

## 安全配置

1. **认证授权**:
   - 启用 MongoDB 认证
   - 创建专用数据库用户
   - 最小权限原则

2. **网络安全**:
   - 绑定特定IP地址
   - 使用 TLS/SSL 加密
   - 配置防火墙规则

3. **数据加密**:
   - 静态数据加密
   - 传输数据加密
   - 敏感字段加密存储