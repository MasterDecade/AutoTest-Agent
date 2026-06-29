"""Pydantic schemas for project management."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    language: Optional[str] = Field(default=None, max_length=50, description="Target programming language")


class ProjectResponse(BaseModel):
    """Project information returned to client."""

    id: str
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    submission_count: int = 0

    model_config = {"from_attributes": True}
