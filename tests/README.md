# Tests

- `unit/`: offline Python unit tests
- `integration/`: acquisition and pipeline integration tests
- `sql/bronze/`: Bronze counts and lineage checks
- `sql/silver/`: Silver contract and reconciliation checks
- `sql/gold/`: Gold grain, relationship, and reconciliation checks
- `04_business_checks/`: business acceptance checks

Install `requirements-dev.txt`, then run Python tests with
`python -m pytest -q`. The integration suite starts a local Spark session and
executes the same pure DataFrame builders used by Lakeflow. Run SQL checks in
Databricks after their upstream tables exist. Placeholder or skipped quality
tests should not be committed.

The checked-in SQL uses the production-default `nyc_mobility` catalog. For a
development deployment, set the SQL editor catalog to `nyc_mobility_dev` and
replace the catalog qualifier before execution. Run Bronze, Silver, then Gold
checks; every acceptance `status` must be `PASS` before promotion.
