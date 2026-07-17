#!/usr/bin/env python3
"""Builds labs/Lab 4 - Business KPIs.ipynb"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbbuild import md, code, write_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cells = [
md("""# Lab 4 — Define Business-Level KPIs with Metric Views

### Databricks Data Camp for Business Users 🛍️

**Story so far:** In Lab 3 you saw the problem: the "best" category *changes*
depending on whether someone looks at revenue, units, margin %, or profit $. If
Marketing computes "ROI" one way and Finance another, your leadership team argues
about *numbers* instead of *decisions*.

The fix is a **Metric View** — a **governed, reusable definition** of your KPIs
that lives in Unity Catalog. Define **revenue**, **profit**, **cost**, and
**marketing ROI** *once*, and everyone (including Genie and your dashboards) uses
the **same** definition.

In this lab you will:
1. Learn what a Metric View is and its YAML structure.
2. Use **Genie Code** to help you author the metric view (with exact prompts).
3. Create the **`retail_metrics_sales`** and **`retail_metrics_marketing`** metric
   views on top of your silver data.
4. **Validate** it with SQL so you know the definitions are right.

⏱️ *Estimated time: 35–40 minutes.*

> 📚 Reference used for this lab's metric-view patterns:
> *Databricks Dashboard In A Day — Lab 2: Data Modelling.*"""),

md("""## 4.0 — (Optional) Load config

This lab is **UI-first** — you'll create the metric views in the Catalog UI. You only
need this cell **if** you want to run the *Optional* create-from-code or validation
cells later. Skip it otherwise."""),

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
print("Gold:", cfg["CATALOG_GOLD"], "| Silver:", cfg["CATALOG_SILVER"])"""),

md("""## 4.1 — What is a Metric View?

A **Metric View** is a Unity Catalog object defined in **YAML** that separates two
things:

- **Dimensions** — the ways you *slice* data (category, channel, month…).
- **Measures** — the *calculations* everyone agrees on (revenue, profit, margin,
  marketing ROI…), written **once**.

Why business users love it:
- 🔒 **One source of truth** — "revenue" means the same thing everywhere.
- 🧮 **No repeated SQL** — measures are pre-defined; you just pick them.
- 🤖 **Genie & dashboards use it** — ask for "profit margin by category" and you get
  *the* agreed number, not someone's ad-hoc formula.

### The YAML shape (you'll fill this in)
```yaml
version: 1.1
source: retail_corp.silver.sales
dimensions:
  - name: Category
    expr: category
measures:
  - name: Total Revenue
    expr: SUM(line_revenue)
```
That's the whole idea: `source` → `dimensions` → `measures`."""),

md("""## 4.2 — Use Genie Code to help author the metric view

**Genie Code** (the coding-focused Genie / Databricks Assistant in the SQL & code
editor) can *write the YAML for you* from a plain-English description. You stay in
control — you review and adjust — but you don't memorize syntax.

### How to use Genie Code here
1. Open a **new SQL editor** or notebook cell, and open the **Assistant** (✨).
2. Give it context + ask for the metric view. **Type prompts like these** (adapt
   wording freely — the point is *what* you ask, not exact phrasing):

   > *"I have a table `retail_corp.silver.sales` with columns category, channel,
   > order_date, quantity, unit_price, unit_cost, line_revenue, line_profit. Write
   > a Databricks **metric view YAML** with dimensions for category, channel, and
   > order month, and measures for total revenue = SUM(line_revenue), total cost =
   > SUM(quantity × unit_cost), total profit = SUM(line_profit), and profit margin
   > % = total profit ÷ total revenue × 100."*

   > *"Add a measure **units sold** = SUM(quantity), and format Total Revenue and
   > Total Profit as USD currency."*

3. Genie Code returns YAML. **Compare it to the reference YAML in 4.3** — they
   should be very close. Fix any differences (measure names, the margin formula
   using `measure(...)` references, etc.).

> 🧠 **Tip:** the more precise your description of each measure, the better Genie's
> YAML. Vague in → vague out."""),

md("""## 4.3 — Create the KPI metric view

Below is the **reference metric-view YAML** for Databricks Retail Corp. This is the
target your Genie-Code output should match. It defines the four KPIs your CEO
decision depends on: **revenue, cost, profit (with margin), and marketing ROI**.

> Because marketing spend lives in a *different* table than sales, we define **two**
> metric views: one over sales (`retail_metrics_sales`) and one over marketing
> (`retail_metrics_marketing`). Each is single-source, which keeps measures clean.

### Create in the UI
1. **Catalog** → open the **`gold`** schema → **Create → Metric View**.
2. Name it **`retail_metrics_sales`**, source = `retail_corp.silver.sales`.
3. Paste the **sales YAML** below into the YAML editor. **Save.**
4. Create a second metric view **`retail_metrics_marketing`** (source =
   `retail_corp.silver.marketing`) and paste the **marketing YAML** below. **Save.**

**Sales metric view YAML** (`retail_metrics_sales`):
```yaml
version: 1.1
source: retail_corp.silver.sales
dimensions:
  - name: Category
    expr: category
  - name: Channel
    expr: channel
  - name: Subcategory
    expr: subcategory
  - name: Order Month
    expr: date_trunc('MONTH', order_date)
measures:
  - name: Total Revenue
    expr: SUM(line_revenue)
    format: {type: currency, currency_code: USD}
  - name: Total Cost
    expr: SUM(quantity * unit_cost)
    format: {type: currency, currency_code: USD}
  - name: Total Profit
    expr: SUM(line_profit)
    format: {type: currency, currency_code: USD}
  - name: Profit Margin Pct
    expr: 100 * measure(`Total Profit`) / measure(`Total Revenue`)
  - name: Units Sold
    expr: SUM(quantity)
  - name: Avg Order Line Value
    expr: AVG(line_revenue)
```

**Marketing metric view YAML** (`retail_metrics_marketing`):
```yaml
version: 1.1
source: retail_corp.silver.marketing
dimensions:
  - name: Category
    expr: category
  - name: Marketing Channel
    expr: channel
measures:
  - name: Marketing Spend
    expr: SUM(spend_usd)
    format: {type: currency, currency_code: USD}
  - name: Attributed Revenue
    expr: SUM(attributed_revenue_usd)
    format: {type: currency, currency_code: USD}
  - name: Marketing ROI
    expr: measure(`Attributed Revenue`) / measure(`Marketing Spend`)
  - name: Conversions
    expr: SUM(conversions)
```

> 💡 If your `silver` catalog/schema names differ from the defaults, adjust the
> `source:` lines accordingly."""),

md("""### 🔎 (Optional) Create the metric views from code

Prefer to create them without the UI (or your workspace doesn't have the Metric View
editor)? The cell below creates them with metric-view DDL and **falls back** to plain
SQL views with the same measures if the DDL isn't available. **Skip it if you created
them in the UI above.** *(Run 4.0 first.)*"""),

code("""# OPTIONAL — create both metric views from code (fallback to SQL views).
G = cfg["CATALOG_GOLD"]; S = cfg["CATALOG_SILVER"]

sales_yaml = f'''version: 1.1
source: {S}.sales
dimensions:
  - name: Category
    expr: category
  - name: Channel
    expr: channel
  - name: Subcategory
    expr: subcategory
  - name: Order Month
    expr: date_trunc('MONTH', order_date)
measures:
  - name: Total Revenue
    expr: SUM(line_revenue)
    format: {{type: currency, currency_code: USD}}
  - name: Total Cost
    expr: SUM(quantity * unit_cost)
    format: {{type: currency, currency_code: USD}}
  - name: Total Profit
    expr: SUM(line_profit)
    format: {{type: currency, currency_code: USD}}
  - name: Profit Margin Pct
    expr: 100 * measure(`Total Profit`) / measure(`Total Revenue`)
  - name: Units Sold
    expr: SUM(quantity)
  - name: Avg Order Line Value
    expr: AVG(line_revenue)
'''
marketing_yaml = f'''version: 1.1
source: {S}.marketing
dimensions:
  - name: Category
    expr: category
  - name: Marketing Channel
    expr: channel
measures:
  - name: Marketing Spend
    expr: SUM(spend_usd)
    format: {{type: currency, currency_code: USD}}
  - name: Attributed Revenue
    expr: SUM(attributed_revenue_usd)
    format: {{type: currency, currency_code: USD}}
  - name: Marketing ROI
    expr: measure(`Attributed Revenue`) / measure(`Marketing Spend`)
  - name: Conversions
    expr: SUM(conversions)
'''

def try_metric_view(name, yaml_text):
    try:
        spark.sql(f"CREATE OR REPLACE VIEW {G}.{name} WITH METRICS "
                  f"LANGUAGE YAML AS $$\\n{yaml_text}$$")
        print(f"✓ Created METRIC VIEW {G}.{name}")
        return True
    except Exception as e:
        print(f"! Metric-view DDL not available for {name} ({str(e)[:90]}...).")
        return False

made_sales = try_metric_view("retail_metrics_sales", sales_yaml)
made_mkt   = try_metric_view("retail_metrics_marketing", marketing_yaml)

if not made_sales:
    spark.sql(f'''CREATE OR REPLACE VIEW {G}.retail_metrics_sales AS
        SELECT category AS Category, channel AS Channel, subcategory AS Subcategory,
               date_trunc('MONTH', order_date) AS Order_Month,
               SUM(line_revenue) AS Total_Revenue,
               SUM(quantity*unit_cost) AS Total_Cost,
               SUM(line_profit) AS Total_Profit,
               100*SUM(line_profit)/SUM(line_revenue) AS Profit_Margin_Pct,
               SUM(quantity) AS Units_Sold,
               AVG(line_revenue) AS Avg_Order_Line_Value
        FROM {S}.sales
        GROUP BY category, channel, subcategory, date_trunc('MONTH', order_date)''')
    print(f"  ↳ created fallback view {G}.retail_metrics_sales")
if not made_mkt:
    spark.sql(f'''CREATE OR REPLACE VIEW {G}.retail_metrics_marketing AS
        SELECT category AS Category, channel AS Marketing_Channel,
               SUM(spend_usd) AS Marketing_Spend,
               SUM(attributed_revenue_usd) AS Attributed_Revenue,
               SUM(attributed_revenue_usd)/SUM(spend_usd) AS Marketing_ROI,
               SUM(conversions) AS Conversions
        FROM {S}.marketing
        GROUP BY category, channel''')
    print(f"  ↳ created fallback view {G}.retail_metrics_marketing")"""),

md("""## 4.4 — Validate the metric views

**Validate in the UI first** — no code needed:

1. **Catalog** → `retail_corp.gold.retail_metrics_sales`. On a Metric View you'll see
   its **dimensions and measures** listed. Many workspaces offer a **preview /
   "Query this metric view"** button — use it to group **Total Profit** by
   **Category** and confirm the numbers look sane (Outerwear highest profit).
2. Open **`retail_metrics_marketing`** and preview **Marketing ROI** by **Category** —
   Outerwear should top the list (~4–5×), Accessories lowest (~1.8×).
3. Sanity-check the definitions read correctly (e.g. Profit Margin Pct uses
   `Total Profit / Total Revenue`).

> 🔎 **(Optional) Validate with SQL** — the cells below cross-check the metric views
> against the raw silver tables and assert the profit identity holds. Skip if the UI
> preview looked right. *(Run 4.0 and, if you used code to create the views, the
> Optional cell above, first.)*"""),

code("""# OPTIONAL — VALIDATION 1: revenue/profit/margin by category vs. silver.sales.
G = cfg["CATALOG_GOLD"]; S = cfg["CATALOG_SILVER"]

print("From the metric view (retail_metrics_sales):")
display(spark.sql(f'''
    SELECT Category,
           ROUND(SUM(Total_Revenue),2)  AS revenue,
           ROUND(SUM(Total_Profit),2)   AS profit,
           ROUND(100*SUM(Total_Profit)/SUM(Total_Revenue),1) AS margin_pct,
           SUM(Units_Sold)              AS units
    FROM {G}.retail_metrics_sales
    GROUP BY Category ORDER BY profit DESC
'''))

print("Ground truth (direct from silver.sales) — numbers must match:")
display(spark.sql(f'''
    SELECT category AS Category,
           ROUND(SUM(line_revenue),2) AS revenue,
           ROUND(SUM(line_profit),2)  AS profit,
           ROUND(100*SUM(line_profit)/SUM(line_revenue),1) AS margin_pct,
           SUM(quantity) AS units
    FROM {S}.sales GROUP BY category ORDER BY profit DESC
'''))"""),

code("""# OPTIONAL — VALIDATION 2: marketing ROI vs. silver.marketing (Outerwear tops ROI).
G = cfg["CATALOG_GOLD"]; S = cfg["CATALOG_SILVER"]

print("From the metric view (retail_metrics_marketing):")
display(spark.sql(f'''
    SELECT Category,
           ROUND(SUM(Marketing_Spend),0)      AS spend,
           ROUND(SUM(Attributed_Revenue),0)   AS attributed,
           ROUND(SUM(Attributed_Revenue)/SUM(Marketing_Spend),2) AS marketing_roi
    FROM {G}.retail_metrics_marketing
    GROUP BY Category ORDER BY marketing_roi DESC
'''))

print("Ground truth (direct from silver.marketing):")
display(spark.sql(f'''
    SELECT category AS Category,
           ROUND(SUM(spend_usd),0) AS spend,
           ROUND(SUM(attributed_revenue_usd),0) AS attributed,
           ROUND(SUM(attributed_revenue_usd)/SUM(spend_usd),2) AS marketing_roi
    FROM {S}.marketing GROUP BY category ORDER BY marketing_roi DESC
'''))"""),

code("""# OPTIONAL — VALIDATION 3: assert the profit identity (Revenue - Cost = Profit).
G = cfg["CATALOG_GOLD"]

row = spark.sql(f'''
    SELECT
      ROUND(100*SUM(Total_Profit)/SUM(Total_Revenue),1) AS overall_margin,
      ROUND(SUM(Total_Revenue) - SUM(Total_Cost) - SUM(Total_Profit),2) AS profit_identity
    FROM {G}.retail_metrics_sales
''').collect()[0]

print(f"Overall profit margin from metric view: {row['overall_margin']}%")
print(f"Revenue - Cost - Profit (should be ~0): {row['profit_identity']}")
assert abs(row["profit_identity"]) < 1.0, "Profit identity broken: revenue - cost != profit!"
print("✓ Profit = Revenue - Cost holds. KPI definitions are consistent.")"""),

md("""## 4.5 — The KPIs, defined once (summary)

You now have four governed KPIs everyone will share:

| KPI | Definition (measure) | Lives in |
|-----|----------------------|----------|
| **Revenue** | `SUM(line_revenue)` | `retail_metrics_sales` |
| **Cost** | `SUM(quantity × unit_cost)` | `retail_metrics_sales` |
| **Profit** | `SUM(line_profit)` = Revenue − Cost | `retail_metrics_sales` |
| **Profit Margin %** | `Profit ÷ Revenue × 100` | `retail_metrics_sales` |
| **Marketing ROI** | `Attributed Revenue ÷ Marketing Spend` | `retail_metrics_marketing` |

> 🧠 **Why this matters for your decision:** now when you (or Genie, or a dashboard)
> say "profit" or "marketing ROI," it's *the same number* every time. In Lab 5
> you'll point a **Genie Space** at these metric views so your natural-language
> questions return trustworthy KPIs — not ad-hoc math."""),

md("""## ✅ Lab 4 complete

- ✅ Learned the Metric View **YAML** structure (source → dimensions → measures)
- ✅ Used **Genie Code** to author the YAML from plain English
- ✅ Created **`retail_metrics_sales`** and **`retail_metrics_marketing`**
- ✅ **Validated** every KPI against ground truth + asserted the profit identity

**Next up → Lab 5: Data-driven decision making.** You'll build a **Genie Space** on
these metric views, explore the data by asking business questions, and combine your
internal KPIs with the **external market-research PDF** to make the call: *which
category do we promote next quarter?*""")
]

out = os.path.join(ROOT, "labs", "Lab 4 - Business KPIs.ipynb")
write_notebook(out, cells)
print("Wrote", out, "with", len(cells), "cells")
