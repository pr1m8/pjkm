"""Informational commands — list, info, doctor."""

from __future__ import annotations

import typer

# Display order for group categories (category is now a field in each group YAML)
CATEGORY_ORDER = [
    "Core Dev", "AI / ML", "Web & API", "Data & Storage",
    "Infrastructure", "Frontend", "Docs & Meta", "Platform",
]

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

        categorized: dict[str, list] = {c: [] for c in CATEGORY_ORDER}
        for g in groups:
            categorized.setdefault(g.category, []).append(g)

        for cat_name in CATEGORY_ORDER:
            cat_groups = categorized.get(cat_name, [])
            if not cat_groups:
                continue
            table = Table(title=f"{cat_name} ({len(cat_groups)})")
            table.add_column("ID", style="cyan")
            table.add_column("Name")
            table.add_column("Requires", style="dim")
            table.add_column("Scaffold", style="green")
            for g in sorted(cat_groups, key=lambda g: g.id):
                reqs = ", ".join(g.requires_groups) if g.requires_groups else ""
                frags = ", ".join(sf.template_fragment for sf in g.scaffolded_files) or ""
                table.add_row(g.id, g.name, reqs, frags)
            console.print(table)
            console.print()
    else:
        console.print(f"[red]Unknown: {what}. Use 'archetypes' or 'groups'.[/red]")


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


def doctor() -> None:
    """Check the local environment for required and optional tools."""
    import re
    import shutil
    import subprocess

    from rich.console import Console

    console = Console()

    required_tools = [
        ("git", ["git", "--version"]),
        ("python", ["python3", "--version"]),
        ("pdm", ["pdm", "--version"]),
    ]
    optional_tools = [
        ("docker", ["docker", "--version"]),
        ("node", ["node", "--version"]),
        ("pnpm", ["pnpm", "--version"]),
        ("gh", ["gh", "--version"]),
        ("git-lfs", ["git-lfs", "--version"]),
        ("pre-commit", ["pre-commit", "--version"]),
        ("trunk", ["trunk", "--version"]),
    ]

    required_total = len(required_tools)
    optional_total = len(optional_tools)
    required_found = 0
    optional_found = 0

    def _get_version(cmd: list[str]) -> str:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() or result.stderr.strip()
        except Exception:
            return ""

    def _print_hint(name: str) -> None:
        hint = FIX_HINTS.get(name)
        if hint:
            console.print(f"         [dim]fix: {hint}[/dim]")

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
