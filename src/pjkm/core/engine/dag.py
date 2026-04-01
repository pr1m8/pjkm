"""DAG resolver using Kahn's algorithm for topological sorting."""

from __future__ import annotations

from collections import defaultdict, deque

from pjkm.core.models.task import Phase, TaskDefinition


class CyclicDependencyError(Exception):
    """Raised when tasks have circular dependencies within a phase."""

    def __init__(self, phase: Phase, remaining_tasks: list[str]) -> None:
        self.phase = phase
        self.remaining_tasks = remaining_tasks
        super().__init__(
            f"Cyclic dependency detected in phase {phase.name} "
            f"among tasks: {', '.join(remaining_tasks)}"
        )


class DAGResolver:
    """Resolves task execution order within each phase using topological sort."""

    def resolve(self, tasks: list[TaskDefinition]) -> list[TaskDefinition]:
        """Sort tasks respecting phase order and intra-phase dependencies.

        Returns a flat list of TaskDefinitions in execution order:
        all SCAFFOLD tasks first (topologically sorted), then CONFIGURE, etc.

        Raises CyclicDependencyError if a cycle is detected within any phase.
        """
        by_phase: dict[Phase, list[TaskDefinition]] = defaultdict(list)
        for task in tasks:
            by_phase[task.phase].append(task)

        result: list[TaskDefinition] = []
        for phase in sorted(Phase):
            phase_tasks = by_phase.get(phase, [])
            if phase_tasks:
                result.extend(self._sort_phase(phase, phase_tasks))
        return result

    def _sort_phase(self, phase: Phase, tasks: list[TaskDefinition]) -> list[TaskDefinition]:
        """Topological sort within a single phase using Kahn's algorithm."""
        task_map: dict[str, TaskDefinition] = {t.id: t for t in tasks}
        task_ids = set(task_map.keys())

        # Build adjacency list and in-degree map
        in_degree: dict[str, int] = dict.fromkeys(task_ids, 0)
        dependents: dict[str, list[str]] = defaultdict(list)

        for task in tasks:
            for dep_id in task.depends_on:
                if dep_id not in task_ids:
                    # Dependency is in a different phase or doesn't exist — skip
                    continue
                in_degree[task.id] += 1
                dependents[dep_id].append(task.id)

        # Start with zero in-degree tasks, sorted by id for deterministic order
        queue: deque[str] = deque(sorted(tid for tid, deg in in_degree.items() if deg == 0))
        sorted_tasks: list[TaskDefinition] = []

        while queue:
            tid = queue.popleft()
            sorted_tasks.append(task_map[tid])
            for dependent_id in sorted(dependents[tid]):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        if len(sorted_tasks) != len(tasks):
            remaining = [tid for tid in task_ids if tid not in {t.id for t in sorted_tasks}]
            raise CyclicDependencyError(phase, remaining)

        return sorted_tasks
