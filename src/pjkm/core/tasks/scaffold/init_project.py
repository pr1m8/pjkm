"""Scaffold task: create the project directory and render base + archetype templates."""

from __future__ import annotations

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.models.task import Phase, TaskResult
from pjkm.core.tasks.base import BaseTask
from pjkm.core.templates.composer import TemplateComposer


class InitProjectTask(BaseTask):
    """Creates the project directory and renders base + archetype templates."""

    id = "init_project"
    phase = Phase.SCAFFOLD
    depends_on = []
    description = "Create project structure from templates"

    def execute(self, ctx: TaskContext) -> TaskResult:
        config = ctx.config
        dest = config.project_dir

        if dest.exists() and any(dest.iterdir()):
            return self.failure_result(
                f"Directory {dest} already exists and is not empty"
            )

        dest.mkdir(parents=True, exist_ok=True)

        data = {
            "project_name": config.project_name,
            "project_slug": config.project_slug,
            "description": config.description,
            "author_name": config.author_name,
            "author_email": config.author_email,
            "python_version": config.python_version,
            "license": config.license,
        }

        composer = TemplateComposer()
        applied = composer.compose(
            archetype=config.archetype.value,
            dest=dest,
            data=data,
            pretend=config.dry_run,
        )

        ctx.extra["applied_templates"] = applied

        # Record archetype in [tool.pjkm] so `pjkm update` can find it later
        if not config.dry_run:
            self._record_archetype(dest, config.archetype.value)

        return self.success_result(
            message=f"Applied templates: {', '.join(applied)}",
        )

    @staticmethod
    def _record_archetype(dest: "Path", archetype: str) -> None:  # noqa: F821
        """Write the archetype into [tool.pjkm] in pyproject.toml."""
        from pathlib import Path

        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        import tomli_w

        pyproject_path = Path(dest) / "pyproject.toml"
        if not pyproject_path.exists():
            return

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        pjkm_config = pyproject.setdefault("tool", {}).setdefault("pjkm", {})
        pjkm_config["archetype"] = archetype

        with open(pyproject_path, "wb") as f:
            tomli_w.dump(pyproject, f)
