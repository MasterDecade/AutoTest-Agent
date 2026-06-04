"""Pydantic schemas for test generation and execution."""

from typing import Optional

from pydantic import BaseModel, Field


class TestGenerateRequest(BaseModel):
    """Request to generate test cases."""

    code: str = Field(..., min_length=1, description="Source code to generate tests for")
    language: str = Field(..., min_length=1, description="Programming language")
    framework: str = Field(default="", description="Test framework (auto-detect if empty)")
    num_cases: int = Field(default=5, ge=1, le=20, description="Number of test cases to generate")


class TestExpandRequest(BaseModel):
    """Request to expand existing test cases."""

    code: str = Field(..., min_length=1, description="Source code")
    existing_test_cases: str = Field(..., min_length=1, description="User-provided test case examples")
    language: str = Field(..., min_length=1, description="Programming language")
    framework: str = Field(default="", description="Test framework")


class TestRunRequest(BaseModel):
    """Request to execute tests in sandbox."""

    code: str = Field(..., min_length=1, description="Source code under test")
    test_code: str = Field(..., min_length=1, description="Generated test code to execute")
    language: str = Field(..., min_length=1, description="Programming language")
    framework: str = Field(default="", description="Test framework")
    timeout: Optional[int] = Field(default=None, ge=10, le=3600, description="Timeout in seconds")


class TestCaseItem(BaseModel):
    """A generated test case."""

    id: str = ""
    description: str = ""
    category: str = ""
    priority: str = "medium"
    test_code: str = ""


class TestSuiteResponse(BaseModel):
    """Response containing generated test suite."""

    language: str = ""
    framework: str = ""
    total_cases: int = 0
    test_code: str = ""
    test_cases: list[dict] = Field(default_factory=list)


class TestResultResponse(BaseModel):
    """Response from running tests in sandbox."""

    language: str = ""
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    pass_rate: float = 0.0
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    timed_out: bool = False
    coverage: float = 0.0