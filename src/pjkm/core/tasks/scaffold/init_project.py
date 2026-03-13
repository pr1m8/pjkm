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

        return self.success_result(
            message=f"Applied templates: {', '.join(applied)}",
        )
