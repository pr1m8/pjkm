"""Discovery commands — recommend, recipe."""

from __future__ import annotations

import typer

# --- Preset definitions for recommend ---

PRESETS: dict[str, dict[str, list[str]]] = {
    "minimal": {
        "single_package": ["dev", "linting", "testing"],
        "service": ["dev", "linting", "testing", "docker"],
        "poly_repo": ["dev", "linting", "testing", "docker", "makefile"],
        "script_tool": ["dev", "linting", "testing"],
    },
    "standard": {
        "single_package": [
            "dev", "linting", "testing", "typecheck", "coverage",
            "security", "docs", "github_templates",
        ],
        "service": [
            "dev", "linting", "testing", "typecheck", "coverage",
            "security", "docs", "api", "database", "docker",
            "logging", "github_templates", "makefile",
        ],
        "poly_repo": [
            "dev", "linting", "testing", "typecheck", "coverage",
            "security", "docs", "docker", "logging", "makefile",
            "github_templates", "submodules",
        ],
        "script_tool": [
            "dev", "linting", "testing", "typecheck", "coverage",
            "scripts", "docs",
        ],
    },
    "full": {
        "single_package": [
            "dev", "dev_extended", "linting", "testing", "testing_extended",
            "typecheck", "coverage", "security", "code_quality", "docs",
            "github_templates", "towncrier", "reporting",
        ],
        "service": [
            "dev", "dev_extended", "linting", "testing", "testing_extended",
            "typecheck", "coverage", "security", "code_quality", "docs",
            "api", "auth", "database", "redis", "docker", "k8s",
            "logging", "otel", "monitoring", "makefile",
            "github_templates", "towncrier", "reporting",
        ],
        "poly_repo": [
            "dev", "dev_extended", "linting", "testing", "testing_extended",
            "typecheck", "coverage", "security", "code_quality", "docs",
            "docker", "k8s", "logging", "otel", "makefile",
            "github_templates", "submodules", "towncrier", "reporting",
        ],
        "script_tool": [
            "dev", "dev_extended", "linting", "testing", "testing_extended",
            "typecheck", "coverage", "security", "scripts", "docs",
            "github_templates", "towncrier",
        ],
    },
    "ai": {
        "single_package": [
            "dev", "linting", "testing", "langchain", "langchain_providers",
            "langgraph", "mcp_tools", "hf", "ml", "vector_stores",
            "search_tools", "doc_parsing", "jupyter", "notebook",
        ],
        "service": [
            "dev", "linting", "testing", "api", "database", "redis",
            "docker", "logging", "otel", "langchain", "langchain_providers",
            "langgraph", "mcp_tools", "hf", "ml", "vector_stores",
            "search_tools", "doc_parsing", "makefile",
        ],
        "poly_repo": [
            "dev", "linting", "testing", "docker", "logging",
            "langchain", "langchain_providers", "langgraph", "mcp_tools",
            "hf", "ml", "vector_stores", "search_tools", "makefile",
        ],
        "script_tool": [
            "dev", "linting", "testing", "langchain", "ml",
            "search_tools", "scripts",
        ],
    },
    "data": {
        "single_package": [
            "dev", "linting", "testing", "ml", "dataviz", "jupyter",
            "notebook", "database", "doc_parsing",
        ],
        "service": [
            "dev", "linting", "testing", "api", "database", "redis",
            "docker", "logging", "ml", "dataviz", "jupyter", "notebook",
            "doc_parsing", "celery", "makefile",
        ],
        "poly_repo": [
            "dev", "linting", "testing", "docker", "database", "redis",
            "ml", "dataviz", "jupyter", "notebook", "celery", "makefile",
        ],
        "script_tool": [
            "dev", "linting", "testing", "ml", "dataviz", "scripts",
        ],
    },
    "web": {
        "service": [
            "dev", "linting", "testing", "api", "auth", "gateway",
            "database", "redis", "docker", "nginx", "logging", "otel",
            "monitoring", "frontend", "makefile", "github_templates",
        ],
        "poly_repo": [
            "dev", "linting", "testing", "api", "database", "redis",
            "docker", "nginx", "logging", "frontend", "makefile",
            "github_templates", "submodules",
        ],
        "single_package": [
            "dev", "linting", "testing", "api", "auth", "database",
        ],
        "script_tool": [
            "dev", "linting", "testing", "scripts",
        ],
    },
}

# --- Recipe definitions ---

RECIPES: dict[str, dict] = {
    "python-lib": {
        "description": "Publish-ready Python library with full CI/CD",
        "archetype": "single-package",
        "groups": [
            "dev", "dev_extended", "linting", "testing", "typecheck",
            "coverage", "security", "code_quality", "docs", "github_templates",
            "towncrier",
        ],
    },
    "fastapi-service": {
        "description": "Production FastAPI service with database, auth, and observability",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "coverage", "security",
            "api", "auth", "database", "redis", "docker", "logging", "otel",
            "monitoring", "makefile", "github_templates", "error_tracking",
        ],
    },
    "ai-agent": {
        "description": "LangChain/LangGraph AI agent with vector store and tools",
        "archetype": "single-package",
        "groups": [
            "dev", "linting", "testing", "typecheck", "langchain",
            "langchain_providers", "langgraph", "mcp_tools", "vector_stores",
            "search_tools", "doc_parsing", "redis", "logging",
        ],
    },
    "ml-pipeline": {
        "description": "ML training pipeline with experiment tracking and data tools",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "ml", "hf", "torch",
            "dataviz", "jupyter", "notebook", "docker", "logging", "makefile",
            "database", "celery",
        ],
    },
    "data-analysis": {
        "description": "Data analysis workspace with notebooks and visualization",
        "archetype": "single-package",
        "groups": [
            "dev", "linting", "testing", "ml", "dataviz", "jupyter",
            "notebook", "database", "doc_parsing", "reporting",
        ],
    },
    "cli-tool": {
        "description": "Polished CLI tool with rich output and testing",
        "archetype": "script-tool",
        "groups": [
            "dev", "linting", "testing", "typecheck", "coverage",
            "security", "scripts", "docs", "github_templates", "towncrier",
        ],
    },
    "fullstack-web": {
        "description": "Full-stack web app with API, frontend, auth, and infra",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "coverage", "security",
            "api", "auth", "gateway", "database", "redis", "docker", "nginx",
            "logging", "otel", "monitoring", "frontend", "frontend_vite",
            "makefile", "github_templates",
        ],
    },
    "monorepo": {
        "description": "Multi-package monorepo with shared infra and CI",
        "archetype": "poly-repo",
        "groups": [
            "dev", "dev_extended", "linting", "testing", "typecheck",
            "coverage", "security", "code_quality", "docs", "docker", "k8s",
            "logging", "otel", "makefile", "github_templates", "submodules",
            "towncrier", "reporting",
        ],
    },
    "scraper": {
        "description": "Web scraping pipeline with crawling, parsing, and storage",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "web_scraping",
            "crawling", "doc_parsing", "database", "redis", "docker",
            "logging", "celery", "makefile",
        ],
    },
    "fintech": {
        "description": "Financial data service with payments, compliance, and monitoring",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "coverage", "security",
            "api", "auth", "database", "redis", "docker", "logging", "otel",
            "monitoring", "finance", "payments", "error_tracking", "makefile",
            "github_templates",
        ],
    },
    "api-microservice": {
        "description": "Lightweight microservice with async API, caching, and health checks",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "api", "database",
            "redis", "caching", "docker", "logging", "otel", "async_tools",
            "http_client", "config_mgmt", "makefile", "ci_cd",
        ],
    },
    "discord-bot": {
        "description": "Discord/Slack bot with async handlers and task scheduling",
        "archetype": "single-package",
        "groups": [
            "dev", "linting", "testing", "typecheck", "async_tools",
            "http_client", "config_mgmt", "messaging", "redis", "logging",
            "scheduling", "docker",
        ],
    },
    "etl-pipeline": {
        "description": "ETL/data pipeline with scheduling, queues, and database",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "database", "redis",
            "celery", "scheduling", "docker", "logging", "otel",
            "doc_parsing", "elasticsearch", "makefile",
        ],
    },
    "saas-backend": {
        "description": "Multi-tenant SaaS backend with auth, billing, email, and webhooks",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "coverage", "security",
            "api", "auth", "database", "redis", "caching", "docker", "logging",
            "otel", "monitoring", "payments", "email", "websocket",
            "scheduling", "error_tracking", "makefile", "github_templates",
            "ci_cd",
        ],
    },
    "document-processor": {
        "description": "Document ingestion, parsing, OCR, and PDF generation pipeline",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "doc_parsing",
            "pdf", "image", "database", "redis", "celery", "docker",
            "logging", "makefile",
        ],
    },
    "media-pipeline": {
        "description": "Video/audio/image processing pipeline with ffmpeg and ML",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "video", "audio",
            "image", "ocr", "file_utils", "s3", "database", "redis",
            "celery", "docker", "logging", "makefile",
        ],
    },
    "realtime-api": {
        "description": "Real-time API with WebSocket, SSE, rate limiting, and streaming",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "api", "auth",
            "websocket", "sse", "rate_limit", "redis", "caching",
            "database", "docker", "logging", "otel", "makefile",
        ],
    },
    "file-service": {
        "description": "File upload/storage service with S3, thumbnails, and metadata",
        "archetype": "service",
        "groups": [
            "dev", "linting", "testing", "typecheck", "api", "auth",
            "file_upload", "s3", "image", "file_utils", "database",
            "redis", "docker", "logging", "makefile",
        ],
    },
}


def recommend(
    archetype: str = typer.Argument(
        help="Project archetype: single-package, service, poly-repo, script-tool"
    ),
    preset: str = typer.Option(
        "",
        "--preset",
        "-p",
        help="Preset profile: minimal, standard, full, ai, data, web",
    ),
) -> None:
    """Recommend package groups for a project type.

    Shows which groups are recommended based on archetype and optional preset.
    Copy the output directly into your `pjkm init` command.
    """
    from rich.console import Console
    from rich.panel import Panel

    from pjkm.core.groups.registry import GroupRegistry

    console = Console()
    archetype = archetype.replace("-", "_")

    if preset:
        preset = preset.lower()
        if preset not in PRESETS:
            console.print(
                f"[red]Unknown preset: {preset}. "
                f"Options: {', '.join(PRESETS.keys())}[/red]"
            )
            raise typer.Exit(1)

        groups_for_preset = PRESETS[preset].get(archetype, [])
        if not groups_for_preset:
            console.print(
                f"[yellow]No preset '{preset}' for archetype '{archetype}'[/yellow]"
            )
            raise typer.Exit(1)

        groups_str = " ".join(f"-g {g}" for g in groups_for_preset)
        console.print(
            Panel(
                f"[bold]{preset.title()}[/bold] preset for [cyan]{archetype}[/cyan]\n\n"
                f"Groups ({len(groups_for_preset)}): "
                + ", ".join(f"[cyan]{g}[/cyan]" for g in groups_for_preset),
                title="Recommended Groups",
            )
        )
        console.print()
        console.print("[dim]Copy this command:[/dim]")
        console.print(
            f"  pjkm init my-project -a {archetype} {groups_str}"
        )
        return

    # No preset — show all presets for this archetype
    console.print(f"\n[bold]Presets for archetype: {archetype}[/bold]\n")
    for preset_name in PRESETS:
        groups_for_preset = PRESETS[preset_name].get(archetype, [])
        if not groups_for_preset:
            continue
        console.print(
            f"  [bold cyan]{preset_name}[/bold cyan] ({len(groups_for_preset)} groups): "
            + ", ".join(groups_for_preset)
        )
    console.print()
    console.print("[dim]Usage: pjkm recommend <archetype> --preset <name>[/dim]")

    # Also show all compatible groups
    registry = GroupRegistry()
    registry.load_all()
    compatible = registry.list_for_archetype(archetype)
    console.print(
        f"\n[dim]Total compatible groups for {archetype}: {len(compatible)}[/dim]"
    )


def recipe(
    name: str = typer.Argument(
        "",
        help="Recipe name: python-lib, fastapi-service, ai-agent, ml-pipeline, "
        "data-analysis, cli-tool, fullstack-web, monorepo, scraper, fintech",
    ),
    show: bool = typer.Option(
        False, "--show", "-s", help="Show recipe details without generating a command"
    ),
) -> None:
    """Generate a full pjkm init command from a named recipe.

    Recipes are opinionated, ready-to-use project configurations that combine
    an archetype, groups, and fragments into a single command. Use --show to
    inspect what a recipe includes before running it.
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    if not name:
        table = Table(title="Available Recipes")
        table.add_column("Recipe", style="cyan bold")
        table.add_column("Archetype", style="green")
        table.add_column("Groups", style="dim", justify="right")
        table.add_column("Description")
        for rname, rdata in RECIPES.items():
            table.add_row(
                rname,
                rdata["archetype"],
                str(len(rdata["groups"])),
                rdata["description"],
            )
        console.print(table)
        console.print()
        console.print("[dim]Usage: pjkm recipe <name> [--show][/dim]")
        return

    if name not in RECIPES:
        console.print(
            f"[red]Unknown recipe: {name}. "
            f"Options: {', '.join(RECIPES.keys())}[/red]"
        )
        raise typer.Exit(1)

    r = RECIPES[name]
    archetype = r["archetype"]
    groups = r["groups"]
    groups_str = " ".join(f"-g {g}" for g in groups)

    if show:
        console.print(
            Panel(
                f"[bold]{name}[/bold] — {r['description']}\n\n"
                f"Archetype: [green]{archetype}[/green]\n"
                f"Groups ({len(groups)}):\n"
                + "\n".join(f"  [cyan]{g}[/cyan]" for g in groups),
                title="Recipe Details",
            )
        )
        return

    console.print(
        Panel(
            f"[bold]{name}[/bold] — {r['description']}\n\n"
            f"Archetype: [green]{archetype}[/green]\n"
            f"Groups: {len(groups)}",
            title="Recipe",
        )
    )
    console.print()
    console.print("[dim]Run this command:[/dim]")
    console.print(
        f"  pjkm init my-project -a {archetype} {groups_str}"
    )
