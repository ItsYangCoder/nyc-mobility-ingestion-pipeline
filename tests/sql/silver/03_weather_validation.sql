-- Weather positional alignment, hourly grain, units, coverage, and lineage.
-- The final result must return PASS before promotion.

WITH bronze AS (
    SELECT
        SUM(SIZE(hourly.time)) AS expected_hourly_rows,
        COUNT_IF(
            SIZE(hourly.time) != SIZE(hourly.temperature_2m)
            OR SIZE(hourly.time) != SIZE(hourly.precipitation)
            OR SIZE(hourly.time) != SIZE(hourly.wind_speed_10m)
        ) AS misaligned_source_responses
    FROM nyc_mobility.nyc_bronze.bronze_weather_raw
),
silver AS (
    SELECT
        COUNT(*) AS actual_hourly_rows,
        COUNT(DISTINCT weather_hour_local) AS distinct_hours,
        COUNT_IF(weather_hour_local IS NULL) AS null_hours,
        COUNT_IF(NOT array_lengths_aligned) AS unaligned_rows,
        COUNT_IF(timezone != 'America/New_York') AS unexpected_timezone_rows,
        COUNT_IF(temperature_unit != '°C') AS unexpected_temperature_units,
        COUNT_IF(precipitation_unit != 'mm') AS unexpected_precipitation_units,
        COUNT_IF(wind_speed_unit != 'km/h') AS unexpected_wind_speed_units,
        COUNT_IF(precipitation_mm < 0) AS negative_precipitation_rows,
        COUNT_IF(wind_speed_10m_kmh < 0) AS negative_wind_speed_rows,
        COUNT_IF(
            source_file IS NULL
            OR source_file_modified_at IS NULL
            OR ingested_at IS NULL
            OR silver_processed_at IS NULL
        ) AS missing_lineage_rows,
        COUNT_IF(is_in_analysis_window) AS in_window_hours
    FROM nyc_mobility.nyc_silver.silver_weather_hourly
)
SELECT
    b.expected_hourly_rows,
    s.actual_hourly_rows,
    s.distinct_hours,
    s.in_window_hours,
    b.misaligned_source_responses,
    s.unaligned_rows,
    s.missing_lineage_rows,
    CASE
        WHEN b.expected_hourly_rows = s.actual_hourly_rows
            AND s.actual_hourly_rows = s.distinct_hours
            AND s.in_window_hours = 2208
            AND b.misaligned_source_responses = 0
            AND s.null_hours = 0
            AND s.unaligned_rows = 0
            AND s.unexpected_timezone_rows = 0
            AND s.unexpected_temperature_units = 0
            AND s.unexpected_precipitation_units = 0
            AND s.unexpected_wind_speed_units = 0
            AND s.negative_precipitation_rows = 0
            AND s.negative_wind_speed_rows = 0
            AND s.missing_lineage_rows = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM bronze b
CROSS JOIN silver s;
