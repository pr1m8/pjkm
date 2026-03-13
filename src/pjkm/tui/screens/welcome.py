"""Welcome screen: project name and archetype selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, Static

from pjkm import __version__
from pjkm.core.models.project import Archetype

ARCHETYPE_DESCRIPTIONS = {
    Archetype.SINGLE_PACKAGE: "Standalone Python package with src layout",
    Archetype.SERVICE: "Service repo with infra, Docker Compose, Makefile",
    Archetype.POLY_REPO: "Multi-package repo with submodules and shared infra",
    Archetype.SCRIPT_TOOL: "Lightweight CLI tool or script",
}


class WelcomeScreen(Screen):
    """First screen: enter project name and select archetype."""

    def compose(self) -> ComposeResult:
        with Vertical(id="wizard-container"):
            yield Static(f"pjkm v{__version__}", classes="title")
            yield Label("Python Project Builder", classes="subtitle")
            yield Label("Project name:")
            yield Input(placeholder="my-project", id="project-name")
            yield Label("")
            yield Label("Archetype:")
            with RadioSet(id="archetype-select"):
                for arch in Archetype:
                    yield RadioButton(
                        f"{arch.value} — {ARCHETYPE_DESCRIPTIONS[arch]}",
                        value=arch == Archetype.SINGLE_PACKAGE,
                        name=arch.value,
                    )
            yield Label("")
            yield Button("Next →", variant="primary", id="next-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "next-btn":
            return

        name_input = self.query_one("#project-name", Input)
        name = name_input.value.strip()
        if not name:
            name_input.focus()
            return

        radio_set = self.query_one("#archetype-select", RadioSet)
        idx = radio_set.pressed_index
        archetypes = list(Archetype)
        archetype = archetypes[idx] if idx >= 0 else Archetype.SINGLE_PACKAGE

        self.app.set_archetype(name, archetype)
