"""Agent Orchestrator — connects all modules into a complete auto-test pipeline.

Pipeline: analyze → plan → approve → test → score
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from src.agent.workflow import WorkflowEngine, WorkflowStage, WorkflowStatus

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    """Complete result from an orchestrated detection pipeline."""

    submission_id: str = ""
    status: str = ""
    stage: str = ""

    # Results from each stage
    analysis: Optional[dict] = None
    plan: Optional[dict] = None
    test_result: Optional[dict] = None
    score: Optional[dict] = None

    errors: list[str] = field(default_factory=list)


class AgentOrchestrator:
    """Orchestrates the full auto-test pipeline.

    Pipeline stages:
    1. ANALYSIS — static code analysis
    2. PLAN — generate inspection plan (requires LLM)
    3. REVIEW — wait for human approval
    4. TEST — generate + run test cases in sandbox
    5. SCORE — compute multi-dimensional scores
    """

    def __init__(self, provider_manager=None, sandbox_mirror: str = ""):
        self.provider_manager = provider_manager
        self.sandbox_mirror = sandbox_mirror

    async def run_full_pipeline(
        self,
        submission_id: str,
        code: str,
        language: str = "",
        num_test_cases: int = 5,
        auto_approve: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> OrchestratorResult:
        """Run the complete auto-test pipeline.

        Args:
            submission_id: Unique submission identifier.
            code: Source code to test.
            language: Programming language (auto-detect if empty).
            num_test_cases: Number of test cases to generate.
            auto_approve: If True, skip review stage and auto-approve.
            progress_callback: Optional callback for stage progress updates.

        Returns:
            OrchestratorResult with all stage outputs.
        """
        result = OrchestratorResult(submission_id=submission_id)

        if self.provider_manager is None:
            from src.llm.provider import get_provider_manager
            self.provider_manager = get_provider_manager()

        # Stage 1: Detect language
        if not language:
            from src.analyzer.language_detector import LanguageDetector
            language = LanguageDetector.from_content(code) or "python"

        workflow = WorkflowEngine(submission_id)
        self._emit_progress(progress_callback, "analysis", "pending")

        # ---- Stage 2: Static Analysis ----
        try:
            workflow.transition(WorkflowStage.ANALYZING)
            self._emit_progress(progress_callback, "analysis", "running")
            analysis_result = await self._run_analysis(code, language)
            result.analysis = analysis_result
            self._emit_progress(progress_callback, "analysis", "done", analysis_result)
        except Exception as e:
            result.errors.append(f"Analysis failed: {e}")
            workflow.transition(WorkflowStage.FAILED)
            result.status = WorkflowStatus.FAILED
            return result

        # ---- Stage 3: Generate Plan ----
        try:
            workflow.transition(WorkflowStage.PLANNING)
            self._emit_progress(progress_callback, "plan", "running")
            plan_result = await self._generate_plan(code, language)
            result.plan = plan_result
            self._emit_progress(progress_callback, "plan", "done", plan_result)
        except Exception as e:
            result.errors.append(f"Plan generation failed: {e}")
            workflow.transition(WorkflowStage.FAILED)
            result.status = WorkflowStatus.FAILED
            return result

        # ---- Stage 4: Review ----
        if not auto_approve:
            workflow.transition(WorkflowStage.PENDING_REVIEW)
            self._emit_progress(progress_callback, "review", "pending")
            result.status = WorkflowStatus.PENDING_REVIEW
            result.stage = "review"
            return result  # Wait for manual approval

        # ---- Stage 5: Test ----
        try:
            workflow.transition(WorkflowStage.TESTING)
            self._emit_progress(progress_callback, "test", "running")
            test_result = await self._run_tests(code, language, num_test_cases)
            result.test_result = test_result
            self._emit_progress(progress_callback, "test", "done", test_result)
        except Exception as e:
            result.errors.append(f"Test execution failed: {e}")
            workflow.transition(WorkflowStage.FAILED)
            result.status = WorkflowStatus.FAILED
            return result

        # ---- Stage 6: Score ----
        try:
            workflow.transition(WorkflowStage.SCORING)
            self._emit_progress(progress_callback, "score", "running")
            score_result = self._compute_score(result.analysis, result.test_result)
            result.score = score_result
            self._emit_progress(progress_callback, "score", "done", score_result)
        except Exception as e:
            result.errors.append(f"Scoring failed: {e}")

        workflow.transition(WorkflowStage.COMPLETED)
        result.status = WorkflowStatus.COMPLETED
        result.stage = "completed"
        return result

    async def continue_after_review(
        self,
        result: OrchestratorResult,
        code: str,
        language: str,
        num_test_cases: int = 5,
        progress_callback: Optional[callable] = None,
    ) -> OrchestratorResult:
        """Continue pipeline after manual review approval.

        Args:
            result: Previous OrchestratorResult (paused at review stage).
            code: Source code.
            language: Programming language.
            num_test_cases: Number of test cases.
            progress_callback: Optional callback.

        Returns:
            Updated OrchestratorResult with completed pipeline.
        """
        # Run remaining stages
        try:
            self._emit_progress(progress_callback, "test", "running")
            test_result = await self._run_tests(code, language, num_test_cases)
            result.test_result = test_result
            self._emit_progress(progress_callback, "test", "done", test_result)
        except Exception as e:
            result.errors.append(f"Test execution failed: {e}")
            result.status = WorkflowStatus.FAILED
            return result

        try:
            self._emit_progress(progress_callback, "score", "running")
            score_result = self._compute_score(result.analysis, result.test_result)
            result.score = score_result
            self._emit_progress(progress_callback, "score", "done", score_result)
        except Exception as e:
            result.errors.append(f"Scoring failed: {e}")

        result.status = WorkflowStatus.COMPLETED
        result.stage = "completed"
        return result

    # === Private Methods ===

    async def _run_analysis(self, code: str, language: str) -> dict:
        """Run static code analysis."""
        from src.analyzer.parsers.c_cpp_parser import CAnalyzer, CCPPAnalyzer
        from src.analyzer.parsers.java_parser import JavaAnalyzer
        from src.analyzer.parsers.python_parser import PythonAnalyzer

        analyzers = {
            "python": PythonAnalyzer(),
            "cpp": CCPPAnalyzer(),
            "c": CAnalyzer(),
            "java": JavaAnalyzer(),
        }

        analyzer = analyzers.get(language, PythonAnalyzer())
        result = await analyzer.analyze_with_llm(
            code=code,
            provider_manager=self.provider_manager,
        )
        return result.to_dict()

    async def _generate_plan(self, code: str, language: str) -> dict:
        """Generate inspection plan via LLM."""
        from src.analyzer.inspection_plan import InspectionPlanGenerator

        plan = await InspectionPlanGenerator.generate(
            project_name="Auto-Detection",
            code_samples=code,
            language=language,
            provider_manager=self.provider_manager,
        )
        return plan.to_dict()

    async def _run_tests(self, code: str, language: str, num_cases: int) -> dict:
        """Generate and run tests in sandbox."""
        from src.tester.generator import TestCaseGenerator
        from src.tester.runner import TestRunner

        # Generate tests
        suite = await TestCaseGenerator.generate(
            code=code,
            language=language,
            num_cases=num_cases,
            provider_manager=self.provider_manager,
        )

        # Run tests in sandbox
        runner = TestRunner(mirror=self.sandbox_mirror)
        run_result = await runner.run_tests(
            code=code,
            test_code=suite.to_text(),
            language=language,
        )

        return {
            "language": run_result.language,
            "total": run_result.total,
            "passed": run_result.passed,
            "failed": run_result.failed,
            "errors": run_result.errors,
            "pass_rate": run_result.pass_rate,
            "stdout": run_result.stdout[:3000],
            "duration_ms": run_result.duration_ms,
            "timed_out": run_result.timed_out,
        }

    def _compute_score(self, analysis: dict, tests: dict) -> dict:
        """Compute multi-dimensional scores."""
        from src.standards.scoring import ScoringEngine

        score = ScoringEngine.compute(
            analysis_result=analysis,
            test_result=tests,
            coverage_percent=min(tests.get("pass_rate", 0), 100),
        )

        return {
            "overall_score": score.overall_score,
            "grade": score.grade,
            "dimension_scores": score.dimension_scores,
            "dimension_weights": score.dimension_weights,
        }

    def _emit_progress(self, callback, stage: str, status: str, data: dict = None):
        """Send progress update to callback if provided."""
        if callback:
            try:
                callback(stage, status, data)
            except Exception:
                pass