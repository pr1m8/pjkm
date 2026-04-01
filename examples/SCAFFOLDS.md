# Scaffold Examples

Real output from `pjkm init` with various recipes and group combinations.

## 1. FastAPI Service (Full Stack)

```bash
pjkm init my-api --recipe fastapi-service
```

**What you get**: 18 groups, ~90 files, runnable with `python -m my_api`

```bash
# Start infrastructure
docker compose -f infra/compose.postgres.yaml -f infra/compose.redis.yaml up -d

# Run the app
python -m my_api
# → http://localhost:8000/docs    (Swagger UI)
# → http://localhost:8000/health  (liveness)
# → http://localhost:8000/ready   (readiness — pings DB + Redis)

# Run tests
pdm run test

# Build docs
pdm run docs
```

**Key generated files**:
- `src/my_api/__main__.py` — uvicorn entry point with settings
- `src/my_api/api/app.py` — FastAPI factory with CORS, middleware
- `src/my_api/api/deps.py` — `Depends(get_db)`, `Depends(get_redis)`, `Depends(get_settings)`
- `src/my_api/core/lifespan.py` — connects DB + Redis on startup, closes on shutdown
- `src/my_api/core/settings.py` — reads DATABASE_URL, REDIS_URL, JWT_SECRET from .env
- `src/my_api/auth/jwt.py` — create_access_token / decode_token
- `src/my_api/models/mixins.py` — TimestampMixin, UUIDPrimaryKeyMixin, SoftDeleteMixin

## 2. AI Agent

```bash
pjkm init my-agent --recipe ai-agent
```

**What you get**: 18 groups, LangGraph agent with tools

```python
# Use the generated agent
from my_agent.agent import run_agent

result = await run_agent("What's the weather in London?")
print(result["messages"][-1].content)
```

**Key generated files**:
- `src/my_agent/agent/graph.py` — LangGraph StateGraph with tool calling + routing
- `src/my_agent/agent/state.py` — TypedDict state with message history
- `src/my_agent/agent/tools.py` — @tool functions (time, calculate, web search)
- `src/my_agent/agent/prompts.py` — ChatPromptTemplate collection

## 3. Multi-Service Platform

```bash
pjkm workspace my-platform --blueprint microservices
```

**What you get**: 4 services + shared infra

```bash
cd my-platform
code my-platform.code-workspace  # VS Code with all services

make install  # install all services
make up       # start Postgres + Redis + all services
make test     # test all services
make lint     # lint all services
```

**docker-compose.yml** includes shared Postgres + Redis that all services connect to.

## 4. Incremental Build

Start minimal, add groups as you need them:

```bash
# Start with just an API
pjkm init my-app -a service -g api -g logging

# Later, add database
pjkm add -g database
# → adds SQLAlchemy, alembic/, models/, migrations

# Add auth
pjkm add -g auth
# → adds JWT module, Bearer dependency

# Add Redis for caching
pjkm add -g redis
# → adds Redis client, compose service

# Check what you have
pjkm status
```

## 5. Adopt + Upgrade Existing Project

```bash
# Scan your project
cd ~/my-existing-flask-app
pjkm adopt
# Output: Detected flask, sqlalchemy, redis, pytest, docker

# Apply groups
pjkm adopt --apply

# Upgrade to latest group definitions
pjkm upgrade --dry-run
pjkm upgrade
```

## 6. Data Platform (Workspace)

```bash
pjkm workspace analytics --blueprint data-platform
```

Creates 8 services:
- `api/` — API gateway for data access
- `ingestion/` — CDC, streaming, batch data loading
- `warehouse/` — dbt transformations
- `orchestration/` — Airflow/Dagster workflows
- `quality/` — data quality checks
- `dashboards/` — Streamlit/Grafana dashboards
- `events/` — shared event schemas (analytics contract)
- `shared/` — common library

## 7. CLI Tool

```bash
pjkm init my-tool --recipe cli-tool
```

```python
# Generated CLI at src/my_tool/cli.py
import typer
app = typer.Typer()

@app.command()
def hello(name: str):
    ...
```

```bash
# Run it
python -m my_tool
# or
my-tool hello world
```

## 8. Preview Before Committing

```bash
# See the full file tree without creating anything
pjkm preview --recipe saas-backend

# Preview with custom groups
pjkm preview service -g api -g database -g redis -g auth -g docker

# Preview a workspace
pjkm workspace test --blueprint ml-platform --dry-run
```

## 9. Custom Defaults

```bash
# Set up once
cat > ~/.pjkmrc.yaml << 'EOF'
author_name: "Will"
author_email: "will@example.com"
python_version: "3.13"
groups: [dev, linting, testing, typecheck]
github:
  org: pr1m8
  create_repo: true
EOF

# Now every project gets your defaults
pjkm init my-lib -a single-package
# → author, email, org filled in automatically
# → dev, linting, testing, typecheck always applied
```

## 10. Registry Workflow

```bash
# Search for AI packs
pjkm search ml
# → pjkm-ml-ops: MLOps with DVC + MLflow

# Install
pjkm install pjkm-ml-ops

# Use the new groups
pjkm init my-ml-project -a service -g dvc -g mlflow -g model_serving

# See what's installed
pjkm installed

# Remove
pjkm uninstall pjkm-ml-ops
```
