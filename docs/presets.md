# Presets

Presets are curated group sets per archetype — lighter than recipes.

```bash
pjkm recommend <archetype> --preset <name>
```

## Available Presets

| Preset | Description |
|--------|-------------|
| `minimal` | Bare minimum: dev, linting, testing |
| `standard` | Production-ready: + typecheck, coverage, security, docs |
| `full` | Everything: + code quality, towncrier, reporting |
| `ai` | AI-focused: + langchain, langgraph, vector stores, ML |
| `data` | Data science: + ML, dataviz, jupyter, notebooks |
| `web` | Web-focused: + API, auth, frontend, nginx, gateway |

## Example

```bash
pjkm recommend service --preset standard
# Shows: dev, linting, testing, typecheck, coverage, security, docs,
#        api, database, docker, logging, github_templates, makefile
```
