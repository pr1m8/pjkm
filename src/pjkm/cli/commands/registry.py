"""Registry commands — search, install, browse community group packs."""

from __future__ import annotations

import typer


def search(
    query: str = typer.Argument("", help="Search term (name, tag, group, or description)"),
    refresh: bool = typer.Option(False, "--refresh", help="Force refresh the registry index"),
) -> None:
    """Search the pjkm registry for community group packs.

    Group packs are installable collections of groups + template fragments
    published as git repos. They extend pjkm with new scaffolding for
    frameworks, platforms, and domains.

    Examples:

      pjkm search django
      pjkm search ml
      pjkm search auth
      pjkm search            # list all packs
    """
    from rich.console import Console
    from rich.table import Table

    from pjkm.core.registry.index import RegistryIndex

    console = Console()
    registry = RegistryIndex()

    try:
        registry.load(force_refresh=refresh)
    except Exception as exc:
        console.print(f"[yellow]Could not fetch registry: {exc}[/yellow]")
        console.print("[dim]Showing cached/built-in packs.[/dim]")

    results = registry.search(query)

    if not results:
        console.print(f"[dim]No packs matching '{query}'.[/dim]")
        return

    table = Table(title=f"Registry Packs ({len(results)} results)")
    table.add_column("Name", style="cyan bold")
    table.add_column("Description")
    table.add_column("Groups", style="dim")
    table.add_column("Tags", style="green")

    for pack in results:
        table.add_row(
            pack.name,
            pack.description,
            ", ".join(pack.groups[:4]) + ("..." if len(pack.groups) > 4 else ""),
            ", ".join(pack.tags[:4]),
        )
    console.print(table)
    console.print()
    console.print("[dim]Install: pjkm install <pack-name>[/dim]")


def install(
    name: str = typer.Argument(help="Pack name to install (e.g. pjkm-django)"),
    no_sync: bool = typer.Option(False, "--no-sync", help="Add without cloning"),
) -> None:
    """Install a group pack from the registry.

    Downloads the pack's git repo and registers it as a group source.
    After install, the pack's groups are available in `pjkm init`,
    `pjkm add`, `pjkm list groups`, etc.

    Examples:

      pjkm install pjkm-django
      pjkm install pjkm-ml-ops
      pjkm install pjkm-quant
    """
    from rich.console import Console

    from pjkm.core.groups.sources import GroupSourceManager
    from pjkm.core.registry.index import RegistryIndex

    console = Console()
    registry = RegistryIndex()

    try:
        registry.load()
    except Exception:
        pass

    pack = registry.get(name)
    if pack is None:
        # Try fuzzy match
        candidates = registry.search(name)
        if candidates:
            console.print(f"[yellow]Pack '{name}' not found. Did you mean:[/yellow]")
            for c in candidates[:5]:
                console.print(f"  [cyan]{c.name}[/cyan] — {c.description}")
        else:
            console.print(f"[red]Pack '{name}' not found in registry.[/red]")
            console.print("[dim]Use `pjkm search` to browse available packs.[/dim]")
        raise typer.Exit(1)

    console.print(f"[bold]Installing {pack.name}...[/bold]")
    console.print(f"  [dim]{pack.description}[/dim]")
    console.print(f"  [dim]URL: {pack.url}[/dim]")
    if pack.groups:
        console.print(f"  [dim]Groups: {', '.join(pack.groups)}[/dim]")
    console.print()

    # Register as a group source
    mgr = GroupSourceManager()
    mgr.load()

    # Check if already installed
    existing = [s for s in mgr.sources if s.url == pack.url]
    if existing:
        console.print(f"[yellow]Already installed as '{existing[0].name}'.[/yellow]")
        console.print("[dim]Use `pjkm group source remove` to reinstall.[/dim]")
        raise typer.Exit(0)

    entry = mgr.add(
        url=pack.url,
        name=pack.name,
        path=pack.path,
        ref=pack.ref,
    )
    console.print(f"[green]Added source:[/green] {entry.name}")

    if not no_sync:
        console.print("[dim]Syncing...[/dim]")
        results = mgr.sync(entry.name)
        for src, ok, msg in results:
            if ok:
                yaml_count = len(list(src.groups_dir.glob("*.yaml")))
                console.print(
                    f"  [green]Synced:[/green] {src.name} — {yaml_count} group(s) available"
                )
            else:
                console.print(f"  [yellow]Sync pending:[/yellow] {msg}")
                console.print(
                    "[dim]The repo may not exist yet. "
                    "Groups will be available once it's published.[/dim]"
                )

    console.print()
    console.print(f"[bold green]Installed {pack.name}![/bold green]")
    if pack.groups:
        console.print("[dim]Now available in pjkm init, pjkm add, and pjkm list groups.[/dim]")


def uninstall(
    name: str = typer.Argument(help="Pack name to uninstall"),
) -> None:
    """Uninstall a group pack (removes the source and cached data)."""
    from rich.console import Console

    from pjkm.core.groups.sources import GroupSourceManager

    console = Console()
    mgr = GroupSourceManager()
    mgr.load()

    if mgr.remove(name):
        console.print(f"[green]Uninstalled {name}.[/green]")
    else:
        console.print(f"[red]Pack '{name}' is not installed.[/red]")
        if mgr.sources:
            console.print(f"Installed: {', '.join(s.name for s in mgr.sources)}")
        raise typer.Exit(1)


def installed() -> None:
    """List all installed group packs."""
    from rich.console import Console
    from rich.table import Table

    from pjkm.core.groups.sources import GroupSourceManager

    console = Console()
    mgr = GroupSourceManager()
    mgr.load()

    if not mgr.sources:
        console.print("[dim]No group packs installed.[/dim]")
        console.print("[dim]Browse: pjkm search[/dim]")
        console.print("[dim]Install: pjkm install <pack-name>[/dim]")
        return

    table = Table(title="Installed Group Packs")
    table.add_column("Name", style="cyan bold")
    table.add_column("URL")
    table.add_column("Groups", style="dim", justify="right")

    for s in mgr.sources:
        yaml_count = len(list(s.groups_dir.glob("*.yaml"))) if s.groups_dir.is_dir() else 0
        table.add_row(s.name, s.url, str(yaml_count) if yaml_count else "-")
    console.print(table)
