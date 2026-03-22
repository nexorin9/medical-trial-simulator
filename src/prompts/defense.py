"""
DefensePrompt - 辩护方（医院说明）

扮演医院说明的角色，为费用进行辩护，生成"辩护词"
"""

from typing import List, Dict, Any
from .base import BaseTrialPrompt, TrialRole, TrialContext, TrialStatement


class DefensePrompt(BaseTrialPrompt):
    """
    辩护方 Prompt

    扮演医院说明的角色，为费用进行辩护，生成辩护词。
    类似于法律诉讼中的"被告律师"角色。
    """

    def __init__(self):
        super().__init__(TrialRole.DEFENSE)

    def _build_system_prompt(self) -> str:
        """
        构建辩护方系统 prompt

        扮演医院说明，为费用进行合理性辩护
        """
        return """你是医院医保办工作人员（辩护方），负责为医院申报的医疗费用进行解释和辩护。

## 角色定位
你扮演的是医院的"代言人"，代表医院的利益进行辩护。你的职责是：
1. 针对医保审核提出的问题进行解释
2. 提供合理的医学依据和临床理由
3. 说明费用的必要性和合理性
4. 引用相关诊疗规范和临床指南支持辩护

## 辩护策略
你应当从以下几个维度进行辩护：

### 1. 目录合规性辩护
- 说明项目/药品在医保目录内的依据
- 提供正确的医保编码
- 解释适应症与目录限定

### 2. 价格合理性辩护
- 说明收费符合物价标准
- 提供定价依据
- 解释加成政策的合理性

### 3. 数量必要性辩护
- 说明用量符合临床诊疗规范
- 提供医嘱和病例支持
- 解释个体差异导致的用量不同

### 4. 适应症合理性辩护
- 说明诊疗项目与诊断的关联性
- 提供药品使用的适应症依据
- 引用临床诊疗指南支持

### 5. 政策符合性辩护
- 说明符合医保政策限定
- 提供资质和准入材料
- 解释政策有效期内执行

## 输出格式
请按以下格式输出你的辩护结果：

### 【辩护词】

#### 一、案件概况
简要说明费用基本情况，针对起诉方的指控进行回应

#### 二、辩护事项（逐条回应）
对每条起诉指控，说明：
1. 被指控的费用项目
2. 辩护理由（医学/临床/政策依据）
3. 提供的证据或说明
4. 结论（是否合理）

#### 三、总结
总结辩护要点，说明费用的合理性和必要性

## 重要提醒
- 你必须为医院的收费行为进行合理辩护
- 每条辩护都需要有依据，不能无中生有
- 如果确实存在问题，也要诚实说明
- 语气要正式、严谨，体现专业性
- 即使费用完全合规，也要出具正式的辩护意见
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
            "请针对医保审核提出的问题，为医院费用进行辩护：",
            "",
            context.format_for_prompt(),
            "",
        ]

        # 如果有起诉方的指控，添加进去
        if context.previous_statements:
            prompt_parts.append("【起诉方指控】")
            for i, statement in enumerate(context.previous_statements):
                if statement.role == TrialRole.PROSECUTOR:
                    prompt_parts.append(statement.content)
                    break
            prompt_parts.append("")

        prompt_parts.extend([
            "请作为医院医保办（辩护方）进行辩护：",
            "1. 逐条回应起诉方提出的每项指控",
            "2. 提供合理的解释和医学依据",
            "3. 说明费用产生的临床必要性",
            "4. 引用相关诊疗规范和临床指南",
            "",
            "请输出详细的【辩护词】，逐条回应所有指控。",
        ])

        return "\n".join(prompt_parts)

    def generate_defense(
        self,
        expense: Dict[str, Any],
        accusation: Dict[str, Any],
        catalog: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        生成单个费用的辩护

        Args:
            expense: 费用明细
            accusation: 起诉指控
            catalog: 医保目录信息

        Returns:
            辩护结果
        """
        defenses = []
        accusation_type = accusation.get("type", "")

        # 根据不同指控类型进行针对性辩护
        if "目录外" in accusation_type:
            # 目录外项目辩护
            item_code = expense.get("item_code", "")
            if catalog and item_code:
                for item in catalog.get("items", []):
                    if item.get("code") == item_code:
                        defenses.append({
                            "type": "目录符合性",
                            "description": f"项目编码 {item_code} 已在医保目录内：{item.get('name')}",
                            "evidence": f"医保目录记录：{item.get('category')} - {item.get('name')}",
                            "strength": "strong",
                        })
                        break
            else:
                defenses.append({
                    "type": "目录符合性",
                    "description": "该项目属于新版医保目录调整范围，正在申报中",
                    "evidence": "医保目录动态调整机制",
                    "strength": "medium",
                })

        elif "超标准" in accusation_type:
            # 超标准收费辩护
            defenses.append({
                "type": "价格合理性",
                "description": "收费标准符合当地医疗服务价格政策",
                "evidence": "当地医疗服务价格文件",
                "strength": "medium",
            })

        elif "超量" in accusation_type:
            # 超量收费辩护
            defenses.append({
                "type": "数量必要性",
                "description": "用量基于患者具体病情和临床需求",
                "evidence": "长期医嘱、病例记录、个体差异说明",
                "strength": "medium",
            })

        elif "无适应症" in accusation_type or "适应症" in accusation_type:
            # 适应症辩护
            defenses.append({
                "type": "适应症合理性",
                "description": "药品/诊疗项目使用符合临床诊疗指南",
                "evidence": "临床诊疗指南、药品说明书适应症",
                "strength": "medium",
            })

        elif "拒付" in accusation_type or "不合理" in accusation_type:
            # 拒付/不合理辩护
            defenses.append({
                "type": "费用合理性",
                "description": "费用产生基于实际诊疗需要",
                "evidence": "医嘱单、收费清单、病例记录",
                "strength": "medium",
            })

        else:
            # 通用辩护
            defenses.append({
                "type": "综合合理性",
                "description": "费用产生符合诊疗规范和政策要求",
                "evidence": "相关政策文件和诊疗规范",
                "strength": "weak",
            })

        return {
            "expense_id": expense.get("id", ""),
            "accusation": accusation,
            "defenses": defenses,
            "conclusion": self._generate_conclusion(defenses),
        }

    def _generate_conclusion(self, defenses: List[Dict[str, Any]]) -> str:
        """
        生成辩护结论

        Args:
            defenses: 辩护列表

        Returns:
            结论文本
        """
        if not defenses:
            return "未能找到有效辩护依据"

        strong_count = sum(1 for d in defenses if d.get("strength") == "strong")
        medium_count = sum(1 for d in defenses if d.get("strength") == "medium")
        weak_count = sum(1 for d in defenses if d.get("strength") == "weak")

        if strong_count > 0:
            return "费用具有充分的合理性依据，辩护成立"
        elif medium_count > 0:
            return "费用具有一定合理性，建议进一步提供补充材料"
        else:
            return "费用合理性存在争议，需要进一步核实"

    def create_defense_plea(self, context: TrialContext) -> TrialStatement:
        """
        创建辩护词

        Args:
            context: 审判上下文

        Returns:
            辩护陈述
        """
        content = self.build_user_prompt(context)
        statement = self.parse_response(content)
        return statement

    def generate_rebuttal_points(self, accusations: List[Dict[str, Any]]) -> List[str]:
        """
        生成反驳要点

        Args:
            accusations: 指控列表

        Returns:
            反驳要点列表
        """
        rebuttal_map = {
            "目录外项目": [
                "该项目已纳入医保目录",
                "项目编码已更新",
                "属于医保目录动态调整范围",
            ],
            "超标准收费": [
                "收费符合当地物价标准",
                "具有物价部门批文",
                "符合医疗服务价格政策",
            ],
            "超量收费": [
                "基于患者病情需要",
                "符合临床诊疗规范",
                "有医嘱和病例支持",
            ],
            "无适应症": [
                "符合药品说明书适应症",
                "符合临床诊疗指南",
                "经科室会诊决定",
            ],
            "重复收费": [
                "不存在重复计费",
                "项目内涵不同",
                "符合收费标准",
            ],
            "分解收费": [
                "未分解收费",
                "符合项目内涵",
                "符合计价单位",
            ],
            "串换项目": [
                "不存在串换行为",
                "按实际项目收费",
                "有收费明细支持",
            ],
            "过度诊疗": [
                "诊疗符合病情需要",
                "遵循临床路径",
                "有检查指征",
            ],
        }

        rebuttal_points = []
        for acc in accusations:
            acc_type = acc.get("type", "")
            for key, points in rebuttal_map.items():
                if key in acc_type:
                    rebuttal_points.extend(points)
                    break

        return list(set(rebuttal_points))


class HospitalDefenseHelper:
    """
    医院辩护助手

    提供辩护所需的常用依据和参考
    """

    # 常用辩护依据
    CLINICAL_GUIDELINES = [
        "《临床诊疗指南》",
        "《临床路径》",
        "《药品说明书》",
        "《临床用药须知》",
    ]

    POLICY_REFERENCES = [
        "《基本医疗保险药品目录》",
        "《诊疗项目目录》",
        "《医疗服务设施目录》",
        "《医疗服务价格项目规范》",
        "《医保诊疗项目支付限定》",
    ]

    @staticmethod
    def get_defense_template(accusation_type: str) -> Dict[str, str]:
        """
        根据指控类型获取辩护模板

        Args:
            accusation_type: 指控类型

        Returns:
            辩护模板
        """
        templates = {
            "目录外项目": {
                "title": "目录合规性辩护",
                "points": [
                    "该项目属于医保目录内项目",
                    "医保编码已正确匹配",
                    "符合目录支付条件",
                ],
            },
            "超标准收费": {
                "title": "价格合理性辩护",
                "points": [
                    "收费标准符合物价政策",
                    "具有定价依据文件",
                    "未超过最高限价",
                ],
            },
            "超量收费": {
                "title": "数量必要性辩护",
                "points": [
                    "用量符合诊疗规范",
                    "基于患者病情需要",
                    "有医嘱和病例支持",
                ],
            },
            "无适应症": {
                "title": "适应症合理性辩护",
                "points": [
                    "符合药品适应症",
                    "符合临床诊疗指南",
                    "经医生专业判断",
                ],
            },
            "重复收费": {
                "title": "非重复收费辩护",
                "points": [
                    "项目内涵不同",
                    "未重复计费",
                    "符合计价规则",
                ],
            },
        }
        return templates.get(accusation_type, {
            "title": "综合辩护",
            "points": ["费用合理，符合政策要求"],
        })

    @staticmethod
    def get_evidence_checklist() -> List[str]:
        """
        获取证据清单

        Returns:
            证据清单
        """
        return [
            "医嘱单",
            "收费明细清单",
            "病例记录",
            "检查报告",
            "药品发放记录",
            "医保目录对照表",
            "物价部门批文",
            "临床路径记录",
        ]
