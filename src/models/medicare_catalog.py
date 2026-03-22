"""
MedicareCatalog - 医保目录整合类

整合诊疗项目、药品、服务设施，提供统一查询接口
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from .medical_item import MedicalItem, ItemCategory
from .medicine import Medicine, MedicineCategory
from .service_facility import ServiceFacility, FacilityCategory


@dataclass
class MedicareCatalog:
    """
    医保目录整合类

    整合三类医保目录：
    - 诊疗项目（medical_items）
    - 药品（medicines）
    - 服务设施（service_facilities）

    提供统一查询接口：
    - 按编码查询
    - 按名称模糊搜索
    - 按类别查询
    - 费用合规性校验
    """

    medical_items: Dict[str, MedicalItem] = field(default_factory=dict)
    medicines: Dict[str, Medicine] = field(default_factory=dict)
    service_facilities: Dict[str, ServiceFacility] = field(default_factory=dict)

    # 缓存用于快速搜索
    _medical_items_by_name: Dict[str, List[str]] = field(default_factory=dict)
    _medicines_by_name: Dict[str, List[str]] = field(default_factory=dict)
    _facilities_by_name: Dict[str, List[str]] = field(default_factory=dict)

    def add_medical_item(self, item: MedicalItem) -> None:
        """添加诊疗项目"""
        self.medical_items[item.code] = item
        self._index_by_name(self._medical_items_by_name, item.code, item.name)

    def add_medicine(self, medicine: Medicine) -> None:
        """添加药品"""
        self.medicines[medicine.code] = medicine
        self._index_by_name(self._medicines_by_name, medicine.code, medicine.name)
        # 同时索引通用名
        if medicine.generic_name:
            self._index_by_name(self._medicines_by_name, medicine.code, medicine.generic_name)

    def add_service_facility(self, facility: ServiceFacility) -> None:
        """添加服务设施"""
        self.service_facilities[facility.code] = facility
        self._index_by_name(self._facilities_by_name, facility.code, facility.name)

    def _index_by_name(self, index: Dict[str, List[str]], code: str, name: str) -> None:
        """按名称索引"""
        # 简单分词索引
        keywords = name.lower().split()
        for keyword in keywords:
            if len(keyword) >= 2:  # 忽略单字符
                if keyword not in index:
                    index[keyword] = []
                if code not in index[keyword]:
                    index[keyword].append(code)

    def get_medical_item(self, code: str) -> Optional[MedicalItem]:
        """按编码获取诊疗项目"""
        return self.medical_items.get(code)

    def get_medicine(self, code: str) -> Optional[Medicine]:
        """按编码获取药品"""
        return self.medicines.get(code)

    def get_service_facility(self, code: str) -> Optional[ServiceFacility]:
        """按编码获取服务设施"""
        return self.service_facilities.get(code)

    def get_by_code(self, code: str) -> Optional[Union[MedicalItem, Medicine, ServiceFacility]]:
        """
        按编码获取任意类型项目

        Returns:
            MedicalItem、Medicine 或 ServiceFacility
        """
        item = self.medical_items.get(code)
        if item:
            return item
        medicine = self.medicines.get(code)
        if medicine:
            return medicine
        return self.service_facilities.get(code)

    def search_medical_items(self, keyword: str) -> List[MedicalItem]:
        """搜索诊疗项目（按名称）"""
        keyword = keyword.lower()
        codes = set()
        for idx_key, idx_codes in self._medical_items_by_name.items():
            if keyword in idx_key:
                codes.update(idx_codes)
        return [self.medical_items[code] for code in codes]

    def search_medicines(self, keyword: str) -> List[Medicine]:
        """搜索药品（按名称）"""
        keyword = keyword.lower()
        codes = set()
        for idx_key, idx_codes in self._medicines_by_name.items():
            if keyword in idx_key:
                codes.update(idx_codes)
        return [self.medicines[code] for code in codes]

    def search_service_facilities(self, keyword: str) -> List[ServiceFacility]:
        """搜索服务设施（按名称）"""
        keyword = keyword.lower()
        codes = set()
        for idx_key, idx_codes in self._facilities_by_name.items():
            if keyword in idx_key:
                codes.update(idx_codes)
        return [self.service_facilities[code] for code in codes]

    def get_medical_items_by_category(self, category: ItemCategory) -> List[MedicalItem]:
        """按类别获取诊疗项目"""
        return [item for item in self.medical_items.values() if item.category == category]

    def get_medicines_by_category(self, category: MedicineCategory) -> List[Medicine]:
        """按类别获取药品"""
        return [medicine for medicine in self.medicines.values() if medicine.category == category]

    def get_service_facilities_by_category(self, category: FacilityCategory) -> List[ServiceFacility]:
        """按类别获取服务设施"""
        return [facility for facility in self.service_facilities.values() if facility.category == category]

    def validate_expense(
        self,
        code: str,
        quantity: int,
        hospital_level: int,
        days: int = 1
    ) -> tuple[bool, str, Optional[Union[MedicalItem, Medicine, ServiceFacility]]]:
        """
        校验费用是否符合医保规定

        Args:
            code: 项目编码
            quantity: 数量（药品为数量，诊疗项目为次数）
            hospital_level: 医院级别（1/2/3）
            days: 天数（服务设施使用）

        Returns:
            (is_valid, reason, item): 是否有效、原因、项目对象
        """
        item = self.get_by_code(code)
        if not item:
            return False, f"未找到编码为 {code} 的医保项目", None

        # 根据类型进行校验
        if isinstance(item, MedicalItem):
            return item.validate_usage(quantity, hospital_level) + (item,)
        elif isinstance(item, Medicine):
            return item.validate_prescription(quantity, hospital_level) + (item,)
        elif isinstance(item, ServiceFacility):
            return item.validate_usage(days, hospital_level) + (item,)

        return False, "未知的项目类型", None

    def calculate_reimbursement(
        self,
        code: str,
        quantity: int = 1,
        hospital_level: int = 3
    ) -> Optional[dict]:
        """
        计算医保报销金额

        Returns:
            dict 包含 standard_amount, self_pay_amount, reimbursement_amount
        """
        item = self.get_by_code(code)
        if not item:
            return None

        if isinstance(item, (MedicalItem, Medicine, ServiceFacility)):
            standard_amount = item.standard_price * quantity
            reimbursement_amount = item.reimbursement_amount * quantity
            self_pay_amount = item.self_pay_amount * quantity

            return {
                "code": code,
                "name": item.name,
                "unit_price": item.standard_price,
                "quantity": quantity,
                "standard_amount": standard_amount,
                "reimbursement_amount": reimbursement_amount,
                "self_pay_amount": self_pay_amount,
                "reimbursement_rate": item.reimbursement_rate,
            }
        return None

    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            "medical_items": [item.to_dict() for item in self.medical_items.values()],
            "medicines": [medicine.to_dict() for medicine in self.medicines.values()],
            "service_facilities": [facility.to_dict() for facility in self.service_facilities.values()],
        }

    def to_json(self, indent: int = 2) -> str:
        """导出为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "MedicareCatalog":
        """从字典加载"""
        catalog = cls()

        # 加载诊疗项目
        for item_data in data.get("medical_items", []):
            item = MedicalItem.from_dict(item_data)
            catalog.add_medical_item(item)

        # 加载药品
        for medicine_data in data.get("medicines", []):
            medicine = Medicine.from_dict(medicine_data)
            catalog.add_medicine(medicine)

        # 加载服务设施
        for facility_data in data.get("service_facilities", []):
            facility = ServiceFacility.from_dict(facility_data)
            catalog.add_service_facility(facility)

        return catalog

    @classmethod
    def from_json(cls, json_str: str) -> "MedicareCatalog":
        """从JSON字符串加载"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load_from_file(cls, file_path: str) -> "MedicareCatalog":
        """从JSON文件加载"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_to_file(self, file_path: str) -> None:
        """保存到JSON文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    def summary(self) -> dict:
        """获取目录摘要"""
        return {
            "total_items": len(self.medical_items) + len(self.medicines) + len(self.service_facilities),
            "medical_items_count": len(self.medical_items),
            "medicines_count": len(self.medicines),
            "service_facilities_count": len(self.service_facilities),
            "categories": {
                "medical_items": list(set(item.category.value for item in self.medical_items.values())),
                "medicines": list(set(medicine.category.value for medicine in self.medicines.values())),
                "service_facilities": list(set(facility.category.value for facility in self.service_facilities.values())),
            },
        }
