"""Scoring engine — calculates multi-dimensional scores for code submissions."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScoringDimensionDef:
    """Definition of a single scoring dimension."""

    name: str = ""
    key: str = ""
    weight: int = 10  # 0-100, will be normalized
    max_score: float = 100.0
    scoring_type: str = "auto"  # auto, llm, manual, hybrid
    description: str = ""
    enabled: bool = True


@dataclass
class ScoringResult:
    """Multi-dimensional scoring result for a submission."""

    submission_id: str = ""
    overall_score: float = 0.0
    dimension_scores: dict[str, float] = field(default_factory=dict)
    dimension_weights: dict[str, int] = field(default_factory=dict)
    grade: str = ""
    summary: str = ""

    @property
    def weighted_total(self) -> float:
        """Calculate weighted total score."""
        total_weight = sum(self.dimension_weights.values())
        if total_weight == 0:
            return 0.0
        weighted = 0.0
        for key, score in self.dimension_scores.items():
            weight = self.dimension_weights.get(key, 0)
            weighted += score * weight
        return round(weighted / total_weight, 2)


class ScoringEngine:
    """Calculates comprehensive scores for code submissions.

    Uses configurable dimensions with weights.
    Default dimensions follow the standard AutoTest-Agent model.
    """

    @classmethod
    def default_dimensions(cls) -> list[ScoringDimensionDef]:
        """Get the system default scoring dimensions."""
        return [
            ScoringDimensionDef(name="功能正确性", key="functionality", weight=40, scoring_type="auto"),
            ScoringDimensionDef(name="代码规范", key="code_style", weight=15, scoring_type="auto"),
            ScoringDimensionDef(name="代码质量", key="code_quality", weight=15, scoring_type="auto"),
            ScoringDimensionDef(name="测试覆盖率", key="test_coverage", weight=15, scoring_type="auto"),
            ScoringDimensionDef(name="性能效率", key="performance", weight=10, scoring_type="auto"),
            ScoringDimensionDef(name="文档注释", key="documentation", weight=5, scoring_type="llm"),
        ]

    @classmethod
    def compute(
        cls,
        analysis_result: dict,
        test_result: dict,
        coverage_percent: float = 0.0,
        dimensions: list[ScoringDimensionDef] = None,
    ) -> ScoringResult:
        """Compute multi-dimensional scores from analysis and test results.

        Args:
            analysis_result: Dict from static analysis (syntax_score, style_score, etc.).
            test_result: Dict from test execution (passed, failed, total).
            coverage_percent: Test coverage percentage.
            dimensions: Optional custom dimension definitions.

        Returns:
            ScoringResult with dimension and overall scores.
        """
        if dimensions is None:
            dimensions = cls.default_dimensions()

        result = ScoringResult()

        for dim in dimensions:
            if not dim.enabled:
                continue

            score = cls._compute_dimension(dim, analysis_result, test_result, coverage_percent)
            result.dimension_scores[dim.key] = score
            result.dimension_weights[dim.key] = dim.weight

        result.overall_score = result.weighted_total
        result.grade = cls._calculate_grade(result.overall_score)

        return result

    @classmethod
    def _compute_dimension(
        cls,
        dim: ScoringDimensionDef,
        analysis: dict,
        tests: dict,
        coverage: float,
    ) -> float:
        """Compute score for a single dimension.

        Args:
            dim: Dimension definition.
            analysis: Analysis result dict.
            tests: Test result dict.
            coverage: Coverage percent.

        Returns:
            Score from 0-100.
        """
        if dim.key == "functionality":
            total = tests.get("total", 0)
            passed = tests.get("passed", 0)
            if total == 0:
                return 0.0
            return round(passed / total * 100, 1)

        elif dim.key == "code_style":
            return analysis.get("style_score", 100.0)

        elif dim.key == "code_quality":
            return analysis.get("syntax_score", 100.0)

        elif dim.key == "test_coverage":
            return round(coverage, 1)

        elif dim.key == "performance":
            duration = tests.get("duration_ms", 0)
            if duration == 0:
                return 100.0
            # Score decreases with longer execution time
            # < 100ms = 100, > 5000ms = 0
            return max(0.0, min(100.0, 100 - duration / 50))

        elif dim.key == "documentation":
            metrics = analysis.get("metrics", {})
            comment_ratio = metrics.get("comment_ratio", 0)
            return min(100.0, comment_ratio * 3)  # Simplified

        return 100.0  # Default full score

    @classmethod
    def _calculate_grade(cls, score: float) -> str:
        """Convert numerical score to letter grade.

        Args:
            score: Score from 0-100.

        Returns:
            Letter grade (A/B/C/D/F).
        """
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        return "F"