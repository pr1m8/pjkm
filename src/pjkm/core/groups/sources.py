"""Remote group source management: clone, cache, and sync git repos of group definitions."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

CACHE_DIR = Path.home() / ".pjkm" / "cache" / "sources"
SOURCES_FILE = Path.home() / ".pjkm" / "sources.yaml"


def _slug_from_url(url: str) -> str:
    """Derive a filesystem-safe slug from a git URL."""
    # git@github.com:org/repo.git -> org-repo
    # https://github.com/org/repo.git -> org-repo
    clean = url.rstrip("/").removesuffix(".git")
    if ":" in clean and "@" in clean:
        # SSH: git@host:org/repo
        clean = clean.split(":")[-1]
    else:
        # HTTPS: scheme://host/org/repo
        clean = "/".join(clean.split("/")[-2:])
    slug = clean.replace("/", "-").replace(".", "-")
    # Add a short hash for uniqueness
    h = hashlib.sha256(url.encode()).hexdigest()[:8]
    return f"{slug}-{h}"


def _run_git(
    args: list[str], cwd: str | Path | None = None, timeout: int = 60
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class SourceEntry:
    """A registered group source."""

    def __init__(self, url: str, name: str = "", path: str = "", ref: str = "") -> None:
        self.url = url
        self.name = name or _slug_from_url(url)
        self.path = path  # subdirectory within repo containing .yaml files
        self.ref = ref  # branch/tag/commit

    @property
    def cache_dir(self) -> Path:
        return CACHE_DIR / self.name

    @property
    def groups_dir(self) -> Path:
        """The directory containing group YAML files within the cached repo."""
        base = self.cache_dir
        if self.path:
            return base / self.path
        return base

    def to_dict(self) -> dict[str, str]:
        d: dict[str, str] = {"url": self.url}
        if self.name:
            d["name"] = self.name
        if self.path:
            d["path"] = self.path
        if self.ref:
            d["ref"] = self.ref
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceEntry:
        return cls(
            url=data["url"],
            name=data.get("name", ""),
            path=data.get("path", ""),
            ref=data.get("ref", ""),
        )


class GroupSourceManager:
    """Manages remote git repositories that provide group definitions.

    Sources are registered in ~/.pjkm/sources.yaml and cached in
    ~/.pjkm/cache/sources/<name>/. They can also be declared in
    .pjkmrc.yaml under `group_sources:`.
    """

    def __init__(self) -> None:
        self._sources: list[SourceEntry] = []

    def load(self) -> None:
        """Load registered sources from ~/.pjkm/sources.yaml."""
        if not SOURCES_FILE.exists():
            return
        try:
            data = yaml.safe_load(SOURCES_FILE.read_text()) or {}
            for entry in data.get("sources", []):
                self._sources.append(SourceEntry.from_dict(entry))
        except Exception:
            pass

    def load_from_defaults(self, sources: list[dict[str, str]]) -> None:
        """Load additional sources from UserDefaults.group_sources."""
        for entry in sources:
            src = SourceEntry.from_dict(entry) if isinstance(entry, dict) else entry
            # Avoid duplicates by URL
            if not any(s.url == src.url for s in self._sources):
                self._sources.append(src)

    def save(self) -> None:
        """Persist the source list to ~/.pjkm/sources.yaml."""
        SOURCES_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {"sources": [s.to_dict() for s in self._sources]}
        SOURCES_FILE.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False)
        )

    @property
    def sources(self) -> list[SourceEntry]:
        return list(self._sources)

    def add(
        self, url: str, name: str = "", path: str = "", ref: str = ""
    ) -> SourceEntry:
        """Register a new group source."""
        entry = SourceEntry(url=url, name=name, path=path, ref=ref)
        # Replace if same name exists
        self._sources = [s for s in self._sources if s.name != entry.name]
        self._sources.append(entry)
        self.save()
        return entry

    def remove(self, name: str) -> bool:
        """Remove a registered source by name. Returns True if found."""
        before = len(self._sources)
        self._sources = [s for s in self._sources if s.name != name]
        if len(self._sources) < before:
            self.save()
            # Clean up cache
            cache = CACHE_DIR / name
            if cache.exists():
                import shutil

                shutil.rmtree(cache)
            return True
        return False

    def sync(self, name: str | None = None) -> list[tuple[SourceEntry, bool, str]]:
        """Clone or pull registered sources.

        Args:
            name: If given, only sync this source. Otherwise sync all.

        Returns:
            List of (source, success, message) tuples.
        """
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        results: list[tuple[SourceEntry, bool, str]] = []

        targets = (
            self._sources
            if name is None
            else [s for s in self._sources if s.name == name]
        )

        for source in targets:
            try:
                if source.cache_dir.exists() and (source.cache_dir / ".git").exists():
                    # Pull
                    _run_git(["fetch", "--quiet"], cwd=source.cache_dir, timeout=30)
                    ref = source.ref or "origin/HEAD"
                    _run_git(["reset", "--hard", ref], cwd=source.cache_dir, timeout=10)
                    results.append((source, True, "updated"))
                else:
                    # Clone
                    clone_args = ["clone", "--quiet", "--depth", "1"]
                    if source.ref:
                        clone_args.extend(["--branch", source.ref])
                    clone_args.extend([source.url, str(source.cache_dir)])
                    result = _run_git(clone_args, timeout=60)
                    if result.returncode != 0:
                        results.append((source, False, result.stderr.strip()))
                    else:
                        results.append((source, True, "cloned"))
            except subprocess.TimeoutExpired:
                results.append((source, False, "timeout"))
            except Exception as e:
                results.append((source, False, str(e)))

        return results

    def get_all_group_dirs(self) -> list[tuple[str, Path]]:
        """Return (source_name, groups_dir) for all cached sources that exist."""
        dirs: list[tuple[str, Path]] = []
        for source in self._sources:
            gd = source.groups_dir
            if gd.is_dir() and any(gd.glob("*.yaml")):
                dirs.append((source.name, gd))
        return dirs
