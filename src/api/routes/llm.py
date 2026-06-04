"""API routes for LLM provider management and chat."""

from fastapi import APIRouter, HTTPException

from src.api.schemas.llm import (
    ChatRequest,
    ChatResponse,
    ProviderConfigRequest,
    ProviderConfigResponse,
    ProviderListResponse,
    ProviderTestRequest,
    ProviderTestResponse,
)
from src.common.exceptions import LLMProviderError, NotFoundError
from src.llm.base import LLMConfig, LLMMessage
from src.llm.provider import get_provider_manager

router = APIRouter(prefix="/api/llm", tags=["llm"])

manager = get_provider_manager()


# ===== Provider Management =====


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers():
    """List all registered LLM providers with their status."""
    providers = manager.list_providers()
    return ProviderListResponse(providers=providers, total=len(providers))


@router.post("/providers", response_model=ProviderConfigResponse, status_code=201)
async def add_provider(config: ProviderConfigRequest):
    """Register a new LLM provider."""
    from src.llm.adapters.custom_adapter import CustomAdapter
    from src.llm.adapters.litellm_adapter import LiteLLMAdapter
    from src.llm.adapters.openai_compat import OpenAICompatAdapter

    llm_config = LLMConfig(
        provider_type=config.provider_type,
        api_key=config.api_key,
        model_name=config.model_name,
        api_base=config.api_base or "",
        extra_params=config.extra_params or {},
    )

    # Choose adapter based on provider type
    if config.provider_type in LiteLLMAdapter.SUPPORTED_PROVIDERS:
        provider = LiteLLMAdapter(llm_config)
    elif config.provider_type == "openai_compat":
        provider = OpenAICompatAdapter(llm_config)
    else:
        provider = CustomAdapter(llm_config)

    manager.register(provider, priority=config.priority)

    return ProviderConfigResponse(
        provider_type=config.provider_type,
        model_name=config.model_name,
        api_base=config.api_base,
        status="registered",
    )


@router.delete("/providers/{provider_type}/{model_name}")
async def remove_provider(provider_type: str, model_name: str):
    """Remove a registered LLM provider."""
    manager.unregister(provider_type, model_name)
    return {"message": f"Provider {provider_type}/{model_name} removed"}


@router.post("/providers/test", response_model=ProviderTestResponse)
async def test_provider(request: ProviderTestRequest):
    """Test connectivity to an LLM provider."""
    try:
        provider = manager.get_provider(request.provider_type, request.model_name)
    except LLMProviderError:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        response = await provider.chat(
            messages=[LLMMessage(role="user", content="ping")],
            temperature=0.0,
            max_tokens=5,
        )
        return ProviderTestResponse(
            success=True,
            model=response.model,
            latency_ms=-1,  # Could measure actual latency
            message="Connection successful",
        )
    except LLMProviderError as e:
        return ProviderTestResponse(success=False, message=str(e))


# ===== Chat Endpoints =====


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """Send a chat completion request to the best available provider."""
    messages = [LLMMessage(role=m.role, content=m.content) for m in request.messages]

    try:
        if request.provider_type and request.model_name:
            provider = manager.get_provider(request.provider_type, request.model_name)
            response = await provider.chat(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        else:
            response = await manager.chat_with_fallback(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

        return ChatResponse(
            content=response.content,
            model=response.model,
            usage=response.usage,
            finish_reason=response.finish_reason,
        )
    except LLMProviderError as e:
        raise HTTPException(status_code=503, detail=e.message)