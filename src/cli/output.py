"""
审判结果输出格式化模块

提供多种格式的审判结果输出
"""

import json
from typing import Dict, Any, List
from datetime import datetime


class OutputFormatter:
    """审判结果格式化器"""

    @staticmethod
    def format_batch_summary(summary: Dict[str, Any]) -> str:
        """
        格式化批量审判汇总

        Args:
            summary: 审判汇总信息

        Returns:
            文本格式字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("                    批量审判汇总")
        lines.append("=" * 60)
        lines.append("")

        lines.append(f"总案件数: {summary.get('total_cases', 0)}")
        lines.append(f"完成: {summary.get('completed_cases', 0)}")
        lines.append(f"失败: {summary.get('error_cases', 0)}")
        lines.append(f"指控总金额: ¥{summary.get('total_accused_amount', 0):.2f}")
        lines.append(f"核减总金额: ¥{summary.get('total_ruling_amount', 0):.2f}")
        lines.append("")

        verdict_counts = summary.get('verdict_distribution', {})
        if verdict_counts:
            lines.append("裁决分布:")
            for verdict, count in verdict_counts.items():
                lines.append(f"  - {verdict}: {count}")

        lines.append("")
        lines.append(f"生成时间: {summary.get('generation_time', 'N/A')}")

        return "\n".join(lines)

    @staticmethod
    def format_json(result: Dict[str, Any], indent: int = 2) -> str:
        """
        格式化为 JSON

        Args:
            result: 审判结果
            indent: 缩进空格数

        Returns:
            JSON 格式字符串
        """
        return json.dumps(result, ensure_ascii=False, indent=indent)

    @staticmethod
    def format_text(result: Dict[str, Any]) -> str:
        """
        格式化为易读的文本

        Args:
            result: 审判结果

        Returns:
            文本格式字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("            医保费用审判模拟器 - 审判结果")
        lines.append("=" * 60)
        lines.append("")

        # 基本信息
        lines.append("【案件信息】")
        lines.append(f"  案件编号: {result.get('case_id', 'N/A')}")
        lines.append(f"  开始时间: {result.get('start_time', 'N/A')}")
        lines.append(f"  结束时间: {result.get('end_time', 'N/A')}")
        lines.append(f"  状态: {result.get('status', 'N/A')}")
        lines.append("")

        # 费用统计
        lines.append("【费用统计】")
        lines.append(f"  涉及费用项目数: {len(result.get('expense_items', []))}")
        lines.append(f"  涉及差异项目数: {len(result.get('diff_items', []))}")
        lines.append(f"  总指控金额: ¥{result.get('total_accused_amount', 0):.2f}")
        lines.append("")

        # 审判阶段
        phases = result.get("phases", [])
        if phases:
            lines.append("【审判过程】")
            for phase in phases:
                phase_name = phase.get("phase", "unknown")
                phase_label = {
                    "prosecutor": "起诉阶段",
                    "defense": "辩护阶段",
                    "judge": "裁决阶段",
                }.get(phase_name, phase_name)

                lines.append(f"\n  ▶ {phase_label}")
                statement = phase.get("statement", {})
                content = statement.get("content", "")

                # 截取前 200 字符作为预览
                if len(content) > 200:
                    content = content[:200] + "..."

                lines.append(f"    {content.replace(chr(10), chr(10) + '    ')}")

                if phase.get("error"):
                    lines.append(f"    [错误]: {phase['error']}")
            lines.append("")

        # 最终裁决
        lines.append("=" * 60)
        lines.append("                        最终裁决")
        lines.append("=" * 60)
        lines.append("")

        verdict = result.get("final_verdict", "待定")
        ruling_amount = result.get("ruling_amount", 0.0)
        ruling_reason = result.get("ruling_reason", "待定")

        lines.append(f"  裁决结果: {verdict}")
        lines.append(f"  核减金额: ¥{ruling_amount:.2f}")
        lines.append(f"  裁决理由: {ruling_reason}")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_markdown(result: Dict[str, Any]) -> str:
        """
        格式化为 Markdown

        Args:
            result: 审判结果

        Returns:
            Markdown 格式字符串
        """
        lines = []
        lines.append("# 医保费用审判结果")
        lines.append("")

        # 基本信息
        lines.append("## 案件信息")
        lines.append("")
        lines.append(f"- **案件编号**: {result.get('case_id', 'N/A')}")
        lines.append(f"- **开始时间**: {result.get('start_time', 'N/A')}")
        lines.append(f"- **结束时间**: {result.get('end_time', 'N/A')}")
        lines.append(f"- **状态**: {result.get('status', 'N/A')}")
        lines.append("")

        # 费用统计
        lines.append("## 费用统计")
        lines.append("")
        lines.append(f"- 涉及费用项目数: {len(result.get('expense_items', []))}")
        lines.append(f"- 涉及差异项目数: {len(result.get('diff_items', []))}")
        lines.append(f"- 总指控金额: ¥{result.get('total_accused_amount', 0):.2f}")
        lines.append("")

        # 审判阶段
        phases = result.get("phases", [])
        if phases:
            lines.append("## 审判过程")
            lines.append("")
            for phase in phases:
                phase_name = phase.get("phase", "unknown")
                phase_label = {
                    "prosecutor": "起诉阶段",
                    "defense": "辩护阶段",
                    "judge": "裁决阶段",
                }.get(phase_name, phase_name)

                lines.append(f"### {phase_label}")
                lines.append("")
                statement = phase.get("statement", {})
                content = statement.get("content", "")

                # 转换为 Markdown 引用格式
                lines.append("> " + content.replace("\n", "\n> "))
                lines.append("")

                if phase.get("error"):
                    lines.append(f"**错误**: {phase['error']}")
                    lines.append("")

        # 最终裁决
        lines.append("## 最终裁决")
        lines.append("")
        lines.append(f"**裁决结果**: {result.get('final_verdict', '待定')}")
        lines.append("")
        lines.append(f"**核减金额**: ¥{result.get('ruling_amount', 0):.2f}")
        lines.append("")
        lines.append(f"**裁决理由**: {result.get('ruling_reason', '待定')}")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_html(result: Dict[str, Any]) -> str:
        """
        格式化为 HTML

        Args:
            result: 审判结果

        Returns:
            HTML 格式字符串
        """
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>医保费用审判结果 - {result.get('case_id', 'N/A')}</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 25px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin: 15px 0;
        }}
        .info-item {{
            padding: 10px;
            background: #ecf0f1;
            border-radius: 4px;
        }}
        .info-label {{
            font-weight: bold;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .info-value {{
            color: #2c3e50;
            font-size: 1.1em;
            margin-top: 5px;
        }}
        .phase {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        .phase-title {{
            font-weight: bold;
            color: #e67e22;
            font-size: 1.1em;
        }}
        .phase-content {{
            margin-top: 10px;
            white-space: pre-wrap;
            line-height: 1.6;
            background: white;
            padding: 15px;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }}
        .verdict {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            margin-top: 25px;
        }}
        .verdict-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .verdict-amount {{
            font-size: 2em;
            font-weight: bold;
        }}
        .verdict-reason {{
            margin-top: 15px;
            opacity: 0.9;
        }}
        .error {{
            color: #e74c3c;
            padding: 10px;
            background: #fadbd8;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ 医保费用审判结果</h1>

        <h2>📋 案件信息</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">案件编号</div>
                <div class="info-value">{result.get('case_id', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">状态</div>
                <div class="info-value">{result.get('status', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">开始时间</div>
                <div class="info-value">{result.get('start_time', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">结束时间</div>
                <div class="info-value">{result.get('end_time', 'N/A')}</div>
            </div>
        </div>

        <h2>💰 费用统计</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">涉及费用项目</div>
                <div class="info-value">{len(result.get('expense_items', []))} 项</div>
            </div>
            <div class="info-item">
                <div class="info-label">涉及差异项目</div>
                <div class="info-value">{len(result.get('diff_items', []))} 项</div>
            </div>
            <div class="info-item">
                <div class="info-label">总指控金额</div>
                <div class="info-value">¥{result.get('total_accused_amount', 0):.2f}</div>
            </div>
            <div class="info-item">
                <div class="info-label">核减金额</div>
                <div class="info-value">¥{result.get('ruling_amount', 0):.2f}</div>
            </div>
        </div>
"""

        # 审判阶段
        phases = result.get("phases", [])
        if phases:
            html += "        <h2>⚖️ 审判过程</h2>\n"
            for phase in phases:
                phase_name = phase.get("phase", "unknown")
                phase_label = {
                    "prosecutor": "起诉阶段",
                    "defense": "辩护阶段",
                    "judge": "裁决阶段",
                }.get(phase_name, phase_name)

                statement = phase.get("statement", {})
                content = statement.get("content", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                html += f"""
        <div class="phase">
            <div class="phase-title">{phase_label}</div>
            <div class="phase-content">{content}</div>
"""
                if phase.get("error"):
                    html += f'            <div class="error">{phase["error"]}</div>\n'
                html += "        </div>\n"

        # 最终裁决
        verdict = result.get("final_verdict", "待定")
        ruling_amount = result.get("ruling_amount", 0.0)
        ruling_reason = result.get("ruling_reason", "待定")

        html += f"""
        <div class="verdict">
            <div class="verdict-title">🎯 最终裁决</div>
            <div class="verdict-amount">{verdict}</div>
            <div class="verdict-amount">¥{ruling_amount:.2f}</div>
            <div class="verdict-reason">{ruling_reason}</div>
        </div>
    </div>
</body>
</html>
"""
        return html
