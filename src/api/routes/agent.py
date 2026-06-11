"""API routes for the Agent orchestrator — one-click detection pipeline."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from src.agent.orchestrator import AgentOrchestrator, OrchestratorResult
from src.api.schemas.agent import AgentDetectRequest, AgentDetectResponse, AgentStatusResponse
from src.common.config import get_settings

router = APIRouter(prefix="/api/agent", tags=["agent"])

settings = get_settings()

# In-memory store for active workflows
_workflows: dict[str, OrchestratorResult] = {}


@router.post("/detect", response_model=AgentDetectResponse)
async def run_detection(request: AgentDetectRequest):
    """Run the full auto-test pipeline on submitted code.

    Stages: analysis → plan → (review) → test → score

    If auto_approve=False (default), the pipeline pauses after generating
    the inspection plan and waits for manual review.
    """
    submission_id = str(uuid.uuid4())[:12]
    orchestrator = AgentOrchestrator(sandbox_mirror=settings.docker_mirror)

    try:
        result = await orchestrator.run_full_pipeline(
            submission_id=submission_id,
            code=request.code,
            language=request.language or "",
            num_test_cases=request.num_test_cases,
            auto_approve=request.auto_approve,
        )

        _workflows[submission_id] = result

        return AgentDetectResponse(
            submission_id=submission_id,
            status=result.status,
            stage=result.stage,
            analysis=result.analysis,
            plan=result.plan,
            test_result=result.test_result,
            score=result.score,
            errors=result.errors,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection pipeline failed: {str(e)}")


@router.post("/detect/{submission_id}/approve", response_model=AgentDetectResponse)
async def approve_and_continue(submission_id: str, request: AgentDetectRequest):
    """Approve a pending inspection plan and continue the pipeline.

    Resumes from the review stage: test → score.
    """
    result = _workflows.get(submission_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Workflow {submission_id} not found")

    if result.status != "pending_review":
        raise HTTPException(status_code=400, detail=f"Workflow is not pending review (status={result.status})")

    orchestrator = AgentOrchestrator(sandbox_mirror=settings.docker_mirror)

    try:
        result = await orchestrator.continue_after_review(
            result=result,
            code=request.code,
            language=request.language or "python",
            num_test_cases=request.num_test_cases,
        )

        _workflows[submission_id] = result

        return AgentDetectResponse(
            submission_id=submission_id,
            status=result.status,
            stage=result.stage,
            analysis=result.analysis,
            plan=result.plan,
            test_result=result.test_result,
            score=result.score,
            errors=result.errors,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline continuation failed: {str(e)}")


@router.get("/detect/{submission_id}", response_model=AgentStatusResponse)
async def get_detection_status(submission_id: str):
    """Get the current status of a detection workflow."""
    result = _workflows.get(submission_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Workflow {submission_id} not found")

    return AgentStatusResponse(
        submission_id=submission_id,
        status=result.status,
        stage=result.stage,
        errors=result.errors,
    )