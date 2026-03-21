"""
审判流程核心模块

实现完整的审判流程：原告指控 → 被告辩护 → 法官裁决 → 陪审团意见
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

from .llm_client import LLMClient, LLMResponse
from .prompts import (
    get_prosecution_prompt,
    get_defense_prompt,
    get_judge_ruling_prompt,
    get_jury_verdict_prompt,
    PromptBuilder
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrialPhase:
    """审判阶段数据类"""
    phase_name: str
    role: str
    input_data: Dict[str, str]
    output: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


@dataclass
class TrialResult:
    """审判结果数据类"""
    medical_record: str
    phases: List[TrialPhase]
    final_verdict: str
    success: bool
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "medical_record": self.medical_record,
            "phases": [
                {
                    "phase_name": p.phase_name,
                    "role": p.role,
                    "input_data": p.input_data,
                    "output": p.output,
                    "timestamp": p.timestamp,
                    "error": p.error
                }
                for p in self.phases
            ],
            "final_verdict": self.final_verdict,
            "success": self.success,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds
        }


class TrialSession:
    """审判会话管理类"""

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: Optional[PromptBuilder] = None,
        verbose: bool = True
    ):
        """
        初始化审判会话

        Args:
            llm_client: LLM 客户端实例
            prompt_builder: Prompt 构建器（可选）
            verbose: 是否输出详细日志
        """
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.verbose = verbose
        self.medical_record: str = ""
        self.phases: List[TrialPhase] = []
        self._start_time: Optional[datetime] = None

    def _log(self, message: str):
        """输出日志"""
        if self.verbose:
            logger.info(message)
            print(f"[审判] {message}")

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        phase_name: str
    ) -> str:
        """
        调用 LLM 并处理响应

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            phase_name: 阶段名称

        Returns:
            LLM 响应内容

        Raises:
            Exception: 调用失败时抛出
        """
        try:
            response = self.llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            return response.content
        except Exception as e:
            self._log(f"调用 LLM 失败 ({phase_name}): {str(e)}")
            raise

    def generate_prosecution(self, medical_record: str) -> TrialPhase:
        """
        生成原告指控

        Args:
            medical_record: 病历内容

        Returns:
            TrialPhase 对象
        """
        self._log("阶段 1/4: 原告律师指控...")
        self.medical_record = medical_record

        system_prompt, user_prompt = get_prosecution_prompt(medical_record)

        try:
            output = self._call_llm(system_prompt, user_prompt, "原告指控")
            phase = TrialPhase(
                phase_name="原告指控",
                role="原告律师",
                input_data={"medical_record": medical_record},
                output=output
            )
            self.phases.append(phase)
            self._log("原告指控完成")
            return phase
        except Exception as e:
            phase = TrialPhase(
                phase_name="原告指控",
                role="原告律师",
                input_data={"medical_record": medical_record},
                output="",
                error=str(e)
            )
            self.phases.append(phase)
            raise

    def generate_defense(self, medical_record: str, prosecution: str) -> TrialPhase:
        """
        生成被告辩护

        Args:
            medical_record: 病历内容
            prosecution: 原告指控

        Returns:
            TrialPhase 对象
        """
        self._log("阶段 2/4: 被告辩护...")

        system_prompt, user_prompt = get_defense_prompt(medical_record, prosecution)

        try:
            output = self._call_llm(system_prompt, user_prompt, "被告辩护")
            phase = TrialPhase(
                phase_name="被告辩护",
                role="被告（病历）",
                input_data={
                    "medical_record": medical_record,
                    "prosecution": prosecution
                },
                output=output
            )
            self.phases.append(phase)
            self._log("被告辩护完成")
            return phase
        except Exception as e:
            phase = TrialPhase(
                phase_name="被告辩护",
                role="被告（病历）",
                input_data={
                    "medical_record": medical_record,
                    "prosecution": prosecution
                },
                output="",
                error=str(e)
            )
            self.phases.append(phase)
            raise

    def generate_judge_ruling(
        self,
        medical_record: str,
        prosecution: str,
        defense: str
    ) -> TrialPhase:
        """
        生成法官裁决

        Args:
            medical_record: 病历内容
            prosecution: 原告指控
            defense: 被告辩护

        Returns:
            TrialPhase 对象
        """
        self._log("阶段 3/4: 法官裁决...")

        system_prompt, user_prompt = get_judge_ruling_prompt(
            medical_record, prosecution, defense
        )

        try:
            output = self._call_llm(system_prompt, user_prompt, "法官裁决")
            phase = TrialPhase(
                phase_name="法官裁决",
                role="法官",
                input_data={
                    "medical_record": medical_record,
                    "prosecution": prosecution,
                    "defense": defense
                },
                output=output
            )
            self.phases.append(phase)
            self._log("法官裁决完成")
            return phase
        except Exception as e:
            phase = TrialPhase(
                phase_name="法官裁决",
                role="法官",
                input_data={
                    "medical_record": medical_record,
                    "prosecution": prosecution,
                    "defense": defense
                },
                output="",
                error=str(e)
            )
            self.phases.append(phase)
            raise

    def generate_jury_verdict(
        self,
        medical_record: str,
        prosecution: str,
        defense: str,
        judge_ruling: str
    ) -> TrialPhase:
        """
        生成陪审团意见

        Args:
            medical_record: 病历内容
            prosecution: 原告指控
            defense: 被告辩护
            judge_ruling: 法官裁决

        Returns:
            TrialPhase 对象
        """
        self._log("阶段 4/4: 陪审团综合意见...")

        system_prompt, user_prompt = get_jury_verdict_prompt(
            medical_record, prosecution, defense, judge_ruling
        )

        try:
            output = self._call_llm(system_prompt, user_prompt, "陪审团意见")
            phase = TrialPhase(
                phase_name="陪审团意见",
                role="陪审团",
                input_data={
                    "medical_record": medical_record,
                    "prosecution": prosecution,
                    "defense": defense,
                    "judge_ruling": judge_ruling
                },
                output=output
            )
            self.phases.append(phase)
            self._log("陪审团意见完成")
            return phase
        except Exception as e:
            phase = TrialPhase(
                phase_name="陪审团意见",
                role="陪审团",
                input_data={
                    "medical_record": medical_record,
                    "prosecution": prosecution,
                    "defense": defense,
                    "judge_ruling": judge_ruling
                },
                output="",
                error=str(e)
            )
            self.phases.append(phase)
            raise

    def run_full_trial(
        self,
        medical_record: str,
        stop_on_error: bool = True
    ) -> TrialResult:
        """
        运行完整审判流程

        Args:
            medical_record: 病历内容
            stop_on_error: 是否在出错时停止

        Returns:
            TrialResult 对象
        """
        self._start_time = datetime.now()
        self._log("=" * 50)
        self._log("医疗法庭审判开始")
        self._log("=" * 50)

        error_message: Optional[str] = None

        try:
            # 阶段 1: 原告指控
            prosecution_phase = self.generate_prosecution(medical_record)
            if prosecution_phase.error and stop_on_error:
                raise Exception(prosecution_phase.error)

            # 阶段 2: 被告辩护
            defense_phase = self.generate_defense(
                medical_record,
                prosecution_phase.output
            )
            if defense_phase.error and stop_on_error:
                raise Exception(defense_phase.error)

            # 阶段 3: 法官裁决
            judge_phase = self.generate_judge_ruling(
                medical_record,
                prosecution_phase.output,
                defense_phase.output
            )
            if judge_phase.error and stop_on_error:
                raise Exception(judge_phase.error)

            # 阶段 4: 陪审团意见
            jury_phase = self.generate_jury_verdict(
                medical_record,
                prosecution_phase.output,
                defense_phase.output,
                judge_phase.output
            )
            if jury_phase.error and stop_on_error:
                raise Exception(jury_phase.error)

            # 计算耗时
            duration = (datetime.now() - self._start_time).total_seconds()

            result = TrialResult(
                medical_record=medical_record,
                phases=self.phases,
                final_verdict=jury_phase.output,
                success=True,
                duration_seconds=duration
            )

            self._log("=" * 50)
            self._log(f"审判完成！耗时: {duration:.2f} 秒")
            self._log("=" * 50)

            return result

        except Exception as e:
            duration = (datetime.now() - self._start_time).total_seconds() if self._start_time else None
            error_message = str(e)

            result = TrialResult(
                medical_record=medical_record,
                phases=self.phases,
                final_verdict="",
                success=False,
                error_message=error_message,
                duration_seconds=duration
            )

            self._log(f"审判失败: {error_message}")
            return result

    def get_phase_output(self, phase_name: str) -> Optional[str]:
        """获取指定阶段的输出"""
        for phase in self.phases:
            if phase.phase_name == phase_name:
                return phase.output
        return None

    def reset(self):
        """重置会话"""
        self.medical_record = ""
        self.phases = []
        self._start_time = None


# 便捷函数
def run_trial(
    medical_record: str,
    llm_client: LLMClient,
    verbose: bool = True
) -> TrialResult:
    """
    运行完整审判流程的便捷函数

    Args:
        medical_record: 病历内容
        llm_client: LLM 客户端实例
        verbose: 是否输出详细日志

    Returns:
        TrialResult 对象
    """
    session = TrialSession(llm_client=llm_client, verbose=verbose)
    return session.run_full_trial(medical_record)
