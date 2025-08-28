import { $fetch } from "ofetch"
import { proxyConfig } from "../config/proxy"

/**
 * 失败的请求记录，用于跟踪重试次数
 */
const failedRequests = new Map<string, number>()

/**
 * 代理状态记录
 */
const proxyStatus = {
  primary: { available: true, lastCheck: 0 },
  fallback: { available: true, lastCheck: 0 }
}

/**
 * 检测代理可用性
 * @param proxyUrl 代理URL
 * @returns Promise<boolean>
 */
async function checkProxyAvailability(proxyUrl: string): Promise<boolean> {
  try {
    const testFetch = $fetch.create({
      // @ts-ignore - ofetch支持proxy选项
      proxy: proxyUrl,
      timeout: 5000,
      retry: 0
    })
    
    await testFetch("https://httpbin.org/ip")
    return true
  } catch (error) {
    console.warn(`[PROXY] 代理检测失败: ${proxyUrl}`, error)
    return false
  }
}

/**
 * 创建带代理的 fetch 实例
 */
function createProxyFetch(proxyUrl: string) {
  return $fetch.create({
    headers: {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    },
    timeout: proxyConfig.timeout,
    retry: 0, // 代理模式下不再重试
    // @ts-ignore - ofetch支持proxy选项
    proxy: proxyUrl
  })
}

/**
 * 创建普通的 fetch 实例
 */
function createNormalFetch() {
  return $fetch.create({
    headers: {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    },
    timeout: proxyConfig.normalTimeout,
    retry: 0, // 手动控制重试
  })
}

const normalFetch = createNormalFetch()

/**
 * 智能 fetch 函数，支持代理检测和备用代理
 * @param url 请求URL
 * @param options 请求选项
 * @returns Promise<any>
 */
export async function myFetch(url: string | URL, options?: any): Promise<any> {
  const urlString = url.toString()
  const currentFailCount = failedRequests.get(urlString) || 0
  
  // 如果代理已启用且失败达到配置的最大重试次数，尝试使用代理
  if (proxyConfig.enabled && currentFailCount >= proxyConfig.maxRetries) {
    // 检查主代理
    if (proxyStatus.primary.available) {
      try {
        console.log(`[PROXY] 使用主代理请求: ${urlString}`)
        const proxyFetch = createProxyFetch(proxyConfig.url)
        const result = await proxyFetch(urlString, options)
        // 成功后重置失败计数
        failedRequests.delete(urlString)
        console.log(`[PROXY] 主代理请求成功: ${urlString}`)
        return result
      } catch (error) {
        console.error(`[PROXY] 主代理请求失败: ${urlString}`, error)
        proxyStatus.primary.available = false
        proxyStatus.primary.lastCheck = Date.now()
      }
    }
    
    // 尝试备用代理
    if (proxyStatus.fallback.available) {
      try {
        console.log(`[PROXY] 使用备用代理请求: ${urlString}`)
        const fallbackFetch = createProxyFetch(proxyConfig.fallbackUrl)
        const result = await fallbackFetch(urlString, options)
        // 成功后重置失败计数
        failedRequests.delete(urlString)
        console.log(`[PROXY] 备用代理请求成功: ${urlString}`)
        return result
      } catch (error) {
        console.error(`[PROXY] 备用代理请求失败: ${urlString}`, error)
        proxyStatus.fallback.available = false
        proxyStatus.fallback.lastCheck = Date.now()
      }
    }
    
    // 如果所有代理都失败，尝试重新检测
    if (proxyConfig.autoDetect) {
      const now = Date.now()
      if (now - proxyStatus.primary.lastCheck > 60000) { // 1分钟后重新检测
        console.log(`[PROXY] 重新检测主代理可用性: ${proxyConfig.url}`)
        proxyStatus.primary.available = await checkProxyAvailability(proxyConfig.url)
        proxyStatus.primary.lastCheck = now
      }
      
      if (now - proxyStatus.fallback.lastCheck > 60000) { // 1分钟后重新检测
        console.log(`[PROXY] 重新检测备用代理可用性: ${proxyConfig.fallbackUrl}`)
        proxyStatus.fallback.available = await checkProxyAvailability(proxyConfig.fallbackUrl)
        proxyStatus.fallback.lastCheck = now
      }
    }
  }
  
  // 普通请求
  try {
    console.log(`[FETCH] 开始普通请求: ${urlString}`)
    const result = await normalFetch(urlString, options)
    // 成功后重置失败计数
    if (currentFailCount > 0) {
      failedRequests.delete(urlString)
      console.log(`[FETCH] 普通请求成功，重置失败计数: ${urlString}`)
    }
    return result
  } catch (error) {
    const newFailCount = currentFailCount + 1
    failedRequests.set(urlString, newFailCount)
    
    console.warn(`[FETCH] 请求失败 (${newFailCount}/${proxyConfig.maxRetries}): ${urlString}`, error)
    
    // 如果还没达到最大重试次数，继续重试
    if (newFailCount < proxyConfig.maxRetries) {
      // 等待一段时间后重试
      const delay = 1000 * newFailCount
      console.log(`[FETCH] 等待 ${delay}ms 后重试: ${urlString}`)
      await new Promise(resolve => setTimeout(resolve, delay))
      return myFetch(url, options)
    }
    
    // 达到最大重试次数，尝试使用代理
    if (proxyConfig.enabled) {
      // 检查主代理
      if (proxyStatus.primary.available) {
        try {
          console.log(`[PROXY] 普通请求失败${proxyConfig.maxRetries}次，切换到主代理: ${urlString}`)
          const proxyFetch = createProxyFetch(proxyConfig.url)
          const result = await proxyFetch(urlString, options)
          // 成功后重置失败计数
          failedRequests.delete(urlString)
          console.log(`[PROXY] 主代理请求成功: ${urlString}`)
          return result
        } catch (proxyError) {
          console.error(`[PROXY] 主代理请求失败: ${urlString}`, proxyError)
          proxyStatus.primary.available = false
          proxyStatus.primary.lastCheck = Date.now()
        }
      }
      
      // 尝试备用代理
      if (proxyStatus.fallback.available) {
        try {
          console.log(`[PROXY] 尝试备用代理: ${urlString}`)
          const fallbackFetch = createProxyFetch(proxyConfig.fallbackUrl)
          const result = await fallbackFetch(urlString, options)
          // 成功后重置失败计数
          failedRequests.delete(urlString)
          console.log(`[PROXY] 备用代理请求成功: ${urlString}`)
          return result
        } catch (proxyError) {
          console.error(`[PROXY] 备用代理请求失败: ${urlString}`, proxyError)
          proxyStatus.fallback.available = false
          proxyStatus.fallback.lastCheck = Date.now()
        }
      }
      
      console.error(`[FETCH] 所有代理都失败: ${urlString}`)
      throw error
    } else {
      console.error(`[FETCH] 请求失败且代理未启用: ${urlString}`)
      throw error
    }
  }
}
