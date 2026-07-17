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
2. **With the standard dashboard workflow** — build datasets + widgets by hand.

Both read from your **Lab 4 metric views** — the *single source of truth* — so the
dashboards show the **exact same numbers** as Genie in Lab 5.

You'll create dashboards for:
- 📈 **Daily revenue**
- 📊 **Operating margin**
- 🏆 **Top-5 best-performing products/categories**

⏱️ *Estimated time: 35–45 minutes.*"""),

md("""## 6.1 — The data behind your dashboards

Your dashboards read from the **metric views** you built in Lab 4 —
`retail_corp.gold.retail_metrics_sales` and `retail_corp.gold.retail_metrics_marketing`
— **not** raw tables. Every chart therefore uses the company's agreed KPI definitions
(revenue, profit, margin, marketing ROI), so a number on a dashboard always matches
the same number in Genie.

You'll paste these **ready-made queries** as **dataset SQL** directly inside the
dashboard editor (both build paths below show exactly where) — nothing to create
ahead of time. Each one just groups a metric view's measures by its dimensions.

**Query 1 — daily business totals** (revenue, profit, operating margin per day):
```sql
SELECT Order_Date AS order_date,
       SUM(Total_Revenue) AS revenue,
       SUM(Total_Profit)  AS profit,
       ROUND(100 * SUM(Total_Profit) / NULLIF(SUM(Total_Revenue),0), 1) AS operating_margin_pct
FROM retail_corp.gold.retail_metrics_sales
GROUP BY Order_Date
ORDER BY Order_Date
```

**Query 2 — product performance** (for the top-5 chart):
```sql
SELECT Product AS product_name, Category AS category,
       ROUND(SUM(Total_Revenue),2) AS revenue,
       ROUND(SUM(Total_Profit),2)  AS profit,
       SUM(Units_Sold)             AS units
FROM retail_corp.gold.retail_metrics_sales
GROUP BY Product, Category
ORDER BY profit DESC
```

> 🧠 **Notice:** these pull `Total_Revenue` / `Total_Profit` / `Units_Sold` **measures**
> and slice them by the **`Order_Date`** and **`Product`** dimensions you added to the
> metric view in Lab 4 — no raw `line_revenue` math anywhere."""),

md("""## 6.2 — Way #1: Build a dashboard with Genie Code

**Genie Code** can generate dashboard SQL + chart specs from plain English. This is
the fastest path for a business user — entirely in the UI.

### Steps
1. Left sidebar → **Dashboards** → **Create dashboard**. Name it
   **`Retail Corp — Daily KPIs (Genie)`**.
2. Add a **dataset**. In the dataset's SQL editor, open the **Assistant** (✨) and
   describe what you want — **point it at the metric views** so KPIs stay governed.
   **Type prompts like** (adapt freely):
   > *"From the metric view `retail_corp.gold.retail_metrics_sales`, give me daily
   > Total Revenue by Order Date across all categories, ordered by date."*

   > *"From `retail_corp.gold.retail_metrics_sales`, show operating margin percent by
   > Order Date: 100 × Total Profit ÷ Total Revenue, grouped by Order Date."*

   > *"From `retail_corp.gold.retail_metrics_sales`, show the top 5 Products by Total
   > Profit."*
3. For each dataset, click **+ Add visualization** and either let Genie **suggest a
   chart** ("visualize this as a line chart by date") or pick the type yourself.
4. Arrange the three charts on the canvas. **Publish.**

> 🧠 **Tip:** name the metric view explicitly in your prompt (as above) so Genie
> aggregates the governed measures instead of reaching for a raw table. You can always
> click into the generated SQL to tweak filters (e.g. last 90 days) or rename fields."""),

md("""## 6.3 — Way #2: Build a dashboard the standard way (on the metric views)

Now the fully manual path, so you understand what Genie Code was doing for you.
You'll build **three widgets** on the **metric views** — all in the dashboard editor.

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
recommendation obvious at a glance. It combines **both** metric views — profit from
`retail_metrics_sales`, ROI from `retail_metrics_marketing` — so it's fully governed.
Add a fourth widget:

- New dataset SQL (joins the two metric views on Category):
  ```sql
  SELECT s.Category                                   AS category,
         ROUND(SUM(s.Total_Profit), 0)                AS profit,
         ROUND(SUM(s.Total_Revenue), 0)               AS revenue,
         ROUND(100*SUM(s.Total_Profit)/SUM(s.Total_Revenue), 1) AS profit_margin_pct,
         SUM(s.Units_Sold)                            AS units_sold,
         ROUND(MAX(m.marketing_roi), 2)               AS marketing_roi
  FROM retail_corp.gold.retail_metrics_sales s
  LEFT JOIN (
      SELECT Category,
             SUM(Attributed_Revenue)/SUM(Marketing_Spend) AS marketing_roi
      FROM retail_corp.gold.retail_metrics_marketing
      GROUP BY Category
  ) m ON s.Category = m.Category
  GROUP BY s.Category
  ORDER BY profit DESC
  ```
- Visualization: **Bar**, X = `category`, Y = `profit`; add `marketing_roi` as a
  second series or a small table beside it.

> 🧠 This single chart captures your decision case — and every number traces back to a
> Lab 4 metric view: the top-**profit** category also leads on **marketing ROI**,
> while units and margin % tell a different story."""),

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
- ✅ Sourced **every chart from the Lab 4 metric views** — dashboards and Genie show
  the same governed numbers
- ✅ Visualized **daily revenue**, **operating margin**, and **top-5 performers**
- ✅ Added a **category profit + marketing ROI** chart that backs your decision
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
