"""
审判流程控制器

整合起诉、辩护、法官三个角色，实现完整审判流程
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Callable

from ..prompts.base import TrialContext, TrialStatement, TrialRole
from ..prompts.prosecutor import ProsecutorPrompt
from ..prompts.defense import DefensePrompt
from ..prompts.judge import JudgePrompt
from ..utils.logging_config import get_logger, TrialLogger
from ..utils.exceptions import LLMCallError, TrialPhaseError

# 获取日志记录器
_logger = get_logger("medical_trial.controller")


class TrialPhase(Enum):
    """审判阶段"""
    INITIAL = "initial"           # 初始状态
    PROSECUTOR = "prosecutor"     # 起诉阶段
    DEFENSE = "defense"           # 辩护阶段
    JUDGE = "judge"               # 裁决阶段
    COMPLETED = "completed"       # 完成


@dataclass
class PhaseResult:
    """阶段结果"""
    phase: TrialPhase
    statement: TrialStatement
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


@dataclass
class TrialResult:
    """审判结果"""
    # 基本信息
    case_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "pending"

    # 阶段结果
    phases: List[PhaseResult] = field(default_factory=list)

    # 费用信息
    expense_items: List[Dict[str, Any]] = field(default_factory=list)
    diff_items: List[Dict[str, Any]] = field(default_factory=list)

    # 最终裁决
    final_verdict: Optional[str] = None
    ruling_amount: float = 0.0
    ruling_reason: Optional[str] = None

    # 统计信息
    total_accused_amount: float = 0.0
    total_defense_responses: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "case_id": self.case_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "phases": [
                {
                    "phase": p.phase.value,
                    "statement": p.statement.to_dict(),
                    "timestamp": p.timestamp,
                    "error": p.error,
                }
                for p in self.phases
            ],
            "expense_items": self.expense_items,
            "diff_items": self.diff_items,
            "final_verdict": self.final_verdict,
            "ruling_amount": self.ruling_amount,
            "ruling_reason": self.ruling_reason,
            "total_accused_amount": self.total_accused_amount,
            "total_defense_responses": self.total_defense_responses,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def get_phase_result(self, phase: TrialPhase) -> Optional[PhaseResult]:
        """获取指定阶段的结果"""
        for p in self.phases:
            if p.phase == phase:
                return p
        return None


class TrialController:
    """
    审判流程控制器

    负责协调起诉方、辩护方、法官三个角色，
    实现完整的审判流程：起诉 → 辩护 → 裁决
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        callback: Optional[Callable[[str, TrialPhase], None]] = None,
        max_retries: int = 3,
    ):
        """
        初始化审判控制器

        Args:
            llm_client: LLM 客户端（用于调用 AI 生成内容）
            callback: 回调函数，用于通知进度
            max_retries: LLM 调用最大重试次数
        """
        self.llm_client = llm_client
        self.callback = callback
        self.max_retries = max_retries

        # 初始化各角色
        self.prosecutor = ProsecutorPrompt()
        self.defense = DefensePrompt()
        self.judge = JudgePrompt()

        # 初始化日志记录器
        self.trial_logger = TrialLogger("medical_trial.trial")

    def _notify_progress(self, message: str, phase: TrialPhase):
        """通知进度"""
        if self.callback:
            self.callback(message, phase)

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        调用 LLM 生成内容（带重试机制）

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示

        Returns:
            生成的内容
        """
        if self.llm_client is None:
            # 如果没有 LLM 客户端，返回模拟响应
            _logger.debug("使用模拟响应（无 LLM 客户端）")
            return self._generate_mock_response(system_prompt, user_prompt)

        # 带重试的 LLM 调用
        last_error = None
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                response = self.llm_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                latency = time.time() - start_time

                # 记录成功的 LLM 调用
                provider = getattr(self.llm_client, 'provider', 'unknown')
                model = getattr(self.llm_client, 'model', 'unknown')
                self.trial_logger.log_llm_call(provider, model, latency, success=True)
                _logger.info(f"LLM 调用成功 - 提供商: {provider}, 模型: {model}, 延迟: {latency:.2f}s")

                return response

            except Exception as e:
                last_error = e
                _logger.warning(f"LLM 调用失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                self.trial_logger.log_retry(attempt + 1, self.max_retries, str(e))

                if attempt < self.max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    _logger.info(f"等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)

        # 所有重试都失败
        error_msg = f"LLM 调用失败（已重试 {self.max_retries} 次）: {str(last_error)}"
        _logger.error(error_msg)

        # 记录失败的 LLM 调用
        provider = getattr(self.llm_client, 'provider', 'unknown')
        model = getattr(self.llm_client, 'model', 'unknown')
        self.trial_logger.log_llm_call(provider, model, 0, success=False)

        return f"LLM 调用失败: {str(last_error)}"

    def _generate_mock_response(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """生成模拟响应（用于测试）"""
        if "起诉" in system_prompt or "prosecutor" in system_prompt.lower():
            return self._generate_mock_prosecutor_response(user_prompt)
        elif "辩护" in system_prompt or "defense" in system_prompt.lower():
            return self._generate_mock_defense_response(user_prompt)
        elif "法官" in system_prompt or "judge" in system_prompt.lower():
            return self._generate_mock_judge_response(user_prompt)
        return "模拟响应内容"

    def _generate_mock_prosecutor_response(self, user_prompt: str) -> str:
        """生成模拟起诉响应"""
        return """### 【起诉状】

#### 一、案件概况
经审查，发现以下费用存在问题，需要进一步核实。

#### 二、违规事项
1. **超标准收费**：部分诊疗项目收费超过医保目录定价
2. **目录匹配问题**：个别项目编码与医保目录不完全匹配
3. **数量异常**：部分项目用量需要进一步核实

#### 三、结论
建议医院提供相关说明材料，进一步核实费用合理性。
"""

    def _generate_mock_defense_response(self, user_prompt: str) -> str:
        """生成模拟辩护响应"""
        return """### 【辩护词】

#### 一、案件概况
针对医保审核提出的问题，医院现进行说明和辩护。

#### 二、辩护事项
1. **价格说明**：所有收费均符合当地医疗服务价格政策
2. **目录符合**：所有项目均在医保目录内，编码已正确匹配
3. **数量合理**：用量基于患者病情需要，符合诊疗规范

#### 三、总结
费用产生具有合理的临床依据，符合医保政策要求。
"""

    def _generate_mock_judge_response(self, user_prompt: str) -> str:
        """生成模拟法官响应"""
        return """### 【裁决书】

#### 一、案件概述
本案涉及医保费用审核争议，起诉方提出多项指控，辩护方进行了说明。

#### 二、双方陈述要点
起诉方（医保审核）：提出了超标准收费、目录匹配等质疑
辩护方（医院）：提供了价格政策文件、目录匹配说明等依据

#### 三、审理查明
经审查，双方提供的材料基本充分，费用产生有一定的合理性依据。

#### 四、本院认为
医院提供的辩护依据基本成立，费用具有一定的合理性。

#### 五、裁决结果
**裁决：部分支持辩护**
- 最终认定金额：按原始申报金额的 80% 核减
- 核减金额：¥XX.XX
- 裁决理由：双方均有合理之处，建议协商解决
"""

    def run_trial(
        self,
        context: TrialContext,
        case_id: Optional[str] = None,
    ) -> TrialResult:
        """
        运行完整审判流程

        Args:
            context: 审判上下文
            case_id: 案件 ID（可选）

        Returns:
            审判结果
        """
        # 初始化结果
        case_id = case_id or f"case_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        result = TrialResult(
            case_id=case_id,
            start_time=datetime.now().isoformat(),
            expense_items=context.expense_items,
            diff_items=context.diff_items,
        )

        # 设置日志记录器的案件 ID
        self.trial_logger.set_case_id(case_id)
        _logger.info(f"开始审判 - 案件ID: {case_id}")

        # 阶段 1: 起诉
        self._notify_progress("开始起诉阶段...", TrialPhase.PROSECUTOR)
        self.trial_logger.log_phase_start("prosecutor")
        prosecutor_result = self._run_prosecutor_phase(context)
        result.phases.append(prosecutor_result)

        if prosecutor_result.error:
            result.status = "error"
            result.end_time = datetime.now().isoformat()
            self.trial_logger.log_phase_end("prosecutor", success=False)
            self.trial_logger.log_error(Exception(prosecutor_result.error), "起诉阶段")
            _logger.error(f"起诉阶段失败 - 案件ID: {case_id}, 错误: {prosecutor_result.error}")
            return result

        self.trial_logger.log_phase_end("prosecutor", success=True)
        _logger.info(f"起诉阶段完成 - 案件ID: {case_id}")

        # 更新上下文，添加起诉陈述
        context.previous_statements.append(prosecutor_result.statement)

        # 阶段 2: 辩护
        self._notify_progress("开始辩护阶段...", TrialPhase.DEFENSE)
        self.trial_logger.log_phase_start("defense")
        defense_result = self._run_defense_phase(context)
        result.phases.append(defense_result)
        result.total_defense_responses = len(result.phases)

        if defense_result.error:
            result.status = "error"
            result.end_time = datetime.now().isoformat()
            self.trial_logger.log_phase_end("defense", success=False)
            self.trial_logger.log_error(Exception(defense_result.error), "辩护阶段")
            _logger.error(f"辩护阶段失败 - 案件ID: {case_id}, 错误: {defense_result.error}")
            return result

        self.trial_logger.log_phase_end("defense", success=True)
        _logger.info(f"辩护阶段完成 - 案件ID: {case_id}")

        # 更新上下文，添加辩护陈述
        context.previous_statements.append(defense_result.statement)

        # 阶段 3: 法官裁决
        self._notify_progress("开始裁决阶段...", TrialPhase.JUDGE)
        self.trial_logger.log_phase_start("judge")
        judge_result = self._run_judge_phase(context)
        result.phases.append(judge_result)

        if judge_result.error:
            result.status = "error"
            result.end_time = datetime.now().isoformat()
            self.trial_logger.log_phase_end("judge", success=False)
            self.trial_logger.log_error(Exception(judge_result.error), "裁决阶段")
            _logger.error(f"裁决阶段失败 - 案件ID: {case_id}, 错误: {judge_result.error}")
            return result

        self.trial_logger.log_phase_end("judge", success=True)
        _logger.info(f"裁决阶段完成 - 案件ID: {case_id}")

        # 提取最终裁决
        result.final_verdict = self._extract_verdict(judge_result.statement.content)
        result.ruling_amount = self._extract_ruling_amount(judge_result.statement.content)
        result.ruling_reason = self._extract_ruling_reason(judge_result.statement.content)
        result.total_accused_amount = self._calculate_accused_amount(context)

        # 完成
        result.status = "completed"
        result.end_time = datetime.now().isoformat()
        self._notify_progress("审判完成", TrialPhase.COMPLETED)

        # 记录审判完成
        self.trial_logger.log_trial_complete(result.status, result.final_verdict)
        _logger.info(f"审判完成 - 案件ID: {case_id}, 状态: {result.status}, 裁决: {result.final_verdict}")

        return result

    def _run_prosecutor_phase(self, context: TrialContext) -> PhaseResult:
        """执行起诉阶段"""
        try:
            system_prompt = self.prosecutor.get_system_prompt()
            user_prompt = self.prosecutor.build_user_prompt(context)

            # 调用 LLM 生成起诉状
            content = self._call_llm(system_prompt, user_prompt)

            # 解析响应
            statement = self.prosecutor.parse_response(content)

            return PhaseResult(
                phase=TrialPhase.PROSECUTOR,
                statement=statement,
            )
        except Exception as e:
            return PhaseResult(
                phase=TrialPhase.PROSECUTOR,
                statement=TrialStatement(role=TrialRole.PROSECUTOR, content=""),
                error=str(e),
            )

    def _run_defense_phase(self, context: TrialContext) -> PhaseResult:
        """执行辩护阶段"""
        try:
            system_prompt = self.defense.get_system_prompt()
            user_prompt = self.defense.build_user_prompt(context)

            # 调用 LLM 生成辩护词
            content = self._call_llm(system_prompt, user_prompt)

            # 解析响应
            statement = self.defense.parse_response(content)

            return PhaseResult(
                phase=TrialPhase.DEFENSE,
                statement=statement,
            )
        except Exception as e:
            return PhaseResult(
                phase=TrialPhase.DEFENSE,
                statement=TrialStatement(role=TrialRole.DEFENSE, content=""),
                error=str(e),
            )

    def _run_judge_phase(self, context: TrialContext) -> PhaseResult:
        """执行法官裁决阶段"""
        try:
            system_prompt = self.judge.get_system_prompt()
            user_prompt = self.judge.build_user_prompt(context)

            # 调用 LLM 生成裁决书
            content = self._call_llm(system_prompt, user_prompt)

            # 解析响应
            statement = self.judge.parse_response(content)

            return PhaseResult(
                phase=TrialPhase.JUDGE,
                statement=statement,
            )
        except Exception as e:
            return PhaseResult(
                phase=TrialPhase.JUDGE,
                statement=TrialStatement(role=TrialRole.JUDGE, content=""),
                error=str(e),
            )

    def _extract_verdict(self, content: str) -> str:
        """从裁决内容中提取裁决结果"""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "裁决" in line or "判决" in line or "本院认为" in line:
                # 尝试获取后续几行作为裁决
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        return "待定"

    def _extract_ruling_amount(self, content: str) -> float:
        """从裁决内容中提取核减金额"""
        import re
        # 匹配金额格式：¥XX.XX 或 XX.XX元
        patterns = [
            r"¥(\d+(?:\.\d{1,2})?)",
            r"(\d+(?:\.\d{1,2})?)元",
            r"核减[：:]?\s*(\d+(?:\.\d{1,2})?)",
            r"认定金额[：:]?\s*(\d+(?:\.\d{1,2})?)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                try:
                    return float(matches[0])
                except (ValueError, IndexError):
                    continue
        return 0.0

    def _extract_ruling_reason(self, content: str) -> str:
        """从裁决内容中提取裁决理由"""
        lines = content.split("\n")
        reason_lines = []
        capture = False

        for line in lines:
            if "理由" in line or "原因" in line:
                capture = True
                continue
            if capture:
                if line.strip() and not line.startswith("#"):
                    reason_lines.append(line.strip())
                if len(reason_lines) >= 3:
                    break

        return " ".join(reason_lines) if reason_lines else "待定"

    def _calculate_accused_amount(self, context: TrialContext) -> float:
        """计算总指控金额"""
        total = 0.0
        for diff in context.diff_items:
            total += diff.get("diff_amount", 0.0)
        return total

    def run_trial_batch(
        self,
        contexts: List[TrialContext],
        case_prefix: str = "case",
    ) -> List[TrialResult]:
        """
        批量运行审判流程

        Args:
            contexts: 审判上下文列表
            case_prefix: 案件 ID 前缀

        Returns:
            审判结果列表
        """
        results = []
        for i, context in enumerate(contexts):
            case_id = f"{case_prefix}_{i+1}"
            result = self.run_trial(context, case_id)
            results.append(result)
        return results

    def generate_trial_summary(
        self,
        results: List[TrialResult],
    ) -> Dict[str, Any]:
        """
        生成审判汇总

        Args:
            results: 审判结果列表

        Returns:
            汇总信息
        """
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
