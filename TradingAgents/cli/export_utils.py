#!/usr/bin/env python3
"""
CLI导出工具模块
支持将分析结果导出为多种格式
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('cli')

# 导入导出相关库
try:
    import markdown
    import re
    import tempfile
    import os
    from pathlib import Path

    # 导入pypandoc（用于markdown转docx和pdf）
    import pypandoc

    # 检查pandoc是否可用
    try:
        pypandoc.get_pandoc_version()
        PANDOC_AVAILABLE = True
    except OSError:
        logger.warning(f"⚠️ 未找到pandoc，正在尝试自动下载...")
        try:
            pypandoc.download_pandoc()
            PANDOC_AVAILABLE = True
            logger.info(f"✅ pandoc下载成功！")
        except Exception as download_error:
            logger.error(f"❌ pandoc下载失败: {download_error}")
            PANDOC_AVAILABLE = False

    EXPORT_AVAILABLE = True

except ImportError as e:
    EXPORT_AVAILABLE = False
    PANDOC_AVAILABLE = False
    logger.info(f"导出功能依赖包缺失: {e}")
    logger.info(f"请安装: pip install pypandoc markdown")


class CLIReportExporter:
    """CLI专用报告导出器"""

    def __init__(self):
        self.export_available = EXPORT_AVAILABLE
        self.pandoc_available = PANDOC_AVAILABLE

        # 记录初始化状态
        logger.info(f"📋 CLIReportExporter初始化:")
        logger.info(f"  - export_available: {self.export_available}")
        logger.info(f"  - pandoc_available: {self.pandoc_available}")

    def _clean_text_for_markdown(self, text: str) -> str:
        """清理文本中可能导致YAML解析问题的字符"""
        if not text:
            return ""
        
        # 替换可能导致YAML解析问题的字符
        text = text.replace('---', '—')  # 替换YAML分隔符
        text = text.replace('...', '…')  # 替换省略号
        text = text.replace('|', '｜')  # 替换管道符
        text = text.replace('`', '`')  # 替换反引号
        
        return text

    def _clean_markdown_for_pandoc(self, content: str) -> str:
        """清理Markdown内容，避免pandoc转换问题"""
        if not content:
            return ""
        
        # 清理可能导致YAML解析问题的内容
        content = self._clean_text_for_markdown(content)
        
        # 移除可能的YAML front matter
        lines = content.split('\n')
        if lines and lines[0].strip() == '---':
            # 找到结束的---
            end_idx = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    end_idx = i
                    break
            if end_idx > 0:
                content = '\n'.join(lines[end_idx + 1:])
        
        return content

    def generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """生成Markdown格式的报告"""
        logger.info("📝 开始生成Markdown报告...")
        
        # 获取基本信息
        ticker = results.get('ticker', 'UNKNOWN')
        analysis_date = results.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建Markdown内容
        md_content = f"""# 股票分析报告: {ticker}

## 📊 基本信息

- **股票代码**: {ticker}
- **分析日期**: {analysis_date}
- **生成时间**: {timestamp}
- **分析类型**: 综合股票分析

## 📈 分析结果

### 投资决策摘要
{results.get('final_trade_decision', '暂无决策信息')}

### 市场分析
{results.get('market_analysis', '暂无市场分析信息')}

### 基本面分析
{results.get('fundamentals_analysis', '暂无基本面分析信息')}

### 新闻分析
{results.get('news_analysis', '暂无新闻分析信息')}

### 社交媒体分析
{results.get('social_analysis', '暂无社交媒体分析信息')}

### 风险管理
{results.get('risk_analysis', '暂无风险管理信息')}

## 📝 技术信息

- **分析时间**: {timestamp}
- **报告版本**: v1.0
- **数据来源**: TradingAgents-CN

---

*本报告由TradingAgents-CN自动生成，仅供参考，不构成投资建议。*
*报告生成时间: {timestamp}*
"""
        
        return md_content

    def generate_docx_report(self, results: Dict[str, Any]) -> bytes:
        """生成Word文档格式的报告"""
        logger.info("📄 开始生成Word文档...")

        if not self.pandoc_available:
            logger.error("❌ Pandoc不可用")
            raise Exception("Pandoc不可用，无法生成Word文档。请安装pandoc或使用Markdown格式导出。")

        # 首先生成markdown内容
        logger.info("📝 生成Markdown内容...")
        md_content = self.generate_markdown_report(results)
        logger.info(f"✅ Markdown内容生成完成，长度: {len(md_content)} 字符")

        try:
            logger.info("📁 创建临时文件用于docx输出...")
            # 创建临时文件用于docx输出
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                output_file = tmp_file.name
            logger.info(f"📁 临时文件路径: {output_file}")

            # 使用强制禁用YAML的参数
            extra_args = ['--from=markdown-yaml_metadata_block']  # 禁用YAML解析
            logger.info(f"🔧 pypandoc参数: {extra_args} (禁用YAML解析)")

            logger.info("🔄 使用pypandoc将markdown转换为docx...")

            # 清理内容避免YAML解析问题
            cleaned_content = self._clean_markdown_for_pandoc(md_content)

            # 使用pypandoc将markdown转换为docx - 禁用YAML解析
            pypandoc.convert_text(
                cleaned_content,
                'docx',
                format='markdown',  # 基础markdown格式
                outputfile=output_file,
                extra_args=extra_args
            )

            # 检查文件是否生成且有内容
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                # 读取生成的docx文件
                with open(output_file, 'rb') as f:
                    docx_content = f.read()

                # 清理临时文件
                os.unlink(output_file)

                logger.info("✅ Word文档生成成功")
                return docx_content
            else:
                raise Exception("Word文档生成失败或为空")

        except Exception as e:
            logger.error(f"❌ Word文档生成失败: {e}")
            # 清理临时文件
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise e

    def generate_pdf_report(self, results: Dict[str, Any]) -> bytes:
        """生成PDF格式的报告"""
        logger.info("📊 开始生成PDF报告...")

        if not self.pandoc_available:
            logger.error("❌ Pandoc不可用")
            raise Exception("Pandoc不可用，无法生成PDF文档。请安装pandoc或使用Markdown格式导出。")

        # 首先生成markdown内容
        logger.info("📝 生成Markdown内容...")
        md_content = self.generate_markdown_report(results)
        logger.info(f"✅ Markdown内容生成完成，长度: {len(md_content)} 字符")

        # PDF引擎优先级列表
        pdf_engines = [
            ('wkhtmltopdf', 'wkhtmltopdf引擎'),
            ('weasyprint', 'weasyprint引擎'),
            (None, '默认引擎')
        ]

        last_error = None

        for engine_info in pdf_engines:
            engine, description = engine_info
            try:
                # 创建临时文件用于PDF输出
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    output_file = tmp_file.name

                # 使用禁用YAML解析的参数
                extra_args = ['--from=markdown-yaml_metadata_block']

                # 如果指定了引擎，添加引擎参数
                if engine:
                    extra_args.append(f'--pdf-engine={engine}')
                    logger.info(f"🔧 使用PDF引擎: {engine}")
                else:
                    logger.info(f"🔧 使用默认PDF引擎")

                logger.info(f"🔧 PDF参数: {extra_args}")

                # 清理内容避免YAML解析问题
                cleaned_content = self._clean_markdown_for_pandoc(md_content)

                # 使用pypandoc将markdown转换为PDF - 禁用YAML解析
                pypandoc.convert_text(
                    cleaned_content,
                    'pdf',
                    format='markdown',  # 基础markdown格式
                    outputfile=output_file,
                    extra_args=extra_args
                )

                # 检查文件是否生成且有内容
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    # 读取生成的PDF文件
                    with open(output_file, 'rb') as f:
                        pdf_content = f.read()

                    # 清理临时文件
                    os.unlink(output_file)

                    logger.info(f"✅ PDF生成成功，使用引擎: {engine or '默认'}")
                    return pdf_content
                else:
                    raise Exception("PDF文件生成失败或为空")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"⚠️ {description}失败: {e}")
                # 清理临时文件
                if os.path.exists(output_file):
                    os.unlink(output_file)
                continue

        # 所有引擎都失败
        error_msg = f"❌ 所有PDF引擎都失败，最后错误: {last_error}\n"
        error_msg += "请检查以下依赖:\n"
        error_msg += "1. 安装pandoc: https://pandoc.org/installing.html\n"
        error_msg += "2. 安装wkhtmltopdf: https://wkhtmltopdf.org/downloads.html\n"
        error_msg += "3. 或安装weasyprint: pip install weasyprint"
        raise Exception(error_msg)

    def export_report(self, results: Dict[str, Any], format_type: str) -> Optional[bytes]:
        """导出报告为指定格式"""
        logger.info(f"🚀 开始导出报告: format={format_type}")

        if not self.export_available:
            logger.error("❌ 导出功能不可用")
            return None

        try:
            if format_type in ['markdown', 'md']:
                logger.info("📝 生成Markdown报告...")
                content = self.generate_markdown_report(results)
                logger.info(f"✅ Markdown报告生成成功，长度: {len(content)} 字符")
                return content.encode('utf-8')

            elif format_type == 'docx':
                logger.info("📄 生成Word文档...")
                if not self.pandoc_available:
                    logger.error("❌ pandoc不可用，无法生成Word文档")
                    return None
                content = self.generate_docx_report(results)
                logger.info(f"✅ Word文档生成成功，大小: {len(content)} 字节")
                return content

            elif format_type == 'pdf':
                logger.info("📊 生成PDF文档...")
                if not self.pandoc_available:
                    logger.error("❌ pandoc不可用，无法生成PDF文档")
                    return None
                content = self.generate_pdf_report(results)
                logger.info(f"✅ PDF文档生成成功，大小: {len(content)} 字节")
                return content

            else:
                logger.error(f"❌ 不支持的导出格式: {format_type}")
                return None

        except Exception as e:
            logger.error(f"❌ 导出失败: {str(e)}")
            return None

    def save_report_to_file(self, content: bytes, filename: str, output_dir: str) -> str:
        """保存报告到文件"""
        try:
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            file_path = output_path / filename
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"✅ 报告已保存到: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ 保存报告失败: {e}")
            return ""


# 创建全局导出器实例
cli_report_exporter = CLIReportExporter()
