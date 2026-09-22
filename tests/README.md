# Tests

- `unit/`: offline Python unit tests
- `integration/`: acquisition and pipeline integration tests
- `sql/bronze/`: Bronze counts and lineage checks
- `sql/silver/`: Silver contract and reconciliation checks
- `sql/gold/`: Gold grain, relationship, and reconciliation checks

Install `requirements-dev.txt`, then run Python tests with
`python -m pytest -q`. The integration suite starts a local Spark session and
executes the same pure DataFrame builders used by Lakeflow. Run SQL checks in
Databricks after their upstream tables exist. Placeholder or skipped quality
tests should not be committed.

The checked-in SQL uses safe default identifiers. Render checks through the
central configuration instead of manually replacing catalog/schema names:

```bash
python -m nyc_mobility.sql tests/sql/silver/silver_date_coverage.sql
```

Run Bronze, Silver, then Gold checks against the rendered target; every
acceptance `status` must be `PASS` before promotion.
