/**
 * 工具函数统一导出
 */

// 基础工具函数
export * from './base64'
export * from './crypto'
export * from './date'
export * from './fetch'
export * from './logger'
export * from './proxy'
export * from './rss2json'
export * from './source'

// 简化的工具函数
export * from './source-simple'
export * from './fetch-simple'

/**
 * 延迟函数
 * @param ms 延迟毫秒数
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 生成随机延迟时间
 * @param min 最小延迟毫秒数
 * @param max 最大延迟毫秒数
 */
export function randomDelay(min: number = 1000, max: number = 3000): Promise<void> {
  const delay = Math.floor(Math.random() * (max - min + 1)) + min
  return sleep(delay)
}

/**
 * 格式化时间
 * @param date 日期对象
 */
export function formatTime(date: Date): string {
  return date.toISOString()
}

/**
 * 检查是否为有效URL
 * @param url 要检查的URL
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * 清理HTML标签
 * @param html HTML字符串
 */
export function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').trim()
}

/**
 * 截断文本
 * @param text 原文本
 * @param maxLength 最大长度
 * @param suffix 后缀
 */
export function truncateText(text: string, maxLength: number, suffix: string = '...'): string {
  if (text.length <= maxLength) {
    return text
  }
  return text.substring(0, maxLength - suffix.length) + suffix
}
