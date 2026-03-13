"""Tests for task registry, runner, and context."""

import pytest

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.engine.task_runner import TaskRunError, TaskRunner
from pjkm.core.models.project import Archetype, ProjectConfig
from pjkm.core.models.task import (
    Phase,
    PhaseCompleted,
    PhaseStarted,
    TaskCompleted,
    TaskDefinition,
    TaskResult,
    TaskStarted,
)
from pjkm.core.tasks.base import BaseTask
from pjkm.core.tasks.registry import TaskRegistry

# ── Test fixtures ──────────────────────────────────────────


class DummyTask(BaseTask):
    id = "dummy"
    phase = Phase.SCAFFOLD
    description = "A dummy task for testing"

    def execute(self, ctx):
        return self.success_result(message="dummy ran")


class FailingTask(BaseTask):
    id = "failing"
    phase = Phase.SCAFFOLD
    description = "A task that always fails"

    def execute(self, ctx):
        return self.failure_result(message="intentional failure")


class ConditionalTask(BaseTask):
    id = "conditional"
    phase = Phase.CONFIGURE
    description = "Only runs if 'logging' group selected"

    def should_run(self, ctx):
        return ctx.has_group("logging")

    def execute(self, ctx):
        return self.success_result(message="conditional ran")


class ExceptionTask(BaseTask):
    id = "exploding"
    phase = Phase.SCAFFOLD
    description = "Raises an exception"

    def execute(self, ctx):
        msg = "boom"
        raise RuntimeError(msg)


@pytest.fixture
def config(tmp_path):
    return ProjectConfig(
        project_name="test-project",
        archetype=Archetype.SINGLE_PACKAGE,
        target_dir=tmp_path,
    )


@pytest.fixture
def ctx(config):
    return TaskContext(config=config)


# ── TaskRegistry tests ─────────────────────────────────────


class TestTaskRegistry:
    def test_register_and_get(self):
        reg = TaskRegistry()
        task = DummyTask()
        reg.register(task)
        assert reg.get("dummy") is task

    def test_register_duplicate_raises(self):
        reg = TaskRegistry()
        reg.register(DummyTask())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(DummyTask())

    def test_get_nonexistent(self):
        reg = TaskRegistry()
        assert reg.get("nope") is None

    def test_get_definitions(self):
        reg = TaskRegistry()
        reg.register(DummyTask())
        reg.register(ConditionalTask())
        defs = reg.get_definitions()
        assert len(defs) == 2
        ids = {d.id for d in defs}
        assert ids == {"dummy", "conditional"}

    def test_task_ids(self):
        reg = TaskRegistry()
        reg.register(DummyTask())
        assert reg.task_ids == ["dummy"]


# ── TaskContext tests ──────────────────────────────────────


class TestTaskContext:
    def test_project_dir(self, ctx, tmp_path):
        assert ctx.project_dir == tmp_path / "test-project"

    def test_has_group(self, tmp_path):
        config = ProjectConfig(
            project_name="test",
            archetype=Archetype.SINGLE_PACKAGE,
            target_dir=tmp_path,
            selected_groups=["logging", "testing"],
        )
        ctx = TaskContext(config=config)
        assert ctx.has_group("logging")
        assert ctx.has_group("testing")
        assert not ctx.has_group("otel")

    def test_get_result(self, ctx):
        r = TaskResult(task_id="t1", success=True, message="ok")
        ctx.results["t1"] = r
        assert ctx.get_result("t1") is r
        assert ctx.get_result("nope") is None


# ── TaskRunner tests ───────────────────────────────────────


class TestTaskRunner:
    def test_run_single_task(self, ctx):
        reg = TaskRegistry()
        reg.register(DummyTask())
        defs = [TaskDefinition(id="dummy", phase=Phase.SCAFFOLD)]
        runner = TaskRunner(registry=reg)
        results = runner.run(defs, ctx)
        assert len(results) == 1
        assert results[0].success
        assert results[0].message == "dummy ran"

    def test_failing_task_raises(self, ctx):
        reg = TaskRegistry()
        reg.register(FailingTask())
        defs = [TaskDefinition(id="failing", phase=Phase.SCAFFOLD)]
        runner = TaskRunner(registry=reg)
        with pytest.raises(TaskRunError, match="intentional failure"):
            runner.run(defs, ctx)

    def test_exception_task_caught(self, ctx):
        reg = TaskRegistry()
        reg.register(ExceptionTask())
        defs = [TaskDefinition(id="exploding", phase=Phase.SCAFFOLD)]
        runner = TaskRunner(registry=reg)
        with pytest.raises(TaskRunError, match="boom"):
            runner.run(defs, ctx)

    def test_conditional_skip(self, ctx):
        """Task with should_run=False is skipped."""
        reg = TaskRegistry()
        reg.register(ConditionalTask())
        defs = [TaskDefinition(id="conditional", phase=Phase.CONFIGURE)]
        runner = TaskRunner(registry=reg)
        results = runner.run(defs, ctx)
        assert len(results) == 1
        assert results[0].skipped

    def test_conditional_runs_when_group_present(self, tmp_path):
        config = ProjectConfig(
            project_name="test",
            archetype=Archetype.SINGLE_PACKAGE,
            target_dir=tmp_path,
            selected_groups=["logging"],
        )
        ctx = TaskContext(config=config)
        reg = TaskRegistry()
        reg.register(ConditionalTask())
        defs = [TaskDefinition(id="conditional", phase=Phase.CONFIGURE)]
        runner = TaskRunner(registry=reg)
        results = runner.run(defs, ctx)
        assert results[0].success
        assert not results[0].skipped

    def test_events_emitted(self, ctx):
        events = []
        reg = TaskRegistry()
        reg.register(DummyTask())
        defs = [TaskDefinition(id="dummy", phase=Phase.SCAFFOLD)]
        runner = TaskRunner(registry=reg, on_event=events.append)
        runner.run(defs, ctx)

        kinds = [type(e) for e in events]
        assert PhaseStarted in kinds
        assert TaskStarted in kinds
        assert TaskCompleted in kinds
        assert PhaseCompleted in kinds

    def test_multiple_phases_emit_transitions(self, ctx):
        events = []
        reg = TaskRegistry()
        reg.register(DummyTask())
        reg.register(ConditionalTask())

        # Force conditional to run
        ctx.config.selected_groups = ["logging"]

        defs = [
            TaskDefinition(id="dummy", phase=Phase.SCAFFOLD),
            TaskDefinition(id="conditional", phase=Phase.CONFIGURE),
        ]
        runner = TaskRunner(registry=reg, on_event=events.append)
        runner.run(defs, ctx)

        phase_events = [
            e for e in events if isinstance(e, (PhaseStarted, PhaseCompleted))
        ]
        assert len(phase_events) == 4  # start/end for SCAFFOLD and CONFIGURE

    def test_missing_task_raises(self, ctx):
        reg = TaskRegistry()
        defs = [TaskDefinition(id="ghost", phase=Phase.SCAFFOLD)]
        runner = TaskRunner(registry=reg)
        with pytest.raises(TaskRunError, match="not found"):
            runner.run(defs, ctx)

    def test_results_accumulated_in_context(self, ctx):
        reg = TaskRegistry()
        reg.register(DummyTask())
        defs = [TaskDefinition(id="dummy", phase=Phase.SCAFFOLD)]
        runner = TaskRunner(registry=reg)
        runner.run(defs, ctx)
        assert len(ctx.results) == 1
        assert ctx.results["dummy"].task_id == "dummy"
