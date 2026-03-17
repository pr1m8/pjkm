"""pjkm CLI application — top-level Typer app."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="pjkm",
    help="Python project builder with DAG-based task system and Copier templates.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        from pjkm import __version__

        typer.echo(f"pjkm {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """pjkm — Python project builder."""


@app.command()
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


@app.command()
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

    # ------------------------------------------------------------------
    # 1. Find pyproject.toml
    # ------------------------------------------------------------------
    if not pyproject_path.exists():
        console.print(
            f"[red]pyproject.toml not found in {project_dir}[/red]"
        )
        raise typer.Exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    # ------------------------------------------------------------------
    # 2. Read existing optional-dependencies and [tool.pjkm.groups]
    # ------------------------------------------------------------------
    pjkm_config = pyproject.get("tool", {}).get("pjkm", {})
    already_applied: list[str] = pjkm_config.get("groups", [])

    # ------------------------------------------------------------------
    # 3. Load registry and validate requested group IDs
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 4. Resolve transitively, filter out already-applied groups
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 5. Merge new group deps into pyproject.toml
    # ------------------------------------------------------------------
    optional_deps = pyproject.setdefault("project", {}).setdefault(
        "optional-dependencies", {}
    )
    tool_config = pyproject.setdefault("tool", {})

    def _deep_merge(target: dict, dotted_key: str, value: dict) -> None:
        parts = dotted_key.split(".")
        current = target
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current.setdefault(parts[-1], {}).update(value)

    for g in new_groups:
        for group_name, deps in g.dependencies.items():
            existing = optional_deps.get(group_name, [])
            merged = list(dict.fromkeys(existing + deps))
            optional_deps[group_name] = merged

        for tool_name, tool_conf in g.pyproject_tool_config.items():
            _deep_merge(tool_config, tool_name, tool_conf)

    # ------------------------------------------------------------------
    # 6. Render scaffolded files for new groups
    # ------------------------------------------------------------------
    loader = TemplateLoader()
    renderer = TemplateRenderer()

    # Derive project_slug from pyproject metadata
    project_name = pyproject.get("project", {}).get("name", project_dir.name)
    project_slug = re.sub(r"[^a-zA-Z0-9]", "_", project_name).lower().strip("_")
    python_version = "3.13"  # fallback
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
                pass  # Fragment not yet created — skip silently

    # ------------------------------------------------------------------
    # 7. Update [tool.pjkm.groups] with full set of applied group IDs
    # ------------------------------------------------------------------
    pjkm_tool = pyproject.setdefault("tool", {}).setdefault("pjkm", {})
    pjkm_tool["groups"] = sorted(set(already_applied + [g.id for g in new_groups]))

    # ------------------------------------------------------------------
    # 8. Write back pyproject.toml
    # ------------------------------------------------------------------
    with open(pyproject_path, "wb") as f:
        tomli_w.dump(pyproject, f)

    # ------------------------------------------------------------------
    # 9. Print summary
    # ------------------------------------------------------------------
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


@app.command()
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

    # Resolve target directory
    project_dir = Path(directory).resolve() if directory else Path.cwd()

    # Check for pyproject.toml
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        console.print(f"[red]No pyproject.toml found in {project_dir}[/red]")
        console.print(
            "[dim]Run this command from a pjkm-generated project directory, "
            "or use --dir to specify one.[/dim]"
        )
        raise typer.Exit(1)

    # Read [tool.pjkm] metadata
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

    # Gather template data from pyproject.toml
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

    # Check for .copier-answers.yml
    copier_answers = project_dir / ".copier-answers.yml"
    use_copier_update = copier_answers.exists()

    renderer = TemplateRenderer()
    loader = TemplateLoader()
    applied: list[str] = []

    if use_copier_update:
        # Use Copier's native update which reads .copier-answers.yml
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
        # Fallback: re-render base + archetype with overwrite=True
        console.print("[dim]Re-rendering templates with overwrite.[/dim]")

        # 1. Base template
        base_path = loader.resolve("base")
        renderer.render(
            template_path=base_path,
            dest=project_dir,
            data=data,
            overwrite=True,
            pretend=False,
        )
        applied.append("base")

        # 2. Archetype template (if known)
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

    # Print summary
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


@app.command()
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

    # Read [tool.pjkm] metadata
    pjkm_config = pyproject.get("tool", {}).get("pjkm", {})
    applied_groups: list[str] = pjkm_config.get("groups", [])

    if not applied_groups:
        console.print("[yellow]No groups found in [tool.pjkm.groups].[/yellow]")
        console.print("[dim]Use `pjkm add` to add groups first.[/dim]")
        raise typer.Exit(1)

    # Determine which groups to upgrade
    target_groups = group if group else applied_groups

    # Load registry
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

    # Resolve groups
    resolver = GroupResolver({g.id: g for g in registry.list_all()})
    platform = PlatformInfo()
    try:
        resolved = resolver.resolve(target_groups, platform=platform)
    except Exception as exc:
        console.print(f"[red]Group resolution failed: {exc}[/red]")
        raise typer.Exit(1)

    # Filter to only the target groups (not transitive deps unless requested)
    target_set = set(target_groups)
    groups_to_upgrade = [g for g in resolved if g.id in target_set]

    # Track changes for summary
    dep_changes: list[tuple[str, str, str, str]] = []  # (section, pkg, old, new)
    tool_changes: list[str] = []

    optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
    tool_config = pyproject.get("tool", {})

    for grp in groups_to_upgrade:
        for section, new_deps in grp.dependencies.items():
            existing = optional_deps.get(section, [])
            existing_map: dict[str, str] = {}
            for dep in existing:
                # Parse "package>=1.0.0" into (package, >=1.0.0)
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
                    # Strip version pin
                    final_dep = m_new.group(1)
                else:
                    final_dep = new_dep

                old_dep = existing_map.get(pkg_name, "")
                if old_dep != final_dep:
                    dep_changes.append((section, pkg_name, old_dep, final_dep))

                updated.append(final_dep)
                # Remove from existing_map so we keep non-group deps
                existing_map.pop(pkg_name, None)

            # Keep deps that aren't from this group
            remaining = [
                dep for dep in existing
                if re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)", dep)
                and re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)", dep).group(1).lower()
                in existing_map
            ]
            optional_deps[section] = updated + remaining

        # Re-apply tool config if requested
        if refresh_tools and grp.pyproject_tool_config:
            for tool_name, tool_conf in grp.pyproject_tool_config.items():
                parts = tool_name.split(".")
                current = tool_config
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = tool_conf
                tool_changes.append(f"[tool.{tool_name}]")

    # Show summary
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

    # Write changes
    pyproject.setdefault("project", {})["optional-dependencies"] = optional_deps
    if refresh_tools:
        pyproject["tool"] = tool_config

    with open(pyproject_path, "wb") as f:
        tomli_w.dump(pyproject, f)

    console.print(
        f"\n[bold green]Upgraded {len(groups_to_upgrade)} group(s) "
        f"({len(dep_changes)} dep change(s))[/bold green]"
    )

    # Run pdm install if requested
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


@app.command(name="link")
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
            # Match if the tool_key starts with the requested tool name
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


@app.command()
def tui() -> None:
    """Launch the interactive TUI wizard."""
    from pjkm.tui.app import run as run_tui

    run_tui()


@app.command(name="list")
def list_cmd(
    what: str = typer.Argument(
        "archetypes",
        help="What to list: archetypes, groups",
    ),
) -> None:
    """List available archetypes or package groups."""
    from rich.console import Console
    from rich.table import Table

    from pjkm.core.groups.registry import GroupRegistry

    console = Console()

    if what == "archetypes":
        table = Table(title="Available Archetypes")
        table.add_column("ID", style="cyan")
        table.add_column("Description")
        table.add_row("single_package", "Standalone Python package with src layout")
        table.add_row("service", "Service repo with infra, Docker Compose, Makefile")
        table.add_row(
            "poly_repo", "Multi-package repo with submodules and shared infra"
        )
        table.add_row("script_tool", "Lightweight CLI tool or script")
        console.print(table)
    elif what == "groups":
        registry = GroupRegistry()
        registry.load_all()
        groups = sorted(registry.list_all(), key=lambda g: g.id)
        if not groups:
            console.print("[dim]No package groups defined yet.[/dim]")
            return
        table = Table(title="Available Package Groups")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Requires", style="dim")
        table.add_column("Archetypes", style="dim")
        table.add_column("Scaffold", style="green")
        for g in groups:
            reqs = ", ".join(g.requires_groups) if g.requires_groups else ""
            archs = ", ".join(g.archetypes) if g.archetypes else "all"
            frags = ", ".join(sf.template_fragment for sf in g.scaffolded_files) or ""
            table.add_row(g.id, g.name, reqs, archs, frags)
        console.print(table)
    else:
        console.print(f"[red]Unknown: {what}. Use 'archetypes' or 'groups'.[/red]")


@app.command()
def info(
    group_id: str = typer.Argument(help="Group ID to show details for"),
) -> None:
    """Show detailed information about a package group."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from pjkm.core.groups.registry import GroupRegistry

    console = Console()
    registry = GroupRegistry()
    registry.load_all()

    group = registry.get(group_id)
    if group is None:
        console.print(f"[red]Unknown group: {group_id}[/red]")
        console.print(f"Available: {', '.join(sorted(registry.group_ids))}")
        raise typer.Exit(1)

    console.print(
        Panel(f"[bold]{group.name}[/bold]\n{group.description}", title=group.id)
    )
    console.print()

    if group.archetypes:
        console.print(f"[dim]Archetypes:[/dim] {', '.join(group.archetypes)}")
    else:
        console.print("[dim]Archetypes:[/dim] all")

    if group.requires_groups:
        console.print(f"[dim]Requires:[/dim]   {', '.join(group.requires_groups)}")

    if group.platform_filter:
        console.print(f"[dim]Platform:[/dim]   {group.platform_filter}")

    console.print()

    if group.dependencies:
        table = Table(title="Dependencies", show_header=True)
        table.add_column("Section", style="cyan")
        table.add_column("Packages")
        for section, deps in group.dependencies.items():
            table.add_row(section, "\n".join(deps))
        console.print(table)
        console.print()

    if group.scaffolded_files:
        table = Table(title="Scaffolded Files", show_header=True)
        table.add_column("Fragment", style="green")
        table.add_column("Destination")
        table.add_column("Description", style="dim")
        for sf in group.scaffolded_files:
            table.add_row(sf.template_fragment, sf.destination, sf.description)
        console.print(table)
        console.print()

    if group.pyproject_tool_config:
        console.print("[bold]pyproject.toml tool config:[/bold]")
        for tool, conf in group.pyproject_tool_config.items():
            console.print(f"  [cyan][tool.{tool}][/cyan]")
            for k, v in conf.items():
                console.print(f"    {k} = {v!r}")


group_app = typer.Typer(help="Manage package groups.")
app.add_typer(group_app, name="group")


@group_app.command(name="create")
def group_create(
    group_id: str = typer.Argument(help="Group ID (e.g. quant, ml-data)"),
    name: str = typer.Option("", "--name", "-n", help="Human-readable name"),
    output_dir: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Output directory (default: ./.pjkm/groups/)",
    ),
) -> None:
    """Scaffold a new package group YAML definition.

    Creates a ready-to-edit YAML file. Add dependencies, set archetypes,
    and optionally reference template fragments.

    Custom groups in ~/.pjkm/groups/ or ./.pjkm/groups/ are loaded
    automatically alongside built-in groups.
    """
    from pathlib import Path

    from rich.console import Console

    console = Console()

    gid = group_id.replace("-", "_")
    display_name = name or gid.replace("_", " ").title()

    if output_dir:
        out = Path(output_dir)
    else:
        out = Path.cwd() / ".pjkm" / "groups"

    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{gid}.yaml"

    if target.exists():
        console.print(f"[yellow]Group file already exists: {target}[/yellow]")
        raise typer.Exit(1)

    template = f"""\
id: {gid}
name: "{display_name}"
description: ""
archetypes: []              # empty = all archetypes
requires_groups: []         # e.g. [logging, database]
platform_filter: null       # null = all platforms, or "darwin", "linux", "win32"

dependencies:
  {gid}:
    # Add your dependencies here:
    # - "package>=1.0.0"

scaffolded_files: []
  # Uncomment to scaffold code when this group is selected:
  # - template_fragment: "{gid}_setup"
  #   destination: "src/{{{{ project_slug }}}}/{gid}/"
  #   description: "Initial {display_name} configuration"

pyproject_tool_config: {{}}
"""
    target.write_text(template)
    console.print(f"[green]Created {target}[/green]")
    console.print("[dim]Edit this file to add dependencies and configuration.[/dim]")
    console.print()
    console.print("[dim]Custom groups are loaded automatically from:[/dim]")
    console.print("[dim]  ~/.pjkm/groups/*.yaml   (global)[/dim]")
    console.print("[dim]  ./.pjkm/groups/*.yaml   (project-local)[/dim]")


@group_app.command(name="import")
def group_import(
    pyproject: str = typer.Argument(help="Path to pyproject.toml to import from"),
    section: list[str] = typer.Option(
        [],
        "--section",
        "-s",
        help="Specific sections to import (default: all)",
    ),
    output_dir: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Output directory (default: ./.pjkm/groups/)",
    ),
) -> None:
    """Import optional dependency groups from an external pyproject.toml.

    Reads [project.optional-dependencies] and creates a .yaml group file
    for each section. Great for importing groups from existing projects.

    Example: pjkm group import ../ooai/packages/wraquant/pyproject.toml
    """
    from pathlib import Path

    from rich.console import Console

    from pjkm.core.groups.registry import GroupRegistry

    console = Console()
    pyproject_path = Path(pyproject).resolve()

    if not pyproject_path.exists():
        console.print(f"[red]File not found: {pyproject_path}[/red]")
        raise typer.Exit(1)

    if output_dir:
        out = Path(output_dir).resolve()
    else:
        out = Path.cwd() / ".pjkm" / "groups"

    created = GroupRegistry.import_from_pyproject(
        pyproject_path,
        out,
        sections=section or None,
    )

    if not created:
        console.print("[yellow]No optional-dependencies found to import.[/yellow]")
        raise typer.Exit(1)

    console.print(f"[green]Imported {len(created)} group(s) to {out}/[/green]")
    for path in created:
        console.print(f"  [cyan]{path.name}[/cyan]")

    console.print()
    console.print(
        "[dim]Edit the generated files to customize names and descriptions.[/dim]"
    )
    console.print("[dim]Use `pjkm group validate` to check your definitions.[/dim]")


@group_app.command(name="validate")
def group_validate(
    path: str = typer.Argument(
        "",
        help="Path to a .yaml file or directory (default: ./.pjkm/groups/)",
    ),
) -> None:
    """Validate package group YAML definitions.

    Checks that group files parse correctly, have valid schema,
    and that dependency references are resolvable.
    """
    from pathlib import Path

    from rich.console import Console

    from pjkm.core.groups.registry import GroupRegistry
    from pjkm.core.models.group import PackageGroup

    console = Console()

    if path:
        target = Path(path).resolve()
    else:
        target = Path.cwd() / ".pjkm" / "groups"

    if not target.exists():
        console.print(f"[red]Path not found: {target}[/red]")
        raise typer.Exit(1)

    files = [target] if target.is_file() else sorted(target.glob("*.yaml"))
    if not files:
        console.print(f"[yellow]No .yaml files found in {target}[/yellow]")
        raise typer.Exit(1)

    # Load built-in groups for cross-reference validation
    registry = GroupRegistry()
    registry.load_builtin()
    builtin_ids = set(registry.group_ids)

    errors = 0
    for f in files:
        try:
            import yaml

            with open(f) as fh:
                data = yaml.safe_load(fh)
            group = PackageGroup.model_validate(data)

            # Check requires_groups references
            bad_refs = [
                r
                for r in group.requires_groups
                if r not in builtin_ids and r != group.id
            ]
            if bad_refs:
                console.print(
                    f"  [yellow]Warning:[/yellow] {f.name} requires unknown groups: {', '.join(bad_refs)}"
                )

            console.print(f"  [green]OK:[/green] {f.name} — {group.id} ({group.name})")
        except Exception as e:
            console.print(f"  [red]Error:[/red] {f.name} — {e}")
            errors += 1

    console.print()
    if errors:
        console.print(f"[bold red]{errors} file(s) have errors.[/bold red]")
        raise typer.Exit(1)
    else:
        console.print(f"[bold green]All {len(files)} group file(s) valid.[/bold green]")


@group_app.command(name="list")
def group_list() -> None:
    """List all available groups (built-in + custom + remote sources)."""
    from rich.console import Console
    from rich.table import Table

    from pjkm.core.groups.registry import GroupRegistry

    console = Console()
    registry = GroupRegistry()
    registry.load_all()

    groups = sorted(registry.list_all(), key=lambda g: g.id)
    if not groups:
        console.print("[dim]No package groups found.[/dim]")
        return

    table = Table(title="All Package Groups (built-in + custom + sources)")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Deps", style="dim", justify="right")
    table.add_column("Requires", style="dim")
    table.add_column("Archetypes", style="dim")
    for g in groups:
        dep_count = sum(len(deps) for deps in g.dependencies.values())
        reqs = ", ".join(g.requires_groups) if g.requires_groups else ""
        archs = ", ".join(g.archetypes) if g.archetypes else "all"
        table.add_row(g.id, g.name, str(dep_count), reqs, archs)
    console.print(table)


source_app = typer.Typer(help="Manage remote group sources (git repos).")
group_app.add_typer(source_app, name="source")


@source_app.command(name="add")
def source_add(
    url: str = typer.Argument(help="Git repo URL containing group YAML files"),
    name: str = typer.Option("", "--name", "-n", help="Short name for this source"),
    path: str = typer.Option(
        "", "--path", "-p", help="Subdirectory within repo containing .yaml files"
    ),
    ref: str = typer.Option("", "--ref", "-r", help="Branch, tag, or commit to track"),
    sync_now: bool = typer.Option(
        True, "--sync/--no-sync", help="Clone the repo immediately"
    ),
) -> None:
    r"""Add a remote git repo as a group source.

    The repo should contain .yaml group definition files (same format as
    built-in groups). After adding, groups from this source are available
    everywhere — in `pjkm init`, `pjkm group list`, etc.

    Examples:

      pjkm group source add https://github.com/org/pjkm-groups-quant.git

      pjkm group source add git@github.com:org/ooai.git \\
        --path packages/wraquant/groups --name quant

      pjkm group source add https://github.com/team/shared-groups.git \\
        --ref main --name team-groups
    """
    from rich.console import Console

    from pjkm.core.groups.sources import GroupSourceManager

    console = Console()

    mgr = GroupSourceManager()
    mgr.load()
    entry = mgr.add(url=url, name=name, path=path, ref=ref)
    console.print(f"[green]Added source:[/green] {entry.name}")
    console.print(f"  [dim]URL:[/dim]  {entry.url}")
    if entry.path:
        console.print(f"  [dim]Path:[/dim] {entry.path}")
    if entry.ref:
        console.print(f"  [dim]Ref:[/dim]  {entry.ref}")

    if sync_now:
        console.print()
        results = mgr.sync(entry.name)
        for src, ok, msg in results:
            if ok:
                console.print(f"  [green]Synced:[/green] {src.name} ({msg})")
                # Show what was found
                yaml_count = len(list(src.groups_dir.glob("*.yaml")))
                if yaml_count:
                    console.print(
                        f"  [dim]Found {yaml_count} group definition(s)[/dim]"
                    )
                else:
                    console.print(
                        f"  [yellow]No .yaml files found in {src.groups_dir}[/yellow]"
                    )
                    if not path:
                        console.print(
                            "  [dim]Hint: use --path to specify the subdirectory with group files[/dim]"
                        )
            else:
                console.print(f"  [red]Failed:[/red] {src.name} — {msg}")


@source_app.command(name="remove")
def source_remove(
    name: str = typer.Argument(help="Source name to remove"),
) -> None:
    """Remove a registered group source and its cached data."""
    from rich.console import Console

    from pjkm.core.groups.sources import GroupSourceManager

    console = Console()
    mgr = GroupSourceManager()
    mgr.load()

    if mgr.remove(name):
        console.print(f"[green]Removed source: {name}[/green]")
    else:
        console.print(f"[red]Source not found: {name}[/red]")
        if mgr.sources:
            console.print(f"Available: {', '.join(s.name for s in mgr.sources)}")
        raise typer.Exit(1)


@source_app.command(name="list")
def source_list() -> None:
    """List all registered group sources."""
    from rich.console import Console
    from rich.table import Table

    from pjkm.core.groups.sources import GroupSourceManager

    console = Console()
    mgr = GroupSourceManager()
    mgr.load()

    # Also show sources from .pjkmrc.yaml
    try:
        from pjkm.core.defaults import UserDefaults

        defaults = UserDefaults.load()
        if defaults.group_sources:
            mgr.load_from_defaults([s.model_dump() for s in defaults.group_sources])
    except Exception:
        pass

    if not mgr.sources:
        console.print("[dim]No group sources registered.[/dim]")
        console.print("[dim]Add one with: pjkm group source add <git-url>[/dim]")
        return

    table = Table(title="Registered Group Sources")
    table.add_column("Name", style="cyan")
    table.add_column("URL")
    table.add_column("Path", style="dim")
    table.add_column("Ref", style="dim")
    table.add_column("Cached", style="green")
    table.add_column("Groups", style="dim", justify="right")

    for s in mgr.sources:
        cached = "yes" if s.cache_dir.exists() else "no"
        yaml_count = (
            len(list(s.groups_dir.glob("*.yaml"))) if s.groups_dir.is_dir() else 0
        )
        table.add_row(
            s.name,
            s.url,
            s.path or "",
            s.ref or "(HEAD)",
            cached,
            str(yaml_count) if yaml_count else "-",
        )
    console.print(table)


@group_app.command(name="sync")
def group_sync(
    name: str = typer.Argument("", help="Source name to sync (default: all)"),
) -> None:
    """Sync (clone or update) remote group sources.

    Pulls the latest group definitions from registered git repos.
    Run this after adding a source or to get updates.
    """
    from rich.console import Console

    from pjkm.core.groups.sources import GroupSourceManager

    console = Console()
    mgr = GroupSourceManager()
    mgr.load()

    # Also include sources from .pjkmrc.yaml
    try:
        from pjkm.core.defaults import UserDefaults

        defaults = UserDefaults.load()
        if defaults.group_sources:
            mgr.load_from_defaults([s.model_dump() for s in defaults.group_sources])
    except Exception:
        pass

    if not mgr.sources:
        console.print(
            "[dim]No sources to sync. Add one with: pjkm group source add <git-url>[/dim]"
        )
        return

    results = mgr.sync(name=name or None)
    for src, ok, msg in results:
        if ok:
            yaml_count = (
                len(list(src.groups_dir.glob("*.yaml")))
                if src.groups_dir.is_dir()
                else 0
            )
            console.print(
                f"  [green]OK:[/green] {src.name} — {msg} ({yaml_count} groups)"
            )
        else:
            console.print(f"  [red]Failed:[/red] {src.name} — {msg}")


FIX_HINTS: dict[str, str] = {
    "git": "brew install git (macOS) / apt install git (Linux)",
    "python": "brew install python@3.13 / pyenv install 3.13",
    "pdm": "pipx install pdm / brew install pdm",
    "docker": "https://docs.docker.com/get-docker/",
    "node": "https://nodejs.org/ or brew install node@22",
    "pnpm": "corepack enable && corepack prepare pnpm@latest",
    "gh": "brew install gh / https://cli.github.com/",
    "git-lfs": "brew install git-lfs / apt install git-lfs",
    "pre-commit": "pipx install pre-commit",
    "trunk": "curl https://get.trunk.io -fsSL | bash",
}


@app.command()
def doctor() -> None:
    """Check the local environment for required and optional tools."""
    import re
    import shutil
    import subprocess

    from rich.console import Console

    console = Console()
    console.print("[bold]pjkm doctor[/bold] — checking your environment\n")

    required_tools: list[tuple[str, list[str]]] = [
        ("git", ["git", "--version"]),
        ("python", ["python3", "--version"]),
        ("pdm", ["pdm", "--version"]),
    ]
    optional_tools: list[tuple[str, list[str]]] = [
        ("pre-commit", ["pre-commit", "--version"]),
        ("trunk", ["trunk", "--version"]),
        ("docker", ["docker", "--version"]),
        ("node", ["node", "--version"]),
        ("pnpm", ["pnpm", "--version"]),
        ("gh", ["gh", "--version"]),
        ("git-lfs", ["git-lfs", "--version"]),
    ]

    required_found = 0
    required_total = len(required_tools)
    optional_found = 0
    optional_total = len(optional_tools)

    def _get_version(cmd: list[str]) -> str | None:
        """Run a version command and return trimmed output, or None."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10,
            )
            return (result.stdout.strip() or result.stderr.strip()) or None
        except Exception:
            return None

    def _print_hint(name: str) -> None:
        hint = FIX_HINTS.get(name)
        if hint:
            console.print(f"         [dim]fix: {hint}[/dim]")

    # --- Required tools ---
    console.print("[bold underline]Required[/bold underline]")
    for name, version_cmd in required_tools:
        if shutil.which(version_cmd[0]) is None:
            console.print(f"  [red]\u2718[/red] {name} — not found")
            _print_hint(name)
            continue
        version = _get_version(version_cmd)
        if version:
            console.print(f"  [green]\u2714[/green] {name} — {version}")
            required_found += 1
            # Python version check: warn if < 3.13
            if name == "python":
                m = re.search(r"(\d+)\.(\d+)", version)
                if m:
                    major, minor = int(m.group(1)), int(m.group(2))
                    if (major, minor) < (3, 13):
                        console.print(
                            f"         [yellow]\u26a0 Python {major}.{minor} detected; "
                            "3.13+ is recommended[/yellow]"
                        )
        else:
            console.print(
                f"  [red]\u2718[/red] {name} — found but could not get version"
            )
            _print_hint(name)

    # --- Optional tools ---
    console.print()
    console.print("[bold underline]Optional[/bold underline]")
    for name, version_cmd in optional_tools:
        if shutil.which(version_cmd[0]) is None:
            console.print(f"  [yellow]![/yellow] {name} — not installed")
            _print_hint(name)
            continue
        version = _get_version(version_cmd)
        if version:
            console.print(f"  [green]\u2714[/green] {name} — {version}")
            optional_found += 1
        else:
            console.print(
                f"  [yellow]![/yellow] {name} — found but could not get version"
            )

    # --- Summary ---
    console.print()
    req_color = "green" if required_found == required_total else "red"
    opt_color = "green" if optional_found == optional_total else "yellow"
    console.print(
        f"[{req_color}]{required_found}/{required_total} required[/{req_color}], "
        f"[{opt_color}]{optional_found}/{optional_total} optional[/{opt_color}]"
    )
    console.print()

    if required_found < required_total:
        console.print(
            "[bold red]Some required tools are missing. "
            "Install them before using pjkm.[/bold red]"
        )
        raise typer.Exit(1)
    else:
        console.print(
            "[bold green]All required tools found. You're good to go![/bold green]"
        )


@app.command()
def defaults(
    init_config: bool = typer.Option(
        False,
        "--init",
        help="Create a .pjkmrc.yaml template in the current directory",
    ),
    show_global: bool = typer.Option(
        False,
        "--global",
        help="Show the global config file path (~/.pjkmrc.yaml)",
    ),
) -> None:
    """Show or create user default configuration.

    Defaults are loaded from ~/.pjkmrc.yaml (global) and ./.pjkmrc.yaml (local).
    Local overrides global. CLI flags override both.
    """
    from pathlib import Path

    from rich.console import Console
    from rich.panel import Panel

    from pjkm.core.defaults import UserDefaults

    console = Console()

    if init_config:
        target = Path.cwd() / ".pjkmrc.yaml"
        if target.exists():
            console.print(f"[yellow]{target} already exists.[/yellow]")
            raise typer.Exit(1)

        template = """\
# pjkm defaults — loaded automatically by `pjkm init`
# See: pjkm defaults --help

author_name: ""
author_email: ""
license: MIT
python_version: "3.13"
archetype: single_package
groups:
  - dev
target_dir: "."

# GitHub / git remote settings
github:
  org: ""                  # GitHub org or user (e.g. "mycompany")
  visibility: private      # private, public, or internal
  remote: ""               # Remote host (default: github.com)
  create_repo: false       # Auto-create repo via `gh` CLI
  default_branch: main

# Remote group sources — git repos containing group YAML definitions
# These are synced with `pjkm group sync` and available everywhere.
# group_sources:
#   - url: https://github.com/org/pjkm-groups-quant.git
#     name: quant                # short name (auto-derived if omitted)
#     path: ""                   # subdirectory with .yaml files
#     ref: ""                    # branch/tag (default: HEAD)
"""
        target.write_text(template)
        console.print(f"[green]Created {target}[/green]")
        console.print("[dim]Edit this file to set your defaults.[/dim]")
        return

    if show_global:
        global_path = Path.home() / ".pjkmrc.yaml"
        if global_path.exists():
            console.print(f"[dim]Global config:[/dim] {global_path}")
            console.print(global_path.read_text())
        else:
            console.print(f"[dim]No global config at {global_path}[/dim]")
            console.print(
                "[dim]Run: pjkm defaults --init  (in ~/ to create global)[/dim]"
            )
        return

    # Show resolved defaults
    user_defaults = UserDefaults.load()

    console.print(
        Panel(
            "[bold]Resolved Defaults[/bold]\n"
            "Merged from ~/.pjkmrc.yaml + ./.pjkmrc.yaml",
            title="pjkm defaults",
        )
    )
    console.print()
    console.print(
        f"  [cyan]author_name:[/cyan]    {user_defaults.author_name or '(not set)'}"
    )
    console.print(
        f"  [cyan]author_email:[/cyan]   {user_defaults.author_email or '(not set)'}"
    )
    console.print(f"  [cyan]license:[/cyan]         {user_defaults.license}")
    console.print(f"  [cyan]python_version:[/cyan]  {user_defaults.python_version}")
    console.print(f"  [cyan]archetype:[/cyan]       {user_defaults.archetype}")
    console.print(
        f"  [cyan]groups:[/cyan]          {', '.join(user_defaults.groups) or '(none)'}"
    )
    console.print(f"  [cyan]target_dir:[/cyan]      {user_defaults.target_dir}")

    gh = user_defaults.github
    console.print()
    console.print("  [bold]GitHub[/bold]")
    console.print(f"  [cyan]org:[/cyan]             {gh.org or '(not set)'}")
    console.print(f"  [cyan]visibility:[/cyan]      {gh.visibility}")
    console.print(
        f"  [cyan]remote:[/cyan]          {gh.remote or '(default: github.com)'}"
    )
    console.print(f"  [cyan]create_repo:[/cyan]     {gh.create_repo}")
    console.print(f"  [cyan]default_branch:[/cyan]  {gh.default_branch}")

    if user_defaults.group_sources:
        console.print()
        console.print("  [bold]Group Sources[/bold]")
        for src in user_defaults.group_sources:
            label = src.name or src.url
            console.print(f"  [cyan]{label}:[/cyan] {src.url}")
            if src.path:
                console.print(f"    [dim]path: {src.path}[/dim]")

    # Show which files were found
    console.print()
    global_path = Path.home() / ".pjkmrc.yaml"
    local_path = Path.cwd() / ".pjkmrc.yaml"
    console.print(
        f"  [dim]~/.pjkmrc.yaml:[/dim]  {'found' if global_path.is_file() else 'not found'}"
    )
    console.print(
        f"  [dim]./.pjkmrc.yaml:[/dim]  {'found' if local_path.is_file() else 'not found'}"
    )
