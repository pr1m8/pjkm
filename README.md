# pjkm

Python project scaffolder with composable templates, 91 package groups, and a community registry.

## Features

- **105 package groups** across 8 categories — API, database, Redis, auth, ML, LangChain, Docker, K8s, and more
- **22 recipes** — one command to scaffold a FastAPI service, AI agent, SaaS backend, ML pipeline, etc.
- **Workspace command** — scaffold multi-service platforms with shared infra, VS Code workspace, docker-compose
- **Group-aware templates** — fragments auto-wire based on what you select (DB + Redis + auth = fully connected app)
- **Source code scaffolding** — generates real Python modules, not just dependency lists
- **Community registry** — `pjkm search django` / `pjkm install pjkm-django`
- **Adopt existing projects** — `pjkm adopt` scans your project and suggests groups
- **22 GitHub Actions workflows** — CI, release, Docker, CodeQL, auto-merge, deploy, and more
- **4 archetypes** — single-package, service, poly-repo, script-tool
- **CLI + TUI** — Typer CLI and Textual TUI wizard

## Install

```bash
pip install pjkm
```

## Quick Start

```bash
# Use a recipe — one command, fully configured
pjkm init my-api --recipe fastapi-service
cd my-api && python -m my_api   # it runs

# Or pick groups manually
pjkm init my-lib -a single-package -g dev -g docs -g coverage

# Preview before creating
pjkm preview --recipe saas-backend

# Adopt an existing project
cd ~/existing-project
pjkm adopt               # detects FastAPI, SQLAlchemy, Redis, etc.
pjkm adopt --apply       # applies detected groups

# Interactive wizard
pjkm tui
```

## Recipes

```bash
pjkm init myapp --recipe <name>
```

| Recipe | What you get |
|--------|-------------|
| `python-lib` | Publish-ready library with full CI/CD |
| `fastapi-service` | Production API with DB, auth, observability |
| `ai-agent` | LangChain/LangGraph agent with vector stores |
| `ml-pipeline` | ML training with experiment tracking |
| `data-analysis` | Notebooks + visualization workspace |
| `cli-tool` | Polished CLI with rich output |
| `fullstack-web` | API + Next.js frontend + auth + infra |
| `monorepo` | Multi-package with shared CI |
| `scraper` | Crawling pipeline with storage |
| `fintech` | Payments, compliance, monitoring |
| `api-microservice` | Lightweight async service with caching |
| `discord-bot` | Async bot with scheduling |
| `etl-pipeline` | ETL with queues and scheduling |
| `saas-backend` | Multi-tenant with billing, email, websocket |
| `document-processor` | Doc ingestion, OCR, PDF generation |
| `media-pipeline` | Video/audio/image processing with ffmpeg |
| `realtime-api` | WebSocket + SSE + rate limiting |
| `file-service` | S3 uploads with thumbnails and metadata |
| `scraper-full` | Full scraping platform with MinIO, Celery, Prometheus |
| `tui-app` | Textual terminal UI with async + config |
| `rag-service` | RAG API with vector store, embeddings, doc ingestion |
| `agent-platform` | Multi-agent with eval, observability, monitoring |

## What gets generated

`pjkm init my-api --recipe fastapi-service` produces:

```
my-api/
├── .env.example                    # only vars for your selected groups
├── .github/workflows/              # 15+ CI/CD workflows
├── Dockerfile                      # multi-stage production build
├── Makefile
├── alembic/                        # database migrations
├── pyproject.toml                  # deps organized by group
└── src/my_api/
    ├── __main__.py                 # python -m my_api starts uvicorn
    ├── api/
    │   ├── app.py                  # FastAPI factory + CORS + middleware
    │   ├── deps.py                 # get_db(), get_redis(), get_settings()
    │   ├── middleware.py           # request ID, timing
    │   ├── pagination.py           # paginated response utility
    │   └── routes/
    │       ├── health.py           # /health + /ready (pings DB, Redis)
    │       └── v1.py
    ├── auth/
    │   ├── jwt.py                  # create/decode tokens
    │   └── deps.py                 # get_current_user dependency
    ├── core/
    │   ├── database.py             # async SQLAlchemy engine + sessions
    │   ├── lifespan.py             # auto-connects DB + Redis on startup
    │   ├── logging/                # structlog + Rich
    │   ├── redis.py                # async client + connection pool
    │   └── settings.py             # Pydantic Settings from .env
    └── models/
        ├── __init__.py             # model registry for Alembic
        └── mixins.py               # timestamps, UUID PKs, soft-delete
```

Templates are **group-aware** — the lifespan, health checks, deps, settings, and .env all dynamically compose based on which groups you selected.

## Package Groups (91)

```bash
pjkm list groups    # browse all, organized by category
pjkm info <group>   # detailed view
```

| Category | Groups | Examples |
|----------|--------|---------|
| Core Dev (23) | dev, linting, testing, typecheck, coverage, security, ... | code quality, profiling, Textual TUI |
| AI / ML (29) | langchain, langgraph, agents, hf, ml, torch, ... | RAG, eval, embeddings, guardrails, MCP |
| Web & API (18) | api, auth, websocket, sse, rate_limit, ... | payments, email, file upload |
| Infrastructure (18) | docker, k8s, otel, celery, ci_cd, s3, ... | terraform, pulumi, MinIO |
| Data & Storage (9) | database, redis, mongodb, kafka, elasticsearch, ... | caching, neo4j |
| Docs & Meta (4) | docs, docs_mkdocs, github_templates, submodules | |
| Frontend (2) | frontend (Next.js), frontend_vite (Vite+React) | |
| Platform (2) | mac, linux | |

## Registry

Browse and install community group packs:

```bash
pjkm search                    # list all packs
pjkm search django             # search
pjkm install pjkm-django       # install
pjkm installed                 # see what's installed
pjkm uninstall pjkm-django     # remove
```

## Project Status

```bash
pjkm status              # show applied groups, detect dep drift
pjkm adopt               # scan project, suggest groups
pjkm upgrade              # update deps to latest group definitions
pjkm upgrade --dry-run    # preview changes
```

## User Defaults

```bash
pjkm defaults --init     # create .pjkmrc.yaml
```

```yaml
author_name: "Your Name"
author_email: "you@example.com"
license: MIT
python_version: "3.13"
archetype: single-package
groups: [dev]

github:
  org: mycompany
  visibility: private
  create_repo: true
```

## CLI Reference

```
pjkm init NAME [-a ARCH] [-g GROUP...] [--recipe NAME] [--dry-run]
pjkm add -g GROUP... [-d DIR]
pjkm update [-d DIR] [--dry-run]
pjkm upgrade [-g GROUP...] [--latest] [--dry-run]
pjkm link TOOL [-d DIR]
pjkm preview [ARCH] [-g GROUP...] [--recipe NAME]

pjkm adopt [--dir DIR] [--apply]
pjkm status [--dir DIR]

pjkm list [archetypes|groups]
pjkm info GROUP_ID
pjkm recommend ARCH [--preset NAME]
pjkm recipe [NAME] [--show]
pjkm doctor

pjkm search [QUERY]
pjkm install PACK
pjkm uninstall PACK
pjkm installed

pjkm adopt [--dir DIR] [--apply]
pjkm status [--dir DIR]
pjkm workspace NAME [-s name:template...] [--blueprint NAME]

pjkm group create|import|validate|list|sync
pjkm group source add|list|remove

pjkm defaults [--init] [--global]
pjkm tui
```

## Development

```bash
git clone https://github.com/pr1m8/pjkm
cd pjkm
pdm install -G dev
pdm run pytest        # 197 tests
pdm run ruff check .
```

## Architecture

See [`docs_internal/`](docs_internal/) and [`CLAUDE.md`](CLAUDE.md) for internals:

- [ARCHITECTURE.md](docs_internal/ARCHITECTURE.md) — package layout, execution flow
- [TASKS.md](docs_internal/TASKS.md) — DAG task system, 9 built-in tasks
- [GROUPS.md](docs_internal/GROUPS.md) — group schema, 105 groups
- [TEMPLATES.md](docs_internal/TEMPLATES.md) — template layers, 34 fragments
- [PACK_AUTHORING.md](docs_internal/PACK_AUTHORING.md) — create and publish group packs

## License

MIT
