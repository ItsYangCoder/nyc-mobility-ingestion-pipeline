-- PENDING: Enable after Gold tables are implemented
-- Silver → Gold measure reconciliation
-- Validates that key measures are preserved from Silver to Gold
-- Expected: Sum of measures should match (or be documented if filtered)

WITH silver_measures AS (
  SELECT 
    COUNT(*) AS total_rows,
    SUM(fare_amount) AS total_fare,
    SUM(total_amount) AS total_amount,
    SUM(trip_distance) AS total_distance
  FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
  -- Add WHERE clause for eligible records if Silver has filtering logic
),
gold_measures AS (
  SELECT 
    COUNT(*) AS total_rows,
    SUM(fare_amount) AS total_fare,
    SUM(total_amount) AS total_amount,
    SUM(trip_distance) AS total_distance
  FROM nyc_mobility.nyc_gold.fact_taxi_trip
)
SELECT 
  'taxi' AS source,
  s.total_rows AS silver_rows,
  g.total_rows AS gold_rows,
  s.total_fare AS silver_fare_sum,
  g.total_fare AS gold_fare_sum,
  s.total_amount AS silver_total_sum,
  g.total_amount AS gold_total_sum,
  s.total_distance AS silver_distance_sum,
  g.total_distance AS gold_distance_sum,
  s.total_fare - g.total_fare AS fare_difference,
  s.total_amount - g.total_amount AS total_difference,
  s.total_distance - g.total_distance AS distance_difference
FROM silver_measures s
CROSS JOIN gold_measures g;
