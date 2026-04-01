"""Template system tests."""

from __future__ import annotations

import pytest

from pjkm.core.templates.loader import TemplateLoader, TemplateNotFoundError


class TestTemplateLoader:
    """Test template path resolution."""

    def test_resolve_base(self):
        loader = TemplateLoader()
        path = loader.resolve("base")
        assert path.exists()
        assert (path / "copier.yml").exists()

    def test_resolve_single_package(self):
        loader = TemplateLoader()
        path = loader.resolve("single_package")
        assert path.exists()

    def test_resolve_service(self):
        loader = TemplateLoader()
        path = loader.resolve("service")
        assert path.exists()

    def test_resolve_fragment(self):
        loader = TemplateLoader()
        path = loader.resolve("fragments/logging_structlog")
        assert path.exists()
        assert (path / "copier.yml").exists()

    def test_resolve_nonexistent(self):
        loader = TemplateLoader()
        with pytest.raises(TemplateNotFoundError):
            loader.resolve("nonexistent_template")

    def test_list_builtin(self):
        loader = TemplateLoader()
        templates = loader.list_builtin()
        assert "base" in templates
        assert "single_package" in templates
        assert "service" in templates

    def test_resolve_all_archetypes(self):
        loader = TemplateLoader()
        for name in ["base", "single_package", "service", "poly_repo", "script_tool"]:
            path = loader.resolve(name)
            assert path.exists(), f"Template {name} not found"
            assert (path / "copier.yml").exists(), f"Template {name} missing copier.yml"

    def test_resolve_all_fragments(self):
        loader = TemplateLoader()
        for name in [
            "logging_structlog",
            "infra_otel",
            "docs_sphinx",
            "database_alembic",
            "infra_nginx",
            "docker_python",
            "k8s_manifests",
            "celery_worker",
            "frontend_next",
        ]:
            path = loader.resolve(f"fragments/{name}")
            assert path.exists(), f"Fragment {name} not found"


class TestGroupRegistry:
    """Test that all group definitions load and are valid."""

    def test_all_groups_load(self):
        from pjkm.core.groups.registry import GroupRegistry

        registry = GroupRegistry()
        registry.load_builtin()
        groups = registry.list_all()
        assert len(groups) >= 25

    def test_all_group_fragments_exist(self):
        """Every fragment referenced by a group must exist as a template."""
        from pjkm.core.groups.registry import GroupRegistry
        from pjkm.core.templates.loader import TemplateLoader

        registry = GroupRegistry()
        registry.load_builtin()
        loader = TemplateLoader()

        for group in registry.list_all():
            for sf in group.scaffolded_files:
                path = loader.resolve(f"fragments/{sf.template_fragment}")
                assert path.exists(), (
                    f"Group '{group.id}' references missing fragment: {sf.template_fragment}"
                )

    def test_group_ids_unique(self):
        from pjkm.core.groups.registry import GroupRegistry

        registry = GroupRegistry()
        registry.load_builtin()
        ids = [g.id for g in registry.list_all()]
        assert len(ids) == len(set(ids)), "Duplicate group IDs found"

    def test_group_requires_exist(self):
        """All requires_groups references must point to existing groups."""
        from pjkm.core.groups.registry import GroupRegistry

        registry = GroupRegistry()
        registry.load_builtin()
        all_ids = {g.id for g in registry.list_all()}
        for group in registry.list_all():
            for req in group.requires_groups:
                assert req in all_ids, f"Group '{group.id}' requires unknown group: {req}"

    def test_load_custom_directory(self, tmp_path):
        """Custom groups can be loaded from an arbitrary directory."""
        import yaml

        from pjkm.core.groups.registry import GroupRegistry

        group_data = {
            "id": "custom_test",
            "name": "Custom Test",
            "description": "Test custom group loading",
            "archetypes": [],
            "requires_groups": [],
            "platform_filter": None,
            "dependencies": {"custom_test": ["requests>=2.0"]},
            "scaffolded_files": [],
            "pyproject_tool_config": {},
        }
        (tmp_path / "custom_test.yaml").write_text(yaml.dump(group_data))

        registry = GroupRegistry()
        count = registry.load_directory(tmp_path)
        assert count == 1
        assert registry.get("custom_test") is not None
        assert registry.get("custom_test").name == "Custom Test"

    def test_import_from_pyproject(self, tmp_path):
        """Groups can be imported from a pyproject.toml."""
        from pjkm.core.groups.registry import GroupRegistry

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""\
[project]
name = "test-pkg"

[project.optional-dependencies]
ml = ["scikit-learn>=1.0", "numpy>=1.26"]
viz = ["matplotlib>=3.0"]
""")

        out = tmp_path / "imported"
        created = GroupRegistry.import_from_pyproject(pyproject, out)
        assert len(created) == 2

        # Verify the imported files are valid group definitions
        registry = GroupRegistry()
        loaded = registry.load_directory(out)
        assert loaded == 2
        ml = registry.get("ml")
        assert ml is not None
        assert "scikit-learn>=1.0" in ml.dependencies["ml"]

    def test_import_specific_sections(self, tmp_path):
        """Only specified sections are imported."""
        from pjkm.core.groups.registry import GroupRegistry

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""\
[project]
name = "test-pkg"

[project.optional-dependencies]
data = ["pandas>=2.0"]
ml = ["scikit-learn>=1.0"]
dev = ["pytest>=8.0"]
""")

        out = tmp_path / "imported"
        created = GroupRegistry.import_from_pyproject(pyproject, out, sections=["data", "ml"])
        assert len(created) == 2
        assert (out / "data.yaml").exists()
        assert (out / "ml.yaml").exists()
        assert not (out / "dev.yaml").exists()
