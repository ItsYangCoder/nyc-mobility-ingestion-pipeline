-- Purpose: verify that the expected catalog and layer schemas are visible.
-- Safety: read-only metadata statements.

SHOW SCHEMAS IN nyc_mobility;
SHOW TABLES IN nyc_mobility.nyc_bronze;
SHOW TABLES IN nyc_mobility.nyc_silver;
SHOW TABLES IN nyc_mobility.nyc_gold;
