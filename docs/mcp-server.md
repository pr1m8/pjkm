# MCP Server

pjkm exposes its full scaffolding engine as an MCP (Model Context Protocol) server. AI agents can create, preview, and manage Python projects programmatically.

## Install

```bash
pip install pjkm[mcp]
```

## Run

```bash
python -m pjkm.mcp                                    # stdio (Claude Desktop)
pjkm-mcp                                              # same thing
fastmcp run pjkm.mcp.server:mcp --transport sse       # SSE (remote agents)
```

## Architecture

```{mermaid}
graph TB
    subgraph "Clients"
        CD[Claude Desktop]
        LC[LangChain Agent]
        CU[Custom Agent]
    end
    subgraph "pjkm MCP Server"
        T1[init_project]
        T2[add_groups]
        T3[preview_project]
        T4[list_recipes]
        T5[list_groups]
        T6[get_group_info]
        T7[search_registry]
        T8[adopt_project]
        R1["pjkm://recipes"]
        R2["pjkm://groups"]
        R3["pjkm://groups/{id}"]
        R4["pjkm://registry"]
    end
    subgraph "pjkm Core"
        ENG[ProjectEngine]
        REG[GroupRegistry]
        RES[GroupResolver]
        TPL[TemplateComposer]
    end
    CD --> T1 & T4 & T5
    LC --> T1 & T2 & T7
    CU --> T3 & T6 & T8
    T1 --> ENG
    T2 --> REG
    T5 --> REG
    T6 --> REG
    ENG --> RES --> TPL
```

## Tools

### `init_project`
Create a new project from a recipe or custom groups.

```
init_project(name="my-api", recipe="fastapi-service")
init_project(name="my-lib", archetype="single-package", groups=["dev", "docs"])
```

### `add_groups`
Add groups to an existing project.

```
add_groups(groups=["auth", "redis"], directory="./my-api")
```

### `preview_project`
See what would be generated without creating files.

```
preview_project(recipe="saas-backend")
```

### `list_recipes`
Browse all 22 recipes with descriptions.

### `list_groups`
Browse all 105 groups, optionally filtered by category.

```
list_groups(category="AI / ML")
```

### `get_group_info`
Detailed info for a group: deps, scaffolded files, config.

```
get_group_info(group_id="database")
```

### `search_registry`
Search community packs.

```
search_registry(query="django")
```

### `adopt_project`
Scan an existing project and detect frameworks/tools.

```
adopt_project(directory="./my-old-project")
```

## Resources

| URI | Description |
|-----|-------------|
| `pjkm://recipes` | All recipes with full details |
| `pjkm://groups` | All groups organized by category |
| `pjkm://groups/{id}` | Detailed info for a specific group |
| `pjkm://registry` | Community pack listing |

## Claude Desktop Setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Then ask Claude: *"Create a FastAPI service with database and auth"*

## LangChain Agent Setup

```python
from langchain_mcp_adapters import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-20250514")

async with MultiServerMCPClient({
    "pjkm": {"command": "python", "args": ["-m", "pjkm.mcp"]}
}) as client:
    tools = client.get_tools()
    agent = create_react_agent(model, tools)
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "Create an AI agent project with LangGraph"}]
    })
```

## Use Cases

### Agent Sandbox Bootstrapping
An orchestrator agent creates isolated project environments for task-specific agents:

```{mermaid}
sequenceDiagram
    participant O as Orchestrator
    participant P as pjkm MCP
    participant A as Task Agent
    O->>P: init_project("task-123", recipe="ai-agent")
    P-->>O: Created at /sandboxes/task-123/
    O->>A: Execute in /sandboxes/task-123/
    A->>A: Uses generated agent scaffolding
    A-->>O: Task complete
```

### Multi-Agent Platform Setup
Create a full platform with shared infrastructure:

```python
# Agent creates a workspace
init_project("my-platform", ...)  # Not quite — use workspace CLI
# But can create individual services:
init_project("api-gateway", recipe="fastapi-service", directory="platform/")
init_project("ml-worker", recipe="ai-agent", directory="platform/")
init_project("data-ingestion", recipe="etl-pipeline", directory="platform/")
```
