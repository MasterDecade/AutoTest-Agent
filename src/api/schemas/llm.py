"""Pydantic schemas for LLM provider management and chat."""

from typing import Any, Optional

from pydantic import BaseModel, Field


# ===== Chat Schemas =====


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str = Field(..., description="Message role: system/user/assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat completion request."""

    messages: list[ChatMessage] = Field(..., min_length=1, description="Conversation messages")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    provider_type: Optional[str] = Field(default=None, description="Specific provider to use")
    model_name: Optional[str] = Field(default=None, description="Specific model to use")


class ChatResponse(BaseModel):
    """Chat completion response."""

    content: str = Field(..., description="Response content")
    model: str = Field(default="", description="Model used")
    usage: dict[str, int] = Field(default_factory=dict, description="Token usage stats")
    finish_reason: str = Field(default="", description="Completion finish reason")


# ===== Provider Management Schemas =====


class ProviderConfigRequest(BaseModel):
    """Request to add/configure an LLM provider."""

    provider_type: str = Field(..., min_length=1, max_length=100, description="Provider type identifier")
    api_key: str = Field(..., description="API key for authentication")
    model_name: str = Field(..., min_length=1, max_length=200, description="Model name")
    api_base: Optional[str] = Field(default=None, max_length=500, description="Custom API base URL")
    priority: int = Field(default=0, ge=0, le=100, description="Provider priority (higher = preferred)")
    extra_params: Optional[dict[str, Any]] = Field(default=None, description="Additional provider parameters")


class ProviderConfigResponse(BaseModel):
    """Response after registering a provider."""

    provider_type: str
    model_name: str
    api_base: Optional[str] = None
    status: str = "registered"


class ProviderTestRequest(BaseModel):
    """Request to test a provider connection."""

    provider_type: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)


class ProviderTestResponse(BaseModel):
    """Result of a provider connection test."""

    success: bool
    model: str = ""
    latency_ms: int = -1
    message: str = ""


class ProviderInfo(BaseModel):
    """Information about a registered provider."""

    provider_type: str
    model_name: str
    api_base: str = "(default)"
    priority: int = 0
    healthy: bool = True


class ProviderListResponse(BaseModel):
    """List of registered providers."""

    providers: list[ProviderInfo]
    total: int