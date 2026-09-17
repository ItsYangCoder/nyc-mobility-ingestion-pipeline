-- PENDING: Enable after Gold tables are implemented
-- Taxi → Weather join cardinality check
-- Validates that the weather join does NOT multiply taxi trip rows
-- Expected: Row count should remain unchanged after left join

WITH taxi_before_join AS (
  SELECT COUNT(*) AS taxi_count
  FROM nyc_mobility.nyc_gold.fact_taxi_trip
),
taxi_after_join AS (
  SELECT COUNT(*) AS taxi_count
  FROM nyc_mobility.nyc_gold.fact_taxi_trip t
  LEFT JOIN nyc_mobility.nyc_gold.fact_weather_hourly w
    ON t.pickup_weather_hour_key = w.weather_hour_key
)
SELECT 
  'taxi_weather_join' AS check_type,
  b.taxi_count AS rows_before_join,
  a.taxi_count AS rows_after_join,
  a.taxi_count - b.taxi_count AS row_difference,
  CASE 
    WHEN b.taxi_count = a.taxi_count THEN 'PASS - No row multiplication'
    ELSE 'FAIL - Weather join multiplied rows'
  END AS status
FROM taxi_before_join b, taxi_after_join a;
