"""User defaults: loads config from ~/.pjkmrc.yaml or ./.pjkmrc.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class GitHubDefaults(BaseModel):
    """GitHub/remote repository defaults."""

    org: str = ""
    visibility: str = "private"  # "private", "public", "internal"
    remote: str = ""  # e.g. "github.com", "github.mycompany.com"
    create_repo: bool = False  # auto-create repo via gh CLI
    default_branch: str = "main"


class GroupSource(BaseModel):
    """A remote git repo containing package group YAML definitions."""

    url: str  # git URL: https://... or git@...:...
    name: str = ""  # short name (derived from URL if empty)
    path: str = ""  # subdirectory within the repo (default: root)
    ref: str = ""  # branch/tag/commit (default: HEAD)


class UserDefaults(BaseModel):
    """User-configurable defaults loaded from .pjkmrc.yaml files."""

    author_name: str = ""
    author_email: str = ""
    license: str = "MIT"
    python_version: str = "3.13"
    archetype: str = "single_package"
    groups: list[str] = Field(default_factory=list)
    target_dir: str = "."
    github: GitHubDefaults = Field(default_factory=GitHubDefaults)
    group_sources: list[GroupSource] = Field(default_factory=list)

    @classmethod
    def load(cls) -> UserDefaults:
        """Load defaults from config files.

        Searches in order (later files override earlier):
        1. ~/.pjkmrc.yaml  (global defaults)
        2. ./.pjkmrc.yaml  (project/workspace defaults)
        """
        merged: dict[str, Any] = {}

        paths = [
            Path.home() / ".pjkmrc.yaml",
            Path.cwd() / ".pjkmrc.yaml",
        ]

        for path in paths:
            if path.is_file():
                try:
                    data = yaml.safe_load(path.read_text()) or {}
                    if isinstance(data, dict):
                        merged.update(data)
                except Exception:
                    pass  # Silently skip malformed config

        return cls.model_validate(merged)
