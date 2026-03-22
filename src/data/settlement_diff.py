"""
SettlementDiff - 结算差异数据模型

用于记录医保结算时的差异信息，包括医院申报金额与医保核算金额的差异
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DiffType(Enum):
    """差异类型"""
    PRICE_DIFF = "price_diff"           # 价格差异
    QUANTITY_DIFF = "quantity_diff"     # 数量差异
    CATEGORY_DIFF = "category_diff"     # 类别差异
    POLICY_DIFF = "policy_diff"         # 政策差异
    EXCLUSION = "exclusion"              # 拒付
    REASONableness = "reasonableness"   # 不合理
    OVER_LIMIT = "over_limit"            # 超限
    DUPLICATE = "duplicate"             # 重复
    OTHER = "other"                      # 其他


class DiffReason(Enum):
    """差异原因"""
    # 价格类
    PRICE_ABOVE_STANDARD = "price_above_standard"     # 超标准定价
    PRICE_BELOW_STANDARD = "price_below_standard"     # 低于标准定价
    PRICE_NOT_IN_CATALOG = "price_not_in_catalog"     # 不在目录内

    # 数量类
    QUANTITY_EXCEEDS_LIMIT = "quantity_exceeds_limit" # 超量
    QUANTITY_BELOW_MIN = "quantity_below_min"         # 不足量
    DUPLICATE_CHARGE = "duplicate_charge"             # 重复收费

    # 类别类
    ITEM_NOT_IN_CATALOG = "item_not_in_catalog"       # 项目不在目录
    MEDICINE_NOT_IN_CATALOG = "medicine_not_in_catalog"  # 药品不在目录
    WRONG_CATEGORY = "wrong_category"                 # 类别错误

    # 政策类
    NOT_COVERED_BY_POLICY = "not_covered_by_policy"   # 政策不覆盖
    POLICY_EXPIRED = "policy_expired"                  # 政策过期
    HOSPITAL_NOT_QUALIFIED = "hospital_not_qualified"  # 医院不符合资质

    # 超限类
    ANNUAL_LIMIT_EXCEEDED = "annual_limit_exceeded"     # 年度限额超
    VISIT_LIMIT_EXCEEDED = "visit_limit_exceeded"      # 就诊限次超
    ITEM_SPECIFIC_LIMIT_EXCEEDED = "item_specific_limit_exceeded"  # 项目特定限额超

    # 不合理类
    NO_INDICATION = "no_indication"                   # 无适应症
    NOT_APPROPRIATE = "not_appropriate"                 # 不适宜
    NO_CLINICAL_VALUE = "no_clinical_value"            # 无临床价值

    # 其他
    DATA_ERROR = "data_error"                          # 数据错误
    OTHER = "other"                                    # 其他


class DiffSeverity(Enum):
    """差异严重程度"""
    LOW = "low"           # 轻微
    MEDIUM = "medium"     # 中等
    HIGH = "high"         # 严重
    CRITICAL = "critical"  # 严重违规


@dataclass
class SettlementDiff:
    """
    结算差异数据模型

    Attributes:
        id: 差异唯一标识
        expense_id: 关联的费用明细ID
        diff_type: 差异类型
        diff_reason: 差异原因
        severity: 严重程度
        hospital_declared_amount: 医院申报金额
        medicare_calculated_amount: 医保核算金额
        diff_amount: 差异金额
        diff_ratio: 差异比例
        description: 差异描述
        policy_reference: 政策依据
        audit_notes: 审核备注
        audit_date: 审核日期
        auditor: 审核人
    """
    id: str
    expense_id: str
    diff_type: DiffType
    diff_reason: DiffReason
    severity: DiffSeverity
    hospital_declared_amount: float
    medicare_calculated_amount: float
    diff_amount: float
    diff_ratio: float
    description: str = ""
    policy_reference: str = ""
    audit_notes: str = ""
    audit_date: Optional[datetime] = None
    auditor: str = ""

    def __post_init__(self):
        """验证数据有效性"""
        if self.hospital_declared_amount < 0:
            raise ValueError("hospital_declared_amount 不能为负数")
        if self.medicare_calculated_amount < 0:
            raise ValueError("medicare_calculated_amount 不能为负数")
        if self.diff_amount < 0:
            raise ValueError("diff_amount 不能为负数")
        if not 0 <= self.diff_ratio <= 1:
            raise ValueError("diff_ratio 必须在 0-1 之间")

    @property
    def is_rejection(self) -> bool:
        """是否为拒付（差异金额等于申报金额）"""
        return self.diff_type == DiffType.EXCLUSION or abs(
            self.diff_amount - self.hospital_declared_amount
        ) < 0.01

    @property
    def is_significant(self) -> bool:
        """是否有重大差异（差异比例 > 20%）"""
        return self.diff_ratio > 0.2

    @property
    def severity_score(self) -> int:
        """严重程度分数（用于排序）"""
        severity_map = {
            DiffSeverity.LOW: 1,
            DiffSeverity.MEDIUM: 2,
            DiffSeverity.HIGH: 3,
            DiffSeverity.CRITICAL: 4,
        }
        return severity_map.get(self.severity, 0)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "expense_id": self.expense_id,
            "diff_type": self.diff_type.value,
            "diff_reason": self.diff_reason.value,
            "severity": self.severity.value,
            "hospital_declared_amount": self.hospital_declared_amount,
            "medicare_calculated_amount": self.medicare_calculated_amount,
            "diff_amount": self.diff_amount,
            "diff_ratio": self.diff_ratio,
            "description": self.description,
            "policy_reference": self.policy_reference,
            "audit_notes": self.audit_notes,
            "audit_date": self.audit_date.isoformat() if self.audit_date else None,
            "auditor": self.auditor,
            "is_rejection": self.is_rejection,
            "is_significant": self.is_significant,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SettlementDiff":
        """从字典创建实例"""
        diff_type = DiffType(data.get("diff_type", "other"))
        diff_reason = DiffReason(data.get("diff_reason", "other"))
        severity = DiffSeverity(data.get("severity", "low"))

        audit_date = None
        if data.get("audit_date"):
            audit_date = datetime.fromisoformat(data["audit_date"])

        return cls(
            id=data["id"],
            expense_id=data["expense_id"],
            diff_type=diff_type,
            diff_reason=diff_reason,
            severity=severity,
            hospital_declared_amount=data["hospital_declared_amount"],
            medicare_calculated_amount=data["medicare_calculated_amount"],
            diff_amount=data["diff_amount"],
            diff_ratio=data.get("diff_ratio", 0),
            description=data.get("description", ""),
            policy_reference=data.get("policy_reference", ""),
            audit_notes=data.get("audit_notes", ""),
            audit_date=audit_date,
            auditor=data.get("auditor", ""),
        )

    @classmethod
    def calculate_diff(
        cls,
        expense_id: str,
        hospital_declared: float,
        medicare_calculated: float,
        diff_type: DiffType,
        diff_reason: DiffReason,
        description: str = "",
    ) -> "SettlementDiff":
        """
        计算差异并创建实例

        Args:
            expense_id: 费用ID
            hospital_declared: 医院申报金额
            medicare_calculated: 医保核算金额
            diff_type: 差异类型
            diff_reason: 差异原因
            description: 描述

        Returns:
            SettlementDiff 实例
        """
        diff_amount = hospital_declared - medicare_calculated
        diff_ratio = (
            diff_amount / hospital_declared
            if hospital_declared > 0
            else 0
        )

        # 根据差异比例确定严重程度
        if diff_ratio >= 0.5:
            severity = DiffSeverity.CRITICAL
        elif diff_ratio >= 0.3:
            severity = DiffSeverity.HIGH
        elif diff_ratio >= 0.1:
            severity = DiffSeverity.MEDIUM
        else:
            severity = DiffSeverity.LOW

        return cls(
            id=f"diff_{expense_id}_{datetime.now().timestamp()}",
            expense_id=expense_id,
            diff_type=diff_type,
            diff_reason=diff_reason,
            severity=severity,
            hospital_declared_amount=hospital_declared,
            medicare_calculated_amount=medicare_calculated,
            diff_amount=diff_amount,
            diff_ratio=diff_ratio,
            description=description,
        )

    def get_summary(self) -> str:
        """获取差异摘要"""
        return (
            f"{self.diff_type.value}: ¥{self.hospital_declared_amount:.2f} → "
            f"¥{self.medicare_calculated_amount:.2f} "
            f"(差异 ¥{self.diff_amount:.2f}, {self.diff_ratio*100:.1f}%)"
        )
