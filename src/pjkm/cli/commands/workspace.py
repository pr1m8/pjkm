"""Workspace commands — multi-repo platform scaffolding."""

from __future__ import annotations

import json

import typer


# Pre-defined service templates for platform init
SERVICE_TEMPLATES: dict[str, dict] = {
    # --- Services ---
    "api": {
        "archetype": "service",
        "groups": ["api", "auth", "database", "redis", "logging", "otel",
                   "monitoring", "docker", "makefile"],
        "description": "Main API gateway",
    },
    "worker": {
        "archetype": "service",
        "groups": ["celery", "database", "redis", "logging", "otel", "docker", "makefile"],
        "description": "Background task worker",
    },
    "web": {
        "archetype": "service",
        "groups": ["frontend", "frontend_vite", "docker"],
        "description": "Frontend web application (Next.js / Vite)",
    },
    "scraper": {
        "archetype": "service",
        "groups": ["web_scraping", "crawling", "celery", "database", "redis",
                   "s3", "docker", "logging", "makefile"],
        "description": "Web scraping service",
    },
    "ml": {
        "archetype": "service",
        "groups": ["ml", "hf", "api", "database", "redis", "docker",
                   "logging", "makefile"],
        "description": "ML model serving",
    },
    "integration": {
        "archetype": "service",
        "groups": ["api", "http_client", "async_tools", "celery", "redis",
                   "database", "logging", "otel", "docker", "makefile"],
        "description": "Integration / webhook service (3rd party APIs)",
    },
    # --- Data Platform ---
    "ingestion": {
        "archetype": "service",
        "groups": ["api", "celery", "kafka", "database", "redis", "s3",
                   "docker", "logging", "otel", "makefile"],
        "description": "Data ingestion pipeline (CDC, streaming, batch)",
    },
    "warehouse": {
        "archetype": "service",
        "groups": ["database", "ml", "dataviz", "docker", "logging", "makefile"],
        "description": "Data warehouse / dbt transformations",
    },
    "orchestration": {
        "archetype": "service",
        "groups": ["airflow", "database", "redis", "docker", "logging", "makefile"],
        "description": "Workflow orchestration (Airflow / Dagster)",
    },
    "quality": {
        "archetype": "service",
        "groups": ["database", "api", "celery", "redis", "logging", "docker", "makefile"],
        "description": "Data quality checks and monitoring",
    },
    # --- Analytics ---
    "dashboards": {
        "archetype": "service",
        "groups": ["api", "database", "redis", "dataviz", "streamlit",
                   "docker", "logging", "makefile"],
        "description": "Analytics dashboards (Streamlit / Grafana)",
    },
    "analytics-events": {
        "archetype": "single-package",
        "groups": ["dev", "linting", "testing", "typecheck", "pydantic_extra"],
        "description": "Shared event schemas and typing (analytics contract)",
    },
    # --- Shared Packages ---
    "lib": {
        "archetype": "single-package",
        "groups": ["dev", "linting", "testing", "typecheck", "coverage", "docs"],
        "description": "Shared Python library",
    },
    "db-models": {
        "archetype": "single-package",
        "groups": ["dev", "linting", "testing", "typecheck", "database"],
        "description": "Shared database models + migrations",
    },
    "storage": {
        "archetype": "single-package",
        "groups": ["dev", "linting", "testing", "s3", "file_utils"],
        "description": "Shared storage / S3 client library",
    },
    "observability": {
        "archetype": "single-package",
        "groups": ["dev", "linting", "testing", "logging", "otel", "otel_instrumentations"],
        "description": "Shared observability (logging, tracing, metrics)",
    },
    # --- CLI / Tools ---
    "cli": {
        "archetype": "script-tool",
        "groups": ["cli_rich", "config_mgmt", "logging", "testing"],
        "description": "CLI tool / admin commands",
    },
    "tui": {
        "archetype": "script-tool",
        "groups": ["textual_tui", "cli_rich", "config_mgmt", "logging"],
        "description": "Terminal UI application",
    },
}

# Pre-defined platform blueprints
PLATFORM_BLUEPRINTS: dict[str, list[str]] = {
    "microservices": [
        "api:api", "jobs:worker", "site:web", "shared:lib",
    ],
    "data-platform": [
        "api:api", "ingestion:ingestion", "warehouse:warehouse",
        "orchestration:orchestration", "quality:quality", "dashboards:dashboards",
        "events:analytics-events", "shared:lib",
    ],
    "scraping-platform": [
        "api:api", "scraper:scraper", "jobs:worker", "site:web",
        "storage-lib:storage", "shared:lib",
    ],
    "ml-platform": [
        "api:api", "ml-service:ml", "jobs:worker", "data:ingestion",
        "dashboards:dashboards", "shared:lib", "models-pkg:db-models",
    ],
    "fullstack": [
        "api:api", "jobs:worker", "site:web", "integrations:integration",
        "shared:lib", "db-pkg:db-models", "obs-pkg:observability",
    ],
}


def workspace(
    name: str = typer.Argument(help="Workspace/platform name"),
    service: list[str] = typer.Option(
        [],
        "--service",
        "-s",
        help="Service to create: name:template (e.g. api:api, jobs:worker, site:web)",
    ),
    blueprint: str = typer.Option(
        "",
        "--blueprint",
        "-b",
        help="Use a pre-defined blueprint: microservices, data-platform, scraping-platform, ml-platform, fullstack",
    ),
    directory: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Parent directory (default: cwd)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be created without doing it",
    ),
) -> None:
    """Create a multi-service workspace with shared infrastructure.

    Generates multiple pjkm projects, a VS Code workspace file,
    root docker-compose, shared Makefile, and GitHub Actions.

    Service format: name:template — see `pjkm workspace --help` for templates.
    Or use --blueprint for a pre-defined platform layout.

    Examples:

      pjkm workspace my-platform -s api:api -s jobs:worker -s site:web
      pjkm workspace my-platform --blueprint microservices
      pjkm workspace my-platform --blueprint data-platform
      pjkm workspace my-platform --blueprint scraping-platform --dry-run
    """
    from pathlib import Path

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    # Blueprint expands to service list
    if blueprint:
        if blueprint not in PLATFORM_BLUEPRINTS:
            console.print(
                f"[red]Unknown blueprint: {blueprint}. "
                f"Options: {', '.join(PLATFORM_BLUEPRINTS.keys())}[/red]"
            )
            raise typer.Exit(1)
        service = list(PLATFORM_BLUEPRINTS[blueprint])
        console.print(f"[dim]Using blueprint '{blueprint}' ({len(service)} services)[/dim]")

    if not service:
        # Show available templates and blueprints
        table = Table(title="Service Templates")
        table.add_column("Template", style="cyan bold")
        table.add_column("Archetype", style="green")
        table.add_column("Groups", style="dim")
        table.add_column("Description")
        for tname, tdata in SERVICE_TEMPLATES.items():
            table.add_row(
                tname, tdata["archetype"],
                str(len(tdata["groups"])),
                tdata["description"],
            )
        console.print(table)
        console.print()
        bp_table = Table(title="Platform Blueprints")
        bp_table.add_column("Blueprint", style="cyan bold")
        bp_table.add_column("Services")
        for bp_name, bp_services in PLATFORM_BLUEPRINTS.items():
            names = [s.split(":")[0] for s in bp_services]
            bp_table.add_row(bp_name, ", ".join(names))
        console.print(bp_table)
        console.print()
        console.print("[dim]Usage: pjkm workspace my-platform --blueprint microservices[/dim]")
        console.print("[dim]   or: pjkm workspace my-platform -s api:api -s jobs:worker -s site:web[/dim]")
        return

    # Parse service specs
    services: list[dict] = []
    for spec in service:
        if ":" in spec:
            svc_name, template = spec.split(":", 1)
        else:
            svc_name = spec
            template = spec

        if template not in SERVICE_TEMPLATES:
            console.print(f"[red]Unknown template: {template}[/red]")
            console.print(f"Available: {', '.join(SERVICE_TEMPLATES.keys())}")
            raise typer.Exit(1)

        tmpl = SERVICE_TEMPLATES[template]
        services.append({
            "name": svc_name,
            "template": template,
            "archetype": tmpl["archetype"],
            "groups": tmpl["groups"],
            "description": tmpl["description"],
        })

    parent = Path(directory).resolve() if directory else Path.cwd()
    workspace_dir = parent / name

    console.print(
        Panel(
            f"[bold]{name}[/bold]\n"
            f"Services: {len(services)}\n"
            + "\n".join(f"  [cyan]{s['name']}[/cyan] ({s['template']}) — {s['description']}"
                        for s in services),
            title="Workspace",
        )
    )

    if dry_run:
        console.print("\n[bold]Dry run — nothing created[/bold]")
        console.print(f"\nWould create: {workspace_dir}/")
        for s in services:
            console.print(f"  {s['name']}/  ({s['archetype']}, {len(s['groups'])} groups)")
        console.print(f"  {name}.code-workspace")
        console.print(f"  docker-compose.yml")
        console.print(f"  Makefile")
        console.print(f"  .github/workflows/")
        raise typer.Exit(0)

    workspace_dir.mkdir(parents=True, exist_ok=True)

    # --- Init each service ---
    from typer.testing import CliRunner as _Runner
    from pjkm.cli.app import app as pjkm_app

    _runner = _Runner()
    for svc in services:
        console.print(f"\n[bold blue]Creating {svc['name']}...[/bold blue]")
        args = [
            "init", svc["name"],
            "-a", svc["archetype"],
            "--dir", str(workspace_dir),
        ]
        for g in svc["groups"]:
            args.extend(["-g", g])

        result = _runner.invoke(pjkm_app, args)
        if result.exit_code != 0:
            console.print(f"[red]Failed to create {svc['name']}[/red]")
            if result.stdout:
                console.print(result.stdout[-300:])
        else:
            console.print(f"  [green]Done[/green]")

    # --- VS Code workspace file ---
    workspace_config = {
        "folders": [
            {"path": svc["name"], "name": f"{svc['name']} ({svc['template']})"}
            for svc in services
        ],
        "settings": {
            "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
            "python.analysis.typeCheckingMode": "basic",
            "editor.formatOnSave": True,
            "[python]": {
                "editor.defaultFormatter": "charliermarsh.ruff",
                "editor.codeActionsOnSave": {"source.fixAll.ruff": "explicit"},
            },
            "files.exclude": {
                "**/__pycache__": True,
                "**/.pytest_cache": True,
                "**/.ruff_cache": True,
            },
        },
        "extensions": {
            "recommendations": [
                "charliermarsh.ruff",
                "ms-python.python",
                "ms-python.vscode-pylance",
                "ms-azuretools.vscode-docker",
                "redhat.vscode-yaml",
                "tamasfe.even-better-toml",
            ]
        },
    }
    ws_file = workspace_dir / f"{name}.code-workspace"
    ws_file.write_text(json.dumps(workspace_config, indent=2) + "\n")

    # --- Root docker-compose.yml ---
    compose_services = {}
    compose_services["postgres"] = {
        "image": "postgres:16",
        "environment": {
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
        },
        "ports": ["5432:5432"],
        "volumes": ["pgdata:/var/lib/postgresql/data"],
        "healthcheck": {
            "test": ["CMD-SHELL", "pg_isready -U postgres"],
            "interval": "5s",
            "timeout": "3s",
            "retries": 5,
        },
    }
    compose_services["redis"] = {
        "image": "redis:7-alpine",
        "ports": ["6379:6379"],
        "healthcheck": {
            "test": ["CMD", "redis-cli", "ping"],
            "interval": "5s",
            "timeout": "3s",
            "retries": 5,
        },
    }

    for svc in services:
        svc_slug = svc["name"].replace("-", "_")
        if svc["archetype"] == "service":
            svc_entry: dict = {
                "build": {"context": f"./{svc['name']}", "dockerfile": "Dockerfile"},
                "env_file": [f"./{svc['name']}/.env"],
                "depends_on": {},
            }
            if any(g in svc["groups"] for g in ["database", "celery"]):
                svc_entry["depends_on"]["postgres"] = {"condition": "service_healthy"}
            if any(g in svc["groups"] for g in ["redis", "celery"]):
                svc_entry["depends_on"]["redis"] = {"condition": "service_healthy"}
            if "api" in svc["groups"]:
                svc_entry["ports"] = ["8000:8000"]
            if "frontend" in svc["groups"]:
                svc_entry["ports"] = ["3000:3000"]
            compose_services[svc_slug] = svc_entry

    import yaml
    compose = {
        "version": "3.9",
        "services": compose_services,
        "volumes": {"pgdata": None},
    }
    (workspace_dir / "docker-compose.yml").write_text(
        yaml.dump(compose, default_flow_style=False, sort_keys=False)
    )

    # --- Root Makefile ---
    svc_names = [s["name"] for s in services]
    makefile_lines = [
        f"# {name} — multi-service workspace",
        f"SERVICES = {' '.join(svc_names)}",
        "",
        ".PHONY: up down build test lint",
        "",
        "up:",
        "\tdocker compose up -d",
        "",
        "down:",
        "\tdocker compose down",
        "",
        "build:",
        "\tdocker compose build",
        "",
        "test:",
        "\t@for svc in $(SERVICES); do echo \"\\n=== Testing $$svc ===\"; (cd $$svc && pdm run pytest -x -q) || exit 1; done",
        "",
        "lint:",
        "\t@for svc in $(SERVICES); do echo \"\\n=== Linting $$svc ===\"; (cd $$svc && pdm run ruff check .) || exit 1; done",
        "",
        "install:",
        "\t@for svc in $(SERVICES); do echo \"\\n=== Installing $$svc ===\"; (cd $$svc && pdm install) || exit 1; done",
        "",
    ]
    (workspace_dir / "Makefile").write_text("\n".join(makefile_lines) + "\n")

    # --- Shared GitHub Actions ---
    gh_dir = workspace_dir / ".github" / "workflows"
    gh_dir.mkdir(parents=True, exist_ok=True)

    ci_workflow = {
        "name": "CI",
        "on": {"push": {"branches": ["main"]}, "pull_request": None},
        "permissions": {"contents": "read"},
        "jobs": {},
    }
    for svc in services:
        svc_slug = svc["name"].replace("-", "_")
        ci_workflow["jobs"][f"test_{svc_slug}"] = {
            "runs-on": "ubuntu-latest",
            "defaults": {"run": {"working-directory": svc["name"]}},
            "steps": [
                {"uses": "actions/checkout@v4"},
                {"name": "Install PDM", "uses": "pdm-project/setup-pdm@v4",
                 "with": {"python-version": "3.13"}},
                {"name": "Install", "run": "pdm install -G testing"},
                {"name": "Test", "run": "pdm run pytest -x -q"},
            ],
        }
    (gh_dir / "ci.yml").write_text(yaml.dump(ci_workflow, default_flow_style=False, sort_keys=False))

    # --- Root .gitignore ---
    (workspace_dir / ".gitignore").write_text(
        "# Python\n__pycache__/\n*.pyc\n.venv/\n*.egg-info/\n\n"
        "# IDE\n.idea/\n.vscode/\n\n"
        "# Environment\n.env\n*.env.local\n\n"
        "# Data\npgdata/\n"
    )

    # --- Summary ---
    console.print(f"\n[bold green]Workspace {name} created at {workspace_dir}[/bold green]")
    console.print()
    console.print("[dim]Next steps:[/dim]")
    console.print(f"  cd {workspace_dir}")
    console.print(f"  code {name}.code-workspace    # open in VS Code")
    console.print(f"  make install                   # install all services")
    console.print(f"  make up                        # start Postgres + Redis + services")
    console.print(f"  make test                      # test all services")
