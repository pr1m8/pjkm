# Architecture

## Execution Flow

```{mermaid}
graph LR
    subgraph Input
        CLI[CLI / TUI]
        MCP[MCP Server]
    end
    subgraph Engine
        CFG[ProjectConfig]
        ENG[ProjectEngine]
        DAG[Task DAG]
    end
    subgraph Phases
        S[SCAFFOLD]
        C[CONFIGURE]
        I[INSTALL]
        V[VERIFY]
    end
    CLI --> CFG
    MCP --> CFG
    CFG --> ENG --> DAG
    DAG --> S --> C --> I --> V
```

### Phase Details

```{mermaid}
graph TB
    subgraph "SCAFFOLD"
        S1[init_project] --> S2[init_git] --> S3[setup_remote]
    end
    subgraph "CONFIGURE"
        C1[apply_groups] --> C2[configure_linting] --> C3[setup_git_lfs]
    end
    subgraph "INSTALL"
        I1[pdm_install] --> I2[pre_commit_install]
    end
    subgraph "VERIFY"
        V1[verify_structure]
    end
    S3 --> C1
    C3 --> I1
    I2 --> V1
```

## Template Composition

```{mermaid}
graph TB
    subgraph "Layer 1: Base"
        B[pyproject.toml, .gitignore, CI workflows, LICENSE, README]
    end
    subgraph "Layer 2: Archetype"
        A1[single_package: src/ + tests/]
        A2[service: + infra/, Makefile, .env]
        A3[poly_repo: + packages/, tools/]
        A4[script_tool: + __main__.py, cli.py]
    end
    subgraph "Layer 3: Fragments"
        F1[api_app: FastAPI + routes + middleware]
        F2[db_models: SQLAlchemy + sessions + mixins]
        F3[redis_client: async pool + health]
        F4[auth_jwt: JWT + Bearer deps]
        F5[agent_app: LangGraph + tools + state]
        F6[settings_module: Pydantic Settings + .env]
        F7[logging_structlog: structlog + Rich]
        F8[...28 more fragments]
    end
    B --> A1 & A2 & A3 & A4
    A2 --> F1 & F2 & F3 & F4 & F6 & F7
    A1 --> F5 & F6 & F7
```

## Group-Aware Wiring

Templates receive `groups` (list of selected group IDs) in Jinja2 context. Fragments conditionally compose:

```{mermaid}
graph LR
    subgraph "Selected: api + database + redis"
        direction TB
        LIFE[lifespan.py]
        HEALTH[health.py]
        DEPS[deps.py]
        SET[settings.py]
        ENV[.env.example]
    end
    LIFE -->|"if database in groups"| DB_CONN[connects DB on startup]
    LIFE -->|"if redis in groups"| R_CONN[connects Redis on startup]
    HEALTH -->|"if database in groups"| DB_PING[pings DB]
    HEALTH -->|"if redis in groups"| R_PING[pings Redis]
    DEPS -->|"if database in groups"| GET_DB["get_db() injector"]
    DEPS -->|"if redis in groups"| GET_R["get_redis() injector"]
    SET -->|"if database in groups"| DB_URL[database_url field]
    SET -->|"if redis in groups"| R_URL[redis_url field]
    ENV -->|"if database in groups"| DB_VAR[DATABASE_URL=...]
    ENV -->|"if redis in groups"| R_VAR[REDIS_URL=...]
```

## Package Layout

```
src/pjkm/
  cli/
    app.py                      # slim entry point
    commands/                   # 8 command modules
  core/
    models/                     # Pydantic models
    groups/
      definitions/              # 105 YAML files in 8 subdirs
      registry.py               # rglob("*.yaml") discovery
      resolver.py               # transitive deps + cycle detection
    registry/                   # community pack index
    templates/                  # composer, loader, renderer
    tasks/                      # DAG task system
    engine/                     # task runner
  mcp/
    server.py                   # FastMCP server (pip install pjkm[mcp])
  templates/
    base/                       # shared (pyproject, CI, gitignore)
    {archetype}/                # per-archetype structure
    fragments/                  # 34 composable template pieces
  tui/                          # Textual wizard
```

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Groups are YAML, not code | Add groups without writing Python |
| Category in YAML schema | No hardcoded maps, self-describing |
| `rglob("*.yaml")` discovery | Groups can be in subdirectories |
| Group-aware Jinja2 | `{% if "database" in groups %}` for composition |
| Copier under the hood | Proven template engine, not reinvented |
| MCP via FastMCP | Standard protocol, works with Claude + LangChain |
| Optional extras | `pjkm[mcp]`, `pjkm[docs]` — pay for what you use |
