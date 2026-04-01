# Template System

## How It Works

Templates are layered via Copier + Jinja2:

1. **Base template** — shared by all projects (pyproject.toml, CI, gitignore)
2. **Archetype template** — project shape (service adds infra/, Makefile, .env)
3. **Fragment templates** — per-group scaffolding (API routes, DB models, etc.)

## Group-Aware Rendering

All templates receive `groups` (list of selected group IDs) in Jinja2 context:

```jinja
{% if "database" in groups %}
from {{ project_slug }}.core.database import get_session
{% endif %}
```

This means fragments auto-wire based on what's selected:
- `.env.example` only includes vars for your groups
- Settings only has fields for selected groups
- Lifespan connects DB + Redis if those groups are present
- Health check pings actual dependencies
- Test fixtures match selected groups

## Source Code Fragments

| Fragment | What it generates |
|----------|-------------------|
| `settings_module` | Pydantic Settings + .env.example |
| `api_app` | FastAPI factory, routes, middleware, deps, __main__.py |
| `db_models` | SQLAlchemy engine, session, Base model, mixins |
| `redis_client` | Async Redis client + connection pool |
| `auth_jwt` | JWT create/decode + Bearer auth dependency |
| `agent_app` | LangGraph agent with graph, state, tools, prompts |
