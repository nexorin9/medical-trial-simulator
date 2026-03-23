"""
审判流程单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.trial import (
    TrialSession,
    TrialPhase,
    TrialResult,
    run_trial
)


class TestTrialPhase:
    """测试 TrialPhase 数据类"""

    def test_trial_phase_creation(self):
        """测试创建审判阶段"""
        phase = TrialPhase(
            phase_name="原告指控",
            role="原告律师",
            input_data={"medical_record": "测试"},
            output="指控内容"
        )

        assert phase.phase_name == "原告指控"
        assert phase.role == "原告律师"
        assert phase.output == "指控内容"
        assert phase.error is None
        assert phase.timestamp is not None

    def test_trial_phase_with_error(self):
        """测试带错误的审判阶段"""
        phase = TrialPhase(
            phase_name="原告指控",
            role="原告律师",
            input_data={},
            output="",
            error="测试错误"
        )

        assert phase.error == "测试错误"


class TestTrialResult:
    """测试 TrialResult 数据类"""

    def test_trial_result_creation(self):
        """测试创建审判结果"""
        phases = [
            TrialPhase("原告指控", "律师", {}, "指控"),
            TrialPhase("被告辩护", "病历", {}, "辩护")
        ]

        result = TrialResult(
            medical_record="病历内容",
            phases=phases,
            final_verdict="合格",
            success=True,
            duration_seconds=60.0
        )

        assert result.medical_record == "病历内容"
        assert len(result.phases) == 2
        assert result.success is True
        assert result.duration_seconds == 60.0

    def test_trial_result_to_dict(self):
        """测试转换为字典"""
        phases = [TrialPhase("原告指控", "律师", {}, "指控")]
        result = TrialResult(
            medical_record="病历",
            phases=phases,
            final_verdict="合格",
            success=True
        )

        result_dict = result.to_dict()

        assert "medical_record" in result_dict
        assert "phases" in result_dict
        assert "success" in result_dict


class TestTrialSession:
    """测试 TrialSession 类"""

    def test_trial_session_init(self):
        """测试审判会话初始化"""
        mock_client = Mock()
        session = TrialSession(llm_client=mock_client, verbose=False)

        assert session.llm_client is mock_client
        assert session.verbose is False
        assert session.medical_record == ""
        assert len(session.phases) == 0

    def test_trial_session_with_prompt_builder(self):
        """测试带 PromptBuilder 的审判会话"""
        from src.prompts import PromptBuilder

        mock_client = Mock()
        builder = PromptBuilder()
        session = TrialSession(
            llm_client=mock_client,
            prompt_builder=builder,
            verbose=False
        )

        assert session.prompt_builder is builder

    def test_generate_prosecution(self):
        """测试生成原告指控"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "原告指控内容"
        mock_client.generate.return_value = mock_response

        session = TrialSession(llm_client=mock_client, verbose=False)
        phase = session.generate_prosecution("测试病历")

        assert phase.phase_name == "原告指控"
        assert phase.role == "原告律师"
        assert phase.output == "原告指控内容"
        assert len(session.phases) == 1

    def test_generate_prosecution_error_handling(self):
        """测试原告指控错误处理"""
        mock_client = Mock()
        mock_client.generate.side_effect = Exception("API Error")

        session = TrialSession(llm_client=mock_client, verbose=False)

        with pytest.raises(Exception):
            session.generate_prosecution("测试病历")

    def test_generate_defense(self):
        """测试生成被告辩护"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "被告辩护内容"
        mock_client.generate.return_value = mock_response

        session = TrialSession(llm_client=mock_client, verbose=False)
        phase = session.generate_defense("病历", "指控")

        assert phase.phase_name == "被告辩护"
        assert phase.role == "被告（病历）"
        assert phase.output == "被告辩护内容"

    def test_generate_judge_ruling(self):
        """测试生成法官裁决"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "法官裁决内容"
        mock_client.generate.return_value = mock_response

        session = TrialSession(llm_client=mock_client, verbose=False)
        phase = session.generate_judge_ruling("病历", "指控", "辩护")

        assert phase.phase_name == "法官裁决"
        assert phase.role == "法官"

    def test_generate_jury_verdict(self):
        """测试生成陪审团意见"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "陪审团意见"
        mock_client.generate.return_value = mock_response

        session = TrialSession(llm_client=mock_client, verbose=False)
        phase = session.generate_jury_verdict("病历", "指控", "辩护", "裁决")

        assert phase.phase_name == "陪审团意见"
        assert phase.role == "陪审团"

    def test_run_full_trial_success(self):
        """测试完整审判流程 - 成功"""
        mock_client = Mock()
        mock_response = Mock()

        # 模拟多个阶段的响应
        def mock_generate(prompt, system_prompt=None):
            response = Mock()
            if "指控" in prompt:
                response.content = "原告指控"
            elif "辩护" in prompt:
                response.content = "被告辩护"
            elif "裁决" in prompt:
                response.content = "法官裁决"
            else:
                response.content = "陪审团意见"
            return response

        mock_client.generate.side_effect = mock_generate

        session = TrialSession(llm_client=mock_client, verbose=False)
        result = session.run_full_trial("测试病历")

        assert result.success is True
        assert len(result.phases) == 4
        assert result.duration_seconds is not None

    def test_run_full_trial_with_stop_on_error(self):
        """测试出错时停止的审判流程"""
        mock_client = Mock()
        mock_client.generate.side_effect = Exception("API Error")

        session = TrialSession(llm_client=mock_client, verbose=False)
        result = session.run_full_trial("测试病历", stop_on_error=True)

        assert result.success is False
        assert result.error_message is not None

    def test_get_phase_output(self):
        """测试获取阶段输出"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "指控内容"
        mock_client.generate.return_value = mock_response

        session = TrialSession(llm_client=mock_client, verbose=False)
        session.generate_prosecution("病历")

        output = session.get_phase_output("原告指控")
        assert output == "指控内容"

    def test_get_phase_output_not_found(self):
        """测试获取不存在的阶段输出"""
        mock_client = Mock()
        session = TrialSession(llm_client=mock_client, verbose=False)

        output = session.get_phase_output("不存在的阶段")
        assert output is None

    def test_reset_session(self):
        """测试重置会话"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "指控"
        mock_client.generate.return_value = mock_response

        session = TrialSession(llm_client=mock_client, verbose=False)
        session.generate_prosecution("病历")

        assert len(session.phases) == 1
        session.reset()

        assert session.medical_record == ""
        assert len(session.phases) == 0


class TestRunTrial:
    """测试 run_trial 便捷函数"""

    def test_run_trial_creates_session(self):
        """测试 run_trial 创建会话"""
        mock_client = Mock()
        mock_response = Mock()

        def mock_generate(prompt, system_prompt=None):
            response = Mock()
            if "指控" in prompt:
                response.content = "原告指控"
            elif "辩护" in prompt:
                response.content = "被告辩护"
            elif "裁决" in prompt:
                response.content = "法官裁决"
            else:
                response.content = "陪审团意见"
            return response

        mock_client.generate.side_effect = mock_generate

        result = run_trial("病历内容", mock_client, verbose=False)

        assert isinstance(result, TrialResult)
        assert result.success is True
