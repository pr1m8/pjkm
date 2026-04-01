"""MCP server tests — verify tools work without FastMCP runtime."""

from __future__ import annotations

import pytest


class TestMCPToolFunctions:
    """Test the underlying tool functions directly (no MCP transport)."""

    def test_list_recipes(self):
        from pjkm.mcp.server import list_recipes

        result = list_recipes()
        assert "fastapi-service" in result
        assert "ai-agent" in result
        assert len(result.splitlines()) >= 20

    def test_list_groups_all(self):
        from pjkm.mcp.server import list_groups

        result = list_groups()
        assert "Core Dev" in result
        assert "AI / ML" in result
        assert "api" in result

    def test_list_groups_by_category(self):
        from pjkm.mcp.server import list_groups

        result = list_groups(category="AI / ML")
        assert "langchain" in result
        assert "Core Dev" not in result

    def test_get_group_info(self):
        from pjkm.mcp.server import get_group_info

        result = get_group_info("database")
        assert "SQLAlchemy" in result or "sqlalchemy" in result
        assert "alembic" in result

    def test_get_group_info_unknown(self):
        from pjkm.mcp.server import get_group_info

        result = get_group_info("nonexistent_group_xyz")
        assert "Unknown group" in result

    def test_search_registry(self):
        from pjkm.mcp.server import search_registry

        result = search_registry()
        assert "pjkm-django" in result

    def test_search_registry_filtered(self):
        from pjkm.mcp.server import search_registry

        result = search_registry("ml")
        assert "pjkm-ml-ops" in result

    def test_init_project_dry_run(self, tmp_path):
        from pjkm.mcp.server import init_project

        result = init_project(
            name="test-mcp",
            recipe="python-lib",
            directory=str(tmp_path),
        )
        # Should succeed (actual init, not dry run — but via CLI runner)
        assert "python-lib" in result or "test-mcp" in result

    def test_preview_project(self):
        from pjkm.mcp.server import preview_project

        result = preview_project(recipe="cli-tool")
        assert "Preview" in result or "script" in result

    def test_mcp_server_object_exists(self):
        from pjkm.mcp.server import mcp

        assert mcp.name == "pjkm"

    def test_adopt_project_empty(self, tmp_path):
        from pjkm.mcp.server import adopt_project

        result = adopt_project(directory=str(tmp_path))
        assert "No recognizable" in result

    def test_project_status_no_project(self, tmp_path):
        from pjkm.mcp.server import project_status

        result = project_status(directory=str(tmp_path))
        assert "pyproject.toml" in result

    def test_add_groups_no_project(self, tmp_path):
        from pjkm.mcp.server import add_groups

        result = add_groups(groups=["api"], directory=str(tmp_path))
        assert "pyproject.toml" in result

    def test_preview_custom(self):
        from pjkm.mcp.server import preview_project

        result = preview_project(archetype="single-package", groups=["dev"])
        assert "Preview" in result or "single" in result

    def test_resources(self):
        from pjkm.mcp.server import (
            get_recipes_resource, get_groups_resource,
            get_registry_resource, get_group_resource,
        )

        assert "fastapi-service" in get_recipes_resource()
        assert "Core Dev" in get_groups_resource()
        assert "pjkm-django" in get_registry_resource()
        assert "fastapi" in get_group_resource("api").lower()

    def test_prompts(self):
        from pjkm.mcp.server import (
            project_advisor, architecture_advisor, agent_scaffold,
        )

        assert "recipe" in project_advisor("a REST API").lower()
        assert "blueprint" in architecture_advisor("microservices").lower()
        assert "LangGraph" in agent_scaffold("rag")
