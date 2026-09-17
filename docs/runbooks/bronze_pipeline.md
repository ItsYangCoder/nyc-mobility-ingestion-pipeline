# Bronze Spark Declarative Pipeline

The Bronze layer reads the three required source folders from the Group C
external Volume. Auto Loader tracks files already processed, so rerunning the
pipeline does not duplicate previously ingested files.

The authoritative catalog and schema contract is
[`src/nyc_mobility/config.py`](../../src/nyc_mobility/config.py) and the
environment contract in [`.env.example`](../../.env.example).

## Pipeline source

During Bronze-only setup, the source path can be:

```text
transformations/bronze
```

For the required end-to-end graph, configure the complete source root:

```text
transformations
```

This allows the pipeline to discover Bronze, Silver, and Gold definitions.

## Databricks configuration

| Setting | Value |
| --- | --- |
| Pipeline name | `nyc_group_c_mobility_pipeline` |
| Pipeline mode | Triggered |
| Source code | `transformations` from the Git folder |
| Catalog | `nyc_mobility` |
| Default schema | `nyc_bronze` |
| Compute | Serverless |

The R2-backed landing Volume remains separate from the table schemas:

```text
/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing
```

The `nyc_group_c` schema owns the external Volume only. It is not the Bronze
table schema. No R2 keys are required in the pipeline code.

## Expected Bronze tables

- `nyc_mobility.nyc_bronze.bronze_green_taxi_raw`
- `nyc_mobility.nyc_bronze.bronze_weather_raw`
- `nyc_mobility.nyc_bronze.bronze_taxi_zones_raw`

Each table keeps the source fields and adds:

- `_source_file`: exact landed file path
- `_ingested_at`: pipeline ingestion timestamp

Metadata sidecar files are excluded by exact filename patterns.

## First-run checks

Run these in the SQL Editor after the pipeline succeeds:

```sql
SELECT COUNT(*) AS green_taxi_rows
FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw;

SELECT COUNT(*) AS weather_files
FROM nyc_mobility.nyc_bronze.bronze_weather_raw;

SELECT COUNT(*) AS taxi_zone_rows
FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw;
```

Expected results:

- Green Taxi: `133367` rows
- Weather: `3` raw API-response rows, one per monthly JSON file
- Taxi Zones: `265` rows

Silver definitions must publish to `nyc_mobility.nyc_silver`, Gold definitions
to `nyc_mobility.nyc_gold`, and validation/quarantine outputs to
`nyc_mobility.nyc_quality`.
