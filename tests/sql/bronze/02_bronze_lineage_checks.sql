-- Purpose: verify required Bronze lineage fields.
-- Pass condition: both missing counts equal zero for every source.

WITH lineage AS (
    SELECT
        'green_taxi' AS source,
        COUNT_IF(_source_file IS NULL) AS missing_source_file,
        COUNT_IF(_source_file_modified_at IS NULL)
            AS missing_source_file_modified_at,
        COUNT_IF(_ingested_at IS NULL) AS missing_ingested_at
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw

    UNION ALL

    SELECT
        'weather' AS source,
        COUNT_IF(_source_file IS NULL) AS missing_source_file,
        COUNT_IF(_source_file_modified_at IS NULL)
            AS missing_source_file_modified_at,
        COUNT_IF(_ingested_at IS NULL) AS missing_ingested_at
    FROM nyc_mobility.nyc_bronze.bronze_weather_raw

    UNION ALL

    SELECT
        'taxi_zones' AS source,
        COUNT_IF(_source_file IS NULL) AS missing_source_file,
        COUNT_IF(_source_file_modified_at IS NULL)
            AS missing_source_file_modified_at,
        COUNT_IF(_ingested_at IS NULL) AS missing_ingested_at
    FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
)
SELECT
    source,
    missing_source_file,
    missing_source_file_modified_at,
    missing_ingested_at,
    CASE
        WHEN missing_source_file = 0
            AND missing_source_file_modified_at = 0
            AND missing_ingested_at = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM lineage
ORDER BY source;
