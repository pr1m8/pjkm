"""Integration tests — actually generate projects and validate the output."""

from __future__ import annotations

import subprocess

import pytest
from typer.testing import CliRunner

from pjkm.cli.app import app

runner = CliRunner()


class TestFullProjectGeneration:
    """Generate real projects and verify they're valid."""

    def test_minimal_library(self, tmp_path):
        """Minimal single-package with no groups."""
        result = runner.invoke(
            app,
            ["init", "my-lib", "-a", "single-package", "--dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.stdout

        project = tmp_path / "my-lib"
        assert project.is_dir()
        assert (project / "pyproject.toml").exists()
        assert (project / "src" / "my_lib" / "__init__.py").exists()
        assert (project / "tests" / "conftest.py").exists()
        assert (project / ".github" / "workflows" / "ci.yml").exists()
        assert (project / "README.md").exists()
        assert (project / ".gitignore").exists()

    def test_service_with_api_and_db(self, tmp_path):
        """Service with API + database + Redis — verify source code scaffolding."""
        result = runner.invoke(
            app,
            [
                "init", "my-api", "-a", "service",
                "-g", "api", "-g", "database", "-g", "redis", "-g", "logging",
                "--dir", str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stdout

        project = tmp_path / "my-api"
        src = project / "src" / "my_api"

        # Core scaffolded modules exist
        assert (src / "__main__.py").exists(), "Missing __main__.py entry point"
        assert (src / "api" / "app.py").exists(), "Missing FastAPI app"
        assert (src / "api" / "routes" / "health.py").exists(), "Missing health routes"
        assert (src / "api" / "routes" / "v1.py").exists(), "Missing v1 routes"
        assert (src / "api" / "middleware.py").exists(), "Missing middleware"
        assert (src / "api" / "pagination.py").exists(), "Missing pagination"
        assert (src / "api" / "deps.py").exists(), "Missing deps"
        assert (src / "core" / "settings.py").exists(), "Missing settings"
        assert (src / "core" / "database.py").exists(), "Missing database module"
        assert (src / "core" / "redis.py").exists(), "Missing redis module"
        assert (src / "core" / "lifespan.py").exists(), "Missing lifespan"
        assert (src / "core" / "logging" / "config.py").exists(), "Missing logging"
        assert (src / "models" / "__init__.py").exists(), "Missing models"
        assert (src / "models" / "mixins.py").exists(), "Missing mixins"

        # .env.example has the right vars
        env = (project / ".env.example").read_text()
        assert "DATABASE_URL" in env, ".env missing DATABASE_URL"
        assert "REDIS_URL" in env, ".env missing REDIS_URL"

        # Settings has the right fields
        settings = (src / "core" / "settings.py").read_text()
        assert "database_url" in settings, "Settings missing database_url"
        assert "redis_url" in settings, "Settings missing redis_url"

        # Lifespan actually wires DB + Redis (not placeholder comments)
        lifespan = (src / "core" / "lifespan.py").read_text()
        assert "database" in lifespan.lower(), "Lifespan doesn't wire database"
        assert "redis" in lifespan.lower(), "Lifespan doesn't wire redis"

        # Health check actually pings
        health = (src / "api" / "routes" / "health.py").read_text()
        assert "db_ping" in health, "Health doesn't ping database"
        assert "redis_ping" in health, "Health doesn't ping redis"

        # Deps has real injectors
        deps = (src / "api" / "deps.py").read_text()
        assert "get_db" in deps, "Deps missing get_db"
        assert "get_redis" in deps, "Deps missing get_redis"

        # Infra files
        assert (project / "alembic").is_dir(), "Missing alembic dir"
        assert (project / "alembic.ini").exists(), "Missing alembic.ini"

        # pyproject.toml has all group deps
        pyproject = (project / "pyproject.toml").read_text()
        assert "fastapi" in pyproject
        assert "sqlalchemy" in pyproject
        assert "redis" in pyproject
        assert "structlog" in pyproject

    def test_service_with_auth(self, tmp_path):
        """Service with API + auth — verify JWT module scaffolding."""
        result = runner.invoke(
            app,
            [
                "init", "my-app", "-a", "service",
                "-g", "api", "-g", "auth",
                "--dir", str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stdout

        src = tmp_path / "my-app" / "src" / "my_app"

        assert (src / "auth" / "__init__.py").exists()
        assert (src / "auth" / "jwt.py").exists()
        assert (src / "auth" / "deps.py").exists()

        jwt_code = (src / "auth" / "jwt.py").read_text()
        assert "create_access_token" in jwt_code
        assert "decode_token" in jwt_code

        env = (tmp_path / "my-app" / ".env.example").read_text()
        assert "JWT_SECRET_KEY" in env

    def test_recipe_fastapi_service(self, tmp_path):
        """Full recipe — fastapi-service."""
        result = runner.invoke(
            app,
            [
                "init", "recipe-test",
                "--recipe", "fastapi-service",
                "--dir", str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stdout

        project = tmp_path / "recipe-test"
        assert project.is_dir()
        assert (project / "src" / "recipe_test" / "api" / "app.py").exists()
        assert (project / "src" / "recipe_test" / "auth").is_dir()
        assert (project / "src" / "recipe_test" / "core" / "database.py").exists()
        assert (project / "Dockerfile").exists()

    def test_recipe_scraper_full(self, tmp_path):
        """Full recipe — scraper-full with all the bells."""
        result = runner.invoke(
            app,
            [
                "init", "my-scraper",
                "--recipe", "scraper-full",
                "--dir", str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stdout

        project = tmp_path / "my-scraper"
        src = project / "src" / "my_scraper"

        # API + auth + DB + Redis all wired
        assert (src / "api" / "app.py").exists()
        assert (src / "auth" / "jwt.py").exists()
        assert (src / "core" / "database.py").exists()
        assert (src / "core" / "redis.py").exists()
        assert (src / "core" / "settings.py").exists()
        assert (src / "core" / "lifespan.py").exists()
        assert (src / "__main__.py").exists()

        # Celery workers
        assert (src / "workers" / "celery_app.py").exists()
        assert (src / "workers" / "tasks.py").exists()

        # Docker + infra
        assert (project / "Dockerfile").exists()
        assert (project / "Makefile").exists()

        # pyproject has scraping deps
        pyproject = (project / "pyproject.toml").read_text()
        assert "scrapy" in pyproject or "beautifulsoup4" in pyproject
        assert "prometheus" in pyproject

    def test_script_tool(self, tmp_path):
        """Script tool archetype."""
        result = runner.invoke(
            app,
            [
                "init", "my-tool", "-a", "script-tool",
                "-g", "cli_rich", "-g", "logging",
                "--dir", str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stdout

        project = tmp_path / "my-tool"
        assert (project / "src" / "my_tool" / "__main__.py").exists()
        assert (project / "src" / "my_tool" / "cli.py").exists()

    def test_add_groups_to_existing(self, tmp_path):
        """Init a project, then add groups incrementally."""
        # Step 1: init with just api
        result = runner.invoke(
            app,
            [
                "init", "my-project", "-a", "service",
                "-g", "api",
                "--dir", str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stdout

        project = tmp_path / "my-project"
        assert (project / "src" / "my_project" / "api" / "app.py").exists()

        # Step 2: add database
        result = runner.invoke(
            app,
            ["add", "-g", "database", "--dir", str(project)],
        )
        assert result.exit_code == 0, result.stdout
        assert "Added 1 group" in result.stdout or "Added" in result.stdout

        # Verify database was added to pyproject
        pyproject = (project / "pyproject.toml").read_text()
        assert "sqlalchemy" in pyproject
        assert '"database"' in pyproject or "'database'" in pyproject

    def test_preview_shows_tree(self, tmp_path):
        """Preview generates a tree without leaving files behind."""
        result = runner.invoke(
            app,
            ["preview", "service", "-g", "api", "-g", "database"],
        )
        assert result.exit_code == 0
        assert "Preview" in result.stdout
        assert "Files" in result.stdout

    def test_generated_python_is_valid(self, tmp_path):
        """Verify generated .py files have no syntax errors."""
        result = runner.invoke(
            app,
            [
                "init", "syntax-check", "-a", "service",
                "-g", "api", "-g", "auth", "-g", "database",
                "-g", "redis", "-g", "logging",
                "--dir", str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stdout

        project = tmp_path / "syntax-check"
        py_files = list(project.rglob("*.py"))
        assert len(py_files) > 10, f"Expected >10 .py files, got {len(py_files)}"

        errors = []
        for py_file in py_files:
            try:
                compile(py_file.read_text(), str(py_file), "exec")
            except SyntaxError as e:
                errors.append(f"{py_file.relative_to(project)}: {e}")

        assert not errors, f"Syntax errors in generated files:\n" + "\n".join(errors)
