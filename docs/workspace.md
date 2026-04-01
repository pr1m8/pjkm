# Workspace

Scaffold multi-service platforms with shared infrastructure.

## Blueprints

```bash
pjkm workspace my-platform --blueprint <name>
```

| Blueprint | Services |
|-----------|----------|
| `microservices` | api, worker, web, shared lib |
| `data-platform` | api, ingestion, warehouse, orchestration, quality, dashboards, events, shared |
| `scraping-platform` | api, scraper, worker, web, storage, shared |
| `ml-platform` | api, ml-service, worker, data, dashboards, shared, db-models |
| `fullstack` | api, worker, web, integrations, shared, db-pkg, observability |

## Custom Services

```bash
pjkm workspace my-platform -s api:api -s jobs:worker -s site:web -s shared:lib
```

## What Gets Created

```
my-platform/
├── my-platform.code-workspace     # VS Code multi-root
├── docker-compose.yml             # shared Postgres + Redis
├── Makefile                       # make up/down/test/lint
├── .github/workflows/ci.yml      # per-service test jobs
├── api/                           # full pjkm project
├── jobs/                          # full pjkm project
├── site/                          # full pjkm project
└── shared/                        # full pjkm project
```

## Usage

```bash
code my-platform/my-platform.code-workspace
make install
make up
make test
```
