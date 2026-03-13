"""Configure task: set up pre-commit and trunk linting."""

from __future__ import annotations

from pjkm.core.engine.task_context import TaskContext
from pjkm.core.models.task import Phase, TaskResult
from pjkm.core.tasks.base import BaseTask

PRE_COMMIT_CONFIG = """\
---
# ===================================================================
# Pre-commit (Python 3.13)
#
# Goals:
# - No local hooks (only upstream repos)
# - Fast pre-commit by default (Ruff-centric)
# - Avoid Go toolchain hooks
#
# Stages:
# - pre-commit: fast hygiene + formatting
# - commit-msg: commitizen
# ===================================================================
minimum_pre_commit_version: 3.0.0
default_stages: [pre-commit]
fail_fast: false
default_language_version:
  python: python3.13
exclude: |
  (?x)^(
    .*/migrations/.*|
    .*/__pycache__/.*|
    \\.history/.*|
    \\.venv/.*|
    \\.nox/.*|
    \\.pytest_cache/.*|
    node_modules/.*|
    dist/.*|
    build/.*|
    .*\\.egg-info/.*
  )
repos:
  # ---------------------------------------------------------------------------
  # Baseline file hygiene
  # NOTE: Explicitly exclude pdm.lock from mutating hooks.
  # ---------------------------------------------------------------------------
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
        exclude: ^pdm\\.lock$
      - id: end-of-file-fixer
        exclude: ^pdm\\.lock$
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements
      - id: detect-private-key
      - id: check-added-large-files
        args: [--maxkb=1500]

  # ---------------------------------------------------------------------------
  # Python modernization
  # ---------------------------------------------------------------------------
  - repo: https://github.com/asottile/pyupgrade
    rev: v3.21.2
    hooks:
      - id: pyupgrade
        args: [--py313-plus]
        types: [python]

  # ---------------------------------------------------------------------------
  # Ruff (lint + format)
  # IMPORTANT: ruff-check runs before ruff-format because we use --fix.
  # ---------------------------------------------------------------------------
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.4
    hooks:
      - id: ruff-check
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # ---------------------------------------------------------------------------
  # Quick Python guardrails
  # ---------------------------------------------------------------------------
  - repo: https://github.com/pre-commit/pygrep-hooks
    rev: v1.10.0
    hooks:
      - id: python-check-blanket-noqa
        types: [python]
      - id: python-check-blanket-type-ignore
        types: [python]

  # ---------------------------------------------------------------------------
  # Docstrings
  # ---------------------------------------------------------------------------
  - repo: https://github.com/PyCQA/docformatter
    rev: v1.7.7
    hooks:
      - id: docformatter
        args: [--in-place]
        types: [python]

  # ---------------------------------------------------------------------------
  # Logger f-strings => lazy formatting
  # ---------------------------------------------------------------------------
  - repo: https://github.com/dmar1n/lazy-log-formatter
    rev: 0.11.0
    hooks:
      - id: lazy-log-formatter
        args: [--fix]
        types: [python]

  # ---------------------------------------------------------------------------
  # .editorconfig enforcement
  # ---------------------------------------------------------------------------
  - repo: https://github.com/editorconfig-checker/editorconfig-checker.python
    rev: 3.6.0
    hooks:
      - id: editorconfig-checker
        alias: ec

  # ---------------------------------------------------------------------------
  # Secrets
  # ---------------------------------------------------------------------------
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  # ---------------------------------------------------------------------------
  # YAML / Markdown linting
  # ---------------------------------------------------------------------------
  - repo: https://github.com/lyz-code/yamlfix/
    rev: 1.19.1
    hooks:
      - id: yamlfix
        files: \\.(yml|yaml)$
        exclude: ^\\.config/yamllint\\.ya?ml$
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.38.0
    hooks:
      - id: yamllint
        args: [--strict, -c, .config/yamllint.yaml]
  - repo: https://github.com/DavidAnson/markdownlint-cli2
    rev: v0.21.0
    hooks:
      - id: markdownlint-cli2
        args: [--config, .config/.markdownlint-cli2.yaml]

  # ---------------------------------------------------------------------------
  # Shell scripts
  # ---------------------------------------------------------------------------
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.11.0.1
    hooks:
      - id: shellcheck
        types: [shell]
  - repo: https://github.com/MaxWinterstein/shfmt-py
    rev: v3.12.0.1
    hooks:
      - id: shfmt
        args: [-w, -sr, -i, '2']
        types: [shell]

  # ---------------------------------------------------------------------------
  # Commit message (commit-msg stage)
  # ---------------------------------------------------------------------------
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.13.9
    hooks:
      - id: commitizen
        stages: [commit-msg]
"""

TRUNK_CONFIG = """\
# Trunk: https://docs.trunk.io/cli
# Trunk orchestrates pre-commit; pre-commit hooks run through trunk check.
version: 0.1
cli:
  version: 1.25.0
plugins:
  sources:
    - id: trunk
      ref: v1.7.6
      uri: https://github.com/trunk-io/plugins
actions:
  disabled:
    - git-lfs
    - trunk-announce
    - trunk-check-pre-push
    - trunk-fmt-pre-commit
  enabled:
    - trunk-upgrade-available
"""

SECRETS_BASELINE = """\
{
  "version": "1.5.0",
  "plugins_used": [
    {"name": "ArtifactoryDetector"},
    {"name": "AWSKeyDetector"},
    {"name": "AzureStorageKeyDetector"},
    {"name": "BasicAuthDetector"},
    {"name": "CloudantDetector"},
    {"name": "DiscordBotTokenDetector"},
    {"name": "HexHighEntropyString", "limit": 3.0},
    {"name": "IbmCloudIamDetector"},
    {"name": "IbmCosHmacDetector"},
    {"name": "JwtTokenDetector"},
    {"name": "KeywordDetector"},
    {"name": "MailchimpDetector"},
    {"name": "NpmDetector"},
    {"name": "PrivateKeyDetector"},
    {"name": "SendGridDetector"},
    {"name": "SlackDetector"},
    {"name": "SoftlayerDetector"},
    {"name": "SquareOAuthDetector"},
    {"name": "StripeDetector"},
    {"name": "TwilioKeyDetector"}
  ],
  "results": {}
}
"""


class ConfigureLintingTask(BaseTask):
    """Sets up pre-commit config, trunk config, and secrets baseline."""

    id = "configure_linting"
    phase = Phase.CONFIGURE
    depends_on = []
    description = "Configure pre-commit, trunk, and secrets baseline"

    def execute(self, ctx: TaskContext) -> TaskResult:
        project_dir = ctx.project_dir
        dry_run = ctx.config.dry_run
        would_create: list[str] = []

        # .pre-commit-config.yaml
        pre_commit_path = project_dir / ".pre-commit-config.yaml"
        if not pre_commit_path.exists():
            if not dry_run:
                pre_commit_path.write_text(PRE_COMMIT_CONFIG)
            would_create.append(".pre-commit-config.yaml")

        # .trunk/trunk.yaml
        trunk_dir = project_dir / ".trunk"
        if not dry_run:
            trunk_dir.mkdir(exist_ok=True)
        trunk_path = trunk_dir / "trunk.yaml"
        if not trunk_path.exists():
            if not dry_run:
                trunk_path.write_text(TRUNK_CONFIG)
            would_create.append(".trunk/trunk.yaml")

        # .secrets.baseline (for detect-secrets)
        baseline_path = project_dir / ".secrets.baseline"
        if not baseline_path.exists():
            if not dry_run:
                baseline_path.write_text(SECRETS_BASELINE)
            would_create.append(".secrets.baseline")

        # .config/ tool configs (if not already from archetype template)
        config_dir = project_dir / ".config"
        if not dry_run:
            config_dir.mkdir(exist_ok=True)

        yamllint_path = config_dir / "yamllint.yaml"
        if not yamllint_path.exists():
            if not dry_run:
                yamllint_path.write_text(YAMLLINT_CONFIG)
            would_create.append(".config/yamllint.yaml")

        mdlint_path = config_dir / ".markdownlint-cli2.yaml"
        if not mdlint_path.exists():
            if not dry_run:
                mdlint_path.write_text(MARKDOWNLINT_CONFIG)
            would_create.append(".config/.markdownlint-cli2.yaml")

        suffix = " (dry run)" if dry_run else ""
        return self.success_result(
            message=f"Linting configured: {', '.join(would_create) or '(all existed)'}{suffix}",
            files_created=would_create,
        )


YAMLLINT_CONFIG = """\
extends: default

rules:
  line-length:
    max: 120
  truthy:
    check-keys: false
  document-start: disable
"""

MARKDOWNLINT_CONFIG = """\
config:
  MD013:
    line_length: 120
  MD033: false
  MD041: false
"""
