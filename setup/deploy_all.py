"""
ONE-SHOT deployment for the Databricks Retail Corp. labs.

Run this ONCE from Lab 0 (inside a Databricks notebook). It is idempotent — safe
to re-run. It performs EVERY deployment step the labs need, in order:

  1. Use the EXISTING catalog and create bronze/silver/gold schemas in it. (The
     catalog is assumed to already exist; bronze starts EMPTY — it is filled in
     Lab 1 by Lakeflow Connect, the proper ingestion path.)
  2. Create a Unity Catalog Volume and upload the market-research PDF (+ a
     reference copy of the CSVs).
  3. Provision a Lakebase (managed Postgres) instance — the "operational source
     system" for the online store.
  4. Seed that Lakebase instance with the operational tables (from the CSVs).
     This is the single source of truth the labs ingest FROM.
  5. Print a deployment report.

We ALWAYS assume Lakebase is available in the account. Bronze Delta tables are no
longer pre-loaded — Lab 1 creates them from Lakebase with Lakeflow Connect so the
medallion story is real.

Everything is driven by setup/config.py — change names there, not here.

If a step needs a permission the learner doesn't have, the step prints a clear
TO-DO and continues where possible, rather than crashing the whole notebook.
"""

import csv
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
    """Use the EXISTING catalog and create the bronze/silver/gold schemas in it.

    The catalog (`retail_corp` by default) is assumed to already exist — it is
    created once, up front, either by an admin or by you in the Databricks UI /
    Lab 0 prerequisites. This step therefore does NOT try to create the catalog;
    it only verifies the catalog is reachable and then creates the schemas inside
    it. This avoids requiring the `CREATE CATALOG` metastore privilege here.
    """
    _step(1, f"Use catalog `{cfg['CATALOG']}` and create schemas")
    try:
        spark.sql(f"USE CATALOG {cfg['CATALOG']}")
        print(f"  ✓ using existing catalog {cfg['CATALOG']}")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ could not use catalog `{cfg['CATALOG']}`: {e}")
        print("     This step assumes the catalog already exists. Create it once")
        print("     (admin, or in the Catalog UI), then re-run deploy_all():")
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

    # The CSVs are the seed data for the Lakebase operational DB (step 4). We read
    # them from the local repo path; return that path for the seeding step.
    return os.path.join(root, "data", "bronze")


# ---------------------------------------------------------------------------
# 3. Provision the Lakebase instance (the operational source system)
# ---------------------------------------------------------------------------
def provision_lakebase(spark, cfg):
    _step(3, f"Provision Lakebase instance `{cfg['LAKEBASE_INSTANCE']}`")
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
              "workspace.")
        print("    TO-DO: ask an admin to enable Lakebase / Database Instances for "
              "this workspace, then re-run deploy_all().")
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
        for _ in range(60):
            cur = w.database.get_database_instance(name=inst_name)
            state = str(getattr(cur, "state", ""))
            if "AVAILABLE" in state or "RUNNING" in state:
                print(f"  ✓ Lakebase instance ready (state: {state}).")
                return cur
            time.sleep(10)
        print("  ! Lakebase instance is still starting up. Wait a couple of minutes,")
        print("    then re-run deploy_all() so the seeding step (4) can connect.")
        return inst
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not create Lakebase instance: {e}")
        print("    TO-DO: ask an admin to enable Lakebase / grant you permission to "
              "create Database Instances, then re-run deploy_all().")
        return None


# ---------------------------------------------------------------------------
# 4. Seed the Lakebase Postgres DB with the operational tables
# ---------------------------------------------------------------------------
# Postgres DDL for each operational table (typed columns, primary keys).
_PG_DDL = {
    "dim_product": """
        product_id INT PRIMARY KEY, product_name TEXT, category TEXT,
        subcategory TEXT, list_price NUMERIC(10,2), unit_cost NUMERIC(10,2),
        launch_date DATE, is_active BOOLEAN
    """,
    "dim_customer": """
        customer_id INT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT,
        region TEXT, country TEXT, customer_segment TEXT, signup_date DATE
    """,
    "fact_orders": """
        order_id BIGINT PRIMARY KEY, customer_id INT, order_date DATE,
        order_ts TIMESTAMP, channel TEXT, order_status TEXT,
        shipping_cost NUMERIC(10,2)
    """,
    "fact_order_items": """
        order_item_id BIGINT PRIMARY KEY, order_id BIGINT, product_id INT,
        quantity INT, unit_price NUMERIC(10,2), discount_amount NUMERIC(10,2)
    """,
    "fact_marketing_campaigns": """
        campaign_id INT PRIMARY KEY, campaign_name TEXT, category TEXT,
        channel TEXT, start_date DATE, end_date DATE, spend_usd NUMERIC(12,2),
        impressions BIGINT, clicks BIGINT, conversions INT,
        attributed_revenue_usd NUMERIC(12,2)
    """,
    "fact_sales_forecast": """
        forecast_id INT PRIMARY KEY, category TEXT, forecast_month DATE,
        forecast_revenue_usd NUMERIC(12,2), lower_bound_usd NUMERIC(12,2),
        upper_bound_usd NUMERIC(12,2), model_name TEXT, generated_by TEXT,
        generated_date DATE
    """,
}


def _pg_connect(cfg, instance):
    """
    Open a psycopg connection to the Lakebase Postgres instance using a short-lived
    Databricks OAuth token as the password (Lakebase's standard auth). Returns a
    live connection or raises.
    """
    from databricks.sdk import WorkspaceClient
    import psycopg  # psycopg 3

    w = WorkspaceClient()
    host = getattr(instance, "read_write_dns", None)
    if not host:
        # refresh the instance to get its DNS
        instance = w.database.get_database_instance(name=cfg["LAKEBASE_INSTANCE"])
        host = getattr(instance, "read_write_dns", None)
    if not host:
        raise RuntimeError("Lakebase instance has no read_write_dns yet.")

    # Databricks-issued OAuth token is used as the Postgres password.
    cred = w.database.generate_database_credential(
        instance_names=[cfg["LAKEBASE_INSTANCE"]]
    )
    token = getattr(cred, "token", None) or getattr(cred, "credential", None)
    user = w.current_user.me().user_name

    conn = psycopg.connect(
        host=host, port=5432, dbname=cfg["LAKEBASE_DB"],
        user=user, password=token, sslmode="require", autocommit=True,
    )
    return conn


def seed_lakebase_tables(cfg, instance, csv_dir_local):
    """
    Create and populate the operational tables inside the Lakebase Postgres DB so
    Lab 1 has a real source to ingest FROM with Lakeflow Connect.

    Idempotent: each table is dropped and recreated from its CSV. If Postgres can't
    be reached (driver missing, networking, permissions), it prints clear TO-DOs and
    does NOT hard-fail the notebook.
    """
    _step(4, f"Seed Lakebase database `{cfg['LAKEBASE_DB']}` with operational tables")
    if instance is None:
        print("  ! Skipped — no Lakebase instance available (see step 3).")
        return False

    # psycopg is needed to talk to Postgres. Install on the fly if missing.
    try:
        import psycopg  # noqa: F401
    except Exception:  # noqa: BLE001
        print("  ! Python Postgres driver 'psycopg' not found on this cluster.")
        print("    TO-DO: run  %pip install psycopg[binary]  in a cell above,")
        print("    restart Python, then re-run deploy_all().")
        return False

    try:
        conn = _pg_connect(cfg, instance)
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not connect to Lakebase Postgres: {str(e)[:200]}")
        print("    TO-DO: confirm the instance is AVAILABLE and that your user has")
        print("    the 'databricks_superuser' / connect role on it, then re-run.")
        return False

    total = 0
    with conn:
        cur = conn.cursor()
        for name in cfg["BRONZE_TABLES"]:
            local = os.path.join(csv_dir_local, f"{name}.csv")
            if not os.path.exists(local):
                print(f"  ! CSV missing for {name} — skipped.")
                continue
            ddl = _PG_DDL[name]
            cur.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')
            cur.execute(f'CREATE TABLE "{name}" ({ddl})')
            with open(local, "r", newline="") as fh:
                reader = csv.reader(fh)
                header = next(reader)
                cols = ", ".join(f'"{c}"' for c in header)
                with cur.copy(
                    f'COPY "{name}" ({cols}) FROM STDIN WITH (FORMAT csv)'
                ) as cp:
                    for row in reader:
                        cp.write_row([None if v == "" else v for v in row])
            cnt = cur.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            total += cnt
            print(f"  ✓ postgres table {name:<28} {cnt:>8,} rows")
    conn.close()
    print(f"  ✓ Lakebase seeded: {len(cfg['BRONZE_TABLES'])} tables, {total:,} rows total.")
    print("    Lab 1 will ingest these into the (currently empty) bronze schema.")
    return True


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
    instance = provision_lakebase(spark, cfg)
    seeded = seed_lakebase_tables(cfg, instance, csv_dir)

    # -------- report --------
    print("\n" + "=" * 64)
    print("  DEPLOYMENT REPORT")
    print("=" * 64)
    print(f"  Catalog ........ {cfg['CATALOG']}")
    print(f"  Bronze schema .. {cfg['CATALOG_BRONZE']}  (EMPTY — filled by Lakeflow Connect in Lab 1)")
    print(f"  Silver schema .. {cfg['CATALOG_SILVER']}  (empty — built in Lab 3)")
    print(f"  Gold schema .... {cfg['CATALOG_GOLD']}    (empty — built in Lab 3)")
    print(f"  Volume ......... {cfg['VOLUME_PATH']}")
    print(f"  Lakebase ....... {cfg['LAKEBASE_INSTANCE']} "
          f"({'seeded — ready to ingest' if seeded else 'NOT seeded — see TO-DO above'})")
    print("=" * 64)
    if seeded:
        print("  ✅ Setup complete. Continue to Lab 1: Data Ingestion.")
    else:
        print("  ⚠️  Setup incomplete: Lakebase was not seeded. Resolve the TO-DO "
              "above and re-run deploy_all() before starting Lab 1.")
    return cfg


if __name__ == "__main__":
    deploy_all()
