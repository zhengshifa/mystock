import type { Collection } from "mongodb"
import type { NewsItem, SourceID } from "@shared/types"
import type { CacheInfo } from "#/types"
import { getMongoCollection, type CacheDocument } from "./mongodb"

/**
 * MongoDB 缓存数据访问层
 */
export class MongoCache {
  private collection: Collection<CacheDocument> | null = null

  /**
   * 获取缓存集合
   */
  private async getCollection(): Promise<Collection<CacheDocument>> {
    if (!this.collection) {
      this.collection = await getMongoCollection<CacheDocument>("cache")
    }
    return this.collection
  }

  /**
   * 初始化缓存表（MongoDB 中不需要显式创建表）
   */
  async init(): Promise<void> {
    try {
      await this.getCollection()
      logger.success("MongoDB cache collection 初始化完成")
    } catch (error) {
      logger.error("MongoDB cache collection 初始化失败:", error)
      throw error
    }
  }

  /**
   * 设置缓存数据
   * @param key 缓存键（sourceId）
   * @param value 新闻项目数组
   */
  async set(key: SourceID, value: NewsItem[]): Promise<void> {
    try {
      const collection = await this.getCollection()
      const now = new Date()
      
      const document: CacheDocument = {
        _id: key,
        sourceId: key,
        data: value,
        updated: now,
        createdAt: now,
        updatedAt: now
      }

      await collection.replaceOne(
        { _id: key },
        document,
        { upsert: true }
      )
      
      logger.success(`设置 ${key} 缓存成功`)
    } catch (error) {
      logger.error(`设置 ${key} 缓存失败:`, error)
      throw error
    }
  }

  /**
   * 获取缓存数据
   * @param key 缓存键（sourceId）
   * @returns 缓存信息或 undefined
   */
  async get(key: SourceID): Promise<CacheInfo | undefined> {
    try {
      const collection = await this.getCollection()
      const document = await collection.findOne({ _id: key })
      
      if (document) {
        logger.success(`获取 ${key} 缓存成功`)
        return {
          id: document.sourceId,
          updated: document.updated.getTime(),
          items: document.data
        }
      }
      
      return undefined
    } catch (error) {
      logger.error(`获取 ${key} 缓存失败:`, error)
      throw error
    }
  }

  /**
   * 批量获取缓存数据
   * @param keys 缓存键数组
   * @returns 缓存信息数组
   */
  async getEntire(keys: SourceID[]): Promise<CacheInfo[]> {
    try {
      const collection = await this.getCollection()
      const documents = await collection.find({
        _id: { $in: keys }
      }).toArray()
      
      if (documents.length > 0) {
        logger.success(`批量获取缓存成功，共 ${documents.length} 条记录`)
        return documents.map(doc => ({
          id: doc.sourceId,
          updated: doc.updated.getTime(),
          items: doc.data
        }))
      }
      
      return []
    } catch (error) {
      logger.error("批量获取缓存失败:", error)
      throw error
    }
  }

  /**
   * 删除缓存数据
   * @param key 缓存键（sourceId）
   */
  async delete(key: SourceID): Promise<void> {
    try {
      const collection = await this.getCollection()
      const result = await collection.deleteOne({ _id: key })
      
      if (result.deletedCount > 0) {
        logger.success(`删除 ${key} 缓存成功`)
      } else {
        logger.warn(`缓存 ${key} 不存在`)
      }
    } catch (error) {
      logger.error(`删除 ${key} 缓存失败:`, error)
      throw error
    }
  }

  /**
   * 清空所有缓存
   */
  async clear(): Promise<void> {
    try {
      const collection = await this.getCollection()
      const result = await collection.deleteMany({})
      logger.success(`清空缓存成功，删除了 ${result.deletedCount} 条记录`)
    } catch (error) {
      logger.error("清空缓存失败:", error)
      throw error
    }
  }

  /**
   * 获取缓存统计信息
   */
  async getStats(): Promise<{
    totalCount: number
    totalSize: number
    oldestCache: Date | null
    newestCache: Date | null
  }> {
    try {
      const collection = await this.getCollection()
      
      const [countResult, statsResult] = await Promise.all([
        collection.countDocuments(),
        collection.aggregate([
          {
            $group: {
              _id: null,
              totalSize: { $sum: { $size: "$data" } },
              oldestCache: { $min: "$updated" },
              newestCache: { $max: "$updated" }
            }
          }
        ]).toArray()
      ])
      
      const stats = statsResult[0] || {
        totalSize: 0,
        oldestCache: null,
        newestCache: null
      }
      
      return {
        totalCount: countResult,
        totalSize: stats.totalSize,
        oldestCache: stats.oldestCache,
        newestCache: stats.newestCache
      }
    } catch (error) {
      logger.error("获取缓存统计信息失败:", error)
      throw error
    }
  }

  /**
   * 清理过期缓存
   * @param maxAge 最大缓存时间（毫秒）
   */
  async cleanExpired(maxAge: number = 7 * 24 * 60 * 60 * 1000): Promise<number> {
    try {
      const collection = await this.getCollection()
      const expireDate = new Date(Date.now() - maxAge)
      
      const result = await collection.deleteMany({
        updated: { $lt: expireDate }
      })
      
      if (result.deletedCount > 0) {
        logger.success(`清理过期缓存成功，删除了 ${result.deletedCount} 条记录`)
      }
      
      return result.deletedCount
    } catch (error) {
      logger.error("清理过期缓存失败:", error)
      throw error
    }
  }
}

/**
 * 获取 MongoDB 缓存表实例
 */
export async function getMongoCacheTable(): Promise<MongoCache | undefined> {
  try {
    if (process.env.ENABLE_CACHE === "false") {
      return undefined
    }
    
    const cacheTable = new MongoCache()
    if (process.env.INIT_TABLE !== "false") {
      await cacheTable.init()
    }
    
    return cacheTable
  } catch (error) {
    logger.error("初始化 MongoDB 缓存表失败:", error)
    return undefined
  }
}