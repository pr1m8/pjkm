# pjkm

Python project scaffolder that generates fully-configured repositories with a DAG-based task engine, composable Copier templates, and YAML-defined package groups.

## Features

- **4 archetypes** — `single_package`, `service`, `poly_repo`, `script_tool`
- **28 package groups** — Docker, K8s, Celery, Kafka, Next.js, Supabase, HuggingFace, LangChain, ML, FastAPI, SQLAlchemy, OTel, and more
- **DAG-based engine** — 8 tasks execute in dependency order across 4 phases (scaffold, configure, install, verify)
- **Composable templates** — base + archetype + 9 fragments layered via Copier + Jinja2
- **Docker-first** — multi-stage Dockerfile, devcontainer, compose.dev.yaml out of the box
- **Fullstack** — Next.js + Supabase + Tailwind + shadcn/ui frontend via pnpm workspaces + Turborepo
- **K8s-ready** — Kustomize base/overlays + Helm chart scaffold
- **ML-ready** — Hugging Face, LangChain, scikit-learn, XGBoost, ONNX with platform-specific quantization
- **Batteries included** — pre-commit (17 hooks), trunk, ruff, commitizen, GitHub Actions (9 workflows), dependabot, RTD
- **CLI + TUI** — same core engine, two interfaces (Typer CLI, Textual TUI)
- **Dry-run mode** — preview what would be generated without writing files
- **User defaults** — configure once in `~/.pjkmrc.yaml`, override per-project or per-command
- **Extensible groups** — add groups via YAML files, import from pyproject.toml, or share via git repos

## Install

```bash
pip install pjkm
```

## Quick Start

```bash
# Scaffold a library with dev tooling and docs
pjkm init my-library -a single_package -g dev -g docs

# Scaffold a full-stack API service with Docker + K8s
pjkm init my-api -a service \
    -g docker -g k8s \
    -g api -g gateway -g database -g redis \
    -g logging -g otel -g monitoring -g nginx \
    -g celery -g dev -g docs

# Fullstack: Python API + Next.js frontend
pjkm init my-app -a service \
    -g docker -g api -g database -g supabase \
    -g frontend -g dev

# Interactive TUI wizard
pjkm tui

# List what's available
pjkm list archetypes
pjkm list groups

# Detailed group info
pjkm info docker
pjkm info k8s

# Check your environment
pjkm doctor

# Preview without creating files
pjkm init my-project -a single_package --dry-run
```

## User Defaults

Configure once, use everywhere:

```bash
pjkm defaults --init
```

Edit `~/.pjkmrc.yaml`:

```yaml
author_name: "Your Name"
author_email: "you@example.com"
license: MIT
python_version: "3.13"
archetype: single_package
groups: [dev]

github:
  org: mycompany
  visibility: private
  create_repo: true

group_sources:
  - url: https://github.com/team/shared-groups.git
```

## Archetypes

| Archetype        | Description                                                                        |
| ---------------- | ---------------------------------------------------------------------------------- |
| `single_package` | Standalone Python library with src layout, tests, py.typed                         |
| `service`        | Deployable service with Docker Compose, Makefile, infra/, .env, .secrets, .config/ |
| `poly_repo`      | Multi-package monorepo with packages/, tools/, scripts/, shared infra              |
| `script_tool`    | CLI tool with Typer, `__main__.py`, and CLI tests                                  |

## Package Groups (28)

### Development & Quality

| Group       | What it adds                                             |
| ----------- | -------------------------------------------------------- |
| `dev`       | Meta: linting + testing + typecheck + coverage + ipython |
| `linting`   | ruff, pre-commit, commitizen                             |
| `testing`   | pytest, pytest-cov, pytest-mock, pytest-asyncio          |
| `typecheck` | pyright, mypy                                            |
| `coverage`  | coverage[toml] (requires: testing)                       |
| `security`  | bandit, detect-secrets                                   |
| `docs`      | Sphinx + autodoc + napoleon + autobuild + myst-parser    |
| `jupyter`   | jupyterlab, ipykernel                                    |

### Infrastructure & Containers

| Group    | What it adds                                                       | Scaffold                                                     |
| -------- | ------------------------------------------------------------------ | ------------------------------------------------------------ |
| `docker` | Dockerfile (multi-stage), .dockerignore, devcontainer, compose.dev | Dockerfile, Dockerfile.dev, .devcontainer/, compose.dev.yaml |
| `k8s`    | kubernetes client (requires: docker)                               | k8s/ Kustomize (base + dev/prod overlays), helm/ chart       |
| `nginx`  | — (config only)                                                    | infra/nginx/ config, Dockerfile, compose override            |

### Backend Services

| Group      | What it adds                                             | Scaffold                          |
| ---------- | -------------------------------------------------------- | --------------------------------- |
| `api`      | FastAPI, Uvicorn, pydantic-settings                      | —                                 |
| `gateway`  | slowapi, tenacity, pyrate-limiter, httpx (requires: api) | —                                 |
| `database` | SQLAlchemy async, Alembic, asyncpg                       | alembic/ async migration scaffold |
| `redis`    | redis[hiredis]                                           | —                                 |
| `mongodb`  | Motor, Beanie ODM, pymongo                               | —                                 |
| `supabase` | supabase-py, PostgREST, Auth, Storage, Realtime          | —                                 |

### Task Queues & Messaging

| Group      | What it adds                                     | Scaffold                                         |
| ---------- | ------------------------------------------------ | ------------------------------------------------ |
| `celery`   | Celery + Redis broker + Flower monitoring        | workers/ (app, tasks, beat), compose.celery.yaml |
| `airflow`  | Apache Airflow + Celery/Postgres/Redis providers | —                                                |
| `kafka`    | confluent-kafka, aiokafka, faust-streaming       | —                                                |
| `rabbitmq` | pika, aio-pika, kombu                            | —                                                |

### Observability

| Group        | What it adds                                                         | Scaffold                                                 |
| ------------ | -------------------------------------------------------------------- | -------------------------------------------------------- |
| `logging`    | rich, structlog                                                      | core/logging/ module                                     |
| `otel`       | OpenTelemetry distro + exporters (requires: logging)                 | infra/ OTel collector, Prometheus, Grafana, Loki, Jaeger |
| `monitoring` | prometheus-client, prometheus-fastapi-instrumentator (requires: api) | —                                                        |

### Frontend

| Group      | What it adds                                                   | Scaffold                                                                                  |
| ---------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `frontend` | Next.js 15 + React 19 + Supabase SSR + Tailwind v4 + shadcn/ui | apps/web/ Next.js app, pnpm-workspace.yaml, turbo.json, Supabase client, shadcn/ui config |

### AI & Machine Learning

| Group       | What it adds                                                                                                   |
| ----------- | -------------------------------------------------------------------------------------------------------------- |
| `hf`        | Hugging Face Hub, Transformers, Datasets, Sentence-Transformers, Accelerate, PEFT, bitsandbytes (Linux x86_64) |
| `ml`        | scikit-learn, XGBoost, LightGBM, ONNX Runtime, pandas, numpy, polars, matplotlib, seaborn                      |
| `langchain` | LangChain core + community + OpenAI/Anthropic/HuggingFace providers, LangGraph, LangSmith                      |

## Custom & Remote Groups

```bash
# Create a custom group
pjkm group create quant-data

# Import from pyproject.toml
pjkm group import ../wraquant/pyproject.toml --section market-data

# Share groups via git
pjkm group source add https://github.com/org/pjkm-groups.git
pjkm group sync

# Validate / list
pjkm group validate
pjkm group list
```

## What Gets Generated

Every project includes (from the base template):

- `pyproject.toml` — PDM build system, commitizen, ruff, pytest, coverage
- `.pre-commit-config.yaml` — 17 hooks
- `.trunk/trunk.yaml` — trunk orchestrator config
- `.github/` — PR template, issue templates, dependabot, 9 workflows (CI, release, Docker build, CodeQL, dependency review, labeler)
- `.editorconfig`, `.gitattributes`, `.gitignore`, `.gitlint`, `.python-version`
- `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `README.md`

Groups add on top: Dockerfile + devcontainer, K8s manifests + Helm, Celery workers, Next.js frontend, and more.

## How It Works

```
User input (CLI or TUI)
  -> UserDefaults.load() (merge config files)
  -> ProjectConfig (Pydantic validation)
  -> ProjectEngine.execute(config, extra={github: ...})
       SCAFFOLD:  render base + archetype templates, git init, setup remote
       CONFIGURE: merge group deps into pyproject.toml, write linting configs
       INSTALL:   pdm install, pre-commit install
       VERIFY:    validate expected files exist
  -> ProjectResult
```

## Development

```bash
git clone https://github.com/you/pjkm
cd pjkm
pdm install -G dev
pdm run pytest          # 133 tests
pdm run ruff check .
```

## Architecture

See [`docs_internal/`](docs_internal/) for detailed internal documentation:

- [ARCHITECTURE.md](docs_internal/ARCHITECTURE.md) — package layout, design principles, execution flow
- [TASKS.md](docs_internal/TASKS.md) — task system, DAG phases, 8 built-in tasks
- [GROUPS.md](docs_internal/GROUPS.md) — group schema, all 25 groups, remote sources
- [TEMPLATES.md](docs_internal/TEMPLATES.md) — template layers, 9 fragments

## License

MIT
