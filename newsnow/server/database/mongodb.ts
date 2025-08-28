import { MongoClient, Db, Collection } from "mongodb"
import process from "node:process"
import { consola } from "consola"
import type { NewsItem, SourceID } from "@shared/types"
import type { CacheInfo } from "#/types"

/**
 * MongoDB 缓存文档接口
 */
export interface CacheDocument {
  _id: string
  sourceId: SourceID
  data: NewsItem[]
  updated: Date
  createdAt: Date
  updatedAt: Date
}



/**
 * MongoDB 连接配置类
 */
class MongoDBConnection {
  private client: MongoClient | null = null
  private db: Db | null = null
  private isConnected = false

  /**
   * 获取 MongoDB 连接字符串
   */
  private getConnectionString(): string {
    // 优先使用 MONGODB_URI 环境变量
    const mongoUri = process.env.MONGODB_URI
    if (mongoUri) {
      return mongoUri
    }

    // 如果没有 MONGODB_URI，则使用单独的配置项构建连接字符串
    const host = process.env.MONGODB_HOST || "localhost"
    const port = process.env.MONGODB_PORT || "27017"
    const database = process.env.MONGODB_DATABASE || "newsnow"
    const username = process.env.MONGODB_USERNAME
    const password = process.env.MONGODB_PASSWORD
    const authSource = process.env.MONGODB_AUTH_SOURCE || "admin"

    if (username && password) {
      return `mongodb://${username}:${password}@${host}:${port}/${database}?authSource=${authSource}`
    }
    return `mongodb://${host}:${port}/${database}`
  }

  /**
   * 获取 MongoDB 客户端配置选项
   */
  private getClientOptions() {
    return {
      // 连接池配置
      minPoolSize: parseInt(process.env.MONGODB_MIN_POOL_SIZE || "5"),
      maxPoolSize: parseInt(process.env.MONGODB_MAX_POOL_SIZE || "50"),
      maxIdleTimeMS: parseInt(process.env.MONGODB_MAX_IDLE_TIME || "30000"),
      
      // 连接超时配置
      connectTimeoutMS: parseInt(process.env.MONGODB_CONNECT_TIMEOUT || "30000"),
      socketTimeoutMS: parseInt(process.env.MONGODB_SOCKET_TIMEOUT || "30000"),
      serverSelectionTimeoutMS: parseInt(process.env.MONGODB_SERVER_SELECTION_TIMEOUT || "30000"),
      
      // 重试配置
      retryWrites: true,
      retryReads: true,
      
      // 压缩配置
      compressors: ["zlib"],
      
      // TLS/SSL 配置
      tls: process.env.MONGODB_TLS === "true",
      tlsInsecure: process.env.MONGODB_TLS_INSECURE === "true",
    }
  }

  /**
   * 连接到 MongoDB
   */
  async connect(): Promise<void> {
    if (this.isConnected && this.client && this.db) {
      return
    }

    try {
      const connectionString = this.getConnectionString()
      const options = this.getClientOptions()
      
      consola.info("正在连接到 MongoDB...")
      this.client = new MongoClient(connectionString, options)
      await this.client.connect()
      
      const dbName = process.env.MONGODB_DATABASE || "newsnow"
      this.db = this.client.db(dbName)
      
      // 测试连接
      await this.db.admin().ping()
      
      this.isConnected = true
      consola.success(`成功连接到 MongoDB 数据库: ${dbName}`)
      
      // 创建索引
      await this.createIndexes()
      
    } catch (error) {
      consola.error("MongoDB 连接失败:", error)
      throw error
    }
  }

  /**
   * 创建数据库索引
   */
  private async createIndexes(): Promise<void> {
    if (!this.db) return

    try {
      // cache 集合索引
      const cacheCollection = this.db.collection("cache")
      await cacheCollection.createIndexes([
        { key: { sourceId: 1, updated: -1 } },
        { key: { updatedAt: 1 }, expireAfterSeconds: 604800 } // 7天TTL
      ])



      consola.success("MongoDB 索引创建完成")
    } catch (error) {
      consola.error("创建索引失败:", error)
    }
  }

  /**
   * 断开 MongoDB 连接
   */
  async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.close()
      this.client = null
      this.db = null
      this.isConnected = false
      consola.info("MongoDB 连接已断开")
    }
  }

  /**
   * 获取数据库实例
   */
  getDatabase(): Db {
    if (!this.db) {
      throw new Error("MongoDB 未连接，请先调用 connect() 方法")
    }
    return this.db
  }

  /**
   * 获取集合
   */
  getCollection<T = any>(name: string): Collection<T> {
    return this.getDatabase().collection<T>(name)
  }

  /**
   * 检查连接状态
   */
  isConnectedToMongoDB(): boolean {
    return this.isConnected
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<boolean> {
    try {
      if (!this.db) return false
      await this.db.admin().ping()
      return true
    } catch {
      return false
    }
  }
}

// 单例实例
const mongoConnection = new MongoDBConnection()

/**
 * 获取 MongoDB 连接实例
 */
export function getMongoConnection(): MongoDBConnection {
  return mongoConnection
}

/**
 * 初始化 MongoDB 连接
 */
export async function initMongoDB(): Promise<MongoDBConnection> {
  if (!mongoConnection.isConnectedToMongoDB()) {
    await mongoConnection.connect()
  }
  return mongoConnection
}

/**
 * 获取 MongoDB 数据库实例
 */
export async function getMongoDatabase(): Promise<Db> {
  const connection = await initMongoDB()
  return connection.getDatabase()
}

/**
 * 获取指定集合
 */
export async function getMongoCollection<T = any>(name: string): Promise<Collection<T>> {
  const connection = await initMongoDB()
  return connection.getCollection<T>(name)
}

/**
 * 优雅关闭 MongoDB 连接
 */
export async function closeMongoDB(): Promise<void> {
  await mongoConnection.disconnect()
}

// 进程退出时自动关闭连接
process.on("SIGINT", async () => {
  await closeMongoDB()
  process.exit(0)
})

process.on("SIGTERM", async () => {
  await closeMongoDB()
  process.exit(0)
})