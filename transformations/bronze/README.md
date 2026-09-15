# Bronze source modules

Each required source has a separate Spark Declarative Pipeline definition:

- `green_taxi.py`: March-May 2026 Green Taxi Parquet files
- `weather.py`: Open-Meteo raw JSON responses
- `taxi_zones.py`: NYC Taxi Zone lookup CSV

Configure the Databricks pipeline source code as this entire folder:

```text
transformations/bronze
```

The pipeline evaluates all three Python files and creates three Bronze streaming
tables. Do not add a source's metadata JSON file as an input; the code excludes
metadata sidecars through its file filter.
