-- A failing result returns one or more rows.
WITH actual AS (
  SELECT 'green_taxi' AS source, COUNT(*) AS actual_count, 133367 AS expected_count
  FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
  UNION ALL
  SELECT 'weather', COUNT(*), 3
  FROM nyc_mobility.nyc_bronze.bronze_weather_raw
  UNION ALL
  SELECT 'taxi_zones', COUNT(*), 265
  FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
)
SELECT *
FROM actual
WHERE actual_count <> expected_count;
