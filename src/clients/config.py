"""
LLM 客户端配置模块

提供配置加载和环境变量支持
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path

from .base import LLMProvider
from .anthropic_client import AnthropicClient
from .openai_client import OpenAIClient
from .base import LLMClient


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件

    优先级：命令行参数 > 环境变量 > 配置文件 > 默认值

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    config = {
        # 默认使用 Anthropic
        "provider": os.getenv("LLM_PROVIDER", "anthropic"),
        # Anthropic 配置
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "anthropic_base_url": os.getenv("ANTHROPIC_BASE_URL"),
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        # OpenAI 配置
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_base_url": os.getenv("OPENAI_BASE_URL"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        # 通用配置
        "timeout": int(os.getenv("LLM_TIMEOUT", "60")),
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", "3")),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
    }

    # 如果提供了配置文件路径，读取并合并配置
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            file_config = json.load(f)
            config.update(file_config)

    return config


def get_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> LLMClient:
    """
    获取 LLM 客户端实例

    Args:
        provider: 服务提供商（anthropic/openai）
        api_key: API 密钥
        model: 模型名称
        config: 配置字典

    Returns:
        LLM 客户端实例

    Raises:
        ValueError: 当无法创建客户端时
    """
    # 加载配置
    if config is None:
        config = load_config()

    # 确定提供商
    provider = provider or config.get("provider", "anthropic")

    # 通用参数
    timeout = config.get("timeout", 60)
    max_retries = config.get("max_retries", 3)

    if provider.lower() == "anthropic":
        return AnthropicClient(
            api_key=api_key or config.get("anthropic_api_key"),
            base_url=config.get("anthropic_base_url"),
            model=model or config.get("anthropic_model"),
            timeout=timeout,
            max_retries=max_retries,
        )
    elif provider.lower() == "openai":
        return OpenAIClient(
            api_key=api_key or config.get("openai_api_key"),
            base_url=config.get("openai_base_url"),
            model=model or config.get("openai_model"),
            timeout=timeout,
            max_retries=max_retries,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_available_providers() -> list:
    """
    获取当前可用的 LLM 提供商

    Returns:
        可用提供商列表
    """
    providers = []

    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append("anthropic")

    if os.getenv("OPENAI_API_KEY"):
        providers.append("openai")

    return providers


def validate_environment() -> Dict[str, bool]:
    """
    验证环境配置

    Returns:
        验证结果字典
    """
    return {
        "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "any_provider_available": len(get_available_providers()) > 0,
    }
