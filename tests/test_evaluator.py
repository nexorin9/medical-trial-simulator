"""
评估器单元测试
"""

import pytest
import json
from src.evaluator import (
    MedicalRecordEvaluator,
    EvaluationReportGenerator,
    EvaluationDimension,
    DimensionScore,
    EvaluationResult,
    get_dimension_info
)


class TestEvaluationDimension:
    """测试评估维度枚举"""

    def test_dimension_enum_values(self):
        """测试枚举值"""
        assert EvaluationDimension.COMPLETENESS.value == "completeness"
        assert EvaluationDimension.LOGICAL_CONSISTENCY.value == "logical_consistency"
        assert EvaluationDimension.SPECIFICATION_COMPLIANCE.value == "specification_compliance"
        assert EvaluationDimension.EVIDENCE_SUPPORT.value == "evidence_support"
        assert EvaluationDimension.TIMELINE_ACCURACY.value == "timeline_accuracy"


class TestDimensionScore:
    """测试 DimensionScore 数据类"""

    def test_dimension_score_creation(self):
        """测试创建评分"""
        score = DimensionScore(
            dimension="completeness",
            score=8.5,
            max_score=10.0,
            details="测试详情",
            issues=["问题1", "问题2"],
            strengths=["优点1"]
        )

        assert score.dimension == "completeness"
        assert score.score == 8.5
        assert score.max_score == 10.0
        assert len(score.issues) == 2

    def test_dimension_score_to_dict(self):
        """测试转换为字典"""
        score = DimensionScore(
            dimension="completeness",
            score=7.0,
            details="详情"
        )

        d = score.to_dict()
        assert d["dimension"] == "completeness"
        assert d["score"] == 7.0


class TestEvaluationResult:
    """测试 EvaluationResult 数据类"""

    def test_evaluation_result_creation(self):
        """测试创建评估结果"""
        scores = [
            DimensionScore(dimension="completeness", score=8.0),
            DimensionScore(dimension="logical_consistency", score=7.0)
        ]

        result = EvaluationResult(
            overall_score=7.5,
            dimension_scores=scores,
            summary="测试摘要",
            recommendations=["建议1"],
            metadata={"test": "data"}
        )

        assert result.overall_score == 7.5
        assert len(result.dimension_scores) == 2
        assert result.summary == "测试摘要"

    def test_evaluation_result_to_dict(self):
        """测试转换为字典"""
        scores = [DimensionScore(dimension="completeness", score=8.0)]
        result = EvaluationResult(
            overall_score=8.0,
            dimension_scores=scores
        )

        d = result.to_dict()
        assert "overall_score" in d
        assert "dimension_scores" in d


class TestMedicalRecordEvaluator:
    """测试 MedicalRecordEvaluator 类"""

    def test_evaluator_init(self):
        """测试评估器初始化"""
        evaluator = MedicalRecordEvaluator()

        assert len(evaluator.dimensions) == 5

    def test_dimension_weights(self):
        """测试维度权重"""
        weights = MedicalRecordEvaluator.DIMENSION_WEIGHTS

        assert EvaluationDimension.COMPLETENESS in weights
        assert EvaluationDimension.LOGICAL_CONSISTENCY in weights

        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_get_dimension_description(self):
        """测试获取维度描述"""
        evaluator = MedicalRecordEvaluator()

        desc = evaluator.get_dimension_description(EvaluationDimension.COMPLETENESS)

        assert "name" in desc
        assert "description" in desc

    def test_get_all_dimensions_description(self):
        """测试获取所有维度描述"""
        evaluator = MedicalRecordEvaluator()

        all_desc = evaluator.get_all_dimensions_description()

        assert len(all_desc) == 5
        # 返回的是以枚举为键的字典
        assert EvaluationDimension.COMPLETENESS in all_desc

    def test_create_prompt_for_dimension(self):
        """测试创建维度评估 prompt"""
        evaluator = MedicalRecordEvaluator()

        prompt = evaluator.create_prompt_for_dimension(
            "测试病历",
            EvaluationDimension.COMPLETENESS
        )

        assert "测试病历" in prompt
        assert "完整性" in prompt

    def test_parse_dimension_result_valid(self):
        """测试解析有效评估结果"""
        evaluator = MedicalRecordEvaluator()

        json_str = json.dumps({
            "dimension": "completeness",
            "score": 8.5,
            "details": "测试详情",
            "issues": ["问题1"],
            "strengths": ["优点1"]
        })

        result = evaluator.parse_dimension_result(json_str)

        assert result is not None
        assert result.score == 8.5

    def test_parse_dimension_result_invalid(self):
        """测试解析无效评估结果"""
        evaluator = MedicalRecordEvaluator()

        result = evaluator.parse_dimension_result("invalid json")
        assert result is None

    def test_parse_dimension_result_score_clamping(self):
        """测试分数范围限制"""
        evaluator = MedicalRecordEvaluator()

        # 分数超过10
        json_str = json.dumps({
            "dimension": "completeness",
            "score": 15,
            "details": "",
            "issues": [],
            "strengths": []
        })

        result = evaluator.parse_dimension_result(json_str)
        assert result.score == 10.0

        # 分数小于0
        json_str = json.dumps({
            "dimension": "completeness",
            "score": -5,
            "details": "",
            "issues": [],
            "strengths": []
        })

        result = evaluator.parse_dimension_result(json_str)
        assert result.score == 0.0

    def test_calculate_overall_score(self):
        """测试计算综合评分"""
        evaluator = MedicalRecordEvaluator()

        scores = [
            DimensionScore(dimension="completeness", score=8.0),
            DimensionScore(dimension="logical_consistency", score=6.0)
        ]

        overall = evaluator.calculate_overall_score(scores)

        assert 0 <= overall <= 10

    def test_calculate_overall_score_empty(self):
        """测试空评分列表"""
        evaluator = MedicalRecordEvaluator()

        overall = evaluator.calculate_overall_score([])
        assert overall == 0.0

    def test_generate_summary(self):
        """测试生成摘要"""
        evaluator = MedicalRecordEvaluator()

        scores = [
            DimensionScore(dimension="completeness", score=9.0),
            DimensionScore(dimension="logical_consistency", score=8.5)
        ]

        summary = evaluator.generate_summary(scores, 8.75)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_generate_recommendations(self):
        """测试生成建议"""
        evaluator = MedicalRecordEvaluator()

        scores = [
            DimensionScore(dimension="completeness", score=5.0, issues=["问题1"]),
            DimensionScore(dimension="logical_consistency", score=8.0)
        ]

        recs = evaluator.generate_recommendations(scores)

        assert isinstance(recs, list)


class TestEvaluationReportGenerator:
    """测试评估报告生成器"""

    def test_report_generator_init(self):
        """测试报告生成器初始化"""
        generator = EvaluationReportGenerator()

        assert generator.evaluator is not None

    def test_generate_text_report(self):
        """测试生成文本报告"""
        generator = EvaluationReportGenerator()

        scores = [DimensionScore(dimension="completeness", score=8.0)]
        result = EvaluationResult(
            overall_score=8.0,
            dimension_scores=scores,
            summary="测试摘要"
        )

        text = generator.generate_text_report(result)

        assert "病历质量评估报告" in text
        assert "综合评分" in text

    def test_generate_text_report_without_details(self):
        """测试不带详情的文本报告"""
        generator = EvaluationReportGenerator()

        scores = [DimensionScore(dimension="completeness", score=8.0)]
        result = EvaluationResult(
            overall_score=8.0,
            dimension_scores=scores,
            recommendations=["建议1"]
        )

        text = generator.generate_text_report(result, include_details=False)

        assert "病历质量评估报告" in text

    def test_generate_markdown_report(self):
        """测试生成 Markdown 报告"""
        generator = EvaluationReportGenerator()

        scores = [DimensionScore(dimension="completeness", score=8.0)]
        result = EvaluationResult(
            overall_score=8.0,
            dimension_scores=scores,
            summary="测试摘要"
        )

        md = generator.generate_markdown_report(result)

        assert "# 病历质量评估报告" in md

    def test_generate_json_report(self):
        """测试生成 JSON 报告"""
        generator = EvaluationReportGenerator()

        scores = [DimensionScore(dimension="completeness", score=8.0)]
        result = EvaluationResult(
            overall_score=8.0,
            dimension_scores=scores
        )

        json_str = generator.generate_json_report(result, pretty=True)

        assert "overall_score" in json_str

    def test_create_result_from_scores(self):
        """测试从评分创建结果"""
        generator = EvaluationReportGenerator()

        scores = [
            DimensionScore(dimension="completeness", score=8.0),
            DimensionScore(dimension="logical_consistency", score=7.0)
        ]

        result = generator.create_result_from_scores(scores, {"test": "meta"})

        assert result.overall_score > 0
        assert len(result.recommendations) >= 0


class TestGetDimensionInfo:
    """测试便捷函数"""

    def test_get_dimension_info(self):
        """测试获取维度信息"""
        info = get_dimension_info()

        assert isinstance(info, dict)
        assert len(info) == 5
