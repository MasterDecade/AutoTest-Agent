"""Custom API adapter — supports user-defined LLM endpoints.

Handles arbitrary HTTP-based LLM APIs (OpenAI-compatible or custom format).
"""

from typing import Any

import httpx

from src.common.exceptions import LLMProviderError
from src.llm.base import BaseProvider, LLMConfig, LLMMessage, LLMResponse


class CustomAdapter(BaseProvider):
    """Adapter for custom LLM API endpoints.

    Supports:
    - OpenAI-compatible APIs (e.g., vLLM, Ollama, custom deployments)
    - Generic HTTP APIs with configurable request/response mapping
    """

    def __init__(self, config: LLMConfig):
        self._client: httpx.AsyncClient | None = None
        super().__init__(config)

    def _validate_config(self) -> None:
        if not self.config.api_key and not self.config.api_base:
            # Allow local endpoints without API key
            pass
        if not self.config.api_base:
            raise ValueError("api_base is required for custom adapter")

    def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init the HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.config.api_base.rstrip("/"),
                headers=headers,
                timeout=self.config.timeout,
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

        # Determine endpoint and payload format
        endpoint = self.config.extra_params.get("endpoint", "/v1/chat/completions")
        payload_format = self.config.extra_params.get("payload_format", "openai")

        if payload_format == "openai":
            request_body = self._build_openai_payload(messages, temperature, max_tokens, **kwargs)
        else:
            request_body = self._build_custom_payload(messages, temperature, max_tokens, **kwargs)

        try:
            response = await client.post(endpoint, json=request_body)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"Custom API HTTP {e.response.status_code}: {e.response.text[:500]}",
                provider=self.config.provider_type,
            )
        except httpx.RequestError as e:
            raise LLMProviderError(
                f"Custom API request failed: {str(e)}",
                provider=self.config.provider_type,
            )

        return self._parse_openai_response(data)

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Any:
        client = self._get_client()
        endpoint = self.config.extra_params.get("endpoint", "/v1/chat/completions")

        request_body = self._build_openai_payload(
            messages, temperature, max_tokens, stream=True, **kwargs
        )

        try:
            async with client.stream("POST", endpoint, json=request_body) as response:
                response.raise_for_status()
                from src.llm.base import LLMStreamChunk

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        import json
                        chunk = json.loads(data_str)
                        if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                            yield LLMStreamChunk(
                                content=chunk["choices"][0]["delta"]["content"]
                            )
        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"Custom API stream HTTP {e.response.status_code}",
                provider=self.config.provider_type,
            )
        except httpx.RequestError as e:
            raise LLMProviderError(
                f"Custom API stream request failed: {str(e)}",
                provider=self.config.provider_type,
            )

    def _build_openai_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict:
        """Build an OpenAI-compatible request payload."""
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        payload.update({k: v for k, v in kwargs.items() if k not in ("model", "messages")})
        return payload

    def _build_custom_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
        **kwargs: Any,
    ) -> dict:
        """Build a custom format request payload (user-defined mapping)."""
        mapping = self.config.extra_params.get("request_mapping", {})
        if mapping:
            payload = {}
            for key, value_template in mapping.items():
                payload[key] = self._resolve_template(value_template, messages, temperature, max_tokens)
            return payload
        # Fall back to OpenAI format
        return self._build_openai_payload(messages, temperature, max_tokens, **kwargs)

    def _parse_openai_response(self, data: dict) -> LLMResponse:
        """Parse an OpenAI-format response."""
        try:
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", self.config.model_name),
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                finish_reason=choice.get("finish_reason", ""),
                raw_response=data,
            )
        except (KeyError, IndexError) as e:
            raise LLMProviderError(
                f"Failed to parse custom API response: {e}",
                provider=self.config.provider_type,
            )

    def _resolve_template(
        self,
        template: str,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> Any:
        """Simple template resolution for custom request mapping."""
        if template == "$messages":
            return [{"role": m.role, "content": m.content} for m in messages]
        if template == "$temperature":
            return temperature
        if template == "$max_tokens":
            return max_tokens
        if template == "$model":
            return self.config.model_name
        return template