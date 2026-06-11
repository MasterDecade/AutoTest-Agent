"""Base provider interface for LLM abstraction layer.

Defines the abstract base class that all LLM provider adapters must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""

    provider_type: str
    api_key: str
    model_name: str = "gpt-4o"
    api_base: str = ""
    max_retries: int = 3
    timeout: int = 120
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMessage:
    """A single message in a chat conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    raw_response: Any = None


@dataclass
class LLMStreamChunk:
    """A single chunk from a streaming LLM response."""

    content: str
    index: int = 0


class BaseProvider(ABC):
    """Abstract base class for all LLM provider adapters.

    All provider implementations must subclass this and implement
    the required methods for chat completion and streaming.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the provider configuration.

        Raises:
            ValueError: If the configuration is invalid.
        """
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature (0.0 - 2.0).
            max_tokens: Maximum tokens in the response.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse with the completion content and metadata.

        Raises:
            src.common.exceptions.LLMProviderError: On provider errors.
        """
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Any:
        """Send a streaming chat completion request.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.
            **kwargs: Additional provider-specific parameters.

        Yields:
            LLMStreamChunk instances.

        Raises:
            src.common.exceptions.LLMProviderError: On provider errors.
        """
        ...

    @staticmethod
    def system(msg: str) -> LLMMessage:
        """Create a system message."""
        return LLMMessage(role="system", content=msg)

    @staticmethod
    def user(msg: str) -> LLMMessage:
        """Create a user message."""
        return LLMMessage(role="user", content=msg)

    @staticmethod
    def assistant(msg: str) -> LLMMessage:
        """Create an assistant message."""
        return LLMMessage(role="assistant", content=msg)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.config.model_name}>"