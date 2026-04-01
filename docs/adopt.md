# Adopt Existing Projects

Scan an existing project and integrate it with pjkm.

## Usage

```bash
cd ~/my-existing-project
pjkm adopt                    # scan and show suggestions
pjkm adopt --apply            # auto-apply detected groups
```

## What It Detects

- **60+ Python packages** → mapped to groups (FastAPI → api, SQLAlchemy → database, etc.)
- **20 file patterns** → mapped to groups (Dockerfile → docker, alembic/ → database, etc.)
- **requirements.txt** → scanned alongside pyproject.toml

## Example

```bash
$ pjkm adopt
Detected Groups (5 new)
┌─────────┬──────────────────────────────────────────┐
│ Group   │ Signals                                  │
├─────────┼──────────────────────────────────────────┤
│ api     │ FastAPI found in dependencies             │
│ database│ SQLAlchemy found, alembic/ directory found │
│ redis   │ redis-py found in dependencies            │
│ docker  │ Dockerfile found                          │
│ testing │ pytest found in dependencies              │
└─────────┴──────────────────────────────────────────┘
```
