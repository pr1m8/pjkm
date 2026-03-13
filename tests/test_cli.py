"""CLI command tests."""

from __future__ import annotations

from typer.testing import CliRunner

from pjkm.cli.app import app

runner = CliRunner()


class TestVersionFlag:
    """Test --version flag."""

    def test_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "pjkm" in result.stdout
        assert "0.1.0" in result.stdout


class TestListCommand:
    """Test the list command."""

    def test_list_archetypes(self):
        result = runner.invoke(app, ["list", "archetypes"])
        assert result.exit_code == 0
        assert "single_package" in result.stdout
        assert "service" in result.stdout
        assert "poly_repo" in result.stdout
        assert "script_tool" in result.stdout

    def test_list_groups(self):
        result = runner.invoke(app, ["list", "groups"])
        assert result.exit_code == 0
        assert "logging" in result.stdout
        assert "testing" in result.stdout
        assert "dev" in result.stdout

    def test_list_groups_shows_columns(self):
        result = runner.invoke(app, ["list", "groups"])
        assert result.exit_code == 0
        assert "Requires" in result.stdout
        assert "Archetypes" in result.stdout
        assert "Scaffold" in result.stdout

    def test_list_invalid(self):
        result = runner.invoke(app, ["list", "invalid"])
        assert "Unknown" in result.stdout or result.exit_code == 0


class TestInitCommand:
    """Test the init command."""

    def test_init_invalid_archetype(self):
        result = runner.invoke(app, ["init", "test-proj", "--archetype", "invalid"])
        assert result.exit_code != 0

    def test_init_accepts_hyphens(self, tmp_path):
        result = runner.invoke(
            app,
            [
                "init",
                "test-proj",
                "--archetype",
                "single-package",
                "--dir",
                str(tmp_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "single_package" in result.stdout

    def test_init_dry_run(self, tmp_path):
        result = runner.invoke(
            app,
            [
                "init",
                "test-proj",
                "--archetype",
                "single_package",
                "--dir",
                str(tmp_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "dry run" in result.stdout.lower() or "Dry run" in result.stdout

    def test_init_with_author(self, tmp_path):
        result = runner.invoke(
            app,
            [
                "init",
                "test-proj",
                "--archetype",
                "single_package",
                "--dir",
                str(tmp_path),
                "--author",
                "Test Author",
                "--email",
                "test@example.com",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0


class TestInfoCommand:
    """Test the info command."""

    def test_info_known_group(self):
        result = runner.invoke(app, ["info", "logging"])
        assert result.exit_code == 0
        assert "Structured Logging" in result.stdout
        assert "rich" in result.stdout

    def test_info_unknown_group(self):
        result = runner.invoke(app, ["info", "nonexistent"])
        assert result.exit_code != 0
        assert "Unknown group" in result.stdout

    def test_info_shows_dependencies(self):
        result = runner.invoke(app, ["info", "database"])
        assert result.exit_code == 0
        assert "sqlalchemy" in result.stdout
        assert "alembic" in result.stdout

    def test_info_shows_scaffold(self):
        result = runner.invoke(app, ["info", "docs"])
        assert result.exit_code == 0
        assert "docs_sphinx" in result.stdout


class TestDoctorCommand:
    """Test the doctor command."""

    def test_doctor_runs(self):
        result = runner.invoke(app, ["doctor"])
        assert "python" in result.stdout.lower() or "Python" in result.stdout

    def test_doctor_checks_required(self):
        result = runner.invoke(app, ["doctor"])
        assert "Required" in result.stdout
        assert "Optional" in result.stdout


class TestDefaultsCommand:
    """Test the defaults command."""

    def test_defaults_show(self):
        result = runner.invoke(app, ["defaults"])
        assert result.exit_code == 0
        assert "python_version" in result.stdout
        assert "archetype" in result.stdout

    def test_defaults_init(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["defaults", "--init"])
        assert result.exit_code == 0
        assert (tmp_path / ".pjkmrc.yaml").exists()

    def test_defaults_init_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".pjkmrc.yaml").write_text("test: true\n")
        result = runner.invoke(app, ["defaults", "--init"])
        assert result.exit_code != 0
        assert "already exists" in result.stdout

    def test_defaults_shows_github(self):
        result = runner.invoke(app, ["defaults"])
        assert result.exit_code == 0
        assert "GitHub" in result.stdout
        assert "org" in result.stdout
        assert "visibility" in result.stdout

    def test_defaults_init_includes_github(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["defaults", "--init"])
        assert result.exit_code == 0
        content = (tmp_path / ".pjkmrc.yaml").read_text()
        assert "github:" in content
        assert "org:" in content
        assert "visibility:" in content
        assert "create_repo:" in content


class TestGroupCommands:
    """Test the group subcommand."""

    def test_group_create(self, tmp_path):
        result = runner.invoke(
            app,
            [
                "group",
                "create",
                "quant-data",
                "--dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        yaml_path = tmp_path / "quant_data.yaml"
        assert yaml_path.exists()
        content = yaml_path.read_text()
        assert "id: quant_data" in content
        assert "dependencies:" in content

    def test_group_create_with_name(self, tmp_path):
        result = runner.invoke(
            app,
            [
                "group",
                "create",
                "ml-core",
                "--name",
                "Machine Learning Core",
                "--dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        content = (tmp_path / "ml_core.yaml").read_text()
        assert "Machine Learning Core" in content

    def test_group_create_already_exists(self, tmp_path):
        (tmp_path / "test.yaml").write_text("id: test\n")
        result = runner.invoke(
            app,
            [
                "group",
                "create",
                "test",
                "--dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code != 0
        assert "already exists" in result.stdout

    def test_group_validate_builtin(self):
        import pjkm.core.groups.registry as reg

        result = runner.invoke(
            app,
            [
                "group",
                "validate",
                str(reg.DEFINITIONS_DIR),
            ],
        )
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_group_validate_custom(self, tmp_path):
        yaml_content = """\
id: test_group
name: "Test Group"
description: "A test group"
archetypes: []
requires_groups: []
platform_filter: null
dependencies:
  test_group:
    - "requests>=2.0.0"
scaffolded_files: []
pyproject_tool_config: {}
"""
        (tmp_path / "test_group.yaml").write_text(yaml_content)
        result = runner.invoke(app, ["group", "validate", str(tmp_path)])
        assert result.exit_code == 0
        assert "test_group" in result.stdout

    def test_group_validate_invalid(self, tmp_path):
        (tmp_path / "bad.yaml").write_text("not: valid: yaml: [")
        result = runner.invoke(app, ["group", "validate", str(tmp_path)])
        assert result.exit_code != 0
        assert "Error" in result.stdout

    def test_group_import(self, tmp_path):
        # Create a minimal pyproject.toml with optional-dependencies
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""\
[project]
name = "test-project"

[project.optional-dependencies]
data = ["pandas>=2.0", "numpy>=1.26"]
viz = ["matplotlib>=3.0", "seaborn>=0.13"]
""")
        out_dir = tmp_path / "groups"
        result = runner.invoke(
            app,
            [
                "group",
                "import",
                str(pyproject),
                "--dir",
                str(out_dir),
            ],
        )
        assert result.exit_code == 0
        assert "2 group(s)" in result.stdout
        assert (out_dir / "data.yaml").exists()
        assert (out_dir / "viz.yaml").exists()

        # Verify content
        import yaml

        with open(out_dir / "data.yaml") as f:
            data = yaml.safe_load(f)
        assert data["id"] == "data"
        assert "pandas>=2.0" in data["dependencies"]["data"]

    def test_group_import_specific_sections(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""\
[project]
name = "test-project"

[project.optional-dependencies]
data = ["pandas>=2.0"]
viz = ["matplotlib>=3.0"]
dev = ["pytest>=8.0"]
""")
        out_dir = tmp_path / "groups"
        result = runner.invoke(
            app,
            [
                "group",
                "import",
                str(pyproject),
                "--section",
                "data",
                "--section",
                "viz",
                "--dir",
                str(out_dir),
            ],
        )
        assert result.exit_code == 0
        assert "2 group(s)" in result.stdout
        assert (out_dir / "data.yaml").exists()
        assert not (out_dir / "dev.yaml").exists()

    def test_group_list_shows_builtin(self):
        result = runner.invoke(app, ["group", "list"])
        assert result.exit_code == 0
        assert "logging" in result.stdout
        assert "testing" in result.stdout


class TestGroupSourceCommands:
    """Test the group source subcommands."""

    def test_source_list_empty(self, tmp_path, monkeypatch):
        # Point sources file to a temp location
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE",
            tmp_path / "sources.yaml",
        )
        result = runner.invoke(app, ["group", "source", "list"])
        assert result.exit_code == 0
        assert "No group sources" in result.stdout

    def test_source_add_no_sync(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE",
            tmp_path / "sources.yaml",
        )
        monkeypatch.setattr(
            "pjkm.core.groups.sources.CACHE_DIR",
            tmp_path / "cache",
        )
        result = runner.invoke(
            app,
            [
                "group",
                "source",
                "add",
                "https://github.com/example/groups.git",
                "--name",
                "test-src",
                "--no-sync",
            ],
        )
        assert result.exit_code == 0
        assert "test-src" in result.stdout
        # Verify persisted
        import yaml

        data = yaml.safe_load((tmp_path / "sources.yaml").read_text())
        assert len(data["sources"]) == 1
        assert data["sources"][0]["url"] == "https://github.com/example/groups.git"

    def test_source_remove(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE",
            tmp_path / "sources.yaml",
        )
        monkeypatch.setattr(
            "pjkm.core.groups.sources.CACHE_DIR",
            tmp_path / "cache",
        )
        # Add first
        runner.invoke(
            app,
            [
                "group",
                "source",
                "add",
                "https://github.com/example/groups.git",
                "--name",
                "removeme",
                "--no-sync",
            ],
        )
        # Remove
        result = runner.invoke(app, ["group", "source", "remove", "removeme"])
        assert result.exit_code == 0
        assert "Removed" in result.stdout

    def test_source_remove_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE",
            tmp_path / "sources.yaml",
        )
        result = runner.invoke(app, ["group", "source", "remove", "nope"])
        assert result.exit_code != 0
        assert "not found" in result.stdout
