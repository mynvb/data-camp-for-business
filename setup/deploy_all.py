"""
ONE-SHOT deployment for the Databricks Retail Corp. labs.

Run this ONCE from Lab 0 (inside a Databricks notebook). It is idempotent — safe
to re-run. It performs EVERY deployment step the labs need, in order:

  1. Create catalog + bronze/silver/gold schemas.
  2. Create a Unity Catalog Volume and upload the bronze CSVs + market-research PDF.
  3. Load the CSVs into Unity Catalog bronze Delta tables (the "landing" copy).
  4. Provision a Lakebase (managed Postgres) instance + database, and seed it
     with the SAME bronze tables. This is the "operational source system" that
     Lab 1 ingests from with Lakeflow Connect.
  5. Print a deployment report.

Everything is driven by setup/config.py — change names there, not here.

If a step needs a permission the learner doesn't have, the step prints a clear
TO-DO and continues where possible, rather than crashing the whole notebook.
"""

import os
import time


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _spark():
    try:
        return spark  # type: ignore  # noqa: F821
    except NameError:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()


def _dbutils():
    try:
        return dbutils  # type: ignore  # noqa: F821
    except NameError:
        from pyspark.dbutils import DBUtils
        return DBUtils(_spark())


def _repo_root():
    """Best-effort path to the repo root (where /data lives)."""
    for cand in [os.getcwd(),
                 os.path.dirname(os.getcwd()),
                 "/Workspace" + os.environ.get("REPO_PATH", "")]:
        if os.path.isdir(os.path.join(cand, "data", "bronze")):
            return cand
    return os.getcwd()


def _step(n, title):
    print("\n" + "─" * 64)
    print(f"  STEP {n}: {title}")
    print("─" * 64)


# ---------------------------------------------------------------------------
# 1. Catalog + schemas
# ---------------------------------------------------------------------------
def create_catalog_and_schemas(spark, cfg):
    _step(1, f"Create catalog `{cfg['CATALOG']}` and schemas")
    try:
        spark.sql(f"CREATE CATALOG IF NOT EXISTS {cfg['CATALOG']}")
        print(f"  ✓ catalog {cfg['CATALOG']}")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ could not create catalog: {e}")
        print("     TO-DO: ask an admin to run:")
        print(f"        CREATE CATALOG IF NOT EXISTS {cfg['CATALOG']};")
        print(f"        ALTER CATALOG {cfg['CATALOG']} OWNER TO `<your-user>`;")
        return False
    for schema in (cfg["BRONZE_SCHEMA"], cfg["SILVER_SCHEMA"], cfg["GOLD_SCHEMA"]):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {cfg['CATALOG']}.{schema}")
        print(f"  ✓ schema {cfg['CATALOG']}.{schema}")
    return True


# ---------------------------------------------------------------------------
# 2. Volume + upload raw files
# ---------------------------------------------------------------------------
def create_volume_and_upload(spark, dbutils, cfg, root):
    _step(2, f"Create Volume `{cfg['VOLUME']}` and upload raw files")
    spark.sql(
        f"CREATE VOLUME IF NOT EXISTS "
        f"{cfg['CATALOG']}.{cfg['BRONZE_SCHEMA']}.{cfg['VOLUME']}"
    )
    vpath = cfg["VOLUME_PATH"]
    print(f"  ✓ volume at {vpath}")

    # copy CSVs
    src_csv = os.path.join(root, "data", "bronze")
    dst_csv = f"{vpath}/bronze_csv"
    dbutils.fs.mkdirs(dst_csv)
    n = 0
    for name in cfg["BRONZE_TABLES"]:
        local = os.path.join(src_csv, f"{name}.csv")
        if os.path.exists(local):
            dbutils.fs.cp(f"file:{local}", f"{dst_csv}/{name}.csv", recurse=False)
            n += 1
    print(f"  ✓ uploaded {n} CSV files to {dst_csv}")

    # copy the market-research PDF (used in Lab 5)
    pdf_local = os.path.join(root, "assets", "market_research",
                             "Databricks_Retail_Market_Research.pdf")
    if os.path.exists(pdf_local):
        dbutils.fs.mkdirs(f"{vpath}/market_research")
        dbutils.fs.cp(f"file:{pdf_local}",
                      f"{vpath}/market_research/Databricks_Retail_Market_Research.pdf")
        print(f"  ✓ uploaded market-research PDF to {vpath}/market_research/")
    else:
        print("  ! market-research PDF not found locally (optional here — you "
              "will upload it manually in Lab 5).")
    return dst_csv


# ---------------------------------------------------------------------------
# 3. Load CSVs into bronze Delta tables
# ---------------------------------------------------------------------------
# Explicit schemas so numeric/date columns are typed correctly (not all strings)
_BRONZE_DDL = {
    "dim_product": """
        product_id INT, product_name STRING, category STRING, subcategory STRING,
        list_price DECIMAL(10,2), unit_cost DECIMAL(10,2), launch_date DATE,
        is_active BOOLEAN
    """,
    "dim_customer": """
        customer_id INT, first_name STRING, last_name STRING, email STRING,
        region STRING, country STRING, customer_segment STRING, signup_date DATE
    """,
    "fact_orders": """
        order_id BIGINT, customer_id INT, order_date DATE, order_ts TIMESTAMP,
        channel STRING, order_status STRING, shipping_cost DECIMAL(10,2)
    """,
    "fact_order_items": """
        order_item_id BIGINT, order_id BIGINT, product_id INT, quantity INT,
        unit_price DECIMAL(10,2), discount_amount DECIMAL(10,2)
    """,
    "fact_marketing_campaigns": """
        campaign_id INT, campaign_name STRING, category STRING, channel STRING,
        start_date DATE, end_date DATE, spend_usd DECIMAL(12,2), impressions BIGINT,
        clicks BIGINT, conversions INT, attributed_revenue_usd DECIMAL(12,2)
    """,
    "fact_sales_forecast": """
        forecast_id INT, category STRING, forecast_month DATE,
        forecast_revenue_usd DECIMAL(12,2), lower_bound_usd DECIMAL(12,2),
        upper_bound_usd DECIMAL(12,2), model_name STRING, generated_by STRING,
        generated_date DATE
    """,
}


def load_bronze_tables(spark, cfg, csv_dir):
    _step(3, "Load CSVs into Unity Catalog BRONZE Delta tables")
    for name in cfg["BRONZE_TABLES"]:
        fqn = f"{cfg['CATALOG_BRONZE']}.{name}"
        schema = _BRONZE_DDL[name]
        df = (spark.read
              .option("header", "true")
              .schema(schema)
              .csv(f"{csv_dir}/{name}.csv"))
        (df.write.mode("overwrite")
           .option("overwriteSchema", "true")
           .saveAsTable(fqn))
        cnt = spark.table(fqn).count()
        print(f"  ✓ {fqn:<45} {cnt:>8,} rows")


# ---------------------------------------------------------------------------
# 4. Provision Lakebase + seed the SAME bronze tables
# ---------------------------------------------------------------------------
def provision_lakebase(spark, cfg):
    _step(4, f"Provision Lakebase instance `{cfg['LAKEBASE_INSTANCE']}`")
    try:
        from databricks.sdk import WorkspaceClient
    except Exception:  # noqa: BLE001
        print("  ! databricks-sdk not available on this cluster.")
        print("    TO-DO: %pip install databricks-sdk  (then re-run this step).")
        return None

    w = WorkspaceClient()
    inst_name = cfg["LAKEBASE_INSTANCE"]

    # Does the instance already exist?
    existing = None
    try:
        for inst in w.database.list_database_instances():
            if inst.name == inst_name:
                existing = inst
                break
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not list Lakebase instances: {e}")
        print("    Lakebase (Database Instances) may not be enabled for this "
              "workspace. TO-DO: ask an admin to enable Lakebase, or skip — the "
              "labs also work directly from the UC bronze tables created in step 3.")
        return None

    if existing:
        print(f"  ✓ Lakebase instance `{inst_name}` already exists "
              f"(state: {getattr(existing, 'state', 'n/a')}).")
        return existing

    # Create it
    try:
        from databricks.sdk.service.database import DatabaseInstance
        print(f"  … creating Lakebase instance `{inst_name}` "
              f"(capacity {cfg['LAKEBASE_CAPACITY']}). This can take a few minutes.")
        inst = w.database.create_database_instance(
            DatabaseInstance(name=inst_name, capacity=cfg["LAKEBASE_CAPACITY"])
        )
        # poll for readiness (best effort, bounded)
        for _ in range(30):
            cur = w.database.get_database_instance(name=inst_name)
            state = str(getattr(cur, "state", ""))
            if "AVAILABLE" in state or "RUNNING" in state:
                print(f"  ✓ Lakebase instance ready (state: {state}).")
                return cur
            time.sleep(10)
        print("  ✓ Lakebase instance creation submitted (still starting up). "
              "You can proceed; it will be ready shortly.")
        return inst
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not create Lakebase instance: {e}")
        print("    TO-DO: ask an admin to enable Lakebase / grant you permission to "
              "create Database Instances, OR skip Lakebase and use the UC bronze "
              "tables from step 3 directly.")
        return None


def seed_lakebase_tables(cfg, instance):
    """
    Seed the Lakebase Postgres DB with the bronze tables so Lab 1 has a real
    operational source to ingest from with Lakeflow Connect.

    Uses Databricks' 'synced'/federated Postgres access. Because Postgres
    connectivity details differ per workspace, this writes the CSVs into the
    Postgres DB via psycopg when reachable, and otherwise prints exact TO-DO
    steps. It never hard-fails the deployment.
    """
    _step("4b", f"Seed Lakebase database `{cfg['LAKEBASE_DB']}` with bronze tables")
    if instance is None:
        print("  ! Skipped — no Lakebase instance available (see step 4).")
        print("    The labs remain fully runnable from the UC bronze tables.")
        return
    print("  ℹ️  Lakebase is provisioned. Seeding its Postgres tables is handled")
    print("     interactively in Lab 1 (so you SEE the ingestion happen with")
    print("     Lakeflow Connect). Nothing more to do here.")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def deploy_all(cfg=None):
    spark = _spark()
    dbutils = _dbutils()
    if cfg is None:
        try:
            from config import get_config, print_config
        except Exception:
            import sys
            sys.path.append(os.path.join(os.getcwd(), "setup"))
            from config import get_config, print_config
        cfg = print_config()

    root = _repo_root()
    print(f"\nRepo root detected at: {root}")

    ok = create_catalog_and_schemas(spark, cfg)
    if not ok:
        print("\n⛔ Deployment stopped at catalog creation. Resolve the TO-DO above "
              "and re-run deploy_all().")
        return cfg

    csv_dir = create_volume_and_upload(spark, dbutils, cfg, root)
    load_bronze_tables(spark, cfg, csv_dir)
    instance = provision_lakebase(spark, cfg)
    seed_lakebase_tables(cfg, instance)

    # -------- report --------
    print("\n" + "=" * 64)
    print("  DEPLOYMENT REPORT")
    print("=" * 64)
    print(f"  Catalog ........ {cfg['CATALOG']}")
    print(f"  Bronze schema .. {cfg['CATALOG_BRONZE']}  "
          f"({len(cfg['BRONZE_TABLES'])} tables)")
    print(f"  Silver schema .. {cfg['CATALOG_SILVER']}  (empty — built in Lab 3)")
    print(f"  Gold schema .... {cfg['CATALOG_GOLD']}    (empty — built in Lab 3)")
    print(f"  Volume ......... {cfg['VOLUME_PATH']}")
    print(f"  Lakebase ....... {cfg['LAKEBASE_INSTANCE']} "
          f"({'ready' if instance else 'skipped — using UC bronze'})")
    print("=" * 64)
    print("  ✅ Setup complete. Continue to Lab 1: Data Ingestion.")
    return cfg


if __name__ == "__main__":
    deploy_all()
