"""Group selection screen: pick package groups via checkboxes."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Label, Static

from pjkm.core.groups.registry import GroupRegistry
from pjkm.core.models.project import Archetype


class GroupSelectionScreen(Screen):
    """Select package groups to include in the project."""

    def __init__(self, archetype: Archetype) -> None:
        super().__init__()
        self._archetype = archetype
        self._registry = GroupRegistry()
        self._registry.load_builtin()

    def compose(self) -> ComposeResult:
        groups = self._registry.list_for_archetype(self._archetype.value)
        with Vertical(id="wizard-container"):
            yield Static("Select Package Groups", classes="title")
            yield Label(f"Archetype: {self._archetype.value}")
            yield Label("")
            with VerticalScroll(id="group-list"):
                for g in groups:
                    yield Checkbox(
                        f"{g.id} — {g.description}",
                        id=f"group-{g.id}",
                        value=g.id == "dev",
                    )
            yield Label("")
            yield Button("Next →", variant="primary", id="next-btn")
            yield Button("← Back", id="back-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
            return

        if event.button.id != "next-btn":
            return

        selected: list[str] = []
        for cb in self.query(Checkbox):
            if cb.value:
                group_id = cb.id.removeprefix("group-") if cb.id else ""
                if group_id:
                    selected.append(group_id)

        self.app.set_groups(selected)
