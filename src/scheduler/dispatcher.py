"""Batch dispatcher — adaptive concurrency, queue management, and task distribution."""

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DispatchConfig:
    """Configuration for batch dispatch."""

    max_concurrency: int = 10
    min_concurrency: int = 2
    cpu_threshold_percent: int = 80
    memory_threshold_percent: int = 85
    cooldown_seconds: int = 30


@dataclass
class SystemResources:
    """Current system resource snapshot for adaptive concurrency."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    available_cpus: int = 4
    available_memory_gb: float = 8.0


class AdaptiveConcurrency:
    """Dynamically adjusts concurrency based on system load.

    Monitors CPU/memory usage and automatically scales
    concurrent task execution up or down.
    """

    def __init__(self, config: DispatchConfig = None):
        self.config = config or DispatchConfig()
        self._current_limit: int = self.config.max_concurrency

    def get_limit(self) -> int:
        """Get the current concurrency limit based on system load.

        Returns:
            Recommended maximum concurrent tasks.
        """
        resources = self._sample_resources()
        return self._compute_limit(resources)

    def _sample_resources(self) -> SystemResources:
        """Get current system resource usage.

        Returns:
            SystemResources snapshot.
        """
        try:
            # CPU load average (try psutil if available, else estimate)
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory().percent
                available_cpus = os.cpu_count() or 4
                available_memory = psutil.virtual_memory().available / (1024 ** 3)
            except ImportError:
                # Fallback: just use config limits
                cpu = 50.0
                mem = 50.0
                available_cpus = os.cpu_count() or 4
                available_memory = 8.0

            return SystemResources(
                cpu_percent=cpu,
                memory_percent=mem,
                available_cpus=available_cpus,
                available_memory_gb=available_memory,
            )
        except Exception as e:
            logger.warning(f"Resource sampling failed: {e}")
            return SystemResources()

    def _compute_limit(self, resources: SystemResources) -> int:
        """Compute safe concurrency limit from resource snapshot.

        Args:
            resources: Current system resource snapshot.

        Returns:
            Adjusted concurrency limit.
        """
        limit = self.config.max_concurrency

        # CPU-based cap: reduce if CPU > threshold
        if resources.cpu_percent > self.config.cpu_threshold_percent:
            cpu_limit = max(
                self.config.min_concurrency,
                int(self.config.max_concurrency * 0.5),
            )
            limit = min(limit, cpu_limit)
            logger.warning(
                f"CPU at {resources.cpu_percent}% > {self.config.cpu_threshold_percent}%, "
                f"reducing concurrency to {limit}"
            )

        # Memory-based cap
        if resources.memory_percent > self.config.memory_threshold_percent:
            mem_limit = self.config.min_concurrency
            limit = min(limit, mem_limit)
            logger.warning(
                f"Memory at {resources.memory_percent}% > {self.config.memory_threshold_percent}%, "
                f"reducing concurrency to {limit}"
            )

        # Prevent too low
        limit = max(self.config.min_concurrency, limit)

        self._current_limit = limit
        return limit


class BatchDispatcher:
    """Dispatches batch tasks with adaptive concurrency and priority."""

    def __init__(self, config: DispatchConfig = None):
        self.config = config or DispatchConfig()
        self.adaptive = AdaptiveConcurrency(self.config)
        self._pending_tasks: list[dict] = []
        self._active_tasks: set[str] = set()

    def submit(self, task_id: str, priority: int = 0, metadata: dict = None) -> None:
        """Submit a task to the batch queue.

        Args:
            task_id: Unique task identifier.
            priority: Priority (higher = runs first).
            metadata: Optional task metadata.
        """
        self._pending_tasks.append({
            "task_id": task_id,
            "priority": priority,
            "metadata": metadata or {},
            "submitted_at": time.time(),
        })
        # Sort by priority descending
        self._pending_tasks.sort(key=lambda t: -t["priority"])

    def get_next_batch(self) -> list[str]:
        """Get the next batch of task IDs to dispatch.

        Respects the adaptive concurrency limit.

        Returns:
            List of task IDs to dispatch.
        """
        limit = self.adaptive.get_limit()
        available = limit - len(self._active_tasks)

        if available <= 0:
            return []

        batch = []
        for task in self._pending_tasks[:available]:
            if task["task_id"] not in self._active_tasks:
                batch.append(task["task_id"])
                self._active_tasks.add(task["task_id"])

        # Remove dispatched tasks from pending
        dispatched_ids = set(batch)
        self._pending_tasks = [
            t for t in self._pending_tasks if t["task_id"] not in dispatched_ids
        ]

        return batch

    def complete(self, task_id: str) -> None:
        """Mark a task as complete.

        Args:
            task_id: Task ID to mark complete.
        """
        self._active_tasks.discard(task_id)

    @property
    def pending_count(self) -> int:
        """Number of pending tasks."""
        return len(self._pending_tasks)

    @property
    def active_count(self) -> int:
        """Number of currently active tasks."""
        return len(self._active_tasks)

    @property
    def stats(self) -> dict:
        """Get dispatcher statistics."""
        return {
            "pending": self.pending_count,
            "active": self.active_count,
            "current_limit": self.adaptive._current_limit,
        }