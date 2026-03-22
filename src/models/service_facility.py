"""
ServiceFacility - 服务设施数据模型

服务设施包括：床位费、诊察费、空调费、取暖费等
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class FacilityCategory(Enum):
    """服务设施类别"""
    BED = "bed"                 # 床位费
    CONSULTATION = "consultation"  # 诊察费
    NURSING = "nursing"         # 护理费
    AIR_CONDITIONING = "air_conditioning"  # 空调费
    HEATING = "heating"         # 取暖费
    MEAL = "meal"               # 膳食费
    TRANSPORT = "transport"    # 救护车费
    OTHER = "other"             # 其他


class BedType(Enum):
    """床位类型"""
    GENERAL = "general"         # 普通床位
    SPECIAL = "special"         # 特殊床位（单间、套间）
    ICU = "icu"                 # 重症监护室
    CCU = "ccu"                # 冠心病监护室
    NICU = "nicu"               # 新生儿监护室
    OPERATING_ROOM = "operating_room"  # 手术室床位
    EMERGENCY = "emergency"     # 急诊观察床


class FacilityType(Enum):
    """设施类型"""
    STANDARD = "standard"      # 标准（可报销）
    ENHANCED = "enhanced"       # 增强（部分自付）
    VIP = "vip"                 # VIP（全额自付）


@dataclass
class ServiceFacility:
    """
    服务设施数据模型

    Attributes:
        code: 设施编码（医保目录编号）
        name: 设施名称
        category: 设施类别
        bed_type: 床位类型（仅床位费适用）
        facility_type: 设施类型
        unit: 计量单位（床位按天，其他按次/项）
        standard_price: 标准价格（元）
        reimbursement_rate: 报销比例
        level_limit: 医院级别限制
        max_days_per_admission: 每次住院最大天数
        max_amount_per_admission: 每次住院最高限额
        description: 说明
        conditions: 适用条件
    """
    code: str
    name: str
    category: FacilityCategory
    facility_type: FacilityType
    unit: str
    standard_price: float
    reimbursement_rate: float = 1.0
    level_limit: Optional[List[int]] = None
    bed_type: Optional[BedType] = None
    max_days_per_admission: Optional[int] = None
    max_amount_per_admission: Optional[float] = None
    description: str = ""
    conditions: str = ""

    def __post_init__(self):
        """验证数据有效性"""
        if self.standard_price < 0:
            raise ValueError("standard_price 不能为负数")
        if not 0 <= self.reimbursement_rate <= 1:
            raise ValueError("reimbursement_rate 必须在 0-1 之间")

    @property
    def self_pay_amount(self) -> float:
        """自付金额"""
        return self.standard_price * (1 - self.reimbursement_rate)

    @property
    def reimbursement_amount(self) -> float:
        """报销金额"""
        return self.standard_price * self.reimbursement_rate

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category.value,
            "bed_type": self.bed_type.value if self.bed_type else None,
            "facility_type": self.facility_type.value,
            "unit": self.unit,
            "standard_price": self.standard_price,
            "reimbursement_rate": self.reimbursement_rate,
            "level_limit": self.level_limit,
            "max_days_per_admission": self.max_days_per_admission,
            "max_amount_per_admission": self.max_amount_per_admission,
            "description": self.description,
            "conditions": self.conditions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceFacility":
        """从字典创建实例"""
        category = FacilityCategory(data.get("category", "other"))
        facility_type = FacilityType(data.get("facility_type", "standard"))
        bed_type = BedType(data.get("bed_type")) if data.get("bed_type") else None

        return cls(
            code=data["code"],
            name=data["name"],
            category=category,
            facility_type=facility_type,
            unit=data.get("unit", "天"),
            standard_price=data["standard_price"],
            reimbursement_rate=data.get("reimbursement_rate", 1.0),
            level_limit=data.get("level_limit"),
            bed_type=bed_type,
            max_days_per_admission=data.get("max_days_per_admission"),
            max_amount_per_admission=data.get("max_amount_per_admission"),
            description=data.get("description", ""),
            conditions=data.get("conditions", ""),
        )

    def is_reimbursable_at_level(self, hospital_level: int) -> bool:
        """检查是否可在指定医院级别报销"""
        if self.level_limit is None:
            return True
        return hospital_level in self.level_limit

    def validate_usage(self, days: int, hospital_level: int) -> tuple[bool, str]:
        """
        验证使用是否符合医保规定

        Returns:
            (is_valid, reason): 是否有效及原因
        """
        # 检查医院级别
        if not self.is_reimbursable_at_level(hospital_level):
            return False, f"该设施不在{hospital_level}级医院医保范围内"

        # 检查住院天数限制
        if self.max_days_per_admission and days > self.max_days_per_admission:
            return False, f"超出每次住院最大天数限制（{self.max_days_per_admission}天）"

        return True, "符合医保规定"
