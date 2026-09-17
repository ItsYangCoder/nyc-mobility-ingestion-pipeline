-- PENDING: Enable after Silver tables are implemented
-- Silver key uniqueness checks
-- Validates that Silver deterministic technical keys are non-null and unique

-- Check 1: silver_green_taxi_trips.trip_key uniqueness
SELECT 'silver_green_taxi_trips' AS table_name,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT trip_key) AS distinct_trip_keys,
       SUM(CASE WHEN trip_key IS NULL THEN 1 ELSE 0 END) AS null_trip_keys,
       COUNT(*) - COUNT(DISTINCT trip_key) AS duplicate_trip_keys
FROM nyc_mobility.nyc_silver.silver_green_taxi_trips

UNION ALL

-- Check 2: silver_weather_hourly.weather_hour_local uniqueness
SELECT 'silver_weather_hourly' AS table_name,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT weather_hour_local) AS distinct_weather_hour_keys,
       SUM(CASE WHEN weather_hour_local IS NULL THEN 1 ELSE 0 END) AS null_weather_hour_keys,
       COUNT(*) - COUNT(DISTINCT weather_hour_local) AS duplicate_weather_hour_keys
FROM nyc_mobility.nyc_silver.silver_weather_hourly

UNION ALL

-- Check 3: silver_taxi_zones.location_id uniqueness
SELECT 'silver_taxi_zones' AS table_name,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT location_id) AS distinct_location_ids,
       SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END) AS null_location_ids,
       COUNT(*) - COUNT(DISTINCT location_id) AS duplicate_location_ids
FROM nyc_mobility.nyc_silver.silver_taxi_zones;
