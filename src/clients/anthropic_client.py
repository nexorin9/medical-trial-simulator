"""
Anthropic Claude 客户端

实现 Claude API 的调用封装
"""

import os
import time
from typing import List, Optional, Dict, Any

from .base import LLMClient, LLMResponse, LLMError, LLMProvider, Message


class AnthropicClient(LLMClient):
    """
    Anthropic Claude 客户端

    使用 Claude API 进行聊天生成
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_BASE_URL = "https://api.anthropic.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        初始化 Anthropic 客户端

        Args:
            api_key: Anthropic API 密钥
            base_url: API 基础 URL
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            base_url=base_url or os.getenv("ANTHROPIC_BASE_URL", self.DEFAULT_BASE_URL),
            model=model or os.getenv("ANTHROPIC_MODEL", self.DEFAULT_MODEL),
            timeout=timeout,
            max_retries=max_retries,
        )

    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        发送聊天请求到 Claude

        Args:
            messages: 消息列表
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        if not self.api_key:
            raise LLMError("Anthropic API key is required", provider="anthropic")

        # 导入 Anthropic SDK
        try:
            from anthropic import Anthropic
        except ImportError:
            raise LLMError(
                "Anthropic SDK not installed. Install with: pip install anthropic",
                provider="anthropic"
            )

        # 构建请求消息格式
        claude_messages = []
        for msg in messages:
            claude_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 设置默认 max_tokens
        if max_tokens is None:
            max_tokens = 4096

        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": claude_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        # 添加其他参数
        request_params.update(kwargs)

        start_time = time.time()

        try:
            client = Anthropic(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )

            response = client.messages.create(**request_params)

            latency = time.time() - start_time

            # 提取响应内容
            content = ""
            if response.content:
                content = response.content[0].text

            # 提取使用量
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
                latency=latency,
            )

        except Exception as e:
            raise LLMError(
                f"Anthropic API error: {str(e)}",
                provider="anthropic"
            )

    def get_provider(self) -> LLMProvider:
        """获取服务提供商"""
        return LLMProvider.ANTHROPIC
