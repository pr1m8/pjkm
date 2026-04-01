"""Registry index — fetch, cache, search, and install group packs."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

CACHE_DIR = Path.home() / ".pjkm" / "registry"
INDEX_CACHE = CACHE_DIR / "index.json"
INDEX_TTL = 3600  # 1 hour cache

# Default registry URL — points to a JSON index file
DEFAULT_REGISTRY_URL = "https://raw.githubusercontent.com/pr1m8/pjkm-registry/main/index.json"


@dataclass
class PackEntry:
    """A group pack in the registry."""

    name: str
    description: str
    url: str
    author: str = ""
    tags: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    stars: int = 0
    path: str = ""
    ref: str = ""

    def matches(self, query: str) -> bool:
        """Check if this pack matches a search query."""
        q = query.lower()
        return (
            q in self.name.lower()
            or q in self.description.lower()
            or any(q in tag.lower() for tag in self.tags)
            or any(q in g.lower() for g in self.groups)
        )


class RegistryIndex:
    """Fetches, caches, and searches the group pack registry."""

    def __init__(self, registry_url: str = DEFAULT_REGISTRY_URL) -> None:
        self.registry_url = registry_url
        self._packs: list[PackEntry] = []
        self._loaded = False

    def load(self, force_refresh: bool = False) -> None:
        """Load the index from cache or network."""
        if self._loaded and not force_refresh:
            return

        if not force_refresh and self._cache_valid():
            self._load_from_cache()
        else:
            self._fetch_remote()

        self._loaded = True

    def search(self, query: str) -> list[PackEntry]:
        """Search packs by name, description, tags, or group names."""
        self.load()
        if not query:
            return list(self._packs)
        return [p for p in self._packs if p.matches(query)]

    def get(self, name: str) -> PackEntry | None:
        """Get a pack by exact name."""
        self.load()
        for p in self._packs:
            if p.name == name:
                return p
        return None

    @property
    def packs(self) -> list[PackEntry]:
        self.load()
        return list(self._packs)

    def _cache_valid(self) -> bool:
        if not INDEX_CACHE.exists():
            return False
        age = time.time() - INDEX_CACHE.stat().st_mtime
        return age < INDEX_TTL

    def _load_from_cache(self) -> None:
        try:
            data = json.loads(INDEX_CACHE.read_text())
            self._packs = [PackEntry(**p) for p in data.get("packs", [])]
        except Exception:
            self._packs = []

    def _fetch_remote(self) -> None:
        """Fetch the index from the registry URL."""
        import urllib.error
        import urllib.request

        try:
            req = urllib.request.Request(
                self.registry_url,
                headers={"User-Agent": "pjkm/0.1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")

            data = json.loads(raw)
            self._packs = [PackEntry(**p) for p in data.get("packs", [])]

            # Cache it
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            INDEX_CACHE.write_text(raw)
        except (urllib.error.URLError, json.JSONDecodeError, OSError):
            # Fall back to cache if available
            if INDEX_CACHE.exists():
                self._load_from_cache()
            else:
                self._packs = _builtin_packs()


def _builtin_packs() -> list[PackEntry]:
    """Fallback built-in pack list when registry is unreachable."""
    return [
        PackEntry(
            name="pjkm-django",
            description="Django project scaffolding with settings, apps, middleware, and management commands",
            url="https://github.com/pr1m8/pjkm-pack-django.git",
            author="pr1m8",
            tags=["django", "web", "orm", "admin"],
            groups=["django", "django_rest", "django_admin", "django_celery"],
        ),
        PackEntry(
            name="pjkm-aws-lambda",
            description="AWS Lambda functions with SAM templates, layers, and API Gateway",
            url="https://github.com/pr1m8/pjkm-pack-aws-lambda.git",
            author="pr1m8",
            tags=["aws", "lambda", "serverless", "sam"],
            groups=["lambda_function", "lambda_layer", "api_gateway", "dynamodb"],
        ),
        PackEntry(
            name="pjkm-ml-ops",
            description="MLOps pipeline with DVC, MLflow, model serving, and feature stores",
            url="https://github.com/pr1m8/pjkm-pack-mlops.git",
            author="pr1m8",
            tags=["ml", "mlops", "dvc", "mlflow", "serving"],
            groups=["dvc", "mlflow", "model_serving", "feature_store"],
        ),
        PackEntry(
            name="pjkm-data-eng",
            description="Data engineering with dbt, Great Expectations, Dagster, and data contracts",
            url="https://github.com/pr1m8/pjkm-pack-data-eng.git",
            author="pr1m8",
            tags=["data", "dbt", "dagster", "quality"],
            groups=["dbt", "great_expectations", "dagster", "data_contracts"],
        ),
        PackEntry(
            name="pjkm-quant",
            description="Quantitative finance with backtesting, market data, and risk models",
            url="https://github.com/pr1m8/pjkm-pack-quant.git",
            author="pr1m8",
            tags=["quant", "finance", "trading", "backtest"],
            groups=["backtest", "market_data", "risk", "portfolio"],
        ),
        PackEntry(
            name="pjkm-iot",
            description="IoT device management with MQTT, time-series DB, and edge computing",
            url="https://github.com/pr1m8/pjkm-pack-iot.git",
            author="pr1m8",
            tags=["iot", "mqtt", "timeseries", "edge"],
            groups=["mqtt", "timescaledb", "edge_agent", "device_registry"],
        ),
        PackEntry(
            name="pjkm-gamedev",
            description="Game backend with matchmaking, leaderboards, inventory, and real-time sync",
            url="https://github.com/pr1m8/pjkm-pack-gamedev.git",
            author="pr1m8",
            tags=["game", "matchmaking", "leaderboard", "realtime"],
            groups=["matchmaking", "leaderboard", "inventory", "realtime_sync"],
        ),
        PackEntry(
            name="pjkm-auth-providers",
            description="OAuth2 providers — Google, GitHub, Apple, SAML, with multi-tenant support",
            url="https://github.com/pr1m8/pjkm-pack-auth-providers.git",
            author="pr1m8",
            tags=["auth", "oauth2", "saml", "sso"],
            groups=["oauth_google", "oauth_github", "oauth_apple", "saml", "multi_tenant"],
        ),
        PackEntry(
            name="pjkm-observability",
            description="Full observability stack — Datadog, PagerDuty, Sentry, custom dashboards",
            url="https://github.com/pr1m8/pjkm-pack-observability.git",
            author="pr1m8",
            tags=["observability", "datadog", "sentry", "pagerduty"],
            groups=["datadog", "pagerduty", "sentry_sdk", "dashboards"],
        ),
        PackEntry(
            name="pjkm-cms",
            description="Headless CMS with content models, media pipeline, and API endpoints",
            url="https://github.com/pr1m8/pjkm-pack-cms.git",
            author="pr1m8",
            tags=["cms", "content", "media", "headless"],
            groups=["content_models", "media_pipeline", "cms_api", "webhooks"],
        ),
    ]
