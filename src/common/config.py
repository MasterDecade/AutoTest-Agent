"""Application configuration via pydantic-settings.

Provides type-safe configuration management with validation,
secure key handling, and environment-aware defaults.
"""

import hashlib
import json
import os
import warnings
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables.

    Uses pydantic-settings for type-safe configuration management.
    Supports loading from .env file and environment variables.

    Security features:
    - Validates secret key strength
    - Warns about default/insecure values
    - Supports encrypted API keys (placeholder for future implementation)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== Database =====
    database_url: str = Field(
        default="postgresql+asyncpg://autotest:autotest_pass@localhost:5432/autotest",
        description="Database connection URL (prefer asyncpg driver)",
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
    secret_key: str = Field(
        default="",
        description="Secret key for session signing and CSRF protection (min 32 chars)",
    )
    api_key_encryption_key: str = Field(
        default="",
        description="Encryption key for API key storage (min 32 chars)",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength.

        In production, the key must be at least 32 characters and not a default value.
        """
        if not v:
            # Generate a warning but allow empty in dev (will use default)
            warnings.warn(
                "SECRET_KEY is not set. Using insecure default for development only!",
                UserWarning,
            )
            return "dev-secret-key-change-in-production-1234567890"

        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")

        # Check for common insecure defaults
        insecure_defaults = ["change-me-in-production", "secret-key", "your-secret-key"]
        if any(default in v.lower() for default in insecure_defaults):
            warnings.warn(
                "SECRET_KEY contains insecure default value. Change it in production!",
                UserWarning,
            )

        return v

    @field_validator("api_key_encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate API key encryption key strength."""
        if not v:
            warnings.warn(
                "API_KEY_ENCRYPTION_KEY is not set. Using insecure default for development!",
                UserWarning,
            )
            return "dev-encryption-key-change-in-prod-1234567890"

        if len(v) < 32:
            raise ValueError("API_KEY_ENCRYPTION_KEY must be at least 32 characters long")

        return v

    @model_validator(mode="after")
    def check_production_security(self):
        """Warn about insecure configuration in production mode."""
        if not self.debug:
            # Production mode checks
            if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
                warnings.warn(
                    "Database URL points to localhost in production mode. "
                    "This is likely a misconfiguration.",
                    UserWarning,
                )

            if "localhost" in self.redis_url or "127.0.0.1" in self.redis_url:
                warnings.warn(
                    "Redis URL points to localhost in production mode. "
                    "This is likely a misconfiguration.",
                    UserWarning,
                )

        return self

    # ===== Logging =====
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default="logs/app.log")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug

    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage.

        Args:
            api_key: Plain text API key.

        Returns:
            Hashed API key string.

        Note:
            For production, consider using bcrypt or argon2.
            This is a simple SHA-256 hash for demonstration.
        """
        salt = self.api_key_encryption_key[:16]
        return hashlib.sha256(f"{salt}{api_key}".encode()).hexdigest()

    def verify_api_key(self, plain_key: str, hashed_key: str) -> bool:
        """Verify a plain API key against a stored hash.

        Args:
            plain_key: Plain text API key to verify.
            hashed_key: Stored hash to compare against.

        Returns:
            True if the key matches.
        """
        return self.hash_api_key(plain_key) == hashed_key


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings instance.

    Returns:
        Settings instance cached for the application lifetime.
    """
    return Settings()