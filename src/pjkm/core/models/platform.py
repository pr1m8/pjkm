"""Platform detection models."""

from __future__ import annotations

import platform
import shutil

from pydantic import BaseModel, Field, computed_field


class PlatformInfo(BaseModel):
    """Current platform details, used for OS-dependent group filtering."""

    os: str = Field(default_factory=lambda: platform.system().lower())
    arch: str = Field(default_factory=lambda: platform.machine().lower())

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_macos(self) -> bool:
        return self.os == "darwin"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_linux(self) -> bool:
        return self.os == "linux"

    def has_tool(self, name: str) -> bool:
        """Check if a CLI tool is available on PATH."""
        return shutil.which(name) is not None
