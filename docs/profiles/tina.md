# Bronze Table Profile — Tina

**Profiled by:** Tina  
**Date:** 2026-09-16  
**Layer:** Bronze  
**Scope:** Green Taxi, Weather, and Taxi Zones

## Scope

This profile documents the observed structure, grain, row counts, completeness, duplicate candidates, date coverage, numeric observations, identifiers, and weather array structure of the three Bronze source tables.

No records were modified, deleted, filtered, or cleaned during profiling.

## Bronze Table Paths

- `nyc_bronze.bronze_green_taxi_raw`
- `nyc_bronze.bronze_weather_raw`
- `nyc_bronze.bronze_taxi_zones_raw`

> Table paths should be verified against Databricks Catalog Explorer before final merge.

---

## 1. Green Taxi

### Grain

One row represents one ingested Green Taxi trip record.

### Observed Results

| Check | Result |
|---|---:|
| Row count | 133,367 |
| Required-field nulls | 0 |
| Duplicate candidate groups | 384 |
| Out-of-scope dates | 11 |
| Negative `passenger_count` | 0 |
| Negative `trip_distance` | 0 |
| Negative `fare_amount` | 384 |
| Negative `total_amount` | 391 |

### Date Coverage

Observed `lpep_pickup_datetime` range:

- Minimum: `2008-12-31 23:05:50`
- Maximum: `2026-05-31 23:59:13`

The expected project coverage is March–May 2026.

The profiling identified 11 records outside the expected date scope.

### Numeric Observations

Observed ranges:

- `passenger_count`: 0–9
- `trip_distance`: 0.0–111005.95
- `fare_amount`: -250.08–738.70
- `total_amount`: -251.08–742.70

Negative values were observed in `fare_amount` and `total_amount`.

An unusually large `trip_distance` value of `111005.95` was also observed and should be reviewed downstream.

These values were documented only. No Bronze records were modified.

### Candidate Key

The following columns were used as a duplicate candidate key:

- `lpep_pickup_datetime`
- `lpep_dropoff_datetime`
- `PULocationID`
- `DOLocationID`

There were 384 duplicate candidate groups based on this combination.

This combination is treated as a candidate key for profiling purposes and is not assumed to be a guaranteed unique identifier.

### Findings

- Required fields contained no nulls.
- 384 duplicate candidate groups were detected.
- 11 records had pickup dates outside the expected March–May 2026 coverage.
- 384 records had negative `fare_amount` values.
- 391 records had negative `total_amount` values.
- No negative `passenger_count` or `trip_distance` values were detected.
- An extreme `trip_distance` value of `111005.95` was observed.

---

## 2. Taxi Zones

### Grain

One row represents one taxi zone/location reference record.

### Observed Results

| Check | Result |
|---|---:|
| Row count | 265 |
| Required-field nulls | 0 |
| Duplicate `LocationID` values | 0 |
| Unique `LocationID` values | 265 |
| `LocationID` range | 1–265 |

### Findings

- The table contains 265 rows.
- Required fields contain no nulls.
- `LocationID` values are unique.
- `LocationID` values range from 1 to 265.
- The observed row count matches the guide reference count of 265 zones.

---

## 3. Weather

### Grain

One row represents one raw weather API response.

Hourly observations are stored as nested arrays inside the `hourly` struct. Therefore, the three Bronze rows represent raw monthly API responses rather than three hourly observations.

### Observed Results

| Check | Result |
|---|---:|
| Raw response rows | 3 |
| Required-field nulls | 0 |
| Invalid coordinates | 0 |
| Hourly array length — minimum | 720 |
| Hourly array length — maximum | 744 |
| Array length mismatches | 0 |

### Timezone and Units

Observed timezone:

- `America/New_York`
- Abbreviation: `GMT-4`

Observed hourly units:

- Time: `iso8601`
- Temperature: `°C`
- Precipitation: `mm`
- Wind speed: `km/h`

The following hourly arrays had matching lengths:

- `time`
- `temperature_2m`
- `precipitation`
- `wind_speed_10m`

### Findings

- The table contains 3 raw weather response rows.
- No required-field nulls were detected.
- Coordinates were within the expected coordinate range.
- Hourly arrays contained 720–744 elements.
- No array length mismatches were detected.
- The source uses `America/New_York` timezone.
- Observed units are `iso8601`, `°C`, `mm`, and `km/h`.

---

## Overall Findings

| Table | Findings | Status |
|---|---|---|
| Green Taxi | Duplicate candidates, out-of-scope dates, negative fare/total values, and an extreme trip distance were observed. | REVIEW |
| Taxi Zones | 265 rows, unique `LocationID` values, and no required-field nulls. | PASS |
| Weather | 3 raw monthly responses with valid array structure, timezone, and units. | PASS |

## Unresolved / Downstream Review Items

### Green Taxi

1. Investigate the 384 duplicate candidate groups.
2. Investigate the 11 records outside the expected March–May 2026 coverage.
3. Review the negative `fare_amount` values.
4. Review the negative `total_amount` values.
5. Review the extreme `trip_distance` value of `111005.95`.
6. Confirm whether the candidate key is sufficient for downstream modeling.

These findings are observations only. Cleaning, deduplication, filtering, or other transformations should be handled in the appropriate downstream layer.

## Bronze Handling

No Bronze records were modified, deleted, filtered, or cleaned during this profiling task.

The purpose of this profile is to document source characteristics and quality observations for downstream investigation and Silver/model consolidation.
