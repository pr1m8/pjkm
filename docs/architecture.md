# Architecture

## Package Layout

```
src/pjkm/
  cli/commands/           # 8 command modules
  core/
    models/               # Pydantic models (group, project, task)
    groups/definitions/   # 105 YAML group files in 8 subdirs
    groups/registry.py    # discovery via rglob("*.yaml")
    groups/resolver.py    # transitive deps + cycle detection
    registry/index.py     # community pack registry
    templates/            # composer, loader, renderer
    tasks/                # DAG-based task system
    engine/               # task execution engine
  templates/
    base/                 # shared by all (pyproject, CI, gitignore)
    service/              # + infra, Makefile, .env
    fragments/            # 34 composable pieces
```

## Execution Flow

```
User input → ProjectConfig → ProjectEngine.execute()
  SCAFFOLD:  base + archetype templates, git init
  CONFIGURE: merge group deps, render fragments
  INSTALL:   pdm install, pre-commit install
  VERIFY:    validate expected files
```

## Key Design Decisions

- **Groups are YAML, not code** — add groups without writing Python
- **Category in YAML** — no hardcoded maps, schema-driven
- **rglob for discovery** — groups can be in subdirectories
- **Group-aware Jinja2** — `{% if "database" in groups %}` for conditional composition
- **Copier under the hood** — proven template engine, not reinvented
