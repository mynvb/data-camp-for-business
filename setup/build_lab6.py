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

md("""## 6.1 — The data behind your dashboards

Your dashboards read straight from the **gold** tables you built in Lab 3:
`retail_corp.gold.daily_revenue` and `retail_corp.gold.category_performance`.

For a couple of charts it's handy to have **two small ready-made queries**. You'll
paste these as **dataset SQL** directly inside the dashboard editor (both build
paths below show exactly where) — no need to create anything ahead of time.

**Query 1 — daily business totals** (revenue, profit, operating margin per day):
```sql
SELECT order_date,
       SUM(daily_revenue) AS revenue,
       SUM(daily_profit)  AS profit,
       ROUND(100 * SUM(daily_profit) / NULLIF(SUM(daily_revenue),0), 1) AS operating_margin_pct,
       SUM(daily_units)   AS units
FROM retail_corp.gold.daily_revenue
GROUP BY order_date
ORDER BY order_date
```

**Query 2 — product performance** (for the top-5 chart):
```sql
SELECT product_name, category,
       ROUND(SUM(line_revenue),2) AS revenue,
       ROUND(SUM(line_profit),2)  AS profit,
       SUM(quantity)              AS units
FROM retail_corp.silver.sales
GROUP BY product_name, category
ORDER BY profit DESC
```"""),

md("""## 6.2 — Way #1: Build a dashboard with Genie Code

**Genie Code** can generate dashboard SQL + chart specs from plain English. This is
the fastest path for a business user — entirely in the UI.

### Steps
1. Left sidebar → **Dashboards** → **Create dashboard**. Name it
   **`Retail Corp — Daily KPIs (Genie)`**.
2. Add a **dataset**. In the dataset's SQL editor, open the **Assistant** (✨) and
   describe what you want. **Type prompts like** (adapt freely):
   > *"From `retail_corp.gold.daily_revenue`, give me daily total revenue across all
   > categories, ordered by date."*

   > *"Show operating margin percent by day: 100 × profit ÷ revenue from
   > `retail_corp.gold.daily_revenue`, grouped by order_date."*

   > *"From `retail_corp.silver.sales`, show the top 5 products by total profit."*
3. For each dataset, click **+ Add visualization** and either let Genie **suggest a
   chart** ("visualize this as a line chart by date") or pick the type yourself.
4. Arrange the three charts on the canvas. **Publish.**

> 🧠 **Tip:** Genie Code is great for first drafts. You can always click into the
> generated SQL to tweak filters (e.g. last 90 days) or rename fields."""),

md("""## 6.3 — Way #2: Build a dashboard the standard way (on gold tables)

Now the fully manual path, so you understand what Genie Code was doing for you.
You'll build **three widgets** on your gold tables — all in the dashboard editor.

### Create the dashboard
1. **Dashboards → Create dashboard**, name it **`Retail Corp — Daily KPIs`**.
2. Go to the **Data** tab → **Create from SQL**. Paste **Query 1** from 6.1 and name
   the dataset `daily_business`. Add a second dataset from **Query 2** named
   `product_performance`.
3. Go to the **Canvas** tab and add the three widgets below, pointing each at a
   dataset.

### Widget A — 📈 Daily revenue (line chart)
- Dataset: `daily_business`.
- Visualization: **Line**, X = `order_date`, Y = `revenue`.

### Widget B — 📊 Operating margin (line + KPI)
- Dataset: `daily_business`.
- Visualization: **Line**, X = `order_date`, Y = `operating_margin_pct`.
  Add a **Counter** widget on the same dataset showing the **latest**
  `operating_margin_pct` as a headline KPI.

### Widget C — 🏆 Top-5 products by profit (bar chart)
- Dataset: `product_performance`.
- Visualization: **Bar**, X = `product_name`, Y = `profit`. In the widget's settings
  set a **row limit of 5** (the query is already sorted by profit).

> 💡 **Confirm as you go:** each widget previews live as you configure it — if a chart
> looks empty, re-check the dataset's SQL ran (green tick in the Data tab)."""),

md("""## 6.4 — Bonus: category view that supports your Lab 5 decision

A chart of **profit and marketing ROI by category** makes your promotion
recommendation obvious at a glance. Add a fourth widget:

- New dataset SQL:
  ```sql
  SELECT category,
         ROUND(total_profit,0)  AS profit,
         ROUND(total_revenue,0) AS revenue,
         profit_margin_pct,
         units_sold,
         marketing_roi
  FROM retail_corp.gold.category_performance
  ORDER BY profit DESC
  ```
- Visualization: **Bar**, X = `category`, Y = `profit`; add `marketing_roi` as a
  second series or a small table beside it.

> 🧠 This single chart captures your decision case: the top-**profit** category also
> leads on **marketing ROI** — while units and margin % tell a different story."""),

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
