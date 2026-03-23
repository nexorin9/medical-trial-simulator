"""
审判报告单元测试
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.report import TrialReport, create_trial_report
from src.trial import TrialPhase, TrialResult


class TestTrialReport:
    """测试 TrialReport 类"""

    def create_mock_trial_result(self, success=True):
        """创建模拟审判结果"""
        phases = [
            TrialPhase(
                phase_name="原告指控",
                role="原告律师",
                input_data={"medical_record": "测试病历"},
                output="1. 病历缺少既往史\n2. 诊断不明确"
            ),
            TrialPhase(
                phase_name="被告辩护",
                role="被告（病历）",
                input_data={"medical_record": "测试病历", "prosecution": "指控"},
                output="1. 既往史已在入院记录体现\n2. 诊断明确"
            ),
            TrialPhase(
                phase_name="法官裁决",
                role="法官",
                input_data={"medical_record": "测试病历"},
                output="病历基本合格，建议改进"
            ),
            TrialPhase(
                phase_name="陪审团意见",
                role="陪审团",
                input_data={"medical_record": "测试病历"},
                output="综合评分80分，病历合格"
            )
        ]

        return TrialResult(
            medical_record="患者张三，男，45岁，因胸痛入院...",
            phases=phases,
            final_verdict="合格",
            success=success,
            duration_seconds=120.5 if success else None,
            error_message=None if success else "测试错误"
        )

    def test_trial_report_init(self):
        """测试审判报告初始化"""
        report = TrialReport()
        assert report.timestamp is not None

    def test_extract_key_findings(self):
        """测试提取关键发现"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        findings = report.extract_key_findings(result)

        assert len(findings) > 0

    def test_extract_defects(self):
        """测试提取病历缺陷"""
        report = TrialReport()

        # 创建符合格式的指控输出（需要长度>10）
        phases = [
            TrialPhase(
                phase_name="原告指控",
                role="原告律师",
                input_data={"medical_record": "测试病历"},
                output="1. 病历缺少既往史记录内容\n2. 诊断与检查结果存在不一致情况\n3. 医嘱书写不符合规范要求"
            )
        ]
        result = TrialResult(
            medical_record="测试",
            phases=phases,
            final_verdict="",
            success=True
        )

        defects = report.extract_defects(result)

        assert isinstance(defects, list)
        assert len(defects) > 0

    def test_generate_summary_success(self):
        """测试生成成功摘要"""
        report = TrialReport()
        result = self.create_mock_trial_result(success=True)

        summary = report.generate_summary(result)

        assert "完成" in summary
        assert "120.5" in summary or "120" in summary

    def test_generate_summary_failure(self):
        """测试生成失败摘要"""
        report = TrialReport()
        result = self.create_mock_trial_result(success=False)

        summary = report.generate_summary(result)

        assert "异常" in summary or "错误" in summary

    def test_get_verdict_summary_qualified(self):
        """测试获取合格判决"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        verdict = report.get_verdict_summary(result)

        assert "verdict_type" in verdict
        assert "verdict_label" in verdict

    def test_to_dict(self):
        """测试转换为字典"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        data = report.to_dict(result)

        assert "report_metadata" in data
        assert "summary" in data
        assert "verdict" in data
        assert "phases" in data

    def test_generate_markdown(self):
        """测试生成 Markdown 报告"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        md = report.generate_markdown(result)

        assert "# 医疗法庭审判报告" in md
        assert "审判结论" in md
        assert "审判流程" in md

    def test_generate_json(self):
        """测试生成 JSON 报告"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        json_str = report.generate_json(result)
        data = json.loads(json_str)

        assert "report_metadata" in data
        assert "summary" in data

    def test_generate_json_pretty(self):
        """测试美化 JSON 输出"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        pretty_json = report.generate_json(result, pretty=True)
        plain_json = report.generate_json(result, pretty=False)

        assert len(pretty_json) > len(plain_json)

    def test_generate_text(self):
        """测试生成纯文本报告"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        text = report.generate_text(result)

        assert "医疗法庭审判报告" in text
        assert "审判结论" in text or "审判" in text

    def test_export_to_file_json(self):
        """测试导出 JSON 文件"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            actual_path = report.export_to_file(result, str(output_path), "json")

            assert Path(actual_path).exists()
            content = Path(actual_path).read_text(encoding="utf-8")
            data = json.loads(content)
            assert "report_metadata" in data

    def test_export_to_file_markdown(self):
        """测试导出 Markdown 文件"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report"
            actual_path = report.export_to_file(result, str(output_path), "markdown")

            assert Path(actual_path).exists()
            content = Path(actual_path).read_text(encoding="utf-8")
            assert "# 医疗法庭审判报告" in content

    def test_export_to_file_text(self):
        """测试导出文本文件"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report"
            actual_path = report.export_to_file(result, str(output_path), "text")

            assert Path(actual_path).exists()
            assert ".txt" in actual_path

    def test_export_creates_parent_dirs(self):
        """测试导出时创建父目录"""
        report = TrialReport()
        result = self.create_mock_trial_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test_report.json"
            actual_path = report.export_to_file(result, str(output_path), "json")

            assert Path(actual_path).exists()
            assert Path(actual_path).parent.exists()

    def test_create_trial_report_function(self):
        """测试便捷函数创建报告"""
        result = self.create_mock_trial_result()
        report = create_trial_report(result)

        assert isinstance(report, TrialReport)


class TestTrialReportEdgeCases:
    """测试边界情况"""

    def test_empty_phases(self):
        """测试空阶段列表"""
        report = TrialReport()
        result = TrialResult(
            medical_record="病历",
            phases=[],
            final_verdict="",
            success=False
        )

        verdict = report.get_verdict_summary(result)
        assert verdict["verdict_type"] == "unknown"

    def test_incomplete_phases(self):
        """测试不完整阶段"""
        report = TrialReport()
        phases = [
            TrialPhase("原告指控", "律师", {}, "指控")
        ]
        result = TrialResult(
            medical_record="病历",
            phases=phases,
            final_verdict="",
            success=True
        )

        verdict = report.get_verdict_summary(result)
        assert verdict["verdict_type"] == "unknown"

    def test_defects_with_different_formats(self):
        """测试不同格式的缺陷提取"""
        report = TrialReport()
        phases = [
            TrialPhase(
                phase_name="原告指控",
                role="原告律师",
                input_data={},
                output="1. 第一项缺陷\n2. 第二项缺陷\n- 第三项\n• 第四项"
            )
        ]
        result = TrialResult(
            medical_record="病历",
            phases=phases,
            final_verdict="",
            success=True
        )

        defects = report.extract_defects(result)
        assert isinstance(defects, list)
