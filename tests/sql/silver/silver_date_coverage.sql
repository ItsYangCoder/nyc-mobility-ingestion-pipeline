-- Configured-default date and hourly weather coverage. Every row must return PASS.

WITH expected_dates AS (
    SELECT EXPLODE(
        SEQUENCE(DATE '2026-03-01', DATE '2026-05-31', INTERVAL 1 DAY)
    ) AS expected_date
),
taxi AS (
    SELECT DISTINCT pickup_date_local AS observed_date
    FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
    WHERE is_in_analysis_window
),
weather_daily AS (
    SELECT weather_date_local AS observed_date, COUNT(*) AS observed_hours
    FROM nyc_mobility.nyc_silver.silver_weather_hourly
    WHERE is_in_analysis_window
    GROUP BY weather_date_local
),
daily_results AS (
    SELECT 'taxi_date' AS check_name, COUNT_IF(t.observed_date IS NULL) AS failures
    FROM expected_dates e LEFT JOIN taxi t ON e.expected_date = t.observed_date
    UNION ALL
    SELECT 'weather_date', COUNT_IF(w.observed_date IS NULL)
    FROM expected_dates e LEFT JOIN weather_daily w ON e.expected_date = w.observed_date
    UNION ALL
    SELECT 'weather_24_hours_per_day',
           COUNT_IF(w.observed_hours != 24 OR w.observed_hours IS NULL)
    FROM expected_dates e LEFT JOIN weather_daily w ON e.expected_date = w.observed_date
)
SELECT check_name, failures,
       CASE WHEN failures = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM daily_results
ORDER BY check_name;
