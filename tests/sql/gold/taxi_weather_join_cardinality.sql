-- PENDING: Enable after Gold tables are implemented
-- Taxi-to-weather join cardinality check.
-- The approved model joins pickup date + hour; there is no direct weather FK.

WITH weather_grain AS (
  SELECT
    date_key,
    hour_key,
    COUNT(*) AS weather_rows
  FROM nyc_mobility.nyc_gold.fact_weather_hourly
  GROUP BY date_key, hour_key
),
taxi_before_join AS (
  SELECT COUNT(*) AS taxi_count
  FROM nyc_mobility.nyc_gold.fact_taxi_trip
),
taxi_after_join AS (
  SELECT COUNT(*) AS taxi_count
  FROM nyc_mobility.nyc_gold.fact_taxi_trip t
  LEFT JOIN weather_grain w
    ON t.pickup_date_key = w.date_key
   AND t.pickup_hour_key = w.hour_key
),
weather_duplicates AS (
  SELECT COUNT_IF(weather_rows > 1) AS duplicate_weather_hours
  FROM weather_grain
)
SELECT
  b.taxi_count AS rows_before_join,
  a.taxi_count AS rows_after_join,
  a.taxi_count - b.taxi_count AS row_difference,
  w.duplicate_weather_hours,
  CASE
    WHEN b.taxi_count = a.taxi_count
      AND w.duplicate_weather_hours = 0
    THEN 'PASS'
    ELSE 'FAIL'
  END AS status
FROM taxi_before_join b
CROSS JOIN taxi_after_join a
CROSS JOIN weather_duplicates w;
