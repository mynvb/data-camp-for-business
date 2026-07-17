#!/usr/bin/env python3
"""Builds labs/Lab 2 - Data Discovery.ipynb"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbbuild import md, code, write_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cells = [
md("""# Lab 2 — Data Discovery

### Databricks Data Camp for Business Users 🛍️

**Story so far:** Your data is in Databricks (Labs 0–1). But as a new CEO, you
don't yet *know your own data*. Which tables exist? What do the columns mean? Is
anything undocumented?

Before you can make a decision, you need to **discover and understand** what you
have. Databricks gives you **three complementary ways** to do this, and you'll try
all three:

1. **Unity Catalog** — the governed catalog/schema/table browser (the "file
   explorer" for your data).
2. **Genie One** — ask questions about your data in **plain English**.
3. **Domains** — organize assets into a business-friendly grouping and access
   data *through the domain*.

You'll also **add missing metadata** (descriptions) so your data is
self-explanatory for everyone — then rediscover it.

⏱️ *Estimated time: 30–35 minutes.*"""),

md("""## 2.1 — Way #1: Discover with Unity Catalog

**Unity Catalog** is your governed data explorer. Everything is organized as
**Catalog → Schema → Table → Column**, with permissions and lineage built in — and
you browse it all in the UI, no code needed.

### Do it in the UI
1. Left sidebar → **Catalog**.
2. Expand **`retail_corp`** → **`bronze`**. You'll see the six tables you ingested.
3. Click **`fact_orders`** and explore the tabs across the top:
   - **Overview / Columns** — column names, types, and (once you add them in 2.3)
     descriptions.
   - **Sample Data** — a preview of real rows, so you know what the data looks like.
   - **Details** — owner, size, created date, row count.
   - **Lineage** — where the data came from (your Lab 1 ingestion) and what depends
     on it.
   - **Insights / Permissions** — who can access it and how it's used.
4. Repeat for a couple of other tables (e.g. `dim_product`, `fact_marketing_campaigns`)
   so you get a feel for the whole dataset.

> 🔎 **Use search.** The **Search** box at the top of Catalog lets you find a table or
> column by name across the whole workspace — handy when you don't know where
> something lives."""),

md("""## 2.2 — Find the metadata gaps

As you click through the tables in 2.1, notice that most columns have **no
description**. A teammate browsing the catalog has no idea what, say,
`attributed_revenue_usd` means. Good data discovery requires good **metadata**.

### Do it in the UI
1. In **Catalog**, open **`retail_corp.bronze.fact_marketing_campaigns`**.
2. Look at the **Columns** tab — the **Comment** column is mostly empty.
3. Click the table name's **description** area at the top — it's blank too.

That's the gap you'll fix next. Undocumented data is hard for people *and* for Genie
(Lab 2.4) to use correctly."""),

md("""## 2.3 — Add metadata (descriptions) — with AI, in the UI

Databricks can **write the descriptions for you** with AI, right in the Catalog UI.
This is the business-friendly way to document data — no SQL.

### Do it in the UI (AI-generated descriptions)
1. In **Catalog**, open a table, e.g. **`bronze.dim_product`**.
2. Next to the table's (empty) description, click **✨ AI generate**. Databricks
   proposes a description from the table's columns and sample data. Review it, edit if
   needed, and **Accept**.
3. On the **Columns** tab, click **✨ AI generate** to suggest descriptions for **all
   columns** at once (or click the pencil ✏️ on a single column to write your own).
   Review and **Accept** the ones that look right.
4. Repeat for the other bronze tables — especially `fact_orders`, `fact_order_items`,
   `fact_marketing_campaigns`, and `fact_sales_forecast`.

### What good descriptions look like
Use these as a guide (edit the AI's suggestions toward this level of clarity):

| Column | Good description |
|--------|------------------|
| `dim_product.unit_cost` | Cost to the company per unit in USD (used to compute profit). |
| `fact_orders.order_status` | COMPLETED, RETURNED, or CANCELLED. |
| `fact_order_items.unit_price` | Actual price paid per unit in USD (after any discount). |
| `fact_marketing_campaigns.attributed_revenue_usd` | Revenue attributed to the campaign in USD (used for marketing ROI). |
| `fact_sales_forecast` (table) | Revenue forecast by category/month from the Data Science team — treat as a hand-off to validate, not ground truth. |

> 💡 **Why this matters:** Genie (next section) reads these descriptions to understand
> intent. Ten minutes documenting your data here pays off every time you or a colleague
> asks Genie a question.

> ✅ **Confirm:** re-open a table's **Columns** tab and check the **Comment** column is
> now filled in. Your data is self-explanatory."""),

md("""## 2.4 — Way #2: Discover with Genie One (natural language)

**Genie** lets you ask questions about your data in plain English — no SQL
required. **Genie One** is the workspace-wide entry point for this.

### Do it in the UI
1. Left sidebar → **Genie** (or the ✨ **Ask Genie** button).
2. Point Genie at your data: choose the **`retail_corp.bronze`** schema (or the
   individual tables).
3. Ask discovery-style questions in your own words, for example (paraphrase — say
   it however feels natural):
   - *"What tables are available and what does each one contain?"*
   - *"How many orders do we have, and what date range do they cover?"*
   - *"What product categories exist?"*
   - *"Show total revenue by category."*
4. Notice how Genie **explains its answer** and shows the SQL it wrote. Because you
   added good descriptions in 2.3, Genie's answers are more accurate.

> 🧠 **Why metadata matters here:** Genie reads your table and column descriptions
> to understand intent. The comments you added in 2.3 directly improve Genie's
> answers. This is the payoff of good documentation."""),

md("""## 2.5 — Way #3: Organize into a Domain, then access through it

**Domains** (Unity Catalog data domains / catalog governance) let you group data
assets into a **business-friendly** collection — e.g. *"Retail Sales & Marketing"*
— so people find data by **business area**, not by hunting through raw schemas.

### Create a domain in the UI
1. Left sidebar → **Catalog**, then open **Governance / Domains** (may appear as
   **Catalog Explorer → Domains**, depending on your workspace).
2. Click **Create domain**. Name it **`Retail Sales & Marketing`**.
3. Add a description: *"All sales, product, customer, and marketing data for
   Databricks Retail Corp."*
4. **Assign assets** to the domain — add the `retail_corp.bronze` schema (or the
   five tables individually).
5. Optionally add **tags** like `sales`, `marketing`, `product` to make assets
   searchable.

### Access your data *through* the domain
6. Open the domain you just created. You should now see all five tables grouped
   under one business heading.
7. From the domain view, click a table (e.g. `fact_marketing_campaigns`) and
   confirm you can preview it — you're now reaching your data **by business area**,
   which is how a non-technical colleague would naturally look for it.

> 🏷️ **Lightweight alternative — tags.** If Domains aren't enabled in your workspace,
> you can still group assets by a business label: in **Catalog**, open the `bronze`
> schema (or each table) → **Tags** → add a tag like `domain` = `Retail Sales &
> Marketing`. Later you can **search** by that tag to pull the group back up. Domains
> are about *organization*, so this is a fine stand-in and no later lab depends on it."""),

md("""## 2.6 — Rediscover through the domain (confirm)

Confirm your assets are now findable by their business label — all in the UI:

1. Open the **Domain** you created (or **Search** for the `domain` tag you added).
2. You should see the bronze tables grouped under **Retail Sales & Marketing**.
3. Click a table (e.g. `fact_marketing_campaigns`) straight from the domain view and
   confirm you can preview it. You're now reaching data **by business area** — exactly
   how a non-technical colleague would look for it."""),

md("""## 2.7 — Your Data Map: what these tables can (and can't) answer

Now that you know your data, here's a **map** connecting each table to the business
questions it can answer. Keep this handy — it tells you *what's answerable* before
you start asking Genie in Labs 4–5, and it's honest about the gaps.

### The six bronze tables
| Table | Grain | The important columns |
|-------|-------|-----------------------|
| `dim_product` | 1 / SKU | category, subcategory, **list_price**, **unit_cost** |
| `dim_customer` | 1 / customer | region, country, **customer_segment** |
| `fact_orders` | 1 / order | **order_date**, **channel**, **order_status** |
| `fact_order_items` | 1 / line | **quantity**, **unit_price**, **discount_amount** |
| `fact_marketing_campaigns` | 1 / category / month | **spend_usd**, conversions, **attributed_revenue_usd** |
| `fact_sales_forecast` | 1 / category / month | **forecast_revenue_usd**, bounds (DS team) |

### How they connect
```
fact_order_items ──(order_id)──▶ fact_orders ──(customer_id)──▶ dim_customer
        │
        └────────(product_id)──▶ dim_product ──(category)──▶ fact_marketing_campaigns
                                        └──────(category)──▶ fact_sales_forecast
```
> 🔑 Two of the most useful numbers are **not stored** — they're computed:
> **`line_revenue = quantity × unit_price`** and
> **`line_profit = quantity × (unit_price − unit_cost)`**. You'll build these into
> your silver layer in Lab 3.

### Questions you CAN answer (and the tables you need)
| Business question | Tables |
|-------------------|--------|
| Revenue / profit / margin by **category** | order_items + product (+ orders) |
| Most **units** vs. most **profit $** by category | order_items + product |
| **Marketing ROI** by category | marketing_campaigns |
| Revenue **growth / momentum** over time | order_items + product + orders |
| **Q4 seasonality** by category | order_items + product + orders |
| **Discount depth** — buying volume with markdowns? | order_items + product |
| Revenue by **channel** (Web / Mobile / Marketplace) | orders + order_items |
| Revenue by **region / country** | orders + customer + order_items |
| Revenue by **customer segment** | orders + customer + order_items |
| **Return / cancellation** rate by category | orders + order_items + product |
| Marketing **funnel** (impressions → clicks → conversions) | marketing_campaigns |
| Top **products** (not just categories) | order_items + product |
| The DS team's **revenue forecast** by category | sales_forecast |

### Questions you CANNOT answer with these tables (be honest!)
- ❌ **Inventory / stock levels** — no inventory table.
- ❌ **Web traffic / sessions / cart abandonment** — we only see completed orders.
- ❌ **Customer acquisition cost per customer** — marketing spend is by *category*,
  not linked to individual customers.
- ❌ **A rigorous forecast from first principles** — you have 18 months of history
  to *extrapolate* a trend (you'll do this with `ai_forecast()` in Lab 5), and the
  DS team handed you `fact_sales_forecast` — but part of Lab 5 is learning to
  **question** a forecast rather than trust it blindly.

> 🧭 The **external market-research PDF** (Lab 5) exists precisely to fill some of
> these gaps: projected market growth, willingness-to-pay, and repeat-purchase
> benchmarks that your internal tables simply don't contain."""),

md("""## ✅ Lab 2 complete

You discovered your data **three ways** and improved it:
- ✅ **Unity Catalog** — browsed catalogs, schemas, tables, columns, lineage
- ✅ Found and **filled metadata gaps** with table & column descriptions
- ✅ **Genie One** — asked plain-English questions about your data
- ✅ **Domains** — grouped assets under *"Retail Sales & Marketing"* and accessed
  data through the business domain
- ✅ Built a **Data Map** connecting tables to answerable business questions

> 🧠 **Takeaway:** good metadata isn't busywork — it's what makes both **people**
> and **Genie** able to find and trust your data. You'll feel the payoff in Labs
> 4–5 when Genie answers business questions.

**Next up → Lab 3: Transform Data.** You'll use **Lakeflow Designer** to turn raw
bronze into clean **silver** and business-ready **gold** tables, and schedule a
daily refresh.""")
]

out = os.path.join(ROOT, "labs", "Lab 2 - Data Discovery.ipynb")
write_notebook(out, cells)
print("Wrote", out, "with", len(cells), "cells")
