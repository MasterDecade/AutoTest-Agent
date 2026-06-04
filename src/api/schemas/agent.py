"""Pydantic schemas for Agent orchestration endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class AgentDetectRequest(BaseModel):
    """Request to run the full auto-test detection pipeline."""

    code: str = Field(..., min_length=1, description="Source code to test")
    language: Optional[str] = Field(default=None, description="Programming language (auto-detect if empty)")
    num_test_cases: int = Field(default=5, ge=1, le=20, description="Number of test cases to generate")
    auto_approve: bool = Field(default=False, description="Skip human review and auto-approve plan")


class AgentDetectResponse(BaseModel):
    """Response from the detection pipeline."""

    submission_id: str = ""
    status: str = ""
    stage: str = ""
    analysis: Optional[dict] = None
    plan: Optional[dict] = None
    test_result: Optional[dict] = None
    score: Optional[dict] = None
    errors: list[str] = Field(default_factory=list)


class AgentStatusResponse(BaseModel):
    """Current status of a detection workflow."""

    submission_id: str = ""
    status: str = ""
    stage: str = ""
    errors: list[str] = Field(default_factory=list)