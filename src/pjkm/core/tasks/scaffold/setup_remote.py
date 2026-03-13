"""Scaffold task: configure git remote and optionally create GitHub repo."""

from __future__ import annotations

import subprocess

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.models.task import Phase, TaskResult
from pjkm.core.tasks.base import BaseTask


class SetupRemoteTask(BaseTask):
    """Configures git remote origin and optionally creates a GitHub repo."""

    id = "setup_remote"
    phase = Phase.SCAFFOLD
    depends_on = ["init_git"]
    description = "Configure git remote"

    def should_run(self, ctx: TaskContext) -> bool:
        github = ctx.extra.get("github", {})
        # Run if org or remote is configured
        return bool(github.get("org") or github.get("remote"))

    def execute(self, ctx: TaskContext) -> TaskResult:
        if ctx.config.dry_run:
            return self.success_result(message="Would configure git remote (dry run)")

        github = ctx.extra.get("github", {})
        org = github.get("org", "")
        remote_host = github.get("remote", "github.com")
        visibility = github.get("visibility", "private")
        create_repo = github.get("create_repo", False)
        default_branch = github.get("default_branch", "main")

        project_name = ctx.config.project_name
        project_dir = ctx.project_dir

        if not (project_dir / ".git").exists():
            return self.skip_result()

        actions: list[str] = []

        # Build remote URL
        if org:
            remote_url = f"git@{remote_host}:{org}/{project_name}.git"
        else:
            remote_url = ""

        # Optionally create the repo via gh CLI
        if create_repo and org and ctx.platform.has_tool("gh"):
            vis_flag = (
                f"--{visibility}"
                if visibility in ("public", "private", "internal")
                else "--private"
            )
            try:
                subprocess.run(
                    [
                        "gh",
                        "repo",
                        "create",
                        f"{org}/{project_name}",
                        vis_flag,
                        "--confirm",
                    ],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                actions.append(f"Created {visibility} repo {org}/{project_name}")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass  # Non-fatal — repo may already exist

        # Set remote origin
        if remote_url:
            try:
                subprocess.run(
                    ["git", "remote", "add", "origin", remote_url],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                actions.append(f"Remote: {remote_url}")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass  # Remote may already exist

        # Set default branch
        if default_branch != "master":
            try:
                subprocess.run(
                    ["git", "branch", "-M", default_branch],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        return self.success_result(
            message="; ".join(actions) if actions else "Git remote configured",
        )
