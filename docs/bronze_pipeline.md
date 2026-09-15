# Bronze Spark Declarative Pipeline

The Bronze pipeline reads the three required source folders from the Group C
external volume. Auto Loader tracks files already processed, so rerunning the
pipeline does not duplicate previously ingested files.

## Pipeline source

Configure the pipeline with this whole Git folder:

```text
transformations/bronze
```

It contains one table definition per source:

- `green_taxi.py`
- `weather.py`
- `taxi_zones.py`

## Databricks configuration

| Setting | Value |
| --- | --- |
| Pipeline name | `nyc_group_c_mobility_pipeline` |
| Pipeline mode | Triggered |
| Source code | `transformations/bronze` from the Git folder |
| Catalog | `nyc_mobility` |
| Schema | `nyc_group_c` |
| Compute | Serverless |

The source path already defaults to:

```text
/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing
```

No R2 keys are required in the pipeline.

## Expected Bronze tables

- `nyc_mobility.nyc_group_c.bronze_green_taxi_raw`
- `nyc_mobility.nyc_group_c.bronze_weather_raw`
- `nyc_mobility.nyc_group_c.bronze_taxi_zones_raw`

Each table keeps the source fields and adds:

- `_source_file`: exact landed file path
- `_ingested_at`: pipeline ingestion timestamp

Metadata sidecar files are excluded by exact filename patterns.

## First-run checks

Run these in the SQL Editor after the pipeline succeeds:

```sql
SELECT COUNT(*) AS green_taxi_rows
FROM nyc_mobility.nyc_group_c.bronze_green_taxi_raw;

SELECT COUNT(*) AS weather_files
FROM nyc_mobility.nyc_group_c.bronze_weather_raw;

SELECT COUNT(*) AS taxi_zone_rows
FROM nyc_mobility.nyc_group_c.bronze_taxi_zones_raw;
```

Expected results:

- Green Taxi: `133367` rows
- Weather: `3` raw API-response rows, one per monthly JSON file
- Taxi Zones: `265` rows

The Silver pipeline will later explode the weather hourly arrays, standardize
types and names, validate keys and dates, and deduplicate records.
