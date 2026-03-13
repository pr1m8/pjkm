"""ProjectEngine: top-level orchestrator that wires everything together."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from pjkm.core.engine.dag import DAGResolver
from pjkm.core.engine.task_context import TaskContext
from pjkm.core.engine.task_runner import TaskRunner
from pjkm.core.models.platform import PlatformInfo
from pjkm.core.models.project import ProjectConfig
from pjkm.core.models.task import TaskEvent, TaskResult
from pjkm.core.tasks.registry import TaskRegistry


class ProjectResult(BaseModel):
    """Aggregate result of a full project generation run."""

    config: ProjectConfig
    results: list[TaskResult] = Field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def failed_tasks(self) -> list[TaskResult]:
        return [r for r in self.results if not r.success and not r.skipped]

    @property
    def skipped_tasks(self) -> list[TaskResult]:
        return [r for r in self.results if r.skipped]

    @property
    def completed_tasks(self) -> list[TaskResult]:
        return [r for r in self.results if r.success and not r.skipped]


class ProjectEngine:
    """Orchestrates project generation.

    Both CLI and TUI call engine.execute(config, on_event=...) with the same
    interface. The engine:
    1. Gathers applicable tasks from the registry
    2. Resolves execution order via DAG
    3. Runs tasks via TaskRunner, emitting events
    4. Returns a ProjectResult
    """

    def __init__(
        self,
        task_registry: TaskRegistry,
        dag_resolver: DAGResolver | None = None,
    ) -> None:
        self._task_registry = task_registry
        self._dag_resolver = dag_resolver or DAGResolver()

    def execute(
        self,
        config: ProjectConfig,
        on_event: Callable[[TaskEvent], None] | None = None,
        extra: dict | None = None,
    ) -> ProjectResult:
        """Run the full project generation pipeline."""
        # 1. Get task definitions applicable to this archetype
        definitions = self._task_registry.get_definitions(archetype=config.archetype)

        # 2. Resolve execution order
        ordered = self._dag_resolver.resolve(definitions)

        # 3. Build context
        ctx = TaskContext(
            config=config,
            platform=PlatformInfo(),
            extra=extra or {},
        )

        # 4. Run tasks
        runner = TaskRunner(
            registry=self._task_registry,
            on_event=on_event,
        )
        results = runner.run(ordered, ctx)

        return ProjectResult(config=config, results=results)
