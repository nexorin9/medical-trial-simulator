"""
LLM 客户端单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os


class TestLLMClient:
    """测试 LLM 客户端功能"""

    def test_llm_response_dataclass(self):
        """测试 LLMResponse 数据类"""
        from src.llm_client import LLMResponse

        # 测试创建响应对象
        response = LLMResponse(
            content="Test response",
            model="gpt-4o",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )

        assert response.content == "Test response"
        assert response.model == "gpt-4o"
        assert response.usage["total_tokens"] == 150

    def test_create_client_with_api_key(self):
        """测试使用 API key 创建客户端"""
        from src.llm_client import create_client

        # 使用模拟 API key
        client = create_client(provider="openai", api_key="test-key-123")
        assert client.api_key == "test-key-123"
        assert client.provider == "openai"

    def test_create_client_default_model(self):
        """测试默认模型选择"""
        from src.llm_client import create_client

        client = create_client(provider="openai", api_key="test-key")
        assert client.model == "gpt-4o"

        client = create_client(provider="anthropic", api_key="test-key")
        assert "claude" in client.model

    def test_available_providers(self):
        """测试获取可用提供商"""
        from src.llm_client import LLMClient

        providers = LLMClient.available_providers()
        assert isinstance(providers, list)

    def test_available_models_openai(self):
        """测试 OpenAI 可用模型列表"""
        from src.llm_client import LLMClient

        models = LLMClient.available_models("openai")
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models

    def test_available_models_anthropic(self):
        """测试 Anthropic 可用模型列表"""
        from src.llm_client import LLMClient

        models = LLMClient.available_models("anthropic")
        assert len(models) > 0

    def test_generate_method(self):
        """测试 generate 方法"""
        from src.llm_client import LLMClient

        # Mock 客户端
        with patch('src.llm_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            # Mock 响应
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Test output"))]
            mock_response.model = "gpt-4o"
            mock_response.usage = Mock(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
            mock_client.chat.completions.create.return_value = mock_response

            client = LLMClient(provider="openai", api_key="test-key")
            response = client.generate(
                prompt="Test prompt",
                system_prompt="System prompt"
            )

            assert response.content == "Test output"
            assert response.model == "gpt-4o"

    def test_chat_method(self):
        """测试 chat 方法"""
        from src.llm_client import LLMClient

        with patch('src.llm_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Chat response"))]
            mock_response.model = "gpt-4o"
            mock_response.usage = Mock(
                prompt_tokens=5,
                completion_tokens=10,
                total_tokens=15
            )
            mock_client.chat.completions.create.return_value = mock_response

            client = LLMClient(provider="openai", api_key="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            response = client.chat(messages)

            assert response.content == "Chat response"

    def test_provider_case_insensitive(self):
        """测试提供商名称大小写不敏感"""
        from src.llm_client import LLMClient

        client = LLMClient(provider="OPENAI", api_key="test-key")
        assert client.provider == "openai"

        client = LLMClient(provider="Anthropic", api_key="test-key")
        assert client.provider == "anthropic"

    def test_temperature_and_max_tokens(self):
        """测试温度和最大 token 参数"""
        from src.llm_client import LLMClient

        client = LLMClient(
            provider="openai",
            api_key="test-key",
            temperature=0.5,
            max_tokens=2000
        )

        assert client.temperature == 0.5
        assert client.max_tokens == 2000


class TestLLMResponse:
    """测试 LLMResponse 数据类"""

    def test_response_with_no_usage(self):
        """测试无 usage 信息的响应"""
        from src.llm_client import LLMResponse

        response = LLMResponse(
            content="Test",
            model="gpt-4o"
        )

        assert response.usage is None

    def test_response_with_raw_response(self):
        """测试带有原始响应的响应"""
        from src.llm_client import LLMResponse

        raw = {"id": "test-id", "choices": []}
        response = LLMResponse(
            content="Test",
            model="gpt-4o",
            raw_response=raw
        )

        assert response.raw_response == raw
