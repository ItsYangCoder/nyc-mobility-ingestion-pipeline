-- TEMPLATE: enable after silver_weather_hourly is implemented.
-- Validate 2,208 source positions before DST/key handling, positional array
-- alignment, unique weather_hour_local, units, missing hours, and lineage.

-- ============================================================
-- WEATHER SILVER VALIDATION
-- ============================================================


-- 1. BASIC SUMMARY

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT weather_hour_local) AS unique_weather_hours,
    MIN(weather_hour_local) AS first_weather_hour,
    MAX(weather_hour_local) AS last_weather_hour
FROM nyc_mobility.nyc_silver.silver_weather_hourly;


-- 2. DUPLICATE WEATHER HOURS
-- Expected: 0 rows

SELECT
    weather_hour_local,
    COUNT(*) AS duplicate_count
FROM nyc_mobility.nyc_silver.silver_weather_hourly
GROUP BY weather_hour_local
HAVING COUNT(*) > 1
ORDER BY weather_hour_local;


-- 3. REQUIRED NULL CHECK
-- Expected: all 0

SELECT
    SUM(
        CASE WHEN weather_hour_local IS NULL
        THEN 1 ELSE 0 END
    ) AS weather_hour_nulls,

    SUM(
        CASE WHEN weather_date_local IS NULL
        THEN 1 ELSE 0 END
    ) AS weather_date_nulls,

    SUM(
        CASE WHEN timezone IS NULL
        THEN 1 ELSE 0 END
    ) AS timezone_nulls,

    SUM(
        CASE WHEN source_file IS NULL
        THEN 1 ELSE 0 END
    ) AS source_file_nulls,

    SUM(
        CASE WHEN ingested_at IS NULL
        THEN 1 ELSE 0 END
    ) AS ingested_at_nulls

FROM nyc_mobility.nyc_silver.silver_weather_hourly;


-- 4. MEASUREMENT NULL CHECK

SELECT
    SUM(
        CASE WHEN temperature_2m_c IS NULL
        THEN 1 ELSE 0 END
    ) AS temperature_nulls,

    SUM(
        CASE WHEN precipitation_mm IS NULL
        THEN 1 ELSE 0 END
    ) AS precipitation_nulls,

    SUM(
        CASE WHEN wind_speed_10m_kmh IS NULL
        THEN 1 ELSE 0 END
    ) AS wind_speed_nulls

FROM nyc_mobility.nyc_silver.silver_weather_hourly;


-- 5. TIMEZONE CHECK
-- Expected: America/New_York only

SELECT
    timezone,
    COUNT(*) AS row_count
FROM nyc_mobility.nyc_silver.silver_weather_hourly
GROUP BY timezone
ORDER BY timezone;


-- 6. MONTHLY COVERAGE

SELECT
    DATE_FORMAT(
        weather_hour_local,
        'yyyy-MM'
    ) AS month,

    COUNT(*) AS row_count,

    COUNT(
        DISTINCT weather_hour_local
    ) AS unique_hours

FROM nyc_mobility.nyc_silver.silver_weather_hourly

GROUP BY
    DATE_FORMAT(
        weather_hour_local,
        'yyyy-MM'
    )

ORDER BY month;


-- 7. ROWS OUTSIDE PROJECT PERIOD
-- Expected: 0 rows

SELECT *
FROM nyc_mobility.nyc_silver.silver_weather_hourly
WHERE weather_date_local < DATE '2026-03-01'
   OR weather_date_local > DATE '2026-05-31'
ORDER BY weather_hour_local;


-- 8. SOURCE LINEAGE

SELECT
    source_file,
    COUNT(*) AS row_count,
    MIN(weather_hour_local) AS first_weather_hour,
    MAX(weather_hour_local) AS last_weather_hour,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS last_ingested_at
FROM nyc_mobility.nyc_silver.silver_weather_hourly
GROUP BY source_file
ORDER BY first_weather_hour;


-- 9. OVERLAPPING SOURCE FILES
-- Expected: 0 rows

SELECT
    weather_hour_local,
    COUNT(DISTINCT source_file) AS source_file_count,
    COLLECT_SET(source_file) AS source_files
FROM nyc_mobility.nyc_silver.silver_weather_hourly
GROUP BY weather_hour_local
HAVING COUNT(DISTINCT source_file) > 1
ORDER BY weather_hour_local;


-- 10. INVALID PRECIPITATION
-- Expected: 0 rows

SELECT
    weather_hour_local,
    precipitation_mm,
    source_file
FROM nyc_mobility.nyc_silver.silver_weather_hourly
WHERE precipitation_mm < 0
ORDER BY weather_hour_local;


-- 11. INVALID WIND SPEED
-- Expected: 0 rows

SELECT
    weather_hour_local,
    wind_speed_10m_kmh,
    source_file
FROM nyc_mobility.nyc_silver.silver_weather_hourly
WHERE wind_speed_10m_kmh < 0
ORDER BY weather_hour_local;


-- 12. HOURLY GAP DIAGNOSTIC
-- Review results carefully because DST applies to America/New_York.

WITH ordered_weather AS (
    SELECT
        weather_hour_local,

        LAG(weather_hour_local) OVER (
            ORDER BY weather_hour_local
        ) AS previous_weather_hour

    FROM nyc_mobility.nyc_silver.silver_weather_hourly
)

SELECT
    previous_weather_hour,
    weather_hour_local,

    TIMESTAMPDIFF(
        MINUTE,
        previous_weather_hour,
        weather_hour_local
    ) AS minute_difference

FROM ordered_weather

WHERE previous_weather_hour IS NOT NULL
  AND TIMESTAMPDIFF(
        MINUTE,
        previous_weather_hour,
        weather_hour_local
      ) <> 60

ORDER BY weather_hour_local;


-- 13. FINAL VALIDATION SUMMARY

SELECT
    COUNT(*) AS total_rows,

    COUNT(
        DISTINCT weather_hour_local
    ) AS unique_weather_hours,

    COUNT(*)
        - COUNT(DISTINCT weather_hour_local)
        AS duplicate_hour_rows,

    SUM(
        CASE WHEN weather_hour_local IS NULL
        THEN 1 ELSE 0 END
    ) AS weather_hour_nulls,

    SUM(
        CASE WHEN timezone IS NULL
        THEN 1 ELSE 0 END
    ) AS timezone_nulls,

    SUM(
        CASE WHEN source_file IS NULL
        THEN 1 ELSE 0 END
    ) AS source_file_nulls,

    SUM(
        CASE WHEN ingested_at IS NULL
        THEN 1 ELSE 0 END
    ) AS ingested_at_nulls,

    SUM(
        CASE WHEN precipitation_mm < 0
        THEN 1 ELSE 0 END
    ) AS negative_precipitation_rows,

    SUM(
        CASE WHEN wind_speed_10m_kmh < 0
        THEN 1 ELSE 0 END
    ) AS negative_wind_rows,

    MIN(weather_hour_local) AS first_weather_hour,

    MAX(weather_hour_local) AS last_weather_hour,

    COUNT(
        DISTINCT source_file
    ) AS source_file_count

FROM nyc_mobility.nyc_silver.silver_weather_hourly;