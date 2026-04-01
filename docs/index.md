# pjkm

Python project scaffolder with composable templates, 105 package groups, and a community registry.

```{toctree}
:maxdepth: 2
:caption: Getting Started

quickstart
recipes
presets
```

```{toctree}
:maxdepth: 2
:caption: User Guide

groups
templates
workspace
registry
adopt
defaults
```

```{toctree}
:maxdepth: 2
:caption: Reference

cli
architecture
pack-authoring
changelog
```

```{toctree}
:maxdepth: 2
:caption: API Reference

autoapi/index
```

## Quick Start

```bash
pip install pjkm

# Use a recipe
pjkm init my-api --recipe fastapi-service
cd my-api && python -m my_api

# Or pick groups
pjkm init my-lib -a single-package -g dev -g docs

# Preview first
pjkm preview --recipe saas-backend

# Interactive
pjkm tui
```

## What You Get

A fully configured project with:

- Real Python source code (API, auth, DB, Redis — all wired together)
- 22 GitHub Actions workflows
- Dockerfile, docker-compose, Makefile
- Pre-commit hooks, ruff, pyright, commitizen
- Sphinx docs, changelog, CONTRIBUTING.md
- Test fixtures that match your selected groups
