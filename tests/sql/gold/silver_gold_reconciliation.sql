-- Eligible Silver-to-Gold row reconciliation. Every row must return PASS.

WITH counts AS (
    SELECT 'taxi' AS fact,
           (SELECT COUNT(*)
            FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
            WHERE is_in_analysis_window
              AND pickup_ts_local IS NOT NULL
              AND dropoff_ts_local IS NOT NULL
              AND pu_location_id IS NOT NULL
              AND do_location_id IS NOT NULL) AS eligible_silver_rows,
           (SELECT COUNT(*) FROM nyc_mobility.nyc_gold.fact_taxi_trip) AS gold_rows
    UNION ALL
    SELECT 'weather',
           (SELECT COUNT(*)
            FROM nyc_mobility.nyc_silver.silver_weather_hourly
            WHERE is_in_analysis_window),
           (SELECT COUNT(*) FROM nyc_mobility.nyc_gold.fact_weather_hourly)
)
SELECT fact, eligible_silver_rows, gold_rows,
       gold_rows - eligible_silver_rows AS row_difference,
       CASE WHEN eligible_silver_rows = gold_rows THEN 'PASS' ELSE 'FAIL' END AS status
FROM counts
ORDER BY fact;
