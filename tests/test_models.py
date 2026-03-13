"""Tests for core Pydantic models."""

import pytest

from pjkm.core.models.group import PackageGroup, ScaffoldedFile
from pjkm.core.models.platform import PlatformInfo
from pjkm.core.models.project import Archetype, ProjectConfig
from pjkm.core.models.task import Phase, TaskDefinition, TaskResult


class TestProjectConfig:
    def test_basic_creation(self):
        config = ProjectConfig(
            project_name="my-project",
            archetype=Archetype.SINGLE_PACKAGE,
        )
        assert config.project_name == "my-project"
        assert config.archetype == Archetype.SINGLE_PACKAGE
        assert config.python_version == "3.13"
        assert config.selected_groups == []
        assert config.dry_run is False

    def test_project_slug(self):
        config = ProjectConfig(
            project_name="My-Cool Project",
            archetype=Archetype.SINGLE_PACKAGE,
        )
        assert config.project_slug == "my_cool_project"

    def test_project_slug_special_chars(self):
        config = ProjectConfig(
            project_name="foo.bar-baz",
            archetype=Archetype.SERVICE,
        )
        assert config.project_slug == "foo_bar_baz"

    def test_project_dir(self, tmp_path):
        config = ProjectConfig(
            project_name="test-proj",
            archetype=Archetype.SCRIPT_TOOL,
            target_dir=tmp_path,
        )
        assert config.project_dir == tmp_path / "test-proj"

    def test_invalid_python_version(self):
        with pytest.raises(ValueError, match="X.Y format"):
            ProjectConfig(
                project_name="test",
                archetype=Archetype.SINGLE_PACKAGE,
                python_version="3.13.1",
            )

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError):
            ProjectConfig(project_name="", archetype=Archetype.SINGLE_PACKAGE)


class TestArchetype:
    def test_all_archetypes_exist(self):
        assert len(Archetype) == 4
        assert Archetype.SINGLE_PACKAGE == "single_package"
        assert Archetype.SERVICE == "service"
        assert Archetype.POLY_REPO == "poly_repo"
        assert Archetype.SCRIPT_TOOL == "script_tool"

    def test_from_string(self):
        assert Archetype("service") == Archetype.SERVICE


class TestPhase:
    def test_phase_ordering(self):
        assert Phase.SCAFFOLD < Phase.CONFIGURE < Phase.INSTALL < Phase.VERIFY

    def test_sorted_phases(self):
        phases = sorted([Phase.VERIFY, Phase.SCAFFOLD, Phase.INSTALL, Phase.CONFIGURE])
        assert phases == [Phase.SCAFFOLD, Phase.CONFIGURE, Phase.INSTALL, Phase.VERIFY]


class TestTaskDefinition:
    def test_basic(self):
        td = TaskDefinition(id="init_project", phase=Phase.SCAFFOLD)
        assert td.id == "init_project"
        assert td.depends_on == []

    def test_with_deps(self):
        td = TaskDefinition(
            id="init_src",
            phase=Phase.SCAFFOLD,
            depends_on=["init_project"],
            description="Create src layout",
        )
        assert td.depends_on == ["init_project"]


class TestTaskResult:
    def test_success(self):
        r = TaskResult(task_id="t1", success=True, message="ok")
        assert r.success
        assert not r.skipped

    def test_skip(self):
        r = TaskResult(task_id="t1", success=True, skipped=True)
        assert r.skipped


class TestPackageGroup:
    def test_basic_group(self):
        g = PackageGroup(
            id="logging",
            name="Structured Logging",
            dependencies={"logging": ["rich>=14.0.0", "structlog>=25.0.0"]},
        )
        assert g.id == "logging"
        assert len(g.dependencies["logging"]) == 2
        assert g.archetypes == []
        assert g.requires_groups == []

    def test_group_with_scaffold(self):
        g = PackageGroup(
            id="otel",
            name="OpenTelemetry",
            requires_groups=["logging"],
            scaffolded_files=[
                ScaffoldedFile(
                    template_fragment="infra_otel",
                    destination="infra/",
                )
            ],
        )
        assert g.requires_groups == ["logging"]
        assert len(g.scaffolded_files) == 1


class TestPlatformInfo:
    def test_auto_detect(self):
        info = PlatformInfo()
        assert info.os in ("darwin", "linux", "windows")
        assert info.arch != ""

    def test_has_tool(self):
        info = PlatformInfo()
        # python should always be available in test env
        assert info.has_tool("python3") or info.has_tool("python")

    def test_has_tool_nonexistent(self):
        info = PlatformInfo()
        assert not info.has_tool("nonexistent_tool_xyz_123")
