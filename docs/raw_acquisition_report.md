# Raw Data Acquisition Verification Report

**Owner:** @crisstin92-ui  
**Verification Date:** September 16, 2026  
**Scope:** Local raw-data acquisition and verification  
**Sources:** Green Taxi, Weather, Taxi Zones

---

## 1. Objective

This report documents the local verification of the required raw datasets for the NYC mobility ingestion pipeline.

The verification covers file availability, readability, non-empty content, expected date coverage, schema, row counts, missing and duplicate keys, source URLs, and retrieval metadata.

Raw records were not cleaned, deleted, or modified during verification.

---

## 2. Verification Summary

| Source | Format | Coverage | Rows / Records | Missing | Duplicates | Status |
|---|---|---|---:|---:|---:|---|
| Green Taxi | Parquet | Mar–May 2026 | 133,367 | 0 | Candidate-key duplicates found | PASS |
| Weather | JSON/API | Mar–May 2026 | 2,208 hourly positions | 0 | 0 | PASS |
| Taxi Zones | CSV | Reference | 265 | 0 | 0 | PASS |

---

## 3. Green Taxi Verification

### Files Verified

- March 2026 Green Taxi Parquet
- April 2026 Green Taxi Parquet
- May 2026 Green Taxi Parquet

### Results

| Month | Rows | Missing Candidate Keys | Duplicate Candidate Keys | Rows Outside Expected Month |
|---|---:|---:|---:|---:|
| March 2026 | 44,208 | 0 | 112 | 9 |
| April 2026 | 44,238 | 0 | 154 | 3 |
| May 2026 | 44,921 | 0 | 118 | 10 |

**Total rows:** 133,367

### Verification Findings

- All expected monthly files were present.
- All Parquet files were readable.
- All files were non-empty.
- Required columns were present.
- Pickup datetime values were checked.
- Expected monthly coverage was checked.
- No missing candidate-key rows were found.
- Duplicate candidate keys were recorded as findings.
- Rows outside the expected monthly coverage were recorded as findings.
- Raw records were not cleaned or deleted.

### Duplicate Key Note

The duplicate counts above refer to the selected **candidate key**, not exact full-row duplicates.

Therefore, these findings do not necessarily indicate exact duplicate records. A separate Bronze profiling check found no exact full-row duplicates.

### Owner Follow-Up

The Green Taxi source owner was asked to rerun/check the acquisition process and verify whether the observed out-of-month records and candidate-key duplicates are expected or related to incomplete/unnecessary duplicate downloads.

---

## 4. Weather Verification

### Files / Responses Verified

- March 2026
- April 2026
- May 2026

### Results

| Month | Hourly Positions | Missing Required Fields | Duplicate Timestamps |
|---|---:|---:|---:|
| March 2026 | 744 | 0 | 0 |
| April 2026 | 720 | 0 | 0 |
| May 2026 | 744 | 0 | 0 |

**Total hourly positions:** 2,208

### Verification Findings

- All three monthly responses were present.
- JSON responses were readable.
- Responses were non-empty.
- Required weather fields were present.
- Weather arrays had matching lengths.
- Timestamps were parseable.
- No duplicate timestamps were found.
- March–May 2026 coverage was verified.
- Source and retrieval metadata were recorded.

**Status:** PASS

---

## 5. Taxi Zones Verification

### File Verified

- `taxi_zone_lookup.csv`

### Results

- **Rows:** 265
- **Unique `LocationID`s:** 265
- **Missing `LocationID`:** 0
- **Duplicate `LocationID`:** 0

### Verification Findings

- CSV was present and readable.
- File was non-empty.
- Required columns were present.
- `LocationID` completeness was verified.
- `LocationID` uniqueness was verified.
- Source URL and retrieval metadata were recorded.

**Status:** PASS

---

## 6. Retrieval Metadata and Source Inventory

The acquisition outputs include source/retrieval metadata where applicable.

The Green Taxi inventory records:

- source URL
- local filename
- file size
- row count
- columns
- retrieval timestamp

Weather outputs include source/API and retrieval metadata.

Taxi Zones includes source and retrieval metadata.

The accepted file inventory is represented by:

`docs/green_taxi_inventory.csv`

---

## 7. Raw-Data Quality Findings

The verification identified the following findings:

### Green Taxi

- March: 9 rows outside the expected month
- April: 3 rows outside the expected month
- May: 10 rows outside the expected month
- Candidate-key duplicates:
  - March: 112
  - April: 154
  - May: 118
- Missing candidate-key rows: 0

These findings were recorded only. No raw records were cleaned or deleted.

### Context from Bronze Profiling

A separate Bronze profiling check reported:

- Green Taxi: 133,367 rows
- No exact full-row duplicates
- 11 Green Taxi pickups before March 2026
- Maximum `trip_distance`: 111,005.95
- 384 negative fare rows
- 391 negative total amount rows
- All PU/DO LocationIDs resolve to Taxi Zones
- Weather: 3 monthly responses and 2,208 aligned hourly positions
- Taxi Zones: 265 rows and 265 unique `LocationID`s

These Bronze findings are downstream profiling results and are not used to modify the raw datasets.

---

## 8. Error / Download Verification

The required raw files were successfully opened and profiled locally.

No obvious HTML/error-page content was detected in the verified dataset outputs.

No incomplete download was confirmed from the current checks.

Green Taxi anomalies were reported to the source owner for rerun/review as required.

---

## 9. Reproducibility

### Verification Script

`tests/test_raw_files.py`

### Run Command

```bash
py tests/test_raw_files.py