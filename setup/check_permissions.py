"""
Permission & prerequisite checker for the Databricks Retail Corp. labs.

Run this INSIDE a Databricks notebook (it uses `spark`). It checks everything a
NON-ADMIN learner needs and, for anything missing, prints a copy-pasteable
TO-DO (either SQL for a workspace admin to run, or a UI step) instead of failing
silently.

Usage (from Lab 0, or standalone):

    %run ./setup/check_permissions      # if imported as a notebook
    # or
    from setup.check_permissions import run_all_checks
    run_all_checks()

Nothing here CHANGES your workspace — it only READS and reports. The actual
creation happens in deploy_all.
"""


def _get_spark():
    try:
        return spark  # type: ignore  # noqa: F821
    except NameError:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()


def _current_user(spark):
    return spark.sql("SELECT current_user() AS u").collect()[0]["u"]


def _safe_sql(spark, q):
    try:
        return spark.sql(q), None
    except Exception as e:  # noqa: BLE001
        return None, str(e)


class Check:
    def __init__(self, name):
        self.name = name
        self.passed = None
        self.detail = ""
        self.todo = ""


def run_all_checks(cfg=None):
    """Run every prerequisite check and print a scorecard + TO-DO list."""
    spark = _get_spark()
    if cfg is None:
        try:
            from config import get_config  # when setup/ is on the path
        except Exception:
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), "setup"))
            from config import get_config
        cfg = get_config()

    user = _current_user(spark)
    catalog = cfg["CATALOG"]
    checks = []

    # -- 0. Serverless / cluster is running (we got here, so SQL works) -------
    c = Check("Compute available (can run SQL)")
    c.passed = True
    c.detail = "Notebook is attached to running compute."
    checks.append(c)

    # -- 1. Unity Catalog is enabled -----------------------------------------
    c = Check("Unity Catalog enabled (SHOW CATALOGS works)")
    df, err = _safe_sql(spark, "SHOW CATALOGS")
    if df is not None:
        c.passed = True
        c.detail = f"{df.count()} catalogs visible."
    else:
        c.passed = False
        c.detail = err or "SHOW CATALOGS failed."
        c.todo = ("Unity Catalog may not be enabled for this workspace. Ask a "
                  "metastore admin to enable UC and assign a metastore to this "
                  "workspace.")
    checks.append(c)

    # -- 2. CREATE CATALOG privilege (or catalog already exists) --------------
    c = Check(f"Catalog `{catalog}` exists OR you can create it")
    df, err = _safe_sql(spark, f"SHOW CATALOGS LIKE '{catalog}'")
    exists = df is not None and df.count() > 0
    if exists:
        c.passed = True
        c.detail = f"Catalog `{catalog}` already exists."
    else:
        # Can we see the CREATE CATALOG privilege on the metastore?
        priv_df, _ = _safe_sql(
            spark,
            "SELECT * FROM information_schema.metastore_privileges "
            f"WHERE grantee = '{user}' AND privilege_type = 'CREATE CATALOG'",
        )
        can_create = priv_df is not None and priv_df.count() > 0
        if can_create:
            c.passed = True
            c.detail = "You hold CREATE CATALOG on the metastore."
        else:
            c.passed = False
            c.detail = f"Catalog `{catalog}` not found and no CREATE CATALOG grant detected."
            c.todo = (
                "Ask a metastore admin to run ONE of:\n"
                f"    -- Option A: let this user create the catalog\n"
                f"    GRANT CREATE CATALOG ON METASTORE TO `{user}`;\n"
                f"    -- Option B: admin pre-creates it and grants you ownership\n"
                f"    CREATE CATALOG IF NOT EXISTS {catalog};\n"
                f"    ALTER CATALOG {catalog} OWNER TO `{user}`;\n"
                "  (Option B is easiest if you are not allowed CREATE CATALOG.)"
            )
    checks.append(c)

    # -- 3. USE + CREATE SCHEMA on the catalog (if it exists) -----------------
    c = Check(f"Can create schemas/tables in `{catalog}`")
    if exists:
        priv_df, _ = _safe_sql(
            spark,
            "SELECT privilege_type FROM information_schema.catalog_privileges "
            f"WHERE grantee IN ('{user}','account users') AND catalog_name = '{catalog}'",
        )
        privs = set()
        if priv_df is not None:
            privs = {r["privilege_type"] for r in priv_df.collect()}
        needed = {"ALL PRIVILEGES"} | {"USE CATALOG", "CREATE SCHEMA"}
        if "ALL PRIVILEGES" in privs or {"USE CATALOG", "CREATE SCHEMA"}.issubset(privs):
            c.passed = True
            c.detail = f"Grants present: {sorted(privs) or 'owner'}."
        else:
            c.passed = False
            c.detail = f"Grants found: {sorted(privs) or 'none'}."
            c.todo = (
                "Ask the catalog owner/admin to run:\n"
                f"    GRANT USE CATALOG, CREATE SCHEMA ON CATALOG {catalog} TO `{user}`;\n"
                f"    GRANT USE SCHEMA, CREATE TABLE, SELECT, MODIFY ON CATALOG {catalog} TO `{user}`;"
            )
    else:
        c.passed = None
        c.detail = "Skipped — catalog does not exist yet (see check above)."
    checks.append(c)

    # -- 4. Can create a Volume (needed for CSVs + PDF) -----------------------
    c = Check("Can create a Unity Catalog Volume")
    if exists:
        c.passed = True
        c.detail = ("CREATE VOLUME is covered by CREATE TABLE-level grants on the "
                    "schema; deploy_all will create it.")
    else:
        c.passed = None
        c.detail = "Skipped — catalog does not exist yet."
    checks.append(c)

    # -- 5. SQL Warehouse present (for Genie / dashboards later) --------------
    c = Check("A SQL Warehouse exists (Genie, metric views, dashboards)")
    # We can't list warehouses via SQL; give guidance instead.
    c.passed = True
    c.detail = ("Not checkable via SQL. Confirm in the UI: SQL > SQL Warehouses. "
                "A Serverless SQL Warehouse is recommended for Labs 4-6.")
    c.todo = ("If you have NO SQL Warehouse: ask a workspace admin, or in the UI go "
              "to SQL > SQL Warehouses > Create, and pick Serverless (2X-Small).")
    checks.append(c)

    # -- 6. Lakeflow / DLT entitlement (Lab 3) --------------------------------
    c = Check("Lakeflow Declarative Pipelines available (Lab 3)")
    c.passed = True
    c.detail = ("Not checkable via SQL. Lab 3 uses Lakeflow Designer (Pipelines). "
                "Confirm the 'Jobs & Pipelines' menu is visible in the left nav.")
    checks.append(c)

    # -- 7. Genie / AI features (Labs 2, 4, 5, 6) -----------------------------
    c = Check("Genie & AI/BI available (Labs 2, 4, 5, 6)")
    c.passed = True
    c.detail = ("Not checkable via SQL. Confirm 'Genie' and 'Dashboards' appear "
                "in the left nav. Requires Databricks Assistant enabled by admin.")
    c.todo = ("If Genie is missing: ask a workspace admin to enable the Databricks "
              "Assistant and AI features in Settings > Advanced.")
    checks.append(c)

    # ---- Print scorecard ----------------------------------------------------
    print("\n" + "=" * 66)
    print(f"  PREREQUISITE CHECK  —  user: {user}")
    print("=" * 66)
    icons = {True: "[ PASS ]", False: "[ FAIL ]", None: "[ SKIP ]"}
    for c in checks:
        print(f"{icons[c.passed]}  {c.name}")
        if c.detail:
            print(f"          {c.detail}")
    print("=" * 66)

    todos = [c for c in checks if c.passed is False and c.todo]
    warnings = [c for c in checks if c.passed is True and c.todo]

    if todos:
        print("\n  ⚠️  ACTION REQUIRED before continuing — hand these to an admin:\n")
        for i, c in enumerate(todos, 1):
            print(f"  {i}. {c.name}")
            for line in c.todo.splitlines():
                print(f"       {line}")
            print()
    else:
        print("\n  ✅ No blocking permission issues detected. You can run deploy_all.\n")

    if warnings:
        print("  ℹ️  Manual things to confirm in the UI (not blocking):\n")
        for c in warnings:
            print(f"   • {c.name}")
            for line in c.todo.splitlines():
                print(f"       {line}")
        print()

    return {
        "user": user,
        "blocking": [c.name for c in todos],
        "all_passed": len(todos) == 0,
    }


if __name__ == "__main__":
    run_all_checks()
