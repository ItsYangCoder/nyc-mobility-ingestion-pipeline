"""Incremental March-to-May tests against production Spark transformations."""

from pyspark.sql import functions as F

from tests.integration.conftest import measures, month_rows


def _assert_unique(frame, key: str) -> None:
    assert frame.count() == frame.select(key).distinct().count()


def test_march_baseline_silver(monthly_snapshots):
    march = monthly_snapshots["march"]
    assert march["taxi_silver"].count() == 2
    assert march["weather_silver"].count() == 2
    _assert_unique(march["taxi_silver"], "trip_key")
    _assert_unique(march["weather_silver"], "weather_hour_local")


def test_april_incremental_silver_preserves_march(monthly_snapshots):
    baseline = monthly_snapshots["march"]
    incremental = monthly_snapshots["april"]
    assert incremental["taxi_silver"].count() == 4
    assert incremental["weather_silver"].count() == 4
    assert month_rows(baseline["taxi_silver"], "pickup_date_local", 3) == month_rows(
        incremental["taxi_silver"], "pickup_date_local", 3
    )


def test_may_incremental_silver_preserves_prior_months(monthly_snapshots):
    before = monthly_snapshots["april"]
    after = monthly_snapshots["may"]
    assert after["taxi_silver"].count() == 6
    assert after["weather_silver"].count() == 6
    for month in (3, 4):
        assert month_rows(before["taxi_silver"], "pickup_date_local", month) == (
            month_rows(after["taxi_silver"], "pickup_date_local", month)
        )
        assert month_rows(before["weather_silver"], "weather_date_local", month) == (
            month_rows(after["weather_silver"], "weather_date_local", month)
        )


def test_march_baseline_gold_reconciles_to_silver(monthly_snapshots):
    march = monthly_snapshots["march"]
    assert (
        march["taxi_gold"].count()
        == march["taxi_silver"].filter(F.col("is_in_analysis_window")).count()
    )
    assert (
        march["weather_gold"].count()
        == march["weather_silver"].filter(F.col("is_in_analysis_window")).count()
    )


def test_april_incremental_gold_preserves_march(monthly_snapshots):
    baseline = monthly_snapshots["march"]
    incremental = monthly_snapshots["april"]
    assert incremental["taxi_gold"].count() == 4
    assert incremental["weather_gold"].count() == 4
    assert month_rows(baseline["taxi_gold"], "pickup_datetime", 3) == month_rows(
        incremental["taxi_gold"], "pickup_datetime", 3
    )


def test_may_incremental_gold_preserves_prior_months(monthly_snapshots):
    before = monthly_snapshots["april"]
    after = monthly_snapshots["may"]
    assert after["taxi_gold"].count() == 6
    assert after["weather_gold"].count() == 6
    for month in (3, 4):
        assert month_rows(before["taxi_gold"], "pickup_datetime", month) == month_rows(
            after["taxi_gold"], "pickup_datetime", month
        )
        assert month_rows(
            before["weather_gold"], "weather_timestamp", month
        ) == month_rows(after["weather_gold"], "weather_timestamp", month)


def test_incremental_measure_totals_are_stable(monthly_snapshots):
    for month, earlier in ((3, "march"), (3, "april"), (4, "april")):
        assert measures(
            monthly_snapshots[earlier]["taxi_gold"], "pickup_datetime", month
        ) == measures(monthly_snapshots["may"]["taxi_gold"], "pickup_datetime", month)
