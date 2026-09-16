-- Expected baseline: 133,367 taxi rows, 3 weather response rows, 265 zones.

SELECT 'green_taxi' AS source, COUNT(*) AS row_count
FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
UNION ALL
SELECT 'weather', COUNT(*)
FROM nyc_mobility.nyc_bronze.bronze_weather_raw
UNION ALL
SELECT 'taxi_zones', COUNT(*)
FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw;
