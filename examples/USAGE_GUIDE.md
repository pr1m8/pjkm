# pjkm Usage Guide

Complete walkthrough from install to production.

## 1. Install

```bash
pip install pjkm
# or
pipx install pjkm
```

## 2. Set Your Defaults (Once)

```bash
pjkm defaults --init
# Creates .pjkmrc.yaml — edit with your name, email, org
```

Or copy the example:
```bash
cp examples/pjkmrc.example.yaml ~/.pjkmrc.yaml
```

## 3. Create a Project

### Option A: Use a Recipe (Recommended)

```bash
# See all recipes
pjkm recipe

# Preview what you'd get
pjkm preview --recipe fastapi-service

# Create it
pjkm init my-api --recipe fastapi-service
```

### Option B: Pick Groups Manually

```bash
# Browse groups
pjkm list groups

# Combine what you need
pjkm init my-api -a service -g api -g database -g redis -g docker -g logging
```

### Option C: Interactive TUI

```bash
pjkm tui
```

## 4. Run Your Project

```bash
cd my-api

# Start infrastructure
docker compose -f infra/compose.postgres.yaml -f infra/compose.redis.yaml up -d

# Run the API
python -m my_api
# → http://localhost:8000
# → http://localhost:8000/health
# → http://localhost:8000/ready
# → http://localhost:8000/docs (Swagger UI)

# Run tests
pdm run test

# Lint + format
pdm run check

# Type check
pdm run typecheck
```

## 5. Add More Groups Later

```bash
# Add auth to an existing project
pjkm add -g auth

# Add monitoring
pjkm add -g monitoring -g error_tracking

# Check what's applied
pjkm status
```

## 6. Adopt an Existing Project

```bash
cd ~/my-old-project

# Scan for frameworks and tools
pjkm adopt
# Output: Detected fastapi, sqlalchemy, redis, pytest...

# Apply detected groups
pjkm adopt --apply
```

## 7. Multi-Service Platform

```bash
# Use a blueprint
pjkm workspace my-platform --blueprint microservices

# Or custom
pjkm workspace my-platform \
  -s api:api \
  -s worker:worker \
  -s site:web \
  -s ml:ml \
  -s shared:lib

# Open in VS Code
code my-platform/my-platform.code-workspace

# Start everything
cd my-platform
make install
make up
make test
```

## 8. Install Community Packs

```bash
# Browse
pjkm search
pjkm search django

# Install
pjkm install pjkm-django

# Now django groups are available
pjkm init my-django-app -g django -g django_rest
```

## 9. Create Your Own Groups

```bash
# Scaffold a group YAML
pjkm group create my-framework

# Edit .pjkm/groups/my_framework.yaml
# Add dependencies, scaffolded files, tool config

# Validate
pjkm group validate

# Share via git
git init && git add . && git push
pjkm group source add https://github.com/you/my-groups.git
```

## 10. Available PDM Scripts

Every generated project includes these scripts in `pyproject.toml`:

```bash
pdm run test          # pytest
pdm run fmt           # ruff format
pdm run lint          # ruff check
pdm run check         # fmt + lint
pdm run typecheck     # pyright
pdm run cov           # pytest --cov
pdm run serve         # python -m <project>  (services only)
pdm run docs          # sphinx-build
pdm run docs-serve    # sphinx-autobuild (live reload)
pdm run changelog     # towncrier build
```

## 11. Generated Test Structure

Services with API groups get test files:

```
tests/
├── __init__.py
├── conftest.py        # fixtures: app, client, db_session, redis_client
├── test_health.py     # health + ready endpoint tests
└── test_settings.py   # settings validation tests
```

Run with: `pdm run test`

## 12. CI/CD Workflows

Up to 22 GitHub Actions workflows depending on your groups:

```bash
# See what workflows you have
ls .github/workflows/

# Key workflows:
# ci.yml          — test, lint, typecheck, docs, security
# release.yml     — PyPI publish on tag
# docker.yml      — multi-arch Docker build + GHCR push
# auto-merge.yml  — auto-merge Dependabot patches
# migration-check.yml — test DB migrations on PRs
```

## 13. Environment Variables

`.env.example` is generated with only the vars your groups need:

```bash
cp .env.example .env
# Edit .env with real values

# The Settings class reads from .env automatically:
# from my_api.core.settings import get_settings
# settings = get_settings()
# settings.database_url  ← reads DATABASE_URL from .env
```

## 14. Upgrading Dependencies

```bash
# See what would change
pjkm upgrade --dry-run

# Upgrade all group deps to latest definitions
pjkm upgrade

# Upgrade specific groups
pjkm upgrade -g database -g redis

# Strip version pins (use latest)
pjkm upgrade --latest
```

## 15. Common Patterns

### Add a new API route

```python
# src/my_api/api/routes/users.py
from fastapi import APIRouter, Depends
from my_api.api.deps import get_db, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return user
```

Then register in `app.py`:
```python
from my_api.api.routes import users
app.include_router(users.router, prefix="/api/v1")
```

### Add a database model

```python
# src/my_api/models/user.py
from sqlalchemy.orm import Mapped, mapped_column
from my_api.core.database import Base
from my_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
```

Then import in `models/__init__.py`:
```python
from my_api.models.user import User  # noqa: F401
```

### Add a Celery task

```python
# src/my_api/workers/tasks.py
from my_api.workers.celery_app import app

@app.task(bind=True, max_retries=3)
def process_upload(self, file_id: str):
    ...
```

### Add an agent tool

```python
# src/my_agent/agent/tools.py
@tool
def lookup_user(user_id: str) -> str:
    """Look up a user by ID."""
    ...
```
