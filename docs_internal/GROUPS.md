# Package Groups

Internal reference for the package group system.

## What a Group Is

A group is a YAML file that bundles:

- Python dependencies (added to `[project.optional-dependencies.<section>]`)
- Scaffolded files (rendered from template fragments)
- `pyproject.toml` tool configuration (merged into `[tool.*]` sections)
- Constraints (archetype compatibility, platform filters, group requirements)

Groups are **auto-discovered** from YAML directories. No registration code needed.

## Where Groups Come From

Groups are loaded in this order (later sources override earlier ones with the same ID):

| Source             | Location                                    | How to add                       |
| ------------------ | ------------------------------------------- | -------------------------------- |
| **Built-in**       | `src/pjkm/core/groups/definitions/*.yaml`   | Ship with pjkm                   |
| **Global custom**  | `~/.pjkm/groups/*.yaml`                     | `pjkm group create ID` or manual |
| **Project custom** | `./.pjkm/groups/*.yaml`                     | `pjkm group create ID` or manual |
| **Remote sources** | `~/.pjkm/cache/sources/<name>/*.yaml`       | `pjkm group source add <url>`    |
| **Config sources** | Cached from `.pjkmrc.yaml` `group_sources:` | Add to config file               |

All sources are merged into a single registry. Custom and remote groups can override built-in groups with the same ID.

## YAML Schema

```yaml
id: database # unique identifier (required)
name: "Database & Migrations" # human-readable name (required)
description: "SQLAlchemy async ORM..." # short description (required)

archetypes: # which archetypes this group applies to
  - service #   empty list = all archetypes
  - poly_repo

requires_groups: # transitive dependencies on other groups
  - logging #   resolved recursively, cycle-detected

platform_filter:
  null # optional OS constraint: "darwin", "linux", etc.
  #   null = no constraint

dependencies: # dict of section name -> list of PEP 508 specs
  database: #   added to [project.optional-dependencies.database]
    - "sqlalchemy[asyncio]>=2.0.40"
    - "alembic>=1.15.0"
    - "asyncpg>=0.30.0"

scaffolded_files: # template fragments to render
  - template_fragment: "database_alembic" #   maps to templates/fragments/database_alembic/
    destination: "." #   rendered relative to project root
    description: "Alembic migration scaffolding"
    conditions: {} #   extra Jinja2 context vars (optional)

pyproject_tool_config: # merged into [tool.*] sections via _deep_merge
  coverage.run: #   dotted keys expanded: [tool.coverage.run]
    source: ["src"]
    branch: true
```

All fields except `id`, `name`, and `description` are optional. Defaults: `archetypes: []`, `requires_groups: []`, `platform_filter: null`, `dependencies: {}`, `scaffolded_files: []`, `pyproject_tool_config: {}`.

## Current Built-in Groups (43)

### Development & Quality (10)

| ID          | Name                     | Dependencies                                                                      | Requires                              | Archetype |
| ----------- | ------------------------ | --------------------------------------------------------------------------------- | ------------------------------------- | --------- |
| `dev`       | Development Essentials   | ipython                                                                           | linting, testing, typecheck, coverage | all       |
| `linting`   | Linting & Formatting     | ruff, pre-commit, commitizen                                                      | —                                     | all       |
| `testing`   | Testing                  | pytest, pytest-cov, pytest-mock, pytest-asyncio                                   | —                                     | all       |
| `typecheck` | Type Checking            | pyright, mypy                                                                     | —                                     | all       |
| `coverage`  | Code Coverage            | coverage[toml]                                                                    | testing                               | all       |
| `security`  | Security Scanning        | bandit, detect-secrets                                                            | —                                     | all       |
| `docs`      | Documentation            | sphinx, sphinx-autobuild, sphinx-autodoc-typehints, sphinx-rtd-theme, myst-parser | —                                     | all       |
| `jupyter`   | Jupyter Notebook Support | jupyterlab, ipykernel                                                             | —                                     | all       |
| `dev_extended` | Extended Dev Tools    | pre-commit, commitizen, tox, nox, hatch                                           | dev, docs, security                   | all       |
| `dataviz`   | Data Visualization       | matplotlib, seaborn, plotly, altair, kaleido                                      | —                                     | all       |

### Infrastructure & Containers (4)

| ID         | Name                    | Dependencies    | Requires | Archetype          | Scaffold                                                                    |
| ---------- | ----------------------- | --------------- | -------- | ------------------ | --------------------------------------------------------------------------- |
| `docker`   | Docker & Containers     | —               | —        | service, poly_repo | Dockerfile, Dockerfile.dev, .devcontainer/, compose.dev.yaml, .dockerignore |
| `k8s`      | Kubernetes & Deployment | kubernetes      | docker   | service, poly_repo | k8s/ (Kustomize base + dev/prod overlays), helm/ chart                      |
| `nginx`    | Nginx Reverse Proxy     | — (config only) | —        | service, poly_repo | infra/nginx/ config + Dockerfile                                            |
| `makefile` | Modular Makefile        | —               | —        | service, poly_repo | make/ directory with 10 composable .mk sections                             |

### Backend Services (9)

| ID       | Name                    | Dependencies    | Requires | Archetype          | Scaffold                                                                    |
| -------- | ----------------------- | --------------- | -------- | ------------------ | --------------------------------------------------------------------------- |
| `docker` | Docker & Containers     | —               | —        | service, poly_repo | Dockerfile, Dockerfile.dev, .devcontainer/, compose.dev.yaml, .dockerignore |
| `k8s`    | Kubernetes & Deployment | kubernetes      | docker   | service, poly_repo | k8s/ (Kustomize base + dev/prod overlays), helm/ chart                      |
| `nginx`  | Nginx Reverse Proxy     | — (config only) | —        | service, poly_repo | infra/nginx/ config + Dockerfile                                            |

### Backend Services (6)

| ID         | Name                     | Dependencies                                                    | Requires | Archetype          |
| ---------- | ------------------------ | --------------------------------------------------------------- | -------- | ------------------ |
| `api`      | API Framework            | fastapi, uvicorn[standard], pydantic-settings, python-multipart | —        | service            |
| `gateway`  | API Gateway & Resilience | slowapi, tenacity, pyrate-limiter, httpx                        | api      | service            |
| `database` | Database & Migrations    | sqlalchemy[asyncio], alembic, asyncpg, greenlet                 | —        | service, poly_repo |
| `redis`    | Redis                    | redis[hiredis]                                                  | —        | service, poly_repo |
| `mongodb`  | MongoDB                  | motor, beanie, pymongo                                          | —        | service, poly_repo |
| `supabase` | Supabase                 | supabase, postgrest, gotrue, storage3, realtime                 | —        | service, poly_repo |
| `grpc`     | gRPC                     | grpcio, grpcio-tools, protobuf, grpcio-reflection               | api      | service            |
| `graphql`  | GraphQL                  | strawberry-graphql[fastapi], graphql-core                       | api      | service            |
| `auth`     | Authentication           | python-jose[cryptography], passlib[bcrypt], authlib              | api      | service            |

### Task Queues & Messaging (4)

| ID         | Name               | Dependencies                                                   | Requires | Archetype          | Scaffold                                                         |
| ---------- | ------------------ | -------------------------------------------------------------- | -------- | ------------------ | ---------------------------------------------------------------- |
| `celery`   | Celery Task Queue  | celery[redis], flower                                          | —        | service, poly_repo | workers/ (celery_app, tasks, beat_schedule), compose.celery.yaml |
| `airflow`  | Apache Airflow     | apache-airflow, apache-airflow-providers-celery/postgres/redis | —        | service, poly_repo | —                                                                |
| `kafka`    | Kafka Streaming    | confluent-kafka, aiokafka, faust-streaming                     | —        | service, poly_repo | —                                                                |
| `rabbitmq` | RabbitMQ Messaging | pika, aio-pika, kombu                                          | —        | service, poly_repo | —                                                                |

### Observability (3)

| ID           | Name                        | Dependencies                                                       | Requires | Archetype          |
| ------------ | --------------------------- | ------------------------------------------------------------------ | -------- | ------------------ |
| `logging`    | Structured Logging          | rich, structlog                                                    | —        | all                |
| `otel`       | OpenTelemetry Observability | opentelemetry-distro, -api, -sdk, -exporter-otlp, -instrumentation | logging  | service, poly_repo |
| `monitoring` | Application Monitoring      | prometheus-client, prometheus-fastapi-instrumentator               | api      | service            |

### Frontend (2)

| ID              | Name                   | Dependencies | Requires | Archetype          | Scaffold                                                                                                |
| --------------- | ---------------------- | ------------ | -------- | ------------------ | ------------------------------------------------------------------------------------------------------- |
| `frontend`      | Next.js Frontend       | — (npm deps) | —        | service, poly_repo | apps/web/ (Next.js 15, React 19, Supabase SSR, Tailwind v4, shadcn/ui), pnpm-workspace.yaml, turbo.json |
| `frontend_vite` | Vite + React + TS      | — (npm deps) | —        | service, poly_repo | Vite 6 + React 19 + TypeScript SPA with /api proxy to :8000                                            |

### AI & Machine Learning (3)

| ID          | Name             | Dependencies                                                                                                                                                                    | Requires | Archetype |
| ----------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------- |
| `hf`        | Hugging Face     | huggingface-hub, transformers, datasets, accelerate, sentence-transformers, sentencepiece, safetensors, tokenizers, hf-transfer, hf-xet, peft, bitsandbytes (Linux x86_64 only) | —        | all       |
| `ml`        | Machine Learning | scikit-learn, xgboost, lightgbm, onnx, onnxruntime, pandas, numpy, scipy, matplotlib, seaborn, polars                                                                           | —        | all       |
| `langchain` | LangChain        | langchain, langchain-core, -community, -openai, -anthropic, -huggingface, langgraph, langsmith                                                                                  | —        | all       |

### Notebook & Data Science (2)

| ID         | Name                     | Dependencies                                              | Requires          | Archetype |
| ---------- | ------------------------ | --------------------------------------------------------- | ----------------- | --------- |
| `notebook` | Notebook & Data Science  | nbconvert, nbformat, ipywidgets, pandas, numpy            | jupyter, dataviz  | all       |
| `scripts`  | Scripts & CLI Tools      | typer[all], click, shellingham, python-dotenv, invoke      | —                 | all       |

### Docs Alternatives (1)

| ID           | Name                 | Dependencies                                                     | Requires | Archetype |
| ------------ | -------------------- | ---------------------------------------------------------------- | -------- | --------- |
| `docs_mkdocs`| Documentation (MkDocs)| mkdocs, mkdocs-material, mkdocstrings[python], gen-files         | —        | all       |

### Cloud & Infra (1)

| ID   | Name | Dependencies                                 | Requires | Archetype |
| ---- | ---- | -------------------------------------------- | -------- | --------- |
| `aws`| AWS  | boto3, botocore, aws-lambda-powertools       | —        | all       |

### Project Management (2)

| ID                 | Name              | Dependencies | Requires | Archetype  | Scaffold                                              |
| ------------------ | ----------------- | ------------ | -------- | ---------- | ----------------------------------------------------- |
| `github_templates` | GitHub Templates  | —            | —        | all        | Issue/PR templates, CODEOWNERS, CONTRIBUTING, SECURITY |
| `submodules`       | Git Submodules    | —            | —        | poly_repo  | .gitmodules + scripts/sync-submodules.sh               |

### Platform (2)

| ID      | Name  | Dependencies                             | Platform | Archetype |
| ------- | ----- | ---------------------------------------- | -------- | --------- |
| `mac`   | macOS | watchdog, pyobjc-core, pyobjc-Cocoa      | darwin   | all       |
| `linux` | Linux | inotify-simple, python-systemd, setproctitle | linux | all       |

## Groups with Scaffolded Files

These groups render template fragments into the generated project:

| Group      | Fragment            | Destination                | What it creates                                                                                             |
| ---------- | ------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `logging`  | `logging_structlog` | `src/{slug}/core/logging/` | `__init__.py`, `config.py` (structlog + Rich)                                                               |
| `otel`     | `infra_otel`        | `infra/`                   | OTel collector, Prometheus, Grafana, Loki configs + compose.otel.yaml                                       |
| `docs`     | `docs_sphinx`       | `docs/`                    | conf.py (autodoc, napoleon, myst), index.rst, Makefile, API docs                                            |
| `database` | `database_alembic`  | `.`                        | alembic.ini, alembic/env.py (async), script.py.mako, versions/                                              |
| `nginx`    | `infra_nginx`       | `infra/`                   | nginx.conf, Dockerfile, compose.nginx.yaml                                                                  |
| `docker`   | `docker_python`     | `.`                        | Dockerfile (multi-stage), Dockerfile.dev (Node.js + pnpm), .dockerignore, .devcontainer/, compose.dev.yaml  |
| `k8s`      | `k8s_manifests`     | `.`                        | k8s/ Kustomize (base + dev/prod overlays), helm/ chart (deployment, HPA, helpers)                           |
| `celery`   | `celery_worker`     | `.`                        | workers/ (celery_app.py, tasks.py, beat_schedule.py), infra/compose.celery.yaml                             |
| `frontend` | `frontend_next`     | `.`                        | apps/web/ (Next.js 15 + React 19 + Supabase SSR + Tailwind v4 + shadcn/ui), pnpm-workspace.yaml, turbo.json |
| `frontend_vite` | `frontend_vite` | `.`                   | Vite + React + TypeScript SPA with dev server proxy                                                      |
| `notebook` | `notebooks`          | `.`                        | notebooks/ with example Jupyter notebook                                                                  |
| `scripts`  | `scripts_cli`        | `.`                        | scripts/ with example Typer CLI script                                                                    |
| `docs_mkdocs` | `docs_mkdocs`    | `.`                        | mkdocs.yml + docs/ with Material theme                                                                    |
| `submodules` | `submodules`       | `.`                        | .gitmodules + scripts/sync-submodules.sh                                                                  |
| `github_templates` | `github_templates` | `.`              | Issue/PR templates, CODEOWNERS, CONTRIBUTING.md, SECURITY.md                                              |
| `makefile` | `makefile_sections`  | `.`                        | make/ with 10 composable .mk include files                                                                |
| `database` | `compose_postgres`   | `.`                        | infra/compose.postgres.yaml Docker Compose service                                                        |
| `redis`    | `compose_redis`      | `.`                        | infra/compose.redis.yaml Docker Compose service                                                           |
| `kafka`    | `compose_kafka`      | `.`                        | infra/compose.kafka.yaml Docker Compose service                                                           |
| `mongodb`  | `compose_mongodb`    | `.`                        | infra/compose.mongodb.yaml Docker Compose service                                                         |
| `rabbitmq` | `compose_rabbitmq`   | `.`                        | infra/compose.rabbitmq.yaml Docker Compose service                                                        |

## Dependency Graph

```
dev
 ├── linting
 ├── testing
 ├── typecheck
 └── coverage
      └── testing

dev_extended
 ├── dev
 │    ├── linting
 │    ├── testing
 │    ├── typecheck
 │    └── coverage
 │         └── testing
 ├── docs
 └── security

k8s
 └── docker

otel
 └── logging

gateway / grpc / graphql / auth / monitoring
 └── api

notebook
 ├── jupyter
 └── dataviz
```

## Resolution Algorithm

`GroupResolver.resolve(selected_ids, platform)`:

1. For each selected group ID, verify it exists in the registry. Raise `GroupResolutionError` if not.
2. Expand `requires_groups` transitively via depth-first recursion. Track visiting set for cycle detection.
3. Build ordered list (dependencies before dependents, deduped).
4. Filter by `platform_filter` if `PlatformInfo` is provided (match against `platform.os`).
5. Return resolved `list[PackageGroup]` in dependency order.

## How Groups Are Applied

`ApplyGroupsTask.execute(ctx)`:

1. Load `GroupRegistry` with `load_all()` (built-in + custom + remote sources).
2. Validate selected group IDs against `registry.group_ids` (fails with clear error if unknown).
3. Resolve groups transitively via `GroupResolver`.
4. Read existing `pyproject.toml` with `tomllib`.
5. For each group:
   - Merge `dependencies` dict into `[project.optional-dependencies]` (deduped via `dict.fromkeys`).
   - Merge `pyproject_tool_config` into `[tool.*]` via `_deep_merge()` (splits dotted keys like `ruff.lint` into nested dicts).
6. Write `pyproject.toml` back with `tomli_w.dump()` (skipped in dry-run mode).
7. Render `scaffolded_files` using `TemplateRenderer` for each group's template fragments.

## Remote Group Sources

Git repos containing group YAML files can be registered as sources:

```bash
# Add a remote source (clones immediately)
pjkm group source add https://github.com/org/pjkm-groups-quant.git

# Source with groups in a subdirectory
pjkm group source add git@github.com:org/ooai.git \
  --path packages/wraquant/groups --name quant

# Pin to a branch
pjkm group source add https://github.com/team/shared-groups.git \
  --ref main --name team-groups

# List, sync, remove
pjkm group source list
pjkm group sync              # pull all sources
pjkm group sync quant         # pull one
pjkm group source remove quant
```

Sources can also be declared in `.pjkmrc.yaml`:

```yaml
group_sources:
  - url: https://github.com/org/pjkm-groups-quant.git
    name: quant
  - url: git@github.com:team/shared-groups.git
    path: groups/
    ref: main
```

**Cache layout:**

```
~/.pjkm/
  sources.yaml                    # registered sources (persisted by CLI)
  cache/sources/
    quant-abc123/                 # shallow clone, one per source
      market_data.yaml
      timeseries.yaml
      optimization.yaml
```

## Importing Groups from pyproject.toml

Convert `[project.optional-dependencies]` sections from any pyproject.toml into pjkm group YAML files:

```bash
# Import all sections
pjkm group import ../ooai/packages/wraquant/pyproject.toml

# Import specific sections only
pjkm group import ../wraquant/pyproject.toml \
  --section market-data --section timeseries --section optimization

# Import to a specific directory
pjkm group import ../pyproject.toml --dir ~/.pjkm/groups/
```

Each section becomes a separate `.yaml` file with dependencies pre-filled.

## How to Add a New Group

### Option 1: Built-in group (ships with pjkm)

1. Create `src/pjkm/core/groups/definitions/<group_id>.yaml` following the schema above.
2. If the group needs scaffolded files:
   - Create `src/pjkm/templates/fragments/<fragment_name>/copier.yml` with template variables.
   - Add a `template/` subdirectory with Jinja2-templated files.
3. That's it. The group is auto-discovered from the YAML directory.

### Option 2: Custom local group

```bash
pjkm group create quant-data --name "Quantitative Data"
# Creates ./.pjkm/groups/quant_data.yaml — edit to add dependencies
```

Custom groups in `~/.pjkm/groups/` (global) or `./.pjkm/groups/` (project-local) are loaded automatically.

### Option 3: Import from existing project

```bash
pjkm group import path/to/pyproject.toml --section data --section ml
# Creates ./.pjkm/groups/data.yaml and ml.yaml with deps pre-filled
```

### Option 4: Share via git repo

1. Create a git repo with `.yaml` group files at the root (or a subdirectory).
2. Others add it: `pjkm group source add <url> [--path subdir/]`
3. Groups become available everywhere after `pjkm group sync`.

### Validating custom groups

```bash
pjkm group validate                    # validate ./.pjkm/groups/
pjkm group validate path/to/groups/    # validate a specific directory
pjkm group validate mygroup.yaml       # validate a single file
```

## Validation

The test suite (`tests/test_templates.py` and `tests/test_group_sources.py`) verifies:

- All 43 built-in groups load without errors
- Every `scaffolded_files` fragment reference points to an existing template (21 fragments, 0 orphans)
- All group IDs are unique
- All `requires_groups` references point to existing groups
- Custom groups can be loaded from arbitrary directories
- Groups can be imported from pyproject.toml files
- Remote source registration, persistence, and cache loading work correctly
