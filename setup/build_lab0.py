#!/usr/bin/env python3
"""Builds labs/Lab 0 - Setup.ipynb"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbbuild import md, code, write_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cells = [
md("""# Lab 0 — Setup

### Databricks Data Camp for Business Users 🛍️

Welcome, **CEO of Databricks Retail Corp.**

You've just taken the helm of Databricks Retail Corp. — the e-commerce shop that
sells Databricks-branded merchandise (hoodies, tees, caps, socks, bottles, and
more). The company has been *selling* data-driven products but, ironically, has
**never used Databricks for its own analytics**. You're here to change that.

> **Your mission across these labs:** decide **which category of merch to promote
> next quarter**. You'll make a truly data-driven call using current sales, a
> forecast, marketing ROI, and external market research.

**Lab 0 is your setup lab.** By the end you will have:
1. Cloned this repo into your Databricks workspace.
2. Confirmed you have the right **permissions** (with clear TO-DOs if not).
3. Run **one deployment script** that creates everything the other labs need.

⏱️ *Estimated time: 15–20 minutes.*"""),

md("""## 0.1 — Clone this repo into Databricks

Do this once, in the Databricks UI:

1. In the left sidebar, click **Workspace**.
2. Click your username, then the **⋮** (kebab) menu → **Create → Git folder**
   (older workspaces call this **Repo**).
3. Paste the repository URL:
   ```
   https://github.com/nikita-bubentsov_data/data-camp-for-business
   ```
4. Click **Create Git folder**.
5. Open the new folder, then open **`labs/Lab 0 - Setup.ipynb`** (this notebook)
   from *inside* Databricks and continue there.

> 💡 **Attach compute.** At the top-right of the notebook, click **Connect** and
> choose **Serverless** (recommended) or any running cluster with **Unity Catalog**
> enabled. Everything in these labs runs on Serverless."""),

md("""## 0.2 — Load the shared configuration

Every lab shares one config file (`setup/config.py`) so we all use the same
catalog and schema names. Run the cell below to load and print it.

If your workspace requires different names (for example, you're not allowed to
create a catalog called `retail_corp`), **stop and edit `setup/config.py`** —
change the value once there and every lab follows."""),

code("""# Make the setup/ folder importable no matter where the notebook is opened from
import os, sys

def find_repo_root():
    p = os.getcwd()
    for _ in range(6):
        if os.path.isdir(os.path.join(p, "setup")) and os.path.isdir(os.path.join(p, "labs")):
            return p
        p = os.path.dirname(p)
    return os.getcwd()

REPO_ROOT = find_repo_root()
sys.path.insert(0, os.path.join(REPO_ROOT, "setup"))
print("Repo root:", REPO_ROOT)

from config import print_config
cfg = print_config()"""),

md("""## 0.3 — Permissions you need

These labs are written so a **non-admin business user** can complete them. You
don't need to memorize a list — the automated check in the next step tells you
exactly which permissions (if any) are missing and prints copy-paste SQL for your
admin.

> 📄 **Want the full reference?** The complete permission table (what each grant is
> for, and which lab needs it) lives in **[SETUP.md](../SETUP.md)**. If you are *not*
> an admin, that's the page to share with whoever administers your workspace."""),

md("""## 0.4 — Run the automated permission check

This **only reads** your workspace — it changes nothing. For anything missing it
prints an actionable **TO-DO** (SQL for an admin, or a UI step)."""),

code("""from check_permissions import run_all_checks
result = run_all_checks(cfg)

if not result["all_passed"]:
    print("\\n👉 Resolve the ACTION REQUIRED items above (hand the SQL to an admin),")
    print("   then re-run this cell. You can still try the deploy step — it will")
    print("   stop gracefully at the first thing it cannot do.")
else:
    print("\\n🎉 You're clear to deploy. Continue to 0.5.")"""),

md("""## 0.5 — Deploy everything (ONE script)

The single call below deploys **all** the assets the labs need. It is
**idempotent** — safe to run more than once. It will:

1. Create the catalog `retail_corp` and the `bronze` / `silver` / `gold` schemas.
   *(Bronze starts **empty** — you'll fill it in Lab 1 with Lakeflow Connect, the
   proper ingestion path.)*
2. Create a **Volume** and upload the market-research **PDF**.
3. Provision a **Lakebase** (managed Postgres) instance — the "operational source
   system" that powers the online store.
4. **Seed that Lakebase instance** with the operational tables (products, customers,
   orders, marketing, forecast). This is the single source of truth Lab 1 ingests
   *from*.
5. Print a **deployment report**.

If any step needs a permission you don't have, that step prints a TO-DO and the
script continues where it safely can."""),

code("""from deploy_all import deploy_all
cfg = deploy_all(cfg)"""),

md("""## 0.6 — Inspect the Lakebase source instance

The deploy step above provisioned a **Lakebase** (Databricks-managed Postgres)
instance and **seeded it** with your operational tables — this is the database that
stands in for the system running the online store. In **Lab 1** you'll ingest from it
with Lakeflow Connect, so let's confirm it's there and see its connection details."""),

code("""try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    inst = w.database.get_database_instance(name=cfg["LAKEBASE_INSTANCE"])
    print("✓ Lakebase instance found:", inst.name)
    print("  state:", getattr(inst, "state", "n/a"))
    print("  read/write DNS:", getattr(inst, "read_write_dns", "n/a"))
    print("\\n  → In Lab 1 you'll connect Lakeflow Connect to this instance.")
except Exception as e:
    print("! Could not read the Lakebase instance:", str(e)[:200])
    print("  → Re-run the deploy cell (0.5). Lab 1 needs this instance seeded.")"""),

md("""## 0.7 — Verify the deployment

Two quick checks:

1. The **bronze schema is empty** — that's expected. You will fill it in Lab 1 using
   Lakeflow Connect (the proper ingestion path), not by pre-loading.
2. The **Lakebase source is seeded** — the operational tables the deploy step loaded
   into Postgres are ready to be ingested (roughly: ~17.5K orders, ~29K order items,
   1,800 customers, 18 products, 72 campaigns, 15 DS forecast rows)."""),

code("""spark.sql(f"USE CATALOG {cfg['CATALOG']}")
print("Bronze schema (should be EMPTY until Lab 1):")
display(spark.sql(f"SHOW TABLES IN {cfg['CATALOG_BRONZE']}"))"""),

code("""# Confirm the Lakebase Postgres source is seeded and reachable.
try:
    import psycopg, uuid
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    inst = w.database.get_database_instance(name=cfg["LAKEBASE_INSTANCE"])
    cred = w.database.generate_database_credential(request_id=str(uuid.uuid4()), instance_names=[cfg["LAKEBASE_INSTANCE"]])
    token = getattr(cred, "token", None) or getattr(cred, "credential", None)
    conn = psycopg.connect(
        host=inst.read_write_dns, port=5432, dbname=cfg["LAKEBASE_DB"],
        user=w.current_user.me().user_name, password=token,
        sslmode="require", autocommit=True,
    )
    cur = conn.cursor()
    print("Rows in the Lakebase (Postgres) source tables:")
    for t in cfg["BRONZE_TABLES"]:
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t:<28} {n:>8,} rows")
    conn.close()
    print("\\n✓ Lakebase source is ready. Continue to Lab 1 to ingest it into bronze.")
except Exception as e:
    print("! Could not query Lakebase yet:", str(e)[:200])
    print("  → If deploy step 4 printed a TO-DO (e.g. install psycopg, or wait for")
    print("    the instance to become AVAILABLE), resolve it and re-run 0.5.")"""),

md("""## 0.8 — Download the market-research PDF (for later)

Lab 5 asks you to combine your internal data with **external market research**.
That research lives in a PDF in this repo:

```
assets/market_research/Databricks_Retail_Market_Research.pdf
```

**Do this now so it's ready for Lab 5:**
1. In the **Workspace** file browser, open the `assets/market_research/` folder
   of your Git folder.
2. Select `Databricks_Retail_Market_Research.pdf` → **⋮ → Download** to your laptop.
3. Keep it handy — in **Lab 5** you'll upload it into your **Genie Space** so
   Genie can answer questions that blend it with your sales data.

> The deploy script also copied this PDF into your Volume at
> `.../raw_files/market_research/` if you'd rather grab it from there."""),

md("""## ✅ Lab 0 complete

You now have:
- ✅ The repo cloned into Databricks
- ✅ Permissions verified (or clear TO-DOs)
- ✅ Catalog `retail_corp` with `bronze`, `silver`, `gold` schemas (all **empty** for now)
- ✅ A **Volume** holding the market-research PDF
- ✅ A **Lakebase** instance provisioned and **seeded** with the operational tables
- ✅ Bronze is intentionally empty — Lab 1 fills it from Lakebase with Lakeflow Connect

> 📄 **Curious what's in the source tables?** The full data model (every table, its
> grain, and what it contains) is documented in **[SETUP.md](../SETUP.md)**. You'll
> also explore it hands-on in Lab 2.

**Next up → Lab 1: Data Ingestion.** You'll connect to the Lakebase source with
Lakeflow Connect and bring the market-research PDF into Databricks.""")
]

out = os.path.join(ROOT, "labs", "Lab 0 - Setup.ipynb")
write_notebook(out, cells)
print("Wrote", out, "with", len(cells), "cells")
