-- PENDING: Enable after Gold tables are implemented
-- Silver → Gold row-count reconciliation
-- Validates that Gold fact tables reconcile to eligible Silver records

WITH silver_taxi AS (
  SELECT COUNT(*) AS silver_count
  FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
  -- Add WHERE clause for eligible records if Silver has filtering logic
),
gold_taxi AS (
  SELECT COUNT(*) AS gold_count
  FROM nyc_mobility.nyc_gold.fact_taxi_trip
),
silver_weather AS (
  SELECT COUNT(*) AS silver_count
  FROM nyc_mobility.nyc_silver.silver_weather_hourly
),
gold_weather AS (
  SELECT COUNT(*) AS gold_count
  FROM nyc_mobility.nyc_gold.fact_weather_hourly
)
SELECT 
  'taxi' AS fact,
  s.silver_count AS silver_rows,
  g.gold_count AS gold_rows,
  s.silver_count - g.gold_count AS difference,
  CASE 
    WHEN s.silver_count = g.gold_count THEN 'MATCH'
    ELSE 'REVIEW - Document exclusion logic'
  END AS status
FROM silver_taxi s, gold_taxi g
UNION ALL
SELECT 
  'weather' AS fact,
  s.silver_count AS silver_rows,
  g.gold_count AS gold_rows,
  s.silver_count - g.gold_count AS difference,
  CASE 
    WHEN s.silver_count = g.gold_count THEN 'MATCH'
    ELSE 'REVIEW - Document exclusion logic'
  END AS status
FROM silver_weather s, gold_weather g;
