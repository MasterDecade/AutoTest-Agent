"""Celery task definitions for AutoTest-Agent.

Tasks are registered here and called by the API layer for async processing.
Integrates with analyzer, tester, and scoring modules.
"""

import asyncio

from celery.utils.log import get_task_logger

from src.common.database import SyncSessionLocal
from src.common.models import Submission, SubmissionStatus
from src.scheduler.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="autotest.analyze_code")
def analyze_code_task(self, submission_id: str) -> dict:
    """Async task: Analyze submitted code.

    Performs static code analysis using language-specific parsers
    and optionally enhances with LLM-based insights.

    Args:
        submission_id: ID of the submission to analyze.

    Returns:
        Analysis result dict with syntax, style, and complexity scores.
    """
    logger.info(f"Starting code analysis for submission {submission_id}")

    try:
        # Import here to avoid circular dependencies
        from src.analyzer.parsers.c_cpp_parser import CAnalyzer, CCPPAnalyzer
        from src.analyzer.parsers.java_parser import JavaAnalyzer
        from src.analyzer.parsers.python_parser import PythonAnalyzer

        db = SyncSessionLocal()
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")

            # Update status
            submission.status = SubmissionStatus.ANALYZING.value
            db.commit()

            # Select appropriate analyzer
            language = (submission.language or "python").lower()
            analyzers = {
                "python": PythonAnalyzer(),
                "cpp": CCPPAnalyzer(),
                "c++": CCPPAnalyzer(),
                "c": CAnalyzer(),
                "java": JavaAnalyzer(),
            }

            analyzer = analyzers.get(language, PythonAnalyzer())

            # Run analysis
            code = submission.code_content or ""
            result = analyzer.analyze(code, file_path=submission.file_name or "")

            logger.info(
                f"Analysis complete for {submission_id}: "
                f"errors={result.error_count}, warnings={result.warning_count}"
            )

            return {
                "submission_id": submission_id,
                "status": "completed",
                "analysis": result.to_dict(),
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Code analysis failed for {submission_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="autotest.run_tests")
def run_tests_task(self, submission_id: str, num_test_cases: int = 5) -> dict:
    """Async task: Run test cases against submitted code.

    Generates test cases using LLM and executes them in Docker sandbox.

    Args:
        submission_id: ID of the submission to test.
        num_test_cases: Number of test cases to generate.

    Returns:
        Test result dict with pass/fail counts and coverage.
    """
    logger.info(f"Starting test execution for submission {submission_id}")

    try:
        from src.llm.provider import get_provider_manager
        from src.sandbox.manager import SandboxConfig, SandboxManager
        from src.tester.generator import TestCaseGenerator
        from src.tester.runner import TestRunner

        db = SyncSessionLocal()
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")

            # Update status
            submission.status = SubmissionStatus.TESTING.value
            db.commit()

            code = submission.code_content or ""
            language = (submission.language or "python").lower()

            # Get LLM provider
            provider_manager = get_provider_manager()

            # Generate test cases
            logger.info(f"Generating {num_test_cases} test cases for {language}")
            suite = asyncio.run(
                TestCaseGenerator.generate(
                    code=code,
                    language=language,
                    num_cases=num_test_cases,
                    provider_manager=provider_manager,
                )
            )

            if not suite.test_cases:
                raise RuntimeError("No test cases generated")

            # Run tests in sandbox
            runner = TestRunner()
            run_result = asyncio.run(
                runner.run_tests(
                    code=code,
                    test_code=suite.to_text(),
                    language=language,
                )
            )

            logger.info(
                f"Test execution complete for {submission_id}: "
                f"passed={run_result.passed}, failed={run_result.failed}"
            )

            return {
                "submission_id": submission_id,
                "status": "completed",
                "test_result": {
                    "language": run_result.language,
                    "total": run_result.total,
                    "passed": run_result.passed,
                    "failed": run_result.failed,
                    "errors": run_result.errors,
                    "pass_rate": run_result.pass_rate,
                    "stdout": run_result.stdout[:3000],
                    "duration_ms": run_result.duration_ms,
                    "timed_out": run_result.timed_out,
                },
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Test execution failed for {submission_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30, name="autotest.generate_report")
def generate_report_task(self, submission_id: str) -> dict:
    """Async task: Generate test report for a submission.

    Combines analysis results and test results into a comprehensive report
    with multi-dimensional scoring.

    Args:
        submission_id: ID of the submission.

    Returns:
        Report data dict with overall score and dimension breakdown.
    """
    logger.info(f"Generating report for submission {submission_id}")

    try:
        from src.standards.scoring import ScoringEngine

        db = SyncSessionLocal()
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")

            # Get analysis result
            analysis_result = submission.analysis_result
            test_report = submission.test_report

            if not analysis_result or not test_report:
                raise ValueError("Analysis or test results not available")

            # Compute multi-dimensional score
            score = ScoringEngine.compute(
                analysis_result=analysis_result.to_dict(),
                test_result=test_report.to_dict(),
                coverage_percent=test_report.coverage_percent or 0.0,
            )

            # Update test report with scores
            test_report.overall_score = score.overall_score
            test_report.dimension_scores = score.dimension_scores
            db.commit()

            logger.info(
                f"Report generated for {submission_id}: "
                f"overall_score={score.overall_score}, grade={score.grade}"
            )

            return {
                "submission_id": submission_id,
                "status": "completed",
                "report": {
                    "overall_score": score.overall_score,
                    "grade": score.grade,
                    "dimension_scores": score.dimension_scores,
                    "dimension_weights": score.dimension_weights,
                },
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Report generation failed for {submission_id}: {exc}")
        raise self.retry(exc=exc)