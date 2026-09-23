-- Bronze-to-Silver taxi measure reconciliation. Result must return PASS.
-- Both sides retain every source trip. Casting to DECIMAL(20, 4) makes decimal
-- comparison and null treatment explicit: SUM is NULL only when all values in
-- the compared population are NULL.

WITH bronze AS (
    SELECT COUNT(*) AS row_count,
           SUM(CAST(fare_amount AS DECIMAL(20, 4))) AS fare_amount,
           SUM(CAST(total_amount AS DECIMAL(20, 4))) AS total_amount,
           SUM(CAST(trip_distance AS DECIMAL(20, 4))) AS trip_distance
    FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
),
silver AS (
    SELECT COUNT(*) AS row_count,
           SUM(CAST(fare_amount AS DECIMAL(20, 4))) AS fare_amount,
           SUM(CAST(total_amount AS DECIMAL(20, 4))) AS total_amount,
           SUM(CAST(trip_distance AS DECIMAL(20, 4))) AS trip_distance
    FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
)
SELECT b.row_count AS bronze_rows, s.row_count AS silver_rows,
       s.fare_amount - b.fare_amount AS fare_difference,
       s.total_amount - b.total_amount AS total_difference,
       s.trip_distance - b.trip_distance AS distance_difference,
       CASE WHEN b.row_count = s.row_count
                 AND s.fare_amount <=> b.fare_amount
                 AND s.total_amount <=> b.total_amount
                 AND s.trip_distance <=> b.trip_distance
            THEN 'PASS' ELSE 'FAIL' END AS status
FROM bronze b CROSS JOIN silver s;
