"""Pydantic schemas for language configuration."""

from typing import Optional

from pydantic import BaseModel, Field


class LanguageConfigCreateRequest(BaseModel):
    """Request to create a new language configuration."""

    name: str = Field(..., min_length=1, max_length=100, description="Language identifier")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable name")
    version: str = Field(default="latest", description="Language version")
    docker_image: str = Field(..., description="Docker image for sandbox")
    extensions: list[str] = Field(default_factory=list, description="File extensions")
    test_frameworks: list[str] = Field(default_factory=list, description="Supported test frameworks")
    static_analyzers: list[str] = Field(default_factory=list, description="Static analysis tools")


class LanguageConfigUpdateRequest(BaseModel):
    """Request to update an existing language configuration."""

    display_name: Optional[str] = None
    version: Optional[str] = None
    docker_image: Optional[str] = None
    extensions: Optional[list[str]] = None
    test_frameworks: Optional[list[str]] = None
    static_analyzers: Optional[list[str]] = None
    is_active: Optional[bool] = None


class LanguageConfigResponse(BaseModel):
    """Language configuration response."""

    name: str
    display_name: str
    version: str = "latest"
    docker_image: str = ""
    extensions: list[str] = Field(default_factory=list)
    test_frameworks: list[str] = Field(default_factory=list)
    static_analyzers: list[str] = Field(default_factory=list)
    is_active: bool = True
    is_builtin: bool = True