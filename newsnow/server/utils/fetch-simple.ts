/**
 * 简化的fetch工具函数
 */

/**
 * 带代理的fetch函数
 */
export async function fetchWithProxy(url: string, options: RequestInit = {}): Promise<Response> {
  const proxyUrl = process.env.HTTP_PROXY || process.env.HTTPS_PROXY || 'http://127.0.0.1:7890'
  
  try {
    // 首先尝试直接请求
    const response = await fetch(url, {
      ...options,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ...options.headers
      }
    })
    
    if (response.ok) {
      return response
    }
  } catch (error) {
    console.warn(`直接请求失败: ${url}`, error)
  }
  
  // 如果直接请求失败，尝试使用代理
  try {
    const proxyOptions = {
      ...options,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ...options.headers
      }
    }
    
    // 这里可以集成代理逻辑，暂时返回直接请求
    return await fetch(url, proxyOptions)
  } catch (error) {
    console.error(`代理请求也失败: ${url}`, error)
    throw error
  }
}

/**
 * 简单的fetch包装器
 */
export async function myFetch(url: string, options: RequestInit = {}): Promise<Response> {
  return fetchWithProxy(url, options)
}

/**
 * 获取HTML内容
 */
export async function getHtml(url: string): Promise<string> {
  const response = await fetchWithProxy(url)
  return await response.text()
}

/**
 * 获取JSON内容
 */
export async function getJson<T = any>(url: string): Promise<T> {
  const response = await fetchWithProxy(url)
  return await response.json()
}


