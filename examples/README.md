# Examples

These examples show what `pjkm` generates for each archetype.

## Quick Start

```bash
# Install pjkm
pip install pjkm

# Generate a single package
pjkm init my-library --archetype single-package

# Generate a service with OTel observability
pjkm init my-api --archetype service --group logging --group otel

# Generate with all dev tooling
pjkm init my-project --archetype single-package --group dev

# Launch the interactive TUI
pjkm tui

# Set up defaults first (optional)
pjkm defaults --init
```

## Archetype: `single-package`

> A standalone Python library with src layout.

```bash
pjkm init my-library --archetype single-package
```

```
my-library/
├── .editorconfig
├── .git/
├── .gitattributes
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── config.yml
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── .gitignore
├── .gitlint
├── .python-version
├── .readthedocs.yaml
├── .secrets.baseline
├── .pre-commit-config.yaml
├── .trunk/
│   └── trunk.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── my_library/
│       ├── __init__.py
│       └── py.typed
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_my_library.py
```

## Archetype: `service`

> A deployable service with Docker Compose infrastructure, Makefile, and environment config.

```bash
pjkm init my-api --archetype service \
    -g docker -g k8s \
    -g api -g gateway -g database -g nginx \
    -g logging -g otel -g monitoring -g docs \
    -g celery -g frontend -g dev
```

```
my-api/
├── .config/
│   ├── .markdownlint-cli2.yaml
│   └── yamllint.yaml
├── .devcontainer/                 # ← from docker group
│   └── devcontainer.json
├── .dockerignore                  # ← from docker group
├── .editorconfig
├── .env.example
├── .git/
├── .gitattributes
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── config.yml
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows/
│       ├── ci.yml                 # test, lint, typecheck, docs, security
│       └── release.yml
├── .gitignore
├── .gitlint
├── .pre-commit-config.yaml
├── .python-version
├── .readthedocs.yaml
├── .secrets.baseline
├── .secrets.example
├── .trunk/
│   └── trunk.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile                     # ← from docker group (multi-stage)
├── Dockerfile.dev                 # ← from docker group (Node.js + pnpm)
├── LICENSE
├── Makefile
├── README.md
├── alembic/                       # ← from database group
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini                    # ← from database group
├── apps/                          # ← from frontend group
│   └── web/
│       ├── app/
│       │   ├── globals.css
│       │   ├── layout.tsx
│       │   ├── lib/
│       │   │   ├── supabase.ts
│       │   │   └── utils.ts
│       │   └── page.tsx
│       ├── components.json        # shadcn/ui config
│       ├── next.config.ts
│       ├── package.json
│       ├── postcss.config.mjs
│       └── tsconfig.json
├── compose.dev.yaml               # ← from docker group
├── docs/                          # ← from docs group
│   ├── Makefile
│   ├── _static/
│   ├── _templates/
│   ├── api/
│   │   └── index.rst
│   ├── changelog.rst
│   ├── conf.py
│   ├── getting-started.rst
│   └── index.rst
├── helm/                          # ← from k8s group
│   ├── Chart.yaml
│   ├── templates/
│   │   ├── _helpers.tpl
│   │   └── deployment.yaml
│   └── values.yaml
├── infra/
│   ├── README.md
│   ├── compose.celery.yaml        # ← from celery group
│   ├── compose.nginx.yaml         # ← from nginx group
│   ├── compose.otel.yaml          # ← from otel group
│   ├── compose.yaml
│   ├── grafana/
│   │   └── provisioning/
│   │       └── datasources/
│   │           └── datasources.yaml
│   ├── loki/
│   │   └── loki.yaml
│   ├── nginx/                     # ← from nginx group
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   ├── otel/
│   │   └── collector.yaml
│   └── prometheus/
│       └── prometheus.yml
├── k8s/                           # ← from k8s group
│   ├── base/
│   │   ├── configmap.yaml
│   │   ├── deployment.yaml
│   │   ├── hpa.yaml
│   │   ├── ingress.yaml
│   │   ├── kustomization.yaml
│   │   └── service.yaml
│   └── overlays/
│       ├── dev/
│       │   └── kustomization.yaml
│       └── prod/
│           └── kustomization.yaml
├── package.json                   # ← from frontend group (turbo scripts)
├── pnpm-workspace.yaml            # ← from frontend group
├── pyproject.toml
├── scripts/
├── src/
│   └── my_api/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   └── logging/           # ← from logging group
│       │       ├── __init__.py
│       │       └── config.py
│       ├── py.typed
│       └── workers/               # ← from celery group
│           ├── __init__.py
│           ├── beat_schedule.py
│           ├── celery_app.py
│           └── tasks.py
├── tests/
│   ├── __init__.py
│   └── conftest.py
└── turbo.json                     # ← from frontend group
```

## Archetype: `poly-repo`

> A multi-package monorepo with shared infrastructure and tooling.

```bash
pjkm init my-platform --archetype poly-repo
```

```
my-platform/
├── .config/
│   ├── .markdownlint-cli2.yaml
│   └── yamllint.yaml
├── .editorconfig
├── .env.example
├── .git/
├── .gitattributes
├── .github/
│   └── ...
├── .gitignore
├── .gitlint
├── .pre-commit-config.yaml
├── .python-version
├── .secrets.baseline
├── .secrets.example
├── .trunk/
│   └── trunk.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── infra/
│   ├── compose.yaml
│   └── README.md
├── packages/                      # ← sub-packages go here
├── pyproject.toml
├── scripts/
├── src/
│   └── my_platform/
│       ├── __init__.py
│       └── py.typed
├── tests/
│   └── __init__.py
└── tools/                         # ← dev tooling scripts
```

## Archetype: `script-tool`

> A CLI tool with Typer and entry points.

```bash
pjkm init my-tool --archetype script-tool
```

```
my-tool/
├── .editorconfig
├── .git/
├── .gitattributes
├── .github/
│   └── ...
├── .gitignore
├── .gitlint
├── .pre-commit-config.yaml
├── .python-version
├── .secrets.baseline
├── .trunk/
│   └── trunk.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── my_tool/
│       ├── __init__.py
│       ├── __main__.py            # ← python -m my_tool
│       └── cli.py                 # ← Typer CLI
└── tests/
    ├── __init__.py
    └── test_cli.py
```

## Package Groups (28)

Groups add optional dependencies AND scaffolded code/config to any archetype.

### Development & Quality

| Group       | What it adds                                             | Requires                              | Scaffold         |
| ----------- | -------------------------------------------------------- | ------------------------------------- | ---------------- |
| `dev`       | Meta: linting + testing + typecheck + coverage + ipython | linting, testing, typecheck, coverage | —                |
| `linting`   | ruff, pre-commit, commitizen                             | —                                     | —                |
| `testing`   | pytest, pytest-cov, pytest-mock, pytest-asyncio          | —                                     | —                |
| `typecheck` | pyright, mypy                                            | —                                     | —                |
| `coverage`  | coverage[toml]                                           | testing                               | —                |
| `security`  | bandit, detect-secrets                                   | —                                     | —                |
| `docs`      | sphinx, autobuild, napoleon, RTD theme, myst-parser      | —                                     | `docs/` skeleton |
| `jupyter`   | jupyterlab, ipykernel                                    | —                                     | —                |

### Infrastructure & Containers

| Group    | What it adds    | Requires | Scaffold                                                                   |
| -------- | --------------- | -------- | -------------------------------------------------------------------------- |
| `docker` | —               | —        | Dockerfile (multi-stage), Dockerfile.dev, .devcontainer/, compose.dev.yaml |
| `k8s`    | kubernetes      | docker   | k8s/ Kustomize (base + dev/prod overlays), helm/ chart                     |
| `nginx`  | — (config only) | —        | `infra/nginx/` config + Dockerfile                                         |

### Backend Services

| Group      | What it adds                                    | Requires | Scaffold                      |
| ---------- | ----------------------------------------------- | -------- | ----------------------------- |
| `api`      | FastAPI, Uvicorn, pydantic-settings             | —        | —                             |
| `gateway`  | slowapi, tenacity, pyrate-limiter, httpx        | api      | —                             |
| `database` | SQLAlchemy async, Alembic, asyncpg              | —        | `alembic/` migration scaffold |
| `redis`    | redis[hiredis]                                  | —        | —                             |
| `mongodb`  | motor, beanie, pymongo                          | —        | —                             |
| `supabase` | supabase, postgrest, gotrue, storage3, realtime | —        | —                             |

### Task Queues & Messaging

| Group      | What it adds                                     | Requires | Scaffold                                                |
| ---------- | ------------------------------------------------ | -------- | ------------------------------------------------------- |
| `celery`   | celery[redis], flower                            | —        | workers/ (celery_app, tasks, beat), compose.celery.yaml |
| `airflow`  | apache-airflow + celery/postgres/redis providers | —        | —                                                       |
| `kafka`    | confluent-kafka, aiokafka, faust-streaming       | —        | —                                                       |
| `rabbitmq` | pika, aio-pika, kombu                            | —        | —                                                       |

### Observability

| Group        | What it adds                                         | Requires | Scaffold               |
| ------------ | ---------------------------------------------------- | -------- | ---------------------- |
| `logging`    | rich, structlog                                      | —        | `core/logging/` module |
| `otel`       | opentelemetry-distro, -api, -sdk, -exporter-otlp     | logging  | `infra/` OTel stack    |
| `monitoring` | prometheus-client, prometheus-fastapi-instrumentator | api      | —                      |

### Frontend

| Group      | What it adds | Requires | Scaffold                                                                                                    |
| ---------- | ------------ | -------- | ----------------------------------------------------------------------------------------------------------- |
| `frontend` | — (npm deps) | —        | apps/web/ (Next.js 15 + React 19 + Supabase SSR + Tailwind v4 + shadcn/ui), pnpm-workspace.yaml, turbo.json |

### AI & Machine Learning

| Group       | What it adds                                                                     | Requires | Scaffold |
| ----------- | -------------------------------------------------------------------------------- | -------- | -------- |
| `hf`        | Hugging Face Hub, Transformers, Datasets, Accelerate, PEFT, bitsandbytes (Linux) | —        | —        |
| `ml`        | scikit-learn, XGBoost, LightGBM, ONNX Runtime, pandas, numpy, polars             | —        | —        |
| `langchain` | LangChain core + community + OpenAI/Anthropic/HF providers, LangGraph            | —        | —        |

### Custom Groups

You can add your own groups without modifying pjkm:

```bash
# Create a group YAML scaffold
pjkm group create quant-data --name "Quantitative Data"
# -> ./.pjkm/groups/quant_data.yaml  (edit to add dependencies)

# Import groups from an existing pyproject.toml
pjkm group import ../wraquant/pyproject.toml --section market-data

# Share groups via a git repo
pjkm group source add https://github.com/org/pjkm-groups-quant.git

# Validate your custom groups
pjkm group validate

# List everything (built-in + custom + remote)
pjkm group list
```

### Example Combinations

```bash
# Library with full dev tooling + docs
pjkm init my-library -a single-package -g dev -g docs

# API service with full stack
pjkm init my-api -a service \
    -g docker -g k8s \
    -g api -g gateway -g database -g redis \
    -g logging -g otel -g monitoring -g nginx \
    -g celery -g dev -g docs

# Fullstack: Python API + Next.js frontend
pjkm init my-app -a service \
    -g docker -g api -g database -g supabase \
    -g frontend -g dev

# Event-driven microservice
pjkm init my-service -a service \
    -g docker -g api -g kafka -g redis -g mongodb \
    -g logging -g otel -g dev

# Data science tool
pjkm init my-analysis -a script-tool -g jupyter -g logging -g dev

# Data pipeline
pjkm init my-pipeline -a service -g airflow -g database -g redis -g dev

# Or interactively in TUI
pjkm tui
```

### CI Pipeline

The generated `.github/workflows/` directory includes **6 workflows**:

**`ci.yml`** — 5 jobs in parallel:

| Job         | What it does                                | Artifact             |
| ----------- | ------------------------------------------- | -------------------- |
| `test`      | pytest with coverage reporting              | `coverage.xml`       |
| `lint`      | ruff check + format (GitHub annotations)    | —                    |
| `typecheck` | pyright strict mode                         | —                    |
| `docs`      | sphinx-build with `-W` (warnings as errors) | `docs-html/`         |
| `security`  | bandit security scan                        | `bandit-report.json` |

All jobs install only the groups they need (`-G testing`, `-G linting`, etc.) for fast, isolated checks.

**Other workflows:**

| Workflow                | Trigger                                | What it does                                                                 |
| ----------------------- | -------------------------------------- | ---------------------------------------------------------------------------- |
| `release.yml`           | Tag push (`v*`)                        | Build + publish to PyPI via PDM                                              |
| `docker.yml`            | Push to main, tags, Dockerfile changes | Build + push multi-arch images to GHCR                                       |
| `codeql.yml`            | Push/PR to main + weekly               | GitHub CodeQL security analysis                                              |
| `dependency-review.yml` | Pull requests                          | Flag high-severity dependency vulnerabilities                                |
| `labeler.yml`           | Pull requests                          | Auto-label by changed files (python, tests, docs, ci, infra, deps, frontend) |

## CLI Reference

```
pjkm init NAME [-a ARCHETYPE] [-g GROUP...] [-d DIR] [--dry-run] [--author] [--email]
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
