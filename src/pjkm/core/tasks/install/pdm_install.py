"""Install task: run pdm install in the generated project."""

from __future__ import annotations

import subprocess

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.models.task import Phase, TaskResult
from pjkm.core.tasks.base import BaseTask


class PdmInstallTask(BaseTask):
    """Runs `pdm install` in the generated project directory."""

    id = "pdm_install"
    phase = Phase.INSTALL
    depends_on = []
    description = "Install project dependencies with PDM"

    def should_run(self, ctx: TaskContext) -> bool:
        return ctx.platform.has_tool("pdm") and (ctx.project_dir / "pyproject.toml").exists()

    def execute(self, ctx: TaskContext) -> TaskResult:
        if ctx.config.dry_run:
            return self.success_result(message="PDM install completed (dry run)")

        try:
            subprocess.run(
                ["pdm", "install"],
                cwd=ctx.project_dir,
                capture_output=True,
                check=True,
                text=True,
                timeout=120,
            )
            return self.success_result(message="PDM install completed")
        except subprocess.CalledProcessError as exc:
            return self.failure_result(f"pdm install failed: {exc.stderr[:500]}")
        except subprocess.TimeoutExpired:
            return self.failure_result("pdm install timed out after 120s")
