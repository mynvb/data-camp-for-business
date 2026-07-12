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

md("""## 2.0 — Load config"""),

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
print("Catalog:", cfg["CATALOG"])"""),

md("""## 2.1 — Way #1: Discover with Unity Catalog

**Unity Catalog** is your governed data explorer. Everything is organized as
**Catalog → Schema → Table → Column**, with permissions and lineage built in.

### Do it in the UI
1. Left sidebar → **Catalog**.
2. Expand **`retail_corp`** → **`bronze`**.
3. Click each table (e.g. `fact_orders`) and explore the tabs:
   - **Overview / Columns** — column names & types.
   - **Sample Data** — a preview of real rows.
   - **Details** — owner, size, created date.
   - **Lineage** — where the data came from and what depends on it.
   - **Insights / Permissions** — who can access it.

### Do it in code
The same information is available via SQL — handy for a quick scan."""),

code("""# List everything in the catalog
display(spark.sql(f"SHOW SCHEMAS IN {cfg['CATALOG']}"))"""),

code("""display(spark.sql(f"SHOW TABLES IN {cfg['CATALOG_BRONZE']}"))"""),

code("""# Inspect the columns of one table
display(spark.sql(f"DESCRIBE TABLE {cfg['CATALOG_BRONZE']}.fact_orders"))"""),

code("""# information_schema is the SQL-standard way to browse metadata across tables
display(spark.sql(f'''
    SELECT table_name, column_name, data_type, comment
    FROM {cfg['CATALOG']}.information_schema.columns
    WHERE table_schema = 'bronze'
    ORDER BY table_name, ordinal_position
'''))"""),

md("""## 2.2 — Find the metadata gaps

Notice in the result above that most `comment` values are **empty**. That means a
teammate browsing the catalog has no idea what, say, `attributed_revenue_usd`
means. Good data discovery requires good **metadata**.

Let's programmatically find which tables and columns are missing descriptions."""),

code("""tables_missing_comment = []
cols_missing = spark.sql(f'''
    SELECT table_name, column_name
    FROM {cfg['CATALOG']}.information_schema.columns
    WHERE table_schema = 'bronze' AND (comment IS NULL OR comment = '')
    ORDER BY table_name, ordinal_position
''')
print("Columns missing a description:")
display(cols_missing)"""),

md("""## 2.3 — Add metadata (descriptions)

Now we fix it. We'll add a **table comment** and **column comments** to each bronze
table. Well-described data is easier to discover — and, importantly, **Genie gets
much smarter** when tables and columns have good descriptions.

> 💡 You can also do this in the UI: open a table in **Catalog**, click the pencil
> ✏️ next to the description, and (on many workspaces) click **AI generate** to let
> Databricks suggest a description. Here we set them explicitly with SQL so the labs
> are reproducible."""),

code("""B = cfg["CATALOG_BRONZE"]

# --- Table-level comments ---
table_comments = {
    "dim_product": "Product catalog for Databricks Retail Corp. One row per merch SKU across 5 categories.",
    "dim_customer": "E-commerce customer master. One row per registered customer.",
    "fact_orders": "Order headers. One row per order placed on the online store.",
    "fact_order_items": "Order line items. One row per product within an order.",
    "fact_marketing_campaigns": "Marketing campaigns by category and month, with spend and attributed revenue.",
    "fact_sales_forecast": "Forward-looking revenue forecast by category and month, provided by the Data Science team. Treat as an external hand-off to be validated, not ground truth.",
}
for t, c in table_comments.items():
    spark.sql(f"COMMENT ON TABLE {B}.{t} IS '{c}'")
    print("✓ described table", t)"""),

code("""# --- Column-level comments ---
column_comments = {
    "dim_product": {
        "product_id": "Unique product identifier (primary key).",
        "product_name": "Display name of the merch item.",
        "category": "Merch category: Outerwear, T-Shirts & Tops, Headwear, Accessories, Drinkware.",
        "subcategory": "Finer product grouping within a category (e.g. Hoodie, Cap).",
        "list_price": "Standard selling price in USD before discounts.",
        "unit_cost": "Cost to the company per unit in USD (used to compute profit).",
        "launch_date": "Date the product was first offered for sale.",
        "is_active": "Whether the product is currently sold.",
    },
    "fact_orders": {
        "order_id": "Unique order identifier (primary key).",
        "customer_id": "Customer who placed the order (FK to dim_customer).",
        "order_date": "Calendar date the order was placed.",
        "order_ts": "Exact timestamp the order was placed.",
        "channel": "Sales channel: Web, Mobile App, or Marketplace.",
        "order_status": "COMPLETED, RETURNED, or CANCELLED.",
        "shipping_cost": "Shipping charged to the customer in USD.",
    },
    "fact_order_items": {
        "order_item_id": "Unique line-item identifier (primary key).",
        "order_id": "Order this line belongs to (FK to fact_orders).",
        "product_id": "Product sold on this line (FK to dim_product).",
        "quantity": "Units of the product on this line.",
        "unit_price": "Actual price paid per unit in USD (after any discount).",
        "discount_amount": "Total discount applied to this line in USD.",
    },
    "fact_marketing_campaigns": {
        "campaign_id": "Unique campaign identifier (primary key).",
        "campaign_name": "Human-readable campaign name.",
        "category": "Merch category the campaign promoted (FK-like to dim_product.category).",
        "channel": "Marketing channel: Paid Search, Paid Social, Email, Display.",
        "spend_usd": "Amount spent on the campaign in USD.",
        "attributed_revenue_usd": "Revenue attributed to the campaign in USD (used for marketing ROI).",
        "conversions": "Number of purchases attributed to the campaign.",
    },
}
for t, cols in column_comments.items():
    for col, c in cols.items():
        spark.sql(f"COMMENT ON COLUMN {B}.{t}.{col} IS '{c}'")
    print(f"✓ described {len(cols)} columns on {t}")"""),

code("""# Re-check: far fewer gaps now (we intentionally described the important columns)
display(spark.sql(f'''
    SELECT table_name, COUNT(*) AS columns_missing_desc
    FROM {cfg['CATALOG']}.information_schema.columns
    WHERE table_schema = 'bronze' AND (comment IS NULL OR comment = '')
    GROUP BY table_name ORDER BY table_name
'''))"""),

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

> 🧭 **If Domains aren't enabled** in your workspace, that's an admin feature
> toggle. You can still complete every later lab — Domains are about *organization*,
> not a hard dependency. As a lightweight stand-in, you can **tag** the schema
> (Catalog → schema → Tags) with `domain=retail_sales_marketing`."""),

code("""# Lightweight, reproducible stand-in for a domain: tag the schema and tables
# so they're discoverable by a business label even without the Domains UI.
B = cfg["CATALOG_BRONZE"]
try:
    spark.sql(f"ALTER SCHEMA {B} SET TAGS ('domain' = 'Retail Sales & Marketing')")
    for t in cfg["BRONZE_TABLES"]:
        spark.sql(f"ALTER TABLE {B}.{t} SET TAGS ('domain' = 'Retail Sales & Marketing')")
    print("✓ Tagged the bronze schema and tables with domain = 'Retail Sales & Marketing'.")
    print("  (In the UI you'd formalize this as a Domain per the steps above.)")
except Exception as e:
    print("Tagging not available here:", str(e)[:150])
    print("→ Use the Domains UI steps above instead.")"""),

md("""## 2.6 — Rediscover through the domain (confirm)

Confirm your assets are now findable by their business label. In the UI you'd
browse the **Domain**; in code we can list everything tagged with our domain."""),

code("""try:
    display(spark.sql(f'''
        SELECT table_name, tag_name, tag_value
        FROM {cfg['CATALOG']}.information_schema.table_tags
        WHERE tag_name = 'domain'
        ORDER BY table_name
    '''))
except Exception as e:
    print("Tag lookup view not available here:", str(e)[:150])
    print("→ Browse the Domain in the Catalog UI to confirm your assets are grouped.")"""),

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
