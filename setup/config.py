"""
Central configuration for the Databricks Retail Corp. labs.

Every lab and setup script imports these names so the whole training uses ONE
consistent set of catalog / schema / instance names. If your workspace needs
different names (e.g. you don't have permission to create a catalog called
`retail_corp`), change them here in ONE place and every lab follows.

In a Databricks notebook you can also override any value with a widget of the
same name, e.g.:

    dbutils.widgets.text("CATALOG", "my_catalog")

`get_config()` reads widgets first, then environment variables, then the
defaults below.
"""

import os

# ---------------------------------------------------------------------------
# Defaults — safe to edit. Lower-case, no spaces (Unity Catalog naming rules).
# ---------------------------------------------------------------------------
DEFAULTS = {
    # Unity Catalog
    "CATALOG": "retail_corp",
    "BRONZE_SCHEMA": "bronze",
    "SILVER_SCHEMA": "silver",
    "GOLD_SCHEMA": "gold",
    "VOLUME": "raw_files",            # UC volume that holds CSVs + the PDF

    # Lakebase (Databricks managed Postgres) — the "operational" source system
    # that Lab 1 ingests from using Lakeflow Connect.
    "LAKEBASE_INSTANCE": "retail-corp-lakebase",
    "LAKEBASE_DB": "retail_corp",
    "LAKEBASE_CAPACITY": "CU_1",      # smallest capacity unit; enough for labs

    # Domain / governance (Lab 2)
    "DOMAIN_NAME": "Retail Sales & Marketing",

    # Job that refreshes gold tables daily (Lab 3)
    "GOLD_JOB_NAME": "retail_corp_gold_daily_refresh",
}

# The bronze tables that live in Lakebase and get ingested into UC bronze.
# fact_sales_forecast is a forecast hand-off "provided by the Data Science team"
# and is used in Lab 5 to contrast against a forecast the learner generates with
# the ai_forecast() SQL function.
BRONZE_TABLES = [
    "dim_product",
    "dim_customer",
    "fact_orders",
    "fact_order_items",
    "fact_marketing_campaigns",
    "fact_sales_forecast",
]


def _from_widget(key):
    try:
        # dbutils is only defined inside a Databricks notebook
        return dbutils.widgets.get(key)  # type: ignore  # noqa: F821
    except Exception:
        return None


def get_config():
    """Return the effective config dict (widgets > env vars > defaults)."""
    cfg = {}
    for key, default in DEFAULTS.items():
        val = _from_widget(key) or os.environ.get(key) or default
        cfg[key] = val
    # Convenience fully-qualified names
    cfg["CATALOG_BRONZE"] = f'{cfg["CATALOG"]}.{cfg["BRONZE_SCHEMA"]}'
    cfg["CATALOG_SILVER"] = f'{cfg["CATALOG"]}.{cfg["SILVER_SCHEMA"]}'
    cfg["CATALOG_GOLD"] = f'{cfg["CATALOG"]}.{cfg["GOLD_SCHEMA"]}'
    cfg["VOLUME_PATH"] = (
        f'/Volumes/{cfg["CATALOG"]}/{cfg["BRONZE_SCHEMA"]}/{cfg["VOLUME"]}'
    )
    cfg["BRONZE_TABLES"] = BRONZE_TABLES
    return cfg


def print_config(cfg=None):
    cfg = cfg or get_config()
    print("Databricks Retail Corp. — effective configuration")
    print("=" * 52)
    for k in ["CATALOG", "BRONZE_SCHEMA", "SILVER_SCHEMA", "GOLD_SCHEMA",
              "VOLUME", "VOLUME_PATH", "LAKEBASE_INSTANCE", "LAKEBASE_DB",
              "DOMAIN_NAME", "GOLD_JOB_NAME"]:
        print(f"  {k:<18} = {cfg[k]}")
    print("=" * 52)
    return cfg
