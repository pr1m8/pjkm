"""Group resolver: expand selected groups including transitive dependencies."""

from __future__ import annotations

from pjkm.core.models.group import PackageGroup
from pjkm.core.models.platform import PlatformInfo


class GroupResolutionError(Exception):
    """Raised when group resolution fails (missing group, circular deps)."""


class GroupResolver:
    """Resolves selected group IDs into a fully-expanded, ordered list of PackageGroups."""

    def __init__(self, groups: dict[str, PackageGroup]) -> None:
        self._groups = groups

    def resolve(
        self,
        selected_ids: list[str],
        platform: PlatformInfo | None = None,
    ) -> list[PackageGroup]:
        """Expand selected groups, resolving requires_groups transitively.

        Returns groups in dependency order (dependencies before dependents).
        Filters out groups that don't match the current platform.
        """
        # Expand transitively
        all_ids: set[str] = set()
        ordered: list[str] = []
        visiting: set[str] = set()

        for gid in selected_ids:
            self._expand(gid, all_ids, ordered, visiting)

        # Filter by platform
        result: list[PackageGroup] = []
        for gid in ordered:
            group = self._groups[gid]
            if platform and group.platform_filter:
                if group.platform_filter != platform.os:
                    continue
            result.append(group)

        return result

    def _expand(
        self,
        group_id: str,
        seen: set[str],
        ordered: list[str],
        visiting: set[str],
    ) -> None:
        if group_id in seen:
            return
        if group_id in visiting:
            msg = f"Circular group dependency detected involving {group_id!r}"
            raise GroupResolutionError(msg)
        if group_id not in self._groups:
            msg = f"Unknown group {group_id!r}"
            raise GroupResolutionError(msg)

        visiting.add(group_id)
        group = self._groups[group_id]

        for dep_id in group.requires_groups:
            self._expand(dep_id, seen, ordered, visiting)

        visiting.discard(group_id)
        seen.add(group_id)
        ordered.append(group_id)
