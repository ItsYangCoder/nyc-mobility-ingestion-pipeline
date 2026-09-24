from pathlib import Path

MONITORING_SQL = Path("analytics/monitoring")
BUNDLE_CONFIG = Path("databricks.yml")


def read_query(name: str) -> str:
    return (MONITORING_SQL / name).read_text(encoding="utf-8")


def test_execution_queries_distinguish_running_from_unknown():
    for name in ("01_pipeline_health.sql", "02_task_run_history.sql"):
        query = read_query(name)

        assert "THEN 'RUNNING'" in query
        assert "ELSE 'UNKNOWN'" in query
        assert "last_observed_at" in query


def test_quality_query_surfaces_expected_rules_that_did_not_run():
    query = read_query("03_quality_results.sql")

    assert ":expected_rule_ids" in query
    assert "CROSS JOIN rule_catalog" in query
    assert "LEFT JOIN observed_results" in query
    assert "COALESCE(q.outcome, 'NOT_EVALUATED')" in query


def test_freshness_query_separates_event_and_processing_times():
    query = read_query("04_dataset_freshness.sql")

    assert query.count("AS last_processed_at") == 1
    assert "actual_through" in query
    assert "TO_DATE(:analysis_end_date)" in query
    assert "'FRESH'" in query
    assert "'STALE'" in query
    assert "'UNKNOWN'" in query


def test_bundle_syncs_dashboard_queries():
    bundle = BUNDLE_CONFIG.read_text(encoding="utf-8")

    assert "- analytics/**" in bundle
