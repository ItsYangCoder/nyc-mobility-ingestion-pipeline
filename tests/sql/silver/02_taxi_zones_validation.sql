-- Purpose: validate the latest Taxi Zones snapshot and Silver output.
-- Safety: read-only; this query does not create or refresh pipeline objects.

WITH config AS (
    SELECT
        265 AS expected_zone_count,
        264 AS unknown_zone_id,
        265 AS outside_zone_id
),
bronze AS (
    SELECT
        COUNT(*) AS bronze_rows,
        COUNT(DISTINCT LocationID) AS bronze_distinct_location_ids,
        COUNT_IF(LocationID IS NULL) AS bronze_null_location_ids,
        COUNT_IF(LocationID <= 0) AS bronze_invalid_location_ids
    FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
    WHERE _ingested_at = (
        SELECT MAX(_ingested_at)
        FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
    )
),
silver AS (
    SELECT
        COUNT(*) AS silver_rows,
        COUNT(DISTINCT location_id) AS silver_distinct_location_ids,
        COUNT_IF(location_id IS NULL) AS null_location_ids,
        COUNT_IF(location_id <= 0) AS invalid_location_ids,
        COUNT_IF(borough IS NULL OR TRIM(borough) = '') AS missing_borough,
        COUNT_IF(zone IS NULL OR TRIM(zone) = '') AS missing_zone,
        COUNT_IF(service_zone IS NULL OR TRIM(service_zone) = '')
            AS missing_service_zone,
        COUNT_IF(
            borough != TRIM(REGEXP_REPLACE(borough, r'\s+', ' '))
        ) AS unstandardized_borough,
        COUNT_IF(
            zone != TRIM(REGEXP_REPLACE(zone, r'\s+', ' '))
        ) AS unstandardized_zone,
        COUNT_IF(
            service_zone != TRIM(
                REGEXP_REPLACE(service_zone, r'\s+', ' ')
            )
        ) AS unstandardized_service_zone,
        COUNT_IF(has_conflicting_values) AS conflicting_location_ids,
        COUNT_IF(has_duplicate_key) AS documented_duplicate_keys,
        COUNT_IF(had_control_char) AS control_char_review_rows,
        COUNT_IF(
            _source_file IS NULL
            OR _source_file_modified_at IS NULL
            OR _ingested_at IS NULL
            OR silver_processed_at IS NULL
        ) AS missing_lineage_rows,
        COUNT_IF(
            location_id IN (c.unknown_zone_id, c.outside_zone_id)
        ) AS special_members_present
    FROM nyc_mobility.nyc_silver.silver_taxi_zones
    CROSS JOIN config c
),
used_zone_ids AS (
    SELECT PULocationID AS location_id
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
    WHERE PULocationID IS NOT NULL

    UNION

    SELECT DOLocationID AS location_id
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
    WHERE DOLocationID IS NOT NULL
),
referential_integrity AS (
    SELECT COUNT(*) AS unmatched_taxi_location_ids
    FROM used_zone_ids t
    LEFT ANTI JOIN nyc_mobility.nyc_silver.silver_taxi_zones z
        ON t.location_id = z.location_id
)
SELECT
    b.bronze_rows,
    s.silver_rows,
    s.silver_distinct_location_ids,
    s.documented_duplicate_keys,
    s.control_char_review_rows,
    r.unmatched_taxi_location_ids,
    CASE
        WHEN b.bronze_rows = c.expected_zone_count
            AND s.silver_rows = c.expected_zone_count
        THEN 'PASS' ELSE 'FAIL'
    END AS row_baseline_check,
    CASE
        WHEN b.bronze_null_location_ids = 0
            AND b.bronze_invalid_location_ids = 0
            AND s.null_location_ids = 0
            AND s.invalid_location_ids = 0
            AND s.silver_rows = s.silver_distinct_location_ids
        THEN 'PASS' ELSE 'FAIL'
    END AS key_integrity_check,
    CASE
        WHEN s.missing_borough
            + s.missing_zone
            + s.missing_service_zone
            + s.unstandardized_borough
            + s.unstandardized_zone
            + s.unstandardized_service_zone = 0
        THEN 'PASS' ELSE 'FAIL'
    END AS text_quality_check,
    CASE
        WHEN s.conflicting_location_ids = 0
            AND s.missing_lineage_rows = 0
            AND s.special_members_present = 2
            AND s.silver_rows = b.bronze_distinct_location_ids
            AND r.unmatched_taxi_location_ids = 0
        THEN 'PASS' ELSE 'FAIL'
    END AS reconciliation_check,
    CASE
        WHEN b.bronze_rows = c.expected_zone_count
            AND s.silver_rows = c.expected_zone_count
            AND b.bronze_null_location_ids = 0
            AND b.bronze_invalid_location_ids = 0
            AND s.null_location_ids = 0
            AND s.invalid_location_ids = 0
            AND s.silver_rows = s.silver_distinct_location_ids
            AND s.missing_borough
                + s.missing_zone
                + s.missing_service_zone
                + s.unstandardized_borough
                + s.unstandardized_zone
                + s.unstandardized_service_zone = 0
            AND s.conflicting_location_ids = 0
            AND s.missing_lineage_rows = 0
            AND s.special_members_present = 2
            AND s.silver_rows = b.bronze_distinct_location_ids
            AND r.unmatched_taxi_location_ids = 0
        THEN 'PASS' ELSE 'FAIL'
    END AS overall_status
FROM bronze b
CROSS JOIN silver s
CROSS JOIN referential_integrity r
CROSS JOIN config c;
