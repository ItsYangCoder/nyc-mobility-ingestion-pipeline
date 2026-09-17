-- Gold fact-to-dimension referential integrity. Every row must return PASS.

WITH checks AS (
    SELECT 'pickup_date' AS check_name, COUNT_IF(t.pickup_date_key IS NULL) AS null_keys,
           COUNT_IF(d.date_key IS NULL AND t.pickup_date_key IS NOT NULL) AS orphan_keys
    FROM nyc_mobility.nyc_gold.fact_taxi_trip t
    LEFT JOIN nyc_mobility.nyc_gold.dim_date d ON t.pickup_date_key = d.date_key
    UNION ALL
    SELECT 'dropoff_date', COUNT_IF(t.dropoff_date_key IS NULL),
           COUNT_IF(d.date_key IS NULL AND t.dropoff_date_key IS NOT NULL)
    FROM nyc_mobility.nyc_gold.fact_taxi_trip t
    LEFT JOIN nyc_mobility.nyc_gold.dim_date d ON t.dropoff_date_key = d.date_key
    UNION ALL
    SELECT 'pickup_hour', COUNT_IF(t.pickup_hour_key IS NULL),
           COUNT_IF(h.hour_key IS NULL AND t.pickup_hour_key IS NOT NULL)
    FROM nyc_mobility.nyc_gold.fact_taxi_trip t
    LEFT JOIN nyc_mobility.nyc_gold.dim_hour h ON t.pickup_hour_key = h.hour_key
    UNION ALL
    SELECT 'dropoff_hour', COUNT_IF(t.dropoff_hour_key IS NULL),
           COUNT_IF(h.hour_key IS NULL AND t.dropoff_hour_key IS NOT NULL)
    FROM nyc_mobility.nyc_gold.fact_taxi_trip t
    LEFT JOIN nyc_mobility.nyc_gold.dim_hour h ON t.dropoff_hour_key = h.hour_key
    UNION ALL
    SELECT 'pickup_location', COUNT_IF(t.pickup_location_id IS NULL),
           COUNT_IF(z.location_id IS NULL AND t.pickup_location_id IS NOT NULL)
    FROM nyc_mobility.nyc_gold.fact_taxi_trip t
    LEFT JOIN nyc_mobility.nyc_gold.dim_zone z ON t.pickup_location_id = z.location_id
    UNION ALL
    SELECT 'dropoff_location', COUNT_IF(t.dropoff_location_id IS NULL),
           COUNT_IF(z.location_id IS NULL AND t.dropoff_location_id IS NOT NULL)
    FROM nyc_mobility.nyc_gold.fact_taxi_trip t
    LEFT JOIN nyc_mobility.nyc_gold.dim_zone z ON t.dropoff_location_id = z.location_id
    UNION ALL
    SELECT 'weather_date', COUNT_IF(w.date_key IS NULL),
           COUNT_IF(d.date_key IS NULL AND w.date_key IS NOT NULL)
    FROM nyc_mobility.nyc_gold.fact_weather_hourly w
    LEFT JOIN nyc_mobility.nyc_gold.dim_date d ON w.date_key = d.date_key
    UNION ALL
    SELECT 'weather_hour', COUNT_IF(w.hour_key IS NULL),
           COUNT_IF(h.hour_key IS NULL AND w.hour_key IS NOT NULL)
    FROM nyc_mobility.nyc_gold.fact_weather_hourly w
    LEFT JOIN nyc_mobility.nyc_gold.dim_hour h ON w.hour_key = h.hour_key
)
SELECT check_name, null_keys, orphan_keys,
       CASE WHEN null_keys = 0 AND orphan_keys = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks
ORDER BY check_name;
