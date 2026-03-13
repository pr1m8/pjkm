"""Tests for DAG resolver."""

import pytest

from pjkm.core.engine.dag import CyclicDependencyError, DAGResolver
from pjkm.core.models.task import Phase, TaskDefinition


@pytest.fixture
def resolver():
    return DAGResolver()


class TestDAGResolver:
    def test_empty_input(self, resolver):
        assert resolver.resolve([]) == []

    def test_single_task(self, resolver):
        tasks = [TaskDefinition(id="a", phase=Phase.SCAFFOLD)]
        result = resolver.resolve(tasks)
        assert len(result) == 1
        assert result[0].id == "a"

    def test_phase_ordering(self, resolver):
        tasks = [
            TaskDefinition(id="verify", phase=Phase.VERIFY),
            TaskDefinition(id="scaffold", phase=Phase.SCAFFOLD),
            TaskDefinition(id="install", phase=Phase.INSTALL),
            TaskDefinition(id="configure", phase=Phase.CONFIGURE),
        ]
        result = resolver.resolve(tasks)
        ids = [t.id for t in result]
        assert ids == ["scaffold", "configure", "install", "verify"]

    def test_intra_phase_deps(self, resolver):
        tasks = [
            TaskDefinition(id="b", phase=Phase.SCAFFOLD, depends_on=["a"]),
            TaskDefinition(id="a", phase=Phase.SCAFFOLD),
            TaskDefinition(id="c", phase=Phase.SCAFFOLD, depends_on=["a", "b"]),
        ]
        result = resolver.resolve(tasks)
        ids = [t.id for t in result]
        assert ids.index("a") < ids.index("b") < ids.index("c")

    def test_independent_tasks_deterministic_order(self, resolver):
        """Independent tasks within a phase should be sorted by id for determinism."""
        tasks = [
            TaskDefinition(id="c", phase=Phase.SCAFFOLD),
            TaskDefinition(id="a", phase=Phase.SCAFFOLD),
            TaskDefinition(id="b", phase=Phase.SCAFFOLD),
        ]
        result = resolver.resolve(tasks)
        ids = [t.id for t in result]
        assert ids == ["a", "b", "c"]

    def test_cyclic_dependency_detected(self, resolver):
        tasks = [
            TaskDefinition(id="a", phase=Phase.SCAFFOLD, depends_on=["b"]),
            TaskDefinition(id="b", phase=Phase.SCAFFOLD, depends_on=["a"]),
        ]
        with pytest.raises(CyclicDependencyError) as exc_info:
            resolver.resolve(tasks)
        assert exc_info.value.phase == Phase.SCAFFOLD
        assert set(exc_info.value.remaining_tasks) == {"a", "b"}

    def test_three_node_cycle(self, resolver):
        tasks = [
            TaskDefinition(id="a", phase=Phase.CONFIGURE, depends_on=["c"]),
            TaskDefinition(id="b", phase=Phase.CONFIGURE, depends_on=["a"]),
            TaskDefinition(id="c", phase=Phase.CONFIGURE, depends_on=["b"]),
        ]
        with pytest.raises(CyclicDependencyError):
            resolver.resolve(tasks)

    def test_cross_phase_deps_ignored(self, resolver):
        """Dependencies referencing tasks in other phases are silently skipped."""
        tasks = [
            TaskDefinition(
                id="configure_lint",
                phase=Phase.CONFIGURE,
                depends_on=["init_project"],  # in SCAFFOLD phase, not present here
            ),
        ]
        result = resolver.resolve(tasks)
        assert len(result) == 1
        assert result[0].id == "configure_lint"

    def test_diamond_dependency(self, resolver):
        """Diamond: a -> b, a -> c, b -> d, c -> d."""
        tasks = [
            TaskDefinition(id="d", phase=Phase.SCAFFOLD, depends_on=["b", "c"]),
            TaskDefinition(id="b", phase=Phase.SCAFFOLD, depends_on=["a"]),
            TaskDefinition(id="c", phase=Phase.SCAFFOLD, depends_on=["a"]),
            TaskDefinition(id="a", phase=Phase.SCAFFOLD),
        ]
        result = resolver.resolve(tasks)
        ids = [t.id for t in result]
        assert ids.index("a") < ids.index("b")
        assert ids.index("a") < ids.index("c")
        assert ids.index("b") < ids.index("d")
        assert ids.index("c") < ids.index("d")

    def test_mixed_phases_with_deps(self, resolver):
        tasks = [
            TaskDefinition(id="s1", phase=Phase.SCAFFOLD),
            TaskDefinition(id="s2", phase=Phase.SCAFFOLD, depends_on=["s1"]),
            TaskDefinition(id="c1", phase=Phase.CONFIGURE),
            TaskDefinition(id="c2", phase=Phase.CONFIGURE, depends_on=["c1"]),
            TaskDefinition(id="v1", phase=Phase.VERIFY),
        ]
        result = resolver.resolve(tasks)
        ids = [t.id for t in result]
        assert ids == ["s1", "s2", "c1", "c2", "v1"]
