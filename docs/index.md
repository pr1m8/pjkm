# pjkm

**Python project scaffolder for humans and agents.**

Build fully configured, production-ready Python projects in one command. 105 composable groups, 22 recipes, group-aware templates that auto-wire, and an MCP server so AI agents can scaffold projects too.

```{toctree}
:maxdepth: 2
:caption: Getting Started

quickstart
recipes
presets
agents
```

```{toctree}
:maxdepth: 2
:caption: User Guide

groups
templates
workspace
registry
adopt
defaults
mcp-server
```

```{toctree}
:maxdepth: 2
:caption: Reference

cli
architecture
pack-authoring
changelog
```

```{toctree}
:maxdepth: 2
:caption: API Reference

autoapi/index
```

## How It Works

```{mermaid}
graph LR
    A[User / AI Agent] -->|recipe or groups| B[pjkm Engine]
    B --> C[Base Template]
    B --> D[Archetype Template]
    B --> E[Fragment Templates]
    C --> F[Project]
    D --> F
    E --> F
    F --> G[pyproject.toml]
    F --> H[src/ with real code]
    F --> I[.github/workflows/]
    F --> J[Dockerfile + infra/]
    F --> K[tests/ with fixtures]
```

## Quick Start

::::{tab-set}

:::{tab-item} Recipe
```bash
pjkm init my-api --recipe fastapi-service
cd my-api && python -m my_api
# → http://localhost:8000/docs
```
:::

:::{tab-item} Groups
```bash
pjkm init my-lib -a single-package -g dev -g docs -g coverage
```
:::

:::{tab-item} Preview
```bash
pjkm preview --recipe saas-backend
```
:::

:::{tab-item} AI Agent (MCP)
```bash
pip install pjkm[mcp]
python -m pjkm.mcp
# Agent calls: init_project(name="my-api", recipe="fastapi-service")
```
:::

::::

## The Group-Aware Difference

Most scaffolders generate static skeletons. pjkm generates **wired, running applications**.

Pick `api + database + redis + auth` and you get:

```{mermaid}
graph TB
    subgraph "Generated src/my_api/"
        M[__main__.py] -->|starts| A[api/app.py]
        A -->|lifespan| L[core/lifespan.py]
        L -->|startup| DB[core/database.py]
        L -->|startup| R[core/redis.py]
        A -->|routes| H[api/routes/health.py]
        H -->|pings| DB
        H -->|pings| R
        A -->|deps| D[api/deps.py]
        D -->|get_db| DB
        D -->|get_redis| R
        D -->|get_user| AUTH[auth/jwt.py]
        DB -->|models| MOD[models/mixins.py]
        S[core/settings.py] -->|reads| ENV[.env]
    end
```

Everything auto-wires because templates use `{% if "database" in groups %}` — fragments compose with each other based on your selection.

## For AI Agents & Sandboxes

pjkm is designed as infrastructure for AI coding agents:

```{mermaid}
graph LR
    subgraph "Agent Workflow"
        AGENT[AI Agent] -->|MCP| PJKM[pjkm MCP Server]
        PJKM -->|init_project| PROJ[New Project]
        PJKM -->|add_groups| PROJ
        PJKM -->|list_groups| AGENT
        PJKM -->|adopt_project| EXISTING[Existing Project]
    end
    subgraph "Standardized Output"
        PROJ --> STD1[Consistent structure]
        PROJ --> STD2[Known entry points]
        PROJ --> STD3[Typed settings]
        PROJ --> STD4[Health checks]
        PROJ --> STD5[Test fixtures]
    end
```

**Why agents need pjkm:**

- **Standardized structure** — agents know where files go (`src/*/api/app.py`, `src/*/core/settings.py`)
- **Known entry points** — `python -m <project>` always works
- **Typed configuration** — `Settings` class with Pydantic validation, not raw env vars
- **Health checks** — `/health` and `/ready` endpoints for sandbox orchestration
- **Test fixtures** — `conftest.py` with async client, DB session, Redis client
- **Reproducible** — same recipe = same output, every time

### Claude Desktop Integration

```json
{
  "mcpServers": {
    "pjkm": {
      "command": "python",
      "args": ["-m", "pjkm.mcp"]
    }
  }
}
```

### LangChain / LangGraph Integration

```python
from langchain_mcp_adapters import MultiServerMCPClient

async with MultiServerMCPClient({
    "pjkm": {"command": "python", "args": ["-m", "pjkm.mcp"]}
}) as client:
    tools = client.get_tools()
    # Agent can now: init_project, list_recipes, add_groups, etc.
```

## At a Glance

| | |
|---|---|
| **105 groups** | 8 categories: Core Dev, AI/ML, Web, Infra, Data, Frontend, Docs, Platform |
| **22 recipes** | fastapi-service, ai-agent, rag-service, saas-backend, and 18 more |
| **34 fragments** | 6 generate real Python source code with group-aware wiring |
| **22 workflows** | CI, release, Docker, CodeQL, deploy, auto-merge, and more |
| **10 MCP tools** | init, add, preview, list, search, adopt, status |
| **5 blueprints** | microservices, data-platform, ml-platform, fullstack, scraping |
| **207 tests** | 17 integration tests that generate and validate real projects |
