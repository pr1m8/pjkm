"""Review screen: confirm choices before building."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from pjkm.core.models.project import Archetype


class ReviewScreen(Screen):
    """Review all choices before executing the build."""

    def __init__(
        self,
        project_name: str,
        archetype: Archetype,
        groups: list[str],
    ) -> None:
        super().__init__()
        self._project_name = project_name
        self._archetype = archetype
        self._groups = groups

    def compose(self) -> ComposeResult:
        with Vertical(id="wizard-container"):
            yield Static("Review Your Project", classes="title")
            yield Label(f"Name: {self._project_name}")
            yield Label(f"Archetype: {self._archetype.value}")
            yield Label(f"Groups: {', '.join(self._groups) or '(none)'}")
            yield Label(f"Directory: {Path.cwd()}")
            yield Label("")
            yield Button("Build →", variant="success", id="build-btn")
            yield Button("← Back", id="back-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
        elif event.button.id == "build-btn":
            self.app.start_build()
