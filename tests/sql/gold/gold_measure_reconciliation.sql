-- Eligible Silver-to-Gold taxi measure reconciliation. Result must return PASS.
-- Gold stores fare and total as DECIMAL(12,2), so expected Silver measures use
-- the same rounding before aggregate comparison. Null measures remain NULL.

WITH eligible_silver AS (
    SELECT COUNT(*) AS row_count,
           SUM(CAST(CAST(fare_amount AS DECIMAL(12, 2)) AS DECIMAL(20, 4)))
               AS fare_amount,
           SUM(CAST(CAST(total_amount AS DECIMAL(12, 2)) AS DECIMAL(20, 4)))
               AS total_amount,
           SUM(CAST(trip_distance AS DECIMAL(20, 4))) AS trip_distance
    FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
    WHERE is_in_analysis_window
      AND pickup_ts_local IS NOT NULL
      AND dropoff_ts_local IS NOT NULL
      AND pu_location_id IS NOT NULL
      AND do_location_id IS NOT NULL
),
gold AS (
    SELECT COUNT(*) AS row_count,
           SUM(CAST(fare_amount AS DECIMAL(20, 4))) AS fare_amount,
           SUM(CAST(total_amount AS DECIMAL(20, 4))) AS total_amount,
           SUM(CAST(trip_distance AS DECIMAL(20, 4))) AS trip_distance
    FROM nyc_mobility.nyc_gold.fact_taxi_trip
)
SELECT s.row_count AS eligible_silver_rows, g.row_count AS gold_rows,
       g.fare_amount - s.fare_amount AS fare_difference,
       g.total_amount - s.total_amount AS total_difference,
       g.trip_distance - s.trip_distance AS distance_difference,
       CASE WHEN s.row_count = g.row_count
                 AND g.fare_amount <=> s.fare_amount
                 AND g.total_amount <=> s.total_amount
                 AND g.trip_distance <=> s.trip_distance
            THEN 'PASS' ELSE 'FAIL' END AS status
FROM eligible_silver s CROSS JOIN gold g;
