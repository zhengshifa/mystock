/**
 * 数据库模块导出
 * 提供统一的数据库访问接口
 */

// useDatabase 是 nitro 提供的全局函数，无需导出

// 导出适配器相关
export { 
  DatabaseAdapterFactory,
  getCacheAdapter,
  closeDatabaseAdapter,
  type ICacheAdapter
} from './adapter'

// 导出迁移工具
export {
  DatabaseMigration,
  initializeDatabase,
  migrateToMongoDB,
  validateMigration,
  cleanupExpiredData
} from './migration'

// 导出 MongoDB 相关
export {
  initMongoDB,
  getMongoDatabase,
  closeMongoDB
} from './mongodb'

// 导出传统表类（向后兼容）
export { Cache, getCacheTable } from './cache'