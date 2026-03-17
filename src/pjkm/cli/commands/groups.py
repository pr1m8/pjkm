"""Group management commands — group create/import/validate/list/sync + source."""

from __future__ import annotations

import typer

group_app = typer.Typer(help="Manage package groups.")
source_app = typer.Typer(help="Manage remote group sources (git repos).")
group_app.add_typer(source_app, name="source")


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
category: "Core Dev"        # Core Dev, AI / ML, Web & API, Data & Storage, Infrastructure, Frontend, Docs & Meta, Platform
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

    files = [target] if target.is_file() else sorted(target.rglob("*.yaml"))
    if not files:
        console.print(f"[yellow]No .yaml files found in {target}[/yellow]")
        raise typer.Exit(1)

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


# --- Source subcommands ---


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

      pjkm group source add git@github.com:org/ooai.git \
        --path packages/wraquant/groups --name quant

      pjkm group source add https://github.com/team/shared-groups.git \
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
