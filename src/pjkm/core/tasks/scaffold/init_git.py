"""Scaffold task: initialize git repository."""

from __future__ import annotations

import subprocess

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.models.task import Phase, TaskResult
from pjkm.core.tasks.base import BaseTask


class InitGitTask(BaseTask):
    """Initializes a git repository in the project directory."""

    id = "init_git"
    phase = Phase.SCAFFOLD
    depends_on = ["init_project"]
    description = "Initialize git repository"

    def should_run(self, ctx: TaskContext) -> bool:
        git_dir = ctx.project_dir / ".git"
        return not git_dir.exists() and ctx.platform.has_tool("git")

    def execute(self, ctx: TaskContext) -> TaskResult:
        if ctx.config.dry_run:
            return self.success_result(message="Git repository initialized (dry run)")

        try:
            subprocess.run(
                ["git", "init"],
                cwd=ctx.project_dir,
                capture_output=True,
                check=True,
                text=True,
            )
            return self.success_result(message="Git repository initialized")
        except subprocess.CalledProcessError as exc:
            return self.failure_result(f"git init failed: {exc.stderr}")
