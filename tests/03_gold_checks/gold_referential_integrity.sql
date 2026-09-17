-- PENDING: Enable after Gold tables are implemented
-- Gold referential integrity checks
-- Validates that Gold fact tables reference valid dimension keys

-- Check 1: fact_taxi_trip pickup_date_key → dim_date
SELECT 'pickup_date' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN pickup_date_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN pickup_date_key NOT IN (SELECT date_key FROM nyc_mobility.nyc_gold.dim_date) THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip

UNION ALL

-- Check 2: fact_taxi_trip dropoff_date_key → dim_date
SELECT 'dropoff_date' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN dropoff_date_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN dropoff_date_key NOT IN (SELECT date_key FROM nyc_mobility.nyc_gold.dim_date) THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip

UNION ALL

-- Check 3: fact_taxi_trip pickup_hour_key → dim_hour
SELECT 'pickup_hour' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN pickup_hour_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN pickup_hour_key NOT IN (SELECT hour_key FROM nyc_mobility.nyc_gold.dim_hour) THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip

UNION ALL

-- Check 4: fact_taxi_trip dropoff_hour_key → dim_hour
SELECT 'dropoff_hour' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN dropoff_hour_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN dropoff_hour_key NOT IN (SELECT hour_key FROM nyc_mobility.nyc_gold.dim_hour) THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip

UNION ALL

-- Check 5: fact_taxi_trip pickup_zone_key → dim_zone
SELECT 'pickup_zone' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN pickup_zone_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN pickup_zone_key NOT IN (SELECT location_id FROM nyc_mobility.nyc_gold.dim_zone) THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip

UNION ALL

-- Check 6: fact_taxi_trip dropoff_zone_key → dim_zone
SELECT 'dropoff_zone' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN dropoff_zone_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN dropoff_zone_key NOT IN (SELECT location_id FROM nyc_mobility.nyc_gold.dim_zone) THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip

UNION ALL

-- Check 7: fact_taxi_trip pickup_weather_hour_key → fact_weather_hourly
SELECT 'pickup_weather' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN pickup_weather_hour_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN pickup_weather_hour_key IS NOT NULL 
                AND pickup_weather_hour_key NOT IN (SELECT weather_hour_key FROM nyc_mobility.nyc_gold.fact_weather_hourly) 
           THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip

UNION ALL

-- Check 8: fact_weather_hourly date_key → dim_date
SELECT 'weather_date' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN date_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN date_key NOT IN (SELECT date_key FROM nyc_mobility.nyc_gold.dim_date) THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_weather_hourly

UNION ALL

-- Check 9: fact_weather_hourly hour_key → dim_hour
SELECT 'weather_hour' AS check_type,
       COUNT(*) AS total_facts,
       SUM(CASE WHEN hour_key IS NULL THEN 1 ELSE 0 END) AS null_keys,
       SUM(CASE WHEN hour_key NOT IN (SELECT hour_key FROM nyc_mobility.nyc_gold.dim_hour) THEN 1 ELSE 0 END) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_weather_hourly;
