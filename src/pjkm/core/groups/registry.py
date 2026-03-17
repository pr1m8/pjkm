"""Group registry: discover and load package group definitions from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pjkm.core.models.group import PackageGroup

DEFINITIONS_DIR = Path(__file__).parent / "definitions"

# Standard search paths for custom group definitions
CUSTOM_GROUP_PATHS = [
    Path.home() / ".pjkm" / "groups",
    Path.cwd() / ".pjkm" / "groups",
]


class GroupRegistry:
    """Loads and provides access to package group definitions."""

    def __init__(self) -> None:
        self._groups: dict[str, PackageGroup] = {}

    def load_builtin(self) -> None:
        """Load all YAML group definitions from the built-in definitions directory."""
        if not DEFINITIONS_DIR.exists():
            return
        for path in sorted(DEFINITIONS_DIR.glob("*.yaml")):
            self.load_file(path)

    def load_custom(self) -> list[Path]:
        """Load custom group definitions from ~/.pjkm/groups/ and ./.pjkm/groups/.

        Custom groups override built-in groups with the same ID.
        Returns list of directories that were loaded.
        """
        loaded_dirs: list[Path] = []
        for group_dir in CUSTOM_GROUP_PATHS:
            if group_dir.is_dir():
                for path in sorted(group_dir.glob("*.yaml")):
                    self.load_file(path)
                loaded_dirs.append(group_dir)
        return loaded_dirs

    def load_sources(self) -> list[tuple[str, int]]:
        """Load group definitions from all registered remote sources.

        Reads ~/.pjkm/sources.yaml and .pjkmrc.yaml group_sources,
        then loads cached repos. Sources must be synced first via
        `pjkm group source sync`.

        Returns list of (source_name, group_count) tuples.
        """
        from pjkm.core.defaults import UserDefaults
        from pjkm.core.groups.sources import GroupSourceManager

        mgr = GroupSourceManager()
        mgr.load()

        # Also pull sources from .pjkmrc.yaml
        try:
            defaults = UserDefaults.load()
            if defaults.group_sources:
                mgr.load_from_defaults([s.model_dump() for s in defaults.group_sources])
        except Exception:
            pass

        loaded: list[tuple[str, int]] = []
        for name, groups_dir in mgr.get_all_group_dirs():
            count = self.load_directory(groups_dir)
            if count > 0:
                loaded.append((name, count))
        return loaded

    def load_plugins(self) -> list[tuple[str, int]]:
        """Load groups from installed plugins via entry points."""
        from importlib.metadata import entry_points

        loaded = []
        for ep in entry_points(group="pjkm.groups"):
            try:
                groups_dir = ep.load()()
                if isinstance(groups_dir, Path) and groups_dir.is_dir():
                    count = self.load_directory(groups_dir)
                    if count > 0:
                        loaded.append((ep.name, count))
            except Exception:
                pass  # Skip broken plugins silently
        return loaded

    def load_all(self) -> None:
        """Load all groups: built-in + custom local + remote sources + plugins."""
        self.load_builtin()
        self.load_custom()
        self.load_sources()
        self.load_plugins()

    def load_directory(self, directory: Path) -> int:
        """Load all YAML group definitions from an arbitrary directory.

        Returns count of groups loaded.
        """
        count = 0
        if not directory.is_dir():
            return count
        for path in sorted(directory.glob("*.yaml")):
            self.load_file(path)
            count += 1
        return count

    def load_file(self, path: Path) -> PackageGroup:
        """Load a single YAML group definition."""
        with open(path) as f:
            data = yaml.safe_load(f)
        group = PackageGroup.model_validate(data)
        self._groups[group.id] = group
        return group

    def get(self, group_id: str) -> PackageGroup | None:
        return self._groups.get(group_id)

    def list_all(self) -> list[PackageGroup]:
        return list(self._groups.values())

    def list_for_archetype(self, archetype: str) -> list[PackageGroup]:
        """Return groups applicable to a given archetype (empty archetypes = all)."""
        return [
            g
            for g in self._groups.values()
            if not g.archetypes or archetype in g.archetypes
        ]

    @property
    def group_ids(self) -> list[str]:
        return list(self._groups.keys())

    @staticmethod
    def import_from_pyproject(
        pyproject_path: Path,
        output_dir: Path,
        sections: list[str] | None = None,
    ) -> list[Path]:
        """Import optional dependency groups from a pyproject.toml into YAML group files.

        Reads [project.optional-dependencies] from the given pyproject.toml
        and creates a .yaml group definition for each section (or specified sections).

        Returns list of created YAML files.
        """
        import tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        opt_deps: dict[str, list[str]] = project.get("optional-dependencies", {})

        if not opt_deps:
            return []

        # Get project name for descriptions
        project_name = project.get("name", pyproject_path.parent.name)

        output_dir.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []

        for section, deps in opt_deps.items():
            if sections and section not in sections:
                continue

            group_id = section.replace("-", "_")
            group_data: dict[str, Any] = {
                "id": group_id,
                "name": _section_to_name(section),
                "description": f"Imported from {project_name} [{section}]",
                "archetypes": [],
                "requires_groups": [],
                "platform_filter": None,
                "dependencies": {group_id: list(deps)},
                "scaffolded_files": [],
                "pyproject_tool_config": {},
            }

            out_path = output_dir / f"{group_id}.yaml"
            with open(out_path, "w") as f:
                yaml.dump(group_data, f, default_flow_style=False, sort_keys=False)
            created.append(out_path)

        return created


def _section_to_name(section: str) -> str:
    """Convert a pyproject section name to a human-readable name."""
    return section.replace("-", " ").replace("_", " ").title()
