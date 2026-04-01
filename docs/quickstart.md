# Quick Start

## Install

```bash
pip install pjkm
```

## Set Your Defaults

```bash
pjkm defaults --init
```

Edit `~/.pjkmrc.yaml`:

```yaml
author_name: "Your Name"
author_email: "you@example.com"
license: "MIT"
python_version: "3.13"
```

## Create Your First Project

### From a Recipe

```bash
pjkm recipe                           # browse 22 recipes
pjkm preview --recipe fastapi-service  # preview the output
pjkm init my-api --recipe fastapi-service
```

### From Groups

```bash
pjkm list groups                      # browse 105 groups
pjkm init my-lib -a single-package -g dev -g docs -g coverage
```

### Interactively

```bash
pjkm tui
```

## Run It

```bash
cd my-api
python -m my_api          # starts uvicorn
# → http://localhost:8000/docs
```

## What's Inside

```
my-api/
├── src/my_api/
│   ├── __main__.py       # entry point
│   ├── api/app.py        # FastAPI factory
│   ├── api/routes/       # health, v1
│   ├── core/settings.py  # Pydantic Settings
│   ├── core/database.py  # SQLAlchemy async
│   ├── core/redis.py     # Redis client
│   ├── auth/jwt.py       # JWT tokens
│   └── models/mixins.py  # timestamps, UUIDs
├── tests/
│   ├── conftest.py       # fixtures for app, db, redis
│   ├── test_health.py    # endpoint tests
│   └── test_settings.py  # settings tests
├── .github/workflows/    # 15+ CI/CD workflows
├── Dockerfile            # multi-stage build
├── pyproject.toml        # all deps organized
└── .env.example          # only vars you need
```

## Next Steps

- {doc}`recipes` — browse all 22 pre-configured project types
- {doc}`groups` — understand the 105 available groups
- {doc}`workspace` — scaffold multi-service platforms
- {doc}`registry` — install community group packs
