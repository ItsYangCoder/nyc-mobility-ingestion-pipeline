# NYC Mobility Data Engineering Pipeline

A Databricks medallion pipeline that combines NYC Green Taxi trips, historical Open-Meteo weather, and NYC Taxi Zones for March-May 2026.

## Business questions

1. When and where is taxi demand highest?
2. How does weather affect taxi demand and trip behavior?
3. Which areas show the strongest mobility patterns or opportunities?

The optional NYC DOT advisory source is outside the required scope.

## Architecture

```text
Source acquisition -> Unity Catalog Volume -> Bronze -> Silver -> Gold -> Analytics
```

- **Ingestion:** reproducible source downloads and raw validation.
- **Bronze:** source-shaped streaming tables with lineage.
- **Silver:** typed, standardized, quality-flagged source tables.
- **Gold:** hourly and daily mobility outputs with validated joins.
- **Analytics:** reproducible SQL for the three required business questions.

See [the data model](docs/architecture/data_model.md) and [pipeline runbook](docs/runbooks/pipeline_execution.md).

## Repository layout

| Path | Purpose |
|---|---|
| `ingestion/` | Source acquisition scripts |
| `transformations/bronze/` | Bronze Spark Declarative Pipeline tables |
| `transformations/silver/` | Silver transformations |
| `transformations/gold/` | Gold transformations |
| `analytics/` | Business-question SQL and small result summaries |
| `quality/` | Cross-layer checks, reconciliation, and idempotency |
| `notebooks/` | Ordered Databricks entry points |
| `tests/` | Local unit and integration tests |
| `docs/` | Architecture, contracts, profiles, runbooks, and evidence |
| `config/` | Unity Catalog and pipeline naming contract |

## Quick start

Use Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
```

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest -q
```

## Databricks execution

1. Pull the latest `development` branch in the Databricks Git folder.
2. Run `notebooks/01_land_raw_sources.py`.
3. Configure the triggered Spark Declarative Pipeline using `config/catalog_and_schemas.yml`.
4. Load all files under `transformations/bronze/`; add Silver and Gold source folders when their reviewed implementations land.
5. Run quality and reconciliation checks before analytics.

Raw data lives in the external Volume and is not committed to Git.

## Branch workflow

```text
feature branch -> pull request to development -> review + green CI -> development
development -> reviewed release pull request -> main
```

Do not commit credentials, raw datasets, local environments, generated caches, or Databricks checkpoints.
