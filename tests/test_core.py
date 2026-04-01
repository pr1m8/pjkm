"""Core module tests — models, utils, registry."""

from __future__ import annotations

import pytest


class TestDeepMerge:
    def test_simple_merge(self):
        from pjkm.core.utils import deep_merge

        target = {}
        deep_merge(target, "ruff.lint", {"select": ["E"]})
        assert target == {"ruff": {"lint": {"select": ["E"]}}}

    def test_nested_merge(self):
        from pjkm.core.utils import deep_merge

        target = {"ruff": {"format": {"quote-style": "double"}}}
        deep_merge(target, "ruff.lint", {"select": ["F"]})
        assert target["ruff"]["format"]["quote-style"] == "double"
        assert target["ruff"]["lint"]["select"] == ["F"]

    def test_existing_key_update(self):
        from pjkm.core.utils import deep_merge

        target = {"tool": {"ruff": {"lint": {"select": ["E"]}}}}
        deep_merge(target["tool"], "ruff.lint", {"ignore": ["E501"]})
        assert "select" in target["tool"]["ruff"]["lint"]
        assert "ignore" in target["tool"]["ruff"]["lint"]


class TestPackageGroupModel:
    def test_defaults(self):
        from pjkm.core.models.group import PackageGroup

        g = PackageGroup(id="test", name="Test")
        assert g.category == "Core Dev"
        assert g.archetypes == []
        assert g.requires_groups == []
        assert g.dependencies == {}
        assert g.scaffolded_files == []

    def test_with_category(self):
        from pjkm.core.models.group import PackageGroup

        g = PackageGroup(id="test", name="Test", category="AI / ML")
        assert g.category == "AI / ML"


class TestGroupRegistry:
    def test_load_builtin(self):
        from pjkm.core.groups.registry import GroupRegistry

        reg = GroupRegistry()
        reg.load_builtin()
        assert len(reg.group_ids) >= 100

    def test_get_group(self):
        from pjkm.core.groups.registry import GroupRegistry

        reg = GroupRegistry()
        reg.load_builtin()
        g = reg.get("api")
        assert g is not None
        assert g.name == "API Framework"

    def test_get_unknown(self):
        from pjkm.core.groups.registry import GroupRegistry

        reg = GroupRegistry()
        reg.load_builtin()
        assert reg.get("nonexistent_xyz") is None

    def test_list_for_archetype(self):
        from pjkm.core.groups.registry import GroupRegistry

        reg = GroupRegistry()
        reg.load_builtin()
        service_groups = reg.list_for_archetype("service")
        assert len(service_groups) > 0

    def test_categories_in_yaml(self):
        from pjkm.core.groups.registry import GroupRegistry

        reg = GroupRegistry()
        reg.load_builtin()
        categories = {g.category for g in reg.list_all()}
        assert "Core Dev" in categories
        assert "AI / ML" in categories
        assert "Web & API" in categories


class TestGroupResolver:
    def test_resolve_simple(self):
        from pjkm.core.groups.registry import GroupRegistry
        from pjkm.core.groups.resolver import GroupResolver

        reg = GroupRegistry()
        reg.load_builtin()
        resolver = GroupResolver({g.id: g for g in reg.list_all()})
        resolved = resolver.resolve(["logging"])
        assert any(g.id == "logging" for g in resolved)

    def test_resolve_with_deps(self):
        from pjkm.core.groups.registry import GroupRegistry
        from pjkm.core.groups.resolver import GroupResolver

        reg = GroupRegistry()
        reg.load_builtin()
        resolver = GroupResolver({g.id: g for g in reg.list_all()})
        resolved = resolver.resolve(["dev"])
        ids = {g.id for g in resolved}
        # dev requires linting, testing, typecheck, coverage
        assert "linting" in ids
        assert "testing" in ids


class TestTemplateLoader:
    def test_resolve_base(self):
        from pjkm.core.templates.loader import TemplateLoader

        loader = TemplateLoader()
        path = loader.resolve("base")
        assert path.exists()
        assert (path / "copier.yml").exists()

    def test_resolve_fragment(self):
        from pjkm.core.templates.loader import TemplateLoader

        loader = TemplateLoader()
        path = loader.resolve("fragments/api_app")
        assert path.exists()

    def test_resolve_not_found(self):
        from pjkm.core.templates.loader import TemplateLoader, TemplateNotFoundError

        loader = TemplateLoader()
        with pytest.raises(TemplateNotFoundError):
            loader.resolve("nonexistent_template_xyz")
