"""Template renderer: wraps Copier's run_copy / run_update for project generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from copier import run_copy


class TemplateRenderer:
    """Renders a Copier template to a destination directory."""

    def render(
        self,
        template_path: Path,
        dest: Path,
        data: dict[str, Any] | None = None,
        overwrite: bool = False,
        skip_if_exists: list[str] | None = None,
        pretend: bool = False,
    ) -> None:
        """Render a template to the destination.

        Args:
            template_path: Path to the Copier template directory.
            dest: Destination directory.
            data: Answers to template questions (bypasses prompts).
            overwrite: Whether to overwrite existing files.
            skip_if_exists: File patterns to skip if they already exist.
            pretend: If True, don't actually write files.
        """
        run_copy(
            src_path=str(template_path),
            dst_path=dest,
            data=data or {},
            defaults=True,
            overwrite=overwrite,
            skip_if_exists=skip_if_exists or [],
            pretend=pretend,
            quiet=True,
            unsafe=True,
            skip_tasks=True,
        )

    def update(
        self,
        template_path: Path,
        dest: Path,
        data: dict[str, Any] | None = None,
        pretend: bool = False,
    ) -> None:
        """Re-render a template that was previously applied to the destination.

        Attempts ``copier.run_update`` which reads ``.copier-answers.yml`` from
        *dest* to determine the original template.  If that file is missing the
        caller should fall back to :meth:`render` with ``overwrite=True``.

        Args:
            template_path: Path to the Copier template directory (unused when
                ``run_update`` reads the answers file, but kept for API symmetry
                with :meth:`render`).
            dest: Destination directory containing the previously-generated project.
            data: Answers/data overrides for template variables.
            pretend: If True, don't actually write files.
        """
        from copier import run_update

        run_update(
            dst_path=dest,
            data=data or {},
            defaults=True,
            pretend=pretend,
            quiet=True,
            unsafe=True,
            skip_tasks=True,
            overwrite=True,
        )
