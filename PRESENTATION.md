# NYC Mobility Data Engineering Pipeline
## Project Presentation

---

## Slide 1: Title Slide

**NYC Mobility Data Engineering Pipeline**

*A Databricks Medallion Architecture for Urban Mobility Analytics*

**September 18, 2026**

---

## Slide 2: Executive Summary

### Project Overview![alt text](image.png)
- **Platform:** Databricks with Unity Catalog
- **Architecture:** Bronze → Silver → Gold medallion pipeline
- **Period:** March - May 2026
- **Status:** Bronze Complete | Silver/Gold In Progress

### Key Achievements
✅ Complete data acquisition (3 sources)  
✅ Bronze layer implemented and tested  
✅ Comprehensive QA framework (12 test files)  
✅ Full documentation and architecture contracts  

### Business Value
Answers 3 critical questions:
1. When and where is taxi demand highest?
2. How does weather affect taxi demand?
3. Which areas show the strongest mobility patterns?

---

## Slide 3: Business Questions

### Question 1: Demand Patterns
**"When and where is taxi demand highest?"**
- Analyze temporal patterns (hourly, daily, weekly)
- Identify spatial hotspots and zones
- Support resource allocation decisions

### Question 2: Weather Impact
**"How does weather affect taxi demand and trip behavior?"**
- Correlate weather conditions with trip metrics
- Measure impact on count, duration, distance, revenue
- Enable weather-aware forecasting

### Question 3: Mobility Opportunities
**"Which areas show the strongest mobility patterns or opportunities?"**
- Rank zones by demand intensity
- Identify high-opportunity corridors
- Support strategic planning

---

## Slide 4: Data Sources

### NYC Green Taxi (TLC)
- **Volume:** 133,367 trips
- **Period:** March-May 2026
- **Fields:** Pickup/dropoff, distance, fare, passenger count
- **Quality:** 384 candidate duplicates, some invalid measures

### Open-Meteo Weather
- **Volume:** 2,208 hourly observations
- **Period:** March-May 2026 (92 days)
- **Fields:** Temperature, precipitation, wind speed
- **Quality:** Complete coverage, no gaps

### NYC Taxi Zones
- **Volume:** 265 geographic zones
- **Type:** Static reference data
- **Fields:** Borough, zone, service zone
- **Quality:** 100% complete, unique keys

---

## Slide 5: Technical Architecture

### Medallion Architecture

```
Source Acquisition → Unity Catalog Volume → Bronze → Silver → Gold → Analytics
```

### Layer Responsibilities

**Bronze (Raw)**
- Preserves source data
- Adds lineage metadata
- Streaming tables
- No cleaning

**Silver (Cleaned)**
- Type standardization
- Quality flagging
- Deterministic keys
- Business validation

**Gold (Integrated)**
- Galaxy schema
- Conformed dimensions
- Optimized for analytics
- Referential integrity

---

## Slide 6: Data Model

### Dimensions
- **dim_date:** Calendar attributes (date, year, quarter, month, day of week)
- **dim_hour:** Hour-of-day attributes (hour, peak periods)
- **dim_zone:** Geographic zones (borough, zone, service zone)

### Facts
- **fact_taxi_trip:** Trip events with measures and dimension keys
- **fact_weather_hourly:** Hourly weather observations

### Key Relationships
- Taxi trips → Date, Hour, Zone dimensions
- Weather → Date, Hour dimensions
- Taxi trips ← Weather (left join by pickup hour)

---

## Slide 7: Implementation Status

### ✅ Completed
- **Data Ingestion:** All 3 sources downloading and validated
- **Bronze Layer:** 3 streaming tables operational
- **Testing Framework:** 12 test files prepared
- **Documentation:** Complete architecture and contracts
- **Quality Assurance:** Bronze validation passing

### 🔄 In Progress
- **Silver Layer:** Schema designed, scripts pending
- **Gold Layer:** Galaxy schema designed, implementation pending
- **Analytics:** Business questions defined, SQL pending

### 📋 Next Steps
1. Implement Silver transformations (2-3 weeks)
2. Implement Gold transformations (2-3 weeks)
3. Execute analytics queries (1 week)
4. Final validation and documentation (1-2 weeks)

---

## Slide 8: Quality Assurance

### Test Coverage

| Layer | Test Files | Status |
|-------|-----------|--------|
| Bronze | 1 | ✅ Passing |
| Silver | 5 | 🔄 Prepared |
| Gold | 5 | 🔄 Prepared |
| Integration | 3 | ✅ Ready |
| Unit | 1 | ✅ Passing |

### Quality Metrics
- **Bronze Validation:** 133,367 taxi rows verified
- **Lineage:** 100% of records have source metadata
- **Duplicate Detection:** 384 candidate groups identified
- **Date Coverage:** Complete March-May coverage
- **Key Uniqueness:** All natural keys verified

### Quality Policy
- Preserve source data with flags
- Exclude only from specific metrics
- Maintain full audit trail
- No automatic dropping without evidence

---

## Slide 9: Project Structure

```
nyc-mobility-ingestion-pipeline/
├── ingestion/              # Source acquisition ✅
├── transformations/
│   ├── bronze/            # Bronze layer ✅
│   ├── silver/            # Silver layer 🔄
│   └── gold/              # Gold layer 🔄
├── analytics/             # Business questions 🔄
├── tests/                 # Test suite ✅
├── docs/                  # Documentation ✅
├── config/                # Configuration ✅
└── notebooks/             # Databricks entry ✅
```

### Key Directories
- **ingestion/**: Data download scripts
- **transformations/**: Medallion layer logic
- **tests/**: Comprehensive validation
- **docs/**: Architecture, contracts, evidence
- **analytics/**: Business question SQL

---

## Slide 10: Technical Decisions

### Deterministic Keys
- Keys generated from source fields (not random)
- Ensures idempotency on reprocessing
- Supports incremental loading

### Timezone Handling
- All timestamps as NYC local time
- America/New_York for taxi-weather alignment
- DST-aware logic (no hardcoded UTC)

### Quality Flagging
- Invalid data preserved with flags
- Excluded only from specific metrics
- Full audit trail maintained

### Incremental Processing
- Process by month
- Add new data without rebuilding
- Rerun for idempotency verification

---

## Slide 11: Challenges & Mitigation

### Data Quality Issues
**Challenge:** Duplicate records, invalid measures, out-of-period data  
**Mitigation:** Quality flagging, selective exclusion, comprehensive validation

### Schema Complexity
**Challenge:** Galaxy schema, complex joins, cardinality requirements  
**Mitigation:** Schema contracts, reconciliation tests, referential integrity checks

### Timezone Handling
**Challenge:** DST transition, weather-timestamp alignment  
**Mitigation:** DST-aware logic, validation tests, timezone standardization

### Incremental Loading
**Challenge:** Key collision, measure drift on reruns  
**Mitigation:** Deterministic keys, idempotency tests, upsert logic

---

## Slide 12: Execution Workflow

### Development Workflow
```
feature branch → PR to development → review + CI → development
development → release PR → main
```

### Pipeline Execution Order
1. Land and verify raw sources
2. Run Bronze tables
3. Build and validate Silver
4. Run Silver quality checks
5. Build Gold dimensions and facts
6. Validate Gold integrity
7. Run incremental tests
8. Execute analytics queries
9. Generate results evidence

---

## Slide 13: Success Metrics

### Technical Metrics
- **Data Completeness:** 100% of required sources
- **Test Coverage:** 100% of acceptance criteria
- **Idempotency:** Zero drift on reruns
- **Performance:** Queries within SLA

### Business Metrics
- **Question 1:** Demand patterns with statistical significance
- **Question 2:** Weather correlations quantified
- **Question 3:** High-opportunity zones ranked

### Quality Metrics
- **Bronze:** 133,367 rows validated
- **Lineage:** 100% metadata coverage
- **Keys:** All natural keys unique
- **Integrity:** All FK relationships valid

---

## Slide 14: Timeline & Roadmap

### Current Status
- **Completed:** Bronze layer, testing framework, documentation
- **In Progress:** Silver/Gold design
- **Remaining:** 6-9 weeks

### Upcoming Milestones
- **Week 1-3:** Silver implementation
- **Week 4-6:** Gold implementation
- **Week 7-8:** Testing and validation
- **Week 9:** Analytics execution

### Completion Criteria
✅ All tables implemented  
✅ All tests passing  
✅ Incremental loading verified  
✅ Idempotency confirmed  
✅ Analytics executed  
✅ Results documented  

---

## Slide 15: Key Technologies

### Platform
- **Databricks:** Unified analytics platform
- **Unity Catalog:** Governance and metadata
- **Delta Lake:** ACID transactions

### Languages & Tools
- **Python 3.12:** Primary language
- **SQL:** Analytics and validation
- **PySpark:** Data processing

### Libraries
- requests, beautifulsoup4 (data acquisition)
- duckdb, pyarrow (data processing)
- boto3 (cloud integration)
- pytest (testing framework)

### Infrastructure
- Git (version control)
- External Volume (raw data storage)
- CI/CD (pull request validation)

---

## Slide 16: Lessons Learned

### Technical Insights
- Bronze preservation critical for auditability
- Deterministic keys essential for idempotency
- Quality flagging preferable to dropping
- Comprehensive testing prevents production issues

### Process Insights
- Documentation alongside implementation improves quality
- Test-driven approach catches issues early
- Schema contracts prevent integration problems
- Incremental validation reduces rework

### Best Practices Established
- Feature branch workflow with PR review
- Comprehensive test coverage
- Full documentation trail
- Quality-first approach

---

## Slide 17: Conclusion

### Project Summary
- **Strong Foundation:** Bronze layer complete and tested
- **Clear Roadmap:** Silver/Gold well-defined
- **Quality Focus:** Comprehensive QA framework
- **Business Ready:** Architecture supports all questions

### Key Strengths
- Robust architecture with medallion design
- Comprehensive testing and validation
- Full documentation and contracts
- Production-ready quality standards

### Next Steps
1. Implement Silver transformations
2. Implement Gold transformations
3. Execute analytics queries
4. Deliver business insights

---

## Slide 18: Q&A

### Questions?

**Project Resources:**
- Repository: NYC Mobility Ingestion Pipeline
- Documentation: docs/ directory
- Architecture: docs/architecture/data_model.md
- QA Report: docs/qa_implementation_report.md

**Contact:**
- Project team available for questions
- Technical documentation available
- Regular updates on progress

---

## Slide 19: Appendix - Key Files

### Documentation
- `README.md` - Project overview
- `docs/architecture/data_model.md` - Data model
- `docs/qa_implementation_report.md` - QA details
- `PROJECT_REPORT.md` - Full project report

### Configuration
- `requirements.txt` - Dependencies
- `config/catalog_and_schemas.yml` - Unity Catalog config
- `.env.example` - Environment template

### Execution
- `notebooks/01_land_raw_sources.py` - Data landing
- `pytest.ini` - Test configuration

---

## Slide 20: Thank You

**NYC Mobility Data Engineering Pipeline**

*Delivering Data-Driven Urban Mobility Insights*

**September 18, 2026**

---

## Presentation Notes

### Speaker Notes by Slide

**Slide 1:** Welcome everyone. Today I'll present our NYC Mobility Data Engineering Pipeline project.

**Slide 2:** This project addresses three critical business questions about urban mobility patterns using a robust Databricks medallion architecture.

**Slide 3:** Our three business questions focus on demand patterns, weather impact, and mobility opportunities - all critical for urban planning and resource allocation.

**Slide 4:** We integrate three data sources: NYC Green Taxi trips, Open-Meteo weather data, and NYC Taxi Zones reference data.

**Slide 5:** Our medallion architecture follows industry best practices with Bronze, Silver, and Gold layers, each with specific responsibilities.

**Slide 6:** The data model uses a galaxy schema with conformed dimensions and separate fact tables for trips and weather.

**Slide 7:** Bronze layer is complete and tested. Silver and Gold layers are designed and ready for implementation.

**Slide 8:** We have comprehensive test coverage with 12 test files covering all layers and integration scenarios.

**Slide 9:** The project structure is well-organized with clear separation of concerns across ingestion, transformations, testing, and documentation.

**Slide 10:** Key technical decisions include deterministic keys for idempotency, timezone-aware processing, and quality flagging over data dropping.

**Slide 11:** We've identified challenges and have clear mitigation strategies for each risk area.

**Slide 12:** Our execution workflow follows best practices with feature branches, PR reviews, and a clear pipeline execution order.

**Slide 13:** Success metrics cover technical quality, business value, and data integrity dimensions.

**Slide 14:** We have a clear timeline with 6-9 weeks remaining for Silver/Gold implementation and analytics execution.

**Slide 15:** The technology stack leverages Databricks, Python, SQL, and industry-standard libraries for data processing and testing.

**Slide 16:** Key lessons learned emphasize the importance of auditability, idempotency, quality flagging, and comprehensive testing.

**Slide 17:** The project has a strong foundation with clear next steps toward completion.

**Slide 18:** Questions? Our documentation and team are available for follow-up.

**Slide 19:** Additional resources and key files are listed for reference.

**Slide 20:** Thank you for your attention. We're delivering data-driven urban mobility insights.
