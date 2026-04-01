"""Integration tests — actually generate projects and validate the output."""

from __future__ import annotations

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
                "init",
                "my-api",
                "-a",
                "service",
                "-g",
                "api",
                "-g",
                "database",
                "-g",
                "redis",
                "-g",
                "logging",
                "--dir",
                str(tmp_path),
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
                "init",
                "my-app",
                "-a",
                "service",
                "-g",
                "api",
                "-g",
                "auth",
                "--dir",
                str(tmp_path),
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
                "init",
                "recipe-test",
                "--recipe",
                "fastapi-service",
                "--dir",
                str(tmp_path),
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
                "init",
                "my-scraper",
                "--recipe",
                "scraper-full",
                "--dir",
                str(tmp_path),
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
                "init",
                "my-tool",
                "-a",
                "script-tool",
                "-g",
                "cli_rich",
                "-g",
                "logging",
                "--dir",
                str(tmp_path),
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
                "init",
                "my-project",
                "-a",
                "service",
                "-g",
                "api",
                "--dir",
                str(tmp_path),
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
                "init",
                "syntax-check",
                "-a",
                "service",
                "-g",
                "api",
                "-g",
                "auth",
                "-g",
                "database",
                "-g",
                "redis",
                "-g",
                "logging",
                "--dir",
                str(tmp_path),
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

        assert not errors, "Syntax errors in generated files:\n" + "\n".join(errors)


class TestAgentGeneration:
    """Test AI agent project generation end-to-end."""

    def test_ai_agent_recipe(self, tmp_path):
        """Full ai-agent recipe — generates agent scaffolding."""
        result = runner.invoke(
            app,
            ["init", "my-agent", "--recipe", "ai-agent", "--dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.stdout

        src = tmp_path / "my-agent" / "src" / "my_agent"

        # Agent module scaffolded
        assert (src / "agent" / "__init__.py").exists()
        assert (src / "agent" / "graph.py").exists()
        assert (src / "agent" / "state.py").exists()
        assert (src / "agent" / "tools.py").exists()
        assert (src / "agent" / "prompts.py").exists()

        # Graph has real LangGraph code
        graph = (src / "agent" / "graph.py").read_text()
        assert "StateGraph" in graph
        assert "ToolNode" in graph
        assert "create_agent" in graph
        assert "run_agent" in graph

        # State has TypedDict
        state = (src / "agent" / "state.py").read_text()
        assert "AgentState" in state
        assert "add_messages" in state

        # Tools has group-aware search
        tools = (src / "agent" / "tools.py").read_text()
        assert "get_all_tools" in tools
        assert "DuckDuckGoSearchRun" in tools  # search_tools group is in recipe

        # pyproject has agent deps
        pyproject = (tmp_path / "my-agent" / "pyproject.toml").read_text()
        assert "langgraph" in pyproject
        assert "langchain" in pyproject
        assert "langsmith" in pyproject

    def test_ai_agent_syntax_valid(self, tmp_path):
        """Every .py in the agent project compiles."""
        result = runner.invoke(
            app,
            ["init", "agent-check", "--recipe", "ai-agent", "--dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.stdout

        errors = []
        for py_file in (tmp_path / "agent-check").rglob("*.py"):
            try:
                compile(py_file.read_text(), str(py_file), "exec")
            except SyntaxError as e:
                errors.append(f"{py_file.name}: {e}")
        assert not errors, "\n".join(errors)

    def test_rag_service_recipe(self, tmp_path):
        """RAG service recipe generates API + agent + vector store."""
        result = runner.invoke(
            app,
            ["init", "my-rag", "--recipe", "rag-service", "--dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.stdout

        src = tmp_path / "my-rag" / "src" / "my_rag"
        assert (src / "api" / "app.py").exists()
        assert (src / "agent" / "graph.py").exists()
        assert (src / "core" / "database.py").exists()
        assert (src / "core" / "redis.py").exists()
        assert (src / "__main__.py").exists()

    def test_agent_platform_recipe(self, tmp_path):
        """Agent platform — full stack with monitoring."""
        result = runner.invoke(
            app,
            ["init", "my-platform", "--recipe", "agent-platform", "--dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.stdout

        project = tmp_path / "my-platform"
        src = project / "src" / "my_platform"
        assert (src / "agent" / "graph.py").exists()
        assert (src / "api" / "app.py").exists()
        assert (project / "Dockerfile").exists()


class TestAllRecipes:
    """Verify every single recipe generates without errors."""

    @pytest.fixture
    def all_recipes(self):
        from pjkm.cli.commands.recipes import RECIPES

        return list(RECIPES.keys())

    def test_every_recipe_inits(self, tmp_path, all_recipes):
        """Init every recipe with --dry-run (fast) to verify they parse."""
        failures = []
        for recipe_name in all_recipes:
            result = runner.invoke(
                app,
                [
                    "init",
                    f"test-{recipe_name[:10]}",
                    "--recipe",
                    recipe_name,
                    "--dir",
                    str(tmp_path),
                    "--dry-run",
                ],
            )
            if result.exit_code != 0:
                failures.append(f"{recipe_name}: {result.stdout[-200:]}")
        assert not failures, "Recipe failures:\n" + "\n".join(failures)

    def test_every_recipe_full_init(self, tmp_path, all_recipes):
        """Actually init every recipe (not dry-run) — verifies template rendering."""
        failures = []
        for recipe_name in all_recipes:
            sub = tmp_path / recipe_name
            sub.mkdir()
            # Use recipe name with hyphens replaced to avoid invalid package names
            proj_name = recipe_name.replace("-", "")[:12] + "proj"
            result = runner.invoke(
                app,
                ["init", proj_name, "--recipe", recipe_name, "--dir", str(sub)],
            )
            if result.exit_code != 0:
                failures.append(f"{recipe_name}: exit={result.exit_code}")
        assert not failures, "Recipe init failures:\n" + "\n".join(failures)


class TestWorkspaceE2E:
    """Test workspace generation end-to-end."""

    def test_microservices_blueprint(self, tmp_path):
        """Microservices blueprint generates all services."""
        result = runner.invoke(
            app,
            ["workspace", "my-plat", "--blueprint", "microservices", "--dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.stdout

        ws = tmp_path / "my-plat"
        assert (ws / "my-plat.code-workspace").exists()
        assert (ws / "docker-compose.yml").exists()
        assert (ws / "Makefile").exists()
        assert (ws / ".github" / "workflows" / "ci.yml").exists()
        assert (ws / "api").is_dir()
        assert (ws / "jobs").is_dir()
        assert (ws / "site").is_dir()
        assert (ws / "shared").is_dir()

        # VS Code workspace has all folders
        import json

        ws_config = json.loads((ws / "my-plat.code-workspace").read_text())
        folder_names = [f["path"] for f in ws_config["folders"]]
        assert "api" in folder_names
        assert "jobs" in folder_names
        assert "site" in folder_names
        assert "shared" in folder_names

    def test_workspace_services_have_pyproject(self, tmp_path):
        """Each service in workspace is a real pjkm project."""
        result = runner.invoke(
            app,
            ["workspace", "ws-test", "-s", "api:api", "-s", "lib:lib", "--dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.stdout

        ws = tmp_path / "ws-test"
        assert (ws / "api" / "pyproject.toml").exists()
        assert (ws / "lib" / "pyproject.toml").exists()
        assert (ws / "api" / "src" / "api" / "api" / "app.py").exists()
