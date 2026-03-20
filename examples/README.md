# Examples

These examples show what `pjkm` generates for each archetype and recipe.

## Quick Start

```bash
# Install pjkm
pip install pjkm

# Use a recipe — one command, everything configured
pjkm init my-api --recipe fastapi-service

# Or pick groups manually
pjkm init my-lib -a single-package -g dev -g docs -g coverage

# Preview what you'd get without creating anything
pjkm preview --recipe saas-backend

# Browse and install community group packs
pjkm search django
pjkm install pjkm-django

# Launch the interactive TUI
pjkm tui
```

## Recipes (22 pre-configured combos)

```bash
pjkm init my-lib      --recipe python-lib          # publish-ready library
pjkm init my-api      --recipe fastapi-service      # production API
pjkm init my-agent    --recipe ai-agent             # LangChain/LangGraph agent
pjkm init my-ml       --recipe ml-pipeline          # ML training pipeline
pjkm init my-data     --recipe data-analysis        # notebooks + viz
pjkm init my-cli      --recipe cli-tool             # polished CLI
pjkm init my-app      --recipe fullstack-web        # API + Next.js frontend
pjkm init my-mono     --recipe monorepo             # multi-package repo
pjkm init my-scraper  --recipe scraper              # crawling pipeline
pjkm init my-fin      --recipe fintech              # payments + compliance
pjkm init my-micro    --recipe api-microservice     # lightweight service
pjkm init my-bot      --recipe discord-bot          # async bot
pjkm init my-etl      --recipe etl-pipeline         # ETL with scheduling
pjkm init my-saas     --recipe saas-backend         # multi-tenant SaaS
pjkm init my-docs     --recipe document-processor   # doc ingestion pipeline
pjkm init my-media    --recipe media-pipeline       # video/audio/image processing
pjkm init my-rt       --recipe realtime-api         # WebSocket + SSE + rate limiting
pjkm init my-files    --recipe file-service         # S3 uploads + thumbnails
pjkm init my-crawler  --recipe scraper-full         # full scraping platform
pjkm init my-tui      --recipe tui-app              # Textual terminal UI
pjkm init my-rag      --recipe rag-service          # RAG API with vector store
pjkm init my-agents   --recipe agent-platform       # multi-agent with eval
```

## What gets generated

### `pjkm init my-api --recipe fastapi-service`

A production-ready FastAPI service with 17 groups applied:

```
my-api/
├── .env.example                          # all env vars documented
├── .github/
│   ├── dependabot.yml
│   ├── release-drafter.yml
│   ├── ISSUE_TEMPLATE/                   # YAML form-based templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       ├── auto-merge.yml                # auto-merge Dependabot
│       ├── changelog.yml                 # release notes via git-cliff
│       ├── ci.yml                        # test, lint, typecheck, docs, security
│       ├── codeql.yml                    # GitHub security analysis
│       ├── dependency-review.yml         # vulnerability scanning
│       ├── docker.yml                    # multi-arch GHCR build
│       ├── docker-security.yml           # Hadolint + Trivy scan
│       ├── draft-release.yml             # draft release notes
│       ├── labeler.yml                   # auto-label PRs
│       ├── lock.yml                      # lock stale threads
│       ├── migration-check.yml           # Alembic CI check
│       ├── pages.yml                     # deploy docs to GitHub Pages
│       ├── pr-size.yml                   # PR size labels
│       ├── release.yml                   # PyPI publish
│       ├── scorecard.yml                 # OpenSSF security score
│       ├── stale.yml                     # stale issue management
│       └── test-matrix.yml              # OS + Python version matrix
├── Dockerfile                            # multi-stage production build
├── Dockerfile.dev                        # dev container with hot-reload
├── .devcontainer/devcontainer.json
├── Makefile
├── alembic/                              # database migrations
│   ├── env.py                            # async SQLAlchemy config
│   └── versions/
├── compose.dev.yaml
├── infra/
│   ├── compose.yaml
│   ├── compose.otel.yaml                 # OTel collector + Grafana + Loki
│   ├── compose.redis.yaml
│   └── compose.postgres.yaml
├── pyproject.toml                        # all deps organized by group
├── src/
│   └── my_api/
│       ├── __init__.py
│       ├── api/                          # ← from api group
│       │   ├── app.py                    # FastAPI factory, CORS, middleware
│       │   ├── deps.py                   # shared dependencies (settings, DB, etc.)
│       │   ├── middleware.py             # request ID, timing
│       │   └── routes/
│       │       ├── health.py             # /health + /ready endpoints
│       │       └── v1.py                 # /api/v1/ routes
│       ├── auth/                         # ← from auth group
│       │   ├── __init__.py
│       │   ├── jwt.py                    # create/decode JWT tokens
│       │   └── deps.py                   # get_current_user dependency
│       ├── core/
│       │   ├── database.py               # ← async SQLAlchemy engine + sessions
│       │   ├── lifespan.py               # ← startup/shutdown hooks
│       │   ├── logging/                  # ← structlog + Rich
│       │   │   ├── __init__.py
│       │   │   └── config.py
│       │   ├── redis.py                  # ← async Redis client + pool
│       │   └── settings.py               # ← Pydantic Settings + .env
│       ├── models/                       # ← from database group
│       │   ├── __init__.py               # import all models for Alembic
│       │   └── mixins.py                 # timestamps, UUID PK, soft-delete
│       └── py.typed
└── tests/
    ├── __init__.py
    └── conftest.py
```

### `pjkm init my-agent --recipe ai-agent`

An AI agent with LangChain, vector stores, and MCP tools:

```bash
# What you get:
# - LangChain + LangGraph + providers (OpenAI, Anthropic, HF)
# - Vector store support (Chroma, FAISS, Qdrant, Pinecone)
# - MCP tools (mcp, httpx-sse)
# - Document parsing (unstructured, pdfplumber, python-docx)
# - Search tools (DuckDuckGo, SerpAPI, Tavily)
# - Redis for caching/sessions
# - Structlog logging
```

### `pjkm init my-saas --recipe saas-backend`

Multi-tenant SaaS with everything:

```bash
# Groups: api, auth, database, redis, caching, docker, logging, otel,
#         monitoring, payments, email, websocket, scheduling,
#         error_tracking, makefile, github_templates, ci_cd, coverage, security
#
# You get:
# - JWT auth + Bearer dependency
# - Stripe/payment integration deps
# - Email (aiosmtplib + templates)
# - WebSocket (real-time)
# - Job scheduling (APScheduler)
# - Error tracking (Sentry)
# - Full CI/CD with deploy workflows
```

## Package Groups (105 across 8 categories)

```bash
pjkm list groups    # see all groups organized by category
pjkm info <group>   # detailed view of a specific group
```

### Core Dev (23)
dev, dev_extended, linting, testing, testing_extended, typecheck, coverage, security,
code_quality, profiling, debugging, refactoring, reporting, scripts, towncrier,
pydantic_extra, config_mgmt, cli_rich, async_tools, http_client, logging,
textual_tui, file_utils

### AI / ML (29)
langchain, langchain_providers, langgraph, hf, ml, torch, mcp_tools, agents,
dataviz, notebook, jupyter, search_tools, doc_parsing, vector_stores, embeddings,
rag, eval, langsmith, llm_providers, claude_sdk, openai_sdk, agent_protocols,
guardrails, translation, finance, image, video, audio, ocr

### Web & API (18)
api, gateway, auth, graphql, grpc, web_scraping, crawling, streamlit,
gradio, messaging, payments, error_tracking, websocket, email, pdf,
file_upload, rate_limit, sse

### Data & Storage (9)
database, redis, mongodb, kafka, rabbitmq, neo4j, elasticsearch, supabase, caching

### Infrastructure (18)
docker, k8s, nginx, otel, otel_instrumentations, monitoring, celery, airflow,
aws, google_cloud, makefile, ci_cd, task_queue, scheduling, s3, minio,
terraform, pulumi

### Frontend (2)
frontend (Next.js + pnpm), frontend_vite (Vite + React + TS)

### Docs & Meta (4)
docs, docs_mkdocs, github_templates, submodules

### Platform (2)
mac, linux

## Registry — Community Group Packs

```bash
# Browse
pjkm search                # list all packs
pjkm search django          # search by keyword
pjkm search ml              # search by tag

# Install
pjkm install pjkm-django    # downloads + registers group source
pjkm installed               # see what's installed
pjkm uninstall pjkm-django  # remove

# After install, new groups appear everywhere:
pjkm list groups             # includes installed pack groups
pjkm init myapp -g django    # use them in projects
```

Available packs: pjkm-django, pjkm-aws-lambda, pjkm-ml-ops, pjkm-data-eng,
pjkm-quant, pjkm-iot, pjkm-gamedev, pjkm-auth-providers, pjkm-observability, pjkm-cms

## Presets

```bash
pjkm recommend service               # show all presets for an archetype
pjkm recommend service -p minimal    # 4 groups
pjkm recommend service -p standard   # 13 groups
pjkm recommend service -p full       # 23 groups
pjkm recommend service -p ai         # 19 AI-focused groups
pjkm recommend service -p data       # 15 data science groups
pjkm recommend service -p web        # 16 web/frontend groups
```

## Workspace — Multi-Service Platforms

```bash
# Use a blueprint
pjkm workspace my-platform --blueprint microservices    # api + worker + web + shared
pjkm workspace my-platform --blueprint data-platform    # 8 services
pjkm workspace my-platform --blueprint fullstack        # api + worker + web + integrations + shared

# Or pick services
pjkm workspace my-platform -s api:api -s scraper:scraper -s site:web -s shared:lib

# Generates: VS Code workspace, docker-compose, Makefile, GitHub Actions CI
# Then: code my-platform.code-workspace && make install && make up
```

Blueprints: microservices, data-platform, scraping-platform, ml-platform, fullstack

## CI Pipeline (15 workflows)

Every generated project includes up to 15 GitHub Actions workflows:

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| ci.yml | push/PR | test, lint, typecheck, docs, security (5 parallel jobs) |
| release.yml | tag `v*` | build + publish to PyPI |
| docker.yml | push/PR | multi-arch Docker build + push to GHCR |
| codeql.yml | push/PR/weekly | GitHub CodeQL security analysis |
| dependency-review.yml | PR | flag vulnerable dependencies |
| labeler.yml | PR | auto-label by changed files |
| stale.yml | daily cron | auto-close stale issues/PRs |
| changelog.yml | release | generate changelog via git-cliff |
| pr-size.yml | PR | label PRs by size (xs/s/m/l/xl) |
| test-matrix.yml | push/PR | OS + Python version matrix |
| auto-merge.yml | PR | auto-merge Dependabot minor/patch |
| draft-release.yml | push to main | draft release notes |
| pages.yml | push (docs) | deploy docs to GitHub Pages |
| lock.yml | weekly cron | lock stale issue threads |
| scorecard.yml | push/weekly | OpenSSF Scorecard security |

Plus group-specific workflows: docker-security, k8s-lint, migration-check, docs-preview, frontend CI, deploy-staging, deploy-prod.

## CLI Reference

```
# Project lifecycle
pjkm init NAME [-a ARCHETYPE] [-g GROUP...] [--recipe NAME] [-d DIR] [--dry-run]
pjkm add -g GROUP... [-d DIR]
pjkm update [-d DIR] [--dry-run]
pjkm upgrade [-g GROUP...] [--latest] [--refresh-tools] [--dry-run]
pjkm link TOOL [-d DIR] [--dry-run]
pjkm preview [ARCHETYPE] [-g GROUP...] [--recipe NAME]

# Discovery
pjkm list [archetypes|groups]
pjkm info GROUP_ID
pjkm recommend ARCHETYPE [--preset NAME]
pjkm recipe [NAME] [--show]
pjkm doctor

# Registry
pjkm search [QUERY] [--refresh]
pjkm install PACK_NAME [--no-sync]
pjkm uninstall PACK_NAME
pjkm installed

# Group management
pjkm group create ID [--name] [--dir]
pjkm group import PYPROJECT [--section...] [--dir]
pjkm group validate [PATH]
pjkm group list
pjkm group sync [NAME]
pjkm group source add URL [--name] [--path] [--ref]
pjkm group source list
pjkm group source remove NAME

# Adopt existing projects
pjkm adopt [--dir DIR] [--apply]
pjkm status [--dir DIR]

# Workspace (multi-service platforms)
pjkm workspace NAME [-s name:template...] [--blueprint NAME] [--dry-run]

# Config
pjkm defaults [--init] [--global]
pjkm tui
```
