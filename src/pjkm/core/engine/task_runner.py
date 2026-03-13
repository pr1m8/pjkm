"""Task runner: executes a resolved task list, emitting events."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from pjkm.core.models.task import (
    Phase,
    PhaseCompleted,
    PhaseStarted,
    TaskCompleted,
    TaskEvent,
    TaskResult,
    TaskStarted,
)

if TYPE_CHECKING:
    from pjkm.core.engine.task_context import TaskContext
    from pjkm.core.models.task import TaskDefinition
    from pjkm.core.tasks.base import BaseTask
    from pjkm.core.tasks.registry import TaskRegistry


class TaskRunError(Exception):
    """Raised when a task fails during execution."""

    def __init__(self, task_id: str, message: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task {task_id!r} failed: {message}")


class TaskRunner:
    """Executes tasks in DAG-resolved order, grouped by phase."""

    def __init__(
        self,
        registry: TaskRegistry,
        on_event: Callable[[TaskEvent], None] | None = None,
    ) -> None:
        self._registry = registry
        self._on_event = on_event

    def run(
        self,
        ordered_definitions: list[TaskDefinition],
        ctx: TaskContext,
    ) -> list[TaskResult]:
        """Execute tasks in the given order, updating context along the way.

        Returns the list of all TaskResults (including skipped tasks).
        Raises TaskRunError if a task fails and success=False.
        """
        results: list[TaskResult] = []
        current_phase: Phase | None = None

        for defn in ordered_definitions:
            # Emit phase transitions
            if defn.phase != current_phase:
                if current_phase is not None:
                    self._emit(PhaseCompleted(phase=current_phase))
                current_phase = defn.phase
                self._emit(PhaseStarted(phase=current_phase))

            task = self._registry.get(defn.id)
            if task is None:
                msg = f"Task {defn.id!r} not found in registry"
                raise TaskRunError(defn.id, msg)

            result = self._execute_one(task, ctx)
            results.append(result)
            ctx.results[defn.id] = result

            if not result.success and not result.skipped:
                self._emit(TaskCompleted(task_id=defn.id, result=result))
                raise TaskRunError(defn.id, result.message)

        # Close final phase
        if current_phase is not None:
            self._emit(PhaseCompleted(phase=current_phase))

        return results

    def _execute_one(self, task: BaseTask, ctx: TaskContext) -> TaskResult:
        """Execute a single task, handling skip logic and timing."""
        if not task.should_run(ctx):
            result = task.skip_result()
            self._emit(TaskCompleted(task_id=task.id, result=result))
            return result

        self._emit(
            TaskStarted(
                task_id=task.id,
                phase=task.phase,
                description=task.description,
            )
        )

        start = time.perf_counter()
        try:
            result = task.execute(ctx)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            result = TaskResult(
                task_id=task.id,
                success=False,
                message=str(exc),
                duration_ms=elapsed_ms,
            )
        else:
            result.duration_ms = (time.perf_counter() - start) * 1000

        self._emit(TaskCompleted(task_id=task.id, result=result))
        return result

    def _emit(self, event: TaskEvent) -> None:
        if self._on_event is not None:
            try:
                self._on_event(event)
            except Exception:
                import sys

                print(
                    f"Warning: event callback raised an exception for {event!r}",
                    file=sys.stderr,
                )
