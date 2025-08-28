import process from "node:process"
import type { NewsItem, SourceID } from "@shared/types"
import type { CacheInfo } from "#/types"
import { logger } from "#/utils/logger"
// useDatabase 是 nitro 提供的全局函数，无需导入

// SQLite 实现
import { Cache, getCacheTable } from "./cache"

// MongoDB 实现
import { MongoCache, getMongoCacheTable } from "./mongodb-cache"
import { initMongoDB, closeMongoDB } from "./mongodb"

/**
 * 数据库适配器接口 - 缓存操作
 */
export interface ICacheAdapter {
  init(): Promise<void>
  set(key: SourceID, value: NewsItem[]): Promise<void>
  get(key: SourceID): Promise<CacheInfo | undefined>
  getEntire(keys: SourceID[]): Promise<CacheInfo[]>
  delete(key: SourceID): Promise<void>
  clear?(): Promise<void>
  getStats?(): Promise<any>
  cleanExpired?(maxAge?: number): Promise<number>
}



/**
 * SQLite 缓存适配器
 */
class SQLiteCacheAdapter implements ICacheAdapter {
  private cache: Cache | undefined

  constructor(cache: Cache | undefined) {
    this.cache = cache
  }

  async init(): Promise<void> {
    if (this.cache) {
      await this.cache.init()
    }
  }

  async set(key: SourceID, value: NewsItem[]): Promise<void> {
    if (this.cache) {
      await this.cache.set(key, value)
    }
  }

  async get(key: SourceID): Promise<CacheInfo | undefined> {
    if (this.cache) {
      return await this.cache.get(key)
    }
    return undefined
  }

  async getEntire(keys: SourceID[]): Promise<CacheInfo[]> {
    if (this.cache) {
      return await this.cache.getEntire(keys)
    }
    return []
  }

  async delete(key: SourceID): Promise<void> {
    if (this.cache) {
      await this.cache.delete(key)
    }
  }
}

/**
 * MongoDB 缓存适配器
 */
class MongoCacheAdapter implements ICacheAdapter {
  private cache: MongoCache | undefined

  constructor(cache: MongoCache | undefined) {
    this.cache = cache
  }

  async init(): Promise<void> {
    if (this.cache) {
      await this.cache.init()
    }
  }

  async set(key: SourceID, value: NewsItem[]): Promise<void> {
    if (this.cache) {
      await this.cache.set(key, value)
    }
  }

  async get(key: SourceID): Promise<CacheInfo | undefined> {
    if (this.cache) {
      return await this.cache.get(key)
    }
    return undefined
  }

  async getEntire(keys: SourceID[]): Promise<CacheInfo[]> {
    if (this.cache) {
      return await this.cache.getEntire(keys)
    }
    return []
  }

  async delete(key: SourceID): Promise<void> {
    if (this.cache) {
      await this.cache.delete(key)
    }
  }

  async clear(): Promise<void> {
    if (this.cache) {
      await this.cache.clear()
    }
  }

  async getStats(): Promise<any> {
    if (this.cache) {
      return await this.cache.getStats()
    }
    return null
  }

  async cleanExpired(maxAge?: number): Promise<number> {
    if (this.cache) {
      return await this.cache.cleanExpired(maxAge)
    }
    return 0
  }
}





/**
 * 数据库适配器工厂
 */
export class DatabaseAdapterFactory {
  private static cacheAdapter: ICacheAdapter | null = null
  private static isInitialized = false

  /**
   * 初始化数据库适配器
   */
  static async initialize(): Promise<void> {
    if (this.isInitialized) {
      return
    }

    const useMongoDB = process.env.USE_MONGODB === 'true'
    
    try {
      if (useMongoDB) {
        logger.info('初始化 MongoDB 适配器')
        
        // 初始化 MongoDB 连接
        await initMongoDB()
        
        // 创建 MongoDB 适配器
        const mongoCache = await getMongoCacheTable()
        
        this.cacheAdapter = new MongoCacheAdapter(mongoCache)
        
        logger.success('MongoDB 适配器初始化完成')
      } else {
        logger.info('初始化 SQLite 适配器')
        
        // 创建 SQLite 适配器
        const sqliteCache = await getCacheTable()
        
        this.cacheAdapter = new SQLiteCacheAdapter(sqliteCache)
        
        logger.success('SQLite 适配器初始化完成')
      }
      
      this.isInitialized = true
    } catch (error) {
      logger.error('数据库适配器初始化失败:', error)
      throw error
    }
  }

  /**
   * 获取缓存适配器
   */
  static async getCacheAdapter(): Promise<ICacheAdapter> {
    if (!this.isInitialized) {
      await this.initialize()
    }
    
    if (!this.cacheAdapter) {
      throw new Error('缓存适配器未初始化')
    }
    
    return this.cacheAdapter
  }



  /**
   * 关闭数据库连接
   */
  static async close(): Promise<void> {
    const useMongoDB = process.env.USE_MONGODB === 'true'
    
    if (useMongoDB) {
      await closeMongoDB()
    }
    
    this.cacheAdapter = null
    this.isInitialized = false
    
    logger.info('数据库适配器已关闭')
  }
}

/**
 * 便捷函数 - 获取缓存适配器
 */
export async function getCacheAdapter(): Promise<ICacheAdapter> {
  return await DatabaseAdapterFactory.getCacheAdapter()
}



/**
 * 便捷函数 - 关闭数据库连接
 */
export async function closeDatabaseAdapter(): Promise<void> {
  await DatabaseAdapterFactory.close()
}