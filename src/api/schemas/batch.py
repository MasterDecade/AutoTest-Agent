"""Pydantic schemas for batch processing."""

from typing import Optional

from pydantic import BaseModel, Field


class BatchSubmitRequest(BaseModel):
    """Request to submit a batch of tasks."""

    project_id: str = Field(..., min_length=1, description="Project identifier")
    submissions: list[dict] = Field(..., min_length=1, description="List of submissions")
    priority: Optional[int] = Field(default=0, description="Batch priority")


class BatchStatusResponse(BaseModel):
    """Current batch processing status."""

    pending: int = 0
    active: int = 0
    stats: dict = Field(default_factory=dict)