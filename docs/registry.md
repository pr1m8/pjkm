# Registry

Browse and install community group packs.

## Search

```bash
pjkm search              # list all
pjkm search django       # by keyword
pjkm search ml           # by tag
```

## Install

```bash
pjkm install pjkm-django
pjkm installed
pjkm uninstall pjkm-django
```

After install, pack groups appear in `pjkm list groups` and can be used in `pjkm init`.

## Available Packs

| Pack | Description |
|------|-------------|
| pjkm-django | Django scaffolding |
| pjkm-aws-lambda | AWS Lambda + SAM |
| pjkm-ml-ops | MLOps with DVC + MLflow |
| pjkm-data-eng | dbt + Dagster + Great Expectations |
| pjkm-quant | Quantitative finance |
| pjkm-iot | IoT with MQTT + TimescaleDB |
| pjkm-gamedev | Game backend |
| pjkm-auth-providers | OAuth2 providers |
| pjkm-observability | Datadog + Sentry |
| pjkm-cms | Headless CMS |

## Create Your Own Pack

See {doc}`pack-authoring`.
