"""Rerun-idempotency tests against production Spark transformations."""

from tests.integration.conftest import measures, month_rows, snapshot


def _keys(frame, key: str) -> set[object]:
    return {row[key] for row in frame.select(key).collect()}


def _assert_unique(frame, key: str) -> None:
    assert frame.count() == frame.select(key).distinct().count()


def test_may_rerun_silver_row_counts(spark):
    first = snapshot(spark, (3, 4, 5))
    rerun = snapshot(spark, (3, 4, 5))
    assert first["taxi_silver"].count() == rerun["taxi_silver"].count() == 6
    assert first["weather_silver"].count() == rerun["weather_silver"].count() == 6


def test_may_rerun_silver_key_stability(spark):
    first = snapshot(spark, (5,))
    rerun = snapshot(spark, (5,))
    assert _keys(first["taxi_silver"], "trip_key") == _keys(
        rerun["taxi_silver"], "trip_key"
    )
    assert _keys(first["weather_silver"], "weather_hour_local") == _keys(
        rerun["weather_silver"], "weather_hour_local"
    )


def test_may_rerun_silver_measure_stability(spark):
    first = snapshot(spark, (5,))["taxi_silver"]
    rerun = snapshot(spark, (5,))["taxi_silver"]
    assert measures(first, "pickup_date_local", 5) == measures(
        rerun, "pickup_date_local", 5
    )


def test_may_rerun_gold_row_counts(spark):
    first = snapshot(spark, (5,))
    rerun = snapshot(spark, (5,))
    assert first["taxi_gold"].count() == rerun["taxi_gold"].count() == 2
    assert first["weather_gold"].count() == rerun["weather_gold"].count() == 2


def test_may_rerun_gold_key_stability(spark):
    first = snapshot(spark, (5,))
    rerun = snapshot(spark, (5,))
    assert _keys(first["taxi_gold"], "trip_key") == _keys(
        rerun["taxi_gold"], "trip_key"
    )
    assert _keys(first["weather_gold"], "weather_hour_key") == _keys(
        rerun["weather_gold"], "weather_hour_key"
    )


def test_may_rerun_gold_measure_stability(spark):
    first = snapshot(spark, (5,))["taxi_gold"]
    rerun = snapshot(spark, (5,))["taxi_gold"]
    assert measures(first, "pickup_datetime", 5) == measures(
        rerun, "pickup_datetime", 5
    )
    assert month_rows(first, "pickup_datetime", 5) == month_rows(
        rerun, "pickup_datetime", 5
    )


def test_may_rerun_creates_no_duplicate_grains(spark):
    first = snapshot(spark, (5,))
    for frame, key in (
        (first["taxi_silver"], "trip_key"),
        (first["weather_silver"], "weather_hour_local"),
        (first["taxi_gold"], "trip_key"),
        (first["weather_gold"], "weather_hour_key"),
    ):
        _assert_unique(frame, key)
