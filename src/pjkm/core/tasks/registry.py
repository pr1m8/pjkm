"""Task registry: discover, register, and filter tasks."""

from __future__ import annotations

from pjkm.core.models.project import Archetype
from pjkm.core.models.task import TaskDefinition
from pjkm.core.tasks.base import BaseTask


class TaskRegistry:
    """Central registry of all available tasks.

    Tasks are registered either by adding BaseTask subclass instances
    or via the register() method. The registry can filter tasks by
    archetype and selected groups.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, BaseTask] = {}

    def register(self, task: BaseTask) -> None:
        """Register a task instance."""
        if task.id in self._tasks:
            msg = f"Task {task.id!r} is already registered"
            raise ValueError(msg)
        self._tasks[task.id] = task

    def get(self, task_id: str) -> BaseTask | None:
        """Look up a task by ID."""
        return self._tasks.get(task_id)

    def get_definitions(
        self,
        archetype: Archetype | None = None,
    ) -> list[TaskDefinition]:
        """Return TaskDefinitions for all registered tasks.

        Optionally filter by archetype (future: filter by group applicability).
        """
        definitions: list[TaskDefinition] = []
        for task in self._tasks.values():
            definitions.append(
                TaskDefinition(
                    id=task.id,
                    phase=task.phase,
                    depends_on=list(task.depends_on),
                    description=task.description,
                )
            )
        return definitions

    def all_tasks(self) -> list[BaseTask]:
        """Return all registered task instances."""
        return list(self._tasks.values())

    @property
    def task_ids(self) -> list[str]:
        return list(self._tasks.keys())
