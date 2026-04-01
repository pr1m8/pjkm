# pjkm MCP Server Extension

## Overview

Expose pjkm's project scaffolding capabilities as an MCP (Model Context Protocol) server. This lets AI agents (Claude, LangChain agents, etc.) discover and use pjkm's templates, groups, and recipes as tools — enabling AI-driven project creation.

## Architecture

```
┌──────────────────────────────────────────────────┐
│  AI Agent (Claude Desktop / LangChain / Custom)  │
│                                                  │
│  "Create a FastAPI service with database and     │
│   Redis, then add authentication"                │
└───────────────────┬──────────────────────────────┘
                    │ MCP Protocol (stdio/SSE)
                    ▼
┌──────────────────────────────────────────────────┐
│  pjkm MCP Server (FastMCP)                       │
│                                                  │
│  Tools:                                          │
│    init_project    — create project from recipe  │
│    add_groups      — add groups to project       │
│    list_recipes    — browse recipes              │
│    list_groups     — browse groups by category   │
│    preview_project — preview without creating    │
│    search_registry — search community packs      │
│    adopt_project   — scan existing project       │
│    get_group_info  — detailed group info         │
│                                                  │
│  Resources:                                      │
│    pjkm://recipes           — all recipes        │
│    pjkm://groups            — all groups         │
│    pjkm://groups/{id}       — group details      │
│    pjkm://templates/{name}  — template info      │
│    pjkm://registry          — community packs    │
│                                                  │
│  Prompts:                                        │
│    project-advisor  — recommend recipe/groups     │
│    architecture     — suggest architecture        │
└──────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Core MCP Server

**File**: `src/pjkm/mcp/server.py`

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="pjkm",
    description="Python project scaffolder — create fully configured projects with AI",
)
```

### Phase 2: Tools

**init_project** — The main tool. Creates a project from a recipe or groups.

```python
@mcp.tool
def init_project(
    name: str,
    recipe: str | None = None,
    archetype: str | None = None,
    groups: list[str] | None = None,
    directory: str = ".",
) -> str:
    """Create a new Python project.

    Use a recipe for a pre-configured setup, or specify archetype + groups.
    Returns the path to the created project and a summary of what was generated.
    """
```

**add_groups** — Add groups to an existing project.

```python
@mcp.tool
def add_groups(
    groups: list[str],
    directory: str = ".",
) -> str:
    """Add package groups to an existing pjkm project.

    Merges dependencies, renders scaffolded files, and updates pyproject.toml.
    """
```

**preview_project** — Preview without creating.

```python
@mcp.tool
def preview_project(
    recipe: str | None = None,
    archetype: str | None = None,
    groups: list[str] | None = None,
) -> str:
    """Preview what a project would look like without creating it.

    Returns the file tree, dependencies, and workflows that would be generated.
    """
```

**list_recipes** — Browse available recipes.

```python
@mcp.tool
def list_recipes() -> str:
    """List all available project recipes with descriptions.

    Returns recipe names, archetypes, group counts, and descriptions.
    """
```

**list_groups** — Browse groups.

```python
@mcp.tool
def list_groups(category: str | None = None) -> str:
    """List available package groups, optionally filtered by category.

    Categories: Core Dev, AI / ML, Web & API, Data & Storage,
    Infrastructure, Frontend, Docs & Meta, Platform
    """
```

**get_group_info** — Detailed group info.

```python
@mcp.tool
def get_group_info(group_id: str) -> str:
    """Get detailed information about a specific package group.

    Returns dependencies, scaffolded files, required groups, and tool config.
    """
```

**search_registry** — Search community packs.

```python
@mcp.tool
def search_registry(query: str = "") -> str:
    """Search the pjkm registry for community group packs.

    Returns matching packs with names, descriptions, and install commands.
    """
```

**adopt_project** — Scan existing project.

```python
@mcp.tool
def adopt_project(directory: str = ".") -> str:
    """Scan an existing project and suggest pjkm groups to adopt.

    Detects frameworks, tools, and patterns from pyproject.toml,
    requirements.txt, and project structure.
    """
```

### Phase 3: Resources

```python
@mcp.resource("pjkm://recipes")
def get_all_recipes() -> str:
    """All available recipes with full details."""

@mcp.resource("pjkm://groups")
def get_all_groups() -> str:
    """All groups organized by category."""

@mcp.resource("pjkm://groups/{group_id}")
def get_group(group_id: str) -> str:
    """Detailed info for a specific group."""

@mcp.resource("pjkm://registry")
def get_registry() -> str:
    """Community group pack registry."""
```

### Phase 4: Prompts

```python
@mcp.prompt
def project_advisor(description: str) -> str:
    """Given a project description, recommend the best recipe and groups."""

@mcp.prompt
def architecture_advisor(requirements: str) -> str:
    """Given requirements, suggest a multi-service architecture with workspace blueprint."""
```

## Dependencies

```
fastmcp>=2.0.0
langchain-mcp-adapters>=0.1.8   # for LangChain integration
```

## Usage

### With Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pjkm": {
      "command": "python",
      "args": ["-m", "pjkm.mcp.server"]
    }
  }
}
```

### With LangChain

```python
from langchain_mcp_adapters import MultiServerMCPClient

async with MultiServerMCPClient(
    {"pjkm": {"command": "python", "args": ["-m", "pjkm.mcp.server"]}}
) as client:
    tools = client.get_tools()
    # Agent can now call init_project, list_recipes, etc.
```

### Standalone

```bash
# Run as stdio server
python -m pjkm.mcp.server

# Run as SSE server (for remote access)
fastmcp run pjkm.mcp.server:mcp --transport sse --port 8080
```

## Example Conversations

**User**: "Create a FastAPI service with PostgreSQL, Redis, and JWT auth"

**Agent calls**: `init_project(name="my-api", recipe="fastapi-service")`

**Agent responds**: "Created my-api/ with FastAPI, SQLAlchemy, Redis, JWT auth, 15 GitHub Actions workflows, and Sphinx docs. Run `cd my-api && python -m my_api` to start."

---

**User**: "What AI agent groups are available?"

**Agent calls**: `list_groups(category="AI / ML")`

**Agent responds**: "There are 29 AI/ML groups including agents (LangGraph), langchain, langgraph, embeddings, vector_stores, rag, eval, claude_sdk, openai_sdk, mcp_tools, guardrails..."

---

**User**: "Scan my current project and suggest what I should add"

**Agent calls**: `adopt_project(directory=".")`

**Agent responds**: "Detected FastAPI, SQLAlchemy, Redis in your project. Suggested groups: api, database, redis, docker, logging. Run `pjkm adopt --apply` to add them."
