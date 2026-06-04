"""LiteLLM adapter — wraps 100+ LLM providers via LiteLLM SDK."""

from typing import Any

from src.common.exceptions import LLMProviderError
from src.llm.base import BaseProvider, LLMConfig, LLMMessage, LLMResponse


class LiteLLMAdapter(BaseProvider):
    """LiteLLM-based adapter for mainstream LLM providers.

    Supports OpenAI, Anthropic, Azure, Gemini, Qwen, DeepSeek,
    ZhipuAI, and many more through LiteLLM's unified interface.
    """

    SUPPORTED_PROVIDERS = {
        "openai", "anthropic", "azure", "gemini", "vertex_ai",
        "qwen", "deepseek", "zhipuai", "moonshot", "baichuan",
        "ollama", "vllm", "together_ai", "replicate", "huggingface",
    }

    def __init__(self, config: LLMConfig):
        self._client = None
        super().__init__(config)

    def _validate_config(self) -> None:
        if not self.config.api_key:
            raise ValueError(f"API key is required for LiteLLM adapter ({self.config.provider_type})")
        if self.config.provider_type not in self.SUPPORTED_PROVIDERS:
            # LiteLLM supports many more - just warn, don't fail
            pass

    def _get_client(self):
        """Lazy-init the LiteLLM client."""
        if self._client is None:
            try:
                import litellm
                self._client = litellm
            except ImportError:
                raise LLMProviderError(
                    "litellm package is not installed. Run: pip install litellm",
                    provider=self.config.provider_type,
                )
        return self._client

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        client = self._get_client()

        # Build provider-specific model string
        model = self._build_model_string()

        # Convert messages to LiteLLM format
        litellm_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            response = await client.acompletion(
                model=model,
                messages=litellm_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.config.api_key,
                api_base=self.config.api_base or None,
                **self.config.extra_params,
                **kwargs,
            )
        except Exception as e:
            raise LLMProviderError(
                f"LiteLLM call failed: {str(e)}",
                provider=self.config.provider_type,
            )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason or "",
            raw_response=response,
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Any:
        client = self._get_client()
        model = self._build_model_string()
        litellm_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            response = await client.acompletion(
                model=model,
                messages=litellm_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                api_key=self.config.api_key,
                api_base=self.config.api_base or None,
                **self.config.extra_params,
                **kwargs,
            )
        except Exception as e:
            raise LLMProviderError(
                f"LiteLLM stream call failed: {str(e)}",
                provider=self.config.provider_type,
            )

        from src.llm.base import LLMStreamChunk

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield LLMStreamChunk(content=chunk.choices[0].delta.content)

    def _build_model_string(self) -> str:
        """Build the model identifier string for LiteLLM.

        Examples:
            - openai/gpt-4o
            - anthropic/claude-3-opus-20240229
            - qwen/qwen-max
        """
        return f"{self.config.provider_type}/{self.config.model_name}"