"""Offline ingestion regressions; no downloaded datasets or credentials needed."""
import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import requests

from nyc_mobility.ingestion import download_taxi_zones as zones
from nyc_mobility.ingestion import green_taxi, weather


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def unexpected_request(*args, **kwargs):
        pytest.fail("Tests must not access the network")
    monkeypatch.setattr(requests, "get", unexpected_request)


@pytest.fixture
def weather_data():
    return {"hourly": {"time": ["2026-03-01T00:00"],
                       **{name: [1.0] for name in weather.HOURLY_VARIABLES}}}


@pytest.mark.parametrize("timestamps", [[None], [123], ["invalid"],
                                        ["2026-03-01T00:00"] * 2])
def test_weather_rejects_invalid_timestamps(weather_data, timestamps):
    weather_data["hourly"]["time"] = timestamps
    for name in weather.HOURLY_VARIABLES:
        weather_data["hourly"][name] = [1.0] * len(timestamps)
    with pytest.raises(ValueError):
        weather.validate_weather(weather_data)


def test_weather_rejects_mismatched_arrays(weather_data):
    weather_data["hourly"]["precipitation"] = []
    with pytest.raises(ValueError, match="length"):
        weather.validate_weather(weather_data)


def test_weather_download_and_reuse(tmp_path, monkeypatch, weather_data):
    content = json.dumps(weather_data).encode()
    class Response:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return weather_data
    response = Response()
    response.content = content
    calls = []
    def get(*args, **kwargs):
        calls.append(kwargs)
        return response
    monkeypatch.setattr(requests, "get", get)
    for _ in range(2):
        weather.download_weather("2026-03-01", "2026-03-01", tmp_path)
    assert len(calls) == 1
    assert (tmp_path / "weather_2026-03-01_2026-03-01.json").read_bytes() == content
    metadata = json.loads((tmp_path / "weather_2026-03-01_2026-03-01_metadata.json").read_text())
    assert metadata["request_parameters"]["timezone"] == weather.TIMEZONE
    assert not list(tmp_path.glob("*.part"))


def test_weather_preserves_invalid_existing_file(tmp_path):
    path = tmp_path / "weather_2026-03-01_2026-03-01.json"
    path.write_text("invalid")
    with pytest.raises(ValueError, match="Existing raw file is invalid"):
        weather.download_weather("2026-03-01", "2026-03-01", tmp_path)
    assert path.read_text() == "invalid"


@pytest.mark.parametrize("rows", ["", "1,A,B\n1,C,D\n", ",A,B\n"])
def test_zones_rejects_empty_or_invalid_keys(tmp_path, rows):
    path = tmp_path / "zones.csv"
    path.write_text("LocationID,Borough,Zone\n" + rows)
    with pytest.raises(ValueError):
        zones.profile_csv(path)


def test_zones_reuses_valid_file(tmp_path):
    path = tmp_path / "taxi_zone_lookup.csv"
    path.write_text("LocationID,Borough,Zone\n1,A,B\n")
    zones.download_or_reuse(tmp_path)
    assert zones.profile_csv(path)["row_count"] == 1


@pytest.mark.parametrize("table", [pa.table({"wrong": [1]}), pa.table({
    name: [] for name in ("VendorID", "lpep_pickup_datetime",
                         "lpep_dropoff_datetime", "PULocationID", "DOLocationID")})])
def test_green_rejects_wrong_schema_or_empty_parquet(tmp_path, table):
    path = tmp_path / "bad.parquet"
    pq.write_table(table, path)
    with pytest.raises(ValueError):
        green_taxi.inspect_parquet(path)


def test_green_failed_download_cleans_partial_file(tmp_path, monkeypatch):
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def raise_for_status(self):
            pass
        def iter_content(self, **kwargs):
            yield b"incomplete"
            raise requests.ConnectionError("interrupted")
    monkeypatch.setattr(requests, "get", lambda *a, **kw: Response())
    inventory = {}
    assert not green_taxi.download_month("03", inventory, tmp_path)
    assert inventory == {}
    assert list(tmp_path.iterdir()) == []


def test_green_reuses_file_and_saves_inventory(tmp_path):
    path = tmp_path / "green_tripdata_2026-03.parquet"
    pq.write_table(pa.table({name: [1] for name in (
        "VendorID", "lpep_pickup_datetime", "lpep_dropoff_datetime",
        "PULocationID", "DOLocationID")}), path)
    inventory = tmp_path / "inventory.csv"
    assert green_taxi.ingest_green_taxi("03", tmp_path, inventory) == 0
    record = green_taxi.load_inventory(inventory)[path.name]
    assert record["row_count"] == "1"
    assert int(record["file_size_bytes"]) == path.stat().st_size
