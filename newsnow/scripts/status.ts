#!/usr/bin/env tsx

/**
 * 项目状态检查脚本
 * 检查系统环境、依赖状态和配置是否正确
 */

import { consola } from 'consola'
import { execSync } from 'child_process'
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

interface StatusCheck {
  name: string
  status: 'pass' | 'fail' | 'warning'
  message: string
  details?: string
}

/**
 * 检查Node.js版本
 */
function checkNodeVersion(): StatusCheck {
  try {
    const version = process.version
    const majorVersion = parseInt(version.slice(1).split('.')[0])
    
    if (majorVersion >= 18) {
      return {
        name: 'Node.js版本',
        status: 'pass',
        message: `✓ Node.js ${version} (满足要求 >= 18)`
      }
    } else {
      return {
        name: 'Node.js版本',
        status: 'fail',
        message: `✗ Node.js ${version} (需要 >= 18)`,
        details: '请升级Node.js到18或更高版本'
      }
    }
  } catch (error) {
    return {
      name: 'Node.js版本',
      status: 'fail',
      message: '✗ 无法获取Node.js版本',
      details: error instanceof Error ? error.message : '未知错误'
    }
  }
}

/**
 * 检查pnpm是否安装
 */
function checkPnpm(): StatusCheck {
  try {
    const version = execSync('pnpm --version', { encoding: 'utf8' }).trim()
    return {
      name: 'pnpm包管理器',
      status: 'pass',
      message: `✓ pnpm ${version}`
    }
  } catch (error) {
    return {
      name: 'pnpm包管理器',
      status: 'fail',
      message: '✗ pnpm未安装',
      details: '请安装pnpm: npm install -g pnpm'
    }
  }
}

/**
 * 检查依赖是否安装
 */
function checkDependencies(): StatusCheck {
  if (!existsSync('node_modules')) {
    return {
      name: '项目依赖',
      status: 'fail',
      message: '✗ 依赖未安装',
      details: '请运行: pnpm install'
    }
  }
  
  if (!existsSync('node_modules/.pnpm')) {
    return {
      name: '项目依赖',
      status: 'warning',
      message: '⚠ 依赖可能不完整',
      details: '建议重新运行: pnpm install'
    }
  }
  
  return {
    name: '项目依赖',
    status: 'pass',
    message: '✓ 依赖已安装'
  }
}

/**
 * 检查环境配置文件
 */
function checkEnvironmentConfig(): StatusCheck {
  if (!existsSync('.env.scheduler')) {
    if (existsSync('example.env.scheduler')) {
      return {
        name: '环境配置',
        status: 'warning',
        message: '⚠ 环境配置文件不存在',
        details: '请复制 example.env.scheduler 为 .env.scheduler 并配置'
      }
    } else {
      return {
        name: '环境配置',
        status: 'fail',
        message: '✗ 环境配置文件不存在',
        details: '缺少 example.env.scheduler 文件'
      }
    }
  }
  
  return {
    name: '环境配置',
    status: 'pass',
    message: '✓ 环境配置文件存在'
  }
}

/**
 * 检查MongoDB连接
 */
async function checkMongoDB(): Promise<StatusCheck> {
  try {
    const { MongoClient } = await import('mongodb')
    const client = new MongoClient('mongodb://localhost:27017')
    
    await client.connect()
    await client.close()
    
    return {
      name: 'MongoDB连接',
      status: 'pass',
      message: '✓ MongoDB连接成功'
    }
  } catch (error) {
    return {
      name: 'MongoDB连接',
      status: 'fail',
      message: '✗ MongoDB连接失败',
      details: error instanceof Error ? error.message : '请确保MongoDB服务正在运行'
    }
  }
}

/**
 * 检查项目文件结构
 */
function checkProjectStructure(): StatusCheck {
  const requiredFiles = [
    'scripts/scheduler.ts',
    'scripts/cleanup.ts',
    'scripts/config.ts',
    'server/database/mongodb.ts',
    'server/getters.ts',
    'shared/types.ts'
  ]
  
  const missingFiles = requiredFiles.filter(file => !existsSync(file))
  
  if (missingFiles.length === 0) {
    return {
      name: '项目结构',
      status: 'pass',
      message: '✓ 项目文件结构完整'
    }
  } else {
    return {
      name: '项目结构',
      status: 'fail',
      message: `✗ 缺少 ${missingFiles.length} 个文件`,
      details: `缺少文件: ${missingFiles.join(', ')}`
    }
  }
}

/**
 * 检查日志目录
 */
function checkLogsDirectory(): StatusCheck {
  if (!existsSync('logs')) {
    return {
      name: '日志目录',
      status: 'warning',
      message: '⚠ 日志目录不存在',
      details: '将自动创建 logs 目录'
    }
  }
  
  return {
    name: '日志目录',
    status: 'pass',
    message: '✓ 日志目录存在'
  }
}

/**
 * 运行所有检查
 */
async function runAllChecks(): Promise<StatusCheck[]> {
  consola.info('开始检查项目状态...')
  consola.info('')
  
  const checks: StatusCheck[] = []
  
  // 同步检查
  checks.push(checkNodeVersion())
  checks.push(checkPnpm())
  checks.push(checkDependencies())
  checks.push(checkEnvironmentConfig())
  checks.push(checkProjectStructure())
  checks.push(checkLogsDirectory())
  
  // 异步检查
  checks.push(await checkMongoDB())
  
  return checks
}

/**
 * 显示检查结果
 */
function displayResults(checks: StatusCheck[]) {
  consola.info('检查结果:')
  consola.info('')
  
  let passCount = 0
  let warningCount = 0
  let failCount = 0
  
  checks.forEach(check => {
    const icon = check.status === 'pass' ? '✓' : check.status === 'warning' ? '⚠' : '✗'
    const color = check.status === 'pass' ? 'green' : check.status === 'warning' ? 'yellow' : 'red'
    
    consola.log(`${icon} ${check.name}: ${check.message}`)
    
    if (check.details) {
      consola.log(`    ${check.details}`)
    }
    
    switch (check.status) {
      case 'pass':
        passCount++
        break
      case 'warning':
        warningCount++
        break
      case 'fail':
        failCount++
        break
    }
  })
  
  consola.info('')
  consola.info('状态摘要:')
  consola.info(`  通过: ${passCount}`)
  consola.info(`  警告: ${warningCount}`)
  consola.info(`  失败: ${failCount}`)
  
  if (failCount === 0 && warningCount === 0) {
    consola.success('🎉 所有检查通过！项目可以正常运行')
  } else if (failCount === 0) {
    consola.warn('⚠️ 有警告，但项目可以运行')
  } else {
    consola.error('❌ 有错误，请修复后重试')
  }
  
  return { passCount, warningCount, failCount }
}

/**
 * 提供修复建议
 */
function provideFixSuggestions(checks: StatusCheck[]) {
  const failedChecks = checks.filter(check => check.status === 'fail')
  
  if (failedChecks.length === 0) {
    return
  }
  
  consola.info('')
  consola.info('修复建议:')
  
  failedChecks.forEach(check => {
    consola.info(`  ${check.name}:`)
    if (check.details) {
      consola.info(`    ${check.details}`)
    }
  })
}

// 主程序入口
async function main() {
  try {
    const checks = await runAllChecks()
    const results = displayResults(checks)
    provideFixSuggestions(checks)
    
    // 如果有错误，返回非零退出码
    if (results.failCount > 0) {
      process.exit(1)
    }
  } catch (error) {
    consola.error('检查过程中发生错误:', error)
    process.exit(1)
  }
}

// 运行主程序
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error)
}


