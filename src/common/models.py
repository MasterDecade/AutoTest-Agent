"""Database ORM models for AutoTest-Agent.

Core entities: Project, Submission, TestStandard, TestCase,
AnalysisResult, TestReport, LanguageConfig, ScoringTemplate.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base


# ===== Helper Functions =====
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


# ===== Enums =====
class SubmissionStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScoringType(str, Enum):
    AUTO = "auto"
    LLM = "llm"
    MANUAL = "manual"
    HYBRID = "hybrid"


# ===== Core Entities =====
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    submissions: Mapped[List["Submission"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    test_standards: Mapped[List["TestStandard"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project {self.id}: {self.name}>"


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitter_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    code_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=SubmissionStatus.PENDING.value, index=True
    )

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="submissions")
    analysis_result: Mapped[Optional["AnalysisResult"]] = relationship(
        back_populates="submission", uselist=False, cascade="all, delete-orphan"
    )
    test_report: Mapped[Optional["TestReport"]] = relationship(
        back_populates="submission", uselist=False, cascade="all, delete-orphan"
    )
    test_cases: Mapped[List["TestCase"]] = relationship(back_populates="submission", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Submission {self.id}: {self.submitter_name}>"


class TestStandard(Base):
    __tablename__ = "test_standards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_framework: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    scoring_template_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    scoring_rules: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    code_style_rules: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="test_standards")
    case_templates: Mapped[List["TestCaseTemplate"]] = relationship(
        back_populates="test_standard", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestStandard {self.id}: {self.name} v{self.version}>"


class TestCaseTemplate(Base):
    __tablename__ = "test_case_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    test_standard_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("test_standards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_spec: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    test_standard: Mapped["TestStandard"] = relationship(back_populates="case_templates")

    def __repr__(self) -> str:
        return f"<TestCaseTemplate {self.id}: {self.description[:50]}>"


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_spec: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actual_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(20), default="llm")
    priority: Mapped[str] = mapped_column(String(20), default="medium")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="test_cases")

    def __repr__(self) -> str:
        return f"<TestCase {self.id}: {'PASS' if self.passed else 'FAIL' if self.passed is False else 'PENDING'}>"


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    syntax_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    style_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    complexity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    issues: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="analysis_result")

    def __repr__(self) -> str:
        return f"<AnalysisResult {self.id}>"


class TestReport(Base):
    __tablename__ = "test_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0)
    coverage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dimension_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    report_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="test_report")

    def __repr__(self) -> str:
        return f"<TestReport {self.id}: {self.overall_score}>"


class LanguageConfig(Base):
    __tablename__ = "language_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="latest")
    docker_image: Mapped[str] = mapped_column(String(500), nullable=False)
    file_extensions: Mapped[dict] = mapped_column(JSONB, default=list)
    build_command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_frameworks: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    static_analyzers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    prompt_templates: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    def __repr__(self) -> str:
        return f"<LanguageConfig {self.name} ({self.version})>"


class ScoringTemplate(Base):
    __tablename__ = "scoring_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    dimensions: Mapped[List["ScoringDimension"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ScoringTemplate {self.id}: {self.name}>"


class ScoringDimension(Base):
    __tablename__ = "scoring_dimensions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scoring_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=10)
    max_score: Mapped[float] = mapped_column(Float, default=100.0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scoring_type: Mapped[str] = mapped_column(
        String(20), default=ScoringType.AUTO.value
    )
    scoring_rules: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    template: Mapped["ScoringTemplate"] = relationship(back_populates="dimensions")

    def __repr__(self) -> str:
        return f"<ScoringDimension {self.key}: weight={self.weight}>"


class LLMProviderConfig(Base):
    __tablename__ = "llm_provider_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    provider_type: Mapped[str] = mapped_column(String(100), nullable=False)
    api_base: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    def __repr__(self) -> str:
        return f"<LLMProviderConfig {self.name}: {self.model_name}>"