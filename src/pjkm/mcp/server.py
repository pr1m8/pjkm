"""pjkm MCP server — expose project scaffolding as MCP tools and resources.

Install: pip install pjkm[mcp]
Run:     python -m pjkm.mcp
         pjkm-mcp
         fastmcp run pjkm.mcp.server:mcp
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP(name="pjkm")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool
def init_project(
    name: str,
    recipe: str | None = None,
    archetype: str | None = None,
    groups: list[str] | None = None,
    directory: str = ".",
) -> str:
    """Create a new Python project with pjkm.

    Use `recipe` for a pre-configured setup (e.g. "fastapi-service", "ai-agent"),
    or specify `archetype` + `groups` for custom composition.

    Args:
        name: Project name (e.g. "my-api")
        recipe: Recipe name (overrides archetype/groups). See list_recipes().
        archetype: Project archetype: single-package, service, poly-repo, script-tool
        groups: List of group IDs to include (e.g. ["api", "database", "redis"])
        directory: Parent directory to create the project in

    Returns:
        Summary of what was created.
    """
    from typer.testing import CliRunner
    from pjkm.cli.app import app

    runner = CliRunner()
    args = ["init", name, "--dir", directory]

    if recipe:
        args.extend(["--recipe", recipe])
    else:
        if archetype:
            args.extend(["-a", archetype])
        for g in groups or []:
            args.extend(["-g", g])

    result = runner.invoke(app, args)
    return result.stdout


@mcp.tool
def add_groups(
    groups: list[str],
    directory: str = ".",
) -> str:
    """Add package groups to an existing pjkm project.

    Merges dependencies into pyproject.toml, renders scaffolded files,
    and updates [tool.pjkm.groups].

    Args:
        groups: Group IDs to add (e.g. ["auth", "redis"])
        directory: Project directory containing pyproject.toml
    """
    from typer.testing import CliRunner
    from pjkm.cli.app import app

    runner = CliRunner()
    args = ["add", "--dir", directory]
    for g in groups:
        args.extend(["-g", g])

    result = runner.invoke(app, args)
    return result.stdout


@mcp.tool
def preview_project(
    recipe: str | None = None,
    archetype: str | None = None,
    groups: list[str] | None = None,
) -> str:
    """Preview what a project would look like without creating it.

    Shows the file tree, dependencies, and workflows that would be generated.

    Args:
        recipe: Recipe name (e.g. "fastapi-service")
        archetype: Archetype (needed if no recipe)
        groups: Groups to preview
    """
    from typer.testing import CliRunner
    from pjkm.cli.app import app

    runner = CliRunner()
    args = ["preview"]

    if recipe:
        args.extend(["--recipe", recipe])
    else:
        if archetype:
            args.append(archetype)
        for g in groups or []:
            args.extend(["-g", g])

    result = runner.invoke(app, args)
    return result.stdout


@mcp.tool
def list_recipes() -> str:
    """List all 22 available project recipes.

    Returns recipe names, archetypes, group counts, and descriptions.
    Use a recipe name with init_project() to create a project.
    """
    from pjkm.cli.commands.recipes import RECIPES

    lines = []
    for name, data in RECIPES.items():
        lines.append(
            f"- **{name}** ({data['archetype']}, {len(data['groups'])} groups): "
            f"{data['description']}"
        )
    return "\n".join(lines)


@mcp.tool
def list_groups(category: str | None = None) -> str:
    """List available package groups, optionally filtered by category.

    Args:
        category: Filter by category. Options: "Core Dev", "AI / ML", "Web & API",
                  "Data & Storage", "Infrastructure", "Frontend", "Docs & Meta", "Platform".
                  None returns all groups.
    """
    from pjkm.core.groups.registry import GroupRegistry

    registry = GroupRegistry()
    registry.load_all()

    groups = sorted(registry.list_all(), key=lambda g: (g.category, g.id))
    if category:
        groups = [g for g in groups if g.category.lower() == category.lower()]

    lines = []
    current_cat = ""
    for g in groups:
        if g.category != current_cat:
            current_cat = g.category
            lines.append(f"\n## {current_cat}")
        dep_count = sum(len(d) for d in g.dependencies.values())
        reqs = f" (requires: {', '.join(g.requires_groups)})" if g.requires_groups else ""
        lines.append(f"- **{g.id}**: {g.name} — {g.description} [{dep_count} deps]{reqs}")

    return "\n".join(lines)


@mcp.tool
def get_group_info(group_id: str) -> str:
    """Get detailed information about a specific package group.

    Args:
        group_id: Group ID (e.g. "database", "langchain", "api")

    Returns:
        Full details: description, category, dependencies, scaffolded files,
        required groups, and pyproject.toml tool config.
    """
    from pjkm.core.groups.registry import GroupRegistry

    registry = GroupRegistry()
    registry.load_all()

    group = registry.get(group_id)
    if group is None:
        return f"Unknown group: {group_id}. Use list_groups() to see available groups."

    lines = [
        f"# {group.name} ({group.id})",
        f"Category: {group.category}",
        f"Description: {group.description}",
        f"Archetypes: {', '.join(group.archetypes) or 'all'}",
    ]

    if group.requires_groups:
        lines.append(f"Requires: {', '.join(group.requires_groups)}")

    if group.dependencies:
        lines.append("\n## Dependencies")
        for section, deps in group.dependencies.items():
            lines.append(f"[{section}]")
            for dep in deps:
                lines.append(f"  - {dep}")

    if group.scaffolded_files:
        lines.append("\n## Scaffolded Files")
        for sf in group.scaffolded_files:
            lines.append(f"  - {sf.template_fragment}: {sf.description}")

    if group.pyproject_tool_config:
        lines.append("\n## Tool Config")
        for tool, conf in group.pyproject_tool_config.items():
            lines.append(f"  [tool.{tool}]: {json.dumps(conf, indent=2)}")

    return "\n".join(lines)


@mcp.tool
def search_registry(query: str = "") -> str:
    """Search the pjkm registry for community group packs.

    Args:
        query: Search term (name, tag, group name, or description).
               Empty string returns all packs.
    """
    from pjkm.core.registry.index import RegistryIndex

    registry = RegistryIndex()
    registry.load()

    results = registry.search(query)
    if not results:
        return f"No packs matching '{query}'."

    lines = [f"Found {len(results)} pack(s):"]
    for pack in results:
        lines.append(
            f"- **{pack.name}**: {pack.description}\n"
            f"  Groups: {', '.join(pack.groups)}\n"
            f"  Install: `pjkm install {pack.name}`"
        )
    return "\n".join(lines)


@mcp.tool
def adopt_project(directory: str = ".") -> str:
    """Scan an existing project and suggest pjkm groups to adopt.

    Detects frameworks and tools from pyproject.toml, requirements.txt,
    and project structure (Dockerfile, alembic/, etc.).

    Args:
        directory: Project directory to scan
    """
    from typer.testing import CliRunner
    from pjkm.cli.app import app

    runner = CliRunner()
    result = runner.invoke(app, ["adopt", "--dir", directory])
    return result.stdout


@mcp.tool
def project_status(directory: str = ".") -> str:
    """Show the pjkm status of a project.

    Displays applied groups, archetype, and dependency drift.

    Args:
        directory: Project directory
    """
    from typer.testing import CliRunner
    from pjkm.cli.app import app

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--dir", directory])
    return result.stdout


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("pjkm://recipes")
def get_recipes_resource() -> str:
    """All available pjkm recipes with full details."""
    return list_recipes()


@mcp.resource("pjkm://groups")
def get_groups_resource() -> str:
    """All 105 groups organized by category."""
    return list_groups()


@mcp.resource("pjkm://groups/{group_id}")
def get_group_resource(group_id: str) -> str:
    """Detailed info for a specific group."""
    return get_group_info(group_id)


@mcp.resource("pjkm://registry")
def get_registry_resource() -> str:
    """Community group pack registry."""
    return search_registry()


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@mcp.prompt()
def project_advisor(description: str) -> str:
    """Recommend the best pjkm recipe and groups for a project.

    Given a description of what the user wants to build, analyze the requirements
    and suggest the optimal recipe, archetype, and groups.
    """
    from pjkm.cli.commands.recipes import RECIPES

    recipe_list = "\n".join(
        f"- {name} ({r['archetype']}, {len(r['groups'])} groups): {r['description']}"
        for name, r in RECIPES.items()
    )

    return (
        f"The user wants to build: {description}\n\n"
        f"Available recipes:\n{recipe_list}\n\n"
        f"Available group categories: Core Dev (23), AI/ML (29), Web & API (18), "
        f"Infrastructure (18), Data & Storage (9), Frontend (2), Docs & Meta (4), Platform (2)\n\n"
        f"Based on the description, recommend:\n"
        f"1. The best matching recipe (or 'custom' if none fit)\n"
        f"2. Any additional groups to add beyond the recipe\n"
        f"3. The archetype if going custom\n"
        f"4. Whether a workspace with multiple services would be better\n\n"
        f"Use list_groups() and get_group_info() to explore specifics. "
        f"Use preview_project() to show the user what they'd get before creating."
    )


@mcp.prompt()
def architecture_advisor(requirements: str) -> str:
    """Design a multi-service architecture using pjkm workspace blueprints.

    Given system requirements, suggest a workspace layout with services,
    shared libraries, and infrastructure.
    """
    return (
        f"System requirements: {requirements}\n\n"
        f"Available workspace blueprints:\n"
        f"- microservices: api + worker + web + shared lib\n"
        f"- data-platform: api + ingestion + warehouse + orchestration + quality + dashboards + events + shared\n"
        f"- scraping-platform: api + scraper + worker + web + storage + shared\n"
        f"- ml-platform: api + ml-service + worker + data + dashboards + shared + db-models\n"
        f"- fullstack: api + worker + web + integrations + shared + db-pkg + observability\n\n"
        f"Available service templates: api, worker, web, scraper, ml, integration, "
        f"ingestion, warehouse, orchestration, quality, dashboards, analytics-events, "
        f"lib, db-models, storage, observability, cli, tui\n\n"
        f"Based on the requirements:\n"
        f"1. Recommend a blueprint or custom service combination\n"
        f"2. Explain the role of each service\n"
        f"3. Describe the shared infrastructure (Postgres, Redis, etc.)\n"
        f"4. Suggest which groups each service should have beyond defaults"
    )


@mcp.prompt()
def agent_scaffold(agent_type: str = "general") -> str:
    """Guide for scaffolding an AI agent project.

    Provides step-by-step instructions for creating an agent with
    the right groups, tools, and configuration.
    """
    return (
        f"Agent type requested: {agent_type}\n\n"
        f"Available AI/ML groups (29):\n"
        f"- agents: LangGraph orchestration with tools + memory\n"
        f"- langchain: LangChain core + providers\n"
        f"- langgraph: LangGraph SDK + prebuilt + checkpointer\n"
        f"- llm_providers: OpenAI, Anthropic, Google, Ollama, LiteLLM\n"
        f"- claude_sdk / openai_sdk: Direct SDKs\n"
        f"- mcp_tools: MCP protocol + adapters\n"
        f"- agent_protocols: MCP + A2A/ACP interop\n"
        f"- rag: Retrieval-augmented generation\n"
        f"- vector_stores: Qdrant, Chroma, pgvector, FAISS\n"
        f"- embeddings: sentence-transformers, tiktoken, Cohere\n"
        f"- search_tools: Tavily, DuckDuckGo, SerpAPI\n"
        f"- eval: LangSmith + ragas + deepeval\n"
        f"- guardrails: output validation + safety\n"
        f"- doc_parsing: PDF, DOCX, HTML parsing\n\n"
        f"Relevant recipes:\n"
        f"- ai-agent: single-package with LangGraph agent scaffolding\n"
        f"- rag-service: API service with vector store + embeddings\n"
        f"- agent-platform: multi-agent with eval + monitoring\n\n"
        f"Steps:\n"
        f"1. Use list_groups('AI / ML') to see all available groups\n"
        f"2. Use preview_project(recipe='ai-agent') to see the output\n"
        f"3. Use init_project() to create the project\n"
        f"4. The agent scaffolding generates: graph.py (LangGraph), state.py (TypedDict), "
        f"tools.py (@tool functions), prompts.py (ChatPromptTemplate)\n"
        f"5. Set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY in .env"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the pjkm MCP server."""
    mcp.run()
