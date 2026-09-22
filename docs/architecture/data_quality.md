# Data quality architecture and response contract

## Scope and execution point

Runtime data-quality logic is implemented in
`src/nyc_mobility/quality/runner.py`. The thin Databricks entry point is
`notebooks/02_run_quality_checks.py`. The notebook is designed to run after the
medallion pipeline refresh and before downstream consumers or monitoring tasks.

Source files are validated while they are downloaded by the ingestion modules.
The quality notebook reuses those validators so Source/Ingestion results use the
same persisted contract as Bronze, Silver, and Gold SQL results.

The SQL checks are post-refresh validation. They can stop later workflow tasks,
but they cannot prevent Gold tables from being created by the pipeline refresh
that already completed. Preventing invalid rows from entering a table requires
Lakeflow expectations or transformation-level enforcement and is separate from
this post-refresh gate.

## Outcome and severity contract

Severity describes the importance of a rule. Outcome describes what happened
during one attempt. They are deliberately separate.

| Severity | Passing outcome | Violation outcome | Query or check error | Workflow action |
|---|---|---|---|---|
| `WARNING` | `PASS` | `WARN` | `ERROR` | Continue and investigate |
| `CRITICAL` | `PASS` | `FAIL` | `ERROR` | Persist results, then stop |

An unexecuted rule is never recorded as `PASS`. A status-based query that
returns no rows, omits its configured status column, or fails to execute is
recorded as `ERROR`. The exception type and message are stored in
`error_message`.

Two query contracts are supported:

- `all_status_pass`: at least one row must be returned and every configured
  status value must equal `PASS`.
- `no_rows`: the query returns violations only, so an empty result is `PASS`.

## Rule catalogue

The code owner for the runtime catalogue is Angela (`@mafelisilda`). The review
owner is Rhea (`@ItsYangCoder`). SQL paths are rendered through
`nyc_mobility.sql.render_sql_file`, so catalog, schema, analysis dates, timezone,
month count, and expected weather hours follow `PipelineConfig`.

| Rule | Layer and dataset | Source | Acceptance condition | Severity | Response |
|---|---|---|---|---|---|
| `source.green_taxi.YYYY-MM` | Source, Green Taxi | `ingestion.green_taxi.inspect_parquet` | Every configured monthly file is readable Parquet, nonempty, and contains the required trip columns | Critical | Stop; retain the file, inspect acquisition logs, then redownload or repair |
| `source.weather.START_END` | Source, Weather | `ingestion.weather.validate_weather` plus configured coverage | JSON has hourly data, valid unique timestamps, aligned arrays, and exactly 24 hourly positions per configured date | Critical | Stop; retain the response and retry acquisition after checking parameters |
| `source.taxi_zones` | Source, Taxi Zones | `ingestion.download_taxi_zones.profile_csv` | CSV is nonempty, has required columns, and has complete unique `LocationID` values | Critical | Stop; retain and replace the invalid snapshot |
| `bronze.expected_source_counts` | Bronze, all sources | `tests/sql/bronze/03_expected_source_counts.sql` | Query returns no baseline count differences | Warning | Continue, investigate a possible source revision, and approve a baseline change explicitly |
| `bronze.lineage` | Bronze, all sources | `tests/sql/bronze/02_bronze_lineage_checks.sql` | Every row reports zero missing source file, modification time, and ingestion time values | Critical | Stop and inspect Auto Loader lineage columns |
| `silver.weather_structure` | Silver, weather | `tests/sql/silver/03_weather_validation.sql` | Source arrays align; hour grain, configured coverage, units, ranges, and lineage all pass | Critical | Stop and inspect weather ingestion and transformation output |
| `silver.key_uniqueness` | Silver, all tables | `tests/sql/silver/silver_key_uniqueness.sql` | Every declared grain key has zero nulls and duplicates | Critical | Stop and investigate key construction or duplicate input |
| `silver.date_coverage` | Silver, taxi and weather | `tests/sql/silver/silver_date_coverage.sql` | Every configured date is present and every weather date contains 24 positions | Critical | Stop and identify missing source dates or transformation loss |
| `silver.referential_integrity` | Silver, taxi to zones | `tests/sql/silver/silver_referential_integrity.sql` | Pickup and dropoff orphan counts are zero | Critical | Stop and compare taxi location IDs with the zone snapshot |
| `silver.row_reconciliation` | Bronze to Silver | `tests/sql/silver/bronze_silver_reconciliation.sql` | Actual Silver grain counts equal expected Bronze-derived counts | Critical | Stop and inspect filters, exploding logic, and duplicate handling |
| `silver.measure_reconciliation` | Bronze to Silver taxi | `tests/sql/silver/silver_measure_reconciliation.sql` | Row count and fare, total, and distance sums are null-safe equal | Critical | Stop and inspect type conversion or row loss |
| `gold.key_uniqueness` | Gold, all tables | `tests/sql/gold/gold_key_uniqueness.sql` | Gold keys are complete and unique and fact lineage is complete | Critical | Stop and inspect fact or dimension key construction |
| `gold.referential_integrity` | Gold facts to dimensions | `tests/sql/gold/gold_referential_integrity.sql` | Null and orphan foreign-key counts are zero | Critical | Stop and rebuild or correct the affected dimensions or facts |
| `gold.row_reconciliation` | Silver to Gold facts | `tests/sql/gold/silver_gold_reconciliation.sql` | Eligible Silver rows equal Gold fact rows | Critical | Stop and inspect Gold eligibility filters and loads |
| `gold.measure_reconciliation` | Silver to Gold taxi | `tests/sql/gold/gold_measure_reconciliation.sql` | Eligible row count and taxi measures are null-safe equal | Critical | Stop and investigate aggregation or casting differences |
| `gold.taxi_weather_cardinality` | Gold, taxi and weather | `tests/sql/gold/taxi_weather_join_cardinality.sql` | Join preserves taxi row count with no missing or multiple weather matches | Critical | Stop and inspect weather grain and date/hour keys |

The larger exploratory SQL files such as
`tests/sql/silver/01_green_taxi_validation.sql` contain multiple result sets and
diagnostic statements. They remain useful for investigation but are not treated
as executable runtime rules. The runner uses the focused single-result queries
listed above.

## Persisted result contract

Results are stored in
`<catalog>.<quality_schema>.quality_results` as a Delta table with change data
feed enabled.

| Field | Meaning |
|---|---|
| `result_id` | Deterministic UUID derived from run, attempt, and rule |
| `run_id` | Databricks job run ID or caller-provided equivalent |
| `attempt_id` | Repair/retry attempt ID |
| `layer`, `dataset`, `rule_id` | Rule identity and scope |
| `severity`, `outcome` | Independent severity and evaluated result |
| `checked_at` | UTC evaluation timestamp |
| `actual_value`, `expected_value` | Extracted values when the rule exposes them |
| `failed_record_count` | Failed count when available, otherwise the count of failing result rows |
| `metrics_json` | Complete JSON representation of returned metrics |
| `error_message` | Visible execution or validation error |
| `action` | `CONTINUE`, `WARN_AND_INVESTIGATE`, or `STOP_AND_INVESTIGATE` |

The table is initialized idempotently. Results are written with `MERGE` on
`result_id`. Repeating the same run and attempt updates the same rule record;
using a new repair attempt preserves a new history record. All selected rules
execute before persistence so one failed check does not hide later results.
Critical failures are raised only after the complete result set is persisted.

The workflow identity needs `USE CATALOG`, `USE SCHEMA`, and permission to
create and modify the quality result table. These permissions must be verified
in the development workspace and are not proven by repository code.

## Workflow interface

Issue #5 owns the final `databricks.yml` wiring. The notebook accepts a
comma-separated `layers` parameter in addition to `run_id` and `attempt_id`.
The workflow should use two quality tasks:

1. Run a source-quality task after `land_raw_sources`, with `layers=source`.
   Consider `ALL_DONE` failure-path wiring so an incomplete landing attempt can
   still produce quality evidence while preserving the original failure.
2. Allow `refresh_medallion_pipeline` only after source quality passes.
3. Run a post-refresh task with `layers=bronze,silver,gold`.
4. Pass `run_id` using the Databricks job run ID.
5. Pass `attempt_id` using the repair count or equivalent attempt identity.
6. Allow a critical `QualityGateFailed` exception to preserve failed job status.
7. Read the `quality_summary` task value when a downstream task needs a compact
   outcome summary.

The full, queryable interface for monitoring issue #8 is the result table. The
task value contains only run ID, attempt ID, table name, outcome counts, and
failed rule IDs.

## Recovery actions

| Condition | Action |
|---|---|
| Source file missing or unreadable | Do not delete evidence automatically. Inspect landing and acquisition logs, correct access or redownload, then repair the job |
| Static Bronze baseline warning | Confirm whether the historical source was republished. Update the approved baseline only with evidence and review |
| Missing Bronze lineage | Inspect Auto Loader metadata projection and source-file permissions before rerunning |
| Silver key, coverage, or reconciliation failure | Compare the persisted metrics with the focused SQL query, correct source or transformation logic, and rerun from the appropriate upstream task |
| Gold key, reference, or reconciliation failure | Prevent downstream consumption, correct the dimension/fact build, and rerun the pipeline and quality task |
| Query `ERROR` | Check table existence, SQL compatibility, configuration rendering, and permissions. Never convert the error to `PASS` |
| Result persistence failure | Fix quality-schema/table permissions and rerun. A quality gate without queryable results is incomplete |

Transient infrastructure errors may use the workflow retry policy. Deterministic
quality failures should not be retried repeatedly without investigation.
Quarantine is not implemented by this issue and must not be claimed as an
automatic response.

## Verification

The Java-free unit suite covers passing rules, warning violations, critical
failures, query errors, empty and malformed results, configured target
rendering, metric extraction, source validators, retry-safe IDs, and persistence
before failure:

```powershell
python -m pytest tests/unit/test_quality_runner.py -q
python -m ruff check src/nyc_mobility/quality tests/unit/test_quality_runner.py notebooks/02_run_quality_checks.py
```

Still required in a development Databricks workspace:

1. Verify the workflow identity can create and modify the result table.
2. Run a successful quality task and query its persisted `PASS`/`WARN` rows.
3. Trigger one controlled critical failure and confirm the result persists
   before the task fails.
4. Repair the run and confirm the new attempt is preserved without duplicates.
5. Record redacted evidence and the table location for issues #6 and #8.
6. Keep the production schedule paused.
