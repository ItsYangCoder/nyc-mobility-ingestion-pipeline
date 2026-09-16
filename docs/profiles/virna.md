# Virna — Bronze Profiling

## Observation Information

**Profiling status:** Final live Bronze profiling completed.

**Live Bronze schema:** `nyc_mobility.nyc_bronze`

**Observation time:**
- Databricks timestamp (UTC): `2026-09-16 08:04:52.335 UTC`
- Asia/Manila: `2026-09-16 16:04:52.335 UTC+08:00`

Tables profiled:
- `nyc_mobility.nyc_bronze.bronze_green_taxi_raw`
- `nyc_mobility.nyc_bronze.bronze_weather_raw`
- `nyc_mobility.nyc_bronze.bronze_taxi_zones_raw`

All profiling queries were read-only. No Bronze data was modified.

Only the required Green Taxi, Weather, and Taxi Zones sources were profiled. No NYC DOT bonus source was included.

---

## Reference Count Reconciliation

| Dataset | Observed Rows | Reference Rows | Result |
|---|---:|---:|---|
| Green Taxi | 133,367 | 133,367 | MATCH |
| Weather | 3 | 3 | MATCH |
| Taxi Zones | 265 | 265 | MATCH |

---

# Resource 1 — Taxi Zones

## Grain

One row = one taxi zone lookup record identified by `LocationID`.

## Schema

- LocationID — int
- Borough — string
- Zone — string
- service_zone — string
- _source_file — string
- _ingested_at — timestamp

## Quality Profile

- Total rows = 265
- Distinct LocationID = 265
- Null LocationID = 0
- Null Borough = 0
- Null Zone = 0
- Null service_zone = 0
- Null _source_file = 0
- Null _ingested_at = 0
- Duplicate LocationID rows = 0
- Exact duplicate groups = 0
- Extra exact duplicate rows = 0
- Minimum LocationID = 1
- Maximum LocationID = 265
- Non-positive LocationID = 0
- Distinct source files = 1

## Special Records

- `264 | Unknown | N/A | N/A`
- `265 | N/A | Outside of NYC | N/A`

These are existing lookup records and are not treated automatically as data errors.

## Source and Ingestion Profile

Source file:

`/Volumes/nyc_mobility/nyc_bronze/nyc_source_files/landing/taxi_zones/taxi_zone_lookup.csv`

All 265 rows were ingested at:

`2026-09-15 19:46:57.493 UTC`

## Key Candidate

`LocationID` is a strong natural key candidate because:

- total rows = 265
- distinct LocationID = 265
- duplicate LocationID rows = 0
- null LocationID = 0

Taxi Zones is static reference data, so date coverage is not applicable.

---

# Resource 2 — Green Taxi

## Grain

One row = one Green Taxi trip record.

## Schema

- VendorID — bigint
- lpep_pickup_datetime — timestamp
- lpep_dropoff_datetime — timestamp
- store_and_fwd_flag — string
- RatecodeID — bigint
- PULocationID — bigint
- DOLocationID — bigint
- passenger_count — bigint
- trip_distance — double
- fare_amount — double
- extra — double
- mta_tax — double
- tip_amount — double
- tolls_amount — double
- ehail_fee — double
- improvement_surcharge — double
- total_amount — double
- payment_type — bigint
- trip_type — bigint
- congestion_surcharge — double
- _source_file — string
- _ingested_at — timestamp

The live Bronze schema does not include `cbd_congestion_fee`.

## Row Count and Null Profile

- Total rows = 133,367
- Null VendorID = 0
- Null pickup datetime = 0
- Null dropoff datetime = 0
- Null store_and_fwd_flag = 18,754
- Null RatecodeID = 18,754
- Null PULocationID = 0
- Null DOLocationID = 0
- Null passenger_count = 18,754
- Null trip_distance = 0
- Null fare_amount = 0
- Null extra = 0
- Null mta_tax = 0
- Null tip_amount = 0
- Null tolls_amount = 0
- Null ehail_fee = 133,367
- Null improvement_surcharge = 0
- Null total_amount = 0
- Null payment_type = 18,754
- Null trip_type = 18,754
- Null congestion_surcharge = 18,754
- Null _source_file = 0
- Null _ingested_at = 0

The six fields with 18,754 nulls were verified to belong to exactly the same 18,754 rows:

- store_and_fwd_flag
- RatecodeID
- passenger_count
- payment_type
- trip_type
- congestion_surcharge

Null-pattern verification:
- Rows where all six fields are null = 18,754
- Rows where any of the six fields is null = 18,754
- Rows with partial/mixed null pattern = 0

Therefore, the six fields share the same null-row subset.

## Date Coverage

- Earliest pickup = 2008-12-31 23:05:50
- Latest pickup = 2026-05-31 23:59:13
- Earliest dropoff = 2008-12-31 23:31:29
- Latest dropoff = 2026-06-01 21:06:14
- Pickups before March 2026 = 11
- Pickups on June 1, 2026 or later = 0

Pickup month distribution:

- 2008-12 = 2
- 2009-01 = 1
- 2026-02 = 8
- 2026-03 = 44,200
- 2026-04 = 44,243
- 2026-05 = 44,913

The 11 pickup records before the intended March–May 2026 period consist of:

- 3 records from 2008–2009
- 8 records from February 2026

Several February records occur only minutes before March 1.

## Duplicate Check

- Exact duplicate groups = 0
- Extra exact duplicate rows = 0

No exact full-row duplicates were found.

## Candidate Key Check

Tested composite:

`VendorID + lpep_pickup_datetime + lpep_dropoff_datetime + PULocationID + DOLocationID`

Results:

- Duplicate candidate-key groups = 384
- Extra rows under candidate key = 384
- Maximum occurrences = 2

Conclusion:

The tested composite is not unique, so no reliable natural trip key has been confirmed. No artificial trip ID was assumed during profiling.

## Numeric Profile

### Passenger Count

- Min = 0
- Max = 9
- Zero rows = 1,727
- Negative rows = 0

### Trip Distance

- Min = 0
- Max = 111,005.95
- Zero rows = 4,592
- Negative rows = 0

The maximum trip distance of `111,005.95` is an extreme value requiring investigation.

### Fare Amount

- Min = -250.08
- Max = 738.70
- Zero rows = 1,891
- Negative rows = 384

### Total Amount

- Min = -251.08
- Max = 742.70
- Zero rows = 228
- Negative rows = 391

Negative and zero numeric values were documented as profiling findings only. No Bronze values were cleaned or modified.

## Zone Identifier Profile

### Pickup

- Min = 1
- Max = 265
- Distinct IDs = 245
- IDs outside 1–265 = 0
- LocationID 264 (Unknown) = 331
- LocationID 265 (Outside NYC) = 113

### Dropoff

- Min = 1
- Max = 265
- Distinct IDs = 254
- IDs outside 1–265 = 0
- LocationID 264 (Unknown) = 1,591
- LocationID 265 (Outside NYC) = 602

## Referential Integrity

Against:

`nyc_mobility.nyc_bronze.bronze_taxi_zones_raw`

Results:

- Missing pickup LocationIDs = 0
- Missing dropoff LocationIDs = 0

All observed Green Taxi pickup and dropoff LocationIDs resolve to the live Bronze Taxi Zones table.

## Source and Ingestion Profile

Source files:

- March Parquet = 44,208 rows
- April Parquet = 44,238 rows
- May Parquet = 44,921 rows
- Total = 133,367 rows

All Green Taxi rows were ingested at:

`2026-09-15 19:46:52.051 UTC`

The source-file row counts differ slightly from pickup-month counts because some records inside the monthly files have pickup timestamps outside their nominal month.

Among the 11 pickups before March 2026, one February pair has:

- identical pickup timestamp
- identical dropoff timestamp
- identical pickup and dropoff LocationIDs
- opposite positive/negative fare and total values

Because the monetary values differ, the pair is not an exact duplicate. It may represent a correction/reversal pattern and should be investigated rather than automatically removed.

---

# Resource 3 — Weather

## Grain

One row = one monthly Open-Meteo API response containing arrays of hourly observations.

The 3 Bronze rows therefore represent 3 monthly responses, not 3 hourly weather observations.

## Schema

Top-level fields:

- latitude — double
- longitude — double
- generationtime_ms — double
- utc_offset_seconds — bigint
- timezone — string
- timezone_abbreviation — string
- elevation — double
- hourly_units — struct
- hourly — struct
- _source_file — string
- _ingested_at — timestamp

`hourly_units` structure:

- time — string
- temperature_2m — string
- precipitation — string
- wind_speed_10m — string

`hourly` structure:

- time — array<string>
- temperature_2m — array<double>
- precipitation — array<double>
- wind_speed_10m — array<double>

## Row Count and Top-Level Null Profile

- Total rows = 3
- Null latitude = 0
- Null longitude = 0
- Null generationtime_ms = 0
- Null utc_offset_seconds = 0
- Null timezone = 0
- Null timezone_abbreviation = 0
- Null elevation = 0
- Null hourly_units = 0
- Null hourly = 0
- Null _source_file = 0
- Null _ingested_at = 0

## Array Lengths and Date Coverage

### March 2026

- First timestamp = 2026-03-01T00:00
- Last timestamp = 2026-03-31T23:00
- time length = 744
- temperature length = 744
- precipitation length = 744
- wind length = 744

### April 2026

- First timestamp = 2026-04-01T00:00
- Last timestamp = 2026-04-30T23:00
- time length = 720
- temperature length = 720
- precipitation length = 720
- wind length = 720

### May 2026

- First timestamp = 2026-05-01T00:00
- Last timestamp = 2026-05-31T23:00
- time length = 744
- temperature length = 744
- precipitation length = 744
- wind length = 744

Total hourly positions represented = 2,208.

No array-length mismatch was observed.

## Units and Timezone

Source-reported values across all 3 monthly responses:

- time = iso8601
- temperature_2m = °C
- precipitation = mm
- wind_speed_10m = km/h
- timezone = America/New_York
- timezone_abbreviation = GMT-4
- utc_offset_seconds = -14400

These values are documented as reported by the source.

## Array Null-Element Check

For March, April, and May:

- Null time values = 0
- Null temperature values = 0
- Null precipitation values = 0
- Null wind-speed values = 0

No null elements were found inside the four hourly arrays.

## Candidate Response Identifier

Using the first hourly timestamp:

- Total responses = 3
- Distinct response starts = 3
- Duplicate response starts = 0

There is no explicit response ID.

The first hourly timestamp is a practical profiling identifier only and is not treated as a formal production primary key.

## Exact Duplicate Check

- Exact duplicate groups = 0
- Extra exact duplicate rows = 0

No exact duplicate Weather response rows were found.

## Source and Ingestion Profile

The 3 Bronze rows correspond to:

- `weather_2026-03-01_2026-03-31.json`
- `weather_2026-04-01_2026-04-30.json`
- `weather_2026-05-01_2026-05-31.json`

All three responses reported:

- latitude = 40.738136
- longitude = -74.04254
- elevation = 32
- ingestion timestamp = `2026-09-15 19:46:46.205 UTC`

---

# Overall Findings

- All 3 live Bronze tables match their expected reference counts.
- Taxi Zones contains 265 unique `LocationID` values with no exact duplicates.
- `LocationID` is a strong natural key candidate for Taxi Zones.
- Green Taxi contains no exact full-row duplicates.
- The tested Green Taxi composite candidate key is not unique.
- Green Taxi contains 11 pickup records before the intended March–May 2026 period.
- Green Taxi contains extreme, zero, and negative numeric values requiring investigation.
- All Green Taxi pickup and dropoff LocationIDs resolve to the live Bronze Taxi Zones table.
- Weather contains 3 monthly responses representing 2,208 aligned hourly positions.
- Weather arrays contain no null elements.
- No exact duplicate Weather response rows were found.
- Bronze metadata fields `_source_file` and `_ingested_at` are populated for all profiled rows.
- Bronze remained unchanged during profiling.
- No NYC DOT bonus data was included.

---

# Unresolved Findings

The following findings require investigation or downstream handling but were not modified during Bronze profiling:

1. Green Taxi has 11 pickup records before March 2026:
   - 3 from 2008–2009
   - 8 from February 2026

2. Green Taxi has an extreme maximum `trip_distance` of `111,005.95`.

3. Green Taxi contains:
   - 384 negative fare rows
   - 391 negative total amount rows

4. One February Green Taxi record pair has matching timestamps and zone identifiers but opposite positive/negative monetary values, suggesting a possible correction/reversal pattern.

5. The tested Green Taxi composite candidate key is not unique, with 384 duplicate candidate-key groups.

6. `ehail_fee` is null in all 133,367 Green Taxi rows.

7. The live Bronze Green Taxi schema does not include `cbd_congestion_fee`.

No cleaning or correction was performed because the profiling task requires Bronze to remain unchanged.

---

# Profiling Evidence and Run Information

## Actual Live Bronze Paths

The live tables were confirmed in Databricks before profiling.

- Green Taxi: `nyc_mobility.nyc_bronze.bronze_green_taxi_raw`
- Weather: `nyc_mobility.nyc_bronze.bronze_weather_raw`
- Taxi Zones: `nyc_mobility.nyc_bronze.bronze_taxi_zones_raw`

The repository documentation referenced `nyc_mobility.nyc_group_c`, but the actual live Bronze tables used for this profiling were found under `nyc_mobility.nyc_bronze`.

## Observation Time

- Databricks timestamp (UTC): `2026-09-16 08:04:52.335 UTC`
- Asia/Manila: `2026-09-16 16:04:52.335 UTC+08:00`

## Sample Evidence

All three live Bronze tables were sampled directly using read-only SQL.

### Green Taxi

```sql
SELECT *
FROM nyc_mobility.nyc_bronze.bronze_green_taxi_raw
LIMIT 20;

```

### Weather

```sql
SELECT *
FROM nyc_mobility.nyc_bronze.bronze_weather_raw
LIMIT 3;
```

### Taxi Zones

```sql
SELECT *
FROM nyc_mobility.nyc_bronze.bronze_taxi_zones_raw
LIMIT 20;
```

## Run Instructions

1. Use the live schema `nyc_mobility.nyc_bronze`.
2. Profile only the three required Bronze tables.
3. Use read-only `SELECT` and `DESCRIBE TABLE` queries.
4. Compare counts against:
   - Green Taxi: 133,367
   - Weather: 3
   - Taxi Zones: 265
5. Record findings without modifying Bronze.
6. Do not repeat acquisition or Bronze ingestion.
7. Do not include NYC DOT.

## Technical Workflow

- Feature branch: `feature/bronze-profiling-virna`
- Target branch: `development`
- Documentation: `docs/bronze_profiles/virna.md`

## Remaining Coordination

- Share final findings with Tina for model consolidation.
- Commit and push this documentation.
- Open a pull request from `feature/bronze-profiling-virna` to `development`.
- Move the work to `In review`; mark `Done` only after required review passes.