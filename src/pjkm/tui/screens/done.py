"""Done screen: shows summary and next steps."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static


class DoneScreen(Screen):
    """Final screen showing the result and next steps."""

    def __init__(self, project_dir: Path, success: bool) -> None:
        super().__init__()
        self._project_dir = project_dir
        self._success = success

    def compose(self) -> ComposeResult:
        with Vertical(id="wizard-container"):
            if self._success:
                yield Static("Project Created!", classes="title")
                yield Label(f"Location: {self._project_dir}")
                yield Label("")
                yield Label("Next steps:")
                yield Label(f"  cd {self._project_dir}")
                yield Label("  pdm install")
                yield Label("  pdm run pytest")
                yield Label(
                    "Run 'pjkm doctor' to verify your environment.", classes="hint"
                )
            else:
                yield Static("Build Failed", classes="title")
                yield Label("Check the logs above for details.")
            yield Label("")
            yield Button("Quit", variant="primary", id="quit-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-btn":
            self.app.exit()
