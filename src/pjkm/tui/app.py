"""pjkm TUI application — Textual-based wizard interface."""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from pjkm.core.models.project import Archetype, ProjectConfig
from pjkm.tui.screens.done import DoneScreen
from pjkm.tui.screens.groups import GroupSelectionScreen
from pjkm.tui.screens.progress import ProgressScreen
from pjkm.tui.screens.review import ReviewScreen
from pjkm.tui.screens.welcome import WelcomeScreen


class PjkmApp(App):
    """Interactive project builder TUI."""

    TITLE = "pjkm"
    SUB_TITLE = "Project Builder"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._project_name: str = ""
        self._archetype: Archetype = Archetype.SINGLE_PACKAGE
        self._selected_groups: list[str] = []
        self._target_dir: Path = Path.cwd()

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())

    def set_archetype(self, name: str, archetype: Archetype) -> None:
        self._project_name = name
        self._archetype = archetype
        self.push_screen(GroupSelectionScreen(archetype=archetype))

    def set_groups(self, groups: list[str]) -> None:
        self._selected_groups = groups
        self.push_screen(
            ReviewScreen(
                project_name=self._project_name,
                archetype=self._archetype,
                groups=self._selected_groups,
            )
        )

    def start_build(self) -> None:
        config = ProjectConfig(
            project_name=self._project_name,
            archetype=self._archetype,
            selected_groups=self._selected_groups,
            target_dir=self._target_dir,
        )
        self.push_screen(ProgressScreen(config=config))

    def show_done(self, project_dir: Path, success: bool) -> None:
        self.push_screen(DoneScreen(project_dir=project_dir, success=success))


def run() -> None:
    """Entry point for the TUI."""
    app = PjkmApp()
    app.run()
