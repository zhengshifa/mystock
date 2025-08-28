#!/usr/bin/env node

/**
 * 网络诊断工具
 * 用于检测网络连接、代理状态和常见网络问题
 */

import { consola } from "consola"
import { envConfig, printEnvConfig } from "../server/config/env"
import { myFetch } from "../server/utils/fetch"

/**
 * 测试直接网络连接
 */
async function testDirectConnection() {
  consola.info("=== 直接网络连接测试 ===")
  
  const testUrls = [
    "https://httpbin.org/ip",
    "https://api.github.com",
    "https://www.google.com",
    "https://news.ycombinator.com"
  ]
  
  for (const url of testUrls) {
    try {
      consola.info(`测试直接连接: ${url}`)
      const startTime = Date.now()
      
      // 使用原生fetch测试直接连接
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        signal: AbortSignal.timeout(10000)
      })
      
      const endTime = Date.now()
      
      if (response.ok) {
        consola.success(`✓ ${url} - 成功 (${endTime - startTime}ms) - 状态: ${response.status}`)
      } else {
        consola.warn(`⚠ ${url} - 响应异常 (${endTime - startTime}ms) - 状态: ${response.status}`)
      }
    } catch (error) {
      consola.error(`✗ ${url} - 失败:`, error)
    }
    
    // 等待一下再测试下一个
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
}

/**
 * 测试代理连接
 */
async function testProxyConnection() {
  consola.info("=== 代理连接测试 ===")
  
  const proxies = [
    { name: "主代理", url: envConfig.proxy.url },
    { name: "备用代理", url: envConfig.proxy.fallbackUrl }
  ]
  
  for (const proxy of proxies) {
    try {
      consola.info(`测试${proxy.name}: ${proxy.url}`)
      const startTime = Date.now()
      
      const result = await myFetch("https://httpbin.org/ip")
      const endTime = Date.now()
      
      if (result) {
        consola.success(`✓ ${proxy.name} - 成功 (${endTime - startTime}ms)`)
        if (typeof result === 'string') {
          consola.info(`  响应长度: ${result.length} 字符`)
        } else {
          consola.info(`  响应类型: ${typeof result}`)
        }
      } else {
        consola.warn(`⚠ ${proxy.name} - 响应为空`)
      }
    } catch (error) {
      consola.error(`✗ ${proxy.name} - 失败:`, error)
    }
    
    // 等待一下再测试下一个
    await new Promise(resolve => setTimeout(resolve, 2000))
  }
}

/**
 * 测试智能fetch功能
 */
async function testSmartFetch() {
  consola.info("=== 智能Fetch功能测试 ===")
  
  const testUrls = [
    "https://news.ycombinator.com",
    "https://www.producthunt.com",
    "https://httpbin.org/delay/3" // 测试超时
  ]
  
  for (const url of testUrls) {
    try {
      consola.info(`测试智能fetch: ${url}`)
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
    await new Promise(resolve => setTimeout(resolve, 2000))
  }
}

/**
 * 网络诊断建议
 */
function provideDiagnosis() {
  consola.info("=== 网络诊断建议 ===")
  
  if (envConfig.proxy.enabled) {
    consola.info("✓ 代理功能已启用")
    consola.info(`  主代理: ${envConfig.proxy.url}`)
    consola.info(`  备用代理: ${envConfig.proxy.fallbackUrl}`)
    
    if (envConfig.proxy.autoDetect) {
      consola.info("✓ 自动代理检测已启用")
    }
  } else {
    consola.warn("⚠ 代理功能已禁用")
  }
  
  consola.info("")
  consola.info("常见问题解决方案:")
  consola.info("1. 如果直接连接失败，检查网络设置和防火墙")
  consola.info("2. 如果代理连接失败，检查代理服务器是否运行")
  consola.info("3. 如果某些网站无法访问，可能需要配置代理规则")
  consola.info("4. 超时问题可以通过调整超时时间解决")
}

/**
 * 主函数
 */
async function main() {
  try {
    consola.start("开始网络诊断...")
    
    // 显示环境配置
    printEnvConfig()
    
    // 测试直接网络连接
    await testDirectConnection()
    
    // 测试代理连接
    await testProxyConnection()
    
    // 测试智能fetch功能
    await testSmartFetch()
    
    // 提供诊断建议
    provideDiagnosis()
    
    consola.success("网络诊断完成！")
  } catch (error) {
    consola.error("诊断过程中发生错误:", error)
    process.exit(1)
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  main()
}
