"""Template composer: layers multiple templates to build a complete project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pjkm.core.templates.loader import TemplateLoader
from pjkm.core.templates.renderer import TemplateRenderer


class TemplateComposer:
    """Composes a project by layering base + archetype + fragment templates.

    Rendering order:
    1. "base" template (shared by all archetypes)
    2. Archetype-specific template (e.g., "single_package")
    3. Fragment templates (e.g., from package groups)
    """

    def __init__(
        self,
        loader: TemplateLoader | None = None,
        renderer: TemplateRenderer | None = None,
    ) -> None:
        self._loader = loader or TemplateLoader()
        self._renderer = renderer or TemplateRenderer()

    def compose(
        self,
        archetype: str,
        dest: Path,
        data: dict[str, Any],
        fragments: list[str] | None = None,
        pretend: bool = False,
    ) -> list[str]:
        """Layer templates to build a complete project.

        Returns a list of template names that were applied.
        """
        applied: list[str] = []

        # 1. Base template
        base_path = self._loader.resolve("base")
        self._renderer.render(
            template_path=base_path,
            dest=dest,
            data=data,
            overwrite=False,
            pretend=pretend,
        )
        applied.append("base")

        # 2. Archetype template
        arch_path = self._loader.resolve(archetype)
        self._renderer.render(
            template_path=arch_path,
            dest=dest,
            data=data,
            overwrite=True,
            pretend=pretend,
        )
        applied.append(archetype)

        # 3. Fragments
        for frag_name in fragments or []:
            frag_path = self._loader.resolve(f"fragments/{frag_name}")
            self._renderer.render(
                template_path=frag_path,
                dest=dest,
                data=data,
                overwrite=True,
                skip_if_exists=["*.py"],
                pretend=pretend,
            )
            applied.append(f"fragments/{frag_name}")

        return applied
