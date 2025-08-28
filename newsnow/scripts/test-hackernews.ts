#!/usr/bin/env node

/**
 * 测试Hacker News源是否正常工作
 * 用于验证网络请求和代理配置
 */

import { consola } from "consola"
import { proxyConfig } from "../server/config/proxy"
import { myFetch } from "../server/utils/fetch"

/**
 * 测试代理配置
 */
function testProxyConfig() {
  consola.info("=== 代理配置测试 ===")
  consola.info(`代理URL: ${proxyConfig.url}`)
  consola.info(`代理启用: ${proxyConfig.enabled}`)
  consola.info(`最大重试次数: ${proxyConfig.maxRetries}`)
  consola.info(`代理超时: ${proxyConfig.timeout}ms`)
  consola.info(`普通请求超时: ${proxyConfig.normalTimeout}ms`)
}

/**
 * 测试网络连接
 */
async function testNetworkConnection() {
  consola.info("=== 网络连接测试 ===")
  
  const testUrls = [
    "https://news.ycombinator.com",
    "https://httpbin.org/ip",
    "https://api.github.com"
  ]
  
  for (const url of testUrls) {
    try {
      consola.info(`测试连接: ${url}`)
      const startTime = Date.now()
      const result = await myFetch(url)
      const endTime = Date.now()
      
      if (result) {
        consola.success(`✓ ${url} - 成功 (${endTime - startTime}ms)`)
        if (typeof result === 'string') {
          consola.info(`  响应长度: ${result.length} 字符`)
        } else {
          consola.info(`  响应类型: ${typeof result}`)
        }
      } else {
        consola.warn(`⚠ ${url} - 响应为空`)
      }
    } catch (error) {
      consola.error(`✗ ${url} - 失败:`, error)
    }
    
    // 等待一下再测试下一个
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
}

/**
 * 测试Hacker News源
 */
async function testHackerNewsSource() {
  consola.info("=== Hacker News源测试 ===")
  
  try {
    // 动态导入源
    const { default: hackernewsSource } = await import("../server/sources/hackernews")
    
    consola.info("开始获取Hacker News数据...")
    const startTime = Date.now()
    const news = await hackernewsSource()
    const endTime = Date.now()
    
    if (news && Array.isArray(news)) {
      consola.success(`✓ 成功获取 ${news.length} 条新闻 (${endTime - startTime}ms)`)
      
      // 显示前几条新闻
      news.slice(0, 3).forEach((item, index) => {
        consola.info(`  ${index + 1}. ${item.title}`)
        consola.info(`     链接: ${item.url}`)
        consola.info(`     分数: ${item.extra?.info || 'N/A'}`)
      })
      
      if (news.length > 3) {
        consola.info(`  ... 还有 ${news.length - 3} 条新闻`)
      }
    } else {
      consola.warn("⚠ 获取到的数据格式不正确")
    }
  } catch (error) {
    consola.error("✗ Hacker News源测试失败:", error)
  }
}

/**
 * 主函数
 */
async function main() {
  try {
    consola.start("开始测试Hacker News源...")
    
    // 测试代理配置
    testProxyConfig()
    
    // 测试网络连接
    await testNetworkConnection()
    
    // 测试Hacker News源
    await testHackerNewsSource()
    
    consola.success("测试完成！")
  } catch (error) {
    consola.error("测试过程中发生错误:", error)
    process.exit(1)
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  main()
}
