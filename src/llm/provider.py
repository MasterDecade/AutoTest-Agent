"""Provider manager for LLM abstraction layer.

Handles provider registration, routing, failover, and health checks.
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Optional

from src.common.exceptions import LLMProviderError
from src.llm.base import BaseProvider, LLMConfig, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manages multiple LLM providers with routing and failover.

    Features:
    - Register multiple providers with priority
    - Automatic failover on failure
    - Health checking
    - Round-robin load balancing
    """

    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}
        self._priorities: dict[str, int] = {}
        self._health_status: dict[str, bool] = {}

    def register(self, provider: BaseProvider, priority: int = 0) -> None:
        """Register a provider instance.

        Args:
            provider: The provider instance to register.
            priority: Higher values = higher priority.
        """
        key = f"{provider.config.provider_type}:{provider.config.model_name}"
        self._providers[key] = provider
        self._priorities[key] = priority
        self._health_status[key] = True
        logger.info(f"Registered provider: {key} (priority={priority})")

    def unregister(self, provider_type: str, model_name: str) -> None:
        """Remove a provider from the registry."""
        key = f"{provider_type}:{model_name}"
        self._providers.pop(key, None)
        self._priorities.pop(key, None)
        self._health_status.pop(key, None)
        logger.info(f"Unregistered provider: {key}")

    def get_provider(self, provider_type: Optional[str] = None, model_name: Optional[str] = None) -> BaseProvider:
        """Get a specific provider or the highest priority healthy one.

        Args:
            provider_type: Optional filter by provider type.
            model_name: Optional filter by model name.

        Returns:
            A BaseProvider instance.

        Raises:
            LLMProviderError: If no healthy provider is available.
        """
        if provider_type and model_name:
            key = f"{provider_type}:{model_name}"
            provider = self._providers.get(key)
            if provider:
                return provider
            raise LLMProviderError(f"Provider not found: {key}")

        # Get highest priority healthy provider
        healthy = [(k, p) for k, p in self._providers.items() if self._health_status.get(k, True)]
        if not healthy:
            raise LLMProviderError("No healthy LLM provider available", provider="all")

        # Sort by priority descending, then by name
        best_key = sorted(healthy, key=lambda x: (-self._priorities.get(x[0], 0), x[0]))[0][0]
        return self._providers[best_key]

    def list_providers(self) -> list[dict]:
        """List all registered providers with their status."""
        return [
            {
                "provider_type": p.config.provider_type,
                "model_name": p.config.model_name,
                "api_base": p.config.api_base or "(default)",
                "priority": self._priorities.get(k, 0),
                "healthy": self._health_status.get(k, True),
            }
            for k, p in self._providers.items()
        ]

    async def health_check(self, provider_type: str = None) -> dict[str, bool]:
        """Run health checks against all or specific providers.

        Sends a minimal ping message to verify connectivity.
        """
        results = {}
        for key, provider in self._providers.items():
            if provider_type and provider.config.provider_type != provider_type:
                continue
            try:
                await provider.chat(
                    messages=[BaseProvider.user("ping")],
                    temperature=0.0,
                    max_tokens=5,
                )
                self._health_status[key] = True
                results[key] = True
            except Exception as e:
                self._health_status[key] = False
                results[key] = False
                logger.warning(f"Health check failed for {key}: {e}")
        return results

    async def chat_with_fallback(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_retries: int = 3,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request with automatic failover across providers.

        Tries providers in priority order until one succeeds.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.
            max_retries: Max attempts per provider.
            **kwargs: Additional parameters.

        Returns:
            LLMResponse from the first successful provider.

        Raises:
            LLMProviderError: If all providers fail.
        """
        errors = []
        healthy = self._get_sorted_healthy_providers()

        if not healthy:
            # Try all providers anyway (maybe health check is stale)
            healthy = sorted(
                self._providers.items(),
                key=lambda x: -self._priorities.get(x[0], 0),
            )

        for key, provider in healthy:
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Attempting {key} (attempt {attempt + 1}/{max_retries})")
                    response = await provider.chat(messages, temperature, max_tokens, **kwargs)
                    self._health_status[key] = True
                    return response
                except Exception as e:
                    error_msg = f"{key} attempt {attempt + 1} failed: {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    self._health_status[key] = False
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise LLMProviderError(
            f"All providers failed. Errors: {'; '.join(errors)}",
            provider="all",
        )

    async def chat_stream_with_fallback(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Streaming chat with failover (falls back to non-streaming if needed)."""
        try:
            provider = self._get_sorted_healthy_providers()
            if provider:
                key, p = provider[0]
                async for chunk in await p.chat_stream(messages, temperature, max_tokens, **kwargs):
                    yield chunk.content
                return
        except Exception:
            pass

        # Fallback to non-streaming
        response = await self.chat_with_fallback(messages, temperature, max_tokens, **kwargs)
        yield response.content

    def _get_sorted_healthy_providers(self) -> list[tuple[str, BaseProvider]]:
        """Get healthy providers sorted by priority (descending)."""
        healthy = [(k, p) for k, p in self._providers.items() if self._health_status.get(k, True)]
        return sorted(healthy, key=lambda x: -self._priorities.get(x[0], 0))


# Global singleton instance
_provider_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """Get or create the global ProviderManager singleton."""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
    return _provider_manager