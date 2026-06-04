"""Static code analyzer base and common utilities.

Provides a unified interface for multi-language static analysis.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Issue:
    """A code issue found during analysis."""

    line: int = 0
    column: int = 0
    severity: str = "warning"  # error, warning, info
    message: str = ""
    rule: str = ""
    category: str = ""  # syntax, style, bug, complexity, security


@dataclass
class AnalysisResult:
    """Result of a static code analysis."""

    language: str = ""
    file_path: str = ""
    summary: str = ""
    issues: list[Issue] = field(default_factory=list)
    syntax_score: float = 100.0
    style_score: float = 100.0
    complexity_score: float = 100.0
    metrics: dict = field(default_factory=dict)
    raw_output: str = ""

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "file_path": self.file_path,
            "summary": self.summary,
            "syntax_score": self.syntax_score,
            "style_score": self.style_score,
            "complexity_score": self.complexity_score,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "total_issues": len(self.issues),
            "issues": [
                {
                    "line": i.line,
                    "column": i.column,
                    "severity": i.severity,
                    "message": i.message,
                    "rule": i.rule,
                    "category": i.category,
                }
                for i in self.issues
            ],
            "metrics": self.metrics,
        }


class StaticAnalyzerBase:
    """Base class for language-specific static analyzers."""

    language: str = "unknown"
    supported_extensions: tuple[str, ...] = ()

    def can_analyze(self, file_path: str, language: str = "") -> bool:
        """Check if this analyzer can handle the given file/language.

        Args:
            file_path: Path to the source file.
            language: Detected language identifier.

        Returns:
            True if this analyzer supports the file.
        """
        if language and language == self.language:
            return True
        if file_path.endswith(self.supported_extensions):
            return True
        return False

    def analyze(self, code: str, file_path: str = "", use_llm: bool = False) -> AnalysisResult:
        """Analyze source code for issues.

        Args:
            code: Source code string.
            file_path: Optional file path for reference.
            use_llm: Whether to use LLM for enhanced analysis.

        Returns:
            AnalysisResult with all found issues.
        """
        raise NotImplementedError

    async def analyze_with_llm(self, code: str, file_path: str = "", provider_manager=None) -> AnalysisResult:
        """Analyze code using LLM with language-specific prompt.

        Args:
            code: Source code string.
            file_path: Optional file path.
            provider_manager: LLM provider manager.

        Returns:
            AnalysisResult with LLM findings.
        """
        result = self.analyze(code, file_path)

        if provider_manager is None:
            from src.llm.provider import get_provider_manager
            provider_manager = get_provider_manager()

        try:
            from src.llm.base import BaseProvider
            from src.llm.prompt_templates.code_analysis import code_analysis_prompt

            prompt = code_analysis_prompt(
                language=self.language,
                code=code,
                project_context="",
            )

            response = await provider_manager.chat_with_fallback(
                messages=[BaseProvider.user(prompt)],
                temperature=0.2,
                max_tokens=4096,
            )

            result.summary = response.content[:500]
            result.raw_output = response.content
        except Exception as e:
            logger.warning(f"LLM analysis supplement failed: {e}")

        return result

    @staticmethod
    def score_from_issues(issues: list[Issue], max_score: float = 100.0) -> float:
        """Calculate a score based on issue count and severity.

        Args:
            issues: List of found issues.
            max_score: Maximum possible score.

        Returns:
            Calculated score (0 - max_score).
        """
        if not issues:
            return max_score

        deductions = 0
        for issue in issues:
            if issue.severity == "error":
                deductions += 5
            elif issue.severity == "warning":
                deductions += 2
            elif issue.severity == "info":
                deductions += 0.5

        return max(0.0, max_score - deductions)