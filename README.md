<div align="center">

# pjkm

**Python project scaffolder with composable templates, 105 package groups, and a community registry.**

[![CI](https://github.com/pr1m8/pjkm/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/pjkm/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/pr1m8/pjkm/graph/badge.svg)](https://codecov.io/gh/pr1m8/pjkm)
[![PyPI](https://img.shields.io/pypi/v/pjkm?color=blue)](https://pypi.org/project/pjkm/)
[![Python](https://img.shields.io/pypi/pyversions/pjkm)](https://pypi.org/project/pjkm/)
[![License](https://img.shields.io/github/license/pr1m8/pjkm)](LICENSE)
[![Docs](https://readthedocs.org/projects/pjkm/badge/?version=latest)](https://pjkm.readthedocs.io)

[Quick Start](#quick-start) · [Recipes](#recipes-22) · [Groups](#package-groups-105) · [Workspace](#workspace) · [Docs](https://pjkm.readthedocs.io)

</div>

---

## Why pjkm?

Most project generators give you a skeleton. pjkm gives you a **running application**.

Pick `api + database + redis + auth` and you get a FastAPI app where the lifespan connects your DB, health checks ping Redis, settings read from `.env`, and test fixtures match your stack. Not placeholder comments — real wired code.

```bash
pjkm init my-api --recipe fastapi-service
cd my-api && python -m my_api   # → http://localhost:8000/docs
```

## Features

| | |
|---|---|
| **105 groups** | Composable dependency + code bundles across 8 categories |
| **22 recipes** | One command → fully configured project |
| **Group-aware templates** | Fragments auto-wire based on selection |
| **Real source code** | API routes, DB models, auth, Redis client — not stubs |
| **22 CI workflows** | Test, lint, Docker, CodeQL, deploy, auto-merge |
| **Community registry** | `pjkm search` / `pjkm install` |
| **Workspace** | Multi-service platforms with shared infra |
| **Adopt** | Scan existing projects, suggest groups |
| **18 Sphinx extensions** | AutoAPI, Furo, mermaid, copybutton |
| **CLI + TUI** | Typer CLI and Textual interactive wizard |

## Install

```bash
pip install pjkm
```

## Quick Start

```bash
# From a recipe
pjkm init my-api --recipe fastapi-service

# From groups
pjkm init my-lib -a single-package -g dev -g docs -g coverage

# Preview first
pjkm preview --recipe saas-backend

# Adopt existing project
cd ~/my-project && pjkm adopt --apply

# Interactive
pjkm tui
```

## Recipes (22)

```bash
pjkm recipe                          # browse all
pjkm recipe ai-agent --show          # details
pjkm init myapp --recipe <name>      # create
```

<details>
<summary><strong>All 22 recipes</strong></summary>

| Recipe | Archetype | Description |
|--------|-----------|-------------|
| `python-lib` | single-package | Publish-ready library with CI/CD |
| `fastapi-service` | service | Production API with DB, auth, observability |
| `ai-agent` | single-package | LangGraph agent with tools, memory, MCP |
| `rag-service` | service | RAG API with vector store + embeddings |
| `agent-platform` | service | Multi-agent with eval + monitoring |
| `ml-pipeline` | service | ML training with experiment tracking |
| `data-analysis` | single-package | Notebooks + visualization |
| `cli-tool` | script-tool | Polished CLI with Typer |
| `fullstack-web` | service | API + Next.js + auth + infra |
| `monorepo` | poly-repo | Multi-package with shared CI |
| `scraper` | service | Crawling pipeline |
| `fintech` | service | Payments, compliance, monitoring |
| `api-microservice` | service | Lightweight async service + caching |
| `discord-bot` | single-package | Async bot with scheduling |
| `etl-pipeline` | service | ETL with queues |
| `saas-backend` | service | Multi-tenant with billing, email, WS |
| `document-processor` | service | Doc ingestion, OCR, PDF |
| `media-pipeline` | service | Video/audio/image with ffmpeg |
| `realtime-api` | service | WebSocket + SSE + rate limiting |
| `file-service` | service | S3 uploads with thumbnails |
| `scraper-full` | service | Full platform + MinIO + Celery |
| `tui-app` | script-tool | Textual terminal UI |

</details>

## What Gets Generated

`pjkm init my-api --recipe fastapi-service` produces:

```
my-api/
├── .env.example                    ← only vars for your groups
├── .github/workflows/              ← 15+ CI/CD workflows
├── Dockerfile                      ← multi-stage production build
├── Makefile + make/*.mk            ← modular build targets
├── alembic/                        ← database migrations
├── docs/                           ← Sphinx + Furo + AutoAPI
├── pyproject.toml                  ← deps organized by group
├── tests/
│   ├── conftest.py                 ← fixtures: app, client, db, redis
│   ├── test_health.py              ← endpoint tests
│   └── test_settings.py            ← settings validation
└── src/my_api/
    ├── __main__.py                 ← python -m my_api
    ├── api/
    │   ├── app.py                  ← FastAPI factory + middleware
    │   ├── deps.py                 ← Depends(get_db), Depends(get_redis)
    │   ├── middleware.py           ← request ID, timing headers
    │   ├── pagination.py           ← cursor/offset pagination
    │   └── routes/{health,v1}.py   ← /health pings DB+Redis
    ├── auth/{jwt,deps}.py          ← JWT + Bearer dependency
    ├── core/
    │   ├── database.py             ← async SQLAlchemy + session factory
    │   ├── lifespan.py             ← auto-wires DB + Redis startup/shutdown
    │   ├── logging/config.py       ← structlog + Rich
    │   ├── redis.py                ← async client + pool + health check
    │   └── settings.py             ← Pydantic Settings ← .env
    └── models/{__init__,mixins}.py ← Base, timestamps, UUID PKs, soft-delete
```

> **Group-aware**: lifespan, health checks, deps, settings, .env, and test fixtures all dynamically compose based on which groups you selected.

## Package Groups (105)

```bash
pjkm list groups        # categorized view
pjkm info database      # detailed view with deps + scaffolding
```

| Category | Count | Highlights |
|----------|-------|-----------|
| **Core Dev** | 23 | testing, linting, typecheck, coverage, profiling, Textual TUI |
| **AI / ML** | 29 | LangGraph agents, RAG, embeddings, eval, Claude/OpenAI SDK, MCP, guardrails |
| **Web & API** | 18 | FastAPI, auth, WebSocket, SSE, rate limiting, payments, email |
| **Infrastructure** | 18 | Docker, K8s, OTel, Celery, Terraform, S3, MinIO |
| **Data & Storage** | 9 | PostgreSQL, Redis, MongoDB, Kafka, Elasticsearch |
| **Docs & Meta** | 4 | Sphinx (18 extensions), MkDocs Material |
| **Frontend** | 2 | Next.js, Vite + React |
| **Platform** | 2 | macOS, Linux |

## Workspace

Scaffold multi-service platforms:

```bash
pjkm workspace my-platform --blueprint microservices
# Creates: api/ + jobs/ + site/ + shared/ + docker-compose + VS Code workspace

pjkm workspace my-platform --blueprint data-platform
# Creates: api/ + ingestion/ + warehouse/ + orchestration/ + dashboards/ + ...
```

**Blueprints**: `microservices` · `data-platform` · `scraping-platform` · `ml-platform` · `fullstack`

Each service is a full pjkm project. Includes shared `docker-compose.yml` (Postgres + Redis), root `Makefile`, VS Code `.code-workspace`, and GitHub Actions CI.

## Registry

```bash
pjkm search django          # browse community packs
pjkm install pjkm-django    # install
pjkm installed               # list installed
```

## Adopt Existing Projects

```bash
cd ~/my-existing-api
pjkm adopt                  # detects 60+ deps, 20 file patterns
pjkm adopt --apply          # applies matching groups
pjkm status                 # shows groups, detects drift
```

## Configuration

```bash
pjkm defaults --init        # create ~/.pjkmrc.yaml
```

```yaml
author_name: "Your Name"
author_email: "you@example.com"
python_version: "3.13"
archetype: single-package
groups: [dev]
github:
  org: mycompany
  create_repo: true
```

## Development

```bash
git clone https://github.com/pr1m8/pjkm
cd pjkm
pdm install -G dev -G docs
pdm run pytest                    # 197 tests
pdm run ruff check src tests
pdm run sphinx-build docs/ docs/_build/html
```

## Documentation

Full docs at [**pjkm.readthedocs.io**](https://pjkm.readthedocs.io):

- [Quick Start](https://pjkm.readthedocs.io/en/latest/quickstart.html)
- [Recipes](https://pjkm.readthedocs.io/en/latest/recipes.html)
- [Groups](https://pjkm.readthedocs.io/en/latest/groups.html)
- [Templates](https://pjkm.readthedocs.io/en/latest/templates.html)
- [Workspace](https://pjkm.readthedocs.io/en/latest/workspace.html)
- [Pack Authoring](https://pjkm.readthedocs.io/en/latest/pack-authoring.html)
- [API Reference](https://pjkm.readthedocs.io/en/latest/autoapi/index.html)

## License

MIT
