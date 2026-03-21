"""
LLM 客户端封装模块

支持 OpenAI 和 Anthropic 两种 API
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv

# 尝试导入客户端库
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

load_dotenv()


@dataclass
class LLMResponse:
    """LLM 响应封装"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None


class LLMClient:
    """统一 LLM 客户端，支持 OpenAI 和 Anthropic"""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """
        初始化 LLM 客户端

        Args:
            provider: "openai" 或 "anthropic"
            model: 模型名称
            api_key: API 密钥，默认从环境变量读取
            base_url: 自定义 API 地址（用于代理）
            temperature: 温度参数
            max_tokens: 最大 token 数
        """
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 获取 API Key
        if api_key:
            self.api_key = api_key
        elif self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        else:
            raise ValueError(f"Unknown provider: {provider}")

        if not self.api_key:
            raise ValueError(
                f"API key not found. Please set {self._get_env_key()} "
                "or pass api_key parameter."
            )

        # 初始化客户端
        self._client = self._init_client(base_url)

    def _get_env_key(self) -> str:
        """获取环境变量键名"""
        if self.provider == "openai":
            return "OPENAI_API_KEY"
        elif self.provider == "anthropic":
            return "ANTHROPIC_API_KEY"
        return "API_KEY"

    def _init_client(self, base_url: Optional[str] = None):
        """初始化底层客户端"""
        if self.provider == "openai":
            if OpenAI is None:
                raise ImportError("openai package not installed")
            return OpenAI(api_key=self.api_key, base_url=base_url)

        elif self.provider == "anthropic":
            if anthropic is None:
                raise ImportError("anthropic package not installed")
            return anthropic.Anthropic(api_key=self.api_key)

        raise ValueError(f"Unknown provider: {self.provider}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLMResponse 对象
        """
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        if self.provider == "openai":
            return self._chat_openai(messages, temperature, max_tokens)
        elif self.provider == "anthropic":
            return self._chat_anthropic(messages, temperature, max_tokens)

        raise ValueError(f"Unknown provider: {self.provider}")

    def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """OpenAI API 调用"""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            raw_response=response
        )

    def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Anthropic API 调用"""
        # 转换消息格式
        system = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                anthropic_messages.append(msg)

        response = self._client.messages.create(
            model=self.model,
            system=system,
            messages=anthropic_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        content = "".join(
            block.text for block in response.content
            if hasattr(block, "text")
        )

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            raw_response=response
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        简化生成接口

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 其他参数

        Returns:
            LLMResponse 对象
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, **kwargs)

    @staticmethod
    def available_providers() -> list:
        """获取可用的提供商列表"""
        providers = []
        if OpenAI is not None:
            providers.append("openai")
        if anthropic is not None:
            providers.append("anthropic")
        return providers

    @staticmethod
    def available_models(provider: str = "openai") -> list:
        """获取指定提供商可用的模型列表"""
        if provider == "openai":
            return [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ]
        elif provider == "anthropic":
            return [
                "claude-sonnet-4-20250514",
                "claude-sonnet-4-20250507",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-sonnet-20240620",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ]
        return []


def create_client(
    provider: str = "openai",
    model: Optional[str] = None,
    **kwargs
) -> LLMClient:
    """
    工厂函数：创建 LLM 客户端

    Args:
        provider: "openai" 或 "anthropic"
        model: 模型名称（可选，默认值见下文）
        **kwargs: 其他参数

    Returns:
        LLMClient 实例
    """
    # 默认模型
    if model is None:
        if provider == "openai":
            model = "gpt-4o"
        elif provider == "anthropic":
            model = "claude-3-5-sonnet-20241022"
        else:
            model = "gpt-4o"

    return LLMClient(provider=provider, model=model, **kwargs)
