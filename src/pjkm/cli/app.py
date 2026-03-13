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


@app.command()
def doctor() -> None:
    """Check the local environment for required and optional tools."""
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
    ]

    missing_required = False

    console.print("[bold underline]Required[/bold underline]")
    for name, version_cmd in required_tools:
        if shutil.which(version_cmd[0]) is None:
            console.print(f"  [red]\u2718[/red] {name} — not found")
            missing_required = True
            continue
        try:
            result = subprocess.run(
                version_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            version = result.stdout.strip() or result.stderr.strip()
            console.print(f"  [green]\u2714[/green] {name} — {version}")
        except Exception:
            console.print(
                f"  [red]\u2718[/red] {name} — found but could not get version"
            )
            missing_required = True

    console.print()
    console.print("[bold underline]Optional[/bold underline]")
    for name, version_cmd in optional_tools:
        if shutil.which(version_cmd[0]) is None:
            console.print(f"  [yellow]![/yellow] {name} — not installed")
            continue
        try:
            result = subprocess.run(
                version_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            version = result.stdout.strip() or result.stderr.strip()
            console.print(f"  [green]\u2714[/green] {name} — {version}")
        except Exception:
            console.print(
                f"  [yellow]![/yellow] {name} — found but could not get version"
            )

    console.print()
    if missing_required:
        console.print(
            "[bold red]Some required tools are missing. Install them before using pjkm.[/bold red]"
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
