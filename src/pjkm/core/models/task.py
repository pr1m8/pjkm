"""Task system models: phases, definitions, results, and events."""

from __future__ import annotations

from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field


class Phase(IntEnum):
    """Execution phases in strict order."""

    SCAFFOLD = 1
    CONFIGURE = 2
    INSTALL = 3
    VERIFY = 4


class TaskDefinition(BaseModel):
    """Metadata describing a registered task."""

    id: str
    phase: Phase
    depends_on: list[str] = Field(default_factory=list)
    description: str = ""


class TaskResult(BaseModel):
    """Outcome of executing a single task."""

    task_id: str
    success: bool
    message: str = ""
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    skipped: bool = False


class TaskStarted(BaseModel):
    """Emitted when a task begins execution."""

    kind: Literal["task_started"] = "task_started"
    task_id: str
    phase: Phase
    description: str


class TaskProgress(BaseModel):
    """Emitted for intermediate task status updates."""

    kind: Literal["task_progress"] = "task_progress"
    task_id: str
    message: str
    fraction: float = 0.0


class TaskCompleted(BaseModel):
    """Emitted when a task finishes."""

    kind: Literal["task_completed"] = "task_completed"
    task_id: str
    result: TaskResult


class PhaseStarted(BaseModel):
    """Emitted when a phase begins."""

    kind: Literal["phase_started"] = "phase_started"
    phase: Phase


class PhaseCompleted(BaseModel):
    """Emitted when all tasks in a phase have finished."""

    kind: Literal["phase_completed"] = "phase_completed"
    phase: Phase


TaskEvent = TaskStarted | TaskProgress | TaskCompleted | PhaseStarted | PhaseCompleted
