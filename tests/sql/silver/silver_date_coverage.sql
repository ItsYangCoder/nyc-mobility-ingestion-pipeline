-- PENDING: Enable after silver_green_taxi_trips is implemented
-- Silver date coverage validation
-- Validates that Silver covers the expected March-May 2026 period
-- Expected: 92 days (31 March + 30 April + 31 May)

WITH taxi_dates AS (
  SELECT 
    DATE(pickup_datetime) AS pickup_date,
    COUNT(*) AS trip_count
  FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
  WHERE pickup_datetime >= DATE('2026-03-01') 
    AND pickup_datetime < DATE('2026-06-01')
  GROUP BY DATE(pickup_datetime)
),
weather_dates AS (
  SELECT 
    DATE(weather_timestamp) AS weather_date,
    COUNT(*) AS hour_count
  FROM nyc_mobility.nyc_silver.silver_weather_hourly
  WHERE weather_timestamp >= DATE('2026-03-01') 
    AND weather_timestamp < DATE('2026-06-01')
  GROUP BY DATE(weather_timestamp)
)
SELECT 
  'taxi' AS source,
  COUNT(DISTINCT pickup_date) AS distinct_dates,
  MIN(pickup_date) AS min_date,
  MAX(pickup_date) AS max_date,
  92 AS expected_dates,
  92 - COUNT(DISTINCT pickup_date) AS missing_dates
FROM taxi_dates
UNION ALL
SELECT 
  'weather' AS source,
  COUNT(DISTINCT weather_date) AS distinct_dates,
  MIN(weather_date) AS min_date,
  MAX(weather_date) AS max_date,
  92 AS expected_dates,
  92 - COUNT(DISTINCT weather_date) AS missing_dates
FROM weather_dates;
