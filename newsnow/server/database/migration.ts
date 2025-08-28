import process from "node:process"
import { logger } from "#/utils/logger"
import { DatabaseAdapterFactory } from "./adapter"
import { initMongoDB, getMongoDatabase, closeMongoDB } from "./mongodb"
// useDatabase 是 nitro 提供的全局函数，无需导入
import { Cache } from "./cache"
import type { CacheInfo } from "#/types"
import type { NewsItem, SourceID } from "@shared/types"

/**
 * 数据库迁移工具类
 */
export class DatabaseMigration {
  /**
   * 初始化数据库
   */
  static async initializeDatabase(): Promise<void> {
    try {
      logger.info('开始初始化数据库...')
      
      // 初始化数据库适配器
      await DatabaseAdapterFactory.initialize()
      
      const useMongoDB = process.env.USE_MONGODB === 'true'
      
      if (useMongoDB) {
        logger.info('MongoDB 数据库初始化完成')
      } else {
        logger.info('SQLite 数据库初始化完成')
      }
      
      logger.success('数据库初始化成功')
    } catch (error) {
      logger.error('数据库初始化失败:', error)
      throw error
    }
  }

  /**
   * 从 SQLite 迁移数据到 MongoDB
   */
  static async migrateFromSQLiteToMongoDB(): Promise<void> {
    if (process.env.USE_MONGODB !== 'true') {
      logger.warn('当前未启用 MongoDB，跳过迁移')
      return
    }

    try {
      logger.info('开始从 SQLite 迁移数据到 MongoDB...')
      
      // 初始化 SQLite 连接
      const sqliteDb = useDatabase()
      if (!sqliteDb) {
        logger.warn('SQLite 数据库不可用，跳过迁移')
        return
      }
      
      // 初始化 MongoDB 连接
      await initMongoDB()
      
      // 迁移缓存数据
      await this.migrateCacheData(sqliteDb)
      

      
      logger.success('数据迁移完成')
    } catch (error) {
      logger.error('数据迁移失败:', error)
      throw error
    }
  }

  /**
   * 迁移缓存数据
   */
  private static async migrateCacheData(sqliteDb: any): Promise<void> {
    try {
      logger.info('开始迁移缓存数据...')
      
      // 创建 SQLite 缓存表实例
      const sqliteCache = new Cache(sqliteDb)
      await sqliteCache.init()
      
      // 获取 MongoDB 缓存适配器
      const mongoAdapter = await DatabaseAdapterFactory.getCacheAdapter()
      
      // 从 SQLite 获取所有缓存数据
      const sqliteData = await sqliteDb.prepare('SELECT id, data, updated FROM cache').all()
      const cacheRows = sqliteData.results || sqliteData || []
      
      if (cacheRows.length === 0) {
        logger.info('没有缓存数据需要迁移')
        return
      }
      
      logger.info(`发现 ${cacheRows.length} 条缓存记录，开始迁移...`)
      
      let migratedCount = 0
      for (const row of cacheRows) {
        try {
          const sourceId = row.id as SourceID
          const newsItems = JSON.parse(row.data) as NewsItem[]
          
          await mongoAdapter.set(sourceId, newsItems)
          migratedCount++
          
          if (migratedCount % 10 === 0) {
            logger.info(`已迁移 ${migratedCount}/${cacheRows.length} 条缓存记录`)
          }
        } catch (error) {
          logger.error(`迁移缓存记录 ${row.id} 失败:`, error)
        }
      }
      
      logger.success(`缓存数据迁移完成，共迁移 ${migratedCount} 条记录`)
    } catch (error) {
      logger.error('迁移缓存数据失败:', error)
      throw error
    }
  }



  /**
   * 验证数据迁移结果
   */
  static async validateMigration(): Promise<void> {
    try {
      logger.info('开始验证数据迁移结果...')
      
      const cacheAdapter = await DatabaseAdapterFactory.getCacheAdapter()
      
      // 验证缓存数据
      if (cacheAdapter.getStats) {
        const cacheStats = await cacheAdapter.getStats()
        logger.info(`缓存统计: ${JSON.stringify(cacheStats, null, 2)}`)
      }
      
      logger.success('数据迁移验证完成')
    } catch (error) {
      logger.error('数据迁移验证失败:', error)
      throw error
    }
  }

  /**
   * 清理过期数据
   */
  static async cleanupExpiredData(): Promise<void> {
    try {
      logger.info('开始清理过期数据...')
      
      const cacheAdapter = await DatabaseAdapterFactory.getCacheAdapter()
      
      if (cacheAdapter.cleanExpired) {
        const cleanedCount = await cacheAdapter.cleanExpired()
        logger.success(`清理了 ${cleanedCount} 条过期缓存记录`)
      } else {
        logger.info('当前数据库不支持自动清理过期数据')
      }
    } catch (error) {
      logger.error('清理过期数据失败:', error)
      throw error
    }
  }

  /**
   * 关闭数据库连接
   */
  static async close(): Promise<void> {
    try {
      await DatabaseAdapterFactory.close()
      logger.info('数据库连接已关闭')
    } catch (error) {
      logger.error('关闭数据库连接失败:', error)
      throw error
    }
  }
}

/**
 * 便捷函数 - 初始化数据库
 */
export async function initializeDatabase(): Promise<void> {
  await DatabaseMigration.initializeDatabase()
}

/**
 * 便捷函数 - 迁移数据
 */
export async function migrateToMongoDB(): Promise<void> {
  await DatabaseMigration.migrateFromSQLiteToMongoDB()
}

/**
 * 便捷函数 - 验证迁移
 */
export async function validateMigration(): Promise<void> {
  await DatabaseMigration.validateMigration()
}

/**
 * 便捷函数 - 清理过期数据
 */
export async function cleanupExpiredData(): Promise<void> {
  await DatabaseMigration.cleanupExpiredData()
}