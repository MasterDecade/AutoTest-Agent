"""Unit tests for exception classes."""

import pytest
from src.common.exceptions import (
    AutoTestError,
    NotFoundError,
    ValidationError,
    SandboxError,
    LLMProviderError,
    TaskSchedulingError,
)


class TestExceptions:
    """Test custom exception classes."""

    def test_autotest_error_base(self):
        """Test base AutoTestError."""
        error = AutoTestError("Test error", code="TEST_ERROR")
        assert str(error) == "Test error"
        assert error.code == "TEST_ERROR"

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Project", "123")
        assert "not found" in str(error)
        assert error.resource == "Project"
        assert error.identifier == "123"
        assert error.code == "NOT_FOUND"

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input", field="email")
        assert error.message == "Invalid input"
        assert error.field == "email"
        assert error.code == "VALIDATION_ERROR"

    def test_sandbox_error(self):
        """Test SandboxError."""
        error = SandboxError("Execution failed", sandbox_id="sandbox-123")
        assert error.message == "Execution failed"
        assert error.sandbox_id == "sandbox-123"
        assert error.code == "SANDBOX_ERROR"

    def test_llm_provider_error(self):
        """Test LLMProviderError."""
        error = LLMProviderError("API timeout", provider="openai")
        assert error.message == "API timeout"
        assert error.provider == "openai"
        assert error.code == "LLM_ERROR"

    def test_task_scheduling_error(self):
        """Test TaskSchedulingError."""
        error = TaskSchedulingError("Queue full")
        assert error.message == "Queue full"
        assert error.code == "SCHEDULING_ERROR"
