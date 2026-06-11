"""Pydantic schemas for document analysis and inspection plans."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ===== Document Analysis =====

class DocumentAnalysisResponse(BaseModel):
    """Response after uploading/analyzing a document."""

    file_name: str = Field(..., description="Original file name")
    text_preview: str = Field(default="", description="First 1000 chars of extracted text")
    text_length: int = Field(default=0, description="Total extracted text length")
    analysis: Optional[Any] = Field(default=None, description="LLM analysis result")


# ===== Inspection Plan =====

class TestCasePlanItem(BaseModel):
    """A planned test case in the inspection plan."""

    id: str = Field(..., description="Test case ID, e.g. TC-001")
    description: str = Field(..., description="What the test case verifies")
    priority: str = Field(default="medium", description="critical|high|medium|low")
    category: str = Field(default="happy_path", description="Test category")
    estimated_count: int = Field(default=3, ge=1, description="Estimated number of test cases this represents")


class ScoringDimensionItem(BaseModel):
    """A scoring dimension in the inspection plan."""

    name: str = Field(..., description="Dimension name, e.g. '功能正确性'")
    weight: int = Field(..., ge=0, le=100, description="Weight percentage (0-100)")
    scoring_type: str = Field(default="auto", description="auto|llm")
    description: str = Field(default="", description="What this dimension evaluates")


class EnvironmentConfig(BaseModel):
    """Environment configuration for code testing."""

    base_image: str = Field(default="", description="Docker base image")
    dependencies: list[str] = Field(default_factory=list, description="Dependency packages")
    build_command: str = Field(default="", description="Build/compile command")
    test_command: str = Field(default="", description="Test execution command")


class InspectionPlanGenerateRequest(BaseModel):
    """Request to generate an inspection plan."""

    project_id: Optional[str] = Field(default=None, description="Project ID")
    project_name: Optional[str] = Field(default="Unknown Project", description="Project name")
    code: str = Field(..., min_length=1, description="Code to analyze")
    language: Optional[str] = Field(default=None, description="Programming language (auto-detect if empty)")
    document_texts: Optional[list[str]] = Field(default=None, description="Document texts to analyze")
    existing_test_cases: Optional[list[dict]] = Field(default=None, description="User-provided test case examples")


class InspectionPlanResponse(BaseModel):
    """An inspection plan (response)."""

    plan_id: str = Field(..., description="Unique plan identifier")
    project_id: str = Field(default="", description="Associated project ID")
    plan_version: str = Field(default="1.0")
    status: str = Field(default="pending_review", description="pending_review|approved|rejected|executed")

    languages: list[str] = Field(default_factory=list)
    files_to_analyze: int = Field(default=0)
    estimated_duration_minutes: int = Field(default=5)

    test_framework: str = Field(default="")
    test_framework_config: dict = Field(default_factory=dict)

    test_cases_plan: list[dict] = Field(default_factory=list, description="Planned test cases")
    scoring_dimensions: list[dict] = Field(default_factory=list, description="Planned scoring dimensions")
    code_style_checks: list[str] = Field(default_factory=list, description="Planned code style checks")

    environment_config: dict = Field(default_factory=dict)

    risk_notes: list[str] = Field(default_factory=list)
    reviewer_notes: str = Field(default="")

    generated_at: str = Field(default="")
    reviewed_at: str = Field(default="")
    reviewed_by: str = Field(default="")


class PlanReviewSubmitRequest(BaseModel):
    """Request to approve or reject an inspection plan."""

    approve: bool = Field(..., description="True to approve, False to reject")
    reviewer_notes: Optional[str] = Field(default="", description="Reviewer comments")
    reviewer_name: Optional[str] = Field(default="anonymous", description="Reviewer name")

    # Optional modifications (applied on approval)
    modified_test_cases: Optional[list[dict]] = Field(default=None)
    modified_scoring_dimensions: Optional[list[dict]] = Field(default=None)
    modified_code_style_checks: Optional[list[str]] = Field(default=None)


class PlanReviewResponse(BaseModel):
    """Response after reviewing an inspection plan."""

    plan_id: str
    status: str = Field(..., description="approved|rejected")
    message: str = Field(default="")