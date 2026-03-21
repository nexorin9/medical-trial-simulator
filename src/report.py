"""
审判报告生成器模块
将审判结果整合为结构化报告
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .trial import TrialResult, TrialPhase
from .evaluator import EvaluationResult


class TrialReport:
    """审判报告生成器"""

    def __init__(self):
        self.timestamp = datetime.now().isoformat()

    def extract_key_findings(self, result: TrialResult) -> List[str]:
        """从审判结果中提取关键发现"""
        findings = []

        # 从陪审团意见中提取关键信息
        if result.phases:
            jury_phase = result.phases[-1]
            if jury_phase.output:
                # 简单提取：取前500字符作为摘要
                output = jury_phase.output.strip()
                if len(output) > 300:
                    findings.append(output[:300] + "...")
                else:
                    findings.append(output)

        # 从法官裁决中提取
        if len(result.phases) >= 3:
            judge_phase = result.phases[2]
            if judge_phase.output:
                output = judge_phase.output.strip()
                if len(output) > 200:
                    findings.append("法官裁决: " + output[:200] + "...")
                else:
                    findings.append("法官裁决: " + output)

        return findings

    def extract_defects(self, result: TrialResult) -> List[Dict[str, str]]:
        """从原告指控中提取病历缺陷列表"""
        defects = []

        if result.phases:
            prosecution_phase = result.phases[0]
            if prosecution_phase.output:
                output = prosecution_phase.output.strip()
                # 尝试按行分割，提取可能的缺陷项
                lines = output.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                        # 清理行首标记
                        clean_line = line.lstrip('0123456789.-•) ').strip()
                        if len(clean_line) > 10:
                            defects.append({
                                "description": clean_line[:200]
                            })

        return defects[:10]  # 最多10个缺陷

    def generate_summary(self, result: TrialResult) -> str:
        """生成审判摘要"""
        summary_parts = []

        # 审判状态
        if result.success:
            summary_parts.append("审判流程已完成")
        else:
            summary_parts.append(f"审判流程异常终止: {result.error_message}")

        # 耗时
        if result.duration_seconds:
            summary_parts.append(f"总耗时: {result.duration_seconds:.2f} 秒")

        # 阶段数
        summary_parts.append(f"完成阶段数: {len(result.phases)}/4")

        return " | ".join(summary_parts)

    def get_verdict_summary(self, result: TrialResult) -> Dict[str, Any]:
        """获取判决摘要"""
        if result.phases and len(result.phases) >= 4:
            jury_phase = result.phases[3]
            judge_phase = result.phases[2]

            # 尝试判断最终立场
            output = jury_phase.output.lower()
            if "合格" in jury_phase.output or "通过" in jury_phase.output or "无异议" in jury_phase.output:
                verdict_type = "qualified"
                verdict_label = "合格"
            elif "不合格" in jury_phase.output or "不通过" in jury_phase.output or "有问题" in jury_phase.output:
                verdict_type = "unqualified"
                verdict_label = "不合格"
            else:
                verdict_type = "uncertain"
                verdict_label = "待定"

            return {
                "verdict_type": verdict_type,
                "verdict_label": verdict_label,
                "jury_opinion": jury_phase.output[:500] if jury_phase.output else "",
                "judge_ruling": judge_phase.output[:500] if judge_phase.output else ""
            }

        return {
            "verdict_type": "unknown",
            "verdict_label": "未知",
            "jury_opinion": "",
            "judge_ruling": ""
        }

    def to_dict(self, result: TrialResult) -> Dict[str, Any]:
        """转换为字典格式"""
        verdict_summary = self.get_verdict_summary(result)

        return {
            "report_metadata": {
                "generated_at": self.timestamp,
                "trial_duration_seconds": result.duration_seconds,
                "success": result.success,
                "phases_completed": len(result.phases)
            },
            "summary": self.generate_summary(result),
            "verdict": verdict_summary,
            "phases": [
                {
                    "phase_name": p.phase_name,
                    "role": p.role,
                    "output": p.output,
                    "timestamp": p.timestamp,
                    "error": p.error
                }
                for p in result.phases
            ],
            "key_findings": self.extract_key_findings(result),
            "defects": self.extract_defects(result),
            "medical_record_preview": result.medical_record[:500] + "..." if len(result.medical_record) > 500 else result.medical_record
        }

    def generate_markdown(self, result: TrialResult) -> str:
        """生成 Markdown 格式的审判报告"""
        verdict_summary = self.get_verdict_summary(result)
        phases_data = self.to_dict(result)

        lines = []

        # 标题
        lines.append("# 医疗法庭审判报告\n")
        lines.append(f"**生成时间**: {self.timestamp}")
        lines.append(f"**审判状态**: {'成功' if result.success else '失败'}")
        if result.duration_seconds:
            lines.append(f"**耗时**: {result.duration_seconds:.2f} 秒")
        lines.append("")

        # 审判结论
        lines.append("## 审判结论\n")
        verdict_emoji = "✅" if verdict_summary["verdict_type"] == "qualified" else "❌" if verdict_summary["verdict_type"] == "unqualified" else "⚠️"
        lines.append(f"{verdict_emoji} **{verdict_summary['verdict_label']}**\n")

        if verdict_summary.get("judge_ruling"):
            lines.append("### 法官裁决")
            lines.append(verdict_summary["judge_ruling"])
            lines.append("")

        if verdict_summary.get("jury_opinion"):
            lines.append("### 陪审团意见")
            lines.append(verdict_summary["jury_opinion"])
            lines.append("")

        # 审判流程
        lines.append("## 审判流程\n")
        lines.append("| 阶段 | 角色 | 状态 |")
        lines.append("|------|------|------|")

        phase_names = ["原告指控", "被告辩护", "法官裁决", "陪审团意见"]
        for i, phase in enumerate(result.phases):
            status = "✅ 完成" if not phase.error else f"❌ 失败: {phase.error}"
            lines.append(f"| {phase.phase_name} | {phase.role} | {status} |")

        lines.append("")

        # 关键发现
        if phases_data["key_findings"]:
            lines.append("## 关键发现\n")
            for i, finding in enumerate(phases_data["key_findings"], 1):
                lines.append(f"{i}. {finding}")
            lines.append("")

        # 病历缺陷
        if phases_data["defects"]:
            lines.append("## 病历缺陷清单\n")
            for i, defect in enumerate(phases_data["defects"], 1):
                lines.append(f"{i}. {defect['description']}")
            lines.append("")

        # 详细阶段内容
        lines.append("## 详细阶段内容\n")

        for phase in result.phases:
            lines.append(f"### {phase.phase_name}（{phase.role}）\n")
            if phase.error:
                lines.append(f"**错误**: {phase.error}\n")
            else:
                lines.append(phase.output)
            lines.append("")

        # 病历预览
        lines.append("## 病历预览\n")
        lines.append("```\n")
        lines.append(phases_data["medical_record_preview"])
        lines.append("```\n")

        return "\n".join(lines)

    def generate_json(self, result: TrialResult, pretty: bool = True) -> str:
        """生成 JSON 格式的审判报告"""
        data = self.to_dict(result)

        if pretty:
            return json.dumps(data, ensure_ascii=False, indent=2)
        return json.dumps(data, ensure_ascii=False)

    def generate_text(self, result: TrialResult) -> str:
        """生成纯文本格式的审判报告"""
        verdict_summary = self.get_verdict_summary(result)

        lines = []

        # 标题
        lines.append("=" * 60)
        lines.append("           医疗法庭审判报告")
        lines.append("=" * 60)
        lines.append("")

        # 基本信息
        lines.append(f"生成时间: {self.timestamp}")
        lines.append(f"审判状态: {'成功' if result.success else '失败'}")
        if result.duration_seconds:
            lines.append(f"耗时: {result.duration_seconds:.2f} 秒")
        lines.append("")

        # 审判结论
        lines.append("-" * 60)
        lines.append("审判结论")
        lines.append("-" * 60)

        verdict_emoji = "[合格]" if verdict_summary["verdict_type"] == "qualified" else "[不合格]" if verdict_summary["verdict_type"] == "unqualified" else "[待定]"
        lines.append(f"最终裁决: {verdict_emoji}")
        lines.append("")

        if verdict_summary.get("judge_ruling"):
            lines.append("法官裁决:")
            lines.append(verdict_summary["judge_ruling"])
            lines.append("")

        if verdict_summary.get("jury_opinion"):
            lines.append("陪审团意见:")
            lines.append(verdict_summary["jury_opinion"])
            lines.append("")

        # 审判流程
        lines.append("-" * 60)
        lines.append("审判流程")
        lines.append("-" * 60)

        for phase in result.phases:
            status = "✓" if not phase.error else "✗"
            lines.append(f"{status} {phase.phase_name}（{phase.role}）")
            if phase.error:
                lines.append(f"  错误: {phase.error}")

        lines.append("")

        # 病历缺陷
        defects = self.extract_defects(result)
        if defects:
            lines.append("-" * 60)
            lines.append("病历缺陷清单")
            lines.append("-" * 60)
            for i, defect in enumerate(defects, 1):
                lines.append(f"{i}. {defect['description']}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def export_to_file(
        self,
        result: TrialResult,
        output_path: str,
        format: str = "json"
    ) -> str:
        """
        导出报告到文件

        Args:
            result: 审判结果
            output_path: 输出文件路径
            format: 报告格式 ("json", "markdown", "text")

        Returns:
            实际写入的文件路径
        """
        path = Path(output_path)
        format = format.lower()

        if format == "json":
            content = self.generate_json(result)
            if not path.suffix:
                path = path.with_suffix('.json')
        elif format == "markdown" or format == "md":
            content = self.generate_markdown(result)
            if not path.suffix:
                path = path.with_suffix('.md')
        else:  # text
            content = self.generate_text(result)
            if not path.suffix:
                path = path.with_suffix('.txt')

        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(path)


def create_trial_report(result: TrialResult) -> TrialReport:
    """
    创建审判报告的便捷函数

    Args:
        result: 审判结果

    Returns:
        TrialReport 实例
    """
    report = TrialReport()
    return report


if __name__ == "__main__":
    # 测试代码
    from .trial import TrialPhase

    # 创建模拟审判结果
    mock_phases = [
        TrialPhase(
            phase_name="原告指控",
            role="原告律师",
            input_data={"medical_record": "测试病历"},
            output="1. 病历缺少既往史记录\n2. 诊断与检查结果不一致\n3. 医嘱书写不规范"
        ),
        TrialPhase(
            phase_name="被告辩护",
            role="被告（病历）",
            input_data={"medical_record": "测试病历", "prosecution": "指控"},
            output="1. 既往史已在入院记录中体现\n2. 诊断与检查结果一致\n3. 医嘱符合规范要求"
        ),
        TrialPhase(
            phase_name="法官裁决",
            role="法官",
            input_data={"medical_record": "测试病历", "prosecution": "指控", "defense": "辩护"},
            output="经审理查明，病历基本符合规范要求，但存在部分需要改进的地方。建议加强既往史的记录完整性。"
        ),
        TrialPhase(
            phase_name="陪审团意见",
            role="陪审团",
            input_data={"medical_record": "测试病历", "prosecution": "指控", "defense": "辩护", "judge_ruling": "裁决"},
            output="陪审团一致认为，该病历基本合格，但应按照法官建议改进既往史记录。综合评分：75分。"
        )
    ]

    mock_result = TrialResult(
        medical_record="患者张三，男，45岁，因胸痛入院...",
        phases=mock_phases,
        final_verdict="基本合格",
        success=True,
        duration_seconds=125.5
    )

    # 生成报告
    report = TrialReport()

    print("=== Markdown 报告 ===")
    print(report.generate_markdown(mock_result))

    print("\n=== JSON 报告 ===")
    print(report.generate_json(mock_result))

    print("\n=== 文本报告 ===")
    print(report.generate_text(mock_result))
