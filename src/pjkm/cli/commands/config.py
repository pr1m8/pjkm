"""Configuration commands — defaults, tui."""

from __future__ import annotations

import typer


def tui() -> None:
    """Launch the interactive TUI wizard."""
    from pjkm.tui.app import run as run_tui

    run_tui()


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
license: "MIT"
python_version: "3.13"
archetype: "single-package"
groups: []
target_dir: "."

github:
  org: ""
  visibility: "private"
  remote: ""
  create_repo: false
  default_branch: "main"
"""
        target.write_text(template)
        console.print(f"[green]Created {target}[/green]")
        console.print("[dim]Edit this file to set your defaults.[/dim]")
        return

    if show_global:
        global_path = Path.home() / ".pjkmrc.yaml"
        console.print(f"Global config: {global_path}")
        if global_path.is_file():
            console.print("[green]File exists.[/green]")
        else:
            console.print("[dim]File does not exist. Create it to set global defaults.[/dim]")
        return

    # Show current defaults
    user_defaults = UserDefaults.load()

    console.print(
        Panel("[bold]Current Defaults[/bold]", title="pjkm defaults")
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
