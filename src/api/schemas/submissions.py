"""Pydantic schemas for code submission management."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SubmissionFileInfo(BaseModel):
    """Information about a single file in a submission."""

    file_name: str
    file_path: str
    language: Optional[str] = None
    size_bytes: int = 0


class SubmissionUploadResponse(BaseModel):
    """Response after uploading code files."""

    submission_id: str
    project_id: str
    submitter_name: Optional[str] = None
    files: list[SubmissionFileInfo] = Field(default_factory=list)
    detected_language: Optional[str] = None
    total_files: int = 0
    status: str = "pending"


class BatchUploadResponse(BaseModel):
    """Response after batch uploading submissions."""

    submissions: list[SubmissionUploadResponse] = Field(default_factory=list)
    total: int = 0
    message: str = ""


class SubmissionListResponse(BaseModel):
    """A submission in a list."""

    submission_id: str
    project_id: str
    submitter_name: Optional[str] = None
    file_name: Optional[str] = None
    language: Optional[str] = None
    status: str = "pending"
    submitted_at: Optional[str] = None
    completed_at: Optional[str] = None
