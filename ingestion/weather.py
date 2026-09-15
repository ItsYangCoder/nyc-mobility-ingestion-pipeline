import argparse
import json
from datetime import datetime
from pathlib import Path

import requests


LATITUDE = 40.7128
LONGITUDE = -74.0060
TIMEZONE = "America/New_York"
HOURLY_VARIABLES = [
    "temperature_2m",
    "precipitation",
    "wind_speed_10m",
]
URL = "https://archive-api.open-meteo.com/v1/archive"
DEFAULT_OUTPUT_DIR = Path("data/raw/weather")


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

    for variable in HOURLY_VARIABLES:
        values = hourly.get(variable)
        if not isinstance(values, list):
            raise ValueError(f"Hourly field is missing or invalid: {variable}")
        if len(values) != len(timestamps):
            raise ValueError(
                f"{variable} length does not match timestamp length."
            )

    return hourly


def load_existing_weather(filename: Path) -> dict | None:
    """Reuse an existing raw file only after it passes validation."""
    if not filename.exists():
        return None

    print(f"Existing file found: {filename}")

    try:
        with filename.open("r", encoding="utf-8") as file:
            data = json.load(file)
        validate_weather(data)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(
            f"Existing raw file is invalid: {filename}. "
            "Keep it for investigation, remove or rename it, then rerun. "
            f"Reason: {error}"
        ) from error

    print("Existing file is valid. Download skipped.")
    return data


def download_weather(
    start_date: str,
    end_date: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None:
    """Download and validate one date range without overwriting valid raw data."""
    if start_date > end_date:
        raise ValueError("Start date must be on or before end date.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"weather_{start_date}_{end_date}.json"
    metadata_filename = (
        output_dir / f"weather_{start_date}_{end_date}_metadata.json"
    )

    existing_data = load_existing_weather(filename)
    if existing_data is not None:
        return

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": TIMEZONE,
    }

    print("Requesting weather data...")
    print(params)

    try:
        response = requests.get(URL, params=params, timeout=30)
        print("HTTP status:", response.status_code)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise RuntimeError(f"Failed to retrieve weather data: {error}") from error
    except ValueError as error:
        raise ValueError("API response is not valid JSON.") from error

    hourly = validate_weather(data)
    raw_temp = filename.with_suffix(".json.part")
    metadata_temp = metadata_filename.with_suffix(".json.part")

    metadata = {
        "retrieved_at": datetime.now().astimezone().isoformat(),
        "request_parameters": params,
        "coordinates": {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
        },
        "timezone": TIMEZONE,
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

    print(f"Saved: {filename}")
    print(f"Saved metadata: {metadata_filename}")
    print(f"File size: {file_size_bytes:,} bytes")
    print("First timestamp:", timestamps[0])
    print("Last timestamp:", timestamps[-1])
    print("Number of hourly timestamps:", len(timestamps))
    print("Coverage and array length checks passed.")


def main() -> None:
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
