# QA implementation report

**Status:** Locally implemented and passing; Databricks execution evidence pending

## Automated Python quality gates

The local suite exercises the same pure PySpark DataFrame builders used by the
Lakeflow registration modules. It covers configuration, ingestion utilities,
structured logging, schema casting, deduplication, deterministic keys,
March-to-May incremental behavior, and rerun idempotency.

Required CI gates are defined in `.github/workflows/tests.yml`:

- Python compilation
- Ruff formatting and linting
- Bandit source scan
- runtime dependency vulnerability audit
- full pytest suite with at least 70% coverage
- zero skipped tests

Latest local result at implementation time: 40 passed, 0 skipped, 81.82%
coverage, with no known vulnerable runtime dependencies.

## Databricks SQL acceptance suite

The SQL checks are executable and contain no disabled-template markers.
Run them after a successful Lakeflow refresh, in this order:

1. `tests/sql/bronze/`
2. `tests/sql/silver/01_green_taxi_validation.sql`
3. `tests/sql/silver/02_taxi_zones_validation.sql`
4. `tests/sql/silver/03_weather_validation.sql`
5. remaining reconciliation, coverage, key, and referential-integrity checks in
   `tests/sql/silver/`
6. all checks in `tests/sql/gold/`

Each acceptance query returns an explicit `PASS` or `FAIL`. Promotion requires
all structural gates to return `PASS`; quality observations such as documented
candidate taxi duplicates must be reviewed and recorded rather than silently
discarded.

## Reconciliation contracts

- Green Taxi Silver retains all Bronze records and preserves source measures.
- Weather Silver reconciles to the number of aligned hourly array positions,
  not to the number of Bronze API-response rows.
- Taxi Zones Silver represents the latest ingestion snapshot at one row per
  `location_id`.
- Gold taxi includes only in-window Silver rows with required timestamps and
  location keys.
- Gold weather includes only in-window hourly observations.
- Gold facts preserve source-file, source modification, ingestion, Silver
  processing, and Gold loading timestamps.
- `dim_zone` preserves source lineage; generated `dim_date` and `dim_hour`
  intentionally have no source-file lineage.

## Evidence still required

The following items require authenticated Databricks or GitHub access and are
not claimed as complete by local validation:

- successful bundle validation and development deployment
- successful raw landing and Lakeflow refresh run IDs
- actual March-May Bronze, Silver, and Gold counts
- outputs from every SQL acceptance query
- April/May incremental refresh and May rerun evidence in Delta tables
- configured workflow failure notification destination
- successful remote GitHub Actions run and reviewed pull request

Attach those results to the pull request before promotion to `testing`.
