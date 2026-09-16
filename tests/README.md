# Tests

- `unit/`: local Python unit tests
- `integration/`: raw-file and acquisition integration tests
- `01_source_checks/`: Databricks SQL checks for landed/Bronze sources
- `02_silver_checks/`: Silver contract and reconciliation templates
- `03_gold_checks/`: Gold grain, join, and reconciliation templates
- `04_business_checks/`: analytics acceptance templates

Run local Python tests with `pytest -q`. SQL checks run in Databricks only after their upstream tables exist.
