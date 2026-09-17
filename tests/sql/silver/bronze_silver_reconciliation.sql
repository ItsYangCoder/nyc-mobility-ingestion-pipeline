-- PENDING: Enable after silver_green_taxi_trips is implemented
-- Bronze → Silver row-count reconciliation
-- Expected: Silver should retain all Bronze rows (133,367) unless explicitly excluded
-- This check identifies any unexpected row count differences

WITH bronze_counts AS (
  SELECT 'green_taxi' AS source, COUNT(*) AS bronze_count
  FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
  UNION ALL
  SELECT 'weather', COUNT(*)
  FROM nyc_mobility.nyc_bronze.bronze_weather_raw
  UNION ALL
  SELECT 'taxi_zones', COUNT(*)
  FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
),
silver_counts AS (
  SELECT 'green_taxi' AS source, COUNT(*) AS silver_count
  FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
  UNION ALL
  SELECT 'weather', COUNT(*)
  FROM nyc_mobility.nyc_silver.silver_weather_hourly
  UNION ALL
  SELECT 'taxi_zones', COUNT(*)
  FROM nyc_mobility.nyc_silver.silver_taxi_zones
)
SELECT 
  b.source,
  b.bronze_count,
  s.silver_count,
  b.bronze_count - s.silver_count AS difference,
  CASE 
    WHEN b.bronze_count = s.silver_count THEN 'MATCH'
    ELSE 'REVIEW'
  END AS status
FROM bronze_counts b
LEFT JOIN silver_counts s ON b.source = s.source
WHERE b.bronze_count <> s.silver_count;
