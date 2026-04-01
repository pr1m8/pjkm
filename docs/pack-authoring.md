# Pack Authoring

Create and publish community group packs.

A pack is a git repo with YAML group definitions + optional template fragments.

## Quick Start

```bash
mkdir pjkm-pack-myframework && cd pjkm-pack-myframework
pjkm group create myframework --dir .
# Edit myframework.yaml — add deps, scaffolded files
git init && git add . && git commit -m "Initial pack"
gh repo create --public --push
```

## Testing

```bash
pjkm group validate .
pjkm group source add ./path/to/pack --name test --no-sync
pjkm preview service -g myframework
```

## Publishing

Submit a PR to [pjkm-registry](https://github.com/pr1m8/pjkm-registry) adding your entry to `index.json`.

See the full guide at `docs_internal/PACK_AUTHORING.md`.
