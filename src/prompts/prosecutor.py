"""
ProsecutorPrompt - 起诉方（医保审核规则）

扮演医保审核规则的角色，逐条指出费用不合规之处，生成"起诉状"
"""

from typing import List, Dict, Any
from .base import BaseTrialPrompt, TrialRole, TrialContext, TrialStatement


class ProsecutorPrompt(BaseTrialPrompt):
    """
    起诉方 Prompt

    扮演医保审核规则，逐条指出费用不合规之处，生成起诉状。
    类似于法律诉讼中的"原告律师"角色。
    """

    def __init__(self):
        super().__init__(TrialRole.PROSECUTOR)

    def _build_system_prompt(self) -> str:
        """
        构建起诉方系统 prompt

        扮演医保审核规则执行者，列举费用问题
        """
        return """你是医保费用审核官（起诉方），负责审查医院申报的医疗费用是否符合医保规定。

## 角色定位
你扮演的是医保制度的"守护者"，代表医保基金的利益。你的职责是：
1. 严格依据医保政策和目录进行审核
2. 逐条审查每项费用的合规性
3. 找出所有不符合报销条件的问题
4. 提供明确的法律/政策依据

## 审核标准
你应当从以下几个维度进行审查：

### 1. 目录合规性
- 项目/药品是否在医保目录内
- 是否属于医保支付范围
- 是否有对应的医保编码

### 2. 价格合规性
- 收费是否超过目录定价
- 是否存在加价行为
- 价格是否符合物价标准

### 3. 数量合规性
- 用量是否符合诊疗规范
- 是否存在超量收费
- 是否存在重复收费

### 4. 适应症合规性
- 诊疗项目是否符合诊断
- 药品使用是否有适应症
- 是否存在无指征用药/检查

### 5. 政策合规性
- 是否符合医保政策限定
- 医院是否具有相应资质
- 是否在政策有效期内

### 6. 完整性审查
- 是否有遗漏的必需材料
- 病例记录是否完整
- 医嘱是否规范

## 输出格式
请按以下格式输出你的审查结果：

### 【起诉状】

#### 一、案件概况
简要说明被审查的费用概况

#### 二、违规事项（逐条列出）
对每条违规事项，说明：
1. 费用项目名称
2. 违规类型（目录/价格/数量/适应症/政策/其他）
3. 违规内容具体说明
4. 涉及金额
5. 政策依据

#### 三、结论
总结违规事实，计算总涉及金额

## 重要提醒
- 你必须扮演严格的审核者，找出所有可能的问题
- 每条指控都需要有明确的依据
- 语气要正式、严谨，体现法律文书的风格
- 如果费用确实没有问题，也要明确说明"未发现违规"
"""

    def build_user_prompt(self, context: TrialContext) -> str:
        """
        构建用户 prompt

        Args:
            context: 审判上下文

        Returns:
            用户 prompt 文本
        """
        prompt_parts = [
            "请对以下医疗费用进行严格审查，列出所有不符合医保规定的问题：",
            "",
            context.format_for_prompt(),
            "",
            "请作为医保审核官（起诉方）进行审查：",
            "1. 逐项检查每笔费用是否符合医保目录",
            "2. 检查收费价格是否超标",
            "3. 检查数量是否合理",
            "4. 检查是否符合适应症要求",
            "5. 检查是否符合医保政策限定",
            "",
            "请输出详细的【起诉状】，逐条列出所有违规事项。",
        ]

        return "\n".join(prompt_parts)

    def generate_accusation(
        self,
        expense: Dict[str, Any],
        diff: Dict[str, Any],
        catalog: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        生成单个费用的指控

        Args:
            expense: 费用明细
            diff: 结算差异
            catalog: 医保目录信息

        Returns:
            指控结果
        """
        accusations = []

        # 检查是否在目录内
        item_code = expense.get("item_code", "")
        if item_code and catalog:
            catalog_items = catalog.get("items", [])
            if not any(item.get("code") == item_code for item in catalog_items):
                accusations.append({
                    "type": "目录外项目",
                    "description": f"项目编码 {item_code} 不在医保目录内",
                    "amount": expense.get("total_amount", 0),
                    "severity": "high",
                })

        # 检查价格
        unit_price = expense.get("unit_price", 0)
        if catalog and item_code:
            for item in catalog.get("items", []):
                if item.get("code") == item_code:
                    standard_price = item.get("price", 0)
                    if standard_price and unit_price > standard_price:
                        accusations.append({
                            "type": "超标准收费",
                            "description": f"单价 ¥{unit_price:.2f} 超过标准 ¥{standard_price:.2f}",
                            "amount": (unit_price - standard_price) * expense.get("quantity", 1),
                            "severity": "high",
                        })

        # 检查差异信息
        if diff:
            diff_type = diff.get("diff_type", "")
            diff_reason = diff.get("diff_reason", "")
            diff_amount = diff.get("diff_amount", 0)

            if diff_type in ["exclusion", "reasonableness"]:
                accusations.append({
                    "type": "拒付/不合理",
                    "description": f"差异原因: {diff_reason}",
                    "amount": diff_amount,
                    "severity": "critical",
                })
            elif diff_type == "over_limit":
                accusations.append({
                    "type": "超限",
                    "description": f"超出医保限定: {diff.get('description', '')}",
                    "amount": diff_amount,
                    "severity": "high",
                })

        return {
            "expense_id": expense.get("id", ""),
            "accusations": accusations,
            "total_accused_amount": sum(a["amount"] for a in accusations),
        }

    def create_indictment(self, context: TrialContext) -> TrialStatement:
        """
        创建起诉状

        Args:
            context: 审判上下文

        Returns:
            起诉陈述
        """
        content = self.build_user_prompt(context)
        statement = self.parse_response(content)
        return statement


class MedicalPolicyReference:
    """
    医保政策引用助手

    提供常用医保政策引用
    """

    # 基本医疗保险药品目录
    MEDICINE_CATALOG_REFERENCE = "《国家基本医疗保险药品目录》"

    # 诊疗项目目录
    MEDICAL_ITEM_CATALOG_REFERENCE = "《国家基本医疗保险诊疗项目目录》"

    # 服务设施目录
    FACILITY_CATALOG_REFERENCE = "《国家基本医疗保险医疗服务设施目录》"

    # 医保政策
    BASIC_INSURANCE_REFERENCE = "《基本医疗保险药品目录》《诊疗项目目录》《医疗服务设施目录》"

    @staticmethod
    def get_reference_for_type(expense_type: str) -> str:
        """
        根据费用类型获取对应的政策引用

        Args:
            expense_type: 费用类型

        Returns:
            政策引用文本
        """
        type_map = {
            "medicine": MedicalPolicyReference.MEDICINE_CATALOG_REFERENCE,
            "medical_item": MedicalPolicyReference.MEDICAL_ITEM_CATALOG_REFERENCE,
            "service_facility": MedicalPolicyReference.FACILITY_CATALOG_REFERENCE,
        }
        return type_map.get(expense_type, MedicalPolicyReference.BASIC_INSURANCE_REFERENCE)

    @staticmethod
    def get_common_violations() -> List[Dict[str, str]]:
        """
        获取常见违规类型

        Returns:
            违规类型列表
        """
        return [
            {
                "type": "目录外项目收费",
                "description": "使用了不在医保目录内的项目或药品",
                "reference": "《基本医疗保险药品目录》《诊疗项目目录》",
            },
            {
                "type": "超标准收费",
                "description": "收费标准超过医保目录定价",
                "reference": "《医疗服务价格项目规范》",
            },
            {
                "type": "超量收费",
                "description": "数量超过医保限定的最大用量",
                "reference": "《医保诊疗项目支付限定》",
            },
            {
                "type": "无适应症用药",
                "description": "药品使用无相应诊断适应症",
                "reference": "《药品说明书》《临床诊疗指南》",
            },
            {
                "type": "重复收费",
                "description": "同一项目多次计费",
                "reference": "《医疗服务价格项目规范》",
            },
            {
                "type": "分解收费",
                "description": "将一个项目分解为多个项目收费",
                "reference": "《医疗服务价格项目规范》",
            },
            {
                "type": "串换项目",
                "description": "将自费项目串换为医保目录内项目",
                "reference": "《医保基金监管条例》",
            },
            {
                "type": "过度诊疗",
                "description": "开展与病情无关的检查或治疗",
                "reference": "《临床诊疗指南》",
            },
        ]
