-- TEMPLATE: enable after silver_weather_hourly is implemented.
-- Validate 2,208 source positions before DST/key handling, positional array
-- alignment, unique weather_hour_local, units, missing hours, and lineage.

-- ============================================================
-- WEATHER SILVER VALIDATION
-- ============================================================

CREATE MATERIALIZED VIEW weather_silver_quality_validation
COMMENT 'Consolidated data quality validation for silver_weather_hourly'
AS

WITH base AS (
    SELECT *
    FROM silver_weather_hourly
),

summary AS (
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT weather_hour_local) AS unique_weather_hours,

        COUNT(*)
            - COUNT(DISTINCT weather_hour_local)
            AS duplicate_hour_rows,

        SUM(
            CASE
                WHEN weather_hour_local IS NULL
                THEN 1 ELSE 0
            END
        ) AS weather_hour_nulls,

        SUM(
            CASE
                WHEN weather_date_local IS NULL
                THEN 1 ELSE 0
            END
        ) AS weather_date_nulls,

        SUM(
            CASE
                WHEN timezone IS NULL
                THEN 1 ELSE 0
            END
        ) AS timezone_nulls,

        SUM(
            CASE
                WHEN source_file IS NULL
                THEN 1 ELSE 0
            END
        ) AS source_file_nulls,

        SUM(
            CASE
                WHEN ingested_at IS NULL
                THEN 1 ELSE 0
            END
        ) AS ingested_at_nulls,

        SUM(
            CASE
                WHEN temperature_2m_c IS NULL
                THEN 1 ELSE 0
            END
        ) AS temperature_nulls,

        SUM(
            CASE
                WHEN precipitation_mm IS NULL
                THEN 1 ELSE 0
            END
        ) AS precipitation_nulls,

        SUM(
            CASE
                WHEN wind_speed_10m_kmh IS NULL
                THEN 1 ELSE 0
            END
        ) AS wind_speed_nulls,

        SUM(
            CASE
                WHEN precipitation_mm < 0
                THEN 1 ELSE 0
            END
        ) AS negative_precipitation_rows,

        SUM(
            CASE
                WHEN wind_speed_10m_kmh < 0
                THEN 1 ELSE 0
            END
        ) AS negative_wind_rows,

        SUM(
            CASE
                WHEN temperature_2m_c < -50
                  OR temperature_2m_c > 60
                THEN 1 ELSE 0
            END
        ) AS suspicious_temperature_rows,

        SUM(
            CASE
                WHEN wind_speed_10m_kmh > 250
                THEN 1 ELSE 0
            END
        ) AS suspicious_wind_rows,

        SUM(
            CASE
                WHEN timezone <> 'America/New_York'
                THEN 1 ELSE 0
            END
        ) AS unexpected_timezone_rows,

        SUM(
            CASE
                WHEN weather_date_local < DATE '2026-03-01'
                  OR weather_date_local > DATE '2026-05-31'
                THEN 1 ELSE 0
            END
        ) AS outside_analysis_period_rows,

        SUM(
            CASE
                WHEN weather_date_local
                     <> CAST(weather_hour_local AS DATE)
                THEN 1 ELSE 0
            END
        ) AS date_timestamp_mismatch_rows,

        SUM(
            CASE
                WHEN ingested_at < weather_hour_local
                THEN 1 ELSE 0
            END
        ) AS invalid_ingestion_timestamp_rows,

        MIN(weather_hour_local)
            AS first_weather_hour,

        MAX(weather_hour_local)
            AS last_weather_hour,

        COUNT(DISTINCT source_file)
            AS source_file_count

    FROM base
),

monthly AS (
    SELECT
        SUM(
            CASE
                WHEN DATE_FORMAT(
                    weather_hour_local,
                    'yyyy-MM'
                ) = '2026-03'
                THEN 1 ELSE 0
            END
        ) AS march_rows,

        SUM(
            CASE
                WHEN DATE_FORMAT(
                    weather_hour_local,
                    'yyyy-MM'
                ) = '2026-04'
                THEN 1 ELSE 0
            END
        ) AS april_rows,

        SUM(
            CASE
                WHEN DATE_FORMAT(
                    weather_hour_local,
                    'yyyy-MM'
                ) = '2026-05'
                THEN 1 ELSE 0
            END
        ) AS may_rows

    FROM base
),

source_overlap AS (
    SELECT
        COUNT(*) AS overlapping_weather_hours

    FROM (
        SELECT
            weather_hour_local

        FROM base

        GROUP BY weather_hour_local

        HAVING COUNT(DISTINCT source_file) > 1
    )
),

hourly_gaps AS (
    SELECT
        COUNT(*) AS unexpected_hour_gaps

    FROM (
        SELECT
            weather_hour_local,

            LAG(weather_hour_local) OVER (
                ORDER BY weather_hour_local
            ) AS previous_weather_hour

        FROM base
    )

    WHERE previous_weather_hour IS NOT NULL

      AND TIMESTAMPDIFF(
            MINUTE,
            previous_weather_hour,
            weather_hour_local
          ) <> 60
)

SELECT
    s.total_rows,
    s.unique_weather_hours,
    s.duplicate_hour_rows,

    s.weather_hour_nulls,
    s.weather_date_nulls,
    s.timezone_nulls,
    s.source_file_nulls,
    s.ingested_at_nulls,

    s.temperature_nulls,
    s.precipitation_nulls,
    s.wind_speed_nulls,

    s.negative_precipitation_rows,
    s.negative_wind_rows,

    s.suspicious_temperature_rows,
    s.suspicious_wind_rows,

    s.unexpected_timezone_rows,
    s.outside_analysis_period_rows,
    s.date_timestamp_mismatch_rows,
    s.invalid_ingestion_timestamp_rows,

    m.march_rows,
    m.april_rows,
    m.may_rows,

    o.overlapping_weather_hours,

    g.unexpected_hour_gaps,

    s.first_weather_hour,
    s.last_weather_hour,
    s.source_file_count,

    CASE
        WHEN s.total_rows = 2208
         AND s.unique_weather_hours = 2208
         AND s.duplicate_hour_rows = 0

         AND s.weather_hour_nulls = 0
         AND s.weather_date_nulls = 0
         AND s.timezone_nulls = 0
         AND s.source_file_nulls = 0
         AND s.ingested_at_nulls = 0

         AND s.temperature_nulls = 0
         AND s.precipitation_nulls = 0
         AND s.wind_speed_nulls = 0

         AND s.negative_precipitation_rows = 0
         AND s.negative_wind_rows = 0

         AND s.unexpected_timezone_rows = 0
         AND s.outside_analysis_period_rows = 0
         AND s.date_timestamp_mismatch_rows = 0
         AND s.invalid_ingestion_timestamp_rows = 0

         AND m.march_rows = 744
         AND m.april_rows = 720
         AND m.may_rows = 744

         AND o.overlapping_weather_hours = 0

         AND s.source_file_count = 3

        THEN 'PASS'
        ELSE 'FAIL'
    END AS overall_validation_status

FROM summary s

CROSS JOIN monthly m
CROSS JOIN source_overlap o
CROSS JOIN hourly_gaps g;