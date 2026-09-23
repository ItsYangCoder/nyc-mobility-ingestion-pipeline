import pyarrow as pa
import pyarrow.parquet as pq

from nyc_mobility.config import PipelineConfig
from tests.integration import verify_raw_files
from tests.integration.verify_raw_files import configured_source_files


def test_raw_file_expectations_follow_injected_config(tmp_path):
    config = PipelineConfig(
        analysis_start_date="2027-11-15",
        analysis_end_date="2028-01-10",
    )

    green, weather = configured_source_files(config, tmp_path)

    assert list(green) == ["2027-11", "2027-12", "2028-01"]
    assert green["2028-01"].name == "green_tripdata_2028-01.parquet"
    assert weather["2027-11"] == (
        tmp_path / "weather" / "weather_2027-11-15_2027-11-30.json",
        "2027-11-15",
        "2027-11-30",
    )
    assert weather["2028-01"] == (
        tmp_path / "weather" / "weather_2028-01-01_2028-01-10.json",
        "2028-01-01",
        "2028-01-10",
    )


def test_raw_file_check_reads_only_header(tmp_path, monkeypatch):
    path = tmp_path / "source.bin"
    path.write_bytes(b"parquet header" + b"x" * 4096)

    def reject_whole_file_read(self):
        raise AssertionError("Raw verification must not read the entire file")

    monkeypatch.setattr(type(path), "read_bytes", reject_whole_file_read)
    assert verify_raw_files.check_file(path)


def test_taxi_verification_streams_rows_and_preserves_quality_counts(
    tmp_path, monkeypatch
):
    path = tmp_path / "green_tripdata_2026-03.parquet"
    table = pa.table(
        {
            "VendorID": [1, 1, 1, 1],
            "lpep_pickup_datetime": [
                "2026-03-01T08:00:00",
                "2026-03-31T08:00:00",
                "2026-03-01T08:00:00",
                None,
            ],
            "lpep_dropoff_datetime": ["2026-03-01T09:00:00"] * 4,
            "PULocationID": [10] * 4,
            "DOLocationID": [11] * 4,
        }
    )
    pq.write_table(table, path, row_group_size=2)

    def reject_full_table_read(*args, **kwargs):
        raise AssertionError("Raw verification must scan selected columns in batches")

    monkeypatch.setattr(verify_raw_files.parquet, "read_table", reject_full_table_read)
    passed, metrics = verify_raw_files.check_green_taxi(path, "2026-03")

    assert passed
    assert metrics == {"missing": 1, "duplicates": 1}
