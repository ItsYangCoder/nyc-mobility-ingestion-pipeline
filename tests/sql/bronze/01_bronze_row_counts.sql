-- Purpose: reconcile Bronze row counts with the approved source baseline.
-- Expected: green_taxi=133367, weather=3, taxi_zones=265.

WITH expected AS (
    SELECT *
    FROM VALUES
        ('green_taxi', 133367),
        ('weather', 3),
        ('taxi_zones', 265)
    AS expected(source, expected_rows)
),
actual AS (
    SELECT 'green_taxi' AS source, COUNT(*) AS actual_rows
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw

    UNION ALL

    SELECT 'weather' AS source, COUNT(*) AS actual_rows
    FROM nyc_mobility.nyc_bronze.bronze_weather_raw

    UNION ALL

    SELECT 'taxi_zones' AS source, COUNT(*) AS actual_rows
    FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
)
SELECT
    e.source,
    e.expected_rows,
    a.actual_rows,
    a.actual_rows - e.expected_rows AS row_difference,
    CASE
        WHEN a.actual_rows = e.expected_rows THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM expected e
JOIN actual a USING (source)
ORDER BY e.source;
