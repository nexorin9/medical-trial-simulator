"""
OpenAI 客户端

实现 OpenAI API 的调用封装
"""

import os
import time
from typing import List, Optional, Dict, Any

from .base import LLMClient, LLMResponse, LLMError, LLMProvider, Message


class OpenAIClient(LLMClient):
    """
    OpenAI GPT 客户端

    使用 OpenAI API 进行聊天生成
    """

    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        初始化 OpenAI 客户端

        Args:
            api_key: OpenAI API 密钥
            base_url: API 基础 URL
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL", self.DEFAULT_BASE_URL),
            model=model or os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL),
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
        发送聊天请求到 GPT

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
            raise LLMError("OpenAI API key is required", provider="openai")

        # 导入 OpenAI SDK
        try:
            from openai import OpenAI
        except ImportError:
            raise LLMError(
                "OpenAI SDK not installed. Install with: pip install openai",
                provider="openai"
            )

        # 构建请求消息格式（OpenAI 使用 user/assistant/system 角色）
        openai_messages = []
        if system_prompt:
            openai_messages.append({
                "role": "system",
                "content": system_prompt
            })

        for msg in messages:
            # 转换角色名称（OpenAI 不支持 "system" 在 messages 中）
            role = msg.role
            if role == "system":
                role = "user"
            openai_messages.append({
                "role": role,
                "content": msg.content
            })

        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens

        # 添加其他参数
        request_params.update(kwargs)

        start_time = time.time()

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )

            response = client.chat.completions.create(**request_params)

            latency = time.time() - start_time

            # 提取响应内容
            content = ""
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content or ""

            # 提取使用量
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
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
                f"OpenAI API error: {str(e)}",
                provider="openai"
            )

    def get_provider(self) -> LLMProvider:
        """获取服务提供商"""
        return LLMProvider.OPENAI
