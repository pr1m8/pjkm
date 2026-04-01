# AI Agents & MCP

pjkm provides standardized project scaffolding that AI coding agents can rely on.

## Why Agents Need pjkm

AI agents work best with **predictable, standardized project structures**:

| Need | pjkm Provides |
|------|---------------|
| Where does code go? | Always `src/<project>/api/`, `src/<project>/core/`, etc. |
| How to start the app? | Always `python -m <project>` |
| How to read config? | Always `from <project>.core.settings import get_settings` |
| How to check if it's running? | Always `GET /health` and `GET /ready` |
| How to run tests? | Always `pdm run test` |
| How to add dependencies? | Always `pjkm add -g <group>` |

## Agent Recipes

```bash
pjkm init my-agent    --recipe ai-agent         # LangGraph agent
pjkm init my-rag      --recipe rag-service       # RAG API service
pjkm init my-platform --recipe agent-platform    # multi-agent platform
```

### What `ai-agent` Generates

```
src/my_agent/
├── agent/
│   ├── __init__.py          # from .graph import create_agent, run_agent
│   ├── graph.py             # LangGraph StateGraph + tool calling + routing
│   ├── state.py             # TypedDict with message history + context
│   ├── tools.py             # @tool functions + get_all_tools()
│   └── prompts.py           # ChatPromptTemplate collection
├── core/
│   ├── logging/config.py    # structlog setup
│   └── redis.py             # async client for caching
└── ...
```

**graph.py** features:
- `StateGraph` with agent → tools → agent loop
- Configurable LLM via `LLM_PROVIDER` env var (Anthropic or OpenAI)
- Max tool calls limit (prevents infinite loops)
- Async `run_agent(query, context)` entry point

**tools.py** is group-aware:
- Always includes `get_current_time` and `calculate`
- Adds `web_search` (DuckDuckGo) when `search_tools` group is selected
- Add your own tools with `@tool` decorator

## 29 AI/ML Groups

```bash
pjkm list groups    # see all
pjkm info agents    # detailed view
```

**Agent frameworks**: `agents`, `langchain`, `langgraph`, `llm_providers`, `claude_sdk`, `openai_sdk`

**Retrieval**: `rag`, `vector_stores`, `embeddings`, `search_tools`, `doc_parsing`

**Protocols**: `mcp_tools`, `agent_protocols`

**Quality**: `eval`, `langsmith`, `guardrails`

**ML/DL**: `ml`, `hf`, `torch`, `dataviz`, `image`, `video`, `audio`, `ocr`

## MCP Server

```bash
pip install pjkm[mcp]
python -m pjkm.mcp
```

### Tools

| Tool | What it does |
|------|-------------|
| `init_project` | Create a project from recipe or groups |
| `add_groups` | Add groups to existing project |
| `preview_project` | Preview without creating files |
| `list_recipes` | Browse 22 recipes |
| `list_groups` | Browse 105 groups by category |
| `get_group_info` | Detailed group info |
| `search_registry` | Search community packs |
| `adopt_project` | Scan existing project |
| `project_status` | Show applied groups + drift |
| `create_recipe` | Save custom recipe |

### Resources

| URI | Description |
|-----|-------------|
| `pjkm://recipes` | All recipes |
| `pjkm://groups` | All groups by category |
| `pjkm://groups/{id}` | Group details |
| `pjkm://registry` | Community packs |
| `pjkm://archetypes` | Available archetypes |
| `pjkm://blueprints` | Workspace blueprints + service templates |
| `pjkm://categories` | Group categories with counts |

### Prompts

| Prompt | Input | Purpose |
|--------|-------|---------|
| `project_advisor` | Project description | Recommend recipe + groups |
| `architecture_advisor` | System requirements | Design workspace layout |
| `agent_scaffold` | Agent type | Step-by-step agent setup |

### Claude Desktop

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

### LangChain Integration

```python
from langchain_mcp_adapters import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-20250514")

async with MultiServerMCPClient({
    "pjkm": {"command": "python", "args": ["-m", "pjkm.mcp"]}
}) as client:
    agent = create_react_agent(model, client.get_tools())
    result = await agent.ainvoke({
        "messages": [{"role": "user",
                      "content": "Create a RAG service with vector store and auth"}]
    })
```

## Sandbox Bootstrapping

An orchestrator can use pjkm to create isolated environments:

```python
# Orchestrator creates sandbox for each task
result = init_project(name="task-123", recipe="ai-agent", directory="/sandboxes/")
# Task agent operates in /sandboxes/task-123/ with known structure
```

Every sandbox has:
- `python -m task_123` starts the app
- `GET /health` confirms it's running
- `pdm run test` validates it works
- `src/task_123/core/settings.py` for configuration
