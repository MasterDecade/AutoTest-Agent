"""API routes for test case generation and execution."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from src.api.schemas.tests import (
    TestExpandRequest,
    TestGenerateRequest,
    TestRunRequest,
    TestResultResponse,
    TestSuiteResponse,
)
from src.common.config import get_settings
from src.llm.provider import get_provider_manager
from src.tester.coverage import CoverageAnalyzer
from src.tester.generator import TestCaseGenerator
from src.tester.runner import TestRunner

router = APIRouter(prefix="/api/tests", tags=["tests"])

settings = get_settings()


@router.post("/generate", response_model=TestSuiteResponse)
async def generate_tests(request: TestGenerateRequest):
    """Generate executable test cases using LLM.

    Requires a configured LLM provider.
    The generated test code is ready to execute in a sandbox.
    """
    try:
        suite = await TestCaseGenerator.generate(
            code=request.code,
            language=request.language,
            framework=request.framework,
            num_cases=request.num_cases,
            provider_manager=get_provider_manager(),
        )

        return TestSuiteResponse(
            language=suite.language,
            framework=suite.framework,
            total_cases=len(suite.test_cases),
            test_code=suite.to_text(),
            test_cases=[
                {
                    "id": tc.id,
                    "description": tc.description,
                    "category": tc.category,
                    "priority": tc.priority,
                    "test_code": tc.test_code[:500],
                }
                for tc in suite.test_cases
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.post("/expand", response_model=TestSuiteResponse)
async def expand_tests(request: TestExpandRequest):
    """Expand existing test cases with LLM.

    Takes user-provided test cases as examples and generates
    additional test cases covering missing scenarios.
    """
    try:
        suite = await TestCaseGenerator.expand(
            code=request.code,
            existing_test_cases=request.existing_test_cases,
            language=request.language,
            framework=request.framework,
            provider_manager=get_provider_manager(),
        )

        return TestSuiteResponse(
            language=suite.language,
            framework=suite.framework,
            total_cases=len(suite.test_cases),
            test_code=suite.to_text(),
            test_cases=[
                {
                    "id": tc.id,
                    "description": tc.description,
                    "test_code": tc.test_code[:500],
                }
                for tc in suite.test_cases
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test expansion failed: {str(e)}")


@router.post("/run", response_model=TestResultResponse)
async def run_tests(request: TestRunRequest):
    """Execute generated test code in an isolated Docker sandbox.

    Creates a container, compiles the code (if applicable),
    runs tests, and returns results.
    """
    runner = TestRunner(mirror=settings.docker_mirror)

    try:
        result = await runner.run_tests(
            code=request.code,
            test_code=request.test_code,
            language=request.language,
            framework=request.framework or "",
            timeout=request.timeout or settings.sandbox_timeout,
        )

        # Estimate coverage
        coverage = CoverageAnalyzer.estimate_from_output(
            result.stdout,
            code_lines=len(request.code.split("\n")),
        )

        return TestResultResponse(
            language=result.language,
            total=result.total,
            passed=result.passed,
            failed=result.failed,
            errors=result.errors,
            pass_rate=result.pass_rate,
            stdout=result.stdout[:5000],
            stderr=result.stderr[:2000],
            duration_ms=result.duration_ms,
            timed_out=result.timed_out,
            coverage=coverage.line_coverage,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")


@router.post("/generate-and-run", response_model=TestResultResponse)
async def generate_and_run(request: TestGenerateRequest):
    """Generate tests, run them, and return combined results.

    Convenience endpoint combining generate + run in one call.
    """
    # Generate tests
    suite = await TestCaseGenerator.generate(
        code=request.code,
        language=request.language,
        framework=request.framework,
        num_cases=request.num_cases,
        provider_manager=get_provider_manager(),
    )

    # Run tests
    runner = TestRunner(mirror=settings.docker_mirror)
    result = await runner.run_tests(
        code=request.code,
        test_code=suite.to_text(),
        language=request.language,
        timeout=settings.sandbox_timeout,
    )

    coverage = CoverageAnalyzer.estimate_from_output(
        result.stdout,
        code_lines=len(request.code.split("\n")),
    )

    return TestResultResponse(
        language=result.language,
        total=result.total,
        passed=result.passed,
        failed=result.failed,
        errors=result.errors,
        pass_rate=result.pass_rate,
        stdout=result.stdout[:5000],
        stderr=result.stderr[:2000],
        duration_ms=result.duration_ms,
        timed_out=result.timed_out,
        coverage=coverage.line_coverage,
    )