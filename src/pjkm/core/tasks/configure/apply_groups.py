"""Configure task: apply selected package groups to pyproject.toml and scaffold code."""

from __future__ import annotations

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

import tomli_w

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.groups.registry import GroupRegistry
from pjkm.core.groups.resolver import GroupResolver
from pjkm.core.models.task import Phase, TaskResult
from pjkm.core.tasks.base import BaseTask
from pjkm.core.templates.loader import TemplateLoader, TemplateNotFoundError
from pjkm.core.templates.renderer import TemplateRenderer
from pjkm.core.utils import deep_merge


class ApplyGroupsTask(BaseTask):
    """Merges selected package groups into pyproject.toml and renders scaffolded code."""

    id = "apply_groups"
    phase = Phase.CONFIGURE
    depends_on = []
    description = "Apply package groups (dependencies + scaffolded code)"

    def should_run(self, ctx: TaskContext) -> bool:
        return len(ctx.config.selected_groups) > 0

    def execute(self, ctx: TaskContext) -> TaskResult:
        config = ctx.config
        pyproject_path = config.project_dir / "pyproject.toml"

        if not pyproject_path.exists():
            return self.failure_result("pyproject.toml not found")

        # Load and resolve groups (built-in + custom + remote sources)
        registry = GroupRegistry()
        registry.load_all()

        # Validate group IDs before proceeding
        valid_ids = set(registry.group_ids)
        invalid = [g for g in config.selected_groups if g not in valid_ids]
        if invalid:
            return self.failure_result(
                f"Unknown group(s): {', '.join(sorted(invalid))}. "
                f"Valid groups: {', '.join(sorted(valid_ids))}"
            )

        resolver = GroupResolver({g.id: g for g in registry.list_all()})
        try:
            groups = resolver.resolve(config.selected_groups, platform=ctx.platform)
        except Exception as exc:
            return self.failure_result(str(exc))

        # Read existing pyproject.toml
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        # Merge dependencies from each group
        optional_deps = pyproject.setdefault("project", {}).setdefault(
            "optional-dependencies", {}
        )
        tool_config = pyproject.setdefault("tool", {})

        for group in groups:
            for group_name, deps in group.dependencies.items():
                existing = optional_deps.get(group_name, [])
                merged = list(dict.fromkeys(existing + deps))
                optional_deps[group_name] = merged

            for tool_name, tool_conf in group.pyproject_tool_config.items():
                deep_merge(tool_config, tool_name, tool_conf)

        # Track applied groups for `pjkm add`
        pjkm_config = pyproject.setdefault("tool", {}).setdefault("pjkm", {})
        existing_groups = pjkm_config.get("groups", [])
        pjkm_config["groups"] = sorted(set(existing_groups + [g.id for g in groups]))

        # Write back (skip if dry run)
        if not config.dry_run:
            with open(pyproject_path, "wb") as f:
                tomli_w.dump(pyproject, f)

        # Render scaffolded files from group fragments
        loader = TemplateLoader()
        renderer = TemplateRenderer()
        data = {
            "project_name": config.project_name,
            "project_slug": config.project_slug,
            "python_version": config.python_version,
        }

        rendered_fragments = []
        for group in groups:
            for sf in group.scaffolded_files:
                try:
                    frag_path = loader.resolve(f"fragments/{sf.template_fragment}")
                    dest = config.project_dir / sf.destination
                    if not config.dry_run:
                        dest.mkdir(parents=True, exist_ok=True)
                    renderer.render(
                        template_path=frag_path,
                        dest=dest,
                        data={**data, **sf.conditions},
                        overwrite=True,
                        pretend=config.dry_run,
                    )
                    rendered_fragments.append(sf.template_fragment)
                except TemplateNotFoundError:
                    pass  # Fragment not yet created — skip silently

        group_names = [g.id for g in groups]
        suffix = " (dry run)" if config.dry_run else ""
        return self.success_result(
            message=f"Applied groups: {', '.join(group_names)}{suffix}",
            files_modified=[str(pyproject_path)],
        )
