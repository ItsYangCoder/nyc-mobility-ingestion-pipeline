-- Silver grain/key checks. Every row must return PASS.

WITH checks AS (
    SELECT 'silver_green_taxi_trips.trip_key' AS check_name,
           COUNT_IF(trip_key IS NULL) AS null_keys,
           COUNT(*) - COUNT(DISTINCT trip_key) AS duplicate_keys
    FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
    UNION ALL
    SELECT 'silver_weather_hourly.weather_hour_local',
           COUNT_IF(weather_hour_local IS NULL),
           COUNT(*) - COUNT(DISTINCT weather_hour_local)
    FROM nyc_mobility.nyc_silver.silver_weather_hourly
    UNION ALL
    SELECT 'silver_taxi_zones.location_id',
           COUNT_IF(location_id IS NULL),
           COUNT(*) - COUNT(DISTINCT location_id)
    FROM nyc_mobility.nyc_silver.silver_taxi_zones
)
SELECT check_name, null_keys, duplicate_keys,
       CASE WHEN null_keys = 0 AND duplicate_keys = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks
ORDER BY check_name;
