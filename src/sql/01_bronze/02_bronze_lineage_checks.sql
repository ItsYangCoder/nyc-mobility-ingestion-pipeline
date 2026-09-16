-- Bronze lineage checks. Each result should be zero.

SELECT 'green_taxi' AS source,
       SUM(CASE WHEN _source_file IS NULL THEN 1 ELSE 0 END) AS missing_source_file,
       SUM(CASE WHEN _ingested_at IS NULL THEN 1 ELSE 0 END) AS missing_ingested_at
FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
UNION ALL
SELECT 'weather',
       SUM(CASE WHEN _source_file IS NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN _ingested_at IS NULL THEN 1 ELSE 0 END)
FROM nyc_mobility.nyc_bronze.bronze_weather_raw
UNION ALL
SELECT 'taxi_zones',
       SUM(CASE WHEN _source_file IS NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN _ingested_at IS NULL THEN 1 ELSE 0 END)
FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw;
