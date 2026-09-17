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
- **Silver:** typed, standardized, quality-checked source tables.
- **Gold:** integrated mobility facts and conformed dimensions.
- **Analytics:** reproducible SQL for the three required business questions.

See [the data model](docs/architecture/data_model.md) and [pipeline runbook](docs/runbooks/pipeline_execution.md).

## Repository layout

| Path | Purpose |
|---|---|
| `ingestion/` | Source acquisition scripts |
| `transformations/bronze/` | Bronze transformations |
| `transformations/silver/` | Silver transformations |
| `transformations/gold/` | Gold transformations |
| `analytics/` | Business-question SQL and result summaries |
| `notebooks/` | Ordered Databricks entry points |
| `src/sql/` | Validation, reconciliation, and analytics SQL |
| `tests/` | Local unit, integration, and data checks |
| `docs/` | Architecture, contracts, profiles, runbooks, and evidence |
| `config/` | Unity Catalog and pipeline naming configuration |

## Current status

Implemented foundations include:

- Green Taxi, historical weather, and Taxi Zones acquisition
- raw-file verification and acquisition evidence
- Unity Catalog external-volume landing
- Bronze pipeline structure
- local ingestion tests and pull-request CI
- architecture, contracts, runbooks, and validation SQL scaffolding

Silver, Gold, analytics, idempotency evidence, and final release validation are promoted through reviewed pull requests.

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
3. Configure the pipeline using the repository configuration under `config/`.
4. Run the applicable Bronze, Silver, and Gold transformations after their reviewed implementations land.
5. Run validation and reconciliation checks before promotion to `testing`.

Raw data lives in the external Volume and is not committed to Git.

## Documentation

- [Data model](docs/architecture/data_model.md)
- [Pipeline execution runbook](docs/runbooks/pipeline_execution.md)
- [Raw landing runbook](docs/runbooks/raw_landing.md)
- [Taxi Zones source profile](docs/contracts/taxi_zones_source_profile.md)
- [Evidence](docs/evidence/)

## DevOps branch workflow

| Branch | Environment | Purpose |
|---|---|---|
| `development` | Development | Integrates reviewed feature and fix branches |
| `testing` | Testing/QA | Holds release candidates for validation |
| `main` | Production | Contains only approved production releases |

```text
feature/* or fix/* -> pull request -> development
development -> release pull request -> testing
testing -> production pull request -> main
```

Every promotion requires a pull request, review, and green CI. Do not push feature work directly to `testing` or `main`.

Do not commit credentials, raw datasets, local environments, generated caches, or Databricks checkpoints.
