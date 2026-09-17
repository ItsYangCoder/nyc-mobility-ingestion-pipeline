-- Silver taxi-to-zone referential integrity. Every row must return PASS.

WITH checks AS (
    SELECT 'pickup_location' AS check_name, COUNT(*) AS orphan_keys
    FROM (
        SELECT DISTINCT pu_location_id
        FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
        WHERE pu_location_id IS NOT NULL
    ) t
    LEFT ANTI JOIN nyc_mobility.nyc_silver.silver_taxi_zones z
        ON t.pu_location_id = z.location_id
    UNION ALL
    SELECT 'dropoff_location', COUNT(*)
    FROM (
        SELECT DISTINCT do_location_id
        FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
        WHERE do_location_id IS NOT NULL
    ) t
    LEFT ANTI JOIN nyc_mobility.nyc_silver.silver_taxi_zones z
        ON t.do_location_id = z.location_id
)
SELECT check_name, orphan_keys,
       CASE WHEN orphan_keys = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks
ORDER BY check_name;
