"""OpenAI-compatible adapter for third-party APIs.

Supports any API endpoint that follows the OpenAI chat completions format
(e.g., local vLLM, Ollama, Text Generation Inference, etc.).
"""

from typing import Any

from src.llm.adapters.custom_adapter import CustomAdapter
from src.llm.base import BaseProvider, LLMConfig


class OpenAICompatAdapter(CustomAdapter):
    """Adapter specifically for OpenAI-compatible third-party APIs.

    Use this for:
    - Self-hosted vLLM
    - Ollama (with OpenAI-compatible endpoint)
    - LocalAI
    - Text Generation Inference (HuggingFace)
    - Any other OpenAI-format compatible API
    """

    def __init__(self, config: LLMConfig):
        # Force OpenAI payload format
        config.extra_params.setdefault("payload_format", "openai")
        config.extra_params.setdefault("endpoint", "/v1/chat/completions")
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate OpenAI-compatible configuration."""
        if not self.config.api_base:
            raise ValueError("api_base is required for OpenAI-compatible adapter")
        # API key is optional for local deployments
        if not self.config.model_name:
            self.config.model_name = "default"