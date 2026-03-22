"""
审判框架 Prompt 模块

包含：
- ProsecutorPrompt: 起诉方（医保审核规则）
- DefensePrompt: 辩护方（医院说明）
- JudgePrompt: 法官（综合裁决）
"""

from .base import TrialRole, TrialStatement, TrialContext

# 起诉方模块
from .prosecutor import ProsecutorPrompt, MedicalPolicyReference

# 辩护方模块（当前任务）
from .defense import DefensePrompt, HospitalDefenseHelper

# 法官模块
from .judge import JudgePrompt, JudgmentCriteria

__all__ = [
    'TrialRole',
    'TrialStatement',
    'TrialContext',
    'ProsecutorPrompt',
    'MedicalPolicyReference',
    'DefensePrompt',
    'HospitalDefenseHelper',
    'JudgePrompt',
    'JudgmentCriteria',
]
