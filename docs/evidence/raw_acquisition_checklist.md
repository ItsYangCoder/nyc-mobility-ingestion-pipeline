# Raw Data Acquisition Checklist

**Scope:** Local raw-data acquisition and verification  
**Sources:** Green Taxi, Weather, Taxi Zones  
**Verification Date:** September 16, 2026

---

## 1. Green Taxi — Parquet

### File and Acquisition
- [x] Expected March 2026 file exists
- [x] Expected April 2026 file exists
- [x] Expected May 2026 file exists
- [x] Expected filenames verified
- [x] Source URL recorded
- [x] Retrieval metadata recorded
- [x] File sizes recorded
- [x] Raw files stored in the expected raw-data directory
- [x] No credentials or secrets included

### Readability and File Integrity
- [x] March Parquet file opened using Python
- [x] April Parquet file opened using Python
- [x] May Parquet file opened using Python
- [x] Files are non-empty
- [x] Files are readable as Parquet
- [x] No obvious HTML/error-page content was saved as dataset content

### Schema and Content
- [x] Required columns are present
- [x] Column lists recorded
- [x] Row counts recorded
- [x] Pickup datetime values checked
- [x] Expected monthly coverage checked
- [x] Records outside the expected month reported
- [x] Missing candidate-key values checked
- [x] Duplicate candidate keys checked
- [x] Findings recorded without modifying raw records

### Green Taxi Results

| Month | Rows | Missing Candidate Keys | Duplicate Candidate Keys | Rows Outside Expected Month |
|---|---:|---:|---:|---:|
| March 2026 | 44,208 | 0 | 112 | 9 |
| April 2026 | 44,238 | 0 | 154 | 3 |
| May 2026 | 44,921 | 0 | 118 | 10 |

**Status:** PASS

---

## 2. Weather — JSON / API

### File and Acquisition
- [x] March 2026 response exists
- [x] April 2026 response exists
- [x] May 2026 response exists
- [x] API/source URL recorded
- [x] Retrieval metadata recorded
- [x] Raw JSON files stored in the expected raw-data directory
- [x] No credentials or secrets included

### Readability and File Integrity
- [x] JSON responses opened using Python
- [x] JSON responses are readable
- [x] Responses are non-empty
- [x] Expected hourly data is present
- [x] No obvious API/error-page response was saved as raw data

### Schema and Content
- [x] Required weather fields are present
- [x] Timestamp array is present
- [x] Weather arrays have matching lengths
- [x] Timestamps can be parsed
- [x] Duplicate timestamps checked
- [x] Required fields checked
- [x] Monthly coverage verified
- [x] Retrieval metadata verified

### Weather Results

| Month | Hourly Positions | Missing Required Fields | Duplicate Timestamps |
|---|---:|---:|---:|
| March 2026 | 744 | 0 | 0 |
| April 2026 | 720 | 0 | 0 |
| May 2026 | 744 | 0 | 0 |

**Total hourly positions:** 2,208

**Status:** PASS

---

## 3. Taxi Zones — CSV

### File and Acquisition
- [x] Expected CSV file exists
- [x] Source URL recorded
- [x] Retrieval metadata recorded
- [x] File size recorded
- [x] Raw CSV stored in the expected raw-data directory
- [x] No credentials or secrets included

### Readability and File Integrity
- [x] CSV opened using Python
- [x] CSV is readable
- [x] CSV is non-empty
- [x] No obvious error-page content was saved as CSV

### Schema and Content
- [x] Required columns are present
- [x] Column list recorded
- [x] Row count recorded
- [x] Missing `LocationID` values checked
- [x] Duplicate `LocationID` values checked

### Taxi Zones Results

- [x] 265 rows verified
- [x] 265 unique `LocationID`s verified
- [x] Missing `LocationID`: 0
- [x] Duplicate `LocationID`: 0

**Status:** PASS

---

## 4. Cross-Source Acquisition Checks

- [x] All required source datasets are present
- [x] Green Taxi March–May 2026 coverage verified
- [x] Weather March–May 2026 coverage verified
- [x] Taxi Zones reference file verified
- [x] Row counts recorded
- [x] Columns recorded
- [x] Source URLs recorded
- [x] Retrieval metadata recorded
- [x] Missing-key findings recorded
- [x] Duplicate-key findings recorded
- [x] Acquisition anomalies documented
- [x] Raw records were not cleaned or deleted
- [x] Raw datasets and credentials are excluded from Git

---

## 5. Source Owner Follow-Up

- [x] Green Taxi findings identified
- [x] Green Taxi source owner asked to rerun/check the acquisition script
- [x] Owner asked to check for incomplete downloads
- [x] Owner asked to check for unnecessary duplicate files
- [ ] Owner rerun results documented, if applicable

---

## 6. Verification and Reproducibility

- [x] Verification script saved under `tests/`
- [x] Exact run command documented
- [x] Verification completed locally using Python
- [x] Results recorded in the acquisition report
- [x] Overall PASS/FAIL status recorded

### Run Command

```bash
python tests/integration/verify_raw_files.py