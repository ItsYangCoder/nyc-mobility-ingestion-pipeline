import argparse
import json
from pathlib import Path
from datetime import datetime

import requests

# NYC coordinates
LATITUDE = 40.7128
LONGITUDE = -74.0060

# Open-Meteo settings
TIMEZONE = "America/New_York"

# Get date range from command line
parser = argparse.ArgumentParser(
    description="Download historical weather data from Open-Meteo."
)

parser.add_argument(
    "--start-date",
    required=True,
    help="Start date in YYYY-MM-DD format"
)

parser.add_argument(
    "--end-date",
    required=True,
    help="End date in YYYY-MM-DD format"
)

args = parser.parse_args()

START_DATE = args.start_date
END_DATE = args.end_date

# Weather variables
HOURLY_VARIABLES = [
    "temperature_2m",
    "precipitation",
    "wind_speed_10m"
]

# API URL
URL = "https://archive-api.open-meteo.com/v1/archive"

# Output folder
OUTPUT_DIR = Path("data/raw/weather")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output filenames
filename = OUTPUT_DIR / f"weather_{START_DATE}_{END_DATE}.json"
metadata_filename = OUTPUT_DIR / f"weather_{START_DATE}_{END_DATE}_metadata.json"

# Prevent accidental duplicate downloads
if filename.exists():
    print(f"File already exists: {filename}")
    print("Download skipped to prevent duplicate or overwritten raw data.")
    raise SystemExit

# API parameters
params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "hourly": ",".join(HOURLY_VARIABLES),
    "timezone": TIMEZONE
}

print("Requesting weather data...")
print(params)

# Send request
try:
    response = requests.get(URL, params=params, timeout=30)

    # Check response
    print("HTTP status:", response.status_code)

    response.raise_for_status()

except requests.RequestException as error:
    print(f"ERROR: Failed to retrieve weather data: {error}")
    raise


# Convert response to JSON
try:
    data = response.json()

except ValueError:
    print("ERROR: API response is not valid JSON.")
    raise

# Check that weather data exists
if "hourly" not in data:
    raise ValueError(
        "ERROR: API response does not contain hourly weather data."
    )

# Record request metadata
metadata = {
    "retrieved_at": datetime.now().astimezone().isoformat(),
    "request_parameters": params,
    "coordinates": {
        "latitude": LATITUDE,
        "longitude": LONGITUDE
    },
    "timezone": TIMEZONE,
    "units": data.get("hourly_units", {})
}

# Save metadata
with open(metadata_filename, "w", encoding="utf-8") as file:
    json.dump(metadata, file, indent=2)

print(f"Saved metadata: {metadata_filename}")

# Save unchanged API response
with open(filename, "wb") as file:
    file.write(response.content)

print(f"Saved: {filename}")

# Check file size
file_size_bytes = filename.stat().st_size
file_size_kb = file_size_bytes / 1024
file_size_mb = file_size_kb / 1024

print(f"File size: {file_size_bytes:,} bytes")
print(f"File size: {file_size_kb:.2f} KB")
print(f"File size: {file_size_mb:.2f} MB")

# Check time coverage and array lengths
hourly = data["hourly"]
timestamps = hourly["time"]

print("\nCoverage check:")
print("First timestamp:", timestamps[0])
print("Last timestamp:", timestamps[-1])
print("Number of hourly timestamps:", len(timestamps))

print("\nArray lengths:")
print("time:", len(hourly["time"]))

for variable in HOURLY_VARIABLES:
    variable_length = len(hourly[variable])
    print(f"{variable}:", variable_length)

    if variable_length != len(timestamps):
        raise ValueError(
            f"ERROR: {variable} length does not match timestamp length."
        )

print("\nCoverage and array length checks passed.")
