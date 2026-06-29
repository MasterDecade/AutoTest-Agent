"""Test Runner — executes generated tests in isolated sandboxes."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.sandbox.image_builder import ImageBuilder
from src.sandbox.manager import SandboxConfig, SandboxManager, SandboxResult

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single test case execution."""

    case_id: str = ""
    description: str = ""
    passed: bool = False
    output: str = ""
    error: str = ""
    duration_ms: float = 0.0


@dataclass
class TestRunResult:
    """Aggregate result from running a test suite."""

    language: str = ""
    framework: str = ""
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    results: list[TestResult] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    timed_out: bool = False

    @property
    def pass_rate(self) -> float:
        """Calculate test pass rate."""
        if self.total == 0:
            return 0.0
        return round(self.passed / self.total * 100, 1)


class TestRunner:
    """Executes generated test suites in Docker sandboxes."""

    def __init__(self, mirror: str = ""):
        self.sandbox = SandboxManager(mirror=mirror)
        self.image_builder = ImageBuilder(mirror=mirror)

    async def run_tests(
        self,
        code: str,
        test_code: str,
        language: str,
        framework: str = "",
        timeout: int = 300,
        files: dict[str, str] | None = None,
    ) -> TestRunResult:
        """Execute generated test code in an isolated sandbox.

        Args:
            code: Source code to test (single-file mode).
            test_code: Generated test code to execute.
            language: Programming language.
            framework: Test framework name.
            timeout: Timeout in seconds.
            files: Optional multi-file mapping (relative_path -> content).

        Returns:
            TestRunResult with execution output and pass/fail counts.
        """
        build_config = self.image_builder.get_build_config(language)

        # Get the appropriate Docker image for the language
        docker_image = self.sandbox._default_image(language)

        if files:
            # Multi-file mode: use files dict directly
            config = SandboxConfig(
                language=language,
                image=docker_image,
                files=files,
                build_command=build_config.get("build_command", ""),
                test_command=build_config.get("test_command", ""),
                timeout=timeout,
            )
        else:
            # Single-file mode: combine code and tests
            combined_code = self._combine_code(code, test_code, language)
            config = SandboxConfig(
                language=language,
                image=docker_image,
                code=combined_code,
                build_command=build_config.get("build_command", ""),
                test_command=build_config.get("test_command", ""),
                timeout=timeout,
            )

        try:
            sandbox_result = await self.sandbox.create_and_run(config)

            # Parse results
            run_result = self._parse_results(sandbox_result, language)

            return run_result

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return TestRunResult(
                language=language,
                errors=1,
                stderr=str(e),
            )

    def _combine_code(self, code: str, test_code: str, language: str) -> str:
        """Combine source code with test code.

        Args:
            code: Source code.
            test_code: Test code.
            language: Language.

        Returns:
            Combined code string.
        """
        if language == "python":
            return f"{code}\n\n# ===== Generated Tests =====\n{test_code}"
        elif language in ("cpp", "c"):
            return f"// Source code:\n{code}\n\n// Test code:\n{test_code}"
        elif language == "java":
            return f"{code}\n\n{test_code}"
        return f"{code}\n\n{test_code}"

    def _parse_results(self, sandbox_result: SandboxResult, language: str) -> TestRunResult:
        """Parse sandbox output into structured test results.

        Args:
            sandbox_result: Raw sandbox execution result.
            language: Language identifier.

        Returns:
            Parsed TestRunResult.
        """
        result = TestRunResult(
            language=language,
            stdout=sandbox_result.stdout,
            stderr=sandbox_result.stderr,
            duration_ms=sandbox_result.duration_ms,
            timed_out=sandbox_result.timed_out,
        )

        output = sandbox_result.stdout

        if sandbox_result.timed_out:
            result.errors = 1
            result.stderr = "Test execution timed out"
            return result

        # Simple pass/fail parsing from test output
        # Pytest format: "X passed, Y failed"
        if language == "python":
            import re
            passed_match = re.search(r"(\d+)\s+passed", output)
            failed_match = re.search(r"(\d+)\s+failed", output)

            if passed_match:
                result.passed = int(passed_match.group(1))
            if failed_match:
                result.failed = int(failed_match.group(1))
            result.total = result.passed + result.failed

            if "no tests" in output.lower() or result.total == 0:
                result.errors = 1
                result.stderr = "No test results found in output"

        elif language in ("cpp", "c"):
            if sandbox_result.exit_code == 0:
                result.passed = 1
                result.total = 1
            else:
                result.failed = 1
                result.total = 1

        elif language == "java":
            import re
            passed_match = re.search(r"(\d+)\s+(?:tests\s+)?successful", output)
            failed_match = re.search(r"(\d+)\s+(?:tests\s+)?failed", output)
            if passed_match:
                result.passed = int(passed_match.group(1))
            if failed_match:
                result.failed = int(failed_match.group(1))
            result.total = max(result.passed + result.failed, 1)

        else:
            if sandbox_result.exit_code == 0:
                result.passed = 1
            else:
                result.failed = 1
            result.total = 1

        return result
