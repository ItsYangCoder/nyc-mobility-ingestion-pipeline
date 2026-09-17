-- PENDING: Enable after silver_green_taxi_trips is implemented
-- Bronze → Silver measure reconciliation
-- Validates that key measures are preserved from Bronze to Silver
-- Expected: Sum of measures should match (or be documented if filtered)

WITH bronze_measures AS (
  SELECT 
    COUNT(*) AS total_rows,
    SUM(fare_amount) AS total_fare,
    SUM(total_amount) AS total_amount,
    SUM(trip_distance) AS total_distance,
    SUM(CASE WHEN fare_amount < 0 THEN 1 ELSE 0 END) AS negative_fare_count,
    SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) AS negative_total_count,
    SUM(CASE WHEN trip_distance < 0 THEN 1 ELSE 0 END) AS negative_distance_count
  FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
),
silver_measures AS (
  SELECT 
    COUNT(*) AS total_rows,
    SUM(fare_amount) AS total_fare,
    SUM(total_amount) AS total_amount,
    SUM(trip_distance) AS total_distance,
    SUM(CASE WHEN fare_amount < 0 THEN 1 ELSE 0 END) AS negative_fare_count,
    SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) AS negative_total_count,
    SUM(CASE WHEN trip_distance < 0 THEN 1 ELSE 0 END) AS negative_distance_count
  FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
)
SELECT 
  'green_taxi' AS source,
  b.total_rows AS bronze_rows,
  s.total_rows AS silver_rows,
  b.total_fare AS bronze_fare_sum,
  s.total_fare AS silver_fare_sum,
  b.total_amount AS bronze_total_sum,
  s.total_amount AS silver_total_sum,
  b.total_distance AS bronze_distance_sum,
  s.total_distance AS silver_distance_sum,
  b.negative_fare_count AS bronze_negative_fare,
  s.negative_fare_count AS silver_negative_fare,
  b.negative_total_count AS bronze_negative_total,
  s.negative_total_count AS silver_negative_total,
  b.negative_distance_count AS bronze_negative_distance,
  s.negative_distance_count AS silver_negative_distance
FROM bronze_measures b
CROSS JOIN silver_measures s;
