#!/usr/bin/env python3
"""Builds labs/Lab 6 - Visualizing Data.ipynb"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbbuild import md, code, write_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cells = [
md("""# Lab 6 — Visualizing the Data with AI/BI Dashboards

### Databricks Data Camp for Business Users 🛍️

**Story so far:** You've made your call on which category to promote (Lab 5). Now
you need the whole company to **track the KPIs behind that decision, every day** —
without anyone re-running notebooks. That's what **AI/BI Dashboards** are for:
interactive, always-fresh, shareable.

You'll build dashboards **two ways**, so you know both:
1. **With Genie Code** — describe the chart in plain English; Genie writes it.
2. **With the standard dashboard workflow** — build datasets + widgets by hand on
   your **gold** tables.

You'll create dashboards for:
- 📈 **Daily revenue**
- 📊 **Operating margin**
- 🏆 **Top-5 best-performing products/categories**

⏱️ *Estimated time: 35–45 minutes.*"""),

md("""## 6.0 — Load config & confirm the gold tables"""),

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
G = cfg["CATALOG_GOLD"]
for t in ["daily_revenue", "category_performance"]:
    print(f"{G}.{t}:", spark.table(f"{G}.{t}").count(), "rows")"""),

md("""## 6.1 — Prep: a couple of dashboard-ready views

Dashboards are easiest when each chart maps to a tidy query. Let's add two small
helper views on top of gold so both the Genie-Code and manual paths have clean
sources. (These are optional conveniences — you could also write the SQL directly
in the dashboard.)"""),

code("""G = cfg["CATALOG_GOLD"]

# Daily operating margin across the whole business (all categories combined)
spark.sql(f'''
CREATE OR REPLACE VIEW {G}.v_daily_business AS
SELECT order_date,
       SUM(daily_revenue) AS revenue,
       SUM(daily_profit)  AS profit,
       ROUND(100 * SUM(daily_profit) / NULLIF(SUM(daily_revenue),0), 1) AS operating_margin_pct,
       SUM(daily_units)   AS units
FROM {G}.daily_revenue
GROUP BY order_date
''')

# Top products by profit (for the "top 5" dashboard). Built from silver.sales.
S = cfg["CATALOG_SILVER"]
spark.sql(f'''
CREATE OR REPLACE VIEW {G}.v_product_performance AS
SELECT product_name, category,
       ROUND(SUM(line_revenue),2) AS revenue,
       ROUND(SUM(line_profit),2)  AS profit,
       SUM(quantity)              AS units
FROM {S}.sales
GROUP BY product_name, category
''')

print("✓ created helper views: v_daily_business, v_product_performance")
display(spark.sql(f"SELECT * FROM {G}.v_product_performance ORDER BY profit DESC LIMIT 5"))"""),

md("""## 6.2 — Way #1: Build a dashboard with Genie Code

**Genie Code** can generate dashboard SQL + chart specs from plain English. This is
the fastest path for a business user.

### Steps
1. Left sidebar → **Dashboards** → **Create dashboard**. Name it
   **`Retail Corp — Daily KPIs (Genie)`**.
2. Add a **dataset**. In the dataset's SQL editor, open the **Assistant** (✨) and
   describe what you want. **Type prompts like** (adapt freely):
   > *"From `retail_corp.gold.daily_revenue`, give me daily total revenue across all
   > categories, ordered by date."*

   > *"From `retail_corp.gold.v_daily_business`, show operating margin percent by
   > day."*

   > *"From `retail_corp.gold.v_product_performance`, show the top 5 products by
   > profit."*
3. For each dataset, click **+ Add visualization** and either let Genie **suggest a
   chart** ("visualize this as a line chart by date") or pick the type yourself.
4. Arrange the three charts on the canvas. **Publish.**

> 🧠 **Tip:** Genie Code is great for first drafts. You can always click into the
> generated SQL to tweak filters (e.g. last 90 days) or rename fields."""),

md("""## 6.3 — Way #2: Build a dashboard the standard way (on gold tables)

Now the fully manual path, so you understand what Genie Code was doing for you.
You'll build **three widgets** on your gold tables.

### Create the dashboard
1. **Dashboards → Create dashboard**, name it **`Retail Corp — Daily KPIs`**.
2. Go to the **Data** tab and add **datasets** (each is a SQL query). Use the three
   queries below — the next cells let you **preview exactly what each widget will
   show** before you paste the SQL into the dashboard.

### Widget A — 📈 Daily revenue (line chart)
- Dataset SQL: select `order_date`, `revenue` from `gold.v_daily_business`.
- Visualization: **Line**, X = `order_date`, Y = `revenue`.

### Widget B — 📊 Operating margin (line or KPI)
- Dataset SQL: select `order_date`, `operating_margin_pct` from `gold.v_daily_business`.
- Visualization: **Line**, X = `order_date`, Y = `operating_margin_pct`.
  Add a **Counter/KPI** widget for the latest margin, too.

### Widget C — 🏆 Top-5 products by profit (bar chart)
- Dataset SQL: top 5 rows of `gold.v_product_performance` by `profit`.
- Visualization: **Bar**, X = `product_name`, Y = `profit`.

> The cells below preview each widget's data so you can confirm it looks right."""),

code("""# Preview Widget A — Daily revenue
G = cfg["CATALOG_GOLD"]
display(spark.sql(f'''
    SELECT order_date, revenue
    FROM {G}.v_daily_business
    ORDER BY order_date
'''))"""),

code("""# Preview Widget B — Operating margin by day (+ latest value as a KPI)
G = cfg["CATALOG_GOLD"]
display(spark.sql(f'''
    SELECT order_date, operating_margin_pct
    FROM {G}.v_daily_business
    ORDER BY order_date
'''))
latest = spark.sql(f'''
    SELECT operating_margin_pct FROM {G}.v_daily_business
    ORDER BY order_date DESC LIMIT 1
''').collect()[0]["operating_margin_pct"]
print(f"Latest operating margin (use as a Counter/KPI widget): {latest}%")"""),

code("""# Preview Widget C — Top 5 products by profit
G = cfg["CATALOG_GOLD"]
display(spark.sql(f'''
    SELECT product_name, category, profit, revenue, units
    FROM {G}.v_product_performance
    ORDER BY profit DESC
    LIMIT 5
'''))"""),

md("""## 6.4 — Bonus: category view that supports your Lab 5 decision

A dashboard that visualizes **profit and marketing ROI by category** makes your
promotion recommendation obvious at a glance. Add this as a fourth widget (bar
chart, X = category, Y = profit; add ROI as a second series or a table)."""),

code("""G = cfg["CATALOG_GOLD"]
display(spark.sql(f'''
    SELECT category,
           ROUND(total_profit,0)   AS profit,
           ROUND(total_revenue,0)  AS revenue,
           profit_margin_pct,
           units_sold,
           marketing_roi
    FROM {G}.category_performance
    ORDER BY profit DESC
'''))
print("This single view captures your decision case: the top-profit category also")
print("leads on marketing ROI — while units and margin % tell a different story.")"""),

md("""## 6.5 — Schedule & share

Make the dashboard a living asset:
1. On the published dashboard, click **Schedule** → refresh **daily** (align it with
   your Lab 3 gold refresh job so numbers are fresh each morning).
2. Click **Share** → grant your team **Can view**. Business users can now self-serve
   the KPIs — no notebook required.
3. (Optional) Set up an **alert** on operating margin so you're notified if it drops
   below a threshold."""),

md("""## ✅ Lab 6 complete — and training complete! 🎉

- ✅ Built dashboards **two ways**: with **Genie Code** and the **standard workflow**
- ✅ Visualized **daily revenue**, **operating margin**, and **top-5 performers**
- ✅ Added a **category profit + marketing ROI** view that backs your decision
- ✅ **Scheduled & shared** so the company tracks KPIs daily

---

## 🏁 The whole journey (as CEO of Databricks Retail Corp.)

| Lab | You did | Databricks capability |
|-----|---------|----------------------|
| 0 | Set up & deployed everything | Workspace, Unity Catalog, permissions |
| 1 | Connected data sources | **Lakeflow Connect**, Volumes |
| 2 | Discovered & documented data | **Unity Catalog, Genie One, Domains** |
| 3 | Cleaned → business-ready tables | **Lakeflow Designer**, medallion, Jobs |
| 4 | Defined shared KPIs | **Metric Views**, Genie Code |
| 5 | Made the decision | **Genie Spaces**, **ai_forecast()**, external PDF |
| 6 | Tracked it for everyone | **AI/BI Dashboards** |

**You went from "we don't use Databricks" to a governed, data-driven decision — and
a live dashboard the whole company can trust.** From raw orders to a defensible Q4
promotion call, backed by internal KPIs *and* external market research.

That's the Lakehouse. Congratulations, CEO. 🧑‍💼📊

---

> 🧹 **Done exploring, or resetting for the next learner?** **Lab 7 — Clean Up**
> removes every resource these labs created. Only run it when you're truly finished
> — it reverts all your progress.""")
]

out = os.path.join(ROOT, "labs", "Lab 6 - Visualizing Data.ipynb")
write_notebook(out, cells)
print("Wrote", out, "with", len(cells), "cells")
