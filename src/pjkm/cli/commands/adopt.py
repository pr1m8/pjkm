"""Adopt and status commands — integrate pjkm with existing projects."""

from __future__ import annotations

import typer


def adopt(
    directory: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Project directory to scan (default: cwd)",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Actually apply detected groups (default: just show suggestions)",
    ),
) -> None:
    """Scan an existing project and suggest pjkm groups to adopt.

    Reads pyproject.toml, requirements files, and project structure to detect
    what frameworks, tools, and patterns are already in use, then maps them
    to pjkm groups.

    Examples:

      pjkm adopt                  # scan cwd, show suggestions
      pjkm adopt --dir ../myapi   # scan another project
      pjkm adopt --apply          # scan and apply detected groups
    """
    import re
    from pathlib import Path

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    from rich.console import Console
    from rich.table import Table

    console = Console()
    project_dir = Path(directory).resolve() if directory else Path.cwd()

    # --- Gather signals ---
    signals: dict[str, list[str]] = {}  # group_id -> [reasons]

    # 1. Scan pyproject.toml dependencies
    pyproject_path = project_dir / "pyproject.toml"
    all_deps: list[str] = []
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        # Main dependencies
        main_deps = pyproject.get("project", {}).get("dependencies", [])
        all_deps.extend(main_deps)
        # Optional dependencies
        for section_deps in pyproject.get("project", {}).get("optional-dependencies", {}).values():
            all_deps.extend(section_deps)

    # 2. Scan requirements*.txt
    for req_file in project_dir.glob("requirements*.txt"):
        for line in req_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                all_deps.append(line)

    # Normalize dep names
    dep_names = set()
    for dep in all_deps:
        m = re.match(r"^([a-zA-Z0-9_-]+)", dep.replace("[", " ").split()[0])
        if m:
            dep_names.add(m.group(1).lower().replace("-", "_"))

    # 3. Map deps to groups
    DEP_TO_GROUP: dict[str, tuple[str, str]] = {
        "fastapi": ("api", "FastAPI found in dependencies"),
        "uvicorn": ("api", "Uvicorn found in dependencies"),
        "sqlalchemy": ("database", "SQLAlchemy found in dependencies"),
        "alembic": ("database", "Alembic found in dependencies"),
        "asyncpg": ("database", "asyncpg found in dependencies"),
        "redis": ("redis", "redis-py found in dependencies"),
        "celery": ("celery", "Celery found in dependencies"),
        "structlog": ("logging", "structlog found in dependencies"),
        "rich": ("logging", "Rich found in dependencies"),
        "pytest": ("testing", "pytest found in dependencies"),
        "pytest_cov": ("coverage", "pytest-cov found in dependencies"),
        "coverage": ("coverage", "coverage found in dependencies"),
        "ruff": ("linting", "Ruff found in dependencies"),
        "pyright": ("typecheck", "Pyright found in dependencies"),
        "mypy": ("typecheck", "mypy found in dependencies"),
        "sphinx": ("docs", "Sphinx found in dependencies"),
        "mkdocs": ("docs_mkdocs", "MkDocs found in dependencies"),
        "bandit": ("security", "Bandit found in dependencies"),
        "python_jose": ("auth", "python-jose found in dependencies"),
        "passlib": ("auth", "passlib found in dependencies"),
        "pydantic_settings": ("config_mgmt", "pydantic-settings found in dependencies"),
        "httpx": ("http_client", "httpx found in dependencies"),
        "langchain": ("langchain", "LangChain found in dependencies"),
        "langchain_core": ("langchain", "LangChain core found in dependencies"),
        "langgraph": ("langgraph", "LangGraph found in dependencies"),
        "transformers": ("hf", "Transformers found in dependencies"),
        "torch": ("torch", "PyTorch found in dependencies"),
        "scikit_learn": ("ml", "scikit-learn found in dependencies"),
        "pandas": ("ml", "pandas found in dependencies"),
        "matplotlib": ("dataviz", "matplotlib found in dependencies"),
        "seaborn": ("dataviz", "seaborn found in dependencies"),
        "plotly": ("dataviz", "plotly found in dependencies"),
        "motor": ("mongodb", "motor (MongoDB) found in dependencies"),
        "kafka": ("kafka", "kafka-python found in dependencies"),
        "confluent_kafka": ("kafka", "confluent-kafka found in dependencies"),
        "pika": ("rabbitmq", "pika (RabbitMQ) found in dependencies"),
        "boto3": ("aws", "boto3 found in dependencies"),
        "kubernetes": ("k8s", "kubernetes-py found in dependencies"),
        "opentelemetry_api": ("otel", "OpenTelemetry found in dependencies"),
        "opentelemetry_sdk": ("otel", "OpenTelemetry found in dependencies"),
        "prometheus_client": ("monitoring", "Prometheus client found in dependencies"),
        "flower": ("celery", "Flower found in dependencies"),
        "slowapi": ("rate_limit", "SlowAPI found in dependencies"),
        "websockets": ("websocket", "websockets found in dependencies"),
        "stripe": ("payments", "Stripe found in dependencies"),
        "sentry_sdk": ("error_tracking", "Sentry SDK found in dependencies"),
        "jupyterlab": ("jupyter", "JupyterLab found in dependencies"),
        "neo4j": ("neo4j", "neo4j found in dependencies"),
        "elasticsearch": ("elasticsearch", "elasticsearch found in dependencies"),
        "supabase": ("supabase", "supabase found in dependencies"),
        "weasyprint": ("pdf", "WeasyPrint found in dependencies"),
        "pillow": ("image", "Pillow found in dependencies"),
        "ffmpeg_python": ("video", "ffmpeg-python found in dependencies"),
        "librosa": ("audio", "librosa found in dependencies"),
        "pytesseract": ("ocr", "pytesseract found in dependencies"),
        "typer": ("cli_rich", "Typer found in dependencies"),
        "streamlit": ("streamlit", "Streamlit found in dependencies"),
        "gradio": ("gradio", "Gradio found in dependencies"),
    }

    for dep_name, (group_id, reason) in DEP_TO_GROUP.items():
        if dep_name in dep_names:
            signals.setdefault(group_id, []).append(reason)

    # 4. Scan project structure for signals
    structure_checks: list[tuple[str, str, str]] = [
        ("Dockerfile", "docker", "Dockerfile found"),
        ("docker-compose.yml", "docker", "docker-compose.yml found"),
        ("compose.yaml", "docker", "compose.yaml found"),
        ("compose.yml", "docker", "compose.yml found"),
        (".dockerignore", "docker", ".dockerignore found"),
        ("k8s", "k8s", "k8s/ directory found"),
        ("helm", "k8s", "helm/ directory found"),
        ("Makefile", "makefile", "Makefile found"),
        ("alembic", "database", "alembic/ directory found"),
        ("alembic.ini", "database", "alembic.ini found"),
        (".pre-commit-config.yaml", "linting", ".pre-commit-config.yaml found"),
        ("docs", "docs", "docs/ directory found"),
        ("mkdocs.yml", "docs_mkdocs", "mkdocs.yml found"),
        (".github/workflows", "ci_cd", ".github/workflows/ found"),
        ("CODEOWNERS", "github_templates", "CODEOWNERS found"),
        ("CONTRIBUTING.md", "github_templates", "CONTRIBUTING.md found"),
        (".gitmodules", "submodules", ".gitmodules found"),
        ("notebooks", "jupyter", "notebooks/ directory found"),
        ("scripts", "scripts", "scripts/ directory found"),
        ("infra/nginx", "nginx", "infra/nginx/ found"),
    ]

    for path, group_id, reason in structure_checks:
        if (project_dir / path).exists():
            signals.setdefault(group_id, []).append(reason)

    if not signals:
        console.print("[dim]No recognizable frameworks or tools detected.[/dim]")
        console.print("[dim]Tip: make sure pyproject.toml or requirements.txt exists.[/dim]")
        raise typer.Exit(0)

    # --- Check what's already tracked ---
    already_tracked: list[str] = []
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        already_tracked = pyproject.get("tool", {}).get("pjkm", {}).get("groups", [])

    # --- Display results ---
    new_groups = {g: reasons for g, reasons in signals.items() if g not in already_tracked}
    existing_groups = {g: reasons for g, reasons in signals.items() if g in already_tracked}

    if existing_groups:
        console.print(f"\n[bold green]Already tracked ({len(existing_groups)}):[/bold green]")
        for g in sorted(existing_groups):
            console.print(f"  [green]{g}[/green]")

    if new_groups:
        table = Table(title=f"Detected Groups ({len(new_groups)} new)")
        table.add_column("Group", style="cyan bold")
        table.add_column("Signals")
        for g in sorted(new_groups):
            table.add_row(g, "\n".join(new_groups[g]))
        console.print()
        console.print(table)

        groups_str = " ".join(f"-g {g}" for g in sorted(new_groups))
        console.print()

        if apply:
            # Actually add the groups
            from typer.testing import CliRunner

            from pjkm.cli.app import app as pjkm_app

            runner = CliRunner()
            add_args = ["add"] + [arg for g in sorted(new_groups) for arg in ("-g", g)]
            if directory:
                add_args.extend(["--dir", directory])
            result = runner.invoke(pjkm_app, add_args)
            console.print(result.stdout)
        else:
            console.print("[dim]To adopt these groups:[/dim]")
            dir_flag = f" --dir {directory}" if directory else ""
            console.print(f"  pjkm add {groups_str}{dir_flag}")
            console.print()
            console.print("[dim]Or auto-apply:[/dim]")
            console.print(f"  pjkm adopt --apply{dir_flag}")
    else:
        console.print("\n[bold green]All detected groups are already tracked![/bold green]")


def status(
    directory: str = typer.Option(
        "",
        "--dir",
        "-d",
        help="Project directory (default: cwd)",
    ),
) -> None:
    """Show the pjkm status of a project.

    Displays applied groups, archetype, dependency drift, and available
    upgrades. Like `git status` but for your project scaffolding.
    """
    from pathlib import Path

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from pjkm.core.groups.registry import GroupRegistry

    console = Console()
    project_dir = Path(directory).resolve() if directory else Path.cwd()
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.exists():
        console.print(f"[red]No pyproject.toml in {project_dir}[/red]")
        raise typer.Exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    pjkm_config = pyproject.get("tool", {}).get("pjkm", {})
    archetype = pjkm_config.get("archetype", "")
    applied_groups = pjkm_config.get("groups", [])
    project_name = pyproject.get("project", {}).get("name", project_dir.name)

    console.print(
        Panel(
            f"[bold]{project_name}[/bold]\n"
            f"Archetype: [cyan]{archetype or '(not set)'}[/cyan]\n"
            f"Groups: [cyan]{len(applied_groups)}[/cyan] applied\n"
            f"Directory: [dim]{project_dir}[/dim]",
            title="pjkm status",
        )
    )

    if not applied_groups:
        console.print("[dim]No groups applied. Use `pjkm add` or `pjkm adopt`.[/dim]")
        return

    # Load registry to check for drift
    registry = GroupRegistry()
    registry.load_all()

    # Check each group
    table = Table(title="Applied Groups")
    table.add_column("Group", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Status", style="green")

    optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})

    for gid in sorted(applied_groups):
        group = registry.get(gid)
        if group is None:
            table.add_row(gid, "?", "[red]not in registry[/red]")
            continue

        # Check if deps match
        status_str = "ok"
        for section, expected_deps in group.dependencies.items():
            actual_deps = optional_deps.get(section, [])
            actual_names = {
                d.split(">")[0].split("=")[0].split("<")[0].split("[")[0].strip().lower()
                for d in actual_deps
            }
            for dep in expected_deps:
                dep_name = (
                    dep.split(">")[0].split("=")[0].split("<")[0].split("[")[0].strip().lower()
                )
                if dep_name not in actual_names:
                    status_str = "[yellow]drift[/yellow]"
                    break

        table.add_row(gid, group.category, status_str)

    console.print(table)

    # Show available groups not yet applied
    all_ids = set(registry.group_ids)
    unapplied = all_ids - set(applied_groups)
    if unapplied and archetype:
        compatible = registry.list_for_archetype(archetype)
        compatible_unapplied = [g for g in compatible if g.id in unapplied]
        if compatible_unapplied:
            console.print(
                f"\n[dim]{len(compatible_unapplied)} more groups available "
                f"for {archetype}. Run `pjkm list groups` to browse.[/dim]"
            )
