-- Green Taxi Silver validation
-- Target: nyc_mobility.nyc_silver.silver_green_taxi_trips


-- 1. Row reconciliation: Bronze vs Silver

SELECT
    (SELECT COUNT(*) FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw) AS bronze_rows,
    (SELECT COUNT(*) FROM nyc_mobility.nyc_silver.silver_green_taxi_trips) AS silver_rows;


-- 2. Trip key uniqueness and null checks

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT trip_key) AS distinct_trip_keys,
    SUM(CASE WHEN trip_key IS NULL THEN 1 ELSE 0 END) AS null_trip_keys
FROM nyc_mobility.nyc_silver.silver_green_taxi_trips;


-- 3. Quality and required-field validation

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT trip_key) AS distinct_trip_keys,
    SUM(CASE WHEN trip_key IS NULL THEN 1 ELSE 0 END) AS null_trip_keys,
    SUM(CASE WHEN is_candidate_duplicate THEN 1 ELSE 0 END) AS candidate_duplicate_rows,
    SUM(CASE WHEN NOT is_in_analysis_window THEN 1 ELSE 0 END) AS outside_analysis_window,
    SUM(CASE WHEN NOT is_valid_duration THEN 1 ELSE 0 END) AS negative_duration_rows,
    SUM(CASE WHEN is_zero_duration THEN 1 ELSE 0 END) AS zero_duration_rows,
    SUM(CASE WHEN NOT is_valid_distance THEN 1 ELSE 0 END) AS negative_distance_rows,
    SUM(CASE WHEN NOT is_valid_fare THEN 1 ELSE 0 END) AS negative_fare_rows,
    SUM(CASE WHEN NOT is_valid_total THEN 1 ELSE 0 END) AS negative_total_rows,
    SUM(CASE WHEN pickup_ts_local IS NULL THEN 1 ELSE 0 END) AS null_pickup_ts,
    SUM(CASE WHEN dropoff_ts_local IS NULL THEN 1 ELSE 0 END) AS null_dropoff_ts,
    SUM(CASE WHEN pu_location_id IS NULL THEN 1 ELSE 0 END) AS null_pickup_zone,
    SUM(CASE WHEN do_location_id IS NULL THEN 1 ELSE 0 END) AS null_dropoff_zone,
    SUM(CASE WHEN source_file IS NULL THEN 1 ELSE 0 END) AS null_source_file,
    SUM(
        CASE WHEN source_file_modified_at IS NULL THEN 1 ELSE 0 END
    ) AS null_source_file_modified_at,
    SUM(CASE WHEN ingested_at IS NULL THEN 1 ELSE 0 END) AS null_ingested_at,
    SUM(
        CASE WHEN silver_processed_at IS NULL THEN 1 ELSE 0 END
    ) AS null_silver_processed_at
FROM nyc_mobility.nyc_silver.silver_green_taxi_trips;


-- 4. Candidate duplicate-group validation

SELECT
    COUNT(*) AS candidate_duplicate_groups,
    SUM(candidate_group_size) AS rows_in_duplicate_groups,
    MAX(candidate_group_size) AS max_group_size
FROM (
    SELECT
        vendor_id,
        pickup_ts_local,
        dropoff_ts_local,
        pu_location_id,
        do_location_id,
        MAX(candidate_group_size) AS candidate_group_size
    FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
    WHERE is_candidate_duplicate = true
    GROUP BY vendor_id, pickup_ts_local, dropoff_ts_local, pu_location_id, do_location_id
);


-- 5. Date coverage

SELECT
    MIN(pickup_ts_local) AS earliest_pickup,
    MAX(pickup_ts_local) AS latest_pickup,
    MIN(dropoff_ts_local) AS earliest_dropoff,
    MAX(dropoff_ts_local) AS latest_dropoff
FROM nyc_mobility.nyc_silver.silver_green_taxi_trips;


-- 6. Monthly reconciliation for March-May 2026

SELECT
    DATE_FORMAT(pickup_date_local, 'yyyy-MM') AS pickup_month,
    COUNT(*) AS rows,
    COUNT(DISTINCT trip_key) AS distinct_trip_keys
FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
WHERE pickup_date_local BETWEEN DATE '2026-03-01' AND DATE '2026-05-31'
GROUP BY DATE_FORMAT(pickup_date_local, 'yyyy-MM')
ORDER BY pickup_month;


-- 7. Schema inspection
-- Expected:
-- trip_key = bigint
-- pickup_ts_local = timestamp_ntz
-- dropoff_ts_local = timestamp_ntz
-- pickup_hour_local = timestamp_ntz

DESCRIBE TABLE nyc_mobility.nyc_silver.silver_green_taxi_trips;

-- 8. Final acceptance summary
-- Every required structural check must return PASS before promotion.

WITH metrics AS (
    SELECT
        COUNT(*) AS silver_rows,
        COUNT(DISTINCT trip_key) AS distinct_trip_keys,
        COUNT_IF(trip_key IS NULL) AS null_trip_keys,
        COUNT_IF(
            pickup_ts_local IS NULL
            OR dropoff_ts_local IS NULL
            OR pu_location_id IS NULL
            OR do_location_id IS NULL
            OR source_file IS NULL
            OR source_file_modified_at IS NULL
            OR ingested_at IS NULL
            OR silver_processed_at IS NULL
        ) AS missing_required_rows,
        COUNT(DISTINCT CASE
            WHEN pickup_date_local BETWEEN DATE '2026-03-01'
                AND DATE '2026-05-31'
            THEN DATE_FORMAT(pickup_date_local, 'yyyy-MM')
        END) AS covered_months
    FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
),
bronze AS (
    SELECT COUNT(*) AS bronze_rows
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
)
SELECT
    CASE WHEN b.bronze_rows = m.silver_rows
        THEN 'PASS' ELSE 'FAIL' END AS row_reconciliation,
    CASE WHEN m.silver_rows = m.distinct_trip_keys
            AND m.null_trip_keys = 0
        THEN 'PASS' ELSE 'FAIL' END AS trip_key_check,
    CASE WHEN m.missing_required_rows = 0
        THEN 'PASS' ELSE 'FAIL' END AS required_fields_check,
    CASE WHEN m.covered_months = 3
        THEN 'PASS' ELSE 'FAIL' END AS march_to_may_coverage,
    CASE WHEN
        b.bronze_rows = m.silver_rows
        AND m.silver_rows = m.distinct_trip_keys
        AND m.null_trip_keys = 0
        AND m.missing_required_rows = 0
        AND m.covered_months = 3
        THEN 'PASS'
        ELSE 'FAIL'
    END AS overall_status
FROM bronze b
CROSS JOIN metrics m;
