<div align="center">

# pjkm

**Standardized Python project scaffolding for humans and AI agents.**

Create production-ready Python projects in one command — with real source code, not skeletons.
105 composable groups, 22 recipes, an MCP server, and group-aware templates that auto-wire.

[![CI](https://github.com/pr1m8/pjkm/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/pjkm/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/pr1m8/pjkm/graph/badge.svg)](https://codecov.io/gh/pr1m8/pjkm)
[![PyPI](https://img.shields.io/pypi/v/pjkm?color=blue)](https://pypi.org/project/pjkm/)
[![Python](https://img.shields.io/pypi/pyversions/pjkm)](https://pypi.org/project/pjkm/)
[![License](https://img.shields.io/github/license/pr1m8/pjkm)](LICENSE)
[![Docs](https://readthedocs.org/projects/pjkm/badge/?version=latest)](https://pjkm.readthedocs.io)

[Quick Start](#quick-start) · [AI Agents](#for-ai-agents) · [Recipes](#recipes-22) · [Groups](#package-groups-105) · [MCP Server](#mcp-server) · [Docs](https://pjkm.readthedocs.io)

</div>

---

## Why pjkm?

Most scaffolders generate empty skeletons. pjkm generates **wired, running applications** — and it works for both humans and AI agents.

Pick `api + database + redis + auth` and you get a FastAPI app where the lifespan connects your DB, health checks ping Redis, settings read from `.env`, and test fixtures match your stack. Not placeholder comments — real code.

```bash
pip install pjkm
pjkm init my-api --recipe fastapi-service
cd my-api && python -m my_api   # → http://localhost:8000/docs
```

## For AI Agents

pjkm is designed as **infrastructure for AI coding agents**. It provides the standardized project structures that agents need to operate in sandboxes:

- **Predictable layout** — agents know where code goes (`src/*/api/app.py`, `src/*/core/settings.py`)
- **Known entry points** — `python -m <project>` always starts the app
- **Typed configuration** — Pydantic Settings, not raw env vars
- **Health checks** — `/health` and `/ready` for sandbox orchestration
- **Test fixtures** — `conftest.py` with async client, DB session, Redis client
- **Reproducible** — same recipe = same output, every time

### MCP Server

pjkm exposes its full engine as an MCP server. AI agents can scaffold projects programmatically:

```bash
pip install pjkm[mcp]
python -m pjkm.mcp        # stdio server for Claude Desktop
pjkm-mcp                  # same thing
```

**Claude Desktop** — add to config:
```json
{"mcpServers": {"pjkm": {"command": "python", "args": ["-m", "pjkm.mcp"]}}}
```

**LangChain / LangGraph**:
```python
from langchain_mcp_adapters import MultiServerMCPClient

async with MultiServerMCPClient(
    {"pjkm": {"command": "python", "args": ["-m", "pjkm.mcp"]}}
) as client:
    tools = client.get_tools()
    # Agent can now: init_project, list_recipes, add_groups, preview, adopt
```

**10 MCP tools**: `init_project`, `add_groups`, `preview_project`, `list_recipes`, `list_groups`, `get_group_info`, `search_registry`, `adopt_project`, `project_status`, `create_recipe`

**7 MCP resources**: `pjkm://recipes`, `pjkm://groups`, `pjkm://groups/{id}`, `pjkm://registry`, `pjkm://archetypes`, `pjkm://blueprints`, `pjkm://categories`

**3 MCP prompts**: `project_advisor`, `architecture_advisor`, `agent_scaffold`

### Agent Recipes

```bash
pjkm init my-agent    --recipe ai-agent          # LangGraph agent with tools + memory
pjkm init my-rag      --recipe rag-service        # RAG API with vector store + embeddings
pjkm init my-platform --recipe agent-platform     # multi-agent with eval + monitoring
```

The `ai-agent` recipe generates a complete LangGraph agent:

```
src/my_agent/agent/
├── graph.py       # StateGraph with tool calling, routing, loop protection
├── state.py       # TypedDict state with message history
├── tools.py       # @tool functions (auto-includes search if selected)
└── prompts.py     # ChatPromptTemplate collection
```

### 29 AI/ML Groups

| Group | What it provides |
|-------|-----------------|
| `agents` | LangGraph agent orchestration with tools + memory |
| `langchain` | LangChain core + OpenAI/Anthropic/HF providers |
| `langgraph` | LangGraph SDK + prebuilt + checkpointer + langmem |
| `llm_providers` | OpenAI, Anthropic, Google, Ollama, LiteLLM, Instructor |
| `claude_sdk` | Anthropic SDK with tool use, batches, streaming |
| `openai_sdk` | OpenAI SDK with assistants, structured outputs |
| `mcp_tools` | MCP protocol + langchain adapters |
| `agent_protocols` | MCP + A2A/ACP + SSE for agent interop |
| `rag` | Retrieval-augmented generation pipeline |
| `vector_stores` | Qdrant, Chroma, pgvector, FAISS, BM25 |
| `embeddings` | sentence-transformers, tiktoken, Cohere, Voyage |
| `search_tools` | Tavily, DuckDuckGo, SerpAPI, Wikipedia, arXiv |
| `eval` | LangSmith + ragas + deepeval |
| `guardrails` | Guardrails AI + NeMo Guardrails |
| `hf` | HuggingFace Hub, Transformers, Datasets, PEFT |
| `torch` | PyTorch + torchvision + torchaudio |
| `ml` | scikit-learn, XGBoost, LightGBM, ONNX, pandas, polars |

## Features

| | |
|---|---|
| **105 groups** | Composable dependency + code bundles across 8 categories |
| **22 recipes** | One command → fully configured project |
| **Group-aware templates** | Fragments auto-wire based on selection |
| **Real source code** | API routes, DB models, auth, Redis, LangGraph agent — not stubs |
| **MCP server** | AI agents scaffold projects via Model Context Protocol |
| **22 CI workflows** | Test, lint, Docker, CodeQL, deploy, auto-merge |
| **Community registry** | `pjkm search` / `pjkm install` |
| **Workspace** | Multi-service platforms with shared infra |
| **Adopt** | Scan existing projects, suggest groups |

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
pjkm recipe-create my-stack -g api -g database -g redis   # save custom recipe
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

## CLI Reference

```
pjkm init NAME [-a ARCH] [-g GROUP...] [--recipe NAME] [--dry-run]
pjkm add -g GROUP... [-d DIR]
pjkm update | upgrade | link TOOL
pjkm preview [ARCH] [-g GROUP...] [--recipe NAME]
pjkm adopt [--apply] | status
pjkm workspace NAME [--blueprint NAME | -s name:template...]
pjkm list [archetypes|groups] | info GROUP | doctor
pjkm recipe [NAME] [--show] | recipe-create NAME -g GROUP...
pjkm recommend ARCH [--preset NAME]
pjkm search [QUERY] | install PACK | uninstall PACK | installed
pjkm group create|import|validate|list|sync
pjkm group source add|list|remove
pjkm defaults [--init] | tui
```

## Development

```bash
git clone https://github.com/pr1m8/pjkm
cd pjkm
pdm install -G dev -G mcp -G docs
pdm run pytest                    # 231 tests
pdm run ruff check src tests
pdm run sphinx-build docs/ docs/_build/html
```

## License

MIT
