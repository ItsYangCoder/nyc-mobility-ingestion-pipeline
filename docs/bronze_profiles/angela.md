## Additional Bronze Profiling Findings

The following Bronze profiling findings from my Databricks notebook are not currently captured in the PR report.

### Green Taxi

- Core fields checked in Bronze have `0` nulls, but the following fields each have `18,754` nulls:
  - `store_and_fwd_flag`
  - `RatecodeID`
  - `passenger_count`
  - `payment_type`
  - `trip_type`
  - `congestion_surcharge`
- `ehail_fee` is null in all `133,367` rows.
- Pickup datetime range:
  - Earliest: `2008-12-31 23:05:50`
  - Latest: `2026-05-31 23:59:13`
- Dropoff datetime range:
  - Earliest: `2008-12-31 23:31:29`
  - Latest: `2026-06-01 21:06:14`
- Trip duration profile:
  - Minimum duration: `-3,420` seconds
  - Maximum duration: `147,382` seconds
  - Negative-duration rows: `1`
  - Zero-duration rows: `99`
- Numeric checks:
  - Zero-distance rows: `4,592`
  - Negative-distance rows: `0`
  - Zero-fare rows: `1,891`
  - Negative-fare rows: `384`
  - Zero-total rows: `228`
  - Negative-total rows: `391`
- The tested candidate key:
  - `VendorID + lpep_pickup_datetime + lpep_dropoff_datetime + PULocationID + DOLocationID` is not unique.
- Exact full-row duplicate groups remain `0`.
- The live Bronze Green Taxi schema does not contain `cbd_congestion_fee`, although the raw Parquet inventory lists that field.

### Weather

- Source-reported timezone: `America/New_York`
- Timezone abbreviation: `GMT-4`
- UTC offset: `-14400`
- Hourly units:
  - Time: `iso8601`
  - Temperature: `°C`
  - Precipitation: `mm`
  - Wind speed: `km/h`
- All hourly arrays are aligned for March, April, and May.
- No null elements were found in:
  - `hourly.time`
  - `hourly.temperature_2m`
  - `hourly.precipitation`
  - `hourly.wind_speed_10m`

### Taxi Zones

- `LocationID` range: `1` to `265`.
- No nulls were found in:
  - `LocationID`
  - `Borough`
  - `Zone`
  - `service_zone`
- Special lookup rows observed:
  - `264 | Unknown | N/A | N/A`
  - `265 | N/A | Outside of NYC | N/A`
- Referential-integrity checks:
  - Missing pickup-zone IDs: `0`
  - Missing dropoff-zone IDs: `0`

### Clarification on Date Coverage Metrics

The raw-file metric **"Rows Outside Expected Month"** is different from the Bronze-wide coverage check.

Raw-file results:

- March: `9`
- April: `3`
- May: `10`

Bronze-wide coverage results:

- Pickups before March 2026: `11`
- Pickups on or after June 1, 2026: `0`

These should remain labeled as separate metrics because they measure different things:

- **Rows Outside Expected Month** compares each source file against its nominal month.
- **Bronze-wide coverage** compares the combined Green Taxi dataset against the overall March-May 2026 analysis window.