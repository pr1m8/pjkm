"""Verify task: validate the generated project structure."""

from __future__ import annotations

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.models.project import Archetype
from pjkm.core.models.task import Phase, TaskResult
from pjkm.core.tasks.base import BaseTask

# Base files expected in all archetypes
_BASE_FILES = [
    "pyproject.toml",
    "README.md",
    ".gitignore",
    ".editorconfig",
    ".gitattributes",
    ".python-version",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    "tests/__init__.py",
]

# Expected paths per archetype (relative to project root)
EXPECTED_FILES: dict[Archetype, list[str]] = {
    Archetype.SINGLE_PACKAGE: [*_BASE_FILES],
    Archetype.SERVICE: [
        *_BASE_FILES,
        "Makefile",
        "infra/compose.yaml",
        ".env.example",
    ],
    Archetype.POLY_REPO: [
        *_BASE_FILES,
        "Makefile",
        "infra/compose.yaml",
        ".env.example",
    ],
    Archetype.SCRIPT_TOOL: [*_BASE_FILES],
}


class VerifyStructureTask(BaseTask):
    """Validates that expected files were created for the archetype."""

    id = "verify_structure"
    phase = Phase.VERIFY
    depends_on = []
    description = "Verify project structure"

    def execute(self, ctx: TaskContext) -> TaskResult:
        project_dir = ctx.project_dir
        archetype = ctx.config.archetype
        expected = EXPECTED_FILES.get(archetype, [])
        missing: list[str] = []

        for rel_path in expected:
            if not (project_dir / rel_path).exists():
                missing.append(rel_path)

        if missing:
            return self.failure_result(f"Missing expected files: {', '.join(missing)}")

        # Also verify src layout exists
        src_init = project_dir / "src" / ctx.config.project_slug / "__init__.py"
        if not src_init.exists():
            return self.failure_result(f"Missing {src_init.relative_to(project_dir)}")

        return self.success_result(message="Project structure verified")
