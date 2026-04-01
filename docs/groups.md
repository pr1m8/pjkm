# Package Groups

Groups are YAML-defined bundles of dependencies, scaffolded code, and tool configuration.

```bash
pjkm list groups    # browse all 105 groups
pjkm info <group>   # detailed view
```

## Categories

### Core Dev (23)

Development tooling, testing, linting, profiling.

| Group | Description |
|-------|-------------|
| `dev` | Meta-group: linting + testing + typecheck + coverage |
| `linting` | Ruff, pre-commit, commitizen |
| `testing` | pytest, pytest-cov, pytest-mock, pytest-asyncio |
| `typecheck` | Pyright, mypy |
| `coverage` | coverage[toml] |
| `security` | Bandit, detect-secrets |
| `code_quality` | interrogate, vulture, radon, xenon |
| `profiling` | py-spy, memray, scalene |
| `debugging` | ipdb, icecream, devtools, snoop |
| `testing_extended` | hypothesis, faker, factory-boy, freezegun |
| `async_tools` | anyio, tenacity, aiocache, aiolimiter |
| `http_client` | httpx, respx, stamina, hishel |
| `cli_rich` | Typer, Rich, Click, questionary |
| `config_mgmt` | Pydantic Settings, dynaconf, python-dotenv |
| `textual_tui` | Textual TUI framework |
| `file_utils` | python-magic, watchfiles, chardet, humanize |
| `logging` | Rich + structlog |

### AI / ML (29)

LLMs, agents, embeddings, vector stores, ML, computer vision, NLP.

| Group | Description |
|-------|-------------|
| `agents` | LangGraph agent orchestration with tools + memory |
| `langchain` | LangChain core + OpenAI/Anthropic/HF providers |
| `langgraph` | LangGraph SDK + prebuilt + checkpointer |
| `langchain_providers` | Google, Mistral, Groq, Together, Ollama, Nvidia |
| `llm_providers` | Direct SDKs: OpenAI, Anthropic, Google, LiteLLM, Instructor |
| `claude_sdk` | Anthropic SDK with tool use and batches |
| `openai_sdk` | OpenAI SDK with assistants and structured outputs |
| `mcp_tools` | MCP protocol + langchain adapters |
| `agent_protocols` | MCP + A2A/ACP + SSE for agent interop |
| `rag` | Retrieval-augmented generation pipeline |
| `vector_stores` | Qdrant, Chroma, pgvector, FAISS, BM25 |
| `embeddings` | sentence-transformers, tiktoken, Cohere, Voyage |
| `search_tools` | Tavily, DuckDuckGo, SerpAPI, Wikipedia, arXiv |
| `eval` | LangSmith + ragas + deepeval |
| `langsmith` | LangSmith tracing, datasets, prompt management |
| `guardrails` | Guardrails AI + NeMo Guardrails |
| `hf` | HuggingFace Hub, Transformers, Datasets, PEFT |
| `torch` | PyTorch + torchvision + torchaudio |
| `ml` | scikit-learn, XGBoost, LightGBM, ONNX, pandas |
| `doc_parsing` | PDF, DOCX, HTML, markdown parsing |
| `image` | Pillow + OpenCV |
| `video` | ffmpeg + moviepy + yt-dlp |
| `audio` | librosa + pydub + Whisper |
| `ocr` | Tesseract + EasyOCR |
| `dataviz` | matplotlib, seaborn, plotly, altair |

### Web & API (18)

FastAPI, auth, WebSocket, payments, email.

### Data & Storage (9)

PostgreSQL, Redis, MongoDB, Kafka, Elasticsearch.

### Infrastructure (18)

Docker, K8s, OTel, Celery, Terraform, S3, MinIO.

### Frontend (2)

Next.js + Vite/React.

### Docs & Meta (4)

Sphinx, MkDocs, GitHub templates.

### Platform (2)

macOS, Linux platform-specific deps.

## Custom Groups

```bash
pjkm group create my-framework     # scaffold YAML
pjkm group import pyproject.toml   # import from existing
pjkm group validate                # check validity
```
