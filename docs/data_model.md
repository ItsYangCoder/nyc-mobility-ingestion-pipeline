# NYC Mobility Data Model and Contracts

**Owner:** Tina (`crisstin92-ui`)  
**Status:** Confirmed contract for implementation  
**Scope:** Green Taxi, Weather, Taxi Zones  
**Analysis period:** March–May 2026  
**Target layer:** Silver and Gold

## 1. Purpose

This document defines the agreed Silver and Gold data model for the NYC mobility pipeline. It specifies table grains, keys, fields, lineage, timezone handling, join cardinality, quality rules, metrics, input/output contracts, and incremental processing.

The contract is based on the Bronze profiling evidence currently available in the repository. It defines the expected downstream model; it does not claim that all Silver/Gold tables already exist.

Required sources are limited to Green Taxi, Weather, and Taxi Zones. NYC DOT is excluded.

## 2. Evidence Used

### Green Taxi

- Bronze grain: one row = one ingested Green Taxi trip record.
- 133,367 Bronze rows across March–May source files.
- Required trip/location fields have no nulls.
- Exact full-row duplicate groups: 0.
- Tested composite `VendorID + lpep_pickup_datetime + lpep_dropoff_datetime + PULocationID + DOLocationID` is not unique: 384 candidate duplicate groups, maximum occurrence 2.
- 11 pickups are before the intended March–May analysis window; 0 are on/after June 1.
- One negative-duration row was observed; 99 zero-duration rows.
- Negative `fare_amount`: 384 rows; negative `total_amount`: 391 rows.
- Maximum `trip_distance`: 111,005.95 and requires downstream quality review.
- All observed pickup/dropoff LocationIDs resolve to the Taxi Zones reference.
- 18,754 rows share nulls in several optional fields; `ehail_fee` is null in all 133,367 rows.

### Weather

- Bronze grain: one row = one monthly Open-Meteo API response.
- March = 744 hourly positions; April = 720; May = 744; total = 2,208 hourly positions.
- No hourly-array length mismatches or null hourly elements were observed.
- Source-reported timezone: `America/New_York`.
- Source-reported units: temperature `°C`, precipitation `mm`, wind speed `km/h`.

### Taxi Zones

- Bronze grain: one row = one taxi zone/location reference record.
- 265 rows and 265 distinct `LocationID` values.
- IDs 1–265 are represented; 264 = `Unknown`, 265 = `Outside of NYC`.
- No nulls or duplicate LocationIDs were observed.

## 3. Layered Model

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
          ▼
GOLD
  ├── gold_mobility_hourly_zone     (pickup zone × local hour)
  └── gold_mobility_daily_zone      (pickup zone × local day)
```

The hourly Gold table is the primary integration path for weather and hourly demand analysis. Daily Gold is derived from the validated hourly path.

## 4. Timezone and Timestamp Contract

### Canonical timezone

Use **`America/New_York`** as the analytical timezone for both Taxi and Weather alignment.

Green Taxi timestamps are treated as NYC local timestamps for this project. Weather explicitly reports `America/New_York`.

### Silver representation

Derive:

- `pickup_ts_local` — pickup timestamp in `America/New_York`.
- `dropoff_ts_local` — dropoff timestamp in `America/New_York`.
- `pickup_hour_local` — pickup timestamp truncated to local hour.
- `pickup_date_local` — local pickup calendar date.
- `dropoff_date_local` — local dropoff calendar date.
- `trip_duration_seconds` — dropoff minus pickup in seconds.

UTC timestamps may also be derived where implementation supports timezone-aware storage/comparison, but UTC is not the analytical timezone and source local timestamps must not be reinterpreted as UTC.

### DST rule — CONFIRMED

Use timezone-aware `America/New_York` handling. Do not hard-code a fixed UTC offset for the whole project period.

The March 2026 spring-forward transition must be handled by the timezone-aware conversion. The team agreed to verify the March DST sample during Silver implementation. There is no November fall-back transition inside the March–May 2026 project window.

## 5. Silver Contracts

### 5.1 `silver_green_taxi_trips`

**Grain:** one row = one retained Green Taxi trip record after validation and standardization.

**Lineage:** `nyc_bronze.bronze_green_taxi_raw`.

| Field | Type | Nullable | Key / role | Notes |
|---|---|---|---|---|
| `trip_key` | string | No | Surrogate/incremental key | Deterministic hash of agreed source identity fields plus a stable source-record discriminator when required to distinguish candidate duplicate records. |
| `vendor_id` | bigint | Yes | Attribute | From `VendorID`. |
| `pickup_ts_local` | timestamp | No | Time key component | From `lpep_pickup_datetime`, normalized to `America/New_York`. |
| `dropoff_ts_local` | timestamp | No | Time key component | From `lpep_dropoff_datetime`, normalized to `America/New_York`. |
| `pickup_hour_local` | timestamp | No | Hour join key | `pickup_ts_local` truncated to hour. |
| `pickup_date_local` | date | No | Day join key | Local pickup date. |
| `dropoff_date_local` | date | No | Attribute | Local dropoff date. |
| `pu_location_id` | bigint | No | FK | Joins to `silver_taxi_zones.location_id`. |
| `do_location_id` | bigint | No | FK | Joins to `silver_taxi_zones.location_id`. |
| `store_and_fwd_flag` | string | Yes | Attribute | Preserve source nulls. |
| `ratecode_id` | bigint | Yes | Attribute | Preserve source nulls. |
| `passenger_count` | bigint | Yes | Input | Preserve source nulls; zero is distinct from null. |
| `trip_distance` | double | No | Measure | Preserve source numeric value; use documented TLC unit. |
| `fare_amount` | double | No | Measure | Preserve source value; negative values are flagged. |
| `extra` | double | Yes | Measure | Source value. |
| `mta_tax` | double | Yes | Measure | Source value. |
| `tip_amount` | double | Yes | Measure | Source value. |
| `tolls_amount` | double | Yes | Measure | Source value. |
| `ehail_fee` | double | Yes | Measure | Preserve as nullable. |
| `improvement_surcharge` | double | Yes | Measure | Source value. |
| `total_amount` | double | No | Measure | Preserve source value; negative values are flagged. |
| `payment_type` | bigint | Yes | Attribute | Preserve source nulls. |
| `trip_type` | bigint | Yes | Attribute | Preserve source nulls. |
| `congestion_surcharge` | double | Yes | Measure | Preserve source nulls. |
| `trip_duration_seconds` | bigint | No | Derived measure | `dropoff - pickup`. |
| `is_in_analysis_window` | boolean | No | Quality flag | True when pickup is in March–May 2026. |
| `is_valid_duration` | boolean | No | Quality flag | False for negative duration. |
| `is_valid_distance` | boolean | No | Quality flag | False for negative distance. |
| `is_valid_fare` | boolean | No | Quality flag | Negative fare is flagged for review. |
| `is_valid_total` | boolean | No | Quality flag | Negative total is flagged for review. |
| `source_file` | string | No | Lineage | Bronze `_source_file`. |
| `ingested_at` | timestamp | No | Lineage | Bronze `_ingested_at`. |

**Trip key policy:** No natural trip key has been proven unique. `trip_key` is a deterministic warehouse key, not a claim that the source contains a unique trip ID. The original candidate-key fields remain available for traceability.

### 5.2 `silver_weather_hourly`

**Grain:** one row = one weather observation for one local hour.

**Lineage:** `nyc_bronze.bronze_weather_raw`, after exploding aligned hourly arrays.

| Field | Type | Nullable | Key / role | Notes |
|---|---|---|---|---|
| `weather_hour_local` | timestamp | No | Natural time key | Source hourly timestamp aligned to `America/New_York`. |
| `weather_date_local` | date | No | Day key | Derived from local hour. |
| `temperature_2m_c` | double | Yes | Measure | `°C`. |
| `precipitation_mm` | double | Yes | Measure | `mm`. |
| `wind_speed_10m_kmh` | double | Yes | Measure | `km/h`. |
| `timezone` | string | No | Source metadata | Expected `America/New_York`. |
| `source_file` | string | No | Lineage | Bronze `_source_file`. |
| `ingested_at` | timestamp | No | Lineage | Bronze `_ingested_at`. |

**Key policy:** `weather_hour_local` must be unique for the final project period. Duplicate weather hours fail/review before joining.

**Array alignment:** explode the nested arrays positionally so `time[i]`, `temperature_2m[i]`, `precipitation[i]`, and `wind_speed_10m[i]` remain one observation.

### 5.3 `silver_taxi_zones`

**Grain:** one row = one taxi zone/location reference record.

**Lineage:** `nyc_bronze.bronze_taxi_zones_raw`.

| Field | Type | Nullable | Key / role |
|---|---|---|---|
| `location_id` | bigint | No | Primary/natural key |
| `borough` | string | No | Attribute |
| `zone` | string | No | Attribute |
| `service_zone` | string | No | Attribute |
| `source_file` | string | No | Lineage |
| `ingested_at` | timestamp | No | Lineage |

`LocationID = 264` (`Unknown`) and `265` (`Outside of NYC`) are valid reference members and must not be dropped.

## 6. Gold Contracts

### 6.1 `gold_mobility_hourly_zone`

**Grain:** one row = one pickup zone × local pickup hour combination for the analysis period. The agreed model contains active combinations only; a complete zone-hour scaffold is not required.

**Lineage:** `silver_green_taxi_trips` + `silver_taxi_zones` + `silver_weather_hourly`.

| Field | Type | Nullable | Key / role | Notes |
|---|---|---|---|---|
| `pickup_hour_local` | timestamp | No | Composite key | Local hourly bucket. |
| `pickup_date_local` | date | No | Dimension | Local calendar date. |
| `pu_location_id` | bigint | No | Composite key / FK | Pickup zone. |
| `borough` | string | No | Dimension | Pickup-zone lookup. |
| `zone` | string | No | Dimension | Pickup-zone lookup. |
| `service_zone` | string | No | Dimension | Pickup-zone lookup. |
| `trip_count` | bigint | No | Metric | Count of eligible Silver trip rows after validated enrichment. |
| `avg_trip_duration_seconds` | double | Yes | Metric | Average valid positive duration. |
| `total_trip_distance` | double | No | Metric | Sum of eligible distances. |
| `avg_trip_distance` | double | Yes | Metric | Average eligible distance. |
| `total_fare_amount` | double | No | Metric | Sum after applying confirmed negative-fare rule. |
| `total_amount` | double | No | Metric | Sum after applying confirmed negative-total rule. |
| `avg_total_amount` | double | Yes | Metric | Average eligible total. |
| `temperature_2m_c` | double | Yes | Weather metric | Left-joined weather. |
| `precipitation_mm` | double | Yes | Weather metric | Left-joined weather. |
| `wind_speed_10m_kmh` | double | Yes | Weather metric | Left-joined weather. |
| `weather_match_status` | string | No | Quality field | `MATCHED` or `MISSING_WEATHER`; duplicate weather keys are rejected before the join. |

**Expected uniqueness:** `pickup_hour_local + pu_location_id` must be unique.

### 6.2 `gold_mobility_daily_zone`

**Grain:** one row = one pickup zone × local calendar day combination.

**Lineage:** aggregate from `gold_mobility_hourly_zone` so there is one authoritative mobility aggregation path.

| Field | Type | Nullable | Key / role |
|---|---|---|---|
| `pickup_date_local` | date | No | Composite key |
| `pu_location_id` | bigint | No | Composite key / FK |
| `borough` | string | No | Dimension |
| `zone` | string | No | Dimension |
| `service_zone` | string | No | Dimension |
| `trip_count` | bigint | No | Metric |
| `avg_trip_duration_seconds` | double | Yes | Metric |
| `total_trip_distance` | double | No | Metric |
| `total_fare_amount` | double | No | Metric |
| `total_amount` | double | No | Metric |
| `avg_temperature_2m_c` | double | Yes | Weather summary |
| `total_precipitation_mm` | double | Yes | Weather summary |
| `avg_wind_speed_10m_kmh` | double | Yes | Weather summary |
| `weather_hours_matched` | bigint | No | Quality metric |
| `weather_hours_expected` | bigint | No | Quality metric |

**Expected uniqueness:** `pickup_date_local + pu_location_id` must be unique.

## 7. Join Contracts and Cardinality

### Pickup zone

```text
silver_green_taxi_trips.pu_location_id
    N : 1
silver_taxi_zones.location_id
```

Each taxi trip must match at most one zone row. Current profiling shows all observed pickup LocationIDs resolve.

### Dropoff zone

```text
silver_green_taxi_trips.do_location_id
    N : 1
silver_taxi_zones.location_id
```

Each taxi trip must match at most one zone row. Current profiling shows all observed dropoff LocationIDs resolve.

### Weather hour

```text
silver_green_taxi_trips.pickup_hour_local
    N : 1
silver_weather_hourly.weather_hour_local
```

Many taxi trips may match one weather observation for the same local hour. Each trip may match zero or one weather row. Missing weather must not remove the mobility record.

### Safe join sequence

1. Validate `silver_taxi_zones.location_id` uniqueness.
2. Validate `silver_weather_hourly.weather_hour_local` uniqueness.
3. Add pickup-zone attributes using the N:1 join.
4. Add dropoff-zone attributes using the N:1 join.
5. Add weather using the N:1 hourly join.
6. Compare trip row counts before and after enrichment.
7. Aggregate only after cardinality checks pass.

Any increase in trip row count indicates a cardinality defect and blocks Gold aggregation.

## 8. Duplicate Policy — CONFIRMED

Exact full-row duplicates were not observed. The tested candidate composite is not unique, so candidate duplicate groups are **preserved and flagged**, not automatically deleted.

The observed candidate pair with the same timestamps/locations but opposite monetary signs may represent a correction/reversal rather than an accidental duplicate.

### Silver

- Preserve source records for traceability.
- Generate a deterministic `trip_key`.
- Do not use `dropDuplicates()` on the candidate composite as the default policy.
- Flag candidate duplicate groups for review.

### Gold

Apply the agreed eligibility rules before aggregation. Enrichment joins must not multiply trip records.

## 9. Invalid and Unknown-Value Handling — CONFIRMED

### Date scope

The required analysis window is March 1 through May 31, 2026, based on pickup local date.

Out-of-window records are retained in Silver with `is_in_analysis_window = false` and excluded from required Gold reporting.

### Trip duration

- Negative duration: invalid; exclude from duration metrics.
- Zero duration: retain and flag/review; do not convert to null.
- Positive duration: eligible for normal duration metrics.

### Distance

- Negative distance: invalid; exclude from distance metrics.
- Zero distance: retain and distinguish from null.
- Extreme values: flag/review; no arbitrary hard cutoff is applied.

### Fare and total amount

- Negative `fare_amount` and `total_amount`: preserve in Silver and flag.
- Negative values are excluded from standard positive-trip revenue metrics.
- Zero values remain valid source observations unless a specific metric requires positive values.
- Never replace negative values with zero.

### Nullable fields

Source-null fields remain nullable. Null is not automatically equivalent to zero or a literal `Unknown` value.

### Taxi Zones

`LocationID 264` (`Unknown`) and `265` (`Outside of NYC`) remain valid reference members.

## 10. Units Contract — CONFIRMED

| Measure | Representation | Source unit | Gold handling |
|---|---|---|---|
| Green Taxi timestamps | timestamp | NYC local time | Align using `America/New_York`. |
| `trip_duration_seconds` | bigint | seconds | Derived from timestamps. |
| `trip_distance` | double | TLC source distance unit | Preserve numeric value; verify/source-label exact unit before consumer documentation; no silent conversion. |
| `fare_amount` | double | source currency amount | Preserve source value; document source currency label. |
| `total_amount` | double | source currency amount | Preserve source value; document source currency label. |
| Weather temperature | double | °C | `temperature_2m_c`. |
| Weather precipitation | double | mm | `precipitation_mm`. |
| Weather wind speed | double | km/h | `wind_speed_10m_kmh`. |

The team confirmed that exact TLC distance/currency labels must be verified against the source documentation before final consumer-facing documentation. No undocumented unit conversion is allowed.

## 11. Metrics Contract

Required Gold outputs support demand by day/hour/zone and mobility volume, duration, distance, fare/total amounts across weather conditions.

- `trip_count`: count of eligible Silver trip rows after validated enrichment.
- `avg_trip_duration_seconds`: average of valid positive durations.
- `total_trip_distance`: sum of distance values passing the distance eligibility rule.
- `avg_trip_distance`: average eligible distance.
- `total_fare_amount`: sum after the confirmed negative-fare exclusion rule.
- `total_amount`: sum after the confirmed negative-total exclusion rule.
- Weather metrics are attached once at the pickup hour.

### Long-trip analysis

Do not hard-code a long-trip threshold in the base contract. The business-query layer defines and documents the threshold for a specific analysis.

## 12. Hourly vs Daily Analysis Path

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

This keeps hourly and daily analysis consistent and avoids rebuilding daily outputs through a separate aggregation path.

## 13. Incremental Contract — CONFIRMED

### Incremental unit

The primary incremental partition is **pickup month** for March–May 2026.

### Silver

Silver is idempotent by deterministic `trip_key` and source file/month. Reprocessing a month must not append a second copy of the same source record.

### Weather

Weather is incremental by `weather_hour_local`. A monthly rerun replaces/upserts the affected hourly range after uniqueness validation.

### Taxi Zones

Taxi Zones is a small reference dimension. Refresh as a full dimension or deterministic overwrite/upsert keyed by `location_id`.

### Gold

For a rerun of month `YYYY-MM`, recompute affected hourly and daily Gold rows from validated Silver inputs, then replace/upsert affected keys. Do not blindly append.

Affected Gold keys:

- Hourly: `pickup_hour_local + pu_location_id`.
- Daily: `pickup_date_local + pu_location_id`.

### Reconciliation

For every rerun:

```text
Silver eligible trips
        ↓
Hourly Gold trip_count sum
        ↓
Daily Gold trip_count sum
```

Any unexplained difference blocks final acceptance.

## 14. Input Contracts

### Green Taxi input

Expected source files:

- March 2026 Parquet
- April 2026 Parquet
- May 2026 Parquet

Required fields:

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

Other source fields should be preserved where available and documented in the Silver schema.

### Weather input

Expected monthly responses containing aligned arrays:

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

`LocationID` must be unique and non-null before use as a dimension key.

## 15. Output Contracts

### Silver outputs

- `silver_green_taxi_trips`: trip grain.
- `silver_weather_hourly`: one row per weather hour.
- `silver_taxi_zones`: one row per LocationID.

### Gold outputs

- `gold_mobility_hourly_zone`: one row per pickup zone × local hour.
- `gold_mobility_daily_zone`: one row per pickup zone × local day.

All outputs must expose enough lineage to trace Gold metrics back to Silver and the source file.

## 16. Quality Gates Before Gold

- [ ] Green Taxi required keys are non-null.
- [ ] Green Taxi timestamps are parseable and ordered for valid-duration records.
- [ ] `trip_key` is deterministic and unique in processed Silver.
- [x] Candidate duplicate groups are documented and policy confirmed.
- [ ] Out-of-window pickups are identified separately from per-file outside-month findings.
- [ ] Taxi Zones `location_id` is unique.
- [ ] Pickup and dropoff LocationIDs have zero unresolved foreign keys.
- [ ] Weather arrays are exploded positionally without changing row alignment.
- [ ] Weather hour key is unique.
- [x] Weather timezone/DST behavior is confirmed as a contract rule; implementation verification remains a quality gate.
- [x] Unit handling policy is confirmed; exact TLC labels remain a source-documentation verification step.
- [ ] Join row counts remain stable through zone/weather enrichment.

## 17. Execution Order

1. Land/verify the three required raw sources.
2. Confirm Bronze profiling evidence and source contracts.
3. Build/validate `silver_taxi_zones`.
4. Build/validate `silver_weather_hourly`.
5. Build/validate `silver_green_taxi_trips`.
6. Run Silver quality gates.
7. Validate N:1 pickup and dropoff zone joins.
8. Validate N:1 weather-hour join.
9. Build `gold_mobility_hourly_zone`.
10. Reconcile hourly Gold trip counts to Silver eligible trips.
11. Build `gold_mobility_daily_zone` from hourly Gold.
12. Reconcile daily totals to hourly totals.
13. Run required business queries.
14. For reruns, replace/upsert only affected month/hour/day keys according to the incremental contract.

## 18. Team Acknowledgement

The following contract decisions were explicitly confirmed by the team:

| Decision | Confirmed rule | Status |
|---|---|---|
| Analytical timezone | `America/New_York` | Confirmed |
| DST handling | Timezone-aware conversion; verify March spring-forward during implementation | Confirmed |
| Weather hourly key | `weather_hour_local`, unique | Confirmed |
| Pickup/dropoff zone joins | N:1 to `location_id` | Confirmed |
| Candidate duplicate trip policy | Preserve + flag; no automatic deduplication | Confirmed |
| Negative fare/total policy | Preserve + flag in Silver; exclude negatives from standard Gold revenue metrics | Confirmed |
| Negative/zero duration policy | Negative invalid; zero retained/reviewed | Confirmed |
| Extreme distance policy | Flag/review; no undocumented hard cutoff | Confirmed |
| Weather missing-hour policy | Left join + `MISSING_WEATHER` status | Confirmed |
| TLC distance/currency labels | Verify exact source labels before final consumer documentation; no silent conversion | Confirmed |
| Incremental strategy | Reprocess affected pickup month; upsert/replace affected Gold keys | Confirmed |

### Team acknowledgement

- Angela — Confirmed
- Shiena — Confirmed
- Virna — Confirmed
- Tina — Updated the contract based on the confirmed decisions

## 19. Evidence and Limitations

The model distinguishes observed Bronze facts from agreed downstream rules.

The 384 Green Taxi candidate duplicate groups are not equivalent to 384 exact duplicate records. Full-row duplicate groups were 0 in the profile, so the model does not assume those records should be removed.

The raw-file metric "rows outside expected month" and the Bronze-wide count of 11 pickups before March 2026 are separate checks and should not be combined.

The weather source reports `America/New_York`; implementation must still verify the March DST behavior rather than manually applying a fixed UTC offset.

TLC source documentation must be used to finalize the exact consumer-facing distance and currency labels before those labels are treated as implementation constants.

## 20. Acceptance Checklist

- [x] Contracts cover Green Taxi, Weather, and Taxi Zones.
- [x] Contracts define hourly and daily Gold grains.
- [x] Silver grains, keys, types, nullable fields, and lineage are documented.
- [x] Timezone and DST rules are explicit.
- [x] Quality and invalid/unknown-value rules are explicit.
- [x] Pickup and dropoff zone joins are explicit.
- [x] Weather hourly join cardinality is explicit.
- [x] Duplicate policy is explicit.
- [x] Incremental policy is explicit.
- [x] Hourly analysis path and daily mobility output are both retained.
- [x] Input/output contracts and execution order are documented.
- [x] Angela confirmed the contracts.
- [x] Shiena confirmed the contracts.
- [x] Virna confirmed the contracts.
- [x] Open contract decisions are resolved/acknowledged.

**Current status: Confirmed — ready for implementation and PR review.**
