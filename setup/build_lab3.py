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

This is a **UI-first** lab: you build the whole pipeline visually in **Lakeflow
Designer** by describing each table in plain English. For every table you'll get the
**exact text to type** and how to **verify it in the UI**. (Optional SQL is provided
at the end of each step for anyone who wants to double-check with numbers — skip it if
the UI looks right.)

⏱️ *Estimated time: 40–45 minutes.*"""),

md("""## 3.0 — (Optional) Load config

You only need this cell **if** you plan to run the *Optional* reference-build or
double-check SQL cells later in the lab. If you're doing everything in the Lakeflow
Designer UI (the main path), you can skip it."""),

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
> silver/gold table we give you **exactly what to type**. After you build it, verify
> it **in the UI** (Catalog → Sample Data / row count).

> ⚠️ **No Lakeflow Designer in your workspace?** Each step also includes an **Optional
> reference-build** cell (clearly marked) that creates the same table with SQL, so you
> can still complete the lab. The learning goal — a correct medallion — is identical."""),

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

md("""### ✅ Validate `silver.sales` — in the UI

After the pipeline runs, confirm the table looks right without any code:

1. **Catalog** → `retail_corp.silver.sales` → **Sample Data**. Check that
   `line_revenue` and `line_profit` columns are present and populated, and that
   `product_name` / `category` came through from the join.
2. **Overview** tab → check the **row count** looks reasonable (~28K line items).
3. Still on Sample Data, use the column filter on **`order_status`** — you should see
   **no `CANCELLED`** rows (the filter worked).
4. In **Lakeflow Designer**, the table node shows a **row count and data preview** as
   it runs — a quick visual confirmation the join produced the expected rows.

> ✅ **What "good" looks like:** `line_revenue` = quantity × unit_price on each row,
> no cancelled orders, and roughly the same row count as bronze `fact_order_items`
> minus cancellations."""),

md("""### 🔎 (Optional) Double-check `silver.sales` with SQL

Prefer exact numbers? These cells assert the join logic and computed columns are
correct. **Skip them if the UI checks above looked good.** *(Run 3.0 first.)*"""),

code("""# OPTIONAL — reference build (use only if you're NOT using Lakeflow Designer).
# Creates the exact silver.sales table the Designer step above produces.
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

code("""# OPTIONAL — numeric validation of the join logic and filter.
S = cfg["CATALOG_SILVER"]; B = cfg["CATALOG_BRONZE"]

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
'''))

# CHECK 3 — computed columns are correct (no rows should violate these)
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
> null."*

### ✅ Validate `silver.marketing` — in the UI
1. **Catalog** → `retail_corp.silver.marketing` → **Sample Data**. Confirm the new
   **`campaign_roi`** column is present and looks like a small multiple (≈1.5–5.0).
2. **Overview** → row count should be ~72 (one per campaign/month, minus any with
   zero spend).

> 🔎 **(Optional) Double-check with SQL** — the cell below rolls ROI up by category.
> Skip if the UI looked right. *(Run 3.0 first.)*"""),

code("""# OPTIONAL — reference build + validation for silver.marketing.
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
print("✓ built", f"{S}.marketing")

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
> and compute marketing_roi = marketing_attributed_revenue ÷ marketing_spend."*

### ✅ Validate `gold.category_performance` — in the UI
1. **Catalog** → `retail_corp.gold.category_performance` → **Sample Data**. You should
   see **one row per category** (5 rows) with columns for revenue, profit, margin %,
   units, and marketing ROI.
2. Sort/scan the preview and notice the **tension** you'll resolve in Labs 4–5:
   - **Outerwear** leads on **profit $** and **marketing ROI**.
   - **T-Shirts** and **Accessories** lead on **units**.
   - **Accessories** has a high **margin %** but small profit $ and the worst ROI.
   - So "what to promote" depends on *which* KPI you trust — exactly why Lab 4 exists.

> 🔎 **(Optional) Double-check with SQL** — confirms the gold aggregate ties back to
> silver exactly. Skip if the preview looked right. *(Run 3.0 first.)*"""),

code("""# OPTIONAL — reference build + validation for gold.category_performance.
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

# gold revenue by category should match silver exactly (gold is just an aggregate)
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

md("""## 3.5 — Gold table #2: `gold.daily_revenue`

For the dashboards in Lab 6 you'll want a **daily time series**. Build a gold table
at the **date × category** grain.

### 👉 Type this into Lakeflow Designer
> *"Create a table **daily_revenue** in the **gold** schema from **silver.sales**.
> Group by **order_date** and **category**. Compute daily_revenue = sum of
> line_revenue, daily_profit = sum of line_profit, daily_units = sum of quantity,
> and orders = count of distinct order_id."*

### ✅ Validate `gold.daily_revenue` — in the UI
1. **Catalog** → `retail_corp.gold.daily_revenue` → **Sample Data**. Confirm you have
   one row per **date × category**, with daily revenue/profit/units.
2. **Overview** → the row count should be large (≈ 18 months × 5 categories of days).

> 🔎 **(Optional) Double-check with SQL** — confirms daily totals sum back to the
> category totals and the date range is continuous. Skip if the preview looked right.
> *(Run 3.0 first.)*"""),

code("""# OPTIONAL — reference build + validation for gold.daily_revenue.
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
print("✓ built", f"{G}.daily_revenue")

# daily totals should sum back to the category_performance totals
display(spark.sql(f'''
    SELECT d.category,
           ROUND(SUM(d.daily_revenue),2) AS summed_daily,
           ROUND(MAX(c.total_revenue),2) AS category_total,
           ROUND(SUM(d.daily_revenue) - MAX(c.total_revenue),2) AS diff
    FROM {G}.daily_revenue d
    JOIN {G}.category_performance c ON d.category = c.category
    GROUP BY d.category ORDER BY category_total DESC
'''))
print("Diffs should be ~0.00. Date coverage:")
display(spark.sql(f"SELECT MIN(order_date) first_day, MAX(order_date) last_day, "
                  f"COUNT(DISTINCT order_date) distinct_days FROM {G}.daily_revenue"))"""),

md("""## 3.6 — Schedule a daily refresh (Job)

Gold tables must stay current. In real life your pipeline reruns on a schedule — and
you set this up entirely in the UI.

### Do it in the UI
1. In your **Lakeflow pipeline** (`retail_corp_medallion`), click **Schedule** →
   **Add schedule**.
2. Set it to run **daily** (e.g. 06:00). Databricks creates a **Job** that triggers
   the pipeline. Name the job **`retail_corp_gold_daily_refresh`**.
3. Save. Your silver + gold tables now refresh every morning from the latest bronze —
   which itself refreshes from Lakebase via your Lab 1 ingestion.

> 🧭 **Check it:** open **Jobs & Pipelines** → `retail_corp_gold_daily_refresh` and
> confirm the schedule shows **Daily**. You can also click **Run now** to test it once."""),

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
