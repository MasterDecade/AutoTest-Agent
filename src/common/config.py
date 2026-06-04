"""Application configuration via pydantic-settings."""

import json
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables.

    Uses pydantic-settings for type-safe configuration management.
    Supports loading from .env file and environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== Database =====
    database_url: str = Field(
        default="postgresql://autotest:autotest_pass@localhost:5432/autotest",
        description="Database connection URL",
    )
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=200)

    # ===== Redis / Celery =====
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # ===== LLM =====
    llm_providers: str = Field(
        default='{"openai": {"api_key": "", "model": "gpt-4o"}}',
        description="JSON string of LLM provider configurations",
    )

    @field_validator("llm_providers", mode="before")
    @classmethod
    def parse_llm_providers(cls, v: str) -> str:
        """Ensure llm_providers is valid JSON."""
        if isinstance(v, str):
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("llm_providers must be a valid JSON string")
        return v

    def get_llm_providers_dict(self) -> dict:
        """Parse LLM providers JSON into a Python dict."""
        return json.loads(self.llm_providers)

    # ===== Server =====
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8080, ge=1, le=65535)
    api_workers: int = Field(default=4, ge=1, le=32)
    debug: bool = Field(default=False)
    frontend_port: int = Field(default=3000, ge=1, le=65535)

    # ===== Docker Sandbox =====
    docker_host: str = Field(default="unix:///var/run/docker.sock")
    docker_mirror: str = Field(
        default="registry.cn-hangzhou.aliyuncs.com",
        description="Domestic Docker registry mirror",
    )
    sandbox_max_cpu: int = Field(default=2, ge=1, le=16)
    sandbox_max_memory: str = Field(default="2g")
    sandbox_timeout: int = Field(default=300, ge=10, le=3600)

    # ===== Concurrency =====
    max_concurrency: int = Field(default=10, ge=1, le=100)
    min_concurrency: int = Field(default=2, ge=1, le=10)
    cpu_threshold_percent: int = Field(default=80, ge=1, le=100)
    memory_threshold_percent: int = Field(default=85, ge=1, le=100)

    # ===== Image Registries =====
    pip_index_url: str = Field(default="https://pypi.tuna.tsinghua.edu.cn/simple")
    npm_registry: str = Field(default="https://registry.npmmirror.com")

    # ===== Security =====
    secret_key: str = Field(default="change-me-in-production", min_length=16)
    api_key_encryption_key: str = Field(default="change-me-in-production", min_length=16)

    # ===== Logging =====
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default="/var/log/autotest-agent/app.log")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()