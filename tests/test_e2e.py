"""End-to-end integration tests for all archetypes."""

import pytest

from pjkm.core.engine.project_engine import ProjectEngine
from pjkm.core.models.project import Archetype, ProjectConfig
from pjkm.core.tasks.defaults import create_default_registry


@pytest.fixture
def registry():
    return create_default_registry()


@pytest.fixture
def engine(registry):
    return ProjectEngine(task_registry=registry)


class TestSinglePackage:
    def test_scaffold(self, tmp_path, engine):
        config = ProjectConfig(
            project_name="my-lib",
            archetype=Archetype.SINGLE_PACKAGE,
            target_dir=tmp_path,
        )
        result = engine.execute(config)
        assert result.success

        project = tmp_path / "my-lib"
        assert (project / "pyproject.toml").exists()
        assert (project / "README.md").exists()
        assert (project / ".gitignore").exists()
        assert (project / ".editorconfig").exists()
        assert (project / "src" / "my_lib" / "__init__.py").exists()
        assert (project / "src" / "my_lib" / "py.typed").exists()
        assert (project / "tests" / "__init__.py").exists()
        assert (project / "tests" / "conftest.py").exists()
        assert (project / "tests" / "test_my_lib.py").exists()
        assert (project / ".git").is_dir()
        assert (project / ".pre-commit-config.yaml").exists()
        assert (project / ".trunk" / "trunk.yaml").exists()


class TestService:
    def test_scaffold(self, tmp_path, engine):
        config = ProjectConfig(
            project_name="my-svc",
            archetype=Archetype.SERVICE,
            target_dir=tmp_path,
        )
        result = engine.execute(config)
        assert result.success

        project = tmp_path / "my-svc"
        assert (project / "pyproject.toml").exists()
        assert (project / "Makefile").exists()
        assert (project / "infra" / "compose.yaml").exists()
        assert (project / ".env.example").exists()
        assert (project / ".secrets.example").exists()
        assert (project / ".config" / "yamllint.yaml").exists()
        assert (project / ".config" / ".markdownlint-cli2.yaml").exists()
        assert (project / "src" / "my_svc" / "__init__.py").exists()
        assert (project / "src" / "my_svc" / "core" / "__init__.py").exists()
        assert (project / "scripts" / ".gitkeep").exists()


class TestPolyRepo:
    def test_scaffold(self, tmp_path, engine):
        config = ProjectConfig(
            project_name="my-mono",
            archetype=Archetype.POLY_REPO,
            target_dir=tmp_path,
        )
        result = engine.execute(config)
        assert result.success

        project = tmp_path / "my-mono"
        assert (project / "pyproject.toml").exists()
        assert (project / "Makefile").exists()
        assert (project / "infra" / "compose.yaml").exists()
        assert (project / "packages" / ".gitkeep").exists()
        assert (project / "tools" / ".gitkeep").exists()
        assert (project / "scripts" / ".gitkeep").exists()
        assert (project / ".env.example").exists()
        assert (project / ".secrets.example").exists()


class TestScriptTool:
    def test_scaffold(self, tmp_path, engine):
        config = ProjectConfig(
            project_name="my-tool",
            archetype=Archetype.SCRIPT_TOOL,
            target_dir=tmp_path,
        )
        result = engine.execute(config)
        assert result.success

        project = tmp_path / "my-tool"
        assert (project / "pyproject.toml").exists()
        assert (project / "src" / "my_tool" / "__init__.py").exists()
        assert (project / "src" / "my_tool" / "__main__.py").exists()
        assert (project / "src" / "my_tool" / "cli.py").exists()
        assert (project / "tests" / "test_cli.py").exists()


class TestWithGroups:
    def test_dev_group_adds_optional_deps(self, tmp_path, engine):
        config = ProjectConfig(
            project_name="grouped",
            archetype=Archetype.SINGLE_PACKAGE,
            target_dir=tmp_path,
            selected_groups=["dev"],
        )
        result = engine.execute(config)
        assert result.success

        pyproject = (tmp_path / "grouped" / "pyproject.toml").read_text()
        assert "ruff" in pyproject
        assert "pytest" in pyproject
        assert "pyright" in pyproject
        assert "coverage" in pyproject

    def test_logging_group_adds_deps(self, tmp_path, engine):
        config = ProjectConfig(
            project_name="with-logging",
            archetype=Archetype.SERVICE,
            target_dir=tmp_path,
            selected_groups=["logging"],
        )
        result = engine.execute(config)
        assert result.success

        pyproject = (tmp_path / "with-logging" / "pyproject.toml").read_text()
        assert "structlog" in pyproject
        assert "rich" in pyproject

    def test_existing_dir_fails(self, tmp_path, engine):
        from pjkm.core.engine.task_runner import TaskRunError

        # Pre-create the directory with a file in it
        project_dir = tmp_path / "existing"
        project_dir.mkdir()
        (project_dir / "somefile.txt").write_text("exists")

        config = ProjectConfig(
            project_name="existing",
            archetype=Archetype.SINGLE_PACKAGE,
            target_dir=tmp_path,
        )
        with pytest.raises(TaskRunError, match="already exists"):
            engine.execute(config)
