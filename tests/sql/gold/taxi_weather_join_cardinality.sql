-- Taxi-to-weather join cardinality and coverage. Result must return PASS.

WITH weather_grain AS (
    SELECT date_key, hour_key, COUNT(*) AS weather_rows
    FROM nyc_mobility.nyc_gold.fact_weather_hourly
    GROUP BY date_key, hour_key
),
joined AS (
    SELECT t.trip_key, w.weather_rows
    FROM nyc_mobility.nyc_gold.fact_taxi_trip t
    LEFT JOIN weather_grain w
      ON t.pickup_date_key = w.date_key
     AND t.pickup_hour_key = w.hour_key
),
metrics AS (
    SELECT COUNT(*) AS rows_after_join,
           COUNT_IF(weather_rows IS NULL) AS trips_without_weather,
           COUNT_IF(weather_rows > 1) AS trips_with_multiple_weather_rows
    FROM joined
)
SELECT (SELECT COUNT(*) FROM nyc_mobility.nyc_gold.fact_taxi_trip) AS rows_before_join,
       rows_after_join,
       trips_without_weather,
       trips_with_multiple_weather_rows,
       CASE WHEN rows_after_join = (
                     SELECT COUNT(*) FROM nyc_mobility.nyc_gold.fact_taxi_trip
                 )
                 AND trips_without_weather = 0
                 AND trips_with_multiple_weather_rows = 0
            THEN 'PASS' ELSE 'FAIL' END AS status
FROM metrics;
