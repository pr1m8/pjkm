# Architecture

Internal design reference for pjkm.

## Package Layout

```
src/pjkm/
  __init__.py                    # __version__ = "0.1.0"
  __main__.py                    # python -m pjkm -> cli.app:app()
  py.typed                       # PEP 561 marker
  core/                          # Zero UI dependencies
    defaults.py                  # UserDefaults, GitHubDefaults, GroupSource
    models/
      project.py                 # Archetype (StrEnum), ProjectConfig
      task.py                    # Phase (IntEnum), TaskDefinition, TaskResult, events
      group.py                   # PackageGroup, ScaffoldedFile
      config.py                  # EnvConfig, SecretsConfig, ToolConfig
      platform.py                # PlatformInfo (OS, arch, has_tool)
    engine/
      project_engine.py          # ProjectEngine orchestrator, ProjectResult
      dag.py                     # DAGResolver (Kahn's algorithm), CyclicDependencyError
      task_runner.py             # TaskRunner, TaskRunError
      task_context.py            # TaskContext (shared mutable state bag)
    tasks/
      base.py                   # BaseTask ABC
      registry.py               # TaskRegistry
      defaults.py               # create_default_registry() -> 9 built-in tasks + plugin loading
      scaffold/
        init_project.py          # Renders base + archetype templates
        init_git.py              # git init
        setup_remote.py          # Configure git remote, optionally create GitHub repo via gh
      configure/
        apply_groups.py          # Merges group deps into pyproject.toml + renders fragments
        configure_linting.py     # Writes pre-commit, trunk, secrets baseline, tool configs
        setup_git_lfs.py         # Auto-setup Git LFS for ML groups (hf, ml)
      install/
        pdm_install.py           # pdm install
        pre_commit_install.py    # pre-commit install (pre-commit + commit-msg hooks)
      verify/
        verify_structure.py      # Validates expected files per archetype
    templates/
      loader.py                  # Resolves built-in/local template paths
      renderer.py                # Wraps copier.run_copy() + run_update()
      composer.py                # Layers base -> archetype -> fragments
    groups/
      registry.py                # GroupRegistry (auto-discovers YAML + custom + remote sources)
      resolver.py                # GroupResolver (transitive deps, cycle detection)
      sources.py                 # GroupSourceManager (git clone/pull/cache for remote repos)
      definitions/               # 91 YAML group files in 8 category subdirectories
    platform/
      detect.py                  # OS, arch, available tools
      groups.py                  # Platform-specific adjustments
  templates/                     # Built-in Copier templates
    base/                        # Shared: pyproject.toml, README, .gitignore, .editorconfig,
                                 #   .gitattributes, .github/, LICENSE, CHANGELOG, CONTRIBUTING
    single_package/              # src layout + tests
    service/                     # + infra/, Makefile, .env.example, .secrets.example, .config/
    poly_repo/                   # + packages/, tools/, scripts/
    script_tool/                 # + __main__.py, cli.py, test_cli.py
    fragments/
      logging_structlog/         # structlog + Rich config module
      infra_otel/                # OTel collector, Prometheus, Grafana, Loki, Jaeger
      docs_sphinx/               # Sphinx conf.py, index.rst, Makefile, API docs
      database_alembic/          # alembic.ini, async env.py, versions/
      infra_nginx/               # nginx.conf, Dockerfile, compose override
      docker_python/             # Dockerfile (multi-stage), Dockerfile.dev, devcontainer, compose.dev
      k8s_manifests/             # Kustomize base + overlays, Helm chart
      celery_worker/             # Celery app, tasks, beat schedule, compose.celery
      frontend_next/             # Next.js 15 + React 19 + Supabase SSR + Tailwind v4 + shadcn/ui
      frontend_vite/             # Vite + React + TypeScript SPA with API proxy
      notebooks/                 # Jupyter notebooks directory + example notebook
      scripts_cli/               # CLI scripts directory + example Typer script
      docs_mkdocs/               # MkDocs + Material theme + mkdocstrings
      submodules/                # .gitmodules + sync-submodules.sh
      github_templates/          # Issue/PR templates, CODEOWNERS, CONTRIBUTING, SECURITY
      makefile_sections/         # Modular .mk include files (docker, python, db, redis, etc.)
      compose_postgres/          # Docker Compose service for PostgreSQL
      compose_redis/             # Docker Compose service for Redis
      compose_kafka/             # Docker Compose service for Kafka
      compose_mongodb/           # Docker Compose service for MongoDB
      compose_rabbitmq/          # Docker Compose service for RabbitMQ
  cli/
    app.py                       # Typer app: init, add, update, upgrade, link, tui, list, info, doctor, defaults, group
  tui/
    app.py                       # PjkmApp (Textual)
    app.tcss                     # TUI stylesheet
    screens/
      welcome.py                 # Project name + archetype selection
      groups.py                  # Group checkbox selection
      review.py                  # Review choices before build
      progress.py                # Live DAG progress with RichLog
      done.py                    # Summary + next steps
    widgets/
      __init__.py                # (uses built-in Textual widgets)
```

## Core Design Principles

1. **Core is synchronous, zero UI deps.** All logic lives in `core/`. Neither Typer nor Textual are imported there.
2. **CLI and TUI are thin shells.** Both call `ProjectEngine.execute()` and consume `TaskEvent` callbacks for progress reporting.
3. **DAG-driven execution.** Tasks declare `depends_on`; the engine resolves and executes them in topological order within each phase.
4. **Data-driven groups.** Adding a group = adding a YAML file + optional template fragment. No Python code needed.
5. **Composable templates.** Three layers (base + archetype + fragments) merged by `TemplateComposer` via Copier.
6. **Repo-based extensibility.** Groups can come from built-in definitions, local directories, or remote git repos. Sources are registered and cached automatically.

## Execution Flow

```
User input (CLI flags or TUI wizard)
  -> ProjectConfig (Pydantic validation: name, archetype, groups, python_version)
  -> UserDefaults.load() (merge ~/.pjkmrc.yaml + ./.pjkmrc.yaml)
  -> ProjectEngine.execute(config, on_event=callback, extra={github: ...})
       -> TaskRegistry.get_definitions() -> list[TaskDefinition]
       -> DAGResolver.resolve(definitions) -> topologically sorted list
       -> TaskContext(config, platform, results={}, extra={})
       -> TaskRunner.run(sorted_tasks, ctx)
            per task:
              -> PhaseStarted event (on phase transition)
              -> task.should_run(ctx) -> skip if False
              -> TaskStarted event
              -> task.execute(ctx) -> TaskResult
              -> ctx.results[task_id] = result
              -> TaskCompleted event
              -> on failure: raise TaskRunError (stops immediately)
            -> PhaseCompleted event
       -> ProjectResult(config, results)
```

## DAG Phases

Tasks are bucketed into four strictly ordered phases. Within each phase, `depends_on` edges define the topological order (Kahn's algorithm). Cross-phase dependencies are implicit: all tasks in phase N must complete before phase N+1 begins.

```
SCAFFOLD (1) -> CONFIGURE (2) -> INSTALL (3) -> VERIFY (4)
```

| Phase       | Tasks                                      | Purpose                                                                        |
| ----------- | ------------------------------------------ | ------------------------------------------------------------------------------ |
| `SCAFFOLD`  | `init_project`, `init_git`, `setup_remote` | Create directory structure from Copier templates, `git init`, configure remote |
| `CONFIGURE` | `apply_groups`, `configure_linting`, `setup_git_lfs` | Merge group deps, write lint configs, LFS setup for ML groups |
| `INSTALL`   | `pdm_install`, `pre_commit_install`        | `pdm install`, `pre-commit install` (pre-commit + commit-msg hooks)            |
| `VERIFY`    | `verify_structure`                         | Validate expected files exist for the archetype                                |

## Task Dependency Graph

```
SCAFFOLD:     init_project -> init_git -> setup_remote
CONFIGURE:    apply_groups    configure_linting    setup_git_lfs   (independent)
INSTALL:      pdm_install -> pre_commit_install
VERIFY:       verify_structure
```

## Template System

Three-layer composition via `TemplateComposer`:

1. **Base** (`templates/base/`) — rendered first with `overwrite=False`. Produces: pyproject.toml, README.md, .gitignore, .editorconfig, .gitattributes, .python-version, .gitlint, .readthedocs.yaml, LICENSE, CHANGELOG.md, CONTRIBUTING.md, `.github/` (PR template, issue templates, dependabot, CI/release workflows).
2. **Archetype** (`templates/{archetype}/`) — rendered on top with `overwrite=True`. Adds archetype-specific files.
3. **Fragments** (`templates/fragments/{fragment_name}/`) — rendered per group with `overwrite=True`, `skip_if_exists=["*.py"]`. Adds group-specific code and config.

See [TEMPLATES.md](TEMPLATES.md) for full reference.

## Package Groups

91 built-in YAML groups in `core/groups/definitions/` (organized in 8 category subdirectories), extensible via:

- **Local custom groups** in `~/.pjkm/groups/` and `./.pjkm/groups/` (auto-loaded)
- **Remote group sources** — git repos registered via `pjkm group source add` or `.pjkmrc.yaml`
- **Imported groups** — converted from any `pyproject.toml` via `pjkm group import`

Each group carries:

- Python dependencies (added to `[project.optional-dependencies]`)
- `pyproject.toml` tool config (merged into `[tool.*]` via `_deep_merge()`)
- Scaffolded files (template fragment references)
- Archetype constraints and platform filters
- Transitive requirements on other groups

Groups are auto-discovered from YAML directories. `GroupResolver` expands `requires_groups` transitively with cycle detection and platform filtering.

See [GROUPS.md](GROUPS.md) for full reference.

## User Defaults & Configuration

Defaults are loaded from config files and merged (later overrides earlier):

1. `~/.pjkmrc.yaml` — global defaults
2. `./.pjkmrc.yaml` — project/workspace defaults
3. CLI flags — override both

Config includes: author, license, python_version, archetype, groups, target_dir, GitHub settings (org, visibility, remote, create_repo, default_branch), and group_sources (remote git repos).

## Group Source System

Remote git repos can provide group definitions, enabling team-wide or community sharing:

```
~/.pjkm/
  sources.yaml              # Registered remote sources
  cache/sources/            # Cloned repos (shallow, depth=1)
    quant-abc123/           # One dir per source
      *.yaml                # Group YAML files
  groups/                   # Global custom groups (manual)
.pjkm/groups/               # Project-local custom groups
```

Sources can also be declared in `.pjkmrc.yaml`:

```yaml
group_sources:
  - url: https://github.com/org/pjkm-groups-quant.git
    name: quant
    path: groups/ # subdirectory within repo
    ref: main # branch/tag to track
```

## Config Pattern

Generated projects follow a three-tier config layout:

| Location            | Contents                                             | Committed |
| ------------------- | ---------------------------------------------------- | --------- |
| `.env.example`      | Runtime env vars (non-secret defaults)               | Yes       |
| `.config/`          | Tool configs: yamllint.yaml, .markdownlint-cli2.yaml | Yes       |
| `.secrets.example`  | Credentials template (copy to .secrets, gitignored)  | Yes       |
| `.secrets.baseline` | detect-secrets baseline for secret scanning          | Yes       |

## CLI Commands

```
pjkm init NAME [-a ARCHETYPE] [-g GROUP...] [-d DIR] [--dry-run] [--author] [--email]
pjkm add [-g GROUP...] [-d DIR]
pjkm update [-d DIR] [--dry-run]
pjkm upgrade [-g GROUP...] [-d DIR] [--latest] [--refresh-tools] [--dry-run] [--install/--no-install]
pjkm link TOOL_NAME [-d DIR] [--dry-run]
pjkm tui
pjkm list [archetypes|groups]
pjkm info GROUP_ID
pjkm doctor
pjkm defaults [--init] [--global]
pjkm group create ID [--name] [--dir]
pjkm group import PYPROJECT [--section...] [--dir]
pjkm group validate [PATH]
pjkm group list
pjkm group sync [NAME]
pjkm group source add URL [--name] [--path] [--ref] [--sync/--no-sync]
pjkm group source list
pjkm group source remove NAME
```

## Key Statistics

- **4** archetypes: single_package, service, poly_repo, script_tool
- **105** built-in package groups in 8 category subdirectories
- **34** template fragments (6 generate Python source code with group-aware wiring)
- **22** recipes + 6 presets + 5 workspace blueprints
- **22** GitHub Actions workflows (15 base + 7 fragment)
- **10** community registry packs
- **9** built-in tasks across 4 phases
- **30** CLI commands/subcommands
- **197** tests (including 17 integration tests)
- **5** TUI screens
