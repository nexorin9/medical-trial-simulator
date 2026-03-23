"""
Prompt 模板单元测试
"""

import pytest
from src.prompts import (
    PromptBuilder,
    get_prosecution_prompt,
    get_defense_prompt,
    get_judge_ruling_prompt,
    get_jury_verdict_prompt,
    PromptTemplate,
    EVALUATION_DIMENSIONS
)


class TestPromptBuilder:
    """测试 PromptBuilder 类"""

    def test_prompt_builder_init(self):
        """测试 PromptBuilder 初始化"""
        builder = PromptBuilder()

        assert "plaintiff" in builder.templates
        assert "defendant" in builder.templates
        assert "judge" in builder.templates
        assert "jury" in builder.templates

    def test_get_prompt_plaintiff(self):
        """测试获取原告 prompt"""
        builder = PromptBuilder()
        medical_record = "测试病历内容"

        system_prompt, user_prompt = builder.get_prompt("plaintiff", medical_record)

        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt, str)
        assert "测试病历内容" in user_prompt

    def test_get_prompt_defendant(self):
        """测试获取被告 prompt"""
        builder = PromptBuilder()
        medical_record = "测试病历"
        context = {"prosecution": "原告指控内容"}

        system_prompt, user_prompt = builder.get_prompt("defendant", medical_record, context)

        assert "测试病历" in user_prompt
        assert "原告指控内容" in user_prompt

    def test_get_prompt_judge(self):
        """测试获取法官 prompt"""
        builder = PromptBuilder()
        medical_record = "测试病历"
        context = {
            "prosecution": "指控",
            "defense": "辩护"
        }

        system_prompt, user_prompt = builder.get_prompt("judge", medical_record, context)

        assert "指控" in user_prompt
        assert "辩护" in user_prompt

    def test_get_prompt_jury(self):
        """测试获取陪审团 prompt"""
        builder = PromptBuilder()
        medical_record = "测试病历"
        context = {
            "prosecution": "指控",
            "defense": "辩护",
            "judge_ruling": "裁决"
        }

        system_prompt, user_prompt = builder.get_prompt("jury", medical_record, context)

        assert "指控" in user_prompt
        assert "辩护" in user_prompt
        assert "裁决" in user_prompt

    def test_get_prompt_invalid_role(self):
        """测试无效角色"""
        builder = PromptBuilder()

        with pytest.raises(ValueError):
            builder.get_prompt("invalid_role", "病历")

    def test_get_system_prompt(self):
        """测试获取系统提示"""
        builder = PromptBuilder()

        system_prompt = builder.get_system_prompt("plaintiff")
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0

    def test_get_user_template(self):
        """测试获取用户模板"""
        builder = PromptBuilder()

        template = builder.get_user_template("plaintiff")
        assert isinstance(template, str)
        assert "{medical_record}" in template


class TestPromptTemplates:
    """测试便捷函数"""

    def test_get_prosecution_prompt(self):
        """测试获取原告指控 prompt"""
        system_prompt, user_prompt = get_prosecution_prompt("病历内容")

        assert "病历内容" in user_prompt
        assert "原告" in system_prompt or "律师" in system_prompt

    def test_get_defense_prompt(self):
        """测试获取被告辩护 prompt"""
        system_prompt, user_prompt = get_defense_prompt("病历", "指控")

        assert "病历" in user_prompt
        assert "指控" in user_prompt
        assert "辩护" in system_prompt or "被告" in system_prompt

    def test_get_judge_ruling_prompt(self):
        """测试获取法官裁决 prompt"""
        system_prompt, user_prompt = get_judge_ruling_prompt("病历", "指控", "辩护")

        assert "病历" in user_prompt
        assert "指控" in user_prompt
        assert "辩护" in user_prompt
        assert "法官" in system_prompt or "裁决" in system_prompt

    def test_get_jury_verdict_prompt(self):
        """测试获取陪审团 prompt"""
        system_prompt, user_prompt = get_jury_verdict_prompt(
            "病历", "指控", "辩护", "裁决"
        )

        assert "病历" in user_prompt
        assert "指控" in user_prompt
        assert "辩护" in user_prompt
        assert "裁决" in user_prompt
        assert "陪审团" in system_prompt


class TestPromptTemplate:
    """测试 PromptTemplate 数据类"""

    def test_prompt_template_creation(self):
        """测试创建 PromptTemplate"""
        template = PromptTemplate(
            role="测试角色",
            system_prompt="系统提示",
            user_template="用户模板 {medical_record}",
            output_format="JSON"
        )

        assert template.role == "测试角色"
        assert template.system_prompt == "系统提示"
        assert template.output_format == "JSON"


class TestEvaluationDimensions:
    """测试评估维度定义"""

    def test_evaluation_dimensions_structure(self):
        """测试评估维度结构"""
        assert "completeness" in EVALUATION_DIMENSIONS
        assert "logical_consistency" in EVALUATION_DIMENSIONS
        assert "norm_compliance" in EVALUATION_DIMENSIONS
        assert "evidence_support" in EVALUATION_DIMENSIONS
        assert "timeline_accuracy" in EVALUATION_DIMENSIONS

    def test_evaluation_dimensions_have_name(self):
        """测试每个维度都有名称"""
        for key, value in EVALUATION_DIMENSIONS.items():
            assert "name" in value
            assert "description" in value

    def test_evaluation_dimensions_have_weights(self):
        """测试每个维度都有权重"""
        for key, value in EVALUATION_DIMENSIONS.items():
            assert "weight" in value
            assert 0 <= value["weight"] <= 1
