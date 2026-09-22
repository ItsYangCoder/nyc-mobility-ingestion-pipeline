from nyc_mobility.config import PipelineConfig
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
