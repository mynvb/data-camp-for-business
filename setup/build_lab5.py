#!/usr/bin/env python3
"""Builds labs/Lab 5 - Decision Making.ipynb"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbbuild import md, code, write_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cells = [
md("""# Lab 5 — Data-Driven Decision Making with Genie Spaces

### Databricks Data Camp for Business Users 🛍️

**Story so far:** You've built clean gold tables (Lab 3) and governed KPIs (Lab 4).
Now comes the actual CEO decision: **which category of Databricks merch do we
promote next quarter?**

You'll answer it the modern way — a **Genie Space**: a curated, conversational
workspace where you (and your team) ask **business questions in plain English** and
get trustworthy answers backed by your **metric views**. You'll also **forecast the
future** two ways and learn to *question* a forecast, then bring in the **external
market-research PDF** and see whether all your signals **agree**.

In this lab you will:
1. Create and **optimize** a Genie Space (Databricks best practices).
2. Explore your data across dimensions by asking business questions.
3. **Forecast** next quarter's revenue with the `ai_forecast()` SQL function.
4. **Compare** your forecast against the Data Science team's hand-off and spot the
   discrepancies.
5. Add the **market-research PDF** to the Space.
6. Reach a **defensible, data-driven recommendation.**

> 📝 **Note on this lab's style:** below, we tell you **what to find out** — the
> *result* you need — but we deliberately **don't script the exact question**.
> Phrasing questions yourself is the skill. Ask, refine, and follow up naturally.

⏱️ *Estimated time: 55–65 minutes.*"""),

md("""## 5.0 — What you'll build a Genie Space over

This lab is mostly done in the **Genie** UI. Your Genie Space is built on the
**metric views** from Lab 4 — they are the **single source of truth** for every KPI:

- `retail_corp.gold.retail_metrics_sales` — **metric view** (Lab 4): revenue, cost,
  profit, margin %, units — sliceable by Category, Channel, Product, Order Date, Month.
- `retail_corp.gold.retail_metrics_marketing` — **metric view** (Lab 4): marketing
  spend, attributed revenue, ROI, conversions — by Category and Channel.

That's **all** the Space needs. Because the metric views carry Product and Order Date
dimensions, they answer daily trends and top-product questions too — so you do **not**
add the raw gold/silver tables (that would let someone bypass the agreed definitions).

> The only place code appears in this lab is the **optional** forecasting section
> (5.5–5.6), because `ai_forecast()` and the forecast-comparison have no point-and-click
> equivalent yet. Everything else is UI."""),

md("""## 5.1 — Create a Genie Space

1. Left sidebar → **Genie** → **New** (Genie Space).
2. Name it **`Retail Corp — Category Decision`**.
3. **Add data.** Add **only the two metric views** — this is the most important choice:
   - ✅ `gold.retail_metrics_sales`
   - ✅ `gold.retail_metrics_marketing`
   Do **not** add the raw `silver.*` or `gold.category_performance` / `daily_revenue`
   tables. Keeping the Space to the metric views guarantees every answer uses the
   company's agreed KPI definitions.
4. Pick a **Serverless SQL Warehouse** for the Space to run on.
5. Save.

> 🧠 **Why metric-views-only?** When Genie answers "what's our profit margin by
> category?", it should use the **agreed** definition from Lab 4 — not invent a
> formula or read a raw table. Restricting the Space to the metric views makes every
> answer *governed, consistent, and traceable* to a single definition."""),

md("""## 5.2 — Make sure Genie USES your Metric Views (from Lab 4)

Adding the metric views isn't quite enough — you want Genie to *prefer* them.
Do this inside the Space's settings:

1. Open the Space → **⚙️ Settings / Instructions** (sometimes "Knowledge" or
   "General instructions").
2. Add a **general instruction** telling Genie to use the metric views as the
   source of truth for KPIs. For example (paraphrase):
   > *"When asked about revenue, cost, profit, profit margin, units, or marketing
   > ROI, use the metric views `retail_metrics_sales` and `retail_metrics_marketing`.
   > These contain the company's official KPI definitions. Do not compute these
   > metrics from raw columns."*
3. Add a couple of **example questions** (Sample/Curated queries) that resolve
   against the metric views — e.g. an example that returns profit by category. Genie
   uses these examples to learn the right pattern.
4. Optionally define **synonyms** (e.g. "sales" → revenue, "margin" → profit margin
   pct) so casual wording still hits the right measure.

> ✅ **Check it's working:** ask for "profit by category," expand Genie's answer,
> and confirm the generated SQL references the **metric view** (not a hand-rolled
> `SUM(...)` over silver). If it doesn't, strengthen the instruction in step 2."""),

md("""## 5.3 — Optimize the Space (Databricks best practices)

A few minutes of curation makes Genie dramatically more reliable:

- 🏷️ **Rich metadata pays off** — the table/column descriptions you added in Lab 2
  feed Genie directly. Good names + comments = good answers.
- 💬 **Add sample questions** covering your main use cases (revenue, profit, ROI,
  trends). These "teach" Genie the house style.
- 📐 **Prefer metric views** for anything numeric (5.2) so KPIs stay consistent.
- 🧩 **Add synonyms & business terms** ("merch" = product, "top category" = highest
  profit) to match how your team actually talks.
- ✂️ **Keep the Space focused** — only add the tables needed for this decision.
  Fewer, well-described assets beat a giant pile.
- 🧪 **Test & correct** — when Genie gets one wrong, use the feedback/"teach Genie"
  option to save the corrected SQL as an example. It learns.
- 🔁 **Iterate** — treat the Space as a living product: review questions your team
  asks and keep adding examples."""),

md("""## 5.4 — Explore the data by asking questions (what to FIND)

Now interview your data. For each item below, **figure out how to ask it** and note
the answer. Don't copy a script — phrase it your way, then refine with follow-ups.

**A. Where does the money come from today?**
- Find the **total revenue and total profit for each category**, ranked.
- Find which category has the **highest profit margin %** — and notice it's *not*
  the same as the highest profit **dollars**. (Why might a high-margin category
  still be a poor promotion choice?)

**B. Volume vs. value.**
- Find which category sells the **most units**, and compare that ranking to the
  **profit** ranking. Where do they disagree?
- Find the **average value of an order line** by category.

**C. Momentum (growth).**
- Using the daily/monthly data, find which category's **revenue is growing
  fastest** over the last several months. (Ask Genie for a trend, then compare
  recent months to earlier ones.)

**D. Marketing efficiency.**
- Find the **marketing ROI by category** (attributed revenue ÷ spend). Which
  category returns the most revenue per marketing dollar?
- Cross-reference: does the category with the best marketing ROI also have strong
  profit and growth?

**E. Seasonality (bonus).**
- Find whether any category **peaks in Q4** (Oct–Dec). A category that naturally
  surges in Q4 is a strong candidate for a Q4 promotion.

> 🎯 **You're building a case.** By the end of D–E you should notice a category that
> keeps showing up near the top on **profit, growth, marketing ROI, and Q4
> seasonality** — even if it isn't #1 on raw units or on margin %."""),

md("""## 5.5 — Forecast next quarter with `ai_forecast()`

So far you've analyzed the **past**. To decide what to promote **next quarter**, you
want a view of the **future**. Databricks gives business users a remarkably simple
tool for this: the built-in **`ai_forecast()`** SQL function. You hand it historical
time-series data and it returns a forecast — **no data-science background required**.

### What `ai_forecast()` does (plain English)
- **Input:** a time series — here, monthly revenue per category, taken from your
  **`retail_metrics_sales` metric view** so the forecast uses the same governed
  revenue definition as everything else.
- **Output:** predicted values for future periods, plus an **upper/lower bound**
  (the uncertainty range).
- It picks a sensible model for you under the hood. You just describe the horizon.

### The shape of the call
```sql
SELECT * FROM ai_forecast(
  TABLE(<your historical data>),   -- a table/subquery of (time, value[, group])
  horizon  => '2025-09-30',        -- forecast up to this date
  time_col => 'month',
  value_col => 'revenue',
  group_col => 'category',         -- forecast each category separately
  frequency => 'month'
)
```

> 🧭 **Availability note:** `ai_forecast()` runs on a **Serverless SQL Warehouse /
> DBSQL**. If it isn't available on your compute, the cell below catches the error
> and falls back to a simple **3-month-average** baseline forecast so you can still
> complete the comparison in 5.6. The *lesson* — comparing two forecasts — is the same.

### Do it in the UI first (ask Genie)
Before running any code, try it conversationally in your **Genie Space**:
- Ask Genie to **show monthly revenue by category over time** (a trend). Note the
  recent trajectory for each category.
- Ask Genie which categories are **trending up** most strongly over the last few
  months. This is your intuition-level "forecast."

Then use the optional code below for a **real statistical forecast** you can compare
against — Genie's trend view and `ai_forecast()` should broadly agree.

### 🔎 (Optional) Generate a statistical forecast with `ai_forecast()`
The cells in 5.5–5.6 are the one place this lab uses code, because forecasting and
forecast-validation have no point-and-click equivalent yet. Run them to produce a
defensible forecast and catch the Data Science team's bad numbers. *(This first cell
loads config; run it before the others.)*"""),

code("""# (Optional) Load config for the forecasting cells.
import os, sys
def find_repo_root():
    p = os.getcwd()
    for _ in range(6):
        if os.path.isdir(os.path.join(p, "setup")) and os.path.isdir(os.path.join(p, "labs")):
            return p
        p = os.path.dirname(p)
    return os.getcwd()
sys.path.insert(0, os.path.join(find_repo_root(), "setup"))
from config import get_config
cfg = get_config()
spark.sql(f"USE CATALOG {cfg['CATALOG']}")
print("Config loaded for forecasting. Gold:", cfg["CATALOG_GOLD"])"""),

code("""# Build the monthly revenue history per category FROM THE METRIC VIEW — so the
# forecast is based on the same governed 'Total Revenue' definition as everything
# else (Lab 4), not a re-derived number. Then forecast 3 months with ai_forecast().
G = cfg["CATALOG_GOLD"]
fc_created = False

# Query the metric view: its 'Order Month' dimension + 'Total Revenue' measure.
# (Column names come through as Order_Month / Total_Revenue on both the true metric
# view and the Lab 4 fallback view.)
hist_sql = f'''
    SELECT CAST(Order_Month AS DATE) AS month,
           Category                  AS category,
           SUM(Total_Revenue)        AS revenue
    FROM {G}.retail_metrics_sales
    GROUP BY CAST(Order_Month AS DATE), Category
'''

# Create the history as a view first so ai_forecast (and section 5.6) can reference it.
spark.sql(f"CREATE OR REPLACE VIEW {G}.v_monthly_revenue_hist AS {hist_sql}")

try:
    spark.sql(f'''
        CREATE OR REPLACE TABLE {G}.revenue_forecast_ai AS
        SELECT category,
               CAST(month AS DATE)  AS forecast_month,
               ROUND(revenue_forecast, 2) AS ai_forecast_revenue,
               ROUND(revenue_lower, 2)    AS ai_lower_bound,
               ROUND(revenue_upper, 2)    AS ai_upper_bound
        FROM ai_forecast(
            TABLE({G}.v_monthly_revenue_hist),
            horizon   => '2025-09-30',
            time_col  => 'month',
            value_col => 'revenue',
            group_col => 'category',
            frequency => 'month'
        )
    ''')
    fc_created = True
    print("✓ ai_forecast() produced revenue_forecast_ai")
except Exception as e:
    print("! ai_forecast() not available here:", str(e)[:150])
    print("  → Falling back to a 3-month-average baseline forecast.")
    spark.sql(f'''
        CREATE OR REPLACE TABLE {G}.revenue_forecast_ai AS
        WITH recent AS (
            SELECT category, AVG(revenue) AS avg_rev
            FROM ({hist_sql})
            WHERE month >= '2025-04-01'
            GROUP BY category
        ),
        months AS (
            SELECT explode(array(DATE'2025-07-01', DATE'2025-08-01', DATE'2025-09-01')) AS forecast_month
        )
        SELECT r.category, m.forecast_month,
               ROUND(r.avg_rev, 2)        AS ai_forecast_revenue,
               ROUND(r.avg_rev * 0.9, 2)  AS ai_lower_bound,
               ROUND(r.avg_rev * 1.1, 2)  AS ai_upper_bound
        FROM recent r CROSS JOIN months m
    ''')
    fc_created = True

display(spark.table(f"{G}.revenue_forecast_ai").orderBy("category", "forecast_month"))"""),

md("""### 🔎 Read your forecast

Look at the output above. For each category you have a **predicted monthly revenue**
for Jul–Sep 2025 and an uncertainty band. Sanity-check it against what you learned in
5.4: the forecast should look like a *reasonable continuation of recent history* —
**Outerwear** highest (~$45–50K/mo), **T-Shirts** next (~$25K), the rest lower.

> 💡 A good forecast doesn't contradict the recent past without a reason. Hold that
> thought — you're about to meet a forecast that does."""),

md("""## 5.6 — Compare: your forecast vs. the Data Science team's

Your company's **Data Science team** already sent over a forecast — it's sitting in
`bronze.fact_sales_forecast` (model `ds_prophet_v1`). As a data-driven CEO, you
**don't just accept a hand-off** — you compare it against your own `ai_forecast()`
numbers and against reality.

> 🔎 **(Optional, continues 5.5)** Run the comparison below. Then **judge for
> yourself which forecast to trust.** *(Requires the optional forecasting cells in
> 5.5.)* If you skipped the code, you can still do this by eye: open
> `bronze.fact_sales_forecast` in **Catalog → Sample Data** and compare its numbers to
> the recent monthly revenue Genie showed you — the problems are visible without code."""),

code("""# Join the two forecasts side by side, plus a recent-actuals baseline for context.
G = cfg["CATALOG_GOLD"]; B = cfg["CATALOG_BRONZE"]

compare = spark.sql(f'''
    WITH actuals AS (   -- recent (Q2 2025) monthly average, our reality check
        SELECT category, ROUND(AVG(revenue), 0) AS recent_monthly_actual
        FROM {G}.v_monthly_revenue_hist
        WHERE month >= '2025-04-01'
        GROUP BY category
    ),
    ai AS (
        SELECT category, ROUND(AVG(ai_forecast_revenue), 0) AS your_ai_forecast
        FROM {G}.revenue_forecast_ai
        GROUP BY category
    ),
    ds AS (
        SELECT category, ROUND(AVG(forecast_revenue_usd), 0) AS ds_team_forecast,
               ROUND(AVG(lower_bound_usd), 0) AS ds_lower,
               ROUND(AVG(upper_bound_usd), 0) AS ds_upper
        FROM {B}.fact_sales_forecast
        GROUP BY category
    )
    SELECT a.category,
           a.recent_monthly_actual,
           ai.your_ai_forecast,
           ds.ds_team_forecast,
           ds.ds_lower, ds.ds_upper,
           ROUND(ds.ds_team_forecast - ai.your_ai_forecast, 0) AS ds_minus_ai,
           ROUND(100.0 * (ds.ds_team_forecast - a.recent_monthly_actual)
                 / NULLIF(a.recent_monthly_actual, 0), 0)      AS ds_vs_actual_pct
    FROM actuals a
    JOIN ai ON a.category = ai.category
    JOIN ds ON a.category = ds.category
    ORDER BY a.recent_monthly_actual DESC
''')
display(compare)"""),

md("""### ⚠️ Spot the discrepancies

Study the comparison table. The Data Science team's forecast **disagrees with both
your `ai_forecast()` and with recent reality** in several alarming ways. See how many
you can spot before reading on:

- 🟥 **Outerwear** — your best, fastest-growing category (~$47K/mo recently). The DS
  model predicts it **collapses to ~$5K/mo**. A ~90% crash with no reason in the data.
- 🟥 **Headwear** — recently ~$10K/mo. The DS model predicts it **explodes to
  ~$80K/mo** — an 8× jump that nothing in the history supports.
- 🟥 **Accessories** — the DS model predicts **negative revenue**. Revenue can't be
  negative. This is a broken output, full stop.
- 🟥 **Drinkware** — the point forecast looks plausible (~$8K) but the **uncertainty
  band runs from −$32K to +$48K** — so wide (and negative) it's meaningless.
- 🟥 **Confidence bounds are broken** — e.g. for Headwear the **lower bound is *above*
  the point forecast**, which is logically impossible for a real interval.

The automated check below flags these anomalies so you have them in writing."""),

code("""# Automated anomaly detector on the DS team's forecast. In real life you'd send
# this back to the DS team before trusting their numbers.
B = cfg["CATALOG_BRONZE"]
anoms = spark.sql(f'''
    SELECT category, forecast_month, forecast_revenue_usd, lower_bound_usd, upper_bound_usd,
        CASE
            WHEN forecast_revenue_usd < 0 THEN 'IMPOSSIBLE: negative revenue'
            WHEN lower_bound_usd > forecast_revenue_usd THEN 'BROKEN: lower bound above point forecast'
            WHEN upper_bound_usd - lower_bound_usd > 3 * ABS(forecast_revenue_usd) THEN 'SUSPECT: uncertainty band absurdly wide'
        END AS anomaly
    FROM {B}.fact_sales_forecast
    HAVING anomaly IS NOT NULL
    ORDER BY category, forecast_month
''')
print("Anomalies detected in the Data Science team's forecast:")
display(anoms)
n = anoms.count()
print(f"\\n⚠️  {n} anomalous rows found. That's why you never accept a forecast hand-off")
print("   blindly — you validate it against your own forecast and against reality.")"""),

md("""### 🧠 What to take away from the comparison

- Your **`ai_forecast()`** output is a *reasonable continuation* of history — you can
  reason about it and defend it.
- The **DS team's forecast** contains impossible values (negative revenue), broken
  intervals, and swings the data doesn't justify. Whether it's a pipeline bug, a
  mislabeled model, or stale inputs — **you can't build a strategy on it.**
- **The skill you just practiced:** a data-driven leader treats every forecast — even
  one from experts — as a claim to be **checked**, not a fact to be obeyed. Two
  independent methods disagreeing is a signal to **investigate before you spend money.**

> 👉 **For your decision:** trust the `ai_forecast()` numbers (and the actuals behind
> them). Send the `ds_prophet_v1` forecast back to the Data Science team with the
> anomaly list attached. Your promotion call will rest on evidence you can stand behind."""),

md("""## 5.7 — Add the external market research (PDF) to the Space

Your internal data tells you what *has* happened. The **market-research PDF** tells
you where the *broader market* is heading. Bring it into the same Space so Genie can
reason over both.

1. Locate the PDF you downloaded in **Lab 0**:
   `assets/market_research/Databricks_Retail_Market_Research.pdf`.
   *(It's also in your Volume at `.../raw_files/market_research/`.)*
2. In your **Genie Space**, open **Add data / Attachments / Knowledge** and
   **upload the PDF** as a document/attachment to the Space.
   *(If your workspace doesn't support PDF attachments in Genie yet, open the PDF
   side-by-side and use its findings manually in the decision step 5.8 — the
   analysis is the same.)*
3. Once attached, ask Genie questions that **combine** the PDF with your data. Find:
   - What does the **external research recommend**, and **why** (growth, seasonality,
     willingness-to-pay, repeat purchase)?
   - Does the PDF's recommended category **match** your internal profit/ROI/growth
     leader? **Where do internal and external signals agree or diverge?**

> 🧠 **This is the real skill:** triangulating *internal evidence* (your KPIs) with
> *external context* (the market). Agreement → high confidence. Divergence → dig in
> before spending budget."""),

md("""## 5.8 — Make the decision

Pull it together. A defensible recommendation cites **multiple, independent
signals** pointing the same way. Fill in what you found:

| Signal (from your questions) | Leading category | Notes |
|------------------------------|------------------|-------|
| Total **profit $** (5.4 A) | ? | |
| **Growth** / momentum (5.4 C) | ? | |
| **Marketing ROI** (5.4 D) | ? | |
| **Q4 seasonality** (5.4 E) | ? | |
| **`ai_forecast()` outlook** (5.5) | ? | your trustworthy forecast |
| **External research** (5.7) | ? | from the PDF |
| **Highest units** (contrast) | ? | volume ≠ value |
| **Highest margin %** (contrast) | ? | margin % ≠ profit $ |
| ~~DS team forecast~~ (5.6) | ⚠️ rejected | failed validation — anomalies |

**Write your recommendation** (2–3 sentences): *Which category will Databricks
Retail Corp. promote next quarter, and what evidence backs it?* Note any caveats —
e.g. a high-units category you'd keep as a traffic driver even if you don't promote it.

> 💡 **What "good" looks like:** the strongest case is a category that wins on
> **profit dollars, growth, and marketing ROI**, is **backed by the external market
> research**, and **peaks in Q4** — while you consciously set aside "highest units"
> and "highest margin %" as *incomplete* lenses. If your evidence lines up that way,
> you've made a genuinely data-driven decision."""),

md("""## ✅ Lab 5 complete

- ✅ Built and **optimized** a Genie Space (best practices)
- ✅ Wired Genie to **use your Lab 4 metric views** for consistent KPIs
- ✅ Explored **profit, volume, growth, marketing ROI, and seasonality** by asking
  business questions in your own words
- ✅ **Forecast** next quarter's revenue with **`ai_forecast()`**
- ✅ **Compared** it to the Data Science team's hand-off, caught the **anomalies**,
  and learned to *validate* a forecast instead of trusting it blindly
- ✅ Added the **market-research PDF** and triangulated internal vs. external signals
- ✅ Reached a **defensible recommendation** for the Q4 promotion

**Next up → Lab 6: Visualizing the data.** You'll turn the KPIs behind your decision
into **AI/BI dashboards** so the whole company can track them daily — built two ways
(with **Genie Code** and the **standard dashboard workflow**), both reading from the
same **metric views** so the dashboards show the exact same numbers as Genie.""")
]

out = os.path.join(ROOT, "labs", "Lab 5 - Decision Making.ipynb")
write_notebook(out, cells)
print("Wrote", out, "with", len(cells), "cells")
