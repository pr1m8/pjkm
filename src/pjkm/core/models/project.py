"""Project configuration and archetype definitions."""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, computed_field, field_validator


class Archetype(StrEnum):
    """Supported project archetypes."""

    SINGLE_PACKAGE = "single_package"
    SERVICE = "service"
    POLY_REPO = "poly_repo"
    SCRIPT_TOOL = "script_tool"


class ProjectConfig(BaseModel):
    """Central configuration describing what the user wants to build."""

    project_name: str = Field(min_length=1, max_length=100)
    archetype: Archetype
    python_version: str = Field(default="3.13")
    author_name: str = Field(default="")
    author_email: str = Field(default="")
    license: str = Field(default="MIT")
    description: str = Field(default="")

    selected_groups: list[str] = Field(default_factory=list)
    target_dir: Path = Field(default_factory=lambda: Path.cwd())
    dry_run: bool = False

    template_overrides: dict[str, str] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def project_slug(self) -> str:
        """Normalized project name for use in Python package paths."""
        return re.sub(r"[^a-zA-Z0-9]", "_", self.project_name).lower().strip("_")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def project_dir(self) -> Path:
        """Full path to the project directory that will be created."""
        return self.target_dir / self.project_name

    @field_validator("python_version")
    @classmethod
    def validate_python_version(cls, v: str) -> str:
        if not re.match(r"^\d+\.\d+$", v):
            msg = f"Python version must be in X.Y format, got {v!r}"
            raise ValueError(msg)
        return v
