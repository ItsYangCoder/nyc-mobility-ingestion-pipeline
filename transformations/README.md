# Transformations

Spark Declarative Pipeline table definitions are organized by medallion layer.

- `bronze/`: source-shaped streaming tables with file and ingestion lineage
- `silver/`: typed, standardized, quality-flagged source tables
- `gold/`: validated hourly and daily mobility outputs

Silver and Gold implementations must follow `docs/architecture/data_model.md`, include reproducible validation evidence, and enter through reviewed pull requests. Do not add placeholder table code.
