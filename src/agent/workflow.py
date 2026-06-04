"""Workflow engine — state machine and progress tracking for the detection pipeline."""

import time
from enum import Enum
from typing import Optional


class WorkflowStage(str, Enum):
    """Stages in the auto-test pipeline."""

    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    PENDING_REVIEW = "pending_review"
    TESTING = "testing"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(str, Enum):
    """Overall workflow status."""

    PENDING = "pending"
    RUNNING = "running"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowEngine:
    """Simple state machine for tracking the detection pipeline.

    Tracks transitions between stages and records timing.
    """

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.current_stage = WorkflowStage.IDLE
        self.status = WorkflowStatus.PENDING
        self.stage_timestamps: dict[str, float] = {}
        self.errors: list[str] = []
        self._record_stage(WorkflowStage.IDLE)

    def transition(self, stage: WorkflowStage) -> bool:
        """Attempt to transition to a new stage.

        Args:
            stage: Target stage.

        Returns:
            True if transition is valid and applied.
        """
        self.current_stage = stage
        self._record_stage(stage)

        if stage == WorkflowStage.FAILED:
            self.status = WorkflowStatus.FAILED
        elif stage == WorkflowStage.COMPLETED:
            self.status = WorkflowStatus.COMPLETED
        elif stage == WorkflowStage.PENDING_REVIEW:
            self.status = WorkflowStatus.PENDING_REVIEW
        else:
            self.status = WorkflowStatus.RUNNING

        return True

    def _record_stage(self, stage: WorkflowStage) -> None:
        """Record timestamp when entering a stage."""
        self.stage_timestamps[stage.value] = time.time()

    def get_duration(self, stage: WorkflowStage) -> Optional[float]:
        """Get time spent in a stage (seconds since entry).

        Args:
            stage: Stage to query.

        Returns:
            Duration in seconds or None if stage not yet entered.
        """
        start = self.stage_timestamps.get(stage.value)
        if start is None:
            return None
        return time.time() - start

    def is_stage_complete(self, stage: WorkflowStage) -> bool:
        """Check if a stage has been entered.

        Args:
            stage: Stage to check.

        Returns:
            True if the stage has been entered.
        """
        return stage.value in self.stage_timestamps

    def to_dict(self) -> dict:
        """Convert workflow state to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "current_stage": self.current_stage.value,
            "status": self.status.value,
            "stages_completed": list(self.stage_timestamps.keys()),
        }