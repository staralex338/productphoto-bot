"""
Lightweight asyncio task queue with concurrency control.

Uses asyncio.Semaphore to limit concurrent AI generation jobs.
No Celery, RabbitMQ, or Redis required.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskStatus(Enum):
    """Status of a queued task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Metadata about a queued task."""

    task_id: str
    task_type: str  # "generation" | "upscale"
    user_id: int
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: Any = None
    coro: asyncio.Task | None = None


class TaskQueue:
    """
    Asyncio-based task queue with concurrency limits.

    Uses a semaphore to ensure no more than MAX_CONCURRENT_GENERATIONS
    run simultaneously. Excess tasks wait in FIFO order.
    """

    def __init__(self, max_concurrent: int | None = None):
        self.max_concurrent = max_concurrent or settings.max_concurrent_generations
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self._tasks: dict[str, TaskInfo] = {}
        self._lock = asyncio.Lock()

    async def submit(
        self,
        task_id: str,
        task_type: str,
        user_id: int,
        coro_factory: Callable[[], Coroutine[Any, Any, Any]],
        timeout: int | None = None,
    ) -> TaskInfo:
        """
        Submit a coroutine to the queue.

        Args:
            task_id: Unique identifier for this task
            task_type: "generation" or "upscale"
            user_id: Telegram user ID for tracking
            coro_factory: Callable that returns the coroutine to run
            timeout: Max seconds to wait for completion (None = use settings)

        Returns:
            TaskInfo with status tracking
        """
        timeout = timeout or settings.generation_timeout_seconds

        info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            user_id=user_id,
        )

        async with self._lock:
            self._tasks[task_id] = info

        # Wrap the coroutine with semaphore + timeout
        wrapped = self._wrap_task(info, coro_factory, timeout)
        asyncio.create_task(wrapped)

        logger.info(
            "Task %s (%s) submitted for user %s. Queue: %d/%d active",
            task_id,
            task_type,
            user_id,
            self.semaphore.locked(),
            self.max_concurrent,
        )
        return info

    async def _wrap_task(
        self,
        info: TaskInfo,
        coro_factory: Callable[[], Coroutine[Any, Any, Any]],
        timeout: int,
    ) -> None:
        """Execute task under semaphore with timeout and error handling."""
        async with self.semaphore:
            info.status = TaskStatus.RUNNING
            info.started_at = datetime.now(timezone.utc)

            try:
                result = await asyncio.wait_for(coro_factory(), timeout=timeout)
                info.status = TaskStatus.COMPLETED
                info.result = result
                logger.info("Task %s completed successfully", info.task_id)

            except asyncio.TimeoutError:
                info.status = TaskStatus.TIMEOUT
                info.error = f"Task timed out after {timeout}s"
                logger.warning("Task %s timed out", info.task_id)

            except asyncio.CancelledError:
                info.status = TaskStatus.CANCELLED
                info.error = "Task was cancelled"
                logger.info("Task %s cancelled", info.task_id)
                raise

            except Exception as e:
                info.status = TaskStatus.FAILED
                info.error = str(e)
                logger.exception("Task %s failed: %s", info.task_id, e)

            finally:
                info.completed_at = datetime.now(timezone.utc)

    def get_task(self, task_id: str) -> TaskInfo | None:
        """Get task info by ID."""
        return self._tasks.get(task_id)

    def get_user_tasks(self, user_id: int) -> list[TaskInfo]:
        """Get all tasks for a specific user."""
        return [t for t in self._tasks.values() if t.user_id == user_id]

    def get_active_count(self) -> int:
        """Number of currently running tasks."""
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)

    def get_pending_count(self) -> int:
        """Number of pending tasks waiting for a slot."""
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        info = self._tasks.get(task_id)
        if not info or info.coro is None:
            return False

        info.coro.cancel()
        return True

    def cleanup_old_tasks(self, max_age_seconds: int = 3600) -> int:
        """Remove completed/failed tasks older than max_age_seconds."""
        now = datetime.now(timezone.utc)
        to_remove = []

        for task_id, info in self._tasks.items():
            if info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT):
                if info.completed_at and (now - info.completed_at).total_seconds() > max_age_seconds:
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self._tasks[task_id]

        return len(to_remove)


# Global task queue instance (singleton per process)
_generation_queue: TaskQueue | None = None


def get_task_queue() -> TaskQueue:
    """Get or create the global task queue singleton."""
    global _generation_queue
    if _generation_queue is None:
        _generation_queue = TaskQueue()
    return _generation_queue
