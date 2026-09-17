# Tests

- `unit/`: offline Python unit tests
- `integration/`: acquisition and pipeline integration tests
- `sql/bronze/`: Bronze counts and lineage checks
- `sql/silver/`: Silver contract and reconciliation checks
- `sql/gold/`: Gold grain, relationship, and reconciliation checks
- `04_business_checks/`: business acceptance checks

Run Python tests with `pytest -q`. Run SQL checks in Databricks after their
upstream tables exist. Placeholder SQL should not be committed.
