"""Configuration pattern models for .env, .secrets, and .config/ scaffolding."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EnvConfig(BaseModel):
    """Describes .env / .env.example variables to scaffold."""

    variables: dict[str, str] = Field(default_factory=dict)
    comments: dict[str, str] = Field(default_factory=dict)


class SecretsConfig(BaseModel):
    """Describes .secrets / .secrets.example variables to scaffold."""

    variables: dict[str, str] = Field(default_factory=dict)
    comments: dict[str, str] = Field(default_factory=dict)


class ToolConfig(BaseModel):
    """Describes a tool config file in .config/ directory."""

    filename: str
    content: str
    description: str = ""
