"""Unit tests for configuration module."""

import pytest
from src.common.config import Settings


class TestSettings:
    """Test Settings class validation and defaults."""

    def test_default_settings(self):
        """Test default settings initialization."""
        settings = Settings()
        assert settings.debug is False
        assert settings.api_port == 8080
        assert settings.database_pool_size == 10

    def test_secret_key_validation_min_length(self):
        """Test secret key minimum length validation."""
        with pytest.raises(ValueError, match="at least 32 characters"):
            Settings(secret_key="short")

    def test_secret_key_accepts_valid_key(self):
        """Test valid secret key is accepted."""
        settings = Settings(secret_key="a" * 32)
        assert settings.secret_key == "a" * 32

    def test_database_url_default_asyncpg(self):
        """Test default database URL uses asyncpg."""
        settings = Settings()
        assert "asyncpg" in settings.database_url

    def test_llm_providers_json_validation(self):
        """Test LLM providers JSON validation."""
        with pytest.raises(ValueError, match="valid JSON"):
            Settings(llm_providers="invalid json")

    def test_get_llm_providers_dict(self):
        """Test parsing LLM providers to dict."""
        settings = Settings(llm_providers='{"openai": {"api_key": "test"}}')
        providers = settings.get_llm_providers_dict()
        assert "openai" in providers

    def test_is_development_property(self):
        """Test is_development property."""
        settings_dev = Settings(debug=True)
        assert settings_dev.is_development is True

        settings_prod = Settings(debug=False)
        assert settings_prod.is_development is False

    def test_api_key_hashing(self):
        """Test API key hashing functionality."""
        settings = Settings()
        plain_key = "my-secret-api-key"
        hashed = settings.hash_api_key(plain_key)
        assert len(hashed) > 0
        assert hashed != plain_key

    def test_api_key_verification(self):
        """Test API key verification."""
        settings = Settings()
        plain_key = "my-secret-api-key"
        hashed = settings.hash_api_key(plain_key)
        assert settings.verify_api_key(plain_key, hashed) is True
        assert settings.verify_api_key("wrong-key", hashed) is False
