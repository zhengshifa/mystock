/**
 * 代理配置模块
 * 统一管理网络请求的代理设置
 */

import { envConfig } from './env'

export interface ProxyConfig {
  /** 代理服务器URL */
  url: string
  /** 备用代理服务器URL */
  fallbackUrl: string
  /** 最大重试次数，达到此次数后启用代理 */
  maxRetries: number
  /** 是否启用代理功能 */
  enabled: boolean
  /** 代理超时时间（毫秒） */
  timeout: number
  /** 普通请求超时时间（毫秒） */
  normalTimeout: number
  /** 是否自动检测代理可用性 */
  autoDetect: boolean
}

/**
 * 从环境配置获取代理配置
 * @returns 代理配置对象
 */
export function getProxyConfig(): ProxyConfig {
  return {
    url: envConfig.proxy.url,
    fallbackUrl: envConfig.proxy.fallbackUrl,
    maxRetries: envConfig.proxy.maxRetries,
    enabled: envConfig.proxy.enabled,
    timeout: envConfig.proxy.timeout,
    normalTimeout: envConfig.proxy.normalTimeout,
    autoDetect: envConfig.proxy.autoDetect
  }
}

/**
 * 导出默认配置供其他模块使用
 */
export const proxyConfig = getProxyConfig()