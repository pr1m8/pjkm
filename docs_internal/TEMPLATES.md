# Template System

Internal reference for pjkm's Copier + Jinja2 template system.

## Overview

Templates live under `src/pjkm/templates/` and are organized into three layers, composed at render time by `TemplateComposer`.

```
src/pjkm/templates/
  base/                          # shared by all projects
    copier.yml                   # variables: project_name, project_slug, description,
                                 #   author_name, author_email, python_version, license
    template/
      pyproject.toml.jinja       # commitizen, ruff, pytest, coverage config
      README.md.jinja
      .gitignore.jinja
      .editorconfig.jinja        # 193 lines, all file types
      .gitattributes.jinja       # text/binary declarations
      .python-version.jinja
      .gitlint.jinja             # conventional commit rules
      .readthedocs.yaml.jinja    # RTD v2 config
      LICENSE.jinja              # MIT license
      CHANGELOG.md.jinja         # keep-a-changelog format
      CONTRIBUTING.md.jinja      # dev setup, commit conventions, PR workflow
      .github/
        PULL_REQUEST_TEMPLATE.md
        ISSUE_TEMPLATE/
          bug_report.md
          feature_request.md
          config.yml
        dependabot.yml.jinja     # pip + github-actions ecosystems
        labeler.yml.jinja        # auto-label PR rules by file path
        workflows/
          ci.yml.jinja           # 5 jobs: test, lint, typecheck, docs, security
          release.yml.jinja      # tag-triggered PyPI publish
          docker.yml.jinja       # Docker build + push to GHCR (multi-arch)
          codeql.yml.jinja       # GitHub CodeQL security analysis
          dependency-review.yml.jinja  # dependency vulnerability review on PRs
          labeler.yml.jinja      # auto-label PRs by changed files
  single_package/                # src layout + tests + conftest + py.typed
    copier.yml
    template/
      src/{{ project_slug }}/__init__.py.jinja
      src/{{ project_slug }}/py.typed
      tests/__init__.py
      tests/conftest.py.jinja
      tests/test_{{ project_slug }}.py.jinja
  service/                       # + infra, Makefile, .env, .secrets, .config, scripts
    copier.yml
    template/
      src/{{ project_slug }}/__init__.py.jinja
      src/{{ project_slug }}/py.typed
      src/{{ project_slug }}/core/__init__.py
      tests/__init__.py
      tests/conftest.py.jinja
      infra/README.md.jinja
      infra/compose.yaml.jinja
      .config/yamllint.yaml
      .config/.markdownlint-cli2.yaml
      .env.example.jinja
      .secrets.example.jinja
      scripts/.gitkeep
      Makefile.jinja
  poly_repo/                     # + packages/, tools/, scripts/
    copier.yml
    template/
      src/{{ project_slug }}/__init__.py.jinja
      src/{{ project_slug }}/py.typed
      packages/.gitkeep
      tools/.gitkeep
      scripts/.gitkeep
      tests/__init__.py
      infra/compose.yaml.jinja
      .env.example.jinja
      .secrets.example.jinja
      Makefile.jinja
  script_tool/                   # + __main__.py, cli.py (Typer)
    copier.yml
    template/
      src/{{ project_slug }}/__init__.py.jinja
      src/{{ project_slug }}/__main__.py.jinja
      src/{{ project_slug }}/cli.py.jinja
      tests/__init__.py
      tests/test_cli.py.jinja
  fragments/                     # composable pieces, one dir per fragment
    logging_structlog/           # structlog + Rich logging module
    infra_otel/                  # OTel collector, Prometheus, Grafana, Loki, Jaeger
    docs_sphinx/                 # Sphinx docs with autodoc, napoleon, autobuild
    database_alembic/            # Alembic async migrations
    infra_nginx/                 # Nginx reverse proxy config + Dockerfile
    docker_python/               # Dockerfile (multi-stage), Dockerfile.dev, devcontainer, compose.dev
    k8s_manifests/               # Kustomize base + overlays, Helm chart
    celery_worker/               # Celery app, tasks, beat schedule, compose.celery
    frontend_next/               # Next.js 15 + React 19 + Supabase SSR + Tailwind v4 + shadcn/ui
```

## Copier Template Format

Each template directory follows the Copier convention:

```
<template_dir>/
  copier.yml              # variable definitions (type, help, default)
  template/               # _subdirectory: "template" in copier.yml
    file.jinja             # .jinja suffix stripped after rendering
    {{ project_slug }}/    # directory names can use Jinja2 syntax
```

- `copier.yml` declares template variables and sets `_min_copier_version: "9.0.0"` and `_subdirectory: "template"`.
- Files ending in `.jinja` have the suffix stripped after rendering.
- File and directory names can use `{{ variable }}` Jinja2 syntax.
- Jinja2 filters available: `| lower`, `| replace('-', '_')`, `| replace('.', '')`, `| length`.

## Template Variables

The base `copier.yml` defines these variables (available in all layers):

| Variable         | Type | Default  | Description                                                |
| ---------------- | ---- | -------- | ---------------------------------------------------------- |
| `project_name`   | str  | —        | Project name (e.g., "my-project")                          |
| `project_slug`   | str  | computed | Python package name (auto-derived: lowercase, underscores) |
| `description`    | str  | `""`     | Short project description                                  |
| `author_name`    | str  | `""`     | Author name                                                |
| `author_email`   | str  | `""`     | Author email                                               |
| `python_version` | str  | `"3.13"` | Minimum Python version                                     |
| `license`        | str  | `"MIT"`  | License type                                               |

Archetype and fragment copier.yml files redeclare the variables they need (typically `project_name`, `project_slug`, and `python_version`).

## Composition Layers

### 1. Base Template

Rendered first. Produces scaffolding common to every project:

- `pyproject.toml` — build system, commitizen, ruff (lint + format + isort), pytest, coverage
- `README.md` — project name, description, install, usage sections
- `.gitignore` — Python, IDE, OS, build artifacts
- `.editorconfig` — comprehensive (Python, TOML, YAML, JSON, Markdown, Shell, Web, Docker, Makefiles)
- `.gitattributes` — text/binary declarations for all common file types
- `.python-version` — pinned version
- `.gitlint` — conventional commit enforcement (72-char title, 120-char body)
- `.readthedocs.yaml` — RTD v2 config with PDM + Sphinx
- `LICENSE` — MIT license
- `CHANGELOG.md` — Keep a Changelog format
- `CONTRIBUTING.md` — dev setup, code style, commit conventions, PR workflow
- `.github/` — PR template, issue templates (bug report, feature request), dependabot (pip + github-actions), labeler config, 6 workflows:
  - `ci.yml` — 5 jobs: test, lint, typecheck, docs, security
  - `release.yml` — tag-triggered PyPI publish via PDM
  - `docker.yml` — Docker build + push to GHCR (multi-arch: amd64 + arm64, GHA cache)
  - `codeql.yml` — GitHub CodeQL security analysis (weekly + on push/PR)
  - `dependency-review.yml` — dependency vulnerability review on PRs
  - `labeler.yml` — auto-label PRs by changed files (python, tests, docs, ci, infra, deps, frontend)

### 2. Archetype Templates

Rendered on top of base with `overwrite=True`. Adds archetype-specific structure:

| Archetype        | What it adds                                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `single_package` | `src/{slug}/` with `__init__.py` + `py.typed`, `tests/` with conftest and first test                                                                               |
| `service`        | Same as single_package + `core/` subpackage, `infra/compose.yaml`, `Makefile`, `.env.example`, `.secrets.example`, `.config/` (yamllint, markdownlint), `scripts/` |
| `poly_repo`      | Same as service + `packages/`, `tools/`, `scripts/` directories                                                                                                    |
| `script_tool`    | `src/{slug}/` with `__init__.py` + `__main__.py` + `cli.py` (Typer), `tests/test_cli.py`                                                                           |

### 3. Fragments

Rendered per selected group. Each fragment maps to a group's `scaffolded_files` field. Rendered with `overwrite=True` and `skip_if_exists=["*.py"]` to avoid clobbering user code.

| Fragment            | Group    | What it renders                                                                                                                                                                                                                                                                                                                 |
| ------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `logging_structlog` | logging  | `__init__.py` (exports `setup_logging`), `config.py` (structlog + Rich console renderer)                                                                                                                                                                                                                                        |
| `infra_otel`        | otel     | `otel/collector.yaml`, `prometheus/prometheus.yml`, `grafana/provisioning/datasources/datasources.yaml`, `loki/loki.yaml`, `compose.otel.yaml`                                                                                                                                                                                  |
| `docs_sphinx`       | docs     | `conf.py` (autodoc, napoleon, viewcode, intersphinx, myst, RTD theme), `index.rst`, `getting-started.rst`, `api/index.rst`, `changelog.rst`, `Makefile` (with `livehtml` target for autobuild), `_static/`, `_templates/`                                                                                                       |
| `database_alembic`  | database | `alembic.ini` (env-based URL, date-prefixed file template), `alembic/env.py` (async-aware with `run_async_migrations()`), `alembic/script.py.mako`, `alembic/versions/`                                                                                                                                                         |
| `infra_nginx`       | nginx    | `nginx/nginx.conf` (upstream proxy, rate limiting 30r/s, gzip, proxy headers, health check), `nginx/Dockerfile` (nginx:1.27-alpine), `compose.nginx.yaml`                                                                                                                                                                       |
| `docker_python`     | docker   | `Dockerfile` (multi-stage: base→deps→runtime, Python 3.13-slim, PDM, pipx, non-root user), `Dockerfile.dev` (+ Node.js 22 LTS, pnpm via corepack), `.dockerignore`, `.devcontainer/devcontainer.json` (VS Code Python + Docker features), `compose.dev.yaml` (app + postgres pgvector:pg17 + redis, hot-reload volumes)         |
| `k8s_manifests`     | k8s      | `k8s/base/` (deployment, service, ingress, configmap, HPA, kustomization), `k8s/overlays/dev/` (1 replica, low resources), `k8s/overlays/prod/` (3 replicas, higher limits), `helm/` (Chart.yaml, values.yaml, templates/deployment.yaml, \_helpers.tpl)                                                                        |
| `celery_worker`     | celery   | `src/{slug}/workers/celery_app.py` (Redis broker, JSON serialization, autodiscover), `workers/tasks.py` (example + periodic tasks with retry), `workers/beat_schedule.py` (crontab config), `infra/compose.celery.yaml` (worker concurrency=4, beat, flower on 5555)                                                            |
| `frontend_next`     | frontend | `pnpm-workspace.yaml` (apps/_ + packages/_), `package.json` (turbo scripts, pnpm 10), `turbo.json` (build/dev/lint/type-check), `apps/web/` (Next.js 15, React 19, Supabase SSR, Tailwind v4, shadcn/ui with new-york style, SCSS, `components.json`, `lib/utils.ts` cn() helper, `lib/supabase.ts` client, API proxy to :8000) |

## TemplateComposer

`TemplateComposer.compose(config, groups)` rendering pipeline:

```python
# 1. Render base template (shared scaffolding)
renderer.render("base", dest, data, overwrite=False)

# 2. Render archetype template (project shape)
renderer.render(archetype, dest, data, overwrite=True)

# 3. Render fragment templates (per-group scaffolding)
for group in groups:
    for sf in group.scaffolded_files:
        renderer.render(f"fragments/{sf.template_fragment}",
                       dest / sf.destination, data,
                       overwrite=True, skip_if_exists=["*.py"])
```

Returns a list of applied template names.

## TemplateRenderer

Wraps `copier.run_copy()`:

```python
copier.run_copy(
    src_path=str(template_path),
    dst_path=str(dest),
    data=answers,
    unsafe=True,           # allow running outside git
    skip_tasks=True,       # don't execute copier tasks
    overwrite=overwrite,
    pretend=dry_run,       # dry-run mode
    quiet=True,
)
```

## TemplateLoader

Resolves template names to filesystem paths:

- `loader.resolve("base")` → `src/pjkm/templates/base/` (via `importlib.resources`)
- `loader.resolve("single_package")` → `src/pjkm/templates/single_package/`
- `loader.resolve("fragments/logging_structlog")` → `src/pjkm/templates/fragments/logging_structlog/`
- Absolute paths pass through unchanged
- Raises `TemplateNotFoundError` for unknown template names
- `loader.list_builtin()` → list of available built-in template names

## How to Add a New Archetype

1. Add the value to `Archetype` enum in `src/pjkm/core/models/project.py`.
2. Create `src/pjkm/templates/<archetype_name>/copier.yml` with variables.
3. Create `src/pjkm/templates/<archetype_name>/template/` with Jinja2 files.
4. Add expected files to `EXPECTED_FILES` in `src/pjkm/core/tasks/verify/verify_structure.py`.
5. Update the `list` command's archetype table in `src/pjkm/cli/app.py`.

## How to Add a New Fragment

1. Create `src/pjkm/templates/fragments/<fragment_name>/copier.yml`.
2. Create `src/pjkm/templates/fragments/<fragment_name>/template/` with Jinja2 files.
3. Reference the fragment in a group's `scaffolded_files` field (see [GROUPS.md](GROUPS.md)).
4. No other registration needed — the group drives discovery.

Note: fragments are always part of the built-in templates. Custom and remote groups can reference built-in fragments, but custom fragment templates must be added to the pjkm source tree.
