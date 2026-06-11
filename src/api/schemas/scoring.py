"""Pydantic schemas for scoring and template management."""

from typing import Optional

from pydantic import BaseModel, Field


class DimensionDef(BaseModel):
    """A single scoring dimension definition."""

    name: str = Field(..., min_length=1, description="Dimension name, e.g. '功能正确性'")
    key: str = Field(..., min_length=1, description="Dimension key, e.g. 'functionality'")
    weight: int = Field(default=10, ge=0, le=100, description="Weight (0-100)")
    scoring_type: str = Field(default="auto", description="auto|llm|manual|hybrid")
    description: str = Field(default="", description="What this dimension evaluates")


class TemplateCreateRequest(BaseModel):
    """Request to create a custom scoring template."""

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(default="", description="Template description")
    dimensions: list[DimensionDef] = Field(..., min_length=1, description="Scoring dimensions")


class TemplateResponse(BaseModel):
    """A scoring template with all dimensions."""

    template_id: str = ""
    name: str = ""
    description: str = ""
    is_default: bool = False
    dimensions: list[dict] = Field(default_factory=list)


class ComputeScoreRequest(BaseModel):
    """Request to compute a submission's score."""

    submission_id: Optional[str] = Field(default=None, description="Submission identifier (for comparison)")
    submitter_name: Optional[str] = Field(default=None, description="Submitter name (for comparison)")
    analysis: Optional[dict] = Field(default=None, description="Analysis result (syntax_score, style_score, etc.)")
    tests: Optional[dict] = Field(default=None, description="Test result (total, passed, failed, duration_ms)")
    coverage: Optional[float] = Field(default=None, ge=0, le=100, description="Test coverage percentage")
    template_id: Optional[str] = Field(default=None, description="Scoring template ID (uses default if empty)")


class ScoreResponse(BaseModel):
    """Response from score computation."""

    overall_score: float = 0.0
    grade: str = ""
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    dimension_weights: dict[str, int] = Field(default_factory=dict)


class ScoredSubmission(BaseModel):
    """A scored submission for comparison/ranking."""

    submission_id: str = ""
    submitter_name: str = ""
    overall_score: float = 0.0
    grade: str = ""
    dimension_scores: dict[str, float] = Field(default_factory=dict)