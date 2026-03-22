"""
集成测试 - 完整审判流程

测试从费用输入到审判输出的完整流程
"""

import json
import pytest
from pathlib import Path

# 添加 src 目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prompts.base import TrialContext
from src.trial.controller import TrialController, TrialPhase


# 测试数据路径
DATA_DIR = Path(__file__).parent.parent / "data"


def load_sample_data():
    """加载示例数据"""
    # 加载费用明细
    with open(DATA_DIR / "sample_expenses.json", "r", encoding="utf-8") as f:
        expense_data = json.load(f)

    # 加载结算差异
    with open(DATA_DIR / "sample_diffs.json", "r", encoding="utf-8") as f:
        diff_data = json.load(f)

    return expense_data, diff_data


def create_trial_context(expense_data, diff_data):
    """创建审判上下文"""
    # 提取费用明细列表
    expense_items = expense_data.get("expenses", [])

    # 提取差异列表（取前3个用于测试）
    diff_items = diff_data.get("diffs", [])[:3]

    # 创建上下文
    context = TrialContext(
        expense_items=expense_items,
        diff_items=diff_items,
        medicare_catalog={},
        hospital_info=expense_data.get("hospital_info", {}),
        patient_info=expense_data.get("patient_info", {}),
        diagnosis=expense_data.get("visit_info", {}).get("diagnosis", ""),
    )

    return context


class TestDataLoading:
    """测试数据加载"""

    def test_load_sample_expenses(self):
        """测试加载费用明细"""
        expense_data, diff_data = load_sample_data()

        assert expense_data is not None
        assert "expenses" in expense_data
        assert len(expense_data["expenses"]) > 0
        assert "hospital_info" in expense_data
        assert "patient_info" in expense_data

    def test_load_sample_diffs(self):
        """测试加载结算差异"""
        expense_data, diff_data = load_sample_data()

        assert diff_data is not None
        assert "diffs" in diff_data
        assert len(diff_data["diffs"]) > 0
        assert "audit_info" in diff_data


class TestTrialContext:
    """测试审判上下文"""

    def test_create_trial_context(self):
        """测试创建审判上下文"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        assert context is not None
        assert len(context.expense_items) > 0
        assert len(context.diff_items) == 3  # 只取前3个
        assert context.hospital_info is not None
        assert context.patient_info is not None
        assert context.diagnosis != ""

    def test_trial_context_to_dict(self):
        """测试审判上下文序列化"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        context_dict = context.to_dict()

        assert "expense_items" in context_dict
        assert "diff_items" in context_dict
        assert "hospital_info" in context_dict
        assert "patient_info" in context_dict

    def test_trial_context_format_for_prompt(self):
        """测试上下文格式化"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        formatted = context.format_for_prompt()

        assert "患者信息" in formatted
        assert "诊断" in formatted
        assert "费用明细" in formatted
        assert "结算差异" in formatted


class TestTrialController:
    """测试审判控制器"""

    def test_create_trial_controller(self):
        """测试创建审判控制器"""
        controller = TrialController()

        assert controller is not None
        assert controller.prosecutor is not None
        assert controller.defense is not None
        assert controller.judge is not None

    def test_run_trial_without_llm(self):
        """测试无 LLM 情况下的审判流程"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        controller = TrialController()
        result = controller.run_trial(context, case_id="test_case_001")

        assert result is not None
        assert result.case_id == "test_case_001"
        assert result.start_time is not None
        assert result.status in ["completed", "error"]
        assert len(result.phases) > 0

    def test_trial_phases(self):
        """测试审判各阶段"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        controller = TrialController()
        result = controller.run_trial(context)

        # 验证各阶段都已执行
        phases = [p.phase for p in result.phases]
        assert TrialPhase.PROSECUTOR in phases
        assert TrialPhase.DEFENSE in phases
        assert TrialPhase.JUDGE in phases

    def test_trial_result_structure(self):
        """测试审判结果结构"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        controller = TrialController()
        result = controller.run_trial(context)

        # 验证结果包含所有必要字段
        assert hasattr(result, "case_id")
        assert hasattr(result, "start_time")
        assert hasattr(result, "end_time")
        assert hasattr(result, "status")
        assert hasattr(result, "phases")
        assert hasattr(result, "expense_items")
        assert hasattr(result, "diff_items")

    def test_trial_result_to_dict(self):
        """测试审判结果序列化"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        controller = TrialController()
        result = controller.run_trial(context)

        result_dict = result.to_dict()

        assert "case_id" in result_dict
        assert "start_time" in result_dict
        assert "status" in result_dict
        assert "phases" in result_dict

    def test_trial_result_to_json(self):
        """测试审判结果 JSON 序列化"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        controller = TrialController()
        result = controller.run_trial(context)

        result_json = result.to_json()

        assert result_json is not None
        assert isinstance(result_json, str)

        # 验证可以解析为 JSON
        parsed = json.loads(result_json)
        assert "case_id" in parsed
        assert "phases" in parsed

    def test_extract_verdict(self):
        """测试裁决结果提取"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        controller = TrialController()
        result = controller.run_trial(context)

        # 验证裁决结果存在
        assert result.final_verdict is not None
        assert result.ruling_amount is not None

    def test_batch_trial(self):
        """测试批量审判"""
        expense_data, diff_data = load_sample_data()

        # 创建多个上下文
        contexts = []
        for i in range(3):
            context = create_trial_context(expense_data, diff_data)
            contexts.append(context)

        controller = TrialController()
        results = controller.run_trial_batch(contexts, case_prefix="batch")

        assert len(results) == 3
        assert results[0].case_id == "batch_1"
        assert results[1].case_id == "batch_2"
        assert results[2].case_id == "batch_3"

    def test_trial_summary(self):
        """测试审判汇总"""
        expense_data, diff_data = load_sample_data()

        contexts = []
        for i in range(3):
            context = create_trial_context(expense_data, diff_data)
            contexts.append(context)

        controller = TrialController()
        results = controller.run_trial_batch(contexts)

        summary = controller.generate_trial_summary(results)

        assert summary is not None
        assert summary["total_cases"] == 3
        assert summary["completed_cases"] >= 0
        assert "generation_time" in summary


class TestOutputFormat:
    """测试输出格式"""

    def test_json_output_format(self):
        """测试 JSON 输出格式"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        controller = TrialController()
        result = controller.run_trial(context)

        # 验证 JSON 输出格式正确
        result_json = result.to_json()
        parsed = json.loads(result_json)

        # 验证关键字段存在
        assert "case_id" in parsed
        assert "start_time" in parsed
        assert "end_time" in parsed
        assert "status" in parsed
        assert "phases" in parsed
        assert "expense_items" in parsed
        assert "diff_items" in parsed

    def test_phase_structure(self):
        """测试阶段结构"""
        expense_data, diff_data = load_sample_data()
        context = create_trial_context(expense_data, diff_data)

        controller = TrialController()
        result = controller.run_trial(context)

        # 验证每个阶段的结构
        for phase_result in result.phases:
            assert phase_result.phase is not None
            assert phase_result.statement is not None
            assert phase_result.timestamp is not None
            # error 字段可以不存在或为 None
            assert "role" in phase_result.statement.to_dict()
            assert "content" in phase_result.statement.to_dict()


class TestErrorHandling:
    """测试错误处理"""

    def test_empty_context(self):
        """测试空上下文"""
        context = TrialContext(
            expense_items=[],
            diff_items=[],
        )

        controller = TrialController()
        result = controller.run_trial(context)

        # 空上下文也应该能运行
        assert result is not None
        assert result.case_id is not None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
