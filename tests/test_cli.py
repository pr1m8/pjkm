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
        assert "Scaffold" in result.stdout
        # Groups are categorized (Core Dev, AI / ML, etc.)
        assert "Core Dev" in result.stdout

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

    def test_init_with_recipe(self, tmp_path):
        result = runner.invoke(
            app,
            [
                "init",
                "test-proj",
                "--recipe",
                "python-lib",
                "--dir",
                str(tmp_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "python-lib" in result.stdout
        assert "single_package" in result.stdout

    def test_init_with_unknown_recipe(self):
        result = runner.invoke(
            app,
            ["init", "test-proj", "--recipe", "nonexistent", "--dry-run"],
        )
        assert result.exit_code != 0
        assert "Unknown recipe" in result.stdout


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


class TestRecommendCommand:
    """Test the recommend command."""

    def test_recommend_no_preset(self):
        result = runner.invoke(app, ["recommend", "service"])
        assert result.exit_code == 0
        assert "Presets for archetype" in result.stdout
        assert "minimal" in result.stdout
        assert "standard" in result.stdout

    def test_recommend_with_preset(self):
        result = runner.invoke(
            app, ["recommend", "service", "--preset", "standard"]
        )
        assert result.exit_code == 0
        assert "pjkm init" in result.stdout
        assert "-g api" in result.stdout

    def test_recommend_preset_minimal(self):
        result = runner.invoke(
            app, ["recommend", "single-package", "--preset", "minimal"]
        )
        assert result.exit_code == 0
        assert "dev" in result.stdout
        assert "linting" in result.stdout

    def test_recommend_preset_ai(self):
        result = runner.invoke(
            app, ["recommend", "service", "--preset", "ai"]
        )
        assert result.exit_code == 0
        assert "langchain" in result.stdout

    def test_recommend_unknown_preset(self):
        result = runner.invoke(
            app, ["recommend", "service", "--preset", "nonexistent"]
        )
        assert result.exit_code != 0
        assert "Unknown preset" in result.stdout

    def test_recommend_all_presets(self):
        for preset in ["minimal", "standard", "full", "ai", "data", "web"]:
            result = runner.invoke(
                app, ["recommend", "service", "--preset", preset]
            )
            assert result.exit_code == 0, f"Preset {preset} failed"


class TestRecipeCommand:
    """Test the recipe command."""

    def test_recipe_list(self):
        result = runner.invoke(app, ["recipe"])
        assert result.exit_code == 0
        assert "python-lib" in result.stdout
        assert "fastapi-service" in result.stdout
        assert "ai-agent" in result.stdout

    def test_recipe_show(self):
        result = runner.invoke(app, ["recipe", "python-lib", "--show"])
        assert result.exit_code == 0
        assert "single-package" in result.stdout
        assert "dev" in result.stdout
        assert "towncrier" in result.stdout

    def test_recipe_generate(self):
        result = runner.invoke(app, ["recipe", "fastapi-service"])
        assert result.exit_code == 0
        assert "pjkm init" in result.stdout
        assert "-a service" in result.stdout
        assert "-g api" in result.stdout

    def test_recipe_unknown(self):
        result = runner.invoke(app, ["recipe", "nonexistent"])
        assert result.exit_code != 0
        assert "Unknown recipe" in result.stdout

    def test_recipe_all_18(self):
        result = runner.invoke(app, ["recipe"])
        assert result.exit_code == 0
        for name in [
            "python-lib", "fastapi-service", "ai-agent", "ml-pipeline",
            "data-analysis", "cli-tool", "fullstack-web", "monorepo",
            "scraper", "fintech", "api-microservice", "discord-bot",
            "etl-pipeline", "saas-backend", "document-processor",
            "media-pipeline", "realtime-api", "file-service",
        ]:
            assert name in result.stdout

    def test_recipe_new_saas(self):
        result = runner.invoke(app, ["recipe", "saas-backend"])
        assert result.exit_code == 0
        assert "pjkm init" in result.stdout
        assert "-g auth" in result.stdout
        assert "-g payments" in result.stdout

    def test_recipe_new_microservice(self):
        result = runner.invoke(app, ["recipe", "api-microservice", "--show"])
        assert result.exit_code == 0
        assert "caching" in result.stdout
        assert "async_tools" in result.stdout


class TestPreviewCommand:
    """Test the preview command."""

    def test_preview_basic(self):
        result = runner.invoke(
            app, ["preview", "single-package"]
        )
        assert result.exit_code == 0
        assert "Preview" in result.stdout

    def test_preview_with_groups(self):
        result = runner.invoke(
            app, ["preview", "service", "-g", "api", "-g", "docker"]
        )
        assert result.exit_code == 0
        assert "service" in result.stdout

    def test_preview_with_recipe(self):
        result = runner.invoke(
            app, ["preview", "--recipe", "fastapi-service"]
        )
        assert result.exit_code == 0
        assert "fastapi-service" in result.stdout

    def test_preview_invalid_archetype(self):
        result = runner.invoke(app, ["preview", "invalid"])
        assert result.exit_code != 0

    def test_preview_no_args(self):
        result = runner.invoke(app, ["preview"])
        assert result.exit_code != 0

    def test_preview_invalid_recipe(self):
        result = runner.invoke(
            app, ["preview", "--recipe", "nonexistent"]
        )
        assert result.exit_code != 0


class TestRegistryCommands:
    """Test the registry search/install commands."""

    def test_search_all(self):
        result = runner.invoke(app, ["search"])
        assert result.exit_code == 0
        assert "pjkm-django" in result.stdout

    def test_search_query(self):
        result = runner.invoke(app, ["search", "django"])
        assert result.exit_code == 0
        assert "pjkm-django" in result.stdout

    def test_search_by_tag(self):
        result = runner.invoke(app, ["search", "ml"])
        assert result.exit_code == 0
        assert "pjkm-ml-ops" in result.stdout

    def test_search_no_match(self):
        result = runner.invoke(app, ["search", "zzz_nonexistent_zzz"])
        assert result.exit_code == 0
        assert "No packs" in result.stdout

    def test_install_unknown(self):
        result = runner.invoke(app, ["install", "nonexistent-pack"])
        assert result.exit_code != 0

    def test_installed_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE",
            tmp_path / "sources.yaml",
        )
        result = runner.invoke(app, ["installed"])
        assert result.exit_code == 0
        assert "No group packs" in result.stdout

    def test_uninstall_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE",
            tmp_path / "sources.yaml",
        )
        result = runner.invoke(app, ["uninstall", "nonexistent"])
        assert result.exit_code != 0


class TestUpdateCommand:
    """Test the update command."""

    def test_update_no_pyproject(self, tmp_path):
        result = runner.invoke(app, ["update", "--dir", str(tmp_path)])
        assert result.exit_code != 0
        assert "pyproject.toml" in result.stdout

    def test_update_dry_run(self, tmp_path):
        # Create a minimal pyproject.toml
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\n\n[tool.pjkm]\narchetype = "single_package"\ngroups = []\n'
        )
        result = runner.invoke(app, ["update", "--dir", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.stdout or "dry run" in result.stdout.lower()


class TestUpgradeCommand:
    """Test the upgrade command."""

    def test_upgrade_no_pyproject(self, tmp_path):
        result = runner.invoke(app, ["upgrade", "--dir", str(tmp_path)])
        assert result.exit_code != 0
        assert "pyproject.toml" in result.stdout

    def test_upgrade_no_groups(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\n'
        )
        result = runner.invoke(app, ["upgrade", "--dir", str(tmp_path)])
        assert result.exit_code != 0
        assert "No groups" in result.stdout

    def test_upgrade_dry_run(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\n\n[project.optional-dependencies]\nlogging = ["structlog>=24.0.0"]\n\n[tool.pjkm]\ngroups = ["logging"]\n'
        )
        result = runner.invoke(
            app, ["upgrade", "--dir", str(tmp_path), "--dry-run"]
        )
        assert result.exit_code == 0


class TestLinkCommand:
    """Test the link command."""

    def test_link_no_pyproject(self, tmp_path):
        result = runner.invoke(
            app, ["link", "ruff", "--dir", str(tmp_path)]
        )
        assert result.exit_code != 0

    def test_link_no_groups(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\n'
        )
        result = runner.invoke(
            app, ["link", "ruff", "--dir", str(tmp_path)]
        )
        assert result.exit_code != 0

    def test_link_unknown_tool(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\n\n[tool.pjkm]\ngroups = ["logging"]\n'
        )
        result = runner.invoke(
            app, ["link", "nonexistent_tool", "--dir", str(tmp_path)]
        )
        assert result.exit_code != 0
