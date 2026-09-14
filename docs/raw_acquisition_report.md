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

| Dataset                       | Expected Coverage       | Format  | Status       |
| ----------------------------- | ----------------------- | ------- | ------------ |
| NYC Green Taxi                | March 2026              | Parquet | NOT VERIFIED |
| NYC Green Taxi                | April 2026              | Parquet | NOT VERIFIED |
| NYC Green Taxi                | May 2026                | Parquet | NOT VERIFIED |
| Open-Meteo Historical Weather | Required project period | JSON    | NOT VERIFIED |
| NYC Taxi Zones                | Reference dataset       | CSV     | NOT VERIFIED |

---

## 3. Green Taxi Verification

### March 2026

* File exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* Parquet is readable: NOT VERIFIED
* Expected columns present: NOT VERIFIED
* Row count recorded: NOT VERIFIED
* Duplicate key check: NOT VERIFIED
* Date coverage verified: NOT VERIFIED
* Source URL recorded: NOT VERIFIED
* Retrieval metadata recorded: NOT VERIFIED

**Status: NOT VERIFIED**

### April 2026

* File exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* Parquet is readable: NOT VERIFIED
* Expected columns present: NOT VERIFIED
* Row count recorded: NOT VERIFIED
* Duplicate key check: NOT VERIFIED
* Date coverage verified: NOT VERIFIED
* Source URL recorded: NOT VERIFIED
* Retrieval metadata recorded: NOT VERIFIED

**Status: NOT VERIFIED**

### May 2026

* File exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* Parquet is readable: NOT VERIFIED
* Expected columns present: NOT VERIFIED
* Row count recorded: NOT VERIFIED
* Duplicate key check: NOT VERIFIED
* Date coverage verified: NOT VERIFIED
* Source URL recorded: NOT VERIFIED
* Retrieval metadata recorded: NOT VERIFIED

**Status: NOT VERIFIED**

---

## 4. Open-Meteo Weather Verification

* JSON file exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* JSON is valid/readable: NOT VERIFIED
* Expected weather fields present: NOT VERIFIED
* Required date coverage present: NOT VERIFIED
* Record count recorded: NOT VERIFIED
* Duplicate dates checked: NOT VERIFIED
* Missing dates checked: NOT VERIFIED
* API URL/request parameters recorded: NOT VERIFIED
* Retrieval timestamp recorded: NOT VERIFIED
* Error response detection completed: NOT VERIFIED

**Status: NOT VERIFIED**

---

## 5. NYC Taxi Zones Verification

* CSV file exists: NOT VERIFIED
* File is non-empty: NOT VERIFIED
* CSV is readable: NOT VERIFIED
* Expected columns present: NOT VERIFIED
* Row count recorded: NOT VERIFIED
* `LocationID` duplicates checked: NOT VERIFIED
* Missing `LocationID` checked: NOT VERIFIED
* Source URL recorded: NOT VERIFIED
* Retrieval timestamp recorded: NOT VERIFIED
* Error response detection completed: NOT VERIFIED

**Status: NOT VERIFIED**

---

## 6. Findings

No final findings have been recorded yet because the raw datasets have not been verified locally.

Once acquisition is complete, findings should include:

* Missing files
* Unexpected duplicate records/keys
* Missing keys or dates
* Unexpected row counts
* Schema differences
* Unreadable/corrupted files
* HTML/error responses saved instead of the expected dataset
* Incomplete date coverage

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
