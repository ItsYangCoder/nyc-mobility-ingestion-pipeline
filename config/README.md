# Databricks configuration

Use `catalog_and_schemas.yml` as the naming contract for the complete pipeline.

| Purpose | Namespace |
|---|---|
| Catalog | `nyc_mobility` |
| R2-backed landing Volume | `nyc_mobility.nyc_group_c.nyc_source_files` |
| Bronze tables | `nyc_mobility.nyc_bronze` |
| Silver tables | `nyc_mobility.nyc_silver` |
| Gold tables | `nyc_mobility.nyc_gold` |
| Quality outputs | `nyc_mobility.nyc_quality` |

The landing schema is for the external Volume only. Configure the Lakeflow
pipeline source root as `src/nyc_mobility/transformations/`. Promote changes
through `development`, `testing`, and `main`.
