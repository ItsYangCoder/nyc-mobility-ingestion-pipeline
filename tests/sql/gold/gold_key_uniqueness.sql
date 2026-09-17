-- Gold grain/key and lineage checks. Every row must return PASS.

WITH checks AS (
    SELECT 'fact_taxi_trip.trip_key' AS check_name,
           COUNT_IF(trip_key IS NULL) AS null_keys,
           COUNT(*) - COUNT(DISTINCT trip_key) AS duplicate_keys,
           COUNT_IF(source_file_modified_at IS NULL OR ingested_at IS NULL
                    OR silver_processed_at IS NULL OR gold_loaded_at IS NULL) AS missing_lineage
    FROM nyc_mobility.nyc_gold.fact_taxi_trip
    UNION ALL
    SELECT 'fact_weather_hourly.weather_hour_key',
           COUNT_IF(weather_hour_key IS NULL),
           COUNT(*) - COUNT(DISTINCT weather_hour_key),
           COUNT_IF(source_file_modified_at IS NULL OR ingested_at IS NULL
                    OR silver_processed_at IS NULL OR gold_loaded_at IS NULL)
    FROM nyc_mobility.nyc_gold.fact_weather_hourly
    UNION ALL
    SELECT 'dim_date.date_key', COUNT_IF(date_key IS NULL),
           COUNT(*) - COUNT(DISTINCT date_key), 0
    FROM nyc_mobility.nyc_gold.dim_date
    UNION ALL
    SELECT 'dim_hour.hour_key', COUNT_IF(hour_key IS NULL),
           COUNT(*) - COUNT(DISTINCT hour_key), 0
    FROM nyc_mobility.nyc_gold.dim_hour
    UNION ALL
    SELECT 'dim_zone.location_id', COUNT_IF(location_id IS NULL),
           COUNT(*) - COUNT(DISTINCT location_id),
           COUNT_IF(source_file_modified_at IS NULL OR ingested_at IS NULL
                    OR silver_processed_at IS NULL OR gold_loaded_at IS NULL)
    FROM nyc_mobility.nyc_gold.dim_zone
)
SELECT check_name, null_keys, duplicate_keys, missing_lineage,
       CASE WHEN null_keys = 0 AND duplicate_keys = 0 AND missing_lineage = 0
            THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks
ORDER BY check_name;
