"""Coverage analyzer — collects and reports test coverage metrics."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CoverageResult:
    """Code coverage results."""

    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    total_lines: int = 0
    covered_lines: int = 0
    uncovered_lines: list[int] = field(default_factory=list)
    files_analyzed: int = 0


class CoverageAnalyzer:
    """Analyzes test coverage from test output."""

    @classmethod
    def parse_pytest_cov(cls, output: str) -> CoverageResult:
        """Parse pytest-cov coverage output.

        Args:
            output: Stdout from pytest with coverage.

        Returns:
            CoverageResult with metrics.
        """
        import re

        result = CoverageResult()
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            result.line_coverage = float(match.group(1))
        return result

    @classmethod
    def estimate_from_output(cls, test_output: str, code_lines: int = 0) -> CoverageResult:
        """Estimate coverage based on test result analysis.

        Args:
            test_output: Test execution output.
            code_lines: Number of lines in the source code.

        Returns:
            Estimated coverage result.
        """
        import re

        result = CoverageResult()
        if code_lines > 0:
            result.total_lines = code_lines

        # Count passed tests as coverage indicator
        passed_match = re.search(r"(\d+)\s+passed", test_output)
        if passed_match and code_lines > 0:
            passed = int(passed_match.group(1))
            # Rough estimate: more passed tests = higher coverage
            result.line_coverage = min(passed * 15, 100.0)
            result.covered_lines = int(code_lines * result.line_coverage / 100)

        return result