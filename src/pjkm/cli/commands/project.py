"""Project lifecycle commands — init, add, update, upgrade, link, preview."""

from __future__ import annotations

import typer


def init(
    name: str = typer.Argument(help="Project name"),
    archetype: str = typer.Option(
        "",
        "--archetype",
        "-a",
        help="Project archetype: single-package, service, poly-repo, script-tool",
    ),
    group: list[str] = typer.Option(
        [],
        "--group",
        "-g",
        help="Package groups to include (repeatable)",
    ),
    recipe_name: str = typer.Option(
        "",
        "--recipe",
        "-r",
        help="Use a named recipe (overrides --archetype and --group)",
    ),
    directory: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Target directory (project will be created as a subdirectory)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
    author: str = typer.Option(
        "",
        "--author",
        help="Author name (overrides defaults)",
    ),
    email: str = typer.Option(
        "",
        "--email",
        help="Author email (overrides defaults)",
    ),
) -> None:
    """Initialize a new project from a template.

    Options not provided on the command line are filled from defaults.
    Set defaults in ~/.pjkmrc.yaml or ./.pjkmrc.yaml.
    Use --recipe for a pre-configured archetype + groups combo.
    """
    from pathlib import Path

    from rich.console import Console

    from pjkm.core.defaults import UserDefaults
    from pjkm.core.engine.project_engine import ProjectEngine
    from pjkm.core.models.project import Archetype, ProjectConfig
    from pjkm.core.models.task import (
        PhaseCompleted,
        PhaseStarted,
        TaskCompleted,
        TaskEvent,
        TaskStarted,
    )
    from pjkm.core.tasks.defaults import create_default_registry

    console = Console()

    # If recipe specified, pull archetype + groups from it
    if recipe_name:
        from pjkm.cli.commands.recipes import RECIPES

        if recipe_name not in RECIPES:
            console.print(
                f"[red]Unknown recipe: {recipe_name}. "
                f"Options: {', '.join(RECIPES.keys())}[/red]"
            )
            raise typer.Exit(1)
        r = RECIPES[recipe_name]
        archetype = r["archetype"]
        group = r["groups"]
        console.print(
            f"[dim]Using recipe '{recipe_name}' "
            f"({r['archetype']}, {len(r['groups'])} groups)[/dim]"
        )

    # Load user defaults from ~/.pjkmrc.yaml and ./.pjkmrc.yaml
    user_defaults = UserDefaults.load()

    # Fill in missing values from defaults
    if not archetype:
        archetype = user_defaults.archetype
    if not group:
        group = user_defaults.groups
    if not directory:
        directory = user_defaults.target_dir
    if not author:
        author = user_defaults.author_name
    if not email:
        email = user_defaults.author_email

    # Normalize: accept hyphens (single-package -> single_package)
    archetype = archetype.replace("-", "_")

    try:
        arch = Archetype(archetype)
    except ValueError:
        console.print(f"[red]Unknown archetype: {archetype}[/red]")
        console.print(f"Valid options: {', '.join(a.value for a in Archetype)}")
        raise typer.Exit(1)

    config = ProjectConfig(
        project_name=name,
        archetype=arch,
        selected_groups=group,
        target_dir=Path(directory).resolve(),
        dry_run=dry_run,
        author_name=author,
        author_email=email,
        python_version=user_defaults.python_version,
        license=user_defaults.license,
    )

    def on_event(event: TaskEvent) -> None:
        match event:
            case PhaseStarted(phase=phase):
                console.print(f"\n[bold blue]>>> Phase: {phase.name}[/bold blue]")
            case TaskStarted(task_id=tid, description=desc):
                console.print(f"  [dim]Running:[/dim] {desc or tid}")
            case TaskCompleted(task_id=tid, result=result):
                if result.skipped:
                    console.print(f"  [yellow]Skipped:[/yellow] {tid}")
                elif result.success:
                    console.print(f"  [green]Done:[/green] {tid}")
                else:
                    console.print(f"  [red]Failed:[/red] {tid} — {result.message}")
            case PhaseCompleted():
                pass

    registry = create_default_registry()
    engine = ProjectEngine(task_registry=registry)

    if dry_run:
        console.print(f"[bold]Dry run:[/bold] would create {config.project_name}")
        console.print(f"  Archetype: {config.archetype.value}")
        console.print(f"  Groups: {', '.join(config.selected_groups) or '(none)'}")
        console.print(f"  Target: {config.project_dir}")
        raise typer.Exit(0)

    github_extra = user_defaults.github.model_dump()
    result = engine.execute(config, on_event=on_event, extra={"github": github_extra})

    if result.success:
        console.print(
            f"\n[bold green]Project {name} created at {config.project_dir}[/bold green]"
        )
        console.print()
        console.print("[dim]Next steps:[/dim]")
        console.print(f"  cd {config.project_dir}")
        console.print("  pdm install")
        console.print("  pdm run pytest")
    else:
        console.print("\n[bold red]Project creation failed[/bold red]")
        for f in result.failed_tasks:
            console.print(f"  [red]{f.task_id}:[/red] {f.message}")
        raise typer.Exit(1)


def add(
    group: list[str] = typer.Option(
        ...,
        "--group",
        "-g",
        help="Package group(s) to add (repeatable)",
    ),
    directory: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Project directory containing pyproject.toml (default: cwd)",
    ),
) -> None:
    """Add package groups to an existing project.

    Reads the existing pyproject.toml, resolves the requested groups
    (including transitive dependencies), merges new dependencies and
    tool config, renders scaffolded files, and updates [tool.pjkm.groups].
    """
    import re
    from pathlib import Path

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    import tomli_w
    from rich.console import Console

    from pjkm.core.groups.registry import GroupRegistry
    from pjkm.core.groups.resolver import GroupResolver
    from pjkm.core.models.platform import PlatformInfo
    from pjkm.core.templates.loader import TemplateLoader, TemplateNotFoundError
    from pjkm.core.templates.renderer import TemplateRenderer

    console = Console()
    project_dir = Path(directory).resolve() if directory else Path.cwd()
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.exists():
        console.print(
            f"[red]pyproject.toml not found in {project_dir}[/red]"
        )
        raise typer.Exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    pjkm_config = pyproject.get("tool", {}).get("pjkm", {})
    already_applied: list[str] = pjkm_config.get("groups", [])

    registry = GroupRegistry()
    registry.load_all()

    valid_ids = set(registry.group_ids)
    invalid = [g for g in group if g not in valid_ids]
    if invalid:
        console.print(
            f"[red]Unknown group(s): {', '.join(sorted(invalid))}[/red]"
        )
        console.print(
            f"Valid groups: {', '.join(sorted(valid_ids))}"
        )
        raise typer.Exit(1)

    resolver = GroupResolver({g.id: g for g in registry.list_all()})
    platform = PlatformInfo()

    try:
        all_resolved = resolver.resolve(group, platform=platform)
    except Exception as exc:
        console.print(f"[red]Group resolution failed: {exc}[/red]")
        raise typer.Exit(1)

    new_groups = [g for g in all_resolved if g.id not in already_applied]

    if not new_groups:
        console.print("[dim]All requested groups are already applied.[/dim]")
        raise typer.Exit(0)

    optional_deps = pyproject.setdefault("project", {}).setdefault(
        "optional-dependencies", {}
    )
    tool_config = pyproject.setdefault("tool", {})

    for g in new_groups:
        for group_name, deps in g.dependencies.items():
            existing = optional_deps.get(group_name, [])
            merged = list(dict.fromkeys(existing + deps))
            optional_deps[group_name] = merged

        for tool_name, tool_conf in g.pyproject_tool_config.items():
            from pjkm.core.utils import deep_merge

            deep_merge(tool_config, tool_name, tool_conf)

    loader = TemplateLoader()
    renderer = TemplateRenderer()

    project_name = pyproject.get("project", {}).get("name", project_dir.name)
    project_slug = re.sub(r"[^a-zA-Z0-9]", "_", project_name).lower().strip("_")
    python_version = "3.13"
    requires_python = pyproject.get("project", {}).get("requires-python", "")
    if requires_python:
        m = re.search(r"(\d+\.\d+)", requires_python)
        if m:
            python_version = m.group(1)

    data = {
        "project_name": project_name,
        "project_slug": project_slug,
        "python_version": python_version,
    }

    rendered_fragments: list[str] = []
    for g in new_groups:
        for sf in g.scaffolded_files:
            try:
                frag_path = loader.resolve(f"fragments/{sf.template_fragment}")
                dest = project_dir / sf.destination
                dest.mkdir(parents=True, exist_ok=True)
                renderer.render(
                    template_path=frag_path,
                    dest=dest,
                    data={**data, **sf.conditions},
                    overwrite=True,
                )
                rendered_fragments.append(sf.template_fragment)
            except TemplateNotFoundError:
                pass

    pjkm_tool = pyproject.setdefault("tool", {}).setdefault("pjkm", {})
    pjkm_tool["groups"] = sorted(set(already_applied + [g.id for g in new_groups]))

    with open(pyproject_path, "wb") as f:
        tomli_w.dump(pyproject, f)

    console.print(
        f"[bold green]Added {len(new_groups)} group(s) to {pyproject_path}[/bold green]"
    )
    for g in new_groups:
        dep_count = sum(len(deps) for deps in g.dependencies.values())
        console.print(f"  [cyan]{g.id}[/cyan] — {dep_count} dep(s)")
    if rendered_fragments:
        console.print()
        console.print("[dim]Scaffolded files:[/dim]")
        for frag in rendered_fragments:
            console.print(f"  [green]{frag}[/green]")
    console.print()
    console.print("[dim]Next: run `pdm install` to install new dependencies.[/dim]")


def _extract_python_version(requires_python: str) -> str:
    """Extract a X.Y version string from a requires-python specifier."""
    import re

    m = re.search(r"(\d+\.\d+)", requires_python)
    return m.group(1) if m else "3.13"


def _extract_license(license_field: dict | str) -> str:
    """Extract a license string from pyproject.toml's license field."""
    if isinstance(license_field, dict):
        return license_field.get("text", "MIT")
    return str(license_field) if license_field else "MIT"


def update(
    directory: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Project directory to update (default: current directory)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
) -> None:
    """Re-render templates on an existing project.

    Reads [tool.pjkm] from pyproject.toml to find the archetype and
    applied groups, then re-renders the base and archetype templates.
    Useful after updating pjkm to pick up new CI workflows, gitignore
    improvements, etc.

    If .copier-answers.yml exists, uses Copier's update mechanism.
    Otherwise, falls back to re-rendering with overwrite.
    """
    import re
    from pathlib import Path

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    from rich.console import Console

    from pjkm.core.templates.loader import TemplateLoader
    from pjkm.core.templates.renderer import TemplateRenderer

    console = Console()

    project_dir = Path(directory).resolve() if directory else Path.cwd()

    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        console.print(f"[red]No pyproject.toml found in {project_dir}[/red]")
        console.print(
            "[dim]Run this command from a pjkm-generated project directory, "
            "or use --dir to specify one.[/dim]"
        )
        raise typer.Exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    pjkm_meta = pyproject.get("tool", {}).get("pjkm", {})
    archetype = pjkm_meta.get("archetype", "")
    groups = pjkm_meta.get("groups", [])

    if not archetype:
        console.print(
            "[yellow]No [tool.pjkm] archetype found in pyproject.toml.[/yellow]"
        )
        console.print(
            "[dim]This project may not have been created by pjkm, "
            "or was created before archetype tracking was added.[/dim]"
        )
        console.print("[dim]Continuing with base template only.[/dim]")

    project_meta = pyproject.get("project", {})
    project_name = project_meta.get("name", project_dir.name)
    project_slug = re.sub(r"[^a-zA-Z0-9]", "_", project_name).lower().strip("_")

    authors = project_meta.get("authors", [{}])
    first_author = authors[0] if authors else {}

    data = {
        "project_name": project_name,
        "project_slug": project_slug,
        "description": project_meta.get("description", ""),
        "author_name": first_author.get("name", ""),
        "author_email": first_author.get("email", ""),
        "python_version": _extract_python_version(
            project_meta.get("requires-python", ">=3.13")
        ),
        "license": _extract_license(project_meta.get("license", {})),
    }

    if dry_run:
        console.print("[bold]Dry run:[/bold] would update templates in-place")
        console.print(f"  Project:   {project_name}")
        console.print(f"  Directory: {project_dir}")
        console.print(f"  Archetype: {archetype or '(none)'}")
        console.print(f"  Groups:    {', '.join(groups) or '(none)'}")
        raise typer.Exit(0)

    copier_answers = project_dir / ".copier-answers.yml"
    use_copier_update = copier_answers.exists()

    renderer = TemplateRenderer()
    loader = TemplateLoader()
    applied: list[str] = []

    if use_copier_update:
        console.print(
            "[dim]Found .copier-answers.yml — using Copier update.[/dim]"
        )
        try:
            renderer.update(
                template_path=loader.resolve("base"),
                dest=project_dir,
                data=data,
                pretend=False,
            )
            applied.append("base (copier update)")
        except Exception as exc:
            console.print(
                f"[yellow]Copier update failed ({exc}), "
                f"falling back to overwrite.[/yellow]"
            )
            use_copier_update = False

    if not use_copier_update:
        console.print("[dim]Re-rendering templates with overwrite.[/dim]")

        base_path = loader.resolve("base")
        renderer.render(
            template_path=base_path,
            dest=project_dir,
            data=data,
            overwrite=True,
            pretend=False,
        )
        applied.append("base")

        if archetype:
            try:
                arch_path = loader.resolve(archetype)
                renderer.render(
                    template_path=arch_path,
                    dest=project_dir,
                    data=data,
                    overwrite=True,
                    pretend=False,
                )
                applied.append(archetype)
            except Exception as exc:
                console.print(
                    f"[yellow]Could not render archetype "
                    f"template '{archetype}': {exc}[/yellow]"
                )

    console.print()
    console.print(
        f"[bold green]Updated {project_name} in {project_dir}[/bold green]"
    )
    console.print(f"  Templates applied: {', '.join(applied)}")
    if groups:
        console.print(f"  Groups in project: {', '.join(groups)}")
        console.print(
            "[dim]  Note: group dependencies/configs were not re-applied. "
            "Use 'pjkm add' to modify groups.[/dim]"
        )


def upgrade(
    group: list[str] = typer.Option(
        [],
        "--group",
        "-g",
        help="Specific group(s) to upgrade (default: all applied groups)",
    ),
    directory: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Project directory (default: cwd)",
    ),
    latest: bool = typer.Option(
        False,
        "--latest",
        help="Remove version pins and use latest (e.g. 'pkg' instead of 'pkg>=1.0')",
    ),
    refresh_tools: bool = typer.Option(
        False,
        "--refresh-tools",
        help="Re-apply tool config from group definitions (overwrites customizations)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would change without modifying files",
    ),
    install: bool = typer.Option(
        True,
        "--install/--no-install",
        help="Run `pdm install` after upgrading (default: yes)",
    ),
) -> None:
    """Upgrade dependencies for applied groups to their latest defined versions.

    Reads [tool.pjkm.groups] from pyproject.toml, loads the current group
    definitions, and replaces dependency version pins with the latest from
    the group YAML files. Optionally re-applies tool config sections.

    Examples:

      pjkm upgrade                        # upgrade all group deps
      pjkm upgrade -g logging -g testing  # upgrade specific groups
      pjkm upgrade --latest               # strip version pins entirely
      pjkm upgrade --refresh-tools        # also re-apply [tool.*] config
      pjkm upgrade --dry-run              # preview changes
    """
    import re
    import subprocess
    from pathlib import Path

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    import tomli_w
    from rich.console import Console
    from rich.table import Table

    from pjkm.core.groups.registry import GroupRegistry
    from pjkm.core.groups.resolver import GroupResolver
    from pjkm.core.models.platform import PlatformInfo

    console = Console()
    project_dir = Path(directory).resolve() if directory else Path.cwd()
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.exists():
        console.print(f"[red]pyproject.toml not found in {project_dir}[/red]")
        raise typer.Exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    pjkm_config = pyproject.get("tool", {}).get("pjkm", {})
    applied_groups: list[str] = pjkm_config.get("groups", [])

    if not applied_groups:
        console.print("[yellow]No groups found in [tool.pjkm.groups].[/yellow]")
        console.print("[dim]Use `pjkm add` to add groups first.[/dim]")
        raise typer.Exit(1)

    target_groups = group if group else applied_groups

    registry = GroupRegistry()
    registry.load_all()
    valid_ids = set(registry.group_ids)

    invalid = [g for g in target_groups if g not in valid_ids]
    if invalid:
        console.print(f"[red]Unknown group(s): {', '.join(sorted(invalid))}[/red]")
        raise typer.Exit(1)

    not_applied = [g for g in target_groups if g not in applied_groups]
    if not_applied:
        console.print(
            f"[yellow]Group(s) not in project: {', '.join(sorted(not_applied))}[/yellow]"
        )
        console.print("[dim]Use `pjkm add` to add them first.[/dim]")
        raise typer.Exit(1)

    resolver = GroupResolver({g.id: g for g in registry.list_all()})
    platform = PlatformInfo()
    try:
        resolved = resolver.resolve(target_groups, platform=platform)
    except Exception as exc:
        console.print(f"[red]Group resolution failed: {exc}[/red]")
        raise typer.Exit(1)

    target_set = set(target_groups)
    groups_to_upgrade = [g for g in resolved if g.id in target_set]

    dep_changes: list[tuple[str, str, str, str]] = []
    tool_changes: list[str] = []

    optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
    tool_config = pyproject.get("tool", {})

    for grp in groups_to_upgrade:
        for section, new_deps in grp.dependencies.items():
            existing = optional_deps.get(section, [])
            existing_map: dict[str, str] = {}
            for dep in existing:
                m = re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)\s*(.*)", dep)
                if m:
                    existing_map[m.group(1).lower()] = dep

            updated: list[str] = []
            for new_dep in new_deps:
                m_new = re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)\s*(.*)", new_dep)
                if not m_new:
                    updated.append(new_dep)
                    continue

                pkg_name = m_new.group(1).lower()
                if latest:
                    final_dep = m_new.group(1)
                else:
                    final_dep = new_dep

                old_dep = existing_map.get(pkg_name, "")
                if old_dep != final_dep:
                    dep_changes.append((section, pkg_name, old_dep, final_dep))

                updated.append(final_dep)
                existing_map.pop(pkg_name, None)

            remaining = [
                dep for dep in existing
                if re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)", dep)
                and re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)", dep).group(1).lower()
                in existing_map
            ]
            optional_deps[section] = updated + remaining

        if refresh_tools and grp.pyproject_tool_config:
            for tool_name, tool_conf in grp.pyproject_tool_config.items():
                parts = tool_name.split(".")
                current = tool_config
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = tool_conf
                tool_changes.append(f"[tool.{tool_name}]")

    if dry_run:
        console.print("[bold]Dry run — no changes will be made[/bold]\n")

    if dep_changes:
        table = Table(title="Dependency Changes")
        table.add_column("Section", style="cyan")
        table.add_column("Package")
        table.add_column("Old", style="red")
        table.add_column("New", style="green")
        for section, pkg, old, new in dep_changes:
            table.add_row(section, pkg, old or "(new)", new)
        console.print(table)
    else:
        console.print("[dim]No dependency changes needed.[/dim]")

    if tool_changes:
        console.print(f"\n[bold]Tool config refreshed:[/bold] {', '.join(tool_changes)}")

    if not dep_changes and not tool_changes:
        console.print("[green]Everything is up to date.[/green]")
        raise typer.Exit(0)

    if dry_run:
        raise typer.Exit(0)

    pyproject.setdefault("project", {})["optional-dependencies"] = optional_deps
    if refresh_tools:
        pyproject["tool"] = tool_config

    with open(pyproject_path, "wb") as f:
        tomli_w.dump(pyproject, f)

    console.print(
        f"\n[bold green]Upgraded {len(groups_to_upgrade)} group(s) "
        f"({len(dep_changes)} dep change(s))[/bold green]"
    )

    if install and dep_changes:
        console.print("\n[dim]Running pdm install...[/dim]")
        result = subprocess.run(
            ["pdm", "install", "-G", ":all"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print("[green]Dependencies installed.[/green]")
        else:
            console.print("[yellow]pdm install had issues:[/yellow]")
            if result.stderr:
                console.print(f"[dim]{result.stderr[:500]}[/dim]")
            console.print("[dim]Run `pdm install` manually to investigate.[/dim]")


def link_tool(
    tool_name: str = typer.Argument(help="Tool to configure (e.g. ruff, pyright, pytest)"),
    directory: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Project directory (default: cwd)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without writing",
    ),
) -> None:
    """Link/refresh tool configuration from group definitions.

    Reads the applied groups and re-applies their [tool.*] config sections
    to pyproject.toml. Useful after updating pjkm or group definitions to
    pick up new recommended settings.

    Examples:

      pjkm link ruff       # refresh [tool.ruff.*] config from groups
      pjkm link pytest     # refresh [tool.pytest.*] config
      pjkm link pyright    # refresh [tool.pyright] config
    """
    from pathlib import Path

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    import tomli_w
    from rich.console import Console

    from pjkm.core.groups.registry import GroupRegistry
    from pjkm.core.groups.resolver import GroupResolver
    from pjkm.core.models.platform import PlatformInfo

    console = Console()
    project_dir = Path(directory).resolve() if directory else Path.cwd()
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.exists():
        console.print(f"[red]pyproject.toml not found in {project_dir}[/red]")
        raise typer.Exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    applied_groups = pyproject.get("tool", {}).get("pjkm", {}).get("groups", [])
    if not applied_groups:
        console.print("[yellow]No groups in [tool.pjkm.groups].[/yellow]")
        raise typer.Exit(1)

    registry = GroupRegistry()
    registry.load_all()
    resolver = GroupResolver({g.id: g for g in registry.list_all()})
    platform = PlatformInfo()
    resolved = resolver.resolve(applied_groups, platform=platform)

    tool_config = pyproject.setdefault("tool", {})
    matched = []

    for grp in resolved:
        for tool_key, tool_conf in grp.pyproject_tool_config.items():
            if tool_key == tool_name or tool_key.startswith(f"{tool_name}."):
                parts = tool_key.split(".")
                current = tool_config
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = tool_conf
                matched.append(f"[tool.{tool_key}]")

    if not matched:
        console.print(
            f"[yellow]No groups define config for '{tool_name}'.[/yellow]"
        )
        console.print("[dim]Available tool configs from your groups:[/dim]")
        all_tools = set()
        for grp in resolved:
            for key in grp.pyproject_tool_config:
                all_tools.add(key.split(".")[0])
        if all_tools:
            console.print(f"  {', '.join(sorted(all_tools))}")
        raise typer.Exit(1)

    if dry_run:
        console.print(f"[bold]Would update:[/bold] {', '.join(matched)}")
        raise typer.Exit(0)

    with open(pyproject_path, "wb") as f:
        tomli_w.dump(pyproject, f)

    console.print(f"[green]Updated {', '.join(matched)} from group definitions.[/green]")


def preview(
    archetype: str = typer.Argument(
        "",
        help="Project archetype (optional when --recipe is given)",
    ),
    group: list[str] = typer.Option(
        [],
        "--group",
        "-g",
        help="Package groups to preview (repeatable)",
    ),
    recipe_name: str = typer.Option(
        "",
        "--recipe",
        "-r",
        help="Use a named recipe instead of specifying groups",
    ),
) -> None:
    """Preview what a project would look like without creating anything.

    Shows the full file tree, dependencies, tool config, and workflows
    that would be generated. Great for trying different combinations
    before committing to `pjkm init`.

    Examples:

      pjkm preview service -g api -g database -g docker
      pjkm preview --recipe python-lib
      pjkm preview --recipe fastapi-service
    """
    import tempfile
    from pathlib import Path

    from rich.console import Console
    from rich.panel import Panel
    from rich.tree import Tree

    from pjkm.core.defaults import UserDefaults
    from pjkm.core.engine.project_engine import ProjectEngine
    from pjkm.core.models.project import Archetype, ProjectConfig
    from pjkm.core.tasks.defaults import create_default_registry

    console = Console()

    # If recipe specified, pull groups from it
    if recipe_name:
        from pjkm.cli.commands.recipes import RECIPES

        if recipe_name not in RECIPES:
            console.print(
                f"[red]Unknown recipe: {recipe_name}. "
                f"Options: {', '.join(RECIPES.keys())}[/red]"
            )
            raise typer.Exit(1)
        r = RECIPES[recipe_name]
        archetype = r["archetype"]
        group = r["groups"]

    if not archetype and not recipe_name:
        console.print("[red]Provide an archetype or use --recipe.[/red]")
        console.print("[dim]Usage: pjkm preview <archetype> or pjkm preview --recipe <name>[/dim]")
        raise typer.Exit(1)

    archetype_normalized = archetype.replace("-", "_")

    try:
        arch = Archetype(archetype_normalized)
    except ValueError:
        console.print(f"[red]Unknown archetype: {archetype}[/red]")
        console.print(f"Valid options: {', '.join(a.value for a in Archetype)}")
        raise typer.Exit(1)

    user_defaults = UserDefaults.load()

    with tempfile.TemporaryDirectory(prefix="pjkm-preview-") as tmpdir:
        config = ProjectConfig(
            project_name="preview-project",
            archetype=arch,
            selected_groups=group,
            target_dir=Path(tmpdir),
            dry_run=False,
            author_name=user_defaults.author_name or "Preview User",
            author_email=user_defaults.author_email or "preview@example.com",
            python_version=user_defaults.python_version,
            license=user_defaults.license,
        )

        registry = create_default_registry()
        engine = ProjectEngine(task_registry=registry)
        github_extra = user_defaults.github.model_dump()
        result = engine.execute(config, extra={"github": github_extra})

        if not result.success:
            console.print("[red]Preview generation failed[/red]")
            for f in result.failed_tasks:
                console.print(f"  [red]{f.task_id}:[/red] {f.message}")
            raise typer.Exit(1)

        # Build file tree
        project_dir = config.project_dir
        title = f"Preview: {archetype}"
        if recipe_name:
            title += f" (recipe: {recipe_name})"
        if group:
            title += f" — {len(group)} groups"

        tree = Tree(f"[bold cyan]{title}[/bold cyan]")

        def _add_tree(parent_tree: Tree, directory: Path, prefix: str = "") -> int:
            count = 0
            items = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name))
            for item in items:
                if item.name.startswith(".git") and item.is_dir() and item.name == ".git":
                    continue
                if item.is_dir():
                    branch = parent_tree.add(f"[bold blue]{item.name}/[/bold blue]")
                    count += _add_tree(branch, item)
                else:
                    size = item.stat().st_size
                    if size > 1024:
                        size_str = f"{size / 1024:.1f}K"
                    else:
                        size_str = f"{size}B"
                    parent_tree.add(f"[green]{item.name}[/green] [dim]({size_str})[/dim]")
                    count += 1
            return count

        file_count = _add_tree(tree, project_dir)
        console.print(tree)
        console.print()

        # Show summary
        console.print(
            Panel(
                f"[bold]Archetype:[/bold] {arch.value}\n"
                f"[bold]Groups:[/bold] {', '.join(group) or '(none)'}\n"
                f"[bold]Files:[/bold] {file_count}",
                title="Preview Summary",
            )
        )

        # Show workflows found
        workflows_dir = project_dir / ".github" / "workflows"
        if workflows_dir.is_dir():
            wf_files = sorted(workflows_dir.glob("*.yml"))
            if wf_files:
                console.print()
                console.print("[bold]GitHub Actions workflows:[/bold]")
                for wf in wf_files:
                    console.print(f"  [cyan]{wf.name}[/cyan]")

        # Show pyproject groups
        pyproject_path = project_dir / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib  # type: ignore[no-redef]
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
            opt_deps = pyproject.get("project", {}).get("optional-dependencies", {})
            if opt_deps:
                total_deps = sum(len(v) for v in opt_deps.values())
                console.print()
                console.print(
                    f"[bold]Dependencies:[/bold] {total_deps} packages "
                    f"across {len(opt_deps)} sections"
                )
                for section, deps in sorted(opt_deps.items()):
                    console.print(f"  [cyan]{section}[/cyan] ({len(deps)}): {', '.join(deps[:5])}"
                                  + ("..." if len(deps) > 5 else ""))

    console.print()
    if recipe_name:
        console.print(
            f"[dim]To create: pjkm init my-project --recipe {recipe_name}[/dim]"
        )
    elif group:
        groups_str = " ".join(f"-g {g}" for g in group)
        console.print(
            f"[dim]To create: pjkm init my-project -a {archetype} {groups_str}[/dim]"
        )
