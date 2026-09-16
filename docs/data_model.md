# NYC Mobility Data Model and Contracts

**Owner:** Tina (`crisstin92-ui`)  
**Status:** Draft / proposed contract for team review  
**Scope:** Green Taxi, Weather, Taxi Zones  
**Analysis period:** March–May 2026  
**Target layer:** Silver and Gold

## 1. Purpose

This document carries forward the contract/model portion of issue #4 into a concrete proposal based on the available Bronze profiling evidence. It defines the proposed Silver/Gold grains, keys, types, nullability, lineage, timezone rules, quality handling, join cardinality, metrics, and incremental strategy.

This is a **proposed contract**, not a claim that all Silver/Gold tables already exist. Open decisions are explicitly marked for owner confirmation before implementation.

Required sources are limited to Green Taxi, Weather, and Taxi Zones. NYC DOT is excluded.

## 2. Evidence Used

The model is based on the three-source Bronze profiles and acquisition evidence currently available in the repository.

### Green Taxi

- Bronze grain: one row = one ingested Green Taxi trip record.
- 133,367 Bronze rows across March–May source files.
- Required trip/location fields have no nulls.
- Exact full-row duplicate groups: 0.
- Tested composite `VendorID + lpep_pickup_datetime + lpep_dropoff_datetime + PULocationID + DOLocationID` is **not unique**: 384 duplicate candidate groups, maximum occurrence 2.
- 11 pickups are before the intended March–May analysis window; 0 are on/after June 1.
- One negative-duration row was observed; 99 zero-duration rows.
- Negative `fare_amount`: 384 rows; negative `total_amount`: 391 rows.
- Maximum `trip_distance`: 111,005.95 and requires downstream quality review.
- All observed pickup/dropoff LocationIDs resolve to the Taxi Zones reference.
- 18,754 rows share nulls in `store_and_fwd_flag`, `RatecodeID`, `passenger_count`, `payment_type`, `trip_type`, and `congestion_surcharge`; `ehail_fee` is null in all 133,367 rows.

### Weather

- Bronze grain: one row = one monthly Open-Meteo API response.
- Three monthly response rows contain nested hourly arrays.
- March = 744 hourly positions; April = 720; May = 744; total = 2,208 hourly positions.
- No hourly-array length mismatches or null hourly elements were observed.
- Source-reported timezone: `America/New_York`.
- Source-reported units: time `iso8601`, temperature `°C`, precipitation `mm`, wind speed `km/h`.

### Taxi Zones

- Bronze grain: one row = one taxi zone/location reference record.
- 265 rows and 265 distinct `LocationID` values.
- `LocationID` is a strong natural key candidate.
- IDs 1–265 are represented; 264 = `Unknown`, 265 = `Outside of NYC`.
- No nulls or duplicate LocationIDs were observed.

## 3. Proposed Layered Model

The proposed model keeps a normalized trip-level analysis path while also providing required hourly and daily mobility outputs.

```text
BRONZE
  ├── bronze_green_taxi_raw
  ├── bronze_weather_raw
  └── bronze_taxi_zones_raw
          │
          ▼
SILVER
  ├── silver_green_taxi_trips       (trip grain)
  ├── silver_weather_hourly         (hour grain)
  └── silver_taxi_zones             (zone dimension grain)
          │
          ├──────────────┐
          ▼              ▼
GOLD
  ├── gold_mobility_hourly_zone     (zone × local hour grain)
  └── gold_mobility_daily_zone      (zone × local day grain)
```

The hourly Gold table is the primary integration path for weather and hourly demand analysis. The daily Gold table is derived from the same validated trip/hour path and satisfies the required daily mobility output.

## 4. Timezone and Timestamp Contract

### Canonical timezone

Use **`America/New_York`** as the analytical timezone for both taxi and weather alignment.

Green Taxi timestamps are treated as NYC local timestamps for this project. Weather explicitly reports `America/New_York`.

### Silver representation

Keep the original parsed trip timestamps as local timestamps and derive explicit analytical fields:

- `pickup_ts_local` — timestamp in `America/New_York`.
- `dropoff_ts_local` — timestamp in `America/New_York`.
- `pickup_hour_local` — truncated pickup timestamp to local hour.
- `pickup_date_local` — local pickup calendar date.
- `dropoff_date_local` — local dropoff calendar date.
- `trip_duration_seconds` — dropoff minus pickup in seconds.

Where the implementation supports timezone-aware timestamps, also derive UTC timestamps for unambiguous storage/comparison. Do not silently reinterpret the source local clock as UTC.

### DST rule

Use timezone-aware `America/New_York` conversion when normalizing timestamps. Do not hard-code a fixed `UTC-04:00` offset for the whole period.

The March 2026 spring-forward transition creates a local-time discontinuity. The weather source currently reports `America/New_York` with `GMT-4` / `-14400` in the observed Bronze profile, so this source behavior must be verified during Silver implementation. The weather source's timestamps must not be manually shifted by an assumed offset without confirming the actual response semantics.

There is no November fall-back transition inside the March–May 2026 project window.

**Open decision / owner:** Angela + Shiena + Virna to confirm the final timezone conversion implementation against a March DST sample before Silver code is finalized.

## 5. Silver Contracts

### 5.1 `silver_green_taxi_trips`

**Grain:** one row = one retained Green Taxi trip record after Silver validation/standardization.

**Lineage:** `nyc_bronze.bronze_green_taxi_raw`.

#### Proposed schema

| Field | Type | Nullable | Key / role | Notes |
|---|---|---|---|---|
| `trip_key` | string | No | Surrogate/incremental key | Deterministic hash of source identity fields plus source file/row context as needed; not presented as a source-native ID. |
| `vendor_id` | bigint | Yes | Attribute | From `VendorID`. |
| `pickup_ts_local` | timestamp | No | Time key component | From `lpep_pickup_datetime`, normalized to `America/New_York`. |
| `dropoff_ts_local` | timestamp | No | Time key component | From `lpep_dropoff_datetime`, normalized to `America/New_York`. |
| `pickup_hour_local` | timestamp | No | Hour join key | `pickup_ts_local` truncated to hour. |
| `pickup_date_local` | date | No | Day join key | Local pickup date. |
| `dropoff_date_local` | date | No | Attribute | Local dropoff date. |
| `pu_location_id` | bigint | No | FK | Joins to `silver_taxi_zones.location_id`. |
| `do_location_id` | bigint | No | FK | Joins to `silver_taxi_zones.location_id`. |
| `store_and_fwd_flag` | string | Yes | Attribute | Preserve source nulls unless a validated source rule is agreed. |
| `ratecode_id` | bigint | Yes | Attribute | Preserve source nulls. |
| `passenger_count` | bigint | Yes | Measure/input | Preserve source nulls; zero is distinct from null. |
| `trip_distance` | double | No | Measure | Source distance; unit must remain documented from TLC source contract. |
| `fare_amount` | double | No | Measure | Preserve source value; invalid negative values are flagged, not silently converted. |
| `extra` | double | Yes | Measure | Source value. |
| `mta_tax` | double | Yes | Measure | Source value. |
| `tip_amount` | double | Yes | Measure | Source value. |
| `tolls_amount` | double | Yes | Measure | Source value. |
| `ehail_fee` | double | Yes | Measure | Observed null for all Bronze rows. Preserve as nullable. |
| `improvement_surcharge` | double | Yes | Measure | Source value. |
| `total_amount` | double | No | Measure | Preserve source value; negative values are flagged. |
| `payment_type` | bigint | Yes | Attribute | Preserve source nulls. |
| `trip_type` | bigint | Yes | Attribute | Preserve source nulls. |
| `congestion_surcharge` | double | Yes | Measure | Preserve source nulls. |
| `trip_duration_seconds` | bigint | No | Derived measure | `dropoff - pickup`. Negative duration is invalid for mobility metrics. |
| `is_in_analysis_window` | boolean | No | Quality flag | True when pickup is in March–May 2026. |
| `is_valid_duration` | boolean | No | Quality flag | False for negative duration. |
| `is_valid_distance` | boolean | No | Quality flag | False for negative distance; extreme values may receive a separate review flag. |
| `is_valid_fare` | boolean | No | Quality flag | Negative fare is flagged for review rather than automatically deleted. |
| `is_valid_total` | boolean | No | Quality flag | Negative total is flagged for review rather than automatically deleted. |
| `source_file` | string | No | Lineage | Bronze `_source_file`. |
| `ingested_at` | timestamp | No | Lineage | Bronze `_ingested_at`. |

**Key policy:** No natural trip key has been proven unique. `trip_key` is therefore a deterministic warehouse key, not a claim that the source contains a unique trip identifier. The original candidate-key columns remain available for traceability.

### 5.2 `silver_weather_hourly`

**Grain:** one row = one weather observation for one local hour.

**Lineage:** `nyc_bronze.bronze_weather_raw`, after exploding aligned hourly arrays.

#### Proposed schema

| Field | Type | Nullable | Key / role | Notes |
|---|---|---|---|---|
| `weather_hour_local` | timestamp | No | Natural time key | Source hourly timestamp aligned to `America/New_York`. |
| `weather_date_local` | date | No | Day key | Derived from local hour. |
| `temperature_2m_c` | double | Yes | Measure | Source unit `°C`. |
| `precipitation_mm` | double | Yes | Measure | Source unit `mm`. |
| `wind_speed_10m_kmh` | double | Yes | Measure | Source unit `km/h`. |
| `timezone` | string | No | Source metadata | Expected `America/New_York`. |
| `source_file` | string | No | Lineage | Bronze `_source_file`. |
| `ingested_at` | timestamp | No | Lineage | Bronze `_ingested_at`. |

**Key:** `weather_hour_local` should be unique for the final project period. If the source produces duplicate hour rows after normalization, Silver must fail/review rather than allowing a many-to-many weather join.

**Source structure rule:** Bronze contains monthly responses with nested arrays; Silver must explode the arrays positionally so `time[i]`, `temperature_2m[i]`, `precipitation[i]`, and `wind_speed_10m[i]` remain one observation.

### 5.3 `silver_taxi_zones`

**Grain:** one row = one taxi zone/location reference record.

**Lineage:** `nyc_bronze.bronze_taxi_zones_raw`.

#### Proposed schema

| Field | Type | Nullable | Key / role | Notes |
|---|---|---|---|---|
| `location_id` | bigint | No | Primary/natural key | Unique 1–265. |
| `borough` | string | No | Attribute | Source value. |
| `zone` | string | No | Attribute | Source value. |
| `service_zone` | string | No | Attribute | Source value. |
| `source_file` | string | No | Lineage | Bronze `_source_file`. |
| `ingested_at` | timestamp | No | Lineage | Bronze `_ingested_at`. |

Special values `LocationID = 264` (`Unknown`) and `265` (`Outside of NYC`) are valid reference members and must not be dropped merely because their labels contain `Unknown`/outside semantics.

## 6. Gold Contracts

### 6.1 `gold_mobility_hourly_zone`

**Required analysis path.**

**Grain:** one row = one **pickup zone × local pickup hour** combination for the analysis period. A row can be present only when the combination has activity, unless the team explicitly chooses a complete zone-hour scaffold.

**Lineage:** `silver_green_taxi_trips` + `silver_taxi_zones` + `silver_weather_hourly`.

#### Proposed schema

| Field | Type | Nullable | Key / role | Notes |
|---|---|---|---|---|
| `pickup_hour_local` | timestamp | No | Composite key | Local hourly bucket. |
| `pickup_date_local` | date | No | Dimension | Local calendar date. |
| `pu_location_id` | bigint | No | Composite key / FK | Pickup zone. |
| `borough` | string | No | Dimension | From pickup-zone lookup. |
| `zone` | string | No | Dimension | From pickup-zone lookup. |
| `service_zone` | string | No | Dimension | From pickup-zone lookup. |
| `trip_count` | bigint | No | Metric | Count of retained/eligible trip rows according to final quality rule. |
| `avg_trip_duration_seconds` | double | Yes | Metric | Average valid trip duration. |
| `total_trip_distance` | double | No | Metric | Sum of eligible distances. |
| `avg_trip_distance` | double | Yes | Metric | Average eligible distance. |
| `total_fare_amount` | double | No | Metric | Sum under documented fare inclusion rule. |
| `total_amount` | double | No | Metric | Sum under documented total inclusion rule. |
| `avg_total_amount` | double | Yes | Metric | Average eligible total. |
| `weather_hour_local` | timestamp | No | Join key | Same local hour as pickup hour. |
| `temperature_2m_c` | double | Yes | Weather metric | Left-joined weather. |
| `precipitation_mm` | double | Yes | Weather metric | Left-joined weather. |
| `wind_speed_10m_kmh` | double | Yes | Weather metric | Left-joined weather. |
| `weather_match_status` | string | No | Quality field | `MATCHED`, `MISSING_WEATHER`, or `DUPLICATE_WEATHER_KEY`. |

**Expected grain uniqueness:** `pickup_hour_local + pu_location_id` must be unique.

### 6.2 `gold_mobility_daily_zone`

**Required daily mobility output.**

**Grain:** one row = one **pickup zone × local calendar day** combination.

**Lineage:** preferably aggregated from `gold_mobility_hourly_zone` to preserve one authoritative mobility path; alternatively directly from Silver with reconciliation to hourly Gold.

#### Proposed schema

| Field | Type | Nullable | Key / role | Notes |
|---|---|---|---|---|
| `pickup_date_local` | date | No | Composite key | Local calendar date. |
| `pu_location_id` | bigint | No | Composite key / FK | Pickup zone. |
| `borough` | string | No | Dimension | Pickup zone borough. |
| `zone` | string | No | Dimension | Pickup zone name. |
| `service_zone` | string | No | Dimension | Pickup zone service zone. |
| `trip_count` | bigint | No | Metric | Daily trip count. |
| `avg_trip_duration_seconds` | double | Yes | Metric | Average valid duration. |
| `total_trip_distance` | double | No | Metric | Daily distance sum. |
| `total_fare_amount` | double | No | Metric | Daily fare sum under documented rule. |
| `total_amount` | double | No | Metric | Daily total sum under documented rule. |
| `avg_temperature_2m_c` | double | Yes | Weather summary | Average hourly temperature across matched hours. |
| `total_precipitation_mm` | double | Yes | Weather summary | Sum of hourly precipitation across matched hours. |
| `avg_wind_speed_10m_kmh` | double | Yes | Weather summary | Average hourly wind speed across matched hours. |
| `weather_hours_matched` | bigint | No | Quality metric | Number of matched hours contributing weather metrics. |
| `weather_hours_expected` | bigint | No | Quality metric | Expected hourly buckets represented by the mobility records. |

**Expected grain uniqueness:** `pickup_date_local + pu_location_id` must be unique.

## 7. Join Contracts and Cardinality

Join cardinality is a core correctness requirement. A weather or zone join must never multiply a taxi trip unexpectedly.

### 7.1 Pickup zone join

```text
silver_green_taxi_trips.pu_location_id
    N : 1
silver_taxi_zones.location_id
```

Expected result: each taxi trip matches **0 or 1** zone row. Based on profiling, all observed pickup LocationIDs currently resolve, so the expected project result is **1 match per trip**.

A zone duplicate would create a many-to-one violation and must fail/review before Gold aggregation.

### 7.2 Dropoff zone join

```text
silver_green_taxi_trips.do_location_id
    N : 1
silver_taxi_zones.location_id
```

Expected result: each taxi trip matches **0 or 1** zone row. Based on profiling, all observed dropoff LocationIDs currently resolve, so the expected project result is **1 match per trip**.

### 7.3 Weather hour join

```text
silver_green_taxi_trips.pickup_hour_local
    N : 1
silver_weather_hourly.weather_hour_local
```

Expected result: each taxi trip matches **0 or 1** weather row.

The weather key must be unique before the join. If weather contains two rows for the same hour, do not join directly; quarantine/review the duplicate weather key first.

### 7.4 Safe join sequence

To prevent multiplication:

1. Validate `silver_taxi_zones.location_id` uniqueness.
2. Validate `silver_weather_hourly.weather_hour_local` uniqueness.
3. Add pickup-zone attributes using `N:1` join.
4. Add dropoff-zone attributes using `N:1` join.
5. Add weather using `N:1` hourly join.
6. Compare trip row count before and after joins.
7. Only then aggregate to hourly Gold.

The expected number of rows after each enrichment join is **equal to the input trip row count**, assuming no unmatched records are dropped by the selected join type. Any increase indicates a cardinality defect.

## 8. Duplicate Policy

### Source duplicates

Exact full-row duplicates in Green Taxi were not observed. The candidate composite is not unique, so duplicate candidate groups are **not automatically deleted**.

The current evidence includes a pair with the same timestamps/locations but opposite monetary signs, which may represent a correction/reversal rather than an accidental duplicate.

### Silver policy

- Preserve source records needed for traceability.
- Generate a deterministic `trip_key` for warehouse processing.
- Do not use `dropDuplicates()` on the candidate composite as the default policy.
- Mark candidate duplicate groups for review.
- If a deterministic duplicate rule is later approved, document it as a separate model decision and reconcile row counts before/after.

### Gold policy

Gold metrics must use the agreed eligibility rule consistently. The chosen rule must be applied before aggregation so the same trip is not counted multiple times merely because of enrichment joins.

## 9. Invalid and Unknown-Value Handling

### Date scope

The project analysis window is March 1 through May 31, 2026, based on **pickup local date**.

Records outside that pickup window are retained in Silver with `is_in_analysis_window = false` for traceability but excluded from the required Gold reporting unless a specific analysis explicitly includes them.

### Trip duration

`trip_duration_seconds = dropoff - pickup`.

- Negative duration: invalid for mobility metrics; flag and exclude from duration averages/sums requiring positive elapsed time.
- Zero duration: retain as an observed source value but flag/review; do not silently convert to null.
- Positive duration: eligible for normal duration metrics subject to other quality checks.

### Distance

- Negative distance: invalid; exclude from distance metrics.
- Zero distance: retain and distinguish from null. The profile found 4,592 zero-distance rows.
- Extreme distance values: flag for review rather than applying an undocumented hard cutoff. The observed maximum is 111,005.95.

### Fare and total amount

- Negative `fare_amount` / `total_amount`: retain in Silver with quality flags; exclude from standard positive-trip revenue metrics **only if the team confirms this analytical rule**.
- Zero values: retain as valid source observations unless a metric explicitly requires positive values.
- Do not replace negative values with zero.

### Nullable fields

Source-null fields remain nullable in Silver. A null means source missing/unknown; it is not automatically equivalent to zero or a literal `Unknown` category.

### Taxi Zones

`LocationID 264` (`Unknown`) and `265` (`Outside of NYC`) are valid reference records. They remain joinable dimensions. They must not be treated as missing foreign keys.

## 10. Units Contract

| Measure | Silver representation | Source unit | Gold handling |
|---|---|---|---|
| Green Taxi pickup/dropoff | timestamp | NYC local time | Normalize/alignment using `America/New_York`. |
| `trip_duration_seconds` | bigint | seconds | Derived from timestamps. |
| `trip_distance` | double | TLC source distance unit; verify source documentation before final consumer labeling | Preserve numeric value; do not silently convert. |
| `fare_amount` | double | source currency amount | Preserve source value; currency label/assumption must be documented by source contract. |
| `total_amount` | double | source currency amount | Preserve source value. |
| Weather temperature | double | °C | `temperature_2m_c`. |
| Weather precipitation | double | mm | `precipitation_mm`. |
| Weather wind speed | double | km/h | `wind_speed_10m_kmh`. |

**Open decision / owner:** Angela + Shiena + Virna should confirm the exact TLC unit/currency labels before Gold consumer documentation is finalized. No unit conversion should be introduced without a documented source basis.

## 11. Metrics Contract

Required Gold outputs must support:

1. Highest demand by day/hour/zone.
2. Mobility volume, duration, distance, and fare/total amounts across weather conditions.
3. Pickup/dropoff/long-trip/fare patterns by area and time.

### Core metrics

- `trip_count`: count of eligible Silver trip rows after validated enrichment.
- `avg_trip_duration_seconds`: average of valid positive durations; invalid durations excluded.
- `total_trip_distance`: sum of distance values passing the distance eligibility rule.
- `avg_trip_distance`: average eligible distance.
- `total_fare_amount`: sum under the agreed negative-fare policy.
- `total_amount`: sum under the agreed negative-total policy.
- Weather metrics are attached at the pickup hour, not repeated as multiple weather rows.

### Long-trip analysis

Do not hard-code an arbitrary "long trip" threshold in the base contract. Preserve `trip_distance` in Silver and allow the business-query layer to define/document the threshold used for the long-trip question.

## 12. Hourly vs Daily Analysis Path

The model intentionally retains both grains:

```text
Trip grain
   │
   ├── pickup_hour_local + pickup_zone
   │          │
   │          ▼
   │   gold_mobility_hourly_zone
   │          │
   │          └── daily rollup
   │                    ▼
   │          gold_mobility_daily_zone
   │
   └── dropoff_zone retained on Silver for OD / area analysis
```

This avoids forcing hourly questions through a daily-only table and avoids rebuilding daily outputs independently with a second, potentially inconsistent aggregation path.

## 13. Incremental Contract

### Incremental unit

The primary incremental partition is **pickup month** for the March–May 2026 project scope.

Affected months are identified from `pickup_date_local`.

### Silver

Silver should be idempotent by deterministic `trip_key` and source file/month. Reprocessing a month must not append a second copy of the same source record.

### Weather

Weather is incremental by `weather_hour_local`. A rerun of a month replaces/upserts the affected hourly range after validating uniqueness.

### Taxi Zones

Taxi Zones is reference data. Refresh as a full small dimension or deterministic overwrite/upsert keyed by `location_id`; there is no need for trip-style monthly incremental processing.

### Gold

For a rerun of month `YYYY-MM`, recompute affected hourly and daily Gold rows for that month from validated Silver inputs, then replace/upsert those affected keys. Do not append blindly.

Affected Gold keys:

- Hourly: `pickup_hour_local + pu_location_id`.
- Daily: `pickup_date_local + pu_location_id`.

### Reconciliation

For every incremental rerun, record before/after counts and aggregate reconciliation:

```text
Silver eligible trips
        ↓
Hourly Gold trip_count sum
        ↓
Daily Gold trip_count sum
```

Any unexplained difference must block final acceptance for the rerun.

## 14. Input Contracts

### Green Taxi input

Expected source:

- March 2026 Parquet
- April 2026 Parquet
- May 2026 Parquet

Required fields for modeling:

```text
VendorID
lpep_pickup_datetime
lpep_dropoff_datetime
PULocationID
DOLocationID
trip_distance
fare_amount
total_amount
```

Other source fields should be preserved where available and documented above.

### Weather input

Expected three monthly API responses containing aligned arrays:

```text
hourly.time
hourly.temperature_2m
hourly.precipitation
hourly.wind_speed_10m
```

Expected source timezone: `America/New_York`.

### Taxi Zones input

Expected fields:

```text
LocationID
Borough
Zone
service_zone
```

`LocationID` must be unique and non-null before it is used as a dimension key.

## 15. Output Contracts

### Silver outputs

- `silver_green_taxi_trips`: trip grain.
- `silver_weather_hourly`: one row per weather hour.
- `silver_taxi_zones`: one row per LocationID.

### Gold outputs

- `gold_mobility_hourly_zone`: one row per pickup zone × local hour.
- `gold_mobility_daily_zone`: one row per pickup zone × local day.

All output tables must expose enough lineage to trace a Gold metric back to its Silver source and source file.

## 16. Quality Gates Before Gold

Silver implementation should not proceed to final Gold aggregation until these checks pass:

- [ ] Green Taxi required keys are non-null.
- [ ] Green Taxi timestamps are parseable and ordered for valid-duration records.
- [ ] `trip_key` is deterministic and unique in the processed Silver dataset.
- [ ] Candidate duplicate groups are documented and policy is acknowledged.
- [ ] Out-of-window pickups are identified separately from per-file outside-month findings.
- [ ] Taxi Zones `location_id` is unique.
- [ ] Pickup and dropoff LocationIDs have zero unresolved foreign keys, based on current profile.
- [ ] Weather arrays are exploded positionally without changing row alignment.
- [ ] Weather hour key is unique.
- [ ] Weather timezone/DST behavior is confirmed.
- [ ] Unit labels are confirmed.
- [ ] Join row counts remain stable through zone/weather enrichment.

## 17. Execution Order

Recommended order for the shared Databricks run:

1. Land/verify the three required raw sources.
2. Confirm Bronze profiling evidence and source contracts.
3. Build/validate `silver_taxi_zones`.
4. Build/validate `silver_weather_hourly`.
5. Build/validate `silver_green_taxi_trips`.
6. Run Silver quality gates.
7. Validate `N:1` pickup and dropoff zone joins.
8. Validate `N:1` weather-hour join.
9. Build `gold_mobility_hourly_zone`.
10. Reconcile hourly Gold trip counts to Silver eligible trips.
11. Build `gold_mobility_daily_zone` from hourly Gold or reconcile direct aggregation.
12. Reconcile daily totals to hourly totals.
13. Run required business queries.
14. For reruns, replace/upsert only affected month/hour/day keys according to the incremental contract.

## 18. Team Acknowledgement / Open Decisions

This document is ready for review, but the following items require explicit confirmation before the contract is considered final:

| Decision | Proposed default | Owner(s) | Status |
|---|---|---|---|
| Analytical timezone | `America/New_York` | Angela / Shiena / Virna | Pending confirmation |
| DST handling | Timezone-aware conversion; verify March spring-forward behavior | Angela / Shiena / Virna | Pending confirmation |
| Weather hourly key | `weather_hour_local`, unique | Angela / Shiena / Virna | Pending confirmation |
| Pickup/dropoff zone joins | `N:1` to `location_id` | Angela / Shiena / Virna | Pending confirmation |
| Duplicate candidate trip policy | Preserve + flag; no automatic deduplication | Angela / Shiena / Virna | Pending confirmation |
| Negative fare/total policy | Preserve + flag in Silver; Gold inclusion rule to be confirmed | Angela / Shiena / Virna | Pending confirmation |
| Negative/zero duration policy | Negative invalid; zero retained/reviewed | Angela / Shiena / Virna | Pending confirmation |
| Extreme distance policy | Flag/review, no undocumented hard cutoff | Angela / Shiena / Virna | Pending confirmation |
| Weather missing-hour policy | Left join + `MISSING_WEATHER` status | Angela / Shiena / Virna | Pending confirmation |
| TLC distance/currency labels | Verify against source documentation before final consumer docs | Angela / Shiena / Virna | Pending confirmation |
| Incremental strategy | Reprocess affected pickup month; upsert affected Gold keys | Angela / Shiena / Virna | Pending confirmation |

## 19. Evidence and Limitations

The model intentionally distinguishes **observed facts** from proposed downstream rules.

Observed Bronze evidence includes 133,367 Green Taxi rows, 265 Taxi Zone rows, and 3 Weather response rows, with the Green Taxi duplicate/invalid-value findings described above. The profiling was read-only and did not clean Bronze records.

The 384 Green Taxi candidate duplicate groups are not equivalent to 384 exact duplicate records. Full-row duplicate groups were 0 in the live profile. Therefore, the model does not assume those records should be removed.

Likewise, the raw-file metric "rows outside expected month" and the Bronze-wide count of 11 pickups before March 2026 are different checks and should not be combined into one metric.

The weather source's reported `GMT-4` / `-14400` offset needs an implementation-level DST check before the final Silver contract is frozen. The source-reported timezone is retained as evidence rather than silently overriding it.

## 20. Acceptance Checklist

- [x] Contracts cover Green Taxi, Weather, and Taxi Zones.
- [x] Contracts define hourly and daily Gold grains.
- [x] Proposed Silver grains, keys, types, nullable fields, and lineage are documented.
- [x] Timezone and DST rules are explicit.
- [x] Quality and invalid/unknown-value rules are explicit.
- [x] Pickup and dropoff zone joins are explicit.
- [x] Weather hourly join cardinality is explicit.
- [x] Duplicate policy is explicit.
- [x] Incremental policy is explicit.
- [x] Hourly analysis path and daily mobility output are both retained.
- [x] Input/output contracts and execution order are documented.
- [ ] Angela confirms contracts.
- [ ] Shiena confirms contracts.
- [ ] Virna confirms contracts.
- [ ] Open decisions are resolved/acknowledged.

**Current status: Draft — model decisions and evidence are ready for Silver-owner review.**
