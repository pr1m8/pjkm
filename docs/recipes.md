# Recipes

Recipes are pre-configured combinations of archetype + groups. One command, fully configured project.

```bash
pjkm init myapp --recipe <name>
```

## All Recipes

| Recipe | Archetype | Groups | Description |
|--------|-----------|--------|-------------|
| `python-lib` | single-package | 11 | Publish-ready library with CI/CD |
| `fastapi-service` | service | 18 | Production API with DB, auth, observability, docs |
| `ai-agent` | single-package | 18 | LangGraph agent with tools, memory, MCP |
| `rag-service` | service | 21 | RAG API with vector store, embeddings |
| `agent-platform` | service | 24 | Multi-agent with eval, monitoring |
| `ml-pipeline` | service | 15 | ML training with experiment tracking |
| `data-analysis` | single-package | 10 | Notebooks + visualization |
| `cli-tool` | script-tool | 10 | Polished CLI with Typer |
| `fullstack-web` | service | 21 | API + Next.js + auth + infra |
| `monorepo` | poly-repo | 18 | Multi-package with shared CI |
| `scraper` | service | 13 | Crawling pipeline |
| `fintech` | service | 20 | Payments, compliance, monitoring |
| `api-microservice` | service | 16 | Lightweight async service |
| `discord-bot` | single-package | 12 | Async bot with scheduling |
| `etl-pipeline` | service | 14 | ETL with queues |
| `saas-backend` | service | 24 | Multi-tenant with billing, email, websocket |
| `document-processor` | service | 13 | Doc ingestion, OCR, PDF |
| `media-pipeline` | service | 16 | Video/audio/image with ffmpeg |
| `realtime-api` | service | 16 | WebSocket + SSE + rate limiting |
| `file-service` | service | 15 | S3 uploads with thumbnails |
| `scraper-full` | service | 27 | Full platform with MinIO, Celery, Prometheus |
| `tui-app` | script-tool | 13 | Textual terminal UI |

## Preview Before Creating

```bash
pjkm preview --recipe fastapi-service
```

## Show Recipe Details

```bash
pjkm recipe ai-agent --show
```
