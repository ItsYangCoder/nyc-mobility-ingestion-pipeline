# Gold fact constellation

Gold uses a fact constellation: two fact tables share conformed date and hour
dimensions, while taxi trips also share the zone dimension.

## Dimensions

| File | Table | Grain |
|---|---|---|
| `dimensions/dim_date.py` | `nyc_gold.dim_date` | One calendar date |
| `dimensions/dim_hour.py` | `nyc_gold.dim_hour` | One hour of day |
| `dimensions/dim_zone.py` | `nyc_gold.dim_zone` | One NYC taxi location |

## Facts

| File | Table | Grain |
|---|---|---|
| `facts/fact_taxi_trip.py` | `nyc_gold.fact_taxi_trip` | One retained in-window taxi trip |
| `facts/fact_weather_hourly.py` | `nyc_gold.fact_weather_hourly` | One local weather observation hour |

Build order: dimensions first, then facts. Taxi-weather analysis joins
`fact_taxi_trip.pickup_date_key + pickup_hour_key` to
`fact_weather_hourly.date_key + hour_key`. Facts remain separate.
