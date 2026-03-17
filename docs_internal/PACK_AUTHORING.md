# Creating a Group Pack

A group pack is a git repo containing YAML group definitions and optional template fragments. Once published, anyone can install it with `pjkm install <pack-name>`.

## Quick Start

```bash
# 1. Create a new repo
mkdir pjkm-pack-myframework && cd pjkm-pack-myframework
git init

# 2. Create group definitions
mkdir -p groups
pjkm group create myframework --dir groups
pjkm group create myframework-admin --dir groups

# 3. Edit the YAML files to add dependencies
# groups/myframework.yaml
# groups/myframework_admin.yaml

# 4. (Optional) Add template fragments
mkdir -p fragments/myframework_app/template/src/{{ project_slug }}/
# Add .jinja files...

# 5. Push to GitHub
git add . && git commit -m "Initial pack"
gh repo create pjkm-pack-myframework --public --push
```

## Group YAML Schema

```yaml
id: myframework               # unique identifier
name: "My Framework"          # human-readable name
description: "Full description of what this group provides"
category: "Web & API"         # Core Dev, AI / ML, Web & API, Data & Storage, Infrastructure, Frontend, Docs & Meta, Platform
archetypes:                   # which archetypes this is compatible with (empty = all)
  - service
requires_groups:              # other groups that must be present
  - api
platform_filter: null         # null = all, or "darwin", "linux", "win32"

dependencies:
  myframework:                # section name in [project.optional-dependencies]
    - "myframework>=2.0.0"
    - "myframework-tools>=1.0.0"

scaffolded_files:
  - template_fragment: "myframework_app"
    destination: "."
    description: "My Framework application scaffold"

pyproject_tool_config:        # merged into [tool.*] sections
  myframework:
    setting: "value"
```

## Template Fragments

Fragments are Copier templates. Each fragment needs:

```
fragments/myframework_app/
  copier.yml              # declares template variables
  template/               # files to render
    src/
      {{ project_slug }}/
        myframework/
          __init__.py.jinja
          app.py.jinja
          config.py.jinja
```

### copier.yml

```yaml
_min_copier_version: "9.0.0"
_subdirectory: "template"

project_name:
  type: str
project_slug:
  type: str
groups:
  type: json
  default: []
```

### Group-aware templates

Use `{% if "groupname" in groups %}` to conditionally include code:

```python
# In app.py.jinja
{% if "database" in groups %}
from {{ project_slug }}.core.database import get_session
{% endif %}
```

## Publishing to the Registry

1. Create a JSON entry for your pack:

```json
{
  "name": "pjkm-myframework",
  "description": "My Framework scaffolding with admin, API, and workers",
  "url": "https://github.com/yourorg/pjkm-pack-myframework.git",
  "author": "yourorg",
  "tags": ["myframework", "web", "admin"],
  "groups": ["myframework", "myframework_admin", "myframework_worker"]
}
```

2. Submit a PR to the [pjkm-registry](https://github.com/pr1m8/pjkm-registry) repo adding your entry to `index.json`.

## Testing Your Pack

```bash
# Validate your group definitions
pjkm group validate ./groups/

# Register locally without publishing
pjkm group source add ./path/to/your/pack --name mypack --no-sync

# Or test from a git URL
pjkm group source add https://github.com/yourorg/pjkm-pack-myframework.git

# Verify groups loaded
pjkm group list

# Test with preview
pjkm preview service -g myframework
```

## Directory Structure Options

Your pack repo can be structured either way:

**Flat (simple):**
```
my-pack/
  myframework.yaml
  myframework_admin.yaml
```

**Organized (recommended for larger packs):**
```
my-pack/
  groups/
    myframework.yaml
    myframework_admin.yaml
  fragments/
    myframework_app/
      copier.yml
      template/
        ...
```

When using a subdirectory, specify `--path groups` when adding the source:
```bash
pjkm group source add https://github.com/org/pack.git --path groups
```
