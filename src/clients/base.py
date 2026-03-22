"""
LLM 客户端基类

定义 LLM 服务的通用接口和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time


class LLMProvider(Enum):
    """LLM 服务提供商"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass
class Message:
    """
    聊天消息

    Attributes:
        role: 角色（system/user/assistant）
        content: 消息内容
    """
    role: str
    content: str


@dataclass
class LLMResponse:
    """
    LLM 响应

    Attributes:
        content: 响应内容
        model: 使用的模型
        usage: token 使用量
        raw_response: 原始响应
        latency: 响应延迟（秒）
    """
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Dict[str, Any]] = None
    latency: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "latency": self.latency,
        }


class LLMError(Exception):
    """LLM 调用错误"""

    def __init__(self, message: str, provider: Optional[str] = None, status_code: Optional[int] = None):
        self.message = message
        self.provider = provider
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self):
        parts = [self.message]
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        return " | ".join(parts)


class LLMClient(ABC):
    """
    LLM 客户端基类

    定义 LLM 服务的通用接口
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        pass

    @abstractmethod
    def get_provider(self) -> LLMProvider:
        """
        获取服务提供商

        Returns:
            服务提供商枚举
        """
        pass

    def _retry_with_backoff(self, func, *args, **kwargs) -> LLMResponse:
        """
        带退避的重试机制

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except LLMError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise last_error

        raise last_error

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            配置是否有效
        """
        if not self.api_key:
            return False
        if not self.model:
            return False
        return True

    def generate(
        self,
        system_prompt: Optional[str] = None,
        user_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        便捷方法：生成文本（封装 chat 方法）

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数

        Returns:
            生成的文本内容
        """
        # 构建消息列表
        messages = [Message(role="user", content=user_prompt)]

        response = self.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return response.content
