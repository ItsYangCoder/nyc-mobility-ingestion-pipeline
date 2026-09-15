import requests
import json
from pathlib import Path
from datetime import datetime

# NYC coordinates
LATITUDE = 40.7128
LONGITUDE = -74.0060

# Open-Meteo settings
TIMEZONE = "America/New_York"

# Dates
START_DATE = "2026-03-01"
END_DATE = "2026-03-03"

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
    raise ValueError("Response does not contain hourly weather data."
)

# Save JSON
filename = OUTPUT_DIR / f"weather_{START_DATE}_{END_DATE}.json"

with open(filename, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)

print(f"Saved: {filename}")

# Check file size
file_size_bytes = filename.stat().st_size
file_size_kb = file_size_bytes / 1024
file_size_mb = file_size_kb / 1024

print(f"File size: {file_size_bytes:,} bytes")
print(f"File size: {file_size_kb:.2f} KB")
print(f"File size: {file_size_mb:.2f} MB")

# Basic coverage check
print("Number of hourly timestamps:", len(data["hourly"]["time"]))