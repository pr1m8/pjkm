"""Base task interface and decorator for lightweight task registration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pjkm.core.models.task import Phase, TaskResult

if TYPE_CHECKING:
    from pjkm.core.engine.task_context import TaskContext


class BaseTask(ABC):
    """Abstract base class for all pjkm tasks."""

    id: str
    phase: Phase
    depends_on: list[str] = []
    description: str = ""

    def should_run(self, ctx: TaskContext) -> bool:
        """Override to conditionally skip this task based on context."""
        return True

    @abstractmethod
    def execute(self, ctx: TaskContext) -> TaskResult:
        """Run the task and return its result."""
        ...

    def skip_result(self) -> TaskResult:
        """Return a skip result for this task."""
        return TaskResult(task_id=self.id, success=True, skipped=True, message="Skipped")

    def success_result(
        self,
        message: str = "",
        files_created: list[str] | None = None,
        files_modified: list[str] | None = None,
        duration_ms: float = 0.0,
    ) -> TaskResult:
        return TaskResult(
            task_id=self.id,
            success=True,
            message=message,
            files_created=files_created or [],
            files_modified=files_modified or [],
            duration_ms=duration_ms,
        )

    def failure_result(self, message: str, duration_ms: float = 0.0) -> TaskResult:
        return TaskResult(
            task_id=self.id,
            success=False,
            message=message,
            duration_ms=duration_ms,
        )
