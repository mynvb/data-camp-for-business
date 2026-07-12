#!/usr/bin/env python3
"""Builds labs/Lab 1 - Data Ingestion.ipynb"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbbuild import md, code, write_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cells = [
md("""# Lab 1 — Data Ingestion: Connect Your Data Sources

### Databricks Data Camp for Business Users 🛍️

**Story so far:** As the new CEO of Databricks Retail Corp., you've set up your
workspace (Lab 0). Your sales data currently lives in an **operational database**
— a **Lakebase** (Databricks-managed Postgres) instance that powers the online
store. On top of that, your strategy team has handed you a **PDF of external
market research**.

To become data-driven, you first need to **get all of this into Databricks**.

In this lab you will:
1. Understand the **two kinds of sources** you're ingesting (a database + files).
2. Use **Lakeflow Connect** to ingest the Lakebase Postgres tables into Unity Catalog.
3. Bring the **market-research PDF** into Databricks.
4. Confirm everything landed in your **bronze** layer.

⏱️ *Estimated time: 25–30 minutes.*"""),

md("""## 1.0 — Load config

Run this first in every lab. It reconnects you to the shared catalog/schema names
from `setup/config.py`."""),

code("""import os, sys
def find_repo_root():
    p = os.getcwd()
    for _ in range(6):
        if os.path.isdir(os.path.join(p, "setup")) and os.path.isdir(os.path.join(p, "labs")):
            return p
        p = os.path.dirname(p)
    return os.getcwd()
REPO_ROOT = find_repo_root()
sys.path.insert(0, os.path.join(REPO_ROOT, "setup"))
from config import get_config
cfg = get_config()
spark.sql(f"USE CATALOG {cfg['CATALOG']}")
print("Catalog:", cfg["CATALOG"], "| Bronze:", cfg["CATALOG_BRONZE"])
print("Lakebase instance:", cfg["LAKEBASE_INSTANCE"])"""),

md("""## 1.1 — What is Lakeflow Connect? (plain-English version)

Think of your data as living in different "buildings":

- 🏢 **The operational database (Lakebase Postgres)** — this is where your live
  store writes every order and customer. It's great for *running* the store, but
  not for *analyzing* it.
- 📄 **Files** — spreadsheets, and in our case a **PDF** of market research.

**Lakeflow Connect** is Databricks' built-in way to **bring data from those other
buildings into your lakehouse** — reliably and on a schedule — without you writing
plumbing code. You point it at a source, pick the tables, and it lands them in
Unity Catalog (your **bronze** layer = the raw, faithful copy).

> **Medallion architecture preview:** we land raw data in **bronze**, clean/join it
> into **silver** (Lab 3), then build business-ready **gold** tables (Lab 3). Bronze
> = "as received."

In Lab 0's deploy step, we also loaded the same tables straight into bronze so the
labs work even if Lakebase isn't enabled in your workspace. **This lab shows you
the *proper* ingestion path** you'd use in real life."""),

md("""## 1.2 — Inspect the Lakebase source instance

Your Lakebase instance was provisioned in Lab 0. Let's confirm it's there and see
its connection details. (If Lakebase isn't enabled in your workspace, this cell
tells you — and you can safely skip to **1.5**, because the bronze tables already
exist from Lab 0.)"""),

code("""lakebase_ok = False
try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    inst = w.database.get_database_instance(name=cfg["LAKEBASE_INSTANCE"])
    print("✓ Lakebase instance found:", inst.name)
    print("  state:", getattr(inst, "state", "n/a"))
    print("  read/write DNS:", getattr(inst, "read_write_dns", "n/a"))
    lakebase_ok = True
except Exception as e:
    print("! Lakebase not available in this workspace:", str(e)[:200])
    print("  → No problem. The bronze tables from Lab 0 let you complete every lab.")
    print("  → Skip ahead to section 1.5 and read 1.3–1.4 for understanding.")"""),

md("""## 1.3 — Ingest with Lakeflow Connect (guided UI steps)

This is the part you do **in the Databricks UI** — it's the click-through a
business user would actually use. Follow along:

1. In the left sidebar, click **Data Ingestion** (or **+ New → Add data**).
2. Choose **Lakeflow Connect**, then pick the **PostgreSQL / Lakebase** source.
3. **Connection:**
   - Select your existing instance **`retail-corp-lakebase`**.
   - Database: **`retail_corp`**.
   - Authentication is handled by Databricks (OAuth) — you don't manage passwords.
4. **Select the tables to ingest** (choose all six):
   - `dim_product`
   - `dim_customer`
   - `fact_orders`
   - `fact_order_items`
   - `fact_marketing_campaigns`
   - `fact_sales_forecast`  *(the Data Science team's forecast hand-off — you'll
     put it to the test in Lab 5)*
5. **Destination:**
   - Catalog: **`retail_corp`**
   - Schema: **`bronze`**
6. **Schedule:** choose **Manual / Triggered** for the lab (in production you'd
   pick a cadence, e.g. hourly). Name the ingestion pipeline
   `retail_corp_bronze_ingest`.
7. Click **Create** and then **Run**.

> 🧭 **Don't see the PostgreSQL connector?** Lakeflow Connect connectors are
> enabled per workspace. If it's missing, that's an admin toggle — for the labs
> you can rely on the bronze tables already created in Lab 0 and continue.

When the pipeline finishes, it will have written (or refreshed) the six tables in
`retail_corp.bronze`. The next cells verify that."""),

md("""## 1.4 — (Optional, technical) Ingest via code

Prefer to *see* the mechanics instead of clicking? This optional cell reads the
Lakebase Postgres tables directly and writes them into bronze — essentially what
the UI does under the hood. **Skip it if the UI path worked** or if Lakebase isn't
enabled. It's here for the curious."""),

code("""# OPTIONAL — only runs if Lakebase is reachable. Safe to skip.
if lakebase_ok:
    try:
        # Databricks can query a Lakebase instance via a registered connection.
        # The exact connection name depends on your workspace; this demonstrates
        # the pattern. If it errors, just use the UI path in 1.3.
        for t in cfg["BRONZE_TABLES"]:
            print(f"(demo) would read postgres table '{t}' and write to "
                  f"{cfg['CATALOG_BRONZE']}.{t}")
        print("\\nℹ️  In practice Lakeflow Connect (1.3) manages this for you,")
        print("   including schema drift and incremental refresh.")
    except Exception as e:
        print("Code path not available here — use the UI path in 1.3. Detail:", str(e)[:150])
else:
    print("Skipped — Lakebase not enabled. Bronze tables from Lab 0 are ready.")"""),

md("""## 1.5 — Verify the bronze layer

However the data got there (Lakeflow Connect UI, code, or Lab 0's loader), you
should now have six populated bronze tables. Let's confirm."""),

code("""from pyspark.sql import functions as F

rows = []
for t in cfg["BRONZE_TABLES"]:
    fqn = f"{cfg['CATALOG_BRONZE']}.{t}"
    try:
        rows.append((t, spark.table(fqn).count()))
    except Exception as e:
        rows.append((t, f"MISSING — {str(e)[:60]}"))

print(f"{'bronze table':<30}{'rows':>12}")
print("-" * 42)
for t, c in rows:
    print(f"{t:<30}{c:>12,}" if isinstance(c, int) else f"{t:<30}{c:>12}")"""),

code("""# Quick business peek: revenue by category straight from bronze.
# (We haven't built clean silver/gold yet — this is a rough look.)
display(spark.sql(f'''
    SELECT p.category,
           ROUND(SUM(oi.unit_price * oi.quantity), 0) AS gross_revenue_usd,
           SUM(oi.quantity)                            AS units_sold
    FROM {cfg['CATALOG_BRONZE']}.fact_order_items oi
    JOIN {cfg['CATALOG_BRONZE']}.dim_product p ON oi.product_id = p.product_id
    JOIN {cfg['CATALOG_BRONZE']}.fact_orders o ON oi.order_id = o.order_id
    WHERE o.order_status <> 'CANCELLED'
    GROUP BY p.category
    ORDER BY gross_revenue_usd DESC
'''))"""),

md("""## 1.6 — Bring in the market-research PDF

Your last source is the **external market-research PDF**. There are two ways it
reaches Databricks; you'll use whichever fits:

**A. It's already in your Volume (from Lab 0's deploy).** Verify with the cell below.

**B. You'll upload it into a Genie Space in Lab 5.** Lab 5 needs the PDF attached
to a Genie Space so Genie can read it. You downloaded the PDF to your laptop at the
end of Lab 0 — keep it ready. (Genie Spaces read attachments directly; you don't
need to parse the PDF here.)

For now, just confirm the file is available."""),

code("""pdf_dir = f"{cfg['VOLUME_PATH']}/market_research"
try:
    files = dbutils.fs.ls(pdf_dir)
    print("Files in", pdf_dir, ":")
    for f in files:
        print("  •", f.name, f"({f.size:,} bytes)")
    print("\\n✓ The market-research PDF is in your Volume. In Lab 5 you'll upload")
    print("  it (from your laptop copy) into a Genie Space.")
except Exception as e:
    print("PDF not found in the Volume:", str(e)[:150])
    print("→ That's OK. You downloaded it from assets/market_research/ in Lab 0.")
    print("  You'll upload it into a Genie Space in Lab 5.")"""),

md("""## ✅ Lab 1 complete

You've connected your data sources:
- ✅ Understood **Lakeflow Connect** and when to use it
- ✅ Ingested the Lakebase Postgres tables into **bronze** (UI, code, or Lab 0 loader)
- ✅ Verified all six bronze tables have data
- ✅ Located the market-research **PDF** for Lab 5
- ✅ Took a first rough peek at revenue by category

> 👀 **Early hint:** in that rough peek, **T-Shirts & Tops** and **Accessories**
> look big on *units*, while **Outerwear** leads on *revenue*. Is revenue the right
> way to choose what to promote? Or profit? Or growth? That's exactly what the next
> labs will make rigorous.

**Next up → Lab 2: Data Discovery.** You'll use Unity Catalog, Genie One, and
Domains to explore what data you actually have — and fix any missing metadata.""")
]

out = os.path.join(ROOT, "labs", "Lab 1 - Data Ingestion.ipynb")
write_notebook(out, cells)
print("Wrote", out, "with", len(cells), "cells")
