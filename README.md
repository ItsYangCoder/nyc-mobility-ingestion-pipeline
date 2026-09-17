# NYC Mobility Data Engineering Pipeline

A Databricks medallion pipeline that combines NYC Green Taxi trips, historical
Open-Meteo weather, and NYC Taxi Zones for March-May 2026.

## Architecture

```text
Source acquisition -> Unity Catalog Volume -> Bronze -> Silver -> Gold -> Analytics
```

## Repository layout

| Path | Purpose |
|---|---|
| `src/nyc_mobility/ingestion/` | Reusable source acquisition modules |
| `src/nyc_mobility/transformations/bronze/` | Bronze Lakeflow table definitions |
| `src/nyc_mobility/transformations/silver/` | Silver cleaning and conformance |
| `src/nyc_mobility/transformations/gold/` | Gold facts, dimensions, and aggregates |
| `src/sql/00_setup/` | Idempotent catalog and schema setup DDL |
| `tests/sql/` | Bronze, Silver, and Gold data-quality checks |
| `tests/unit/` | Offline Python unit tests |
| `tests/integration/` | Acquisition and pipeline integration tests |
| `notebooks/` | Thin Databricks orchestration entry points |
| `analytics/` | Business-question SQL and saved results |
| `config/` | Catalog, schema, and pipeline configuration |
| `docs/` | Architecture, contracts, profiles, and runbooks |

Production logic belongs under `src/`. Notebooks should orchestrate that logic,
not duplicate it. Validation queries belong under `tests/`.

## Quick start

Use Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --editable .
python -m pytest -q
```

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install --editable .
python -m pytest -q
```

## Databricks execution

The repository is deployed through the root `databricks.yml` bundle.

```bash
export DATABRICKS_HOST="https://<workspace-host>"
databricks bundle validate -t development
databricks bundle deploy -t development
databricks bundle run -t development mobility_workflow
```

Production additionally requires `BUNDLE_VAR_service_principal_name`. The
production schedule is intentionally deployed in `PAUSED` state and must be
enabled only after a reviewed smoke run. See
[`docs/runbooks/bundle_deployment.md`](docs/runbooks/bundle_deployment.md).

## Branch workflow

```text
feature/* or fix/* -> development -> testing -> main
```

Every promotion requires a pull request, review, and green CI. Do not commit
credentials, raw datasets, local environments, caches, or checkpoints.
