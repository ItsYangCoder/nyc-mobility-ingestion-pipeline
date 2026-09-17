-- PENDING: Enable after Silver tables are implemented
-- Silver referential integrity checks
-- Validates that Silver taxi trips reference valid zone IDs

WITH taxi_pickup_zones AS (
  SELECT DISTINCT pickup_zone_id
  FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
  WHERE pickup_zone_id IS NOT NULL
),
taxi_dropoff_zones AS (
  SELECT DISTINCT dropoff_zone_id
  FROM nyc_mobility.nyc_silver.silver_green_taxi_trips
  WHERE dropoff_zone_id IS NOT NULL
),
silver_zones AS (
  SELECT location_id
  FROM nyc_mobility.nyc_silver.silver_taxi_zones
)
SELECT 
  'pickup_zone' AS check_type,
  COUNT(*) AS total_distinct_zones,
  SUM(CASE WHEN pz.pickup_zone_id NOT IN (SELECT location_id FROM silver_zones) THEN 1 ELSE 0 END) AS orphan_zones
FROM taxi_pickup_zones pz
UNION ALL
SELECT 
  'dropoff_zone' AS check_type,
  COUNT(*) AS total_distinct_zones,
  SUM(CASE WHEN dz.dropoff_zone_id NOT IN (SELECT location_id FROM silver_zones) THEN 1 ELSE 0 END) AS orphan_zones
FROM taxi_dropoff_zones dz;
