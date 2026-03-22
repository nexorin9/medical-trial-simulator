"""
全局异常处理模块

定义项目专用的异常类型和异常处理函数
"""

import sys
import traceback
from typing import Optional, Callable, Any
from functools import wraps

from .logging_config import get_logger


class MedicalTrialError(Exception):
    """医保费用审判基础异常"""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class DataLoadError(MedicalTrialError):
    """数据加载异常"""

    pass


class ValidationError(MedicalTrialError):
    """数据验证异常"""

    pass


class LLMCallError(MedicalTrialError):
    """LLM 调用异常"""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        self.provider = provider
        self.status_code = status_code
        full_details = details or {}
        if provider:
            full_details["provider"] = provider
        if status_code:
            full_details["status_code"] = status_code
        super().__init__(message, full_details)


class TrialPhaseError(MedicalTrialError):
    """审判阶段异常"""

    def __init__(self, message: str, phase: Optional[str] = None, details: Optional[dict] = None):
        self.phase = phase
        full_details = details or {}
        if phase:
            full_details["phase"] = phase
        super().__init__(message, full_details)


class ConfigurationError(MedicalTrialError):
    """配置异常"""

    pass


# 全局异常处理器
_logger = get_logger("medical_trial.exceptions")


def setup_global_exception_handler(
    log_file: Optional[str] = None,
    reraise: bool = True,
) -> None:
    """
    设置全局异常处理器

    Args:
        log_file: 错误日志文件路径（可选）
        reraise: 是否在处理后重新抛出异常
    """

    def handle_exception(exc_type, exc_value, exc_traceback):
        """全局异常处理函数"""
        # 忽略 KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 构建错误消息
        error_msg = f"{exc_type.__name__}: {exc_value}"

        # 记录 traceback
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        _logger.error(f"未捕获的异常:\n{tb_str}")

        # 写入错误日志文件
        if log_file:
            try:
                from pathlib import Path
                from datetime import datetime

                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{'=' * 60}\n")
                    f.write(f"时间: {datetime.now().isoformat()}\n")
                    f.write(f"异常类型: {exc_type.__name__}\n")
                    f.write(f"异常消息: {exc_value}\n")
                    f.write(f"Traceback:\n{tb_str}\n")
            except Exception as write_err:
                _logger.error(f"写入错误日志失败: {write_err}")

        # 打印错误消息到控制台
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"错误: {error_msg}", file=sys.stderr)
        print(f"如需详细信息，请使用 --verbose 参数运行", file=sys.stderr)
        print(f"{'=' * 60}\n", file=sys.stderr)

        if reraise:
            # 重新抛出异常
            raise exc_value

    # 设置全局异常钩子
    sys.excepthook = handle_exception


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_name: Optional[str] = None,
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
        exceptions: 需要重试的异常类型元组
        logger_name: 日志记录器名称

    Returns:
        装饰器函数
    """
    logger = get_logger(logger_name or "retry")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries - 1:
                        logger.warning(
                            f"重试 {attempt + 1}/{max_retries} - "
                            f"函数: {func.__name__}, 错误: {type(e).__name__}: {str(e)}, "
                            f"等待 {current_delay:.1f}s"
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"重试耗尽 - 函数: {func.__name__}, "
                            f"最终错误: {type(e).__name__}: {str(e)}"
                        )

            # 所有重试都失败，抛出最后一个异常
            raise last_exception

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    default: Any = None,
    error_msg: str = "",
    log_errors: bool = True,
    logger_name: Optional[str] = None,
) -> Any:
    """
    安全执行函数，捕获异常并返回默认值

    Args:
        func: 要执行的函数
        default: 异常时返回的默认值
        error_msg: 错误消息前缀
        log_errors: 是否记录错误
        logger_name: 日志记录器名称

    Returns:
        函数执行结果或默认值
    """
    logger = get_logger(logger_name or "safe_execute")

    try:
        return func()
    except Exception as e:
        if log_errors:
            msg = f"{error_msg}: {type(e).__name__}: {str(e)}" if error_msg else str(e)
            logger.error(msg)
        return default


class ErrorContext:
    """
    错误上下文管理器

    用于捕获和记录代码块的异常
    """

    def __init__(
        self,
        context_name: str,
        logger_name: Optional[str] = None,
        reraise: bool = True,
    ):
        self.context_name = context_name
        self.logger = get_logger(logger_name or "error_context")
        self.reraise = reraise
        self.error: Optional[Exception] = None

    def __enter__(self):
        self.logger.debug(f"进入上下文: {self.context_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            self.logger.error(
                f"上下文异常: {self.context_name} - "
                f"{type(exc_val).__name__}: {str(exc_val)}"
            )
            if self.reraise:
                return False  # 重新抛出异常
        else:
            self.logger.debug(f"正常退出上下文: {self.context_name}")

        return True  # 抑制异常
