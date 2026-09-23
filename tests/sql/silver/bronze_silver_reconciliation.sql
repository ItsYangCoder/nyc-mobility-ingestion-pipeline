-- Source-aware Bronze-to-Silver reconciliation. Every row must return PASS.
-- Weather is compared at its actual Silver grain: exploded hourly positions,
-- followed by the latest-row-per-hour selection. Taxi Zones compares the latest
-- snapshot after its one-row-per-canonical-key reduction.

WITH weather_exploded AS (
    SELECT
        CAST(weather.time AS TIMESTAMP) AS weather_hour_local,
        _source_file,
        _source_file_modified_at,
        _ingested_at,
        source_position
    FROM nyc_mobility.nyc_bronze.bronze_weather_raw
    LATERAL VIEW posexplode_outer(
        arrays_zip(
            hourly.time,
            hourly.temperature_2m,
            hourly.precipitation,
            hourly.wind_speed_10m
        )
    ) exploded AS source_position, weather
),
weather_latest AS (
    SELECT weather_hour_local
    FROM (
        SELECT
            weather_hour_local,
            ROW_NUMBER() OVER (
                PARTITION BY weather_hour_local
                ORDER BY
                    _source_file_modified_at DESC NULLS LAST,
                    _ingested_at DESC NULLS LAST,
                    _source_file DESC NULLS LAST,
                    source_position DESC NULLS LAST
            ) AS row_rank
        FROM weather_exploded
    )
    WHERE row_rank = 1
),
latest_zone_snapshot AS (
    SELECT CAST(LocationID AS INT) AS location_id
    FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
    WHERE _ingested_at = (
        SELECT MAX(_ingested_at)
        FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
    )
),
expected AS (
    SELECT 'green_taxi' AS source, COUNT(*) AS expected_rows
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
    UNION ALL
    SELECT 'weather', COUNT(*)
    FROM weather_latest
    UNION ALL
    SELECT 'taxi_zones', COUNT(*)
    FROM (SELECT location_id FROM latest_zone_snapshot GROUP BY location_id)
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
