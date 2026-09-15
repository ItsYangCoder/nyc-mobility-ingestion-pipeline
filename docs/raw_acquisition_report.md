# Raw Data Acquisition & Verification Report

## 1. Purpose

This report documents the acquisition and local verification of the raw datasets required for the NYC Mobility Ingestion Pipeline.

The verification focuses on:

* File existence and completeness
* File readability
* Expected file formats
* Expected schema/columns
* Date coverage
* Row counts
* Duplicate and missing key indicators
* Detection of HTML/error responses saved as data
* Source and retrieval metadata

**Raw records are not cleaned, transformed, or deleted during verification.**

---

## 2. Required Raw Datasets

| Dataset | Expected Coverage | Format | Expected Raw File | Status |
| --- | --- | --- | --- | --- |
| Green Taxi | March 2026 | Parquet | `green_tripdata_2026-03.parquet` | NOT VERIFIED |
| Green Taxi | April 2026 | Parquet | `green_tripdata_2026-04.parquet` | NOT VERIFIED |
| Green Taxi | May 2026 | Parquet | `green_tripdata_2026-05.parquet` | NOT VERIFIED |
| Open-Meteo Weather | March 2026 | JSON | `weather_2026-03-01_2026-03-31.json` | NOT VERIFIED |
| Open-Meteo Weather | April 2026 | JSON | `weather_2026-04-01_2026-04-30.json` | NOT VERIFIED |
| Open-Meteo Weather | May 2026 | JSON | `weather_2026-05-01_2026-05-31.json` | NOT VERIFIED |
| Taxi Zones | Reference data | CSV | `taxi_zone_lookup.csv` | NOT VERIFIED |

---

## 3. Green Taxi Verification

### March 2026

* File exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* Parquet is readable: NOT VERIFIED
* Required columns present: NOT VERIFIED
* Row count recorded: NOT VERIFIED
* Pickup date coverage verified: NOT VERIFIED
* Duplicate key indicators checked: NOT VERIFIED
* Missing key values checked: NOT VERIFIED
* Source URL recorded: NOT VERIFIED
* Retrieval metadata recorded: NOT VERIFIED

**Status: NOT VERIFIED**

### April 2026

* File exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* Parquet is readable: NOT VERIFIED
* Required columns present: NOT VERIFIED
* Row count recorded: NOT VERIFIED
* Pickup date coverage verified: NOT VERIFIED
* Duplicate key indicators checked: NOT VERIFIED
* Missing key values checked: NOT VERIFIED
* Source URL recorded: NOT VERIFIED
* Retrieval metadata recorded: NOT VERIFIED

**Status: NOT VERIFIED**

### May 2026

* File exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* Parquet is readable: NOT VERIFIED
* Required columns present: NOT VERIFIED
* Row count recorded: NOT VERIFIED
* Pickup date coverage verified: NOT VERIFIED
* Duplicate key indicators checked: NOT VERIFIED
* Missing key values checked: NOT VERIFIED
* Source URL recorded: NOT VERIFIED
* Retrieval metadata recorded: NOT VERIFIED

**Status: NOT VERIFIED**

---

## 4. Open-Meteo Weather Verification

### March 2026

* JSON file exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* JSON is valid/readable: NOT VERIFIED
* `hourly` data present: NOT VERIFIED
* Required weather fields present: NOT VERIFIED
* Weather array lengths match timestamps: NOT VERIFIED
* Date coverage verified: NOT VERIFIED
* Duplicate timestamps checked: NOT VERIFIED
* Missing dates checked: NOT VERIFIED
* API request parameters recorded: NOT VERIFIED
* Retrieval timestamp recorded: NOT VERIFIED

**Status: NOT VERIFIED**

### April 2026

* JSON file exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* JSON is valid/readable: NOT VERIFIED
* `hourly` data present: NOT VERIFIED
* Required weather fields present: NOT VERIFIED
* Weather array lengths match timestamps: NOT VERIFIED
* Date coverage verified: NOT VERIFIED
* Duplicate timestamps checked: NOT VERIFIED
* Missing dates checked: NOT VERIFIED
* API request parameters recorded: NOT VERIFIED
* Retrieval timestamp recorded: NOT VERIFIED

**Status: NOT VERIFIED**

### May 2026

* JSON file exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* JSON is valid/readable: NOT VERIFIED
* `hourly` data present: NOT VERIFIED
* Required weather fields present: NOT VERIFIED
* Weather array lengths match timestamps: NOT VERIFIED
* Date coverage verified: NOT VERIFIED
* Duplicate timestamps checked: NOT VERIFIED
* Missing dates checked: NOT VERIFIED
* API request parameters recorded: NOT VERIFIED
* Retrieval timestamp recorded: NOT VERIFIED

**Status: NOT VERIFIED**

---

## 5. NYC Taxi Zones Verification

* CSV file exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* CSV is readable: NOT VERIFIED
* Required columns present: NOT VERIFIED
* Row count recorded: NOT VERIFIED
* `LocationID` duplicates checked: NOT VERIFIED
* Missing `LocationID` checked: NOT VERIFIED
* Source URL recorded: NOT VERIFIED
* Retrieval timestamp recorded: NOT VERIFIED
* Error response detection completed: NOT VERIFIED

**Status: NOT VERIFIED**

---

## 6. Findings

No final findings have been recorded yet because the required raw datasets have not been verified locally.

Once acquisition is complete, findings should include:

* Missing files
* Unexpected duplicate records/keys or timestamps
* Missing key values or dates
* Unexpected row counts
* Schema differences
* Unreadable/corrupted files
* HTML/error responses saved instead of the expected dataset
* Incomplete date coverage
* Missing acquisition metadata

These findings will be reported to the corresponding source owner for rerun or correction.

---

## 7. Failure Handling

If a dataset fails verification:

1. Record the failed check and supporting evidence.
2. Notify the corresponding source/acquisition owner.
3. Request a rerun or correction of the acquisition process.
4. Re-run the local verification checks.
5. Update this report with the final result.

Raw records will not be manually cleaned or deleted as part of acquisition verification.

---

## 8. Verification Command

Run the automated raw-data checker from the project root:

```bash
python tests/test_raw_files.py
```

The checker is intended to be run after the required raw datasets have been acquired.

---

## 9. Final Acceptance Criteria

The raw-data acquisition is considered ready for the next pipeline stage when:

* All required datasets are present.
* Files are non-empty and readable.
* File formats match expectations.
* Required columns are present.
* Required date coverage is complete.
* Duplicate/missing key findings have been recorded.
* No HTML/error response has been saved as a dataset.
* Source URLs and retrieval metadata are documented.
* Any acquisition failures have been resolved or explicitly reported.

**Overall Status: NOT VERIFIED — awaiting raw-data acquisition.**
