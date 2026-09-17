-- PENDING: Enable after Gold tables are implemented
-- Gold key uniqueness checks
-- Validates that Gold surrogate keys are non-null and unique

-- Check 1: fact_taxi_trip.trip_key uniqueness
SELECT 'fact_taxi_trip' AS table_name,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT trip_key) AS distinct_trip_keys,
       SUM(CASE WHEN trip_key IS NULL THEN 1 ELSE 0 END) AS null_trip_keys,
       COUNT(*) - COUNT(DISTINCT trip_key) AS duplicate_trip_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip

UNION ALL

-- Check 2: fact_weather_hourly.weather_hour_key uniqueness
SELECT 'fact_weather_hourly' AS table_name,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT weather_hour_key) AS distinct_weather_hour_keys,
       SUM(CASE WHEN weather_hour_key IS NULL THEN 1 ELSE 0 END) AS null_weather_hour_keys,
       COUNT(*) - COUNT(DISTINCT weather_hour_key) AS duplicate_weather_hour_keys
FROM nyc_mobility.nyc_gold.fact_weather_hourly

UNION ALL

-- Check 3: dim_date.date_key uniqueness
SELECT 'dim_date' AS table_name,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT date_key) AS distinct_date_keys,
       SUM(CASE WHEN date_key IS NULL THEN 1 ELSE 0 END) AS null_date_keys,
       COUNT(*) - COUNT(DISTINCT date_key) AS duplicate_date_keys
FROM nyc_mobility.nyc_gold.dim_date

UNION ALL

-- Check 4: dim_hour.hour_key uniqueness
SELECT 'dim_hour' AS table_name,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT hour_key) AS distinct_hour_keys,
       SUM(CASE WHEN hour_key IS NULL THEN 1 ELSE 0 END) AS null_hour_keys,
       COUNT(*) - COUNT(DISTINCT hour_key) AS duplicate_hour_keys
FROM nyc_mobility.nyc_gold.dim_hour

UNION ALL

-- Check 5: dim_zone.location_id uniqueness
SELECT 'dim_zone' AS table_name,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT location_id) AS distinct_location_ids,
       SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END) AS null_location_ids,
       COUNT(*) - COUNT(DISTINCT location_id) AS duplicate_location_ids
FROM nyc_mobility.nyc_gold.dim_zone;
