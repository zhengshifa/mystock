/**
 * 调度器配置文件
 * 管理新闻数据获取的各种参数和设置
 */

export interface SchedulerConfig {
  // 数据获取间隔（毫秒）
  fetchInterval: number
  // 每次获取的最大新闻数量
  maxNewsPerSource: number
  // 重试次数
  maxRetries: number
  // 重试延迟（毫秒）
  retryDelay: number
  // 是否启用并发获取
  enableConcurrent: boolean
  // 并发获取时的延迟间隔（毫秒）
  concurrentDelay: number
  // 日志级别
  logLevel: 'debug' | 'info' | 'warn' | 'error'
  // 是否保存原始HTML内容
  saveRawHtml: boolean
  // 数据清理设置
  cleanup: {
    // 是否启用自动清理
    enabled: boolean
    // 清理间隔（毫秒）
    interval: number
    // 保留天数
    keepDays: number
  }
}

// 默认配置
export const defaultConfig: SchedulerConfig = {
  fetchInterval: 5 * 60 * 1000, // 5分钟
  maxNewsPerSource: 50,
  maxRetries: 3,
  retryDelay: 1000,
  enableConcurrent: true,
  concurrentDelay: 1000,
  logLevel: 'info',
  saveRawHtml: false,
  cleanup: {
    enabled: true,
    interval: 24 * 60 * 60 * 1000, // 24小时
    keepDays: 30
  }
}

// 开发环境配置
export const devConfig: SchedulerConfig = {
  ...defaultConfig,
  fetchInterval: 1 * 60 * 1000, // 1分钟
  logLevel: 'debug',
  saveRawHtml: true
}

// 生产环境配置
export const prodConfig: SchedulerConfig = {
  ...defaultConfig,
  fetchInterval: 10 * 60 * 1000, // 10分钟
  logLevel: 'info',
  saveRawHtml: false
}

// 获取当前环境配置
export function getConfig(): SchedulerConfig {
  const env = process.env.NODE_ENV || 'development'
  
  switch (env) {
    case 'production':
      return prodConfig
    case 'development':
      return devConfig
    default:
      return defaultConfig
  }
}

// 从环境变量覆盖配置
export function loadConfigFromEnv(config: SchedulerConfig): SchedulerConfig {
  const env = process.env
  
  return {
    ...config,
    fetchInterval: parseInt(env.FETCH_INTERVAL || config.fetchInterval.toString()),
    maxNewsPerSource: parseInt(env.MAX_NEWS_PER_SOURCE || config.maxNewsPerSource.toString()),
    maxRetries: parseInt(env.MAX_RETRIES || config.maxRetries.toString()),
    retryDelay: parseInt(env.RETRY_DELAY || config.retryDelay.toString()),
    enableConcurrent: env.ENABLE_CONCURRENT !== 'false',
    concurrentDelay: parseInt(env.CONCURRENT_DELAY || config.concurrentDelay.toString()),
    logLevel: (env.LOG_LEVEL as any) || config.logLevel,
    saveRawHtml: env.SAVE_RAW_HTML === 'true',
    cleanup: {
      ...config.cleanup,
      enabled: env.CLEANUP_ENABLED !== 'false',
      interval: parseInt(env.CLEANUP_INTERVAL || config.cleanup.interval.toString()),
      keepDays: parseInt(env.CLEANUP_KEEP_DAYS || config.cleanup.keepDays.toString())
    }
  }
}


