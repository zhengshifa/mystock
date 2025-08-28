/**
 * 环境配置管理
 * 统一管理应用的环境变量和配置
 */

export interface EnvConfig {
  /** 代理配置 */
  proxy: {
    url: string
    fallbackUrl: string
    enabled: boolean
    maxRetries: number
    timeout: number
    normalTimeout: number
    autoDetect: boolean
  }
  /** 数据库配置 */
  database: {
    uri: string
  }
  /** 应用配置 */
  app: {
    port: number
    env: string
  }
}

/**
 * 获取环境变量值，支持默认值
 * @param key 环境变量名
 * @param defaultValue 默认值
 * @returns 环境变量值或默认值
 */
function getEnv(key: string, defaultValue: string): string {
  return process.env[key] || defaultValue
}

/**
 * 获取环境变量数值，支持默认值
 * @param key 环境变量名
 * @param defaultValue 默认值
 * @returns 环境变量数值或默认值
 */
function getEnvNumber(key: string, defaultValue: number): number {
  const value = process.env[key]
  return value ? parseInt(value, 10) : defaultValue
}

/**
 * 获取环境变量布尔值，支持默认值
 * @param key 环境变量名
 * @param defaultValue 默认值
 * @returns 环境变量布尔值或默认值
 */
function getEnvBoolean(key: string, defaultValue: boolean): boolean {
  const value = process.env[key]
  if (value === undefined) return defaultValue
  return value.toLowerCase() === 'true'
}

/**
 * 环境配置
 */
export const envConfig: EnvConfig = {
  proxy: {
    url: getEnv('PROXY_URL', 'http://127.0.0.1:7890'),
    fallbackUrl: getEnv('PROXY_FALLBACK_URL', 'http://127.0.0.1:1080'),
    enabled: getEnvBoolean('PROXY_ENABLED', true),
    maxRetries: getEnvNumber('PROXY_MAX_RETRIES', 1),
    timeout: getEnvNumber('PROXY_TIMEOUT', 30000),
    normalTimeout: getEnvNumber('PROXY_NORMAL_TIMEOUT', 20000),
    autoDetect: getEnvBoolean('PROXY_AUTO_DETECT', true)
  },
  database: {
    uri: getEnv('MONGODB_URI', 'mongodb://localhost:27017/newsnow')
  },
  app: {
    port: getEnvNumber('PORT', 3000),
    env: getEnv('NODE_ENV', 'development')
  }
}

/**
 * 打印当前环境配置
 */
export function printEnvConfig(): void {
  console.log('=== 环境配置 ===')
  console.log(`代理URL: ${envConfig.proxy.url}`)
  console.log(`备用代理URL: ${envConfig.proxy.fallbackUrl}`)
  console.log(`代理启用: ${envConfig.proxy.enabled}`)
  console.log(`最大重试次数: ${envConfig.proxy.maxRetries}`)
  console.log(`代理超时: ${envConfig.proxy.timeout}ms`)
  console.log(`普通请求超时: ${envConfig.proxy.normalTimeout}ms`)
  console.log(`自动检测代理: ${envConfig.proxy.autoDetect}`)
  console.log(`数据库URI: ${envConfig.database.uri}`)
  console.log(`应用端口: ${envConfig.app.port}`)
  console.log(`环境: ${envConfig.app.env}`)
  console.log('================')
}
