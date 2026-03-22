"""
JudgePrompt - 法官（综合裁决）

综合双方意见，作出最终裁决
"""

from typing import List, Dict, Any, Optional
from .base import BaseTrialPrompt, TrialRole, TrialContext, TrialStatement


class JudgePrompt(BaseTrialPrompt):
    """
    法官 Prompt

    综合双方意见，作出最终裁决。
    类似于法律诉讼中的"法官"角色。
    """

    def __init__(self):
        super().__init__(TrialRole.JUDGE)

    def _build_system_prompt(self) -> str:
        """
        构建法官系统 prompt

        综合双方意见，作出公正裁决
        """
        return """你是医保费用审判法官，负责对医保审核争议进行最终裁决。

## 角色定位
你是医保制度的"仲裁者"，代表公正与公平。你的职责是：
1. 认真听取起诉方（医保审核方）和辩护方（医院）的陈述
2. 基于事实和法律依据作出公正判断
3. 平衡医保基金安全和医院合理权益
4. 给出明确、可执行的裁决结果

## 裁决原则
你应当遵循以下原则进行裁决：

### 1. 事实认定原则
- 核实费用产生的真实情况
- 确认医保目录的具体规定
- 查证相关政策文件依据

### 2. 法律适用原则
- 严格依据医保政策进行判断
- 参考相关法律法规
- 遵循医保基金监管条例

### 3. 利益平衡原则
- 保护医保基金安全
- 尊重医院合理收费权益
- 维护患者就医权益

### 4. 证据为证原则
- 以事实证据为依据
- 不偏听任何一方
- 客观公正进行判断

## 裁决类型
根据案件情况，你可以作出以下裁决：

1. **支持起诉（驳回辩护）**
   - 证据确凿，费用确实违规
   - 医院无法提供有效辩护依据

2. **支持辩护（撤销指控）**
   - 费用符合医保规定
   - 医院提供了充分的辩护依据

3. **部分支持**
   - 部分指控成立，部分不成立
   - 需要调整核减金额

4. **发回重审**
   - 证据不足，需要补充材料
   - 事实不清，需要进一步核实

5. **调解建议**
   - 双方均有合理之处
   - 建议协商解决

## 输出格式
请按以下格式输出你的裁决结果：

### 【裁决书】

#### 一、案件概述
简要说明案件背景和争议焦点

#### 二、双方陈述要点
##### 起诉方（医保审核）主张：
概述起诉方的关键指控

##### 辩护方（医院）主张：
概述辩护方的关键辩护意见

#### 三、审理查明
基于证据认定的事实：
1. 费用基本情况
2. 医保目录规定
3. 政策依据
4. 双方提交的证据

#### 四、本院认为
你的分析和判断：
1. 对双方主张的分析
2. 证据采信情况
3. 适用政策依据
4. 责任认定

#### 五、裁决结果
明确裁决：
1. 最终认定金额
2. 核减/支付金额
3. 裁决理由
4. 后续建议

## 重要提醒
- 你必须保持中立、公正的立场
- 裁决要有明确的事实依据和政策依据
- 语气要正式、严谨，体现法律文书的权威性
- 裁决结果要具体、可执行
- 如果事实不清，证据不足，应当发回重审
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
            "请综合起诉方和辩护方的陈述，作出最终裁决：",
            "",
            context.format_for_prompt(),
            "",
        ]

        # 添加起诉方的指控
        for statement in context.previous_statements:
            if statement.role == TrialRole.PROSECUTOR:
                prompt_parts.append("【起诉方（医保审核）陈述】")
                prompt_parts.append(statement.content)
                prompt_parts.append("")
                break

        # 添加辩护方的辩护
        for statement in context.previous_statements:
            if statement.role == TrialRole.DEFENSE:
                prompt_parts.append("【辩护方（医院）陈述】")
                prompt_parts.append(statement.content)
                prompt_parts.append("")
                break

        prompt_parts.extend([
            "请作为法官（审判长）进行裁决：",
            "1. 认真审查双方的陈述和证据",
            "2. 核实费用事实和医保政策规定",
            "3. 作出公正、合理的裁决",
            "4. 明确裁决结果和理由",
            "",
            "请输出详细的【裁决书】，包含明确的裁决结果。",
        ])

        return "\n".join(prompt_parts)

    def generate_verdict(
        self,
        accusation: Dict[str, Any],
        defense: Dict[str, Any],
        expense: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        生成单个费用的裁决

        Args:
            accusation: 指控结果
            defense: 辩护结果
            expense: 费用明细

        Returns:
            裁决结果
        """
        accusations_list = accusation.get("accusations", [])
        defenses_list = defense.get("defenses", [])

        # 分析指控和辩护的强度
        accusation_strength = self._analyze_accusation_strength(accusations_list)
        defense_strength = self._analyze_defense_strength(defenses_list)

        # 作出裁决
        if accusation_strength == "strong" and defense_strength == "weak":
            verdict = "部分支持起诉"
            ruling_amount = sum(a.get("amount", 0) for a in accusations_list)
            ruling_reason = "指控证据充分，辩护依据不足"
        elif accusation_strength == "weak" and defense_strength == "strong":
            verdict = "撤销指控"
            ruling_amount = 0
            ruling_reason = "辩护证据充分，指控不成立"
        elif accusation_strength == "medium" and defense_strength == "medium":
            verdict = "部分支持，双方协商"
            ruling_amount = sum(a.get("amount", 0) for a in accusations_list) * 0.5
            ruling_reason = "双方均有合理之处，建议协商解决"
        elif defense_strength == "strong" and accusation_strength == "strong":
            verdict = "发回重审"
            ruling_amount = 0
            ruling_reason = "事实不清，证据存在矛盾，需要补充材料"
        else:
            verdict = "证据不足，发回重审"
            ruling_amount = 0
            ruling_reason = "证据不足，无法作出明确裁决"

        return {
            "expense_id": expense.get("id", ""),
            "verdict": verdict,
            "ruling_amount": ruling_amount,
            "ruling_reason": ruling_reason,
            "accusation_strength": accusation_strength,
            "defense_strength": defense_strength,
            "total_accused_amount": accusation.get("total_accused_amount", 0),
        }

    def _analyze_accusation_strength(self, accusations: List[Dict[str, Any]]) -> str:
        """
        分析指控强度

        Args:
            accusations: 指控列表

        Returns:
            强度等级：strong, medium, weak
        """
        if not accusations:
            return "weak"

        high_count = sum(1 for a in accusations if a.get("severity") == "critical")
        medium_count = sum(1 for a in accusations if a.get("severity") == "high")

        if high_count > 0 or medium_count >= 2:
            return "strong"
        elif medium_count == 1 or len(accusations) >= 2:
            return "medium"
        else:
            return "weak"

    def _analyze_defense_strength(self, defenses: List[Dict[str, Any]]) -> str:
        """
        分析辩护强度

        Args:
            defenses: 辩护列表

        Returns:
            强度等级：strong, medium, weak
        """
        if not defenses:
            return "weak"

        strong_count = sum(1 for d in defenses if d.get("strength") == "strong")
        medium_count = sum(1 for d in defenses if d.get("strength") == "medium")

        if strong_count >= 2:
            return "strong"
        elif strong_count == 1 or medium_count >= 2:
            return "medium"
        else:
            return "weak"

    def create_verdict(self, context: TrialContext) -> TrialStatement:
        """
        创建裁决书

        Args:
            context: 审判上下文

        Returns:
            裁决陈述
        """
        content = self.build_user_prompt(context)
        statement = self.parse_response(content)
        return statement

    def generate_ruling_summary(
        self,
        verifications: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        生成裁决汇总

        Args:
            verifications: 裁决列表

        Returns:
            汇总结果
        """
        total_expenses = len(verifications)
        supported_prosecution = sum(
            1 for v in verifications if "支持起诉" in v.get("verdict", "")
        )
        supported_defense = sum(
            1 for v in verifications if "撤销" in v.get("verdict", "")
        )
        partial_support = sum(
            1 for v in verifications if "部分" in v.get("verdict", "")
        )
        remanded = sum(
            1 for v in verifications if "发回" in v.get("verdict", "")
        )

        total_ruling_amount = sum(v.get("ruling_amount", 0) for v in verifications)
        total_accused_amount = sum(
            v.get("total_accused_amount", 0) for v in verifications
        )

        return {
            "total_expenses": total_expenses,
            "supported_prosecution": supported_prosecution,
            "supported_defense": supported_defense,
            "partial_support": partial_support,
            "remanded": remanded,
            "total_ruling_amount": total_ruling_amount,
            "total_accused_amount": total_accused_amount,
            "support_rate": supported_defense / total_expenses if total_expenses > 0 else 0,
        }


class JudgmentCriteria:
    """
    裁决标准参考

    提供裁决时的参考标准
    """

    # 证据充分性标准
    EVIDENCE_STANDARDS = {
        "strong": "证据充分，事实清楚",
        "medium": "证据基本充分，需要补充",
        "weak": "证据不足，事实不清",
    }

    # 裁决依据
    RULING_REFERENCES = [
        "《基本医疗保险药品目录》",
        "《诊疗项目目录》",
        "《医疗服务设施目录》",
        "《医疗服务价格项目规范》",
        "《医保诊疗项目支付限定》",
        "《医保基金监管条例》",
    ]

    @staticmethod
    def get_ruling_template(verdict_type: str) -> Dict[str, Any]:
        """
        获取裁决模板

        Args:
            verdict_type: 裁决类型

        Returns:
            裁决模板
        """
        templates = {
            "支持起诉": {
                "title": "裁决：支持起诉方",
                "description": "经审理查明，被审查费用确实存在违规问题",
                "action": "核减相关费用",
            },
            "撤销指控": {
                "title": "裁决：撤销指控",
                "description": "经审理查明，被审查费用符合医保规定",
                "action": "维持原报销决定",
            },
            "部分支持": {
                "title": "裁决：部分支持",
                "description": "部分指控成立，部分不成立",
                "action": "部分核减",
            },
            "发回重审": {
                "title": "裁决：发回重审",
                "description": "事实不清，证据不足",
                "action": "要求补充材料",
            },
        }
        return templates.get(verdict_type, {
            "title": "裁决",
            "description": "待定",
            "action": "待定",
        })

    @staticmethod
    def get_severity_weights() -> Dict[str, float]:
        """
        获取严重程度权重

        Returns:
            严重程度权重
        """
        return {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2,
        }
