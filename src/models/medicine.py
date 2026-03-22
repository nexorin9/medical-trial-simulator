"""
Medicine - 药品数据模型

药品包括：西药、中成药、中药饮片等
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class MedicineCategory(Enum):
    """药品类别"""
    WESTERN = "western"           # 西药
    CHINESE_PATENT = "chinese_patent"  # 中成药
    CHINESE_HERBAL = "chinese_herbal"  # 中药饮片
    BIOLOGIC = "biologic"        # 生物制品
    VACCINE = "vaccine"          # 疫苗
    OTHER = "other"              # 其他


class MedicineForm(Enum):
    """药品剂型"""
    TABLET = "tablet"           # 片剂
    CAPSULE = "capsule"         # 胶囊
    INJECTION = "injection"     # 注射剂
    ORAL_LIQUID = "oral_liquid" # 口服液
    CREAM = "cream"             # 软膏剂
    POWDER = "powder"           # 散剂
    GRANULE = "granule"         # 颗粒剂
    SYRUP = "syrup"             # 糖浆剂
    PATCH = "patch"             # 贴剂
    OTHER = "other"             # 其他


class MedicineType(Enum):
    """药品类型（甲类/乙类/丙类）"""
    CLASS_A = "class_a"   # 甲类 - 全额报销
    CLASS_B = "class_b"   # 乙类 - 部分自付
    CLASS_C = "class_c"   # 丙类 - 全额自付


@dataclass
class Medicine:
    """
    药品数据模型

    Attributes:
        code: 药品编码（医保目录编号）
        name: 药品名称
        generic_name: 通用名
        brand_name: 商品名
        category: 药品类别
        form: 剂型
        medicine_type: 药品类型（甲类/乙类/丙类）
        specification: 规格
        unit: 计量单位
        standard_price: 标准价格（元）
        reimbursement_rate: 报销比例（乙类药品使用）
        level_limit: 医院级别限制
        manufacturer: 生产企业
        approval_number: 批准文号
        indication: 适应症
        usage: 用法用量
        side_effects: 不良反应
        max_days_per_prescription: 每次处方最大天数
        max_amount_per_year: 年度最高限额
        is_essential: 是否国家基本药物
        is_emergency: 是否急救药品
    """
    code: str
    name: str
    generic_name: str
    category: MedicineCategory
    form: MedicineForm
    medicine_type: MedicineType
    specification: str
    unit: str
    standard_price: float
    level_limit: Optional[List[int]] = None
    brand_name: str = ""
    manufacturer: str = ""
    approval_number: str = ""
    indication: str = ""
    usage: str = ""
    side_effects: str = ""
    reimbursement_rate: float = 1.0  # 默认为1，甲类全额报销
    max_days_per_prescription: Optional[int] = None
    max_amount_per_year: Optional[float] = None
    is_essential: bool = False
    is_emergency: bool = False

    def __post_init__(self):
        """验证数据有效性"""
        if self.standard_price < 0:
            raise ValueError("standard_price 不能为负数")
        if not 0 <= self.reimbursement_rate <= 1:
            raise ValueError("reimbursement_rate 必须在 0-1 之间")

    @property
    def effective_reimbursement_rate(self) -> float:
        """实际报销比例"""
        if self.medicine_type == MedicineType.CLASS_A:
            return 1.0  # 甲类全额报销
        elif self.medicine_type == MedicineType.CLASS_B:
            return self.reimbursement_rate  # 乙类按设定比例
        else:
            return 0.0  # 丙类自费

    @property
    def self_pay_amount(self) -> float:
        """自付金额"""
        return self.standard_price * (1 - self.effective_reimbursement_rate)

    @property
    def reimbursement_amount(self) -> float:
        """报销金额"""
        return self.standard_price * self.effective_reimbursement_rate

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "generic_name": self.generic_name,
            "brand_name": self.brand_name,
            "category": self.category.value,
            "form": self.form.value,
            "medicine_type": self.medicine_type.value,
            "specification": self.specification,
            "unit": self.unit,
            "standard_price": self.standard_price,
            "reimbursement_rate": self.reimbursement_rate,
            "level_limit": self.level_limit,
            "manufacturer": self.manufacturer,
            "approval_number": self.approval_number,
            "indication": self.indication,
            "usage": self.usage,
            "side_effects": self.side_effects,
            "max_days_per_prescription": self.max_days_per_prescription,
            "max_amount_per_year": self.max_amount_per_year,
            "is_essential": self.is_essential,
            "is_emergency": self.is_emergency,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Medicine":
        """从字典创建实例"""
        category = MedicineCategory(data.get("category", "other"))
        form = MedicineForm(data.get("form", "other"))
        medicine_type = MedicineType(data.get("medicine_type", "class_c"))

        return cls(
            code=data["code"],
            name=data["name"],
            generic_name=data.get("generic_name", data["name"]),
            brand_name=data.get("brand_name", ""),
            category=category,
            form=form,
            medicine_type=medicine_type,
            specification=data.get("specification", ""),
            unit=data.get("unit", "盒"),
            standard_price=data["standard_price"],
            reimbursement_rate=data.get("reimbursement_rate", 1.0),
            level_limit=data.get("level_limit"),
            manufacturer=data.get("manufacturer", ""),
            approval_number=data.get("approval_number", ""),
            indication=data.get("indication", ""),
            usage=data.get("usage", ""),
            side_effects=data.get("side_effects", ""),
            max_days_per_prescription=data.get("max_days_per_prescription"),
            max_amount_per_year=data.get("max_amount_per_year"),
            is_essential=data.get("is_essential", False),
            is_emergency=data.get("is_emergency", False),
        )

    def is_reimbursable_at_level(self, hospital_level: int) -> bool:
        """检查是否可在指定医院级别报销"""
        if self.level_limit is None:
            return True
        return hospital_level in self.level_limit

    def validate_prescription(self, days: int, hospital_level: int) -> tuple[bool, str]:
        """
        验证处方是否符合医保规定

        Returns:
            (is_valid, reason): 是否有效及原因
        """
        # 检查医院级别
        if not self.is_reimbursable_at_level(hospital_level):
            return False, f"该药品不在{hospital_level}级医院医保范围内"

        # 检查处方天数限制
        if self.max_days_per_prescription and days > self.max_days_per_prescription:
            return False, f"超出每次处方最大天数限制（{self.max_days_per_prescription}天）"

        return True, "符合医保规定"
