# Databricks raw landing runbook

This project has three required sources. NYC DOT Traffic Advisories is a bonus
source and is intentionally excluded.

## Destination

All source files land in this R2-backed external volume:

```text
/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing
├── green_taxi
├── weather
└── taxi_zones
```

Writing to a `/Volumes/...` path is enough. Do not add R2 keys to the code and
do not manually upload the files.

## Run in Databricks

1. In **Workspace**, create or open the Git folder for this repository.
2. Select the `development` branch and pull the latest changes.
3. Open `notebooks/01_land_raw_sources.py`.
4. Attach serverless compute, then click **Run all**.
5. The last cell must print:
   `PASS: all three required sources landed in the R2-backed volume.`
6. In **Catalog**, open
   `nyc_mobility > nyc_group_c > Volumes > nyc_source_files > landing`
   and click **Refresh**.

Expected source data files:

| Folder | Source data |
| --- | --- |
| `green_taxi` | 3 Parquet files: March, April, May 2026 |
| `weather` | 3 JSON source files plus 3 metadata files |
| `taxi_zones` | 1 CSV source file plus 1 metadata file |

The notebook and scripts are idempotent: rerunning them validates and reuses
existing valid source files instead of downloading duplicates.

## Optional Python task parameters

The scripts can also run as Databricks Python script tasks:

```text
ingestion/green_taxi.py
all
--output-dir
/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing/green_taxi
--inventory-path
/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing/green_taxi/_metadata/green_taxi_inventory.csv
```

```text
ingestion/weather.py
--start-date
2026-03-01
--end-date
2026-03-31
--output-dir
/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing/weather
```

Create separate weather tasks for April and May by changing both dates.
Taxi Zones parameters are:

```text
ingestion/download_taxi_zones.py
--output-dir
/Volumes/nyc_mobility/nyc_group_c/nyc_source_files/landing/taxi_zones
```

After the landing check passes, the next phase is a Spark Declarative Pipeline
that reads these three folders into Bronze tables.
