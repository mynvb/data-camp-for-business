#!/usr/bin/env python3
"""Builds labs/Lab 3 - Transform Data.ipynb"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbbuild import md, code, write_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cells = [
md("""# Lab 3 — Transform Data (Medallion: Bronze → Silver → Gold)

### Databricks Data Camp for Business Users 🛍️

**Story so far:** You've ingested (Lab 1) and discovered (Lab 2) your data. But
bronze is *raw* — it has cancelled orders mixed in, no joined-up view, and no
business-ready aggregates. To answer *"which category should we promote?"* you
need **clean, trustworthy tables**.

You'll use **Lakeflow Designer** — a **visual, no-/low-code pipeline builder** — to
apply the **medallion architecture**:

- 🥉 **Bronze** = raw, as-ingested (you already have this).
- 🥈 **Silver** = cleaned & joined (one tidy sales table; validated marketing).
- 🥇 **Gold** = business-ready aggregates (category performance, daily revenue).

Then you'll **schedule a daily job** to keep gold fresh.

For each build step you'll get: **(a)** the plain-English instruction to type into
Lakeflow Designer, and **(b)** SQL you can run here to **validate** the result.

⏱️ *Estimated time: 40–45 minutes.*"""),

md("""## 3.0 — Load config"""),

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
print("Bronze:", cfg["CATALOG_BRONZE"])
print("Silver:", cfg["CATALOG_SILVER"])
print("Gold:  ", cfg["CATALOG_GOLD"])"""),

md("""## 3.1 — Meet Lakeflow Designer

**Lakeflow Designer** is a visual canvas where you build a data pipeline by
describing transformations in plain language and connecting boxes — Databricks
generates the underlying pipeline for you. It's the business-analyst-friendly way
to build the same **Lakeflow Declarative Pipelines** an engineer would write in code.

### Open it
1. Left sidebar → **Jobs & Pipelines** → **Create → ETL Pipeline** (Lakeflow), or
   look for **Lakeflow Designer** directly.
2. Start a new pipeline named **`retail_corp_medallion`**.
3. Set the pipeline's **default catalog** to `retail_corp` and **target schema**
   handling so silver objects go to `silver` and gold to `gold` (you can set the
   schema per table/dataset).
4. Add your **source** tables from `retail_corp.bronze`.

> 🧭 **How the "text examples" below work:** Lakeflow Designer lets you describe a
> transformation in natural language (and/or configure joins visually). For each
> silver/gold table we give you **exactly what to type**. After you build it,
> run the matching **validation SQL** cell here to confirm it's correct.

> ⚠️ **No Lakeflow Designer in your workspace?** You can still complete the lab: run
> the provided "reference build" SQL cells (clearly marked) to create the same
> silver/gold tables directly, then run the validations. The learning goal — a
> correct medallion — is identical."""),

md("""## 3.2 — Silver table #1: `silver.sales`

**Goal:** one clean, analysis-ready sales table at the **order-line grain**, with
cancelled orders removed and product attributes joined in.

### 👉 Type this into Lakeflow Designer (natural-language transformation)
> *"Create a table called **sales** in the **silver** schema. Start from
> **bronze.fact_order_items**. Join **bronze.fact_orders** on `order_id` and
> **bronze.dim_product** on `product_id`. Exclude orders where `order_status` is
> **CANCELLED**. Keep these columns: order_id, order_date, channel, order_status,
> customer_id, product_id, product_name, category, subcategory, quantity,
> unit_price, unit_cost, discount_amount. Add a computed column **line_revenue** =
> quantity × unit_price, and **line_profit** = quantity × (unit_price − unit_cost)."*

### Join logic (for the visual editor)
| Left | Right | Join key | Type |
|------|-------|----------|------|
| `fact_order_items` | `fact_orders` | `order_id` | inner |
| `fact_order_items` | `dim_product` | `product_id` | inner |

Filter: `order_status <> 'CANCELLED'`."""),

code("""# --- REFERENCE BUILD (use only if you're NOT using Lakeflow Designer) ---
# This creates the exact silver.sales table the Designer step above produces.
S = cfg["CATALOG_SILVER"]; B = cfg["CATALOG_BRONZE"]
spark.sql(f'''
CREATE OR REPLACE TABLE {S}.sales AS
SELECT
    o.order_id,
    o.order_date,
    o.channel,
    o.order_status,
    o.customer_id,
    oi.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    oi.quantity,
    oi.unit_price,
    p.unit_cost,
    oi.discount_amount,
    oi.quantity * oi.unit_price                       AS line_revenue,
    oi.quantity * (oi.unit_price - p.unit_cost)       AS line_profit
FROM {B}.fact_order_items oi
JOIN {B}.fact_orders  o ON oi.order_id  = o.order_id
JOIN {B}.dim_product  p ON oi.product_id = p.product_id
WHERE o.order_status <> 'CANCELLED'
''')
print("✓ built", f"{S}.sales")"""),

md("""### ✅ Validate `silver.sales`

Run these checks whether you built the table in Designer or via the reference SQL.
They confirm the join logic and filter are correct."""),

code("""S = cfg["CATALOG_SILVER"]; B = cfg["CATALOG_BRONZE"]

print("CHECK 1 — no CANCELLED orders leaked in:")
display(spark.sql(f"SELECT order_status, COUNT(*) n FROM {S}.sales GROUP BY order_status"))

print("CHECK 2 — row count equals non-cancelled bronze line items (join didn't drop/duplicate):")
display(spark.sql(f'''
    SELECT
      (SELECT COUNT(*) FROM {S}.sales) AS silver_rows,
      (SELECT COUNT(*)
         FROM {B}.fact_order_items oi
         JOIN {B}.fact_orders o ON oi.order_id = o.order_id
         WHERE o.order_status <> 'CANCELLED') AS expected_rows
'''))"""),

code("""# CHECK 3 — computed columns are correct (no rows should violate these)
bad = spark.sql(f'''
    SELECT COUNT(*) AS bad_rows FROM {S}.sales
    WHERE ROUND(line_revenue, 2) <> ROUND(quantity * unit_price, 2)
       OR ROUND(line_profit, 2)  <> ROUND(quantity * (unit_price - unit_cost), 2)
''').collect()[0]["bad_rows"]
print("Rows with incorrect line_revenue/line_profit:", bad, "(should be 0)")
assert bad == 0, "Computed columns are wrong — recheck your Designer formulas."
print("✓ silver.sales validated")"""),

md("""## 3.3 — Silver table #2: `silver.marketing`

**Goal:** a clean marketing table with a computed **campaign ROI** (return on ad
spend), ready to roll up by category.

### 👉 Type this into Lakeflow Designer
> *"Create a table **marketing** in the **silver** schema from
> **bronze.fact_marketing_campaigns**. Keep campaign_id, campaign_name, category,
> channel, start_date, spend_usd, impressions, clicks, conversions,
> attributed_revenue_usd. Add a computed column **campaign_roi** =
> attributed_revenue_usd ÷ spend_usd. Exclude any rows where spend_usd is 0 or
> null."*"""),

code("""# --- REFERENCE BUILD (skip if using Lakeflow Designer) ---
S = cfg["CATALOG_SILVER"]; B = cfg["CATALOG_BRONZE"]
spark.sql(f'''
CREATE OR REPLACE TABLE {S}.marketing AS
SELECT
    campaign_id, campaign_name, category, channel, start_date,
    spend_usd, impressions, clicks, conversions, attributed_revenue_usd,
    ROUND(attributed_revenue_usd / spend_usd, 3) AS campaign_roi
FROM {B}.fact_marketing_campaigns
WHERE spend_usd IS NOT NULL AND spend_usd > 0
''')
print("✓ built", f"{S}.marketing")"""),

code("""# ✅ Validate silver.marketing
S = cfg["CATALOG_SILVER"]
print("CHECK — ROI computed and positive; every category represented:")
display(spark.sql(f'''
    SELECT category,
           COUNT(*)               AS campaigns,
           ROUND(SUM(spend_usd),0)              AS total_spend,
           ROUND(SUM(attributed_revenue_usd),0) AS total_attributed,
           ROUND(SUM(attributed_revenue_usd)/SUM(spend_usd),2) AS blended_roi
    FROM {S}.marketing
    GROUP BY category
    ORDER BY blended_roi DESC
'''))
print("Expect: Outerwear has the HIGHEST blended ROI (~4.x), Accessories the lowest (~1.8).")"""),

md("""## 3.4 — Gold table #1: `gold.category_performance`

This is the **decision table** — one row per category with the KPIs you'll use to
choose what to promote: revenue, profit, margin, units, and marketing ROI.

### 👉 Type this into Lakeflow Designer
> *"Create a table **category_performance** in the **gold** schema. From
> **silver.sales**, group by **category** and compute: total_revenue = sum of
> line_revenue, total_profit = sum of line_profit, units_sold = sum of quantity,
> order_lines = count of rows, and profit_margin_pct = total_profit ÷ total_revenue
> × 100. Then join **silver.marketing** aggregated by category to add marketing_spend
> = sum of spend_usd and marketing_attributed_revenue = sum of attributed_revenue_usd,
> and compute marketing_roi = marketing_attributed_revenue ÷ marketing_spend."*"""),

code("""# --- REFERENCE BUILD (skip if using Lakeflow Designer) ---
G = cfg["CATALOG_GOLD"]; S = cfg["CATALOG_SILVER"]
spark.sql(f'''
CREATE OR REPLACE TABLE {G}.category_performance AS
WITH s AS (
    SELECT category,
           SUM(line_revenue)  AS total_revenue,
           SUM(line_profit)   AS total_profit,
           SUM(quantity)      AS units_sold,
           COUNT(*)           AS order_lines
    FROM {S}.sales
    GROUP BY category
),
m AS (
    SELECT category,
           SUM(spend_usd)               AS marketing_spend,
           SUM(attributed_revenue_usd)  AS marketing_attributed_revenue
    FROM {S}.marketing
    GROUP BY category
)
SELECT
    s.category,
    ROUND(s.total_revenue, 2)                              AS total_revenue,
    ROUND(s.total_profit, 2)                               AS total_profit,
    s.units_sold,
    s.order_lines,
    ROUND(100 * s.total_profit / s.total_revenue, 1)       AS profit_margin_pct,
    ROUND(m.marketing_spend, 2)                            AS marketing_spend,
    ROUND(m.marketing_attributed_revenue, 2)              AS marketing_attributed_revenue,
    ROUND(m.marketing_attributed_revenue / m.marketing_spend, 2) AS marketing_roi
FROM s LEFT JOIN m ON s.category = m.category
''')
print("✓ built", f"{G}.category_performance")
display(spark.table(f"{G}.category_performance").orderBy("total_profit", ascending=False))"""),

code("""# ✅ Validate gold.category_performance
G = cfg["CATALOG_GOLD"]; S = cfg["CATALOG_SILVER"]
print("CHECK 1 — gold revenue by category matches silver (gold is just an aggregate):")
display(spark.sql(f'''
    SELECT g.category,
           g.total_revenue AS gold_revenue,
           ROUND(s.chk, 2) AS silver_revenue,
           ROUND(g.total_revenue - s.chk, 2) AS difference
    FROM {G}.category_performance g
    JOIN (SELECT category, SUM(line_revenue) chk FROM {S}.sales GROUP BY category) s
      ON g.category = s.category
    ORDER BY gold_revenue DESC
'''))
print("All differences should be ~0.00")"""),

code("""# CHECK 2 — the business punchline: rank categories by each KPI
G = cfg["CATALOG_GOLD"]
display(spark.sql(f'''
    SELECT category, total_revenue, total_profit, profit_margin_pct,
           units_sold, marketing_roi
    FROM {G}.category_performance
    ORDER BY total_profit DESC
'''))
print("Notice the tension you'll resolve in Labs 4-5:")
print("  • Outerwear leads on PROFIT $ and MARKETING ROI.")
print("  • T-Shirts & Accessories lead on UNITS.")
print("  • Accessories has a high MARGIN % but tiny profit $ and worst ROI.")
print("  → 'What to promote' depends on which KPI you trust. That's Lab 4.")"""),

md("""## 3.5 — Gold table #2: `gold.daily_revenue`

For the dashboards in Lab 6 you'll want a **daily time series**. Build a gold table
at the **date × category** grain.

### 👉 Type this into Lakeflow Designer
> *"Create a table **daily_revenue** in the **gold** schema from **silver.sales**.
> Group by **order_date** and **category**. Compute daily_revenue = sum of
> line_revenue, daily_profit = sum of line_profit, daily_units = sum of quantity,
> and orders = count of distinct order_id."*"""),

code("""# --- REFERENCE BUILD (skip if using Lakeflow Designer) ---
G = cfg["CATALOG_GOLD"]; S = cfg["CATALOG_SILVER"]
spark.sql(f'''
CREATE OR REPLACE TABLE {G}.daily_revenue AS
SELECT
    order_date,
    category,
    ROUND(SUM(line_revenue), 2)      AS daily_revenue,
    ROUND(SUM(line_profit), 2)       AS daily_profit,
    SUM(quantity)                    AS daily_units,
    COUNT(DISTINCT order_id)         AS orders
FROM {S}.sales
GROUP BY order_date, category
''')
print("✓ built", f"{G}.daily_revenue")"""),

code("""# ✅ Validate gold.daily_revenue
G = cfg["CATALOG_GOLD"]
print("CHECK 1 — daily totals sum back to the category_performance totals:")
display(spark.sql(f'''
    SELECT d.category,
           ROUND(SUM(d.daily_revenue),2) AS summed_daily,
           ROUND(MAX(c.total_revenue),2) AS category_total,
           ROUND(SUM(d.daily_revenue) - MAX(c.total_revenue),2) AS diff
    FROM {G}.daily_revenue d
    JOIN {G}.category_performance c ON d.category = c.category
    GROUP BY d.category ORDER BY category_total DESC
'''))
print("CHECK 2 — date coverage looks continuous:")
display(spark.sql(f"SELECT MIN(order_date) first_day, MAX(order_date) last_day, "
                  f"COUNT(DISTINCT order_date) distinct_days FROM {G}.daily_revenue"))"""),

md("""## 3.6 — Schedule a daily refresh (Job)

Gold tables must stay current. In real life your pipeline reruns on a schedule.

### Do it in the UI (recommended)
1. In your **Lakeflow pipeline** (`retail_corp_medallion`), click **Schedule** →
   **Add schedule**.
2. Set it to run **daily** (e.g. 06:00). Databricks creates a **Job** that triggers
   the pipeline. Name the job **`retail_corp_gold_daily_refresh`**.
3. Save. Your silver + gold tables now refresh every morning from the latest bronze.

### Or create the Job from code (below)
This creates a scheduled Job that reruns *this notebook's* build steps daily. It's
a simple, dependency-free alternative to the pipeline schedule."""),

code("""# Create a daily Job via the SDK. Idempotent-ish: it looks for an existing job by name.
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

job_name = cfg["GOLD_JOB_NAME"]
try:
    w = WorkspaceClient()
    existing = [j for j in w.jobs.list(name=job_name)]
    if existing:
        print(f"✓ Job '{job_name}' already exists (job_id={existing[0].job_id}).")
    else:
        this_nb = None
        try:
            this_nb = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
        except Exception:
            pass
        if this_nb:
            created = w.jobs.create(
                name=job_name,
                tasks=[jobs.Task(
                    task_key="refresh_gold",
                    notebook_task=jobs.NotebookTask(notebook_path=this_nb),
                )],
                schedule=jobs.CronSchedule(
                    quartz_cron_expression="0 0 6 * * ?",   # daily 06:00
                    timezone_id="UTC",
                ),
            )
            print(f"✓ Created daily Job '{job_name}' (job_id={created.job_id}). Runs 06:00 UTC.")
        else:
            print("Could not resolve this notebook's path automatically.")
            print("→ Use the UI steps above to schedule the pipeline instead.")
except Exception as e:
    print("Could not create Job automatically:", str(e)[:200])
    print("→ Use the UI steps in 3.6 to add a daily schedule to your pipeline.")"""),

md("""## ✅ Lab 3 complete

You built a full **medallion** with Lakeflow Designer (or the reference SQL) and
validated every step:
- ✅ 🥈 `silver.sales` — clean, joined, cancelled orders removed, profit computed
- ✅ 🥈 `silver.marketing` — campaign ROI computed
- ✅ 🥇 `gold.category_performance` — the decision table (revenue, profit, margin, ROI)
- ✅ 🥇 `gold.daily_revenue` — daily time series for dashboards
- ✅ ⏰ a **daily job** to keep gold fresh

> 🧠 **Takeaway:** you saw a real analytical tension in the gold data — the "best"
> category flips depending on whether you look at revenue, units, margin %, or
> profit $. To stop people arguing past each other, the company needs **agreed
> definitions** of each KPI. That's Lab 4.

**Next up → Lab 4: Define business-level KPIs** with **Metric Views**, so everyone
uses the *same* definition of revenue, profit, cost, and marketing ROI.""")
]

out = os.path.join(ROOT, "labs", "Lab 3 - Transform Data.ipynb")
write_notebook(out, cells)
print("Wrote", out, "with", len(cells), "cells")
