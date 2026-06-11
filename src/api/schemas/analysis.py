"""Pydantic schemas for code analysis endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request to analyze source code."""

    code: str = Field(..., min_length=1, description="Source code to analyze")
    language: Optional[str] = Field(default=None, description="Programming language (auto-detect if empty)")
    file_path: Optional[str] = Field(default=None, description="Original file path")
    use_llm: bool = Field(default=False, description="Include LLM-enhanced analysis")


class IssueItem(BaseModel):
    """A code issue found during analysis."""

    line: int = 0
    column: int = 0
    severity: str = "warning"
    message: str = ""
    rule: str = ""
    category: str = ""


class AnalysisResponse(BaseModel):
    """Response from code analysis."""

    language: str = ""
    file_path: str = ""
    summary: str = ""
    syntax_score: float = 100.0
    style_score: float = 100.0
    complexity_score: float = 100.0
    error_count: int = 0
    warning_count: int = 0
    total_issues: int = 0
    issues: list[IssueItem] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)