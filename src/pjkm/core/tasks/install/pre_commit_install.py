"""Install task: install pre-commit hooks."""

from __future__ import annotations

import subprocess

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.models.task import Phase, TaskResult
from pjkm.core.tasks.base import BaseTask


class PreCommitInstallTask(BaseTask):
    """Installs pre-commit hooks in the generated project."""

    id = "pre_commit_install"
    phase = Phase.INSTALL
    depends_on = ["pdm_install"]
    description = "Install pre-commit hooks"

    def should_run(self, ctx: TaskContext) -> bool:
        return (
            ctx.platform.has_tool("pre-commit")
            and (ctx.project_dir / ".pre-commit-config.yaml").exists()
            and (ctx.project_dir / ".git").exists()
        )

    def execute(self, ctx: TaskContext) -> TaskResult:
        if ctx.config.dry_run:
            return self.success_result(message="Pre-commit hooks installed (dry run)")

        try:
            subprocess.run(
                ["pre-commit", "install"],
                cwd=ctx.project_dir,
                capture_output=True,
                check=True,
                text=True,
                timeout=60,
            )
            subprocess.run(
                ["pre-commit", "install", "--hook-type", "commit-msg"],
                cwd=ctx.project_dir,
                capture_output=True,
                check=True,
                text=True,
                timeout=60,
            )
            return self.success_result(message="Pre-commit hooks installed")
        except subprocess.CalledProcessError as exc:
            return self.failure_result(f"pre-commit install failed: {exc.stderr[:500]}")
        except subprocess.TimeoutExpired:
            return self.failure_result("pre-commit install timed out")
