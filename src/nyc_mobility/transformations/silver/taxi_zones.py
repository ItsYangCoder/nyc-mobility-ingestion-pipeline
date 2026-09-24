"""Silver cleaning transformation for NYC Taxi Zones."""

from pyspark import pipelines as dp

from nyc_mobility.config import load_config
from nyc_mobility.transformations.core import build_silver_taxi_zones

CONFIG = load_config(spark)
BRONZE_TAXI_ZONES = CONFIG.table("bronze", "bronze_taxi_zones_raw")
SILVER_TAXI_ZONES = CONFIG.table("silver", "silver_taxi_zones")


@dp.materialized_view(
    name=SILVER_TAXI_ZONES,
    comment=(
        "Cleaned and standardized NYC Taxi Zones "
        "from the latest source ingestion snapshot."
    ),
    table_properties={"quality": "silver"},
)
def silver_taxi_zones():
    return build_silver_taxi_zones(spark.read.table(BRONZE_TAXI_ZONES))
