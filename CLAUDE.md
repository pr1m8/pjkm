# pjkm — Python Project Builder

## What this is
A CLI tool that scaffolds Python projects using a DAG-based task system with Copier templates. Projects are composed from an archetype (single-package, service, poly-repo, script-tool) plus optional package groups that add dependencies, tool config, GitHub Actions workflows, and real Python source code.

## Architecture
```
src/pjkm/
  cli/
    app.py                      # Slim entry point, wires commands from submodules
    commands/
      project.py                # init, add, update, upgrade, link, preview
      info.py                   # list, info, doctor
      groups.py                 # group create/import/validate/list/sync + source subcommands
      recipes.py                # recommend (6 presets), recipe (18 recipes)
      config.py                 # defaults, tui
      registry.py               # search, install, uninstall, installed
      adopt.py                  # adopt, status
  core/
    models/
      group.py                  # PackageGroup model (id, name, category, deps, scaffolded_files, etc.)
      project.py                # ProjectConfig, Archetype enum
      task.py                   # TaskEvent, Phase, TaskResult
    groups/
      definitions/              # 91 YAML group definitions in 8 category subdirectories
        core_dev/               # dev, linting, testing, typecheck, coverage, ...
        ai_ml/                  # langchain, ml, torch, vector_stores, ...
        web_api/                # api, auth, websocket, payments, ...
        infrastructure/         # docker, k8s, otel, celery, ...
        data_storage/           # database, redis, kafka, neo4j, ...
        docs_meta/              # docs, github_templates, submodules
        frontend/               # frontend, frontend_vite
        platform/               # mac, linux
      registry.py               # GroupRegistry — discovers YAML via rglob("*.yaml")
      resolver.py               # GroupResolver — transitive deps with cycle detection
      sources.py                # Remote group source management (git repos)
    registry/
      index.py                  # RegistryIndex — fetch/cache/search community packs
    templates/
      composer.py               # TemplateComposer — layers base + archetype + fragments
      loader.py                 # TemplateLoader — resolves names to paths
      renderer.py               # TemplateRenderer — wraps Copier run_copy
    tasks/                      # DAG-based task system (scaffold, configure, install, verify)
    engine/                     # ProjectEngine — executes task DAG
    utils.py                    # Shared utilities (deep_merge)
    defaults.py                 # UserDefaults from ~/.pjkmrc.yaml
  templates/
    base/                       # Shared by all projects (pyproject.toml, .gitignore, CI workflows)
    single_package/             # src layout + tests
    service/                    # + infra, Makefile, .env, .secrets
    poly_repo/                  # + packages/, tools/
    script_tool/                # + __main__.py, cli.py
    fragments/                  # 33 composable template fragments
  tui/                          # Textual TUI wizard
```

## Key patterns
- **Group-aware templates**: All templates receive `groups` (list of selected group IDs) in Jinja2 context. Use `{% if "database" in groups %}` to conditionally compose.
- **Category is in YAML**: Each group YAML has a `category` field. No hardcoded category maps.
- **rglob for discovery**: GroupRegistry uses `rglob("*.yaml")` so groups can be in subdirectories.
- **Fragments scaffold real code**: `api_app` fragment generates a full FastAPI app with routes, middleware, lifespan, deps. `db_models` generates SQLAlchemy engine + session + mixins. etc.

## Testing
```bash
pdm run pytest           # full suite
pdm run pytest -x -q     # quick, stop on first failure
```

## Common tasks
- Add a new group: create YAML in appropriate `definitions/<category>/` subdir
- Add a new fragment: create dir in `templates/fragments/<name>/` with copier.yml + template/
- Add a new recipe: add entry to RECIPES dict in `cli/commands/recipes.py`
- Run tests after changes: `pdm run pytest -x -q`
