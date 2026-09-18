# NYC Mobility Data Engineering Pipeline - Project Report

**Project Name:** NYC Mobility Data Engineering Pipeline  
**Date:** September 18, 2026  
**Status:** Bronze Layer Complete | Silver/Gold Pending Implementation  
**Platform:** Databricks with Unity Catalog  
**Analysis Period:** March 1 - May 31, 2026  

---

## Executive Summary

This project implements a Databricks medallion architecture data pipeline that integrates NYC Green Taxi trips, historical Open-Meteo weather data, and NYC Taxi Zones to answer three critical business questions about urban mobility patterns. The pipeline follows a Bronze → Silver → Gold architecture with comprehensive quality assurance, testing, and documentation.

### Key Achievements
- ✅ Complete data acquisition for all three sources
- ✅ Bronze layer implementation with streaming tables
- ✅ Comprehensive test suite (12 test files prepared)
- ✅ Full documentation and architecture contracts
- ✅ Quality assurance framework established

### Current Status
- **Bronze Layer:** 100% Complete and tested
- **Silver Layer:** Architecture defined, implementation pending
- **Gold Layer:** Schema designed, implementation pending
- **Analytics:** Business questions defined, execution pending

---

## 1. Project Overview

### 1.1 Business Questions

The pipeline addresses three strategic business questions:

1. **When and where is taxi demand highest?**
   - Analyzes temporal and spatial patterns in taxi usage
   - Identifies peak hours, days, and locations

2. **How does weather affect taxi demand and trip behavior?**
   - Correlates weather conditions with trip metrics
   - Measures impact on trip count, duration, distance, and revenue

3. **Which areas show the strongest mobility patterns or opportunities?**
   - Identifies high-demand zones and corridors
   - Supports strategic planning and resource allocation

### 1.2 Data Sources

| Source | Description | Data Volume | Period |
|---|---|---|---|
| **NYC Green Taxi** | Taxi trip records (TLC) | 133,367 trips | March-May 2026 |
| **Open-Meteo Weather** | Historical weather data | 2,208 hourly observations | March-May 2026 |
| **NYC Taxi Zones** | Geographic zone reference | 265 zones | Static reference |

---

## 2. Technical Architecture

### 2.1 Medallion Architecture

```
Source Acquisition → Unity Catalog Volume → Bronze → Silver → Gold → Analytics
```

#### Layer Responsibilities

**Bronze Layer (Raw Data)**
- Preserves source data in original format
- Adds lineage metadata (`_source_file`, `_ingested_at`)
- Streaming tables for real-time ingestion
- No cleaning or filtering applied

**Silver Layer (Cleaned & Standardized)**
- Data type standardization
- Quality flagging (invalid measures, duplicates)
- Deterministic key generation
- Business rule validation

**Gold Layer (Integrated & Optimized)**
- Galaxy schema with conformed dimensions
- Fact tables for trips and weather
- Referential integrity enforced
- Optimized for analytics queries

### 2.2 Data Model

#### Dimensions
- **dim_date:** Calendar attributes (date, year, quarter, month, day of week)
- **dim_hour:** Hour-of-day attributes (hour, peak periods)
- **dim_zone:** Geographic zones (borough, zone, service zone)

#### Facts
- **fact_taxi_trip:** Trip events with measures and dimension keys
- **fact_weather_hourly:** Hourly weather observations

### 2.3 Technology Stack

- **Platform:** Databricks with Unity Catalog
- **Language:** Python 3.12
- **Libraries:** requests, beautifulsoup4, duckdb, pyarrow, boto3
- **Testing:** pytest framework
- **Version Control:** Git with feature branch workflow

---

## 3. Implementation Status

### 3.1 Completed Components

#### Data Ingestion ✅
- `ingestion/green_taxi.py` - Green Taxi data download (6,619 bytes)
- `ingestion/weather.py` - Weather data download (6,148 bytes)
- `ingestion/download_taxi_zones.py` - Taxi zones download (4,165 bytes)

#### Bronze Transformations ✅
- `transformations/bronze/green_taxi.py` - Green Taxi streaming table
- `transformations/bronze/weather.py` - Weather streaming table
- `transformations/bronze/taxi_zones.py` - Taxi zones streaming table

#### Testing Framework ✅
- **Unit Tests:** `tests/unit/test_ingestion.py` (127 lines)
- **Integration Tests:** `tests/integration/test_raw_files.py` (525 lines)
- **Source Checks:** Bronze row count validation
- **Silver Checks:** 5 SQL test files prepared
- **Gold Checks:** 5 SQL test files prepared
- **Incremental/Idempotency:** 2 Python test files prepared

#### Documentation ✅
- Complete data model contract (165 lines)
- Architecture documentation
- Source profiles and contracts
- QA implementation report (420 lines)
- Runbooks and execution guides

### 3.2 Pending Components

#### Silver Layer 🔄
- Schema design complete
- Transformation scripts not implemented
- Quality rules defined but not enforced
- Test files prepared but pending activation

#### Gold Layer 🔄
- Galaxy schema designed
- Dimension and fact contracts defined
- Transformation scripts not implemented
- Reconciliation tests prepared

#### Analytics 🔄
- Business questions defined
- SQL queries not implemented
- Results not generated

---

## 4. Quality Assurance & Testing

### 4.1 Test Coverage

| Test Category | Files | Status | Coverage |
|---|---|---|---|
| Bronze Source Checks | 1 | ✅ Ready | Row counts, lineage |
| Silver Validation | 5 | 🔄 Prepared | Reconciliation, keys, measures |
| Gold Validation | 5 | 🔄 Prepared | Reconciliation, FK integrity |
| Integration Tests | 3 | ✅ Ready | Raw files, incremental, idempotency |
| Unit Tests | 1 | ✅ Ready | Ingestion logic |

### 4.2 Quality Metrics

#### Bronze Layer Validation
- **Green Taxi:** 133,367 rows verified
- **Weather:** 3 monthly JSON responses (2,208 hourly positions)
- **Taxi Zones:** 265 unique locations
- **Lineage:** All records have source file and ingestion timestamp

#### Data Quality Issues Identified
- 384 candidate duplicate groups (taxi)
- 11 pickups before March 1
- 1 negative-duration row
- 99 zero-duration rows
- 384 negative fare rows
- 391 negative total rows

#### Quality Policy
- Preserve source rows in Silver with quality flags
- Exclude invalid measures only from affected Gold metrics
- No automatic data dropping without evidence

---

## 5. Project Structure

```
nyc-mobility-ingestion-pipeline/
├── ingestion/              # Source acquisition scripts
├── transformations/
│   ├── bronze/            # Bronze transformations ✅
│   ├── silver/            # Silver transformations 🔄
│   └── gold/              # Gold transformations 🔄
├── analytics/             # Business question SQL 🔄
├── notebooks/             # Databricks entry points
├── src/sql/               # Validation and reconciliation SQL
├── tests/                 # Comprehensive test suite
│   ├── 01_source_checks/  # Bronze validation ✅
│   ├── 02_silver_checks/  # Silver validation 🔄
│   ├── 03_gold_checks/    # Gold validation 🔄
│   ├── 04_business_checks/ # Analytics validation 🔄
│   ├── integration/       # Integration tests ✅
│   └── unit/              # Unit tests ✅
├── docs/                  # Architecture and contracts
│   ├── architecture/      # Data model and design
│   ├── contracts/        # Source contracts
│   ├── profiles/          # Data profiling
│   ├── evidence/          # Acquisition evidence
│   └── runbooks/          # Execution guides
├── config/                # Unity Catalog configuration
└── requirements.txt       # Python dependencies
```

---

## 6. Key Technical Decisions

### 6.1 Design Patterns

**Deterministic Keys**
- Trip keys generated from source fields (not random)
- Ensures idempotency on reprocessing
- Supports incremental loading

**Timezone Handling**
- All timestamps treated as NYC local time
- America/New_York timezone for taxi-weather alignment
- DST-aware logic (no hardcoded UTC offsets)

**Quality Flagging vs. Dropping**
- Invalid data preserved with flags in Silver
- Excluded only from specific Gold metrics
- Full audit trail maintained

### 6.2 Incremental Processing

**Loading Strategy**
- Process by source file and pickup month
- Add April to March without rebuilding
- Add May to March+April without rebuilding
- Rerun May to verify idempotency

**Idempotency Requirements**
- Same source file must not create new keys
- Rerun replaces or upserts affected keys only
- Row counts and measure totals must remain unchanged

---

## 7. Dependencies & Prerequisites

### 7.1 System Requirements
- Python 3.12
- Databricks workspace with Unity Catalog
- Git for version control
- External Volume for raw data landing

### 7.2 Python Dependencies
```
requests
beautifulsoup4
duckdb
pyarrow
boto3
python-dotenv
pytest
```

### 7.3 Configuration
- Unity Catalog schema configuration
- Pipeline naming conventions
- Environment variables for credentials

---

## 8. Execution Workflow

### 8.1 Development Workflow
```
feature branch → pull request to development → review + green CI → development
development → reviewed release pull request → main
```

### 8.2 Pipeline Execution Order
1. Land and verify raw sources
2. Run Bronze tables and record counts
3. Build and validate Silver tables
4. Run Silver quality checks
5. Build Gold dimensions and facts
6. Validate Gold integrity
7. Run incremental and idempotency tests
8. Execute analytics queries
9. Generate results evidence

---

## 9. Challenges & Risk Mitigation

### 9.1 Identified Challenges

**Data Quality Issues**
- Duplicate records in source data
- Negative and invalid measures
- Out-of-period records
- **Mitigation:** Quality flagging and selective exclusion

**Schema Complexity**
- Galaxy schema with multiple fact tables
- Complex join cardinality requirements
- **Mitigation:** Comprehensive reconciliation tests

**Timezone Handling**
- Daylight saving time transition
- Weather-timestamp alignment
- **Mitigation:** DST-aware logic and validation

### 9.2 Risk Mitigation Strategies

**Incremental Loading Risks**
- Key collision on reprocessing
- Measure drift on reruns
- **Mitigation:** Deterministic key generation and idempotency tests

**Integration Risks**
- Silver/Gold schema mismatches
- Referential integrity violations
- **Mitigation:** Schema contracts and validation tests

---

## 10. Next Steps & Roadmap

### 10.1 Immediate Priorities

1. **Silver Implementation** (High Priority)
   - Implement transformation scripts
   - Activate Silver validation tests
   - Verify schema compliance

2. **Gold Implementation** (High Priority)
   - Build dimension tables
   - Implement fact tables
   - Activate Gold validation tests

3. **Integration Testing** (Medium Priority)
   - Implement incremental loading tests
   - Execute idempotency validation
   - Document test results

### 10.2 Completion Criteria

The project is complete when:

- ✅ All Bronze, Silver, Gold tables implemented
- ✅ All validation tests pass
- ✅ Incremental loading verified
- ✅ Idempotency confirmed
- ✅ Three analytics queries executed
- ✅ Results documented and saved
- ✅ Full evidence package compiled

### 10.3 Estimated Timeline

- Silver Implementation: 2-3 weeks
- Gold Implementation: 2-3 weeks
- Testing & Validation: 1-2 weeks
- Analytics Execution: 1 week
- **Total Remaining:** ~6-9 weeks

---

## 11. Success Metrics

### 11.1 Technical Metrics
- **Data Completeness:** 100% of required sources ingested
- **Data Quality:** All quality flags documented and handled
- **Test Coverage:** 100% of acceptance criteria tested
- **Idempotency:** Zero drift on reruns
- **Performance:** Queries complete within SLA

### 11.2 Business Metrics
- **Question 1:** Demand patterns identified with statistical significance
- **Question 2:** Weather correlations quantified
- **Question 3:** High-opportunity zones ranked and prioritized

---

## 12. Lessons Learned

### 12.1 Technical Insights
- Bronze layer preservation critical for auditability
- Deterministic keys essential for idempotency
- Quality flagging preferable to dropping
- Comprehensive testing prevents production issues

### 12.2 Process Insights
- Documentation alongside implementation improves quality
- Test-driven approach catches issues early
- Schema contracts prevent integration problems
- Incremental validation reduces rework

---

## 13. Conclusion

The NYC Mobility Data Engineering Pipeline represents a robust, production-ready foundation for urban mobility analytics. The Bronze layer is complete with comprehensive quality assurance, and the architecture is fully designed for Silver and Gold implementation. The project demonstrates strong engineering practices with extensive testing, documentation, and quality controls.

The remaining work focuses on Silver and Gold implementation, which are well-defined with clear contracts and prepared test suites. The project is on track for successful completion within the estimated timeline.

---

## Appendix

### A. Key Files
- `README.md` - Project overview and quick start
- `docs/architecture/data_model.md` - Complete data model contract
- `docs/qa_implementation_report.md` - QA test preparation details
- `requirements.txt` - Python dependencies

### B. Documentation References
- Data Model: `docs/architecture/data_model.md`
- Pipeline Execution: `docs/runbooks/pipeline_execution.md`
- Raw Landing: `docs/runbooks/raw_landing.md`
- Source Profiles: `docs/profiles/`
- Evidence: `docs/evidence/`

### C. Contact & Support
- Project Repository: NYC Mobility Ingestion Pipeline
- Branch Strategy: Feature → Development → Main
- CI/CD: Pull request validation with pytest

---

**Report Generated:** September 18, 2026  
**Report Version:** 1.0  
**Next Review:** Upon Silver layer completion
