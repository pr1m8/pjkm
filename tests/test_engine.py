"""Tests for ProjectEngine integration."""

import pytest

from pjkm.core.engine.project_engine import ProjectEngine, ProjectResult
from pjkm.core.models.project import Archetype, ProjectConfig
from pjkm.core.models.task import Phase
from pjkm.core.tasks.base import BaseTask
from pjkm.core.tasks.registry import TaskRegistry


class StubScaffoldTask(BaseTask):
    id = "stub_scaffold"
    phase = Phase.SCAFFOLD
    description = "Stub scaffold"

    def execute(self, ctx):
        return self.success_result(message="scaffolded")


class StubConfigureTask(BaseTask):
    id = "stub_configure"
    phase = Phase.CONFIGURE
    depends_on = []
    description = "Stub configure"

    def execute(self, ctx):
        return self.success_result(message="configured")


@pytest.fixture
def config(tmp_path):
    return ProjectConfig(
        project_name="integration-test",
        archetype=Archetype.SINGLE_PACKAGE,
        target_dir=tmp_path,
    )


class TestProjectEngine:
    def test_empty_registry(self, config):
        reg = TaskRegistry()
        engine = ProjectEngine(task_registry=reg)
        result = engine.execute(config)
        assert isinstance(result, ProjectResult)
        assert result.success
        assert result.results == []

    def test_single_task(self, config):
        reg = TaskRegistry()
        reg.register(StubScaffoldTask())
        engine = ProjectEngine(task_registry=reg)
        result = engine.execute(config)
        assert result.success
        assert len(result.completed_tasks) == 1
        assert result.completed_tasks[0].task_id == "stub_scaffold"

    def test_multi_phase(self, config):
        reg = TaskRegistry()
        reg.register(StubScaffoldTask())
        reg.register(StubConfigureTask())
        engine = ProjectEngine(task_registry=reg)
        result = engine.execute(config)
        assert result.success
        assert len(result.completed_tasks) == 2
        ids = [r.task_id for r in result.results]
        assert ids.index("stub_scaffold") < ids.index("stub_configure")

    def test_events_collected(self, config):
        events = []
        reg = TaskRegistry()
        reg.register(StubScaffoldTask())
        engine = ProjectEngine(task_registry=reg)
        engine.execute(config, on_event=events.append)
        assert len(events) >= 3  # PhaseStarted, TaskStarted, TaskCompleted, PhaseCompleted

    def test_result_properties(self, config):
        reg = TaskRegistry()
        reg.register(StubScaffoldTask())
        engine = ProjectEngine(task_registry=reg)
        result = engine.execute(config)
        assert result.failed_tasks == []
        assert result.skipped_tasks == []
        assert len(result.completed_tasks) == 1
