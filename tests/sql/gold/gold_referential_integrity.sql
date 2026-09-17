-- PENDING: Enable after Gold tables are implemented
-- Gold referential integrity checks
-- Validates that Gold facts reference valid dimension keys.

SELECT 'pickup_date' AS check_type,
       COUNT(*) AS total_facts,
       COUNT_IF(pickup_date_key IS NULL) AS null_keys,
       COUNT_IF(d.date_key IS NULL AND t.pickup_date_key IS NOT NULL) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip t
LEFT JOIN nyc_mobility.nyc_gold.dim_date d
  ON t.pickup_date_key = d.date_key

UNION ALL

SELECT 'dropoff_date' AS check_type,
       COUNT(*) AS total_facts,
       COUNT_IF(dropoff_date_key IS NULL) AS null_keys,
       COUNT_IF(d.date_key IS NULL AND t.dropoff_date_key IS NOT NULL) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip t
LEFT JOIN nyc_mobility.nyc_gold.dim_date d
  ON t.dropoff_date_key = d.date_key

UNION ALL

SELECT 'pickup_hour' AS check_type,
       COUNT(*) AS total_facts,
       COUNT_IF(pickup_hour_key IS NULL) AS null_keys,
       COUNT_IF(h.hour_key IS NULL AND t.pickup_hour_key IS NOT NULL) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip t
LEFT JOIN nyc_mobility.nyc_gold.dim_hour h
  ON t.pickup_hour_key = h.hour_key

UNION ALL

SELECT 'dropoff_hour' AS check_type,
       COUNT(*) AS total_facts,
       COUNT_IF(dropoff_hour_key IS NULL) AS null_keys,
       COUNT_IF(h.hour_key IS NULL AND t.dropoff_hour_key IS NOT NULL) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip t
LEFT JOIN nyc_mobility.nyc_gold.dim_hour h
  ON t.dropoff_hour_key = h.hour_key

UNION ALL

SELECT 'pickup_location' AS check_type,
       COUNT(*) AS total_facts,
       COUNT_IF(pickup_location_id IS NULL) AS null_keys,
       COUNT_IF(z.location_id IS NULL AND t.pickup_location_id IS NOT NULL) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip t
LEFT JOIN nyc_mobility.nyc_gold.dim_zone z
  ON t.pickup_location_id = z.location_id

UNION ALL

SELECT 'dropoff_location' AS check_type,
       COUNT(*) AS total_facts,
       COUNT_IF(dropoff_location_id IS NULL) AS null_keys,
       COUNT_IF(z.location_id IS NULL AND t.dropoff_location_id IS NOT NULL) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_taxi_trip t
LEFT JOIN nyc_mobility.nyc_gold.dim_zone z
  ON t.dropoff_location_id = z.location_id

UNION ALL

SELECT 'weather_date' AS check_type,
       COUNT(*) AS total_facts,
       COUNT_IF(w.date_key IS NULL) AS null_keys,
       COUNT_IF(d.date_key IS NULL AND w.date_key IS NOT NULL) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_weather_hourly w
LEFT JOIN nyc_mobility.nyc_gold.dim_date d
  ON w.date_key = d.date_key

UNION ALL

SELECT 'weather_hour' AS check_type,
       COUNT(*) AS total_facts,
       COUNT_IF(w.hour_key IS NULL) AS null_keys,
       COUNT_IF(h.hour_key IS NULL AND w.hour_key IS NOT NULL) AS orphan_keys
FROM nyc_mobility.nyc_gold.fact_weather_hourly w
LEFT JOIN nyc_mobility.nyc_gold.dim_hour h
  ON w.hour_key = h.hour_key;
