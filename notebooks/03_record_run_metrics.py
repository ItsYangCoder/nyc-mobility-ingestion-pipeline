# Databricks notebook source
# MAGIC %md
# MAGIC # NYC Mobility run monitoring
# MAGIC
# MAGIC TODO(mafelisilda): After the DQ contract and audit-table schema are
# MAGIC approved, this notebook will call reusable logic from
# MAGIC `nyc_mobility.monitoring.run_audit` to record workflow metrics.
# MAGIC
# MAGIC Required inputs: run ID, process date, task status, timestamps,
# MAGIC duration, failure context, freshness, row counts, and DQ status.
# MAGIC Do not add this notebook as a Databricks Job task until its upstream
# MAGIC dependencies and failure behavior are agreed in `databricks.yml`.

# COMMAND ----------

# TODO(mafelisilda): Add the thin Databricks entry point here. Keep business
# logic in src/nyc_mobility/monitoring/run_audit.py, not in this notebook.
