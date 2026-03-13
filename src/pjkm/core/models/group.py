"""Package group models: curated dependency bundles with scaffolded code."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScaffoldedFile(BaseModel):
    """A template fragment to render when a group is selected."""

    template_fragment: str
    destination: str
    description: str = ""
    conditions: dict[str, bool | str] = Field(default_factory=dict)


class PackageGroup(BaseModel):
    """A curated bundle of dependencies and scaffolded code/config."""

    id: str
    name: str
    description: str = ""
    archetypes: list[str] = Field(default_factory=list)
    requires_groups: list[str] = Field(default_factory=list)
    platform_filter: str | None = None

    dependencies: dict[str, list[str]] = Field(default_factory=dict)
    scaffolded_files: list[ScaffoldedFile] = Field(default_factory=list)
    pyproject_tool_config: dict[str, dict] = Field(default_factory=dict)
