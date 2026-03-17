"""pjkm CLI application — top-level Typer app.

Commands are organized into submodules under pjkm.cli.commands:
  - project: init, add, update, upgrade, link
  - info: list, info, doctor
  - groups: group create/import/validate/list/sync + source subcommands
  - recipes: recommend, recipe
  - config: defaults, tui
"""

from __future__ import annotations

import typer

from pjkm.cli.commands import adopt as adopt_mod
from pjkm.cli.commands import config, groups, info, project, recipes, registry

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


# --- Register commands from submodules ---

# Project lifecycle
app.command()(project.init)
app.command()(project.add)
app.command()(project.update)
app.command()(project.upgrade)
app.command(name="link")(project.link_tool)
app.command()(project.preview)

# Informational
app.command(name="list")(info.list_cmd)
app.command()(info.info)
app.command()(info.doctor)

# Discovery / recipes
app.command()(recipes.recommend)
app.command()(recipes.recipe)

# Configuration
app.command()(config.tui)
app.command()(config.defaults)

# Adopt existing projects
app.command()(adopt_mod.adopt)
app.command()(adopt_mod.status)

# Registry — search and install community group packs
app.command()(registry.search)
app.command()(registry.install)
app.command()(registry.uninstall)
app.command()(registry.installed)

# Group management (nested sub-app)
app.add_typer(groups.group_app, name="group")
