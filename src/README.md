# Source code

This directory contains deployable pipeline code.

- `nyc_mobility/ingestion/`: idempotent raw-source acquisition
- `nyc_mobility/transformations/`: Lakeflow Bronze, Silver, and Gold definitions
- `sql/00_setup/`: idempotent Unity Catalog and schema setup

Keep notebooks thin. Put automated validation in `tests/` and business-facing
queries in `analytics/`.
