-- per-dataset historical coverage and processing freshness.
-- bind the five table parameters, :analysis_end_date, and :tolerance_days.
WITH dataset_metrics AS (
  SELECT 'silver_green_taxi_trips' AS dataset, 'EVENT_DATE' AS coverage_type,
         MAX(pickup_date_local) AS actual_through,
         MAX(silver_processed_at) AS last_processed_at,
         COUNT(*) AS row_count
  FROM IDENTIFIER(:silver_taxi_table)
  UNION ALL
  SELECT 'silver_weather_hourly', 'EVENT_DATE', MAX(weather_date_local),
         MAX(silver_processed_at), COUNT(*)
  FROM IDENTIFIER(:silver_weather_table)
  UNION ALL
  SELECT 'silver_taxi_zones', 'STATIC_REFERENCE', CAST(NULL AS DATE),
         MAX(silver_processed_at), COUNT(*)
  FROM IDENTIFIER(:silver_zones_table)
  UNION ALL
  SELECT 'fact_taxi_trip', 'EVENT_DATE', MAX(TO_DATE(pickup_datetime)),
         MAX(gold_loaded_at), COUNT(*)
  FROM IDENTIFIER(:gold_taxi_table)
  UNION ALL
  SELECT 'fact_weather_hourly', 'EVENT_DATE', MAX(TO_DATE(weather_timestamp)),
         MAX(gold_loaded_at), COUNT(*)
  FROM IDENTIFIER(:gold_weather_table)
)
SELECT
  dataset,
  coverage_type,
  CASE WHEN coverage_type = 'EVENT_DATE' THEN TO_DATE(:analysis_end_date) END
    AS expected_through,
  actual_through,
  last_processed_at,
  row_count,
  CASE
    WHEN coverage_type = 'STATIC_REFERENCE' AND row_count > 0 THEN 'FRESH'
    WHEN row_count = 0 OR actual_through IS NULL THEN 'UNKNOWN'
    WHEN DATEDIFF(TO_DATE(:analysis_end_date), actual_through)
      <= CAST(:tolerance_days AS INT) THEN 'FRESH'
    ELSE 'STALE'
  END AS freshness_status,
  CASE
    WHEN coverage_type = 'EVENT_DATE' AND actual_through IS NOT NULL
      THEN DATEDIFF(TO_DATE(:analysis_end_date), actual_through)
  END AS lag_days,
  CASE
    WHEN coverage_type = 'STATIC_REFERENCE' THEN 'refresh on approved source revision'
    ELSE 'historical window through configured analysis end date'
  END AS availability_expectation
FROM dataset_metrics
ORDER BY dataset;
