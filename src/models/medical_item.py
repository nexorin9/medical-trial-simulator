"""
MedicalItem - 诊疗项目数据模型

诊疗项目包括：检查费、治疗费、手术费、化验费等
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class ItemCategory(Enum):
    """诊疗项目类别"""
    EXAMINATION = "examination"      # 检查费
    TREATMENT = "treatment"          # 治疗费
    SURGERY = "surgery"               # 手术费
    LABORATORY = "laboratory"         # 化验费
    NURSING = "nursing"               # 护理费
    CONSULTATION = "consultation"     # 诊疗费
    OTHER = "other"                   # 其他


class ReimbursementType(Enum):
    """报销类型"""
    FULL = "full"           # 全额报销
    PARTIAL = "partial"     # 部分报销
    SELF_PAY = "self_pay"  # 自费


@dataclass
class MedicalItem:
    """
    诊疗项目数据模型

    Attributes:
        code: 项目编码（医保目录编号）
        name: 项目名称
        category: 项目类别
        unit: 计量单位
        standard_price: 标准价格（元）
        reimbursement_rate: 报销比例（0-1）
        reimbursement_type: 报销类型
        level_limit: 医院级别限制（1/2/3级医院）
        description: 项目说明
        indications: 适应症说明
        contraindications: 禁忌症说明
        requires_approval: 是否需要审批
        max_times_per_visit: 每次就诊最大次数
        max_amount_per_year: 年度最高限额
    """
    code: str
    name: str
    category: ItemCategory
    unit: str
    standard_price: float
    reimbursement_rate: float
    reimbursement_type: ReimbursementType
    level_limit: Optional[List[int]] = None
    description: str = ""
    indications: str = ""
    contraindications: str = ""
    requires_approval: bool = False
    max_times_per_visit: Optional[int] = None
    max_amount_per_year: Optional[float] = None

    def __post_init__(self):
        """验证数据有效性"""
        if self.standard_price < 0:
            raise ValueError("standard_price 不能为负数")
        if not 0 <= self.reimbursement_rate <= 1:
            raise ValueError("reimbursement_rate 必须在 0-1 之间")

    @property
    def self_pay_amount(self) -> float:
        """自付金额 = 标准价格 × (1 - 报销比例)"""
        return self.standard_price * (1 - self.reimbursement_rate)

    @property
    def reimbursement_amount(self) -> float:
        """报销金额 = 标准价格 × 报销比例"""
        return self.standard_price * self.reimbursement_rate

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category.value,
            "unit": self.unit,
            "standard_price": self.standard_price,
            "reimbursement_rate": self.reimbursement_rate,
            "reimbursement_type": self.reimbursement_type.value,
            "level_limit": self.level_limit,
            "description": self.description,
            "indications": self.indications,
            "contraindications": self.contraindications,
            "requires_approval": self.requires_approval,
            "max_times_per_visit": self.max_times_per_visit,
            "max_amount_per_year": self.max_amount_per_year,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MedicalItem":
        """从字典创建实例"""
        category = ItemCategory(data.get("category", "other"))
        reimbursement_type = ReimbursementType(data.get("reimbursement_type", "partial"))

        return cls(
            code=data["code"],
            name=data["name"],
            category=category,
            unit=data.get("unit", "次"),
            standard_price=data["standard_price"],
            reimbursement_rate=data.get("reimbursement_rate", 0.85),
            reimbursement_type=reimbursement_type,
            level_limit=data.get("level_limit"),
            description=data.get("description", ""),
            indications=data.get("indications", ""),
            contraindications=data.get("contraindications", ""),
            requires_approval=data.get("requires_approval", False),
            max_times_per_visit=data.get("max_times_per_visit"),
            max_amount_per_year=data.get("max_amount_per_year"),
        )

    def is_reimbursable_at_level(self, hospital_level: int) -> bool:
        """检查是否可在指定医院级别报销"""
        if self.level_limit is None:
            return True
        return hospital_level in self.level_limit

    def validate_usage(self, quantity: int, hospital_level: int) -> tuple[bool, str]:
        """
        验证使用是否符合医保规定

        Returns:
            (is_valid, reason): 是否有效及原因
        """
        # 检查医院级别
        if not self.is_reimbursable_at_level(hospital_level):
            return False, f"该项目不在{hospital_level}级医院医保范围内"

        # 检查每次就诊次数限制
        if self.max_times_per_visit and quantity > self.max_times_per_visit:
            return False, f"超出每次就诊最大次数限制（{self.max_times_per_visit}次）"

        return True, "符合医保规定"
