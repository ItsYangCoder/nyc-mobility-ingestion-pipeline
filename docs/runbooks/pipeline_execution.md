# Pipeline execution runbook

## Order

1. Pull the latest reviewed branch in Databricks.
2. Run `notebooks/01_land_raw_sources.py`.
3. Validate landed files and Bronze tables.
4. Run reviewed Silver transformations.
5. Run Silver quality gates.
6. Run reviewed Gold transformations.
7. Reconcile Gold counts and measures to Silver.
8. Run the three analytics queries.
9. Record run links, table paths, counts, and limitations under `docs/evidence/`.

The current repository contains the raw landing and Bronze implementation. Silver, Gold, and analytics are added only through their dedicated reviewed pull requests.
