"""
示例病历数据加载模块

提供加载示例病历的便捷函数
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_sample_cases_dir() -> Path:
    """获取示例病历目录路径"""
    current_dir = Path(__file__).parent.parent
    return current_dir / "data" / "sample_cases"


def load_sample_case(case_id: str) -> Optional[Dict[str, Any]]:
    """
    加载指定 ID 的示例病历

    Args:
        case_id: 病历 ID（如 'normal_001'）

    Returns:
        病历数据字典，若不存在则返回 None
    """
    sample_dir = get_sample_cases_dir()
    index_file = sample_dir / "index.json"

    if not index_file.exists():
        return None

    with open(index_file, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    for case in index_data.get("sample_cases", []):
        if case["id"] == case_id:
            case_file = sample_dir / case["file"]
            if case_file.exists():
                with open(case_file, "r", encoding="utf-8") as f:
                    return json.load(f)

    return None


def load_all_sample_cases() -> List[Dict[str, Any]]:
    """
    加载所有示例病历

    Returns:
        所有病历数据字典的列表
    """
    sample_dir = get_sample_cases_dir()
    index_file = sample_dir / "index.json"

    if not index_file.exists():
        return []

    with open(index_file, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    cases = []
    for case_info in index_data.get("sample_cases", []):
        case_file = sample_dir / case_info["file"]
        if case_file.exists():
            with open(case_file, "r", encoding="utf-8") as f:
                case_data = json.load(f)
                case_data["_meta"] = {
                    "id": case_info["id"],
                    "name": case_info["name"],
                    "type": case_info["type"],
                    "description": case_info["description"],
                    "characteristics": case_info.get("characteristics", []),
                    "expected_trial_result": case_info.get("expected_trial_result", "")
                }
                cases.append(case_data)

    return cases


def list_sample_cases() -> List[Dict[str, Any]]:
    """
    列出所有示例病历的基本信息

    Returns:
        病历基本信息列表
    """
    sample_dir = get_sample_cases_dir()
    index_file = sample_dir / "index.json"

    if not index_file.exists():
        return []

    with open(index_file, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    return index_data.get("sample_cases", [])


def get_sample_case_names() -> List[str]:
    """
    获取所有示例病历的名称列表

    Returns:
        病历名称列表
    """
    cases = list_sample_cases()
    return [case["name"] for case in cases]


def case_to_text(case_data: Dict[str, Any]) -> str:
    """
    将病历数据转换为文本格式（用于审判）

    Args:
        case_data: 病历数据字典

    Returns:
        格式化的病历文本
    """
    parts = []

    # 患者基本信息
    if "patient_info" in case_data:
        p = case_data["patient_info"]
        parts.append(f"患者信息：{p.get('name', '未知')}，{p.get('gender', '未知')}，{p.get('age', '未知')}岁")

    # 就诊信息
    if "visit_info" in case_data:
        v = case_data["visit_info"]
        parts.append(f"就诊科室：{v.get('department', '未知')}")
        parts.append(f"入院日期：{v.get('admission_date', '未知')}")
        if "discharge_date" in v:
            parts.append(f"出院日期：{v.get('discharge_date', '未知')}")
        parts.append(f"主诊断：{v.get('principal_diagnosis', '未知')}")

    # 主诉
    if "chief_complaint" in case_data:
        parts.append(f"主诉：{case_data['chief_complaint']}")

    # 现病史
    if "history_of_present_illness" in case_data:
        parts.append(f"现病史：{case_data['history_of_present_illness']}")

    # 既往史
    if "past_history" in case_data:
        ph = case_data["past_history"]
        ph_texts = []
        for key, value in ph.items():
            if isinstance(value, dict):
                ph_texts.append(f"{key}: {value.get('duration', '')}")
            else:
                ph_texts.append(f"{key}: {value}")
        if ph_texts:
            parts.append(f"既往史：{', '.join(ph_texts)}")

    # 体格检查
    if "physical_examination" in case_data:
        pe = case_data["physical_examination"]
        parts.append(f"一般情况：{pe.get('general_condition', '未知')}")
        if "vital_signs" in pe:
            vs = pe["vital_signs"]
            vs_text = []
            for k, v in vs.items():
                vs_text.append(f"{k}: {v}")
            parts.append(f"生命体征：{', '.join(vs_text)}")

    # 辅助检查
    if "auxiliary_examinations" in case_data:
        ae = case_data["auxiliary_examinations"]
        ae_texts = []
        for key, value in ae.items():
            if isinstance(value, dict):
                ae_texts.append(f"{key}: {value.get('result', '')}")
            else:
                ae_texts.append(f"{key}: {value}")
        if ae_texts:
            parts.append(f"辅助检查：{', '.join(ae_texts[:5])}...")

    # 诊疗经过
    if "course_of_treatment" in case_data:
        cot = case_data["course_of_treatment"]
        parts.append(f"诊疗经过：共记录 {len(cot)} 项治疗措施")

    # 出院医嘱
    if "discharge_medication" in case_data:
        dm = case_data["discharge_medication"]
        if isinstance(dm, dict):
            parts.append(f"出院带药：共 {len(dm)} 种药物")
        else:
            parts.append(f"出院医嘱：{dm}")

    return "\n".join(parts)


# 便捷函数
def get_normal_case() -> Optional[Dict[str, Any]]:
    """获取正常病历示例"""
    return load_sample_case("normal_001")


def get_defective_case() -> Optional[Dict[str, Any]]:
    """获取有缺陷病历示例"""
    return load_sample_case("defective_001")


def get_complex_case() -> Optional[Dict[str, Any]]:
    """获取复杂病历示例"""
    return load_sample_case("complex_001")
