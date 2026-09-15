# NYC Mobility Pipeline — Raw Data Acquisition Checklist

## Purpose

This checklist verifies that the raw datasets acquired for the NYC Mobility Pipeline are complete, readable, and suitable for the Bronze/raw stage before further processing.

**Scope:** Raw data acquisition and verification only.
**Deadline:** September 17, 2026 EOD (Asia/Manila)

---

## 1. Expected Raw Sources

### A. Green Taxi Trip Records

**Source:** NYC Taxi & Limousine Commission (TLC)

Expected coverage:

* [ ] March 2026
* [ ] April 2026
* [ ] May 2026

Expected format:

* [ ] Parquet

Expected raw paths:

* `data/raw/green_taxi/green_tripdata_2026-03.parquet`
* `data/raw/green_taxi/green_tripdata_2026-04.parquet`
* `data/raw/green_taxi/green_tripdata_2026-05.parquet`

Verification:

* [ ] File exists for each expected month
* [ ] File is not empty
* [ ] File can be opened successfully
* [ ] File is valid Parquet
* [ ] Required columns are present
* [ ] Row count is recorded
* [ ] Pickup date coverage is recorded
* [ ] Duplicate/missing key indicators are recorded
* [ ] Source URL is recorded in the acquisition inventory
* [ ] Retrieval metadata is recorded in the acquisition inventory
* [ ] File is not an HTML/error response saved with a `.parquet` extension

**Status:** ☐ PASS ☐ FAIL ☐ PENDING

**Findings/Notes:**

---

### B. Historical Weather Data

**Source:** Open-Meteo Historical Weather API

Expected coverage:

* [ ] March 2026
* [ ] April 2026
* [ ] May 2026

Expected format:

* [ ] JSON

Expected raw paths:

* `data/raw/weather/weather_2026-03-01_2026-03-31.json`
* `data/raw/weather/weather_2026-04-01_2026-04-30.json`
* `data/raw/weather/weather_2026-05-01_2026-05-31.json`

Expected hourly fields:

* `time`
* `temperature_2m`
* `precipitation`
* `wind_speed_10m`

Verification:

* [ ] File exists for each expected month
* [ ] Response is not empty
* [ ] Response is valid JSON
* [ ] `hourly` data is present
* [ ] Expected weather fields are present
* [ ] Each weather array matches the timestamp count
* [ ] Expected date coverage is present
* [ ] Duplicate/missing timestamp/date findings are recorded
* [ ] API request parameters are recorded in metadata
* [ ] Retrieval timestamp is recorded in metadata
* [ ] Error response was not saved as valid data

**Status:** ☐ PASS ☐ FAIL ☐ PENDING

**Findings/Notes:**

---

### C. Taxi Zones

**Source:** NYC Taxi & Limousine Commission (TLC)

Expected format:

* [ ] CSV

Expected raw path:

* `data/raw/taxi_zones/taxi_zone_lookup.csv`

Required columns:

* `LocationID`
* `Borough`
* `Zone`

Verification:

* [ ] File exists
* [ ] File is not empty
* [ ] File can be opened successfully
* [ ] File is valid CSV
* [ ] Required columns are present
* [ ] Row count is recorded
* [ ] Duplicate/missing `LocationID` findings are recorded
* [ ] Source URL is recorded
* [ ] Retrieval metadata is recorded
* [ ] File is not an HTML/error response saved as `.csv`

**Status:** ☐ PASS ☐ FAIL ☐ PENDING

**Findings/Notes:**

---

## 2. File-Level Verification

For every acquired raw file:

* [ ] Expected file exists
* [ ] Filename follows the expected naming convention
* [ ] File size is greater than zero
* [ ] File can be opened using the expected format reader
* [ ] File contains records
* [ ] File extension matches the actual content
* [ ] File is not an HTML error page or other error response
* [ ] Source URL is documented
* [ ] Retrieval timestamp/metadata is documented

---

## 3. Schema Verification

For each dataset:

* [ ] Actual columns were recorded
* [ ] Required columns are present
* [ ] Unexpected schema changes are documented
* [ ] Data types can be read successfully
* [ ] Schema issues are reported to the source owner

**Important:** Do not clean, delete, or modify raw records during this verification stage.

---

## 4. Record-Level Findings

Record findings without modifying the raw data.

Check for:

* [ ] Duplicate keys or duplicate timestamp indicators
* [ ] Missing key values
* [ ] Unexpected nulls in important fields
* [ ] Unexpected date coverage
* [ ] Unexpected row counts
* [ ] Other obvious acquisition issues

**Finding:**

**Affected file/source:**

**Evidence:**

**Reported to source owner:** ☐ Yes ☐ No ☐ N/A

---

## 5. Error and Incomplete Download Check

A download should be considered failed or needing rerun if:

* [ ] File is empty
* [ ] File cannot be parsed
* [ ] File contains an HTML/error response instead of the expected format
* [ ] Expected date/month is missing
* [ ] Expected columns are missing
* [ ] Weather arrays do not match timestamp count
* [ ] Download appears incomplete
* [ ] Retrieval metadata/source URL is missing
* [ ] Other acquisition error is observed

When a failure is found:

1. Record the failure and evidence.
2. Notify the responsible source/acquisition owner.
3. Ask the owner to rerun the acquisition script.
4. Re-run verification after the corrected file is available.

---

## 6. Raw Data Inventory

| Source | Expected Period | Format | File | Rows | Status | Findings |
| --- | --- | --- | --- | ---: | --- | --- |
| Green Taxi | March 2026 | Parquet | `green_tripdata_2026-03.parquet` | TBD | PENDING | |
| Green Taxi | April 2026 | Parquet | `green_tripdata_2026-04.parquet` | TBD | PENDING | |
| Green Taxi | May 2026 | Parquet | `green_tripdata_2026-05.parquet` | TBD | PENDING | |
| Weather | March 2026 | JSON | `weather_2026-03-01_2026-03-31.json` | TBD | PENDING | |
| Weather | April 2026 | JSON | `weather_2026-04-01_2026-04-30.json` | TBD | PENDING | |
| Weather | May 2026 | JSON | `weather_2026-05-01_2026-05-31.json` | TBD | PENDING | |
| Taxi Zones | Reference data | CSV | `taxi_zone_lookup.csv` | TBD | PENDING | |

---

## 7. Final Acceptance

A raw dataset can be marked **PASS** when:

* [ ] Expected file/data is present
* [ ] Expected coverage is present
* [ ] File is non-empty and readable
* [ ] Expected schema is available
* [ ] Row count has been recorded
* [ ] Duplicate/missing key findings have been recorded
* [ ] Source URL is documented
* [ ] Retrieval metadata is documented
* [ ] No acquisition error was detected

### Overall Status

**Raw Acquisition Verification:** ☐ PASS ☐ FAIL ☐ PENDING

**Verified by:** @crisstin92-ui

**Verification date:** __________

**Summary:**

---
