import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

from nyc_mobility.config import CONFIG, PipelineConfig
from nyc_mobility.logging import configure_logging, get_logger, log_event

LATITUDE = 40.7128
LONGITUDE = -74.0060
TIMEZONE = CONFIG.timezone
HOURLY_VARIABLES = [
    "temperature_2m",
    "precipitation",
    "wind_speed_10m",
]
URL = CONFIG.weather_source_url
DEFAULT_OUTPUT_DIR = Path("data/raw/weather")
LOGGER = get_logger(__name__)


def valid_date(value: str) -> str:
    """Validate command-line dates and return the original value."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from error
    return value


def validate_weather(data: object) -> dict:
    """Validate the fields needed by the pipeline."""
    if not isinstance(data, dict):
        raise ValueError("API response must be a JSON object.")

    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise ValueError("API response does not contain hourly weather data.")

    timestamps = hourly.get("time")
    if not isinstance(timestamps, list) or not timestamps:
        raise ValueError("Hourly timestamps are missing or empty.")

    try:
        parsed = [
            datetime.fromisoformat(value.replace("Z", "+00:00")) for value in timestamps
        ]
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(
            "Hourly timestamps must be valid ISO datetime strings."
        ) from error
    if len(set(parsed)) != len(parsed):
        raise ValueError("Duplicate hourly timestamps are not allowed.")

    for variable in HOURLY_VARIABLES:
        values = hourly.get(variable)
        if not isinstance(values, list):
            raise ValueError(f"Hourly field is missing or invalid: {variable}")
        if len(values) != len(timestamps):
            raise ValueError(f"{variable} length does not match timestamp length.")

    return hourly


def load_existing_weather(
    filename: Path,
    metadata_filename: Path,
    config: PipelineConfig,
) -> dict | None:
    """Reuse raw weather only when data and source metadata still match."""
    if not filename.exists():
        return None

    try:
        with filename.open("r", encoding="utf-8") as file:
            data = json.load(file)
        validate_weather(data)
        with metadata_filename.open("r", encoding="utf-8") as file:
            metadata = json.load(file)
        if metadata.get("source_url") != config.weather_source_url:
            raise ValueError("saved source URL does not match current configuration")
        if metadata.get("timezone") != config.timezone:
            raise ValueError("saved timezone does not match current configuration")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(
            f"Existing raw file is invalid: {filename}. "
            "Keep it for investigation, remove or rename it, then rerun. "
            f"Reason: {error}"
        ) from error

    log_event(
        LOGGER,
        logging.INFO,
        "weather.reused",
        "Existing weather file is valid; download skipped",
        filename=filename,
        file_size_bytes=filename.stat().st_size,
    )
    return data


def download_weather(
    start_date: str,
    end_date: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    config: PipelineConfig = CONFIG,
) -> None:
    """Download and validate one date range without overwriting valid raw data."""
    if start_date > end_date:
        raise ValueError("Start date must be on or before end date.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"weather_{start_date}_{end_date}.json"
    metadata_filename = output_dir / f"weather_{start_date}_{end_date}_metadata.json"

    existing_data = load_existing_weather(filename, metadata_filename, config)
    if existing_data is not None:
        return

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": config.timezone,
    }

    log_event(
        LOGGER,
        logging.INFO,
        "weather.download_started",
        "Requesting weather data",
        source_url=config.weather_source_url,
        output_file=filename,
        request_parameters=params,
    )

    try:
        response = requests.get(config.weather_source_url, params=params, timeout=30)
        log_event(
            LOGGER,
            logging.INFO,
            "weather.http_response",
            "Weather API response received",
            status_code=response.status_code,
            start_date=start_date,
            end_date=end_date,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        log_event(
            LOGGER,
            logging.ERROR,
            "weather.request_failed",
            "Weather API request failed",
            source_url=config.weather_source_url,
            start_date=start_date,
            end_date=end_date,
            error=str(error),
            exc_info=True,
        )
        raise RuntimeError(f"Failed to retrieve weather data: {error}") from error
    except ValueError as error:
        log_event(
            LOGGER,
            logging.ERROR,
            "weather.invalid_json",
            "Weather API returned invalid JSON",
            start_date=start_date,
            end_date=end_date,
            error=str(error),
            exc_info=True,
        )
        raise ValueError("API response is not valid JSON.") from error

    hourly = validate_weather(data)
    raw_temp = filename.with_suffix(".json.part")
    metadata_temp = metadata_filename.with_suffix(".json.part")

    metadata = {
        "source_url": config.weather_source_url,
        "retrieved_at": datetime.now().astimezone().isoformat(),
        "request_parameters": params,
        "coordinates": {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
        },
        "timezone": config.timezone,
        "units": data.get("hourly_units", {}),
    }

    try:
        raw_temp.write_bytes(response.content)
        with metadata_temp.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        raw_temp.replace(filename)
        metadata_temp.replace(metadata_filename)
    finally:
        if raw_temp.exists():
            raw_temp.unlink()
        if metadata_temp.exists():
            metadata_temp.unlink()

    timestamps = hourly["time"]
    file_size_bytes = filename.stat().st_size

    log_event(
        LOGGER,
        logging.INFO,
        "weather.download_completed",
        "Weather data downloaded and validated",
        output_file=filename,
        metadata_file=metadata_filename,
        file_size_bytes=file_size_bytes,
        first_timestamp=timestamps[0],
        last_timestamp=timestamps[-1],
        hourly_timestamp_count=len(timestamps),
    )


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(
        description="Download historical weather data from Open-Meteo."
    )
    parser.add_argument("--start-date", required=True, type=valid_date)
    parser.add_argument("--end-date", required=True, type=valid_date)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="landing directory; accepts a Databricks /Volumes/... path",
    )
    args = parser.parse_args()
    download_weather(
        args.start_date,
        args.end_date,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
