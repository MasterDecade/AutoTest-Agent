"""API routes for batch processing and queue management."""

from fastapi import APIRouter, HTTPException

from src.api.schemas.batch import BatchSubmitRequest, BatchStatusResponse
from src.scheduler.dispatcher import BatchDispatcher

router = APIRouter(prefix="/api/batch", tags=["batch"])

dispatcher = BatchDispatcher()


@router.post("/submit", response_model=BatchStatusResponse)
async def submit_batch(request: BatchSubmitRequest):
    """Submit a batch of submissions for processing.

    Returns queue statistics after submission.
    """
    for i, submission in enumerate(request.submissions):
        task_id = f"{request.project_id}-{i}-{submission.get('id', 'unknown')}"
        dispatcher.submit(
            task_id=task_id,
            priority=request.priority or 0,
            metadata=submission,
        )

    return BatchStatusResponse(
        pending=dispatcher.pending_count,
        active=dispatcher.active_count,
        stats=dispatcher.stats,
    )


@router.get("/status", response_model=BatchStatusResponse)
async def batch_status():
    """Get current batch processing status and queue depth."""
    return BatchStatusResponse(
        pending=dispatcher.pending_count,
        active=dispatcher.active_count,
        stats=dispatcher.stats,
    )