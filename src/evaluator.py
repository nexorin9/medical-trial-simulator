"""
医疗记录评估器模块
定义病历质量评估的多个维度和评分标准
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class EvaluationDimension(Enum):
    """评估维度枚举"""
    COMPLETENESS = "completeness"           # 完整性
    LOGICAL_CONSISTENCY = "logical_consistency"  # 逻辑一致性
    SPECIFICATION_COMPLIANCE = "specification_compliance"  # 规范符合度
    EVIDENCE_SUPPORT = "evidence_support"    # 证据支持度
    TIMELINE_ACCURACY = "timeline_accuracy"  # 时间线准确性


@dataclass
class DimensionScore:
    """单个评估维度的评分"""
    dimension: str
    score: float  # 0-10
    max_score: float = 10.0
    details: str = ""
    issues: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "max_score": self.max_score,
            "details": self.details,
            "issues": self.issues,
            "strengths": self.strengths
        }


@dataclass
class EvaluationResult:
    """完整评估结果"""
    overall_score: float  # 综合评分 0-10
    dimension_scores: List[DimensionScore]
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "dimension_scores": [ds.to_dict() for ds in self.dimension_scores],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "metadata": self.metadata
        }


class MedicalRecordEvaluator:
    """
    病历质量评估器

    评估维度说明：
    1. 完整性 - 病历各项内容是否完整
    2. 逻辑一致性 - 诊断、治疗、检查等是否逻辑一致
    3. 规范符合度 - 是否符合病历书写规范
    4. 证据支持度 - 诊疗措施是否有充分证据支持
    5. 时间线准确性 - 时间记录是否准确、合理
    """

    # 各维度权重
    DIMENSION_WEIGHTS = {
        EvaluationDimension.COMPLETENESS: 0.25,
        EvaluationDimension.LOGICAL_CONSISTENCY: 0.25,
        EvaluationDimension.SPECIFICATION_COMPLIANCE: 0.20,
        EvaluationDimension.EVIDENCE_SUPPORT: 0.15,
        EvaluationDimension.TIMELINE_ACCURACY: 0.15,
    }

    # 维度说明
    DIMENSION_DESCRIPTIONS = {
        EvaluationDimension.COMPLETENESS: {
            "name": "完整性",
            "description": "评估病历是否包含所有必要的内容，包括：主诉、现病史、既往史、体格检查、辅助检查、诊断、治疗方案、医嘱等关键部分。",
            "check_points": [
                "基本信息是否完整（姓名、年龄、性别、住院号等）",
                "主诉是否清晰明确",
                "现病史是否详细记录发病过程",
                "既往史、个人史、家族史是否记录",
                "体格检查是否完整",
                "辅助检查是否齐全",
                "诊断是否明确",
                "治疗方案和医嘱是否完整"
            ]
        },
        EvaluationDimension.LOGICAL_CONSISTENCY: {
            "name": "逻辑一致性",
            "description": "评估病历中各个部分之间是否存在逻辑矛盾，包括诊断与症状、检查结果与诊断、治疗方案与诊断等的一致性。",
            "check_points": [
                "诊断与症状是否匹配",
                "检查结果与诊断是否一致",
                "治疗方案是否符合诊断",
                "用药方案是否合理",
                "病程记录是否连贯",
                "前后记录是否存在矛盾"
            ]
        },
        EvaluationDimension.SPECIFICATION_COMPLIANCE: {
            "name": "规范符合度",
            "description": "评估病历书写是否符合医疗机构病历书写规范，包括格式、内容、签名等方面的合规性。",
            "check_points": [
                "格式是否符合规范",
                "术语使用是否规范",
                "是否使用医学专业缩写（如规范允许）",
                "签名和时间是否完整",
                "修改是否符合规范",
                "是否使用蓝黑墨水或黑色签字笔（纸质病历）"
            ]
        },
        EvaluationDimension.EVIDENCE_SUPPORT: {
            "name": "证据支持度",
            "description": "评估诊疗措施是否有充分的证据支持，包括检查、诊断、治疗方案等是否有相应的检查结果或临床依据。",
            "check_points": [
                "诊断是否有检查结果支持",
                "治疗方案是否有依据",
                "用药是否有适应症",
                "检查项目是否有针对性",
                "会诊意见是否被采纳及说明理由",
                "特殊检查/治疗是否有知情同意"
            ]
        },
        EvaluationDimension.TIMELINE_ACCURACY: {
            "name": "时间线准确性",
            "description": "评估病历中时间记录的准确性，包括入院时间、手术时间、查房时间、检查时间等是否合理、准确。",
            "check_points": [
                "时间顺序是否合理",
                "关键时间点是否记录准确",
                "时间逻辑是否一致",
                "时效性记录是否及时",
                "抢救时间记录是否准确",
                "会诊、手术时间是否准确"
            ]
        }
    }

    def __init__(self):
        self.dimensions = list(EvaluationDimension)

    def get_dimension_description(self, dimension: EvaluationDimension) -> Dict[str, str]:
        """获取评估维度的详细说明"""
        return self.DIMENSION_DESCRIPTIONS.get(dimension, {})

    def get_all_dimensions_description(self) -> Dict[str, Dict[str, str]]:
        """获取所有评估维度的说明"""
        return self.DIMENSION_DESCRIPTIONS

    def create_prompt_for_dimension(
        self,
        medical_record: str,
        dimension: EvaluationDimension
    ) -> str:
        """为特定评估维度创建评估 Prompt"""
        dim_info = self.DIMENSION_DESCRIPTIONS.get(dimension, {})
        name = dim_info.get("name", dimension.value)
        description = dim_info.get("description", "")
        check_points = dim_info.get("check_points", [])

        check_points_text = "\n".join([f"  - {cp}" for cp in check_points])

        prompt = f"""你是一位资深的医疗质控专家。请根据以下病历内容，对病历的「{name}」维度进行评估。

## 评估维度说明
{description}

## 评估要点
{check_points_text}

## 待评估病历
---
{medical_record}
---

## 输出要求
请以 JSON 格式输出评估结果，格式如下：
{{
    "score": <评分 0-10>,
    "details": "<详细说明>",
    "issues": ["问题1", "问题2", ...],
    "strengths": ["优点1", "优点2", ...]
}}

请只输出 JSON，不要输出其他内容。"""
        return prompt

    def parse_dimension_result(self, result_text: str) -> Optional[DimensionScore]:
        """解析 LLM 返回的评估结果"""
        try:
            # 尝试提取 JSON
            data = json.loads(result_text)

            dimension = data.get("dimension", "")
            score = float(data.get("score", 5.0))
            details = data.get("details", "")
            issues = data.get("issues", [])
            strengths = data.get("strengths", [])

            # 确保 score 在有效范围内
            score = max(0, min(10, score))

            return DimensionScore(
                dimension=dimension,
                score=score,
                details=details,
                issues=issues,
                strengths=strengths
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # 解析失败，返回默认评分
            return None

    def calculate_overall_score(
        self,
        dimension_scores: List[DimensionScore]
    ) -> float:
        """根据各维度评分计算综合评分"""
        if not dimension_scores:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for ds in dimension_scores:
            # 找到对应的权重
            for dim_enum in self.dimensions:
                if dim_enum.value == ds.dimension:
                    weight = self.DIMENSION_WEIGHTS.get(dim_enum, 0.2)
                    weighted_sum += ds.score * weight
                    total_weight += weight
                    break

        if total_weight > 0:
            return round(weighted_sum / total_weight, 2)
        return round(sum(ds.score for ds in dimension_scores) / len(dimension_scores), 2)

    def generate_summary(
        self,
        dimension_scores: List[DimensionScore],
        overall_score: float
    ) -> str:
        """生成评估摘要"""
        # 找出主要问题和优点
        issues_by_dimension = {}
        strengths_by_dimension = {}

        for ds in dimension_scores:
            if ds.issues:
                issues_by_dimension[ds.dimension] = ds.issues
            if ds.strengths:
                strengths_by_dimension[ds.dimension] = ds.strengths

        # 构建摘要
        summary_parts = []

        if overall_score >= 8:
            summary_parts.append("该病历整体质量良好，各项评估指标表现优秀。")
        elif overall_score >= 6:
            summary_parts.append("该病历整体质量合格，存在少量需要改进的地方。")
        elif overall_score >= 4:
            summary_parts.append("该病历整体质量一般，存在多项需要改进的问题。")
        else:
            summary_parts.append("该病历存在严重质量问题，需要全面修订。")

        # 添加主要问题
        if issues_by_dimension:
            problem_dims = list(issues_by_dimension.keys())
            summary_parts.append(f"主要问题集中在：{', '.join(problem_dims)}。")

        return " ".join(summary_parts)

    def generate_recommendations(
        self,
        dimension_scores: List[DimensionScore]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        for ds in dimension_scores:
            if ds.score < 7:  # 低于7分的维度需要改进
                dimension_name = ds.dimension
                for dim_enum in self.dimensions:
                    if dim_enum.value == dimension_name:
                        dimension_name = self.DIMENSION_DESCRIPTIONS[dim_enum].get("name", dimension_name)
                        break

                recommendations.append(f"【{dimension_name}】需要改进：")
                for issue in ds.issues[:3]:  # 最多3条建议
                    recommendations.append(f"  - {issue}")

        return recommendations


class EvaluationReportGenerator:
    """评估报告生成器"""

    def __init__(self, evaluator: Optional[MedicalRecordEvaluator] = None):
        self.evaluator = evaluator or MedicalRecordEvaluator()

    def generate_text_report(
        self,
        result: EvaluationResult,
        include_details: bool = True
    ) -> str:
        """生成文本格式的评估报告"""
        lines = []

        # 标题
        lines.append("=" * 60)
        lines.append("          病历质量评估报告")
        lines.append("=" * 60)
        lines.append("")

        # 综合评分
        lines.append(f"【综合评分】{result.overall_score}/10")
        lines.append("")

        # 评分条
        score_bar = "★" * int(result.overall_score) + "☆" * (10 - int(result.overall_score))
        lines.append(f"评分: [{score_bar}]")
        lines.append("")

        # 各维度评分
        lines.append("【各维度评分】")
        lines.append("-" * 40)

        for ds in result.dimension_scores:
            dim_name = ds.dimension
            # 尝试获取中文名称
            for dim_enum in EvaluationDimension:
                if dim_enum.value == ds.dimension:
                    dim_name = self.evaluator.DIMENSION_DESCRIPTIONS[dim_enum].get("name", ds.dimension)
                    break

            bar = "▓" * int(ds.score) + "░" * (10 - int(ds.score))
            lines.append(f"  {dim_name}: {ds.score}/10 [{bar}]")

        lines.append("")

        # 摘要
        if result.summary:
            lines.append("【评估摘要】")
            lines.append(result.summary)
            lines.append("")

        # 详细问题和建议
        if include_details and result.recommendations:
            lines.append("【改进建议】")
            for rec in result.recommendations:
                lines.append(rec)
            lines.append("")

        # 元数据
        if result.metadata:
            lines.append("【评估信息】")
            for key, value in result.metadata.items():
                lines.append(f"  {key}: {value}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_markdown_report(
        self,
        result: EvaluationResult
    ) -> str:
        """生成 Markdown 格式的评估报告"""
        lines = []

        # 标题
        lines.append("# 病历质量评估报告\n")

        # 综合评分
        lines.append(f"## 综合评分: {result.overall_score}/10\n")

        # 评分进度条
        score_percentage = int(result.overall_score * 10)
        progress_bar = f"![score](https://progress-bar.dev/{score_percentage}?title=score&width=400)"
        lines.append(f"{progress_bar}\n")

        # 各维度评分表格
        lines.append("## 各维度评分\n")
        lines.append("| 评估维度 | 评分 | 详情 |")
        lines.append("|---------|------|------|")

        for ds in result.dimension_scores:
            dim_name = ds.dimension
            for dim_enum in EvaluationDimension:
                if dim_enum.value == ds.dimension:
                    dim_name = self.evaluator.DIMENSION_DESCRIPTIONS[dim_enum].get("name", ds.dimension)
                    break

            # 处理详情中的换行
            details = ds.details.replace("\n", " ")[:50] + "..." if len(ds.details) > 50 else ds.details

            lines.append(f"| {dim_name} | {ds.score}/10 | {details} |")

        lines.append("")

        # 摘要
        if result.summary:
            lines.append("## 评估摘要\n")
            lines.append(result.summary)
            lines.append("")

        # 问题列表
        all_issues = []
        for ds in result.dimension_scores:
            for issue in ds.issues:
                all_issues.append(f"- [{dim_name}] {issue}")

        if all_issues:
            lines.append("## 发现的问题\n")
            lines.extend(all_issues)
            lines.append("")

        # 优点列表
        all_strengths = []
        for ds in result.dimension_scores:
            for strength in ds.strengths:
                all_strengths.append(f"- {strength}")

        if all_strengths:
            lines.append("## 优点\n")
            lines.extend(all_strengths)
            lines.append("")

        # 改进建议
        if result.recommendations:
            lines.append("## 改进建议\n")
            lines.append("\n".join(result.recommendations))
            lines.append("")

        # 元数据
        if result.metadata:
            lines.append("---\n")
            lines.append("**评估信息**\n")
            for key, value in result.metadata.items():
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def generate_json_report(
        self,
        result: EvaluationResult,
        pretty: bool = True
    ) -> str:
        """生成 JSON 格式的评估报告"""
        if pretty:
            return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
        return json.dumps(result.to_dict(), ensure_ascii=False)

    def create_result_from_scores(
        self,
        dimension_scores: List[DimensionScore],
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """根据评分列表创建完整评估结果"""
        overall_score = self.evaluator.calculate_overall_score(dimension_scores)
        summary = self.evaluator.generate_summary(dimension_scores, overall_score)
        recommendations = self.evaluator.generate_recommendations(dimension_scores)

        return EvaluationResult(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            summary=summary,
            recommendations=recommendations,
            metadata=metadata or {}
        )


def get_dimension_info() -> Dict[str, Dict[str, str]]:
    """获取所有评估维度信息的便捷函数"""
    evaluator = MedicalRecordEvaluator()
    return evaluator.get_all_dimensions_description()


if __name__ == "__main__":
    # 测试代码
    evaluator = MedicalRecordEvaluator()

    print("评估维度说明:")
    print("-" * 40)

    for dim in EvaluationDimension:
        info = evaluator.get_dimension_description(dim)
        print(f"\n【{info.get('name', dim.value)}】")
        print(f"说明: {info.get('description', '')[:50]}...")
