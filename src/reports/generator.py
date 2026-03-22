"""
审判报告生成器

支持 JSON、Markdown、HTML 格式的审判报告输出
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class TrialReportGenerator:
    """审判报告生成器"""

    def __init__(self, title: str = "医保费用审判报告"):
        """
        初始化报告生成器

        Args:
            title: 报告标题
        """
        self.title = title

    def generate_json(
        self,
        result: Any,
        include_phases: bool = True,
        indent: int = 2,
    ) -> str:
        """
        生成 JSON 格式报告

        Args:
            result: 审判结果
            include_phases: 是否包含各阶段详情
            indent: 缩进空格数

        Returns:
            JSON 格式报告字符串
        """
        report_data = self._build_report_data(result, include_phases)
        return json.dumps(report_data, ensure_ascii=False, indent=indent)

    def generate_markdown(self, result: Any) -> str:
        """
        生成 Markdown 格式报告

        Args:
            result: 审判结果

        Returns:
            Markdown 格式报告字符串
        """
        lines = []

        # 标题
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 案件基本信息
        lines.append("## 案件基本信息")
        lines.append("")
        lines.append(f"| 字段 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 案件编号 | {result.case_id} |")
        lines.append(f"| 开始时间 | {result.start_time} |")
        lines.append(f"| 结束时间 | {result.end_time or '进行中'} |")
        lines.append(f"| 审判状态 | {self._format_status(result.status)} |")
        lines.append("")

        # 费用汇总
        lines.append("## 费用汇总")
        lines.append("")
        lines.append(f"| 项目 | 金额 |")
        lines.append(f"|------|------|")
        lines.append(f"| 总指控金额 | ¥{result.total_accused_amount:,.2f} |")
        lines.append(f"| 裁决核减金额 | ¥{result.ruling_amount:,.2f} |")
        lines.append("")

        # 最终裁决
        if result.final_verdict:
            lines.append("## 最终裁决")
            lines.append("")
            lines.append(f"**裁决结果**: {result.final_verdict}")
            lines.append("")
            if result.ruling_reason:
                lines.append(f"**裁决理由**: {result.ruling_reason}")
                lines.append("")

        # 费用明细
        if result.expense_items:
            lines.append("## 费用明细")
            lines.append("")
            for i, item in enumerate(result.expense_items, 1):
                name = item.get("item_name", "未知项目")
                amount = item.get("amount", 0)
                code = item.get("item_code", "-")
                lines.append(f"{i}. **{name}** (编码: {code}) - ¥{amount:,.2f}")
            lines.append("")

        # 差异明细
        if result.diff_items:
            lines.append("## 差异明细")
            lines.append("")
            for i, diff in enumerate(result.diff_items, 1):
                reason = diff.get("diff_reason", "未知原因")
                amount = diff.get("diff_amount", 0)
                lines.append(f"{i}. {reason} - ¥{amount:,.2f}")
            lines.append("")

        # 各阶段陈述
        if result.phases:
            lines.append("## 审判过程")
            lines.append("")

            for phase in result.phases:
                phase_name = self._get_phase_name(phase.phase)
                lines.append(f"### {phase_name}")
                lines.append("")
                lines.append(f"**时间**: {phase.timestamp}")
                lines.append("")

                content = phase.statement.content if phase.statement else ""
                if content:
                    # 简单格式化内容
                    for line in content.split("\n"):
                        if line.strip():
                            lines.append(line)
                else:
                    lines.append("*（无内容）*")

                if phase.error:
                    lines.append("")
                    lines.append(f"**错误**: {phase.error}")

                lines.append("")

        return "\n".join(lines)

    def generate_html(
        self,
        result: Any,
        include_styles: bool = True,
    ) -> str:
        """
        生成 HTML 格式报告

        Args:
            result: 审判结果
            include_styles: 是否包含 CSS 样式

        Returns:
            HTML 格式报告字符串
        """
        styles = ""
        if include_styles:
            styles = """
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .report {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    padding: 30px;
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }
                h2 {
                    color: #34495e;
                    margin-top: 25px;
                }
                h3 {
                    color: #7f8c8d;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }
                th, td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background: #3498db;
                    color: white;
                }
                tr:hover {
                    background: #f8f9fa;
                }
                .status {
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                .status-completed {
                    background: #d4edda;
                    color: #155724;
                }
                .status-error {
                    background: #f8d7da;
                    color: #721c24;
                }
                .status-pending {
                    background: #fff3cd;
                    color: #856404;
                }
                .amount {
                    font-weight: bold;
                    color: #e74c3c;
                }
                .verdict {
                    background: #e8f4fd;
                    padding: 15px;
                    border-left: 4px solid #3498db;
                    margin: 15px 0;
                }
                .phase {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 10px 0;
                }
                .error {
                    color: #dc3545;
                    font-weight: bold;
                }
                .footer {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #6c757d;
                    font-size: 0.9em;
                }
            </style>
            """

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            f"<meta charset='UTF-8'>",
            f"<title>{self.title}</title>",
            styles,
            "</head>",
            "<body>",
            f"<div class='report'>",
            f"<h1>{self.title}</h1>",
            f"<p><strong>生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        ]

        # 案件基本信息
        html_parts.extend([
            "<h2>案件基本信息</h2>",
            "<table>",
            f"<tr><th>字段</th><th>值</th></tr>",
            f"<tr><td>案件编号</td><td>{result.case_id}</td></tr>",
            f"<tr><td>开始时间</td><td>{result.start_time}</td></tr>",
            f"<tr><td>结束时间</td><td>{result.end_time or '进行中'}</td></tr>",
            f"<tr><td>审判状态</td><td>{self._format_status_html(result.status)}</td></tr>",
            "</table>",
        ])

        # 费用汇总
        html_parts.extend([
            "<h2>费用汇总</h2>",
            "<table>",
            "<tr><th>项目</th><th>金额</th></tr>",
            f"<tr><td>总指控金额</td><td class='amount'>¥{result.total_accused_amount:,.2f}</td></tr>",
            f"<tr><td>裁决核减金额</td><td class='amount'>¥{result.ruling_amount:,.2f}</td></tr>",
            "</table>",
        ])

        # 最终裁决
        if result.final_verdict:
            html_parts.extend([
                "<h2>最终裁决</h2>",
                f"<div class='verdict'>",
                f"<p><strong>裁决结果</strong>: {result.final_verdict}</p>",
            ])
            if result.ruling_reason:
                html_parts.append(f"<p><strong>裁决理由</strong>: {result.ruling_reason}</p>")
            html_parts.append("</div>")

        # 费用明细
        if result.expense_items:
            html_parts.append("<h2>费用明细</h2><ul>")
            for item in result.expense_items:
                name = item.get("item_name", "未知项目")
                amount = item.get("amount", 0)
                code = item.get("item_code", "-")
                html_parts.append(f"<li><strong>{name}</strong> (编码: {code}) - ¥{amount:,.2f}</li>")
            html_parts.append("</ul>")

        # 差异明细
        if result.diff_items:
            html_parts.append("<h2>差异明细</h2><ul>")
            for diff in result.diff_items:
                reason = diff.get("diff_reason", "未知原因")
                amount = diff.get("diff_amount", 0)
                html_parts.append(f"<li>{reason} - ¥{amount:,.2f}</li>")
            html_parts.append("</ul>")

        # 各阶段陈述
        if result.phases:
            html_parts.append("<h2>审判过程</h2>")
            for phase in result.phases:
                phase_name = self._get_phase_name(phase.phase)
                html_parts.append(f"<div class='phase'>")
                html_parts.append(f"<h3>{phase_name}</h3>")
                html_parts.append(f"<p><strong>时间</strong>: {phase.timestamp}</p>")

                content = phase.statement.content if phase.statement else ""
                if content:
                    # 简单格式化内容，保留换行
                    formatted_content = content.replace("\n", "<br>")
                    html_parts.append(f"<p>{formatted_content}</p>")
                else:
                    html_parts.append("<p><em>（无内容）</em></p>")

                if phase.error:
                    html_parts.append(f"<p class='error'>错误: {phase.error}</p>")

                html_parts.append("</div>")

        # 页脚
        html_parts.extend([
            "<div class='footer'>",
            f"<p>此报告由医保费用审判模拟器自动生成</p>",
            "</div>",
            "</div>",
            "</body>",
            "</html>",
        ])

        return "\n".join(html_parts)

    def _build_report_data(
        self,
        result: Any,
        include_phases: bool,
    ) -> Dict[str, Any]:
        """构建报告数据"""
        data = {
            "case_id": result.case_id,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "status": result.status,
            "total_accused_amount": result.total_accused_amount,
            "ruling_amount": result.ruling_amount,
            "final_verdict": result.final_verdict,
            "ruling_reason": result.ruling_reason,
            "expense_items": result.expense_items,
            "diff_items": result.diff_items,
            "generated_at": datetime.now().isoformat(),
        }

        if include_phases:
            data["phases"] = []
            for phase in result.phases:
                data["phases"].append({
                    "phase": phase.phase.value if hasattr(phase.phase, 'value') else str(phase.phase),
                    "timestamp": phase.timestamp,
                    "content": phase.statement.content if phase.statement else "",
                    "role": phase.statement.role.value if phase.statement and hasattr(phase.statement.role, 'value') else str(phase.statement.role) if phase.statement else "",
                    "error": phase.error,
                })

        return data

    def _format_status(self, status: str) -> str:
        """格式化状态显示"""
        status_map = {
            "completed": "已完成",
            "error": "错误",
            "pending": "进行中",
        }
        return status_map.get(status, status)

    def _format_status_html(self, status: str) -> str:
        """格式化状态为 HTML"""
        status_text = self._format_status(status)
        class_name = f"status-{status}"
        return f"<span class='status {class_name}'>{status_text}</span>"

    def _get_phase_name(self, phase: Any) -> str:
        """获取阶段名称"""
        phase_map = {
            "prosecutor": "起诉阶段",
            "defense": "辩护阶段",
            "judge": "裁决阶段",
            "initial": "初始阶段",
            "completed": "完成",
        }
        phase_val = phase.value if hasattr(phase, 'value') else str(phase)
        return phase_map.get(phase_val, phase_val)

    def save_report(
        self,
        result: Any,
        output_path: str,
        format: str = "json",
    ) -> None:
        """
        保存报告到文件

        Args:
            result: 审判结果
            output_path: 输出文件路径
            format: 报告格式 (json/markdown/html)
        """
        if format == "json":
            content = self.generate_json(result)
        elif format == "markdown" or format == "md":
            content = self.generate_markdown(result)
        elif format == "html":
            content = self.generate_html(result)
        else:
            raise ValueError(f"不支持的格式: {format}")

        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)


class BatchReportGenerator:
    """批量审判报告生成器"""

    def __init__(self, title: str = "医保费用批量审判报告"):
        """
        初始化批量报告生成器

        Args:
            title: 报告标题
        """
        self.title = title
        self.single_generator = TrialReportGenerator(title)

    def generate_summary_json(self, results: List[Any]) -> str:
        """
        生成汇总 JSON 报告

        Args:
            results: 审判结果列表

        Returns:
            JSON 格式汇总报告
        """
        summary = self._build_summary(results)
        return json.dumps(summary, ensure_ascii=False, indent=2)

    def generate_summary_markdown(self, results: List[Any]) -> str:
        """
        生成汇总 Markdown 报告

        Args:
            results: 审判结果列表

        Returns:
            Markdown 格式汇总报告
        """
        summary = self._build_summary(results)
        lines = []

        # 标题
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 汇总统计
        lines.append("## 汇总统计")
        lines.append("")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 总案件数 | {summary['total_cases']} |")
        lines.append(f"| 完成案件 | {summary['completed_cases']} |")
        lines.append(f"| 错误案件 | {summary['error_cases']} |")
        lines.append(f"| 总指控金额 | ¥{summary['total_accused_amount']:,.2f} |")
        lines.append(f"| 总核减金额 | ¥{summary['total_ruling_amount']:,.2f} |")
        lines.append("")

        # 裁决分布
        lines.append("## 裁决分布")
        lines.append("")
        for verdict, count in summary.get("verdict_distribution", {}).items():
            lines.append(f"- {verdict}: {count} 件")
        lines.append("")

        # 案件列表
        lines.append("## 案件列表")
        lines.append("")
        lines.append("| 案件编号 | 状态 | 裁决结果 | 核减金额 |")
        lines.append("|----------|------|----------|----------|")
        for result in results:
            status = self._format_status(result.status)
            verdict = result.final_verdict or "-"
            amount = f"¥{result.ruling_amount:,.2f}" if result.ruling_amount > 0 else "-"
            lines.append(f"| {result.case_id} | {status} | {verdict} | {amount} |")
        lines.append("")

        return "\n".join(lines)

    def generate_summary_html(self, results: List[Any]) -> str:
        """
        生成汇总 HTML 报告

        Args:
            results: 审判结果列表

        Returns:
            HTML 格式汇总报告
        """
        summary = self._build_summary(results)

        html = f"""
<!DOCTYPE html>
<html lang='zh-CN'>
<head>
    <meta charset='UTF-8'>
    <title>{self.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .report {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 25px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
        tr:hover {{ background: #f8f9fa; }}
        .amount {{ font-weight: bold; color: #e74c3c; }}
        .status-completed {{ background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 4px; }}
        .status-error {{ background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class='report'>
        <h1>{self.title}</h1>
        <p><strong>生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>汇总统计</h2>
        <table>
            <tr><th>指标</th><th>数值</th></tr>
            <tr><td>总案件数</td><td>{summary['total_cases']}</td></tr>
            <tr><td>完成案件</td><td>{summary['completed_cases']}</td></tr>
            <tr><td>错误案件</td><td>{summary['error_cases']}</td></tr>
            <tr><td>总指控金额</td><td class='amount'>¥{summary['total_accused_amount']:,.2f}</td></tr>
            <tr><td>总核减金额</td><td class='amount'>¥{summary['total_ruling_amount']:,.2f}</td></tr>
        </table>

        <h2>裁决分布</h2>
        <ul>
"""
        for verdict, count in summary.get("verdict_distribution", {}).items():
            html += f"            <li>{verdict}: {count} 件</li>\n"

        html += """        </ul>

        <h2>案件列表</h2>
        <table>
            <tr><th>案件编号</th><th>状态</th><th>裁决结果</th><th>核减金额</th></tr>
"""
        for result in results:
            status_class = "status-completed" if result.status == "completed" else "status-error"
            status_text = "已完成" if result.status == "completed" else "错误"
            verdict = result.final_verdict or "-"
            amount = f"¥{result.ruling_amount:,.2f}" if result.ruling_amount > 0 else "-"
            html += f"""            <tr>
                <td>{result.case_id}</td>
                <td><span class='{status_class}'>{status_text}</span></td>
                <td>{verdict}</td>
                <td>{amount}</td>
            </tr>
"""

        html += """        </table>
    </div>
</body>
</html>
"""
        return html

    def _build_summary(self, results: List[Any]) -> Dict[str, Any]:
        """构建汇总数据"""
        total_cases = len(results)
        completed_cases = sum(1 for r in results if r.status == "completed")
        error_cases = sum(1 for r in results if r.status == "error")

        total_ruling = sum(r.ruling_amount for r in results)
        total_accused = sum(r.total_accused_amount for r in results)

        verdict_counts = {}
        for r in results:
            verdict = r.final_verdict or "unknown"
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

        return {
            "total_cases": total_cases,
            "completed_cases": completed_cases,
            "error_cases": error_cases,
            "total_ruling_amount": total_ruling,
            "total_accused_amount": total_accused,
            "verdict_distribution": verdict_counts,
            "generation_time": datetime.now().isoformat(),
        }

    def _format_status(self, status: str) -> str:
        """格式化状态"""
        status_map = {
            "completed": "已完成",
            "error": "错误",
            "pending": "进行中",
        }
        return status_map.get(status, status)

    def save_summary_report(
        self,
        results: List[Any],
        output_path: str,
        format: str = "json",
    ) -> None:
        """
        保存汇总报告到文件

        Args:
            results: 审判结果列表
            output_path: 输出文件路径
            format: 报告格式 (json/markdown/html)
        """
        if format == "json":
            content = self.generate_summary_json(results)
        elif format == "markdown" or format == "md":
            content = self.generate_summary_markdown(results)
        elif format == "html":
            content = self.generate_summary_html(results)
        else:
            raise ValueError(f"不支持的格式: {format}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
