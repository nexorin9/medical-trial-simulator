"""
日志配置模块

提供统一的日志配置和管理功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选）
        log_format: 日志格式（可选）
        verbose: 是否启用详细输出
    """
    # 确定日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 如果 verbose 模式，降低日志级别
    if verbose:
        log_level = logging.DEBUG

    # 默认日志格式
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 创建格式化器
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 设置第三方库的日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


class TrialLogger:
    """
    审判日志记录器

    提供审判流程专用的日志记录功能
    """

    def __init__(self, name: str = "medical_trial"):
        self.logger = get_logger(name)
        self.case_id: Optional[str] = None

    def set_case_id(self, case_id: str) -> None:
        """设置案件 ID"""
        self.case_id = case_id
        self.logger.info(f"开始新案件: {case_id}")

    def log_phase_start(self, phase: str) -> None:
        """记录阶段开始"""
        phase_names = {
            "prosecutor": "起诉阶段",
            "defense": "辩护阶段",
            "judge": "裁决阶段",
        }
        phase_display = phase_names.get(phase, phase)
        self.logger.info(f"[{self.case_id}] 开始: {phase_display}")

    def log_phase_end(self, phase: str, success: bool = True) -> None:
        """记录阶段结束"""
        phase_names = {
            "prosecutor": "起诉阶段",
            "defense": "辩护阶段",
            "judge": "裁决阶段",
        }
        phase_display = phase_names.get(phase, phase)
        status = "成功" if success else "失败"
        self.logger.info(f"[{self.case_id}] 结束: {phase_display} - {status}")

    def log_llm_call(
        self,
        provider: str,
        model: str,
        latency: float,
        success: bool = True,
    ) -> None:
        """记录 LLM 调用"""
        status = "成功" if success else "失败"
        msg = f"[{self.case_id}] LLM调用 - 提供商: {provider}, 模型: {model}, 延迟: {latency:.2f}s, 状态: {status}"
        if success:
            self.logger.info(msg)
        else:
            self.logger.warning(msg)

    def log_error(self, error: Exception, context: str = "") -> None:
        """记录错误"""
        context_msg = f" - {context}" if context else ""
        self.logger.error(f"[{self.case_id}] 错误{context_msg}: {type(error).__name__}: {str(error)}")

    def log_retry(self, attempt: int, max_retries: int, error: str) -> None:
        """记录重试"""
        self.logger.warning(
            f"[{self.case_id}] 重试 {attempt}/{max_retries} - 错误: {error}"
        )

    def log_trial_complete(self, status: str, verdict: Optional[str] = None) -> None:
        """记录审判完成"""
        verdict_msg = f", 裁决: {verdict}" if verdict else ""
        self.logger.info(f"[{self.case_id}] 审判完成 - 状态: {status}{verdict_msg}")
