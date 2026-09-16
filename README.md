# NYC Mobility Data Engineering Pipeline

An incremental data pipeline integrating NYC Green Taxi trips, historical Open-Meteo weather, and NYC Taxi Zones into a trusted mobility dataset for March-May 2026.

## Business questions

1. When and where is taxi demand highest?
2. How does weather affect taxi demand and trip behavior?
3. Which areas show the strongest mobility patterns or opportunities?

NYC DOT traffic advisories are optional and are outside the required scope.

## Architecture

Source acquisition -> Unity Catalog Volume -> Bronze -> Silver -> Gold -> Analytics

- **Ingestion:** reproducible downloads and raw-file validation
- **Bronze:** source-shaped streaming tables with file and ingestion lineage
- **Silver:** typed, standardized, and quality-flagged source tables
- **Gold:** integrated mobility facts and conformed dimensions
- **Analytics:** reproducible queries for the three required business questions

## Current main-branch status

Implemented and validated on main:

- Green Taxi, historical weather, and Taxi Zones acquisition
- raw-file verification and acquisition evidence
- Unity Catalog external-volume landing
- three Bronze Spark Declarative Pipeline tables
- offline ingestion tests and pull-request CI
- catalog and schema naming contract

Silver, Gold, analytics, idempotency evidence, and final release validation remain in progress and will be promoted through reviewed pull requests.

## Local validation

Use Python 3.12:

    python3.12 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    pytest -q

The pytest suite uses temporary files and mocked HTTP responses. It does not require credentials or downloaded datasets.

Raw-file verification requires the acquired files under data/raw:

    python tests/test_raw_files.py

Databricks Bronze execution and Volume access require the configured Databricks workspace and are not exercised by the offline test suite.

## Documentation

- [Databricks namespace contract](config/README.md)
- [Data model contract](docs/data_model.md)
- [Raw landing runbook](docs/databricks_raw_landing.md)
- [Bronze pipeline runbook](docs/bronze_pipeline.md)
- [Raw acquisition report](docs/raw_acquisition_report.md)

## Branch workflow

feature branch -> pull request to development -> review and green CI -> development  
development -> reviewed release pull request -> main

Do not commit credentials, raw datasets, local environments, generated caches, or Databricks checkpoints.
