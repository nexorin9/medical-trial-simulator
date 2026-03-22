"""
ExpenseDetail - 费用明细数据模型

用于记录每笔费用的详细信息，包括项目、药品、服务设施等
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ExpenseType(Enum):
    """费用类型"""
    MEDICAL_ITEM = "medical_item"      # 诊疗项目
    MEDICINE = "medicine"              # 药品
    SERVICE_FACILITY = "service_facility"  # 服务设施
    OTHER = "other"                    # 其他


class ExpenseCategory(Enum):
    """费用类别"""
    EXAMINATION = "examination"        # 检查费
    TREATMENT = "treatment"            # 治疗费
    SURGERY = "surgery"                # 手术费
    LABORATORY = "laboratory"          # 化验费
    MEDICATION = "medication"          # 药费
    MATERIALS = "materials"            # 材料费
    NURSING = "nursing"                # 护理费
    BED = "bed"                        # 床位费
    OTHER = "other"                    # 其他


class ChargeType(Enum):
    """费用结算类型"""
    medicare = "medicard"              # 医保
    SELF_PAY = "self_pay"             # 自费
    MIXED = "mixed"                    # 混合


@dataclass
class ExpenseDetail:
    """
    费用明细数据模型

    Attributes:
        id: 费用唯一标识
        expense_type: 费用类型（诊疗项目/药品/服务设施）
        expense_category: 费用类别
        item_code: 医保目录项目编码
        item_name: 项目名称
        quantity: 数量
        unit_price: 单价（元）
        total_amount: 总金额（元）
        charge_type: 费用结算类型
        hospital_level: 医院级别（1/2/3级）
        department: 科室
        doctor: 医生
        visit_date: 就诊日期
        diagnosis: 诊断
        is_reimbursable: 是否可报销
        reimbursement_amount: 报销金额
        self_pay_amount: 自付金额
        notes: 备注
    """
    id: str
    expense_type: ExpenseType
    expense_category: ExpenseCategory
    item_code: str
    item_name: str
    quantity: float
    unit_price: float
    total_amount: float
    charge_type: ChargeType
    hospital_level: int
    department: str = ""
    doctor: str = ""
    visit_date: Optional[datetime] = None
    diagnosis: str = ""
    is_reimbursable: bool = True
    reimbursement_amount: float = 0.0
    self_pay_amount: float = 0.0
    notes: str = ""

    def __post_init__(self):
        """验证数据有效性"""
        if self.quantity < 0:
            raise ValueError("quantity 不能为负数")
        if self.unit_price < 0:
            raise ValueError("unit_price 不能为负数")
        if self.total_amount < 0:
            raise ValueError("total_amount 不能为负数")
        if self.hospital_level not in [1, 2, 3]:
            raise ValueError("hospital_level 必须是 1、2 或 3")

    @property
    def calculated_total(self) -> float:
        """计算总金额（数量 × 单价）"""
        return self.quantity * self.unit_price

    @property
    def actual_total(self) -> float:
        """实际总金额（使用字段值或计算值）"""
        if self.total_amount > 0:
            return self.total_amount
        return self.calculated_total

    @property
    def out_of_pocket_ratio(self) -> float:
        """自付比例"""
        if self.actual_total == 0:
            return 0.0
        return self.self_pay_amount / self.actual_total

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "expense_type": self.expense_type.value,
            "expense_category": self.expense_category.value,
            "item_code": self.item_code,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_amount": self.actual_total,
            "charge_type": self.charge_type.value,
            "hospital_level": self.hospital_level,
            "department": self.department,
            "doctor": self.doctor,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "diagnosis": self.diagnosis,
            "is_reimbursable": self.is_reimbursable,
            "reimbursement_amount": self.reimbursement_amount,
            "self_pay_amount": self.self_pay_amount,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpenseDetail":
        """从字典创建实例"""
        expense_type = ExpenseType(data.get("expense_type", "other"))
        expense_category = ExpenseCategory(data.get("expense_category", "other"))
        charge_type = ChargeType(data.get("charge_type", "medicare"))

        visit_date = None
        if data.get("visit_date"):
            visit_date = datetime.fromisoformat(data["visit_date"])

        return cls(
            id=data["id"],
            expense_type=expense_type,
            expense_category=expense_category,
            item_code=data["item_code"],
            item_name=data["item_name"],
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            total_amount=data.get("total_amount", 0),
            charge_type=charge_type,
            hospital_level=data["hospital_level"],
            department=data.get("department", ""),
            doctor=data.get("doctor", ""),
            visit_date=visit_date,
            diagnosis=data.get("diagnosis", ""),
            is_reimbursable=data.get("is_reimbursable", True),
            reimbursement_amount=data.get("reimbursement_amount", 0),
            self_pay_amount=data.get("self_pay_amount", 0),
            notes=data.get("notes", ""),
        )

    def get_summary(self) -> str:
        """获取费用摘要"""
        return f"{self.item_name} × {self.quantity} = ¥{self.actual_total:.2f}"

    def validate_for_medicare(self) -> tuple[bool, List[str]]:
        """
        验证是否符合医保报销条件

        Returns:
            (is_valid, reasons): 是否有效及原因列表
        """
        reasons = []

        # 检查是否为医保项目
        if self.charge_type == ChargeType.SELF_PAY:
            reasons.append("该项目为自费项目")
            return False, reasons

        # 检查是否在医保目录中
        if not self.item_code:
            reasons.append("该项目无医保目录编码")

        # 检查金额
        if self.unit_price <= 0:
            reasons.append("单价必须大于0")

        return len(reasons) == 0, reasons
