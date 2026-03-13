"""Progress screen: shows live task execution."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Label, ProgressBar, RichLog, Static
from textual.worker import Worker, WorkerState

from pjkm.core.engine.project_engine import ProjectEngine, ProjectResult
from pjkm.core.models.project import ProjectConfig
from pjkm.core.models.task import (
    PhaseCompleted,
    PhaseStarted,
    TaskCompleted,
    TaskEvent,
    TaskStarted,
)
from pjkm.core.tasks.defaults import create_default_registry


class ProgressScreen(Screen):
    """Displays live progress of project generation."""

    def __init__(self, config: ProjectConfig, extra: dict | None = None) -> None:
        super().__init__()
        self._config = config
        self._extra = extra or {}
        self._total_tasks = 0
        self._completed_tasks = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="wizard-container"):
            yield Static("Building Project...", classes="title")
            yield ProgressBar(id="progress-bar", total=100)
            yield Label("", id="status-label")
            yield Label("")
            with VerticalScroll(id="log-scroll"):
                yield RichLog(id="task-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        self._run_build()

    @property
    def _log(self) -> RichLog:
        return self.query_one("#task-log", RichLog)

    @property
    def _progress(self) -> ProgressBar:
        return self.query_one("#progress-bar", ProgressBar)

    @property
    def _status(self) -> Label:
        return self.query_one("#status-label", Label)

    def _run_build(self) -> None:
        self.run_worker(self._execute, exclusive=True, thread=True)

    def _execute(self) -> ProjectResult:
        registry = create_default_registry()
        engine = ProjectEngine(task_registry=registry)

        def on_event(event: TaskEvent) -> None:
            self.call_from_thread(self._handle_event, event)

        return engine.execute(self._config, on_event=on_event, extra=self._extra)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            result = event.worker.result
            if isinstance(result, ProjectResult):
                self.app.show_done(
                    project_dir=self._config.project_dir,
                    success=result.success,
                )

    def _handle_event(self, event: TaskEvent) -> None:
        match event:
            case PhaseStarted(phase=phase):
                self._log.write(f"[bold blue]>>> {phase.name}[/bold blue]")
            case TaskStarted(task_id=tid, description=desc):
                self._status.update(f"Running: {desc or tid}")
            case TaskCompleted(task_id=tid, result=result):
                self._completed_tasks += 1
                pct = min(
                    99, int(self._completed_tasks / max(self._total_tasks, 7) * 100)
                )
                self._progress.update(progress=pct)
                if result.skipped:
                    self._log.write(f"  [yellow]Skipped:[/yellow] {tid}")
                elif result.success:
                    self._log.write(f"  [green]Done:[/green] {tid}")
                else:
                    self._log.write(f"  [red]Failed:[/red] {tid} — {result.message}")
            case PhaseCompleted():
                pass
