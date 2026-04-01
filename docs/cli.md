# CLI Reference

## Project Lifecycle

```bash
pjkm init NAME [-a ARCH] [-g GROUP...] [--recipe NAME] [--dry-run]
pjkm add -g GROUP... [-d DIR]
pjkm update [-d DIR] [--dry-run]
pjkm upgrade [-g GROUP...] [--latest] [--refresh-tools] [--dry-run]
pjkm link TOOL [-d DIR] [--dry-run]
pjkm preview [ARCH] [-g GROUP...] [--recipe NAME]
```

## Discovery

```bash
pjkm list [archetypes|groups]
pjkm info GROUP_ID
pjkm recommend ARCH [--preset NAME]
pjkm recipe [NAME] [--show]
pjkm doctor
```

## Existing Projects

```bash
pjkm adopt [--dir DIR] [--apply]
pjkm status [--dir DIR]
```

## Registry

```bash
pjkm search [QUERY] [--refresh]
pjkm install PACK [--no-sync]
pjkm uninstall PACK
pjkm installed
```

## Workspace

```bash
pjkm workspace NAME [-s name:template...] [--blueprint NAME] [--dry-run]
```

## Group Management

```bash
pjkm group create ID [--name] [--dir]
pjkm group import PYPROJECT [--section...] [--dir]
pjkm group validate [PATH]
pjkm group list
pjkm group sync [NAME]
pjkm group source add URL [--name] [--path] [--ref]
pjkm group source list
pjkm group source remove NAME
```

## Configuration

```bash
pjkm defaults [--init] [--global]
pjkm tui
pjkm --version
```
