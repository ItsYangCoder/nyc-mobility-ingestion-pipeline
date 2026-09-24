-- Shared result contract: source, expected_rows, actual_rows, row_difference,
-- fare_difference, total_difference, distance_difference, status.
-- Taxi exclusion reasons are ordered and mutually exclusive, preventing a row
-- with several missing fields from being counted more than once.

WITH taxi_classified AS (
    SELECT CASE
        WHEN NOT COALESCE(is_in_analysis_window, false)
            THEN 'outside_analysis_window'
        WHEN pickup_ts_local IS NULL OR dropoff_ts_local IS NULL
            THEN 'missing_trip_timestamp'
        WHEN pu_location_id IS NULL THEN 'missing_pickup_location'
        WHEN do_location_id IS NULL THEN 'missing_dropoff_location'
        ELSE 'eligible'
    END AS eligibility_reason
    FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
),
counts AS (
    SELECT
        'green_taxi' AS source,
        COUNT_IF(eligibility_reason = 'eligible') AS eligible_silver_rows,
        COUNT_IF(eligibility_reason != 'eligible') AS expected_excluded_rows,
        COUNT_IF(eligibility_reason = 'outside_analysis_window')
            AS outside_analysis_window_rows,
        COUNT_IF(eligibility_reason = 'missing_trip_timestamp')
            AS missing_trip_timestamp_rows,
        COUNT_IF(eligibility_reason = 'missing_pickup_location')
            AS missing_pickup_location_rows,
        COUNT_IF(eligibility_reason = 'missing_dropoff_location')
            AS missing_dropoff_location_rows,
        (SELECT COUNT(*) FROM nyc_mobility.nyc_gold.fact_taxi_trip) AS gold_rows
    FROM taxi_classified
    UNION ALL
    SELECT
        'weather',
        COUNT_IF(COALESCE(is_in_analysis_window, false)),
        COUNT_IF(NOT COALESCE(is_in_analysis_window, false)),
        COUNT_IF(NOT COALESCE(is_in_analysis_window, false)),
        0,
        0,
        0,
        (SELECT COUNT(*) FROM nyc_mobility.nyc_gold.fact_weather_hourly)
    FROM nyc_mobility.nyc_silver.silver_weather_hourly
)
SELECT
       source,
       eligible_silver_rows AS expected_rows,
       gold_rows AS actual_rows,
       gold_rows - eligible_silver_rows AS row_difference,
       CAST(NULL AS DECIMAL(20, 4)) AS fare_difference,
       CAST(NULL AS DECIMAL(20, 4)) AS total_difference,
       CAST(NULL AS DECIMAL(20, 4)) AS distance_difference,
       CASE WHEN eligible_silver_rows = gold_rows THEN 'PASS' ELSE 'FAIL' END AS status
FROM counts
ORDER BY source;
