"""Template loader: resolves built-in, git, and local template sources."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

BUILTIN_TEMPLATES_ANCHOR = "pjkm.templates"

ARCHETYPE_TEMPLATES = {
    "single_package",
    "service",
    "poly_repo",
    "script_tool",
}


class TemplateNotFoundError(Exception):
    """Raised when a template cannot be resolved."""


class TemplateLoader:
    """Resolves template names to local filesystem paths."""

    def resolve(self, name: str) -> Path:
        """Resolve a template name to a local path.

        Supports:
        - Built-in names: "base", "single_package", "service", etc.
        - Local paths: "/path/to/template" or "./relative/path"
        - Fragment names: "fragments/infra_otel"
        """
        # Local path
        local = Path(name)
        if local.is_absolute() and local.exists():
            return local
        if local.exists() and (local / "copier.yml").exists():
            return local.resolve()

        # Built-in template
        return self._resolve_builtin(name)

    def _resolve_builtin(self, name: str) -> Path:
        """Resolve a built-in template by name."""
        try:
            ref = resources.files(BUILTIN_TEMPLATES_ANCHOR).joinpath(name)
            path = Path(str(ref))
            if path.is_dir():
                return path
        except (TypeError, FileNotFoundError):
            pass

        msg = f"Template {name!r} not found"
        raise TemplateNotFoundError(msg)

    def list_builtin(self) -> list[str]:
        """List available built-in template names."""
        try:
            ref = resources.files(BUILTIN_TEMPLATES_ANCHOR)
            base = Path(str(ref))
            if not base.is_dir():
                return []
            return sorted(
                d.name for d in base.iterdir() if d.is_dir() and not d.name.startswith("_")
            )
        except (TypeError, FileNotFoundError):
            return []
