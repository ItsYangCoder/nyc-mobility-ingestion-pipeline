# NYC Mobility Data Model

**Status:** Implementation contract under final team review  
**Scope:** NYC Green Taxi, Open-Meteo weather, and NYC Taxi Zones  
**Analysis period:** March 1-May 31, 2026  
**Analytical timezone:** America/New_York  
**Target:** Bronze -> Silver -> Gold galaxy schema

This document defines the table grains, keys, joins, quality rules, and evidence required for implementation. It does not claim that Silver and Gold tables already exist.

## 1. Verified source evidence

| Source | Verified evidence | Required action |
|---|---|---|
| Green Taxi | 133,367 Bronze rows across March-May; 0 exact full-row duplicate groups; 384 candidate duplicate groups; 11 pickups before March 1; 1 negative-duration row; 99 zero-duration rows; 384 negative fare rows; 391 negative total rows | Preserve source rows in Silver, add deterministic trip_key and quality flags, and exclude invalid measures only from affected Gold metrics |
| Weather | 3 monthly JSON responses; 744 March hours, 720 April hours, 744 May hours; 2,208 total hourly positions; no array-length mismatch or null hourly elements observed | Explode arrays by matching position and require one unique weather row per local hour |
| Taxi Zones | 265 rows and 265 distinct LocationID values; no null or duplicate keys; IDs 1-265 are present | Keep LocationID 264 (Unknown) and 265 (Outside of NYC) as valid dimension members |

Evidence is recorded in:

- [Angela Bronze profile](../profiles/angela.md)
- [Tina Bronze profile](../profiles/tina.md)
- [Virna Bronze profile](../profiles/virna.md)
- [Raw acquisition report](../evidence/raw_acquisition_report.md)
- [Raw acquisition checklist](../evidence/raw_acquisition_checklist.md)

## 2. Layer contracts

### Bronze

| Table | Grain | Required lineage |
|---|---|---|
| bronze_green_taxi_raw | One ingested Green Taxi source record | _source_file, _ingested_at |
| bronze_weather_raw | One monthly Open-Meteo response | _source_file, _ingested_at |
| bronze_taxi_zones_raw | One taxi-zone reference record | _source_file, _ingested_at |

Bronze preserves received values. Cleaning, filtering, and deduplication do not occur in Bronze.

### Silver

| Table | Grain and key | Required content |
|---|---|---|
| silver_green_taxi_trips | One retained source trip; unique deterministic trip_key | Local pickup/drop-off timestamps, pickup/drop-off date and hour, pickup/drop-off LocationID, trip measures, payment fields, source lineage, and quality flags |
| silver_weather_hourly | One weather observation per America/New_York hour; unique weather_hour_local | Temperature in °C, precipitation in mm, wind speed in km/h, timezone, source lineage |
| silver_taxi_zones | One row per LocationID; unique location_id | Borough, zone, service_zone, source lineage |

The tested taxi composite of VendorID, pickup timestamp, drop-off timestamp, pickup LocationID, and drop-off LocationID is not unique. It cannot be used as the trip primary key without a stable source-record discriminator.

## 3. Gold galaxy schema

Gold keeps trip events and hourly weather as separate facts that share conformed date and hour dimensions.

### Dimensions

| Table | Grain | Primary key | Main attributes |
|---|---|---|---|
| dim_date | One calendar date | date_key | full_date, year, quarter, month, month_name, day_of_month, day_of_week, day_name, weekend_flag |
| dim_hour | One hour of day | hour_key | hour, time_of_day, peak_hour_flag |
| dim_zone | One NYC taxi location | location_id | borough, zone, service_zone |

### Facts

| Table | Grain | Key | Main measures and references |
|---|---|---|---|
| fact_taxi_trip | One retained Green Taxi trip | trip_key | pickup/drop-off timestamps; pickup/drop-off date_key, hour_key, and zone keys; optional pickup_weather_hour_key; passenger_count; trip_distance; trip_duration_minutes; fare_amount; tip_amount; total_amount; payment_type; source_file; gold_loaded_at |
| fact_weather_hourly | One weather observation per local hour | weather_hour_key | weather_timestamp; date_key; hour_key; temperature_2m; precipitation; wind_speed_10m; precipitation_flag; temperature_band; timezone; source_file; gold_loaded_at |

### Required relationships

| From | To | Cardinality and rule |
|---|---|---|
| fact_taxi_trip.pickup_date_key | dim_date.date_key | Many-to-one |
| fact_taxi_trip.dropoff_date_key | dim_date.date_key | Many-to-one |
| fact_taxi_trip.pickup_hour_key | dim_hour.hour_key | Many-to-one |
| fact_taxi_trip.dropoff_hour_key | dim_hour.hour_key | Many-to-one |
| fact_taxi_trip.pickup_zone_key | dim_zone.location_id | Many-to-one |
| fact_taxi_trip.dropoff_zone_key | dim_zone.location_id | Many-to-one |
| fact_weather_hourly.date_key | dim_date.date_key | Many-to-one |
| fact_weather_hourly.hour_key | dim_hour.hour_key | Many-to-one |
| fact_taxi_trip.pickup_weather_hour_key | fact_weather_hourly.weather_hour_key | Zero-or-one weather match per trip; use a left join |

Before integration, dim_zone.location_id and the weather hourly key must be unique. The weather join must never increase the taxi-trip row count.

## 4. Time and units

- Treat Green Taxi timestamps as NYC local timestamps.
- Use America/New_York for taxi-weather alignment.
- Use timezone-aware logic for the March daylight-saving transition; do not hard-code one UTC offset.
- Derive trip_duration_minutes from dropoff minus pickup timestamps.
- Preserve trip_distance as the TLC source value until the exact consumer-facing unit is confirmed from TLC documentation.
- Preserve monetary source values; do not silently replace negatives with zero.
- Weather units are °C, mm, and km/h.

## 5. Quality policy

| Condition | Silver treatment | Gold treatment |
|---|---|---|
| Candidate taxi duplicate | Preserve and flag | Count according to the accepted eligibility rule; do not automatically drop |
| Exact full-row duplicate | Investigate and quarantine or reject according to evidence | Must not create duplicate fact keys |
| Pickup outside March-May | Preserve with is_in_analysis_window = false | Exclude from required reporting |
| Negative duration | Preserve and flag invalid | Exclude from duration metrics |
| Zero duration | Preserve and flag for review | Keep distinct from null |
| Negative distance | Preserve and flag invalid | Exclude from distance metrics |
| Negative fare or total | Preserve and flag | Exclude from standard positive-revenue metrics |
| Missing weather hour | Preserve taxi trip | Left join and record missing-weather status |
| Unknown/outside zone 264 or 265 | Preserve as valid reference member | Keep in dim_zone and reporting |

Null is not equivalent to zero or the text Unknown.

## 6. Incremental and idempotent processing

- Green Taxi is processed by source file and pickup month.
- Weather is processed by weather_hour_local.
- Taxi Zones is refreshed by deterministic overwrite or upsert on location_id.
- Reprocessing the same source file or month must not create another trip_key or weather_hour_key.
- A rerun replaces or upserts only affected keys; it must not blindly append.
- Run March, then add April, then add May without rebuilding accepted prior months.
- Run the May load twice. Silver and Gold row counts and measure totals must remain unchanged on the second run.

## 7. Business-question coverage

| Business question | Required tables and grouping |
|---|---|
| When and where is taxi demand highest? | fact_taxi_trip grouped through dim_date, dim_hour, and pickup dim_zone |
| How does weather affect demand and trip behavior? | fact_taxi_trip matched to fact_weather_hourly by local pickup hour; compare trip count, duration, distance, fare, and total amount |
| Which areas show the strongest mobility patterns or opportunities? | fact_taxi_trip grouped by pickup/drop-off dim_zone and compared across dim_date, dim_hour, and weather conditions |

## 8. Acceptance evidence

The pipeline is accepted only when the following checks return evidence, not only documentation:

| Check | Pass condition |
|---|---|
| Bronze counts | Green Taxi = 133,367; Weather raw responses = 3; Taxi Zones = 265 |
| Weather explosion | 2,208 hourly positions before any documented DST-specific adjustment |
| Silver trip key | trip_key is non-null, deterministic, and unique |
| Silver weather key | weather_hour_local is non-null and unique |
| Zone key | location_id is non-null and unique |
| Foreign keys | Pickup and drop-off zone keys resolve, including valid members 264 and 265 |
| Join cardinality | Zone and weather enrichment do not increase taxi-trip row count |
| Gold grains | fact_taxi_trip.trip_key and fact_weather_hourly.weather_hour_key are unique |
| Reconciliation | Gold trip rows reconcile to eligible Silver trips; excluded records are counted by reason |
| Idempotency | A repeated May load changes neither accepted row counts nor totals |
| Analytics | All three required questions have executable SQL and saved result evidence |

## 9. Execution order

1. Land and verify the three required raw sources.
2. Run the three Bronze tables and record counts.
3. Build and validate silver_taxi_zones.
4. Build and validate silver_weather_hourly.
5. Build and validate silver_green_taxi_trips.
6. Run Silver key, quality, and reconciliation checks.
7. Build dim_date, dim_hour, dim_zone, fact_weather_hourly, and fact_taxi_trip.
8. Validate join cardinality and Gold grains.
9. Run incremental and repeated-load tests.
10. Run the three analytics queries and save concise evidence.

## 10. Current limitations

- NYC DOT traffic advisories are optional and excluded from the required model.
- Silver and Gold implementations must still provide Databricks run evidence before this contract can be marked complete.
- Exact TLC labels for trip distance and currency must be confirmed from the source documentation before final consumer-facing release.
- The final schema approval remains a team review item; implementation must not silently diverge from this contract.
