"""
审判流程模块

整合起诉、辩护、法官三个角色，实现完整审判流程
"""

from .controller import TrialController, TrialResult, TrialPhase

__all__ = [
    "TrialController",
    "TrialResult",
    "TrialPhase",
]
