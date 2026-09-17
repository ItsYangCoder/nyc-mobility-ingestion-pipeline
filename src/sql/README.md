# SQL operational workspace

This directory contains executable, read-only Databricks SQL used to inspect,
validate, and reconcile pipeline outputs. It must not create or mutate production
tables, views, or materialized views.

## Ownership boundaries

| Concern | Location |
|---|---|
| Bronze/Silver/Gold table definitions | `transformations/` |
| Operational SQL validation and reconciliation | `src/sql/` |
| Automated acceptance and regression checks | `tests/` |
| Business-question queries and saved results | `analytics/` |
| Databricks orchestration entry points | `notebooks/` |

## Execution order

- `00_setup/`: catalog, schema, and access verification
- `01_bronze/`: Bronze counts and lineage checks
- `02_silver/`: executable Silver validation summaries
- `03_gold/`: executable Gold reconciliation after Gold is implemented

Only executable SQL belongs here. Planned checks remain in issues or
documentation until their upstream tables exist. Every validation query should
be read-only and return explicit evidence such as counts, differences, and
`PASS`/`FAIL` status.
