# SQL workspace

Numbered folders mirror the pipeline order and provide reviewable SQL entry points for Databricks SQL. Python/Spark table implementations remain under `transformations/`.

- `00_setup/`: catalog, schema, and access verification
- `01_bronze/`: read-only source inspection
- `02_silver/`: Silver validation and exploration
- `03_gold/`: Gold reconciliation and consumer views
- `04_analytics/`: the three required business questions

Files labeled as templates contain only comments until their upstream tables are implemented and accepted.
