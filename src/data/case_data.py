"""
CaseData - 案件数据整合类

将费用明细和结算差异整合为完整的案件数据，用于审判流程
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from .expense_detail import ExpenseDetail
from .settlement_diff import SettlementDiff


class CaseStatus(Enum):
    """案件状态"""
    PENDING = "pending"           # 待处理
    PROSECUTING = "prosecuting"   # 起诉中
    DEFENDING = "defending"       # 辩护中
    JUDGING = "judging"           # 审理中
    CLOSED = "closed"             # 已结案
    REJECTED = "rejected"         # 已驳回


class CaseType(Enum):
    """案件类型"""
    SINGLE = "single"             # 单笔费用
    BATCH = "batch"               # 批量费用
    APPEAL = "appeal"             # 申诉
    AUDIT = "audit"               # 审计


class Verdict(Enum):
    """裁决结果"""
    PROSECUTION_WINS = "prosecution_wins"     # 起诉方胜诉
    DEFENSE_WINS = "defense_wins"             # 辩护方胜诉
    COMPROMISE = "compromise"                  # 折中裁决
    PARTIAL_WIN = "partial_win"               # 部分支持


@dataclass
class CaseData:
    """
    案件数据整合类

    Attributes:
        id: 案件唯一标识
        case_type: 案件类型
        status: 案件状态
        patient_id: 患者ID
        patient_name: 患者姓名
        hospital_id: 医院ID
        hospital_name: 医院名称
        hospital_level: 医院级别
        visit_id: 就诊ID
        visit_date: 就诊日期
        department: 科室
        diagnosis: 诊断
        total_expense_amount: 总费用金额
        total_reimbursement: 医保报销金额
        total_self_pay: 自付金额
        total_diff_amount: 差异总金额
        expenses: 费用明细列表
        diffs: 结算差异列表
        created_at: 创建时间
        updated_at: 更新时间
        trial_record: 审判记录
        verdict: 裁决结果
        judgment: 判决书
    """
    id: str
    case_type: CaseType
    status: CaseStatus
    patient_id: str
    patient_name: str
    hospital_id: str
    hospital_name: str
    hospital_level: int
    visit_id: str
    visit_date: datetime
    department: str
    diagnosis: str
    expenses: List[ExpenseDetail] = field(default_factory=list)
    diffs: List[SettlementDiff] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    trial_record: Dict = field(default_factory=dict)
    verdict: Optional[Verdict] = None
    judgment: str = ""

    # 计算属性（在 __post_init__ 中计算）
    total_expense_amount: float = 0.0
    total_reimbursement: float = 0.0
    total_self_pay: float = 0.0
    total_diff_amount: float = 0.0

    def __post_init__(self):
        """初始化计算属性"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

        # 计算汇总数据
        self._recalculate_totals()

    def _recalculate_totals(self):
        """重新计算汇总数据"""
        self.total_expense_amount = sum(e.actual_total for e in self.expenses)
        self.total_reimbursement = sum(e.reimbursement_amount for e in self.expenses)
        self.total_self_pay = sum(e.self_pay_amount for e in self.expenses)
        self.total_diff_amount = sum(d.diff_amount for d in self.diffs)

    def add_expense(self, expense: ExpenseDetail):
        """添加费用明细"""
        self.expenses.append(expense)
        self._recalculate_totals()
        self.updated_at = datetime.now()

    def add_diff(self, diff: SettlementDiff):
        """添加结算差异"""
        self.diffs.append(diff)
        self._recalculate_totals()
        self.updated_at = datetime.now()

    def remove_expense(self, expense_id: str) -> bool:
        """移除费用明细"""
        original_len = len(self.expenses)
        self.expenses = [e for e in self.expenses if e.id != expense_id]
        if len(self.expenses) < original_len:
            self._recalculate_totals()
            self.updated_at = datetime.now()
            return True
        return False

    def get_expense_by_id(self, expense_id: str) -> Optional[ExpenseDetail]:
        """根据ID获取费用明细"""
        for expense in self.expenses:
            if expense.id == expense_id:
                return expense
        return None

    def get_diff_by_expense_id(self, expense_id: str) -> List[SettlementDiff]:
        """获取指定费用明细的所有差异"""
        return [d for d in self.diffs if d.expense_id == expense_id]

    @property
    def has_significant_diff(self) -> bool:
        """是否有重大差异"""
        return any(d.is_significant for d in self.diffs)

    @property
    def has_rejection(self) -> bool:
        """是否有拒付"""
        return any(d.is_rejection for d in self.diffs)

    @property
    def diff_count(self) -> int:
        """差异数量"""
        return len(self.diffs)

    @property
    def expense_count(self) -> int:
        """费用明细数量"""
        return len(self.expenses)

    @property
    def diff_ratio(self) -> float:
        """差异比例"""
        if self.total_expense_amount == 0:
            return 0.0
        return self.total_diff_amount / self.total_expense_amount

    def get_severity_summary(self) -> Dict[str, int]:
        """获取严重程度统计"""
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        for diff in self.diffs:
            summary[diff.severity.value] += 1
        return summary

    def get_high_risk_expenses(self) -> List[ExpenseDetail]:
        """获取高风险费用明细（存在重大差异）"""
        high_risk_ids = {d.expense_id for d in self.diffs if d.is_significant}
        return [e for e in self.expenses if e.id in high_risk_ids]

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "case_type": self.case_type.value,
            "status": self.status.value,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "hospital_id": self.hospital_id,
            "hospital_name": self.hospital_name,
            "hospital_level": self.hospital_level,
            "visit_id": self.visit_id,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "department": self.department,
            "diagnosis": self.diagnosis,
            "total_expense_amount": self.total_expense_amount,
            "total_reimbursement": self.total_reimbursement,
            "total_self_pay": self.total_self_pay,
            "total_diff_amount": self.total_diff_amount,
            "diff_ratio": self.diff_ratio,
            "expense_count": self.expense_count,
            "diff_count": self.diff_count,
            "has_significant_diff": self.has_significant_diff,
            "has_rejection": self.has_rejection,
            "severity_summary": self.get_severity_summary(),
            "expenses": [e.to_dict() for e in self.expenses],
            "diffs": [d.to_dict() for d in self.diffs],
            "trial_record": self.trial_record,
            "verdict": self.verdict.value if self.verdict else None,
            "judgment": self.judgment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CaseData":
        """从字典创建实例"""
        case_type = CaseType(data.get("case_type", "single"))
        status = CaseStatus(data.get("status", "pending"))

        visit_date = None
        if data.get("visit_date"):
            visit_date = datetime.fromisoformat(data["visit_date"])

        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        verdict = None
        if data.get("verdict"):
            verdict = Verdict(data["verdict"])

        # 解析费用明细
        expenses = []
        for e_data in data.get("expenses", []):
            expenses.append(ExpenseDetail.from_dict(e_data))

        # 解析结算差异
        diffs = []
        for d_data in data.get("diffs", []):
            diffs.append(SettlementDiff.from_dict(d_data))

        return cls(
            id=data["id"],
            case_type=case_type,
            status=status,
            patient_id=data["patient_id"],
            patient_name=data["patient_name"],
            hospital_id=data["hospital_id"],
            hospital_name=data["hospital_name"],
            hospital_level=data["hospital_level"],
            visit_id=data["visit_id"],
            visit_date=visit_date,
            department=data.get("department", ""),
            diagnosis=data.get("diagnosis", ""),
            expenses=expenses,
            diffs=diffs,
            created_at=created_at,
            updated_at=updated_at,
            trial_record=data.get("trial_record", {}),
            verdict=verdict,
            judgment=data.get("judgment", ""),
        )

    def get_summary(self) -> str:
        """获取案件摘要"""
        return (
            f"案件 {self.id}: {self.patient_name} | "
            f"费用 ¥{self.total_expense_amount:.2f} | "
            f"差异 ¥{self.total_diff_amount:.2f} ({self.diff_ratio*100:.1f}%) | "
            f"差异数: {self.diff_count}"
        )

    def get_expenses_summary_text(self) -> str:
        """获取费用汇总文本（用于LLM输入）"""
        lines = ["## 费用明细"]
        for expense in self.expenses:
            lines.append(
                f"- {expense.item_name} ({expense.item_code}): "
                f"¥{expense.actual_total:.2f} × {expense.quantity} = "
                f"¥{expense.actual_total:.2f}"
            )
        return "\n".join(lines)

    def get_diffs_summary_text(self) -> str:
        """获取差异汇总文本（用于LLM输入）"""
        lines = ["## 结算差异"]
        for diff in self.diffs:
            lines.append(
                f"- {diff.description or diff.diff_reason.value}: "
                f"申报¥{diff.hospital_declared_amount:.2f} → "
                f"核算¥{diff.medicare_calculated_amount:.2f} "
                f"(差异¥{diff.diff_amount:.2f}, {diff.diff_ratio*100:.1f}%)"
            )
        return "\n".join(lines)
