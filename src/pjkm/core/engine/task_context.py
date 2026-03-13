"""Shared state bag passed through all task executions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from pjkm.core.models.platform import PlatformInfo
from pjkm.core.models.project import ProjectConfig
from pjkm.core.models.task import TaskResult


class TaskContext(BaseModel):
    """Mutable state passed to each task during execution.

    Holds the project configuration, target directory, accumulated results,
    and a shared pyproject dict that tasks can read/write to before final flush.
    """

    config: ProjectConfig
    platform: PlatformInfo = Field(default_factory=PlatformInfo)
    results: dict[str, TaskResult] = Field(default_factory=dict)
    pyproject_data: dict[str, Any] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)

    @property
    def project_dir(self) -> Path:
        return self.config.project_dir

    def get_result(self, task_id: str) -> TaskResult | None:
        """Look up a previous task's result by ID (O(1) dict lookup)."""
        return self.results.get(task_id)

    def has_group(self, group_id: str) -> bool:
        """Check if a package group was selected."""
        return group_id in self.config.selected_groups
