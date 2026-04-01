# Defaults & Configuration

## Create Config

```bash
pjkm defaults --init        # create .pjkmrc.yaml in current dir
```

## Config Locations

| File | Scope |
|------|-------|
| `~/.pjkmrc.yaml` | Global defaults |
| `./.pjkmrc.yaml` | Project-local overrides |

Local overrides global. CLI flags override both.

## Full Config

```yaml
author_name: "Your Name"
author_email: "you@example.com"
license: "MIT"
python_version: "3.13"
archetype: "single-package"
groups: [dev]
target_dir: "."

github:
  org: "mycompany"
  visibility: "private"
  create_repo: false
  default_branch: "main"

group_sources:
  - url: https://github.com/team/shared-groups.git
    name: team-groups
```
