# Databricks configuration

Use [`catalog_and_schemas.yml`](catalog_and_schemas.yml) as the single naming
contract for the complete NYC Mobility pipeline.

## Canonical namespaces

| Purpose | Namespace |
| --- | --- |
| Catalog | `nyc_mobility` |
| R2-backed landing Volume | `nyc_mobility.nyc_group_c.nyc_source_files` |
| Bronze tables | `nyc_mobility.nyc_bronze` |
| Silver tables | `nyc_mobility.nyc_silver` |
| Gold tables | `nyc_mobility.nyc_gold` |
| Quality and quarantine outputs | `nyc_mobility.nyc_quality` |

The landing schema `nyc_group_c` is for the external Volume only. Pipeline
tables must not be created there.

## Branch policy

Active configuration and transformation work belongs in `development`.
Promote `development` to `main` only through a reviewed pull request after
CI passes.

## Spark Declarative Pipeline publishing

The pipeline source root must include the complete `transformations/` folder.
Bronze definitions currently use unqualified table names and therefore publish
to the configured default schema `nyc_bronze`. Silver and Gold definitions
must publish to their fully qualified namespaces so one pipeline graph can show
Bronze → Silver → Gold.
