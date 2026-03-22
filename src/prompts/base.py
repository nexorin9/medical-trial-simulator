"""
审判框架基础类

定义审判角色的基类和通用接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class TrialRole(Enum):
    """审判角色类型"""
    PROSECUTOR = "prosecutor"    # 起诉方（医保审核规则）
    DEFENSE = "defense"          # 辩护方（医院说明）
    JUDGE = "judge"              # 法官（综合裁决）


@dataclass
class TrialStatement:
    """
    审判陈述

    Attributes:
        role: 角色类型
        content: 陈述内容
        evidence: 证据列表
        references: 引用依据
        timestamp: 时间戳
    """
    role: TrialRole
    content: str
    evidence: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role.value,
            "content": self.content,
            "evidence": self.evidence,
            "references": self.references,
            "timestamp": self.timestamp,
        }


@dataclass
class TrialContext:
    """
    审判上下文

    包含审判所需的所有信息
    """
    # 费用信息
    expense_items: List[Dict[str, Any]] = field(default_factory=list)

    # 差异信息
    diff_items: List[Dict[str, Any]] = field(default_factory=list)

    # 医保目录
    medicare_catalog: Dict[str, Any] = field(default_factory=dict)

    # 医院信息
    hospital_info: Dict[str, Any] = field(default_factory=dict)

    # 患者信息
    patient_info: Dict[str, Any] = field(default_factory=dict)

    # 诊断信息
    diagnosis: str = ""

    # 既往陈述
    previous_statements: List[TrialStatement] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "expense_items": self.expense_items,
            "diff_items": self.diff_items,
            "medicare_catalog": self.medicare_catalog,
            "hospital_info": self.hospital_info,
            "patient_info": self.patient_info,
            "diagnosis": self.diagnosis,
            "previous_statements": [
                s.to_dict() for s in self.previous_statements
            ],
        }

    def format_for_prompt(self) -> str:
        """格式化为 prompt 所需文本"""
        lines = []

        # 患者信息
        if self.patient_info:
            lines.append("【患者信息】")
            for k, v in self.patient_info.items():
                lines.append(f"  {k}: {v}")
            lines.append("")

        # 诊断信息
        if self.diagnosis:
            lines.append(f"【诊断】{self.diagnosis}")
            lines.append("")

        # 费用明细
        if self.expense_items:
            lines.append("【费用明细】")
            for i, item in enumerate(self.expense_items, 1):
                lines.append(f"  {i}. {item.get('item_name', '未知项目')}")
                lines.append(f"     编码: {item.get('item_code', 'N/A')}")
                lines.append(f"     数量: {item.get('quantity', 0)}")
                lines.append(f"     单价: ¥{item.get('unit_price', 0):.2f}")
                lines.append(f"     金额: ¥{item.get('total_amount', 0):.2f}")
                lines.append(f"     类型: {item.get('expense_type', 'N/A')}")
            lines.append("")

        # 结算差异
        if self.diff_items:
            lines.append("【结算差异】")
            for i, diff in enumerate(self.diff_items, 1):
                lines.append(f"  {i}. {diff.get('description', '差异')}")
                lines.append(f"     差异类型: {diff.get('diff_type', 'N/A')}")
                lines.append(f"     原因: {diff.get('diff_reason', 'N/A')}")
                lines.append(f"     申报金额: ¥{diff.get('hospital_declared_amount', 0):.2f}")
                lines.append(f"     核算金额: ¥{diff.get('medicare_calculated_amount', 0):.2f}")
                lines.append(f"     差异金额: ¥{diff.get('diff_amount', 0):.2f}")
                lines.append(f"     严重程度: {diff.get('severity', 'N/A')}")
            lines.append("")

        return "\n".join(lines)


class BaseTrialPrompt(ABC):
    """
    审判角色基类

    定义各角色的通用接口和行为
    """

    def __init__(self, role: TrialRole):
        """
        初始化审判角色

        Args:
            role: 角色类型
        """
        self.role = role
        self._system_prompt = self._build_system_prompt()

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """
        构建系统 prompt

        Returns:
            系统 prompt 文本
        """
        pass

    @abstractmethod
    def build_user_prompt(self, context: TrialContext) -> str:
        """
        构建用户 prompt

        Args:
            context: 审判上下文

        Returns:
            用户 prompt 文本
        """
        pass

    def get_system_prompt(self) -> str:
        """获取系统 prompt"""
        return self._system_prompt

    def parse_response(self, response: str) -> TrialStatement:
        """
        解析 LLM 响应

        Args:
            response: LLM 响应文本

        Returns:
            审判陈述
        """
        # 提取证据和引用
        evidence = self._extract_evidence(response)
        references = self._extract_references(response)

        return TrialStatement(
            role=self.role,
            content=response,
            evidence=evidence,
            references=references,
        )

    def _extract_evidence(self, text: str) -> List[str]:
        """提取证据列表"""
        evidence = []
        lines = text.split("\n")

        in_evidence_section = False
        for line in lines:
            if "证据" in line or "依据" in line:
                in_evidence_section = True
                continue
            if in_evidence_section:
                if line.strip().startswith(("-", "•", "*", "1.", "2.", "3.")):
                    evidence.append(line.strip().lstrip("-•*1234567890. "))
                elif line.strip() == "":
                    in_evidence_section = False

        return evidence

    def _extract_references(self, text: str) -> List[str]:
        """提取引用列表"""
        references = []

        # 提取政策文件引用
        import re
        patterns = [
            r"(医保目录|药品目录|诊疗项目目录)",
            r"(医保发|人社部|卫健委|国家医保局)\d{4}号?",
            r"(基本医疗保险|药品目录|诊疗项目).*?规定",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            references.extend(matches)

        return list(set(references))
