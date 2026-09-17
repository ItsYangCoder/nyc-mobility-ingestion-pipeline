-- Taxi Zones Silver validation
-- Run only AFTER the ETL Pipeline Job creates/updates silver_taxi_zones.


-- Latest Taxi Zones ingestion snapshot only.
WITH latest_bronze AS (
    SELECT *
    FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
    WHERE _ingested_at = (
        SELECT MAX(_ingested_at)
        FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
    )
),

bronze AS (
    SELECT
        COUNT(*) AS bronze_rows,
        COUNT(DISTINCT LocationID) AS bronze_distinct_location_ids,

        SUM(
            CASE
                WHEN LocationID IS NULL
                THEN 1 ELSE 0
            END
        ) AS bronze_null_location_ids,

        SUM(
            CASE
                WHEN LocationID <= 0
                THEN 1 ELSE 0
            END
        ) AS bronze_invalid_location_ids

    FROM latest_bronze
),

silver AS (
    SELECT
        COUNT(*) AS silver_rows,
        COUNT(DISTINCT location_id) AS silver_distinct_location_ids,

        SUM(
            CASE
                WHEN location_id IS NULL
                THEN 1 ELSE 0
            END
        ) AS null_location_ids,

        SUM(
            CASE
                WHEN location_id <= 0
                THEN 1 ELSE 0
            END
        ) AS invalid_location_ids,

        SUM(
            CASE
                WHEN borough IS NULL
                  OR TRIM(borough) = ''
                THEN 1 ELSE 0
            END
        ) AS missing_borough,

        SUM(
            CASE
                WHEN zone IS NULL
                  OR TRIM(zone) = ''
                THEN 1 ELSE 0
            END
        ) AS missing_zone,

        SUM(
            CASE
                WHEN service_zone IS NULL
                  OR TRIM(service_zone) = ''
                THEN 1 ELSE 0
            END
        ) AS missing_service_zone,

        SUM(
            CASE
                WHEN borough != TRIM(
                    REGEXP_REPLACE(
                        borough,
                        r'\s+',
                        ' '
                    )
                )
                THEN 1 ELSE 0
            END
        ) AS unstandardized_borough,

        SUM(
            CASE
                WHEN zone != TRIM(
                    REGEXP_REPLACE(
                        zone,
                        r'\s+',
                        ' '
                    )
                )
                THEN 1 ELSE 0
            END
        ) AS unstandardized_zone,

        SUM(
            CASE
                WHEN service_zone != TRIM(
                    REGEXP_REPLACE(
                        service_zone,
                        r'\s+',
                        ' '
                    )
                )
                THEN 1 ELSE 0
            END
        ) AS unstandardized_service_zone,

        SUM(
            CASE
                WHEN has_conflicting_values
                THEN 1 ELSE 0
            END
        ) AS conflicting_location_ids,

        SUM(
            CASE
                WHEN has_duplicate_key
                THEN 1 ELSE 0
            END
        ) AS documented_duplicate_keys,

        SUM(
            CASE
                WHEN had_control_char
                THEN 1 ELSE 0
            END
        ) AS control_char_review_rows,

        SUM(
            CASE
                WHEN _source_file IS NULL
                  OR _ingested_at IS NULL
                THEN 1 ELSE 0
            END
        ) AS missing_lineage_rows,

        SUM(
            CASE
                WHEN location_id IN (264, 265)
                THEN 1 ELSE 0
            END
        ) AS special_members_present

    FROM nyc_mobility.nyc_silver.silver_taxi_zones
),

-- Distinct pickup/dropoff LocationIDs actually used by Green Taxi.
taxi_location_ids AS (
    SELECT DISTINCT
        PULocationID AS location_id
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw

    UNION

    SELECT DISTINCT
        DOLocationID AS location_id
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
),

referential_integrity AS (
    SELECT
        COUNT(*) AS unmatched_taxi_location_ids
    FROM taxi_location_ids t

    LEFT ANTI JOIN
        nyc_mobility.nyc_silver.silver_taxi_zones z
        ON t.location_id = z.location_id
)

SELECT
    bronze.*,
    silver.*,
    referential_integrity.*,

    CASE
        WHEN bronze_rows = 265
         AND silver_rows = 265
        THEN 'PASS'
        ELSE 'FAIL'
    END AS current_265_row_baseline_check,

    CASE
        WHEN silver_rows = silver_distinct_location_ids
        THEN 'PASS'
        ELSE 'FAIL'
    END AS unique_location_id_check,

    CASE
        WHEN null_location_ids = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS non_null_location_id_check,

    CASE
        WHEN invalid_location_ids = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS location_id_range_check,

    CASE
        WHEN missing_borough = 0
         AND missing_zone = 0
         AND missing_service_zone = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS required_text_check,

    CASE
        WHEN unstandardized_borough = 0
         AND unstandardized_zone = 0
         AND unstandardized_service_zone = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS text_standardization_check,

    CASE
        WHEN conflicting_location_ids = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS conflicting_values_check,

    CASE
        WHEN documented_duplicate_keys = 0
        THEN 'PASS'
        ELSE 'REVIEW'
    END AS duplicate_key_check,

    CASE
        WHEN control_char_review_rows = 0
        THEN 'PASS'
        ELSE 'REVIEW'
    END AS control_character_check,

    CASE
        WHEN missing_lineage_rows = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS lineage_check,

    CASE
        WHEN special_members_present = 2
        THEN 'PASS'
        ELSE 'FAIL'
    END AS special_members_264_265_check,

    CASE
        WHEN silver_rows = bronze_distinct_location_ids
        THEN 'PASS'
        ELSE 'FAIL'
    END AS bronze_silver_reconciliation,

    CASE
        WHEN unmatched_taxi_location_ids = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS pickup_dropoff_zone_compatibility_check

FROM bronze
CROSS JOIN silver
CROSS JOIN referential_integrity;