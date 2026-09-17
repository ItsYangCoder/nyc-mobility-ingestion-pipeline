-- Bronze-to-Silver reconciliation. Every row must return PASS.
-- Weather reconciles source array positions, not one Bronze API response row.

WITH expected AS (
    SELECT 'green_taxi' AS source, COUNT(*) AS expected_rows
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
    UNION ALL
    SELECT 'weather', SUM(SIZE(hourly.time))
    FROM nyc_mobility.nyc_bronze.bronze_weather_raw
    UNION ALL
    SELECT 'taxi_zones', COUNT(DISTINCT LocationID)
    FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
    WHERE _ingested_at = (
        SELECT MAX(_ingested_at)
        FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
    )
),
actual AS (
    SELECT 'green_taxi' AS source, COUNT(*) AS actual_rows
    FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
    UNION ALL
    SELECT 'weather', COUNT(*)
    FROM nyc_mobility.nyc_silver.silver_weather_hourly
    UNION ALL
    SELECT 'taxi_zones', COUNT(*)
    FROM nyc_mobility.nyc_silver.silver_taxi_zones
)
SELECT
    e.source,
    e.expected_rows,
    a.actual_rows,
    a.actual_rows - e.expected_rows AS row_difference,
    CASE WHEN a.actual_rows = e.expected_rows THEN 'PASS' ELSE 'FAIL' END AS status
FROM expected e
JOIN actual a USING (source)
ORDER BY e.source;
