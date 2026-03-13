"""Tests for group registry and resolver."""

import pytest

from pjkm.core.groups.resolver import GroupResolutionError, GroupResolver
from pjkm.core.models.group import PackageGroup
from pjkm.core.models.platform import PlatformInfo


def _make_group(
    id: str, requires: list[str] | None = None, platform: str | None = None
) -> PackageGroup:
    return PackageGroup(
        id=id,
        name=id.title(),
        requires_groups=requires or [],
        platform_filter=platform,
    )


class TestGroupResolver:
    def test_single_group(self):
        groups = {"logging": _make_group("logging")}
        resolver = GroupResolver(groups)
        result = resolver.resolve(["logging"])
        assert [g.id for g in result] == ["logging"]

    def test_transitive_deps(self):
        groups = {
            "logging": _make_group("logging"),
            "otel": _make_group("otel", requires=["logging"]),
        }
        resolver = GroupResolver(groups)
        result = resolver.resolve(["otel"])
        ids = [g.id for g in result]
        assert ids == ["logging", "otel"]

    def test_deep_transitive(self):
        groups = {
            "a": _make_group("a"),
            "b": _make_group("b", requires=["a"]),
            "c": _make_group("c", requires=["b"]),
        }
        resolver = GroupResolver(groups)
        result = resolver.resolve(["c"])
        ids = [g.id for g in result]
        assert ids == ["a", "b", "c"]

    def test_dedup_shared_dep(self):
        groups = {
            "a": _make_group("a"),
            "b": _make_group("b", requires=["a"]),
            "c": _make_group("c", requires=["a"]),
        }
        resolver = GroupResolver(groups)
        result = resolver.resolve(["b", "c"])
        ids = [g.id for g in result]
        assert ids.count("a") == 1
        assert "b" in ids
        assert "c" in ids

    def test_unknown_group_raises(self):
        resolver = GroupResolver({})
        with pytest.raises(GroupResolutionError, match="Unknown group"):
            resolver.resolve(["nonexistent"])

    def test_circular_dep_raises(self):
        groups = {
            "a": _make_group("a", requires=["b"]),
            "b": _make_group("b", requires=["a"]),
        }
        resolver = GroupResolver(groups)
        with pytest.raises(GroupResolutionError, match="Circular"):
            resolver.resolve(["a"])

    def test_platform_filter_excludes(self):
        groups = {
            "mac_stuff": _make_group("mac_stuff", platform="darwin"),
            "logging": _make_group("logging"),
        }
        resolver = GroupResolver(groups)
        linux = PlatformInfo(os="linux", arch="x86_64")
        result = resolver.resolve(["mac_stuff", "logging"], platform=linux)
        ids = [g.id for g in result]
        assert "mac_stuff" not in ids
        assert "logging" in ids

    def test_platform_filter_includes(self):
        groups = {
            "mac_stuff": _make_group("mac_stuff", platform="darwin"),
        }
        resolver = GroupResolver(groups)
        mac = PlatformInfo(os="darwin", arch="arm64")
        result = resolver.resolve(["mac_stuff"], platform=mac)
        assert [g.id for g in result] == ["mac_stuff"]

    def test_empty_selection(self):
        groups = {"a": _make_group("a")}
        resolver = GroupResolver(groups)
        assert resolver.resolve([]) == []
