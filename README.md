# 🛍️ Databricks Data Camp for Business Users

**Executable, business-friendly Databricks labs — go from raw data to a data-driven
decision, no data-engineering background required.**

These guided labs teach business users and analysts how to use Databricks for
real self-service analytics. You already know a little SQL; you are **not** a
professional engineer. Every step is explained in plain language, with click-through
UI instructions and copy-paste-ready code, wrapped in a story that makes the *why*
obvious.

---

## 📖 The story: you are the new CEO of Databricks Retail Corp.

![Databricks Retail Corp. storefront](assets/screenshot%20mock%20website.png)

You've just been appointed **CEO of Databricks Retail Corp.** — the e-commerce shop
(a Databricks subsidiary) that sells Databricks-branded merchandise: hoodies, tees,
caps, socks, bottles, and more. Funny enough, Databricks Retail Corp. has **never
used Databricks for its own analytics**. You're here to change that.

*(The storefront above is a fictional mockup for the training. The products shown —
like the Databricks Logo Tee — are the same items you'll analyze in the labs.)*

> **Your mission:** decide **which category of Databricks-branded merch to promote
> next quarter.** You'll make a *truly data-driven* call using:
> - 📊 current **sales numbers**
> - 🔮 a **forecast / growth** view built from sales data
> - 💸 **marketing ROI** and campaign data
> - 📄 **external market research** contained in a PDF
>
> By the end you'll have a defensible recommendation *and* a live dashboard the whole
> company can trust.

Every lab moves that story forward — you connect data, discover it, clean it, define
KPIs, decide, and visualize.

---

## 🧭 What you'll build (the 7 labs)

| Lab | Title | What you do | Key Databricks capabilities |
|-----|-------|-------------|-----------------------------|
| **0** | **Setup** | Clone the repo, check permissions, run **one** deploy script that creates everything | Workspace, Unity Catalog, permission checks |
| **1** | **Data Ingestion** | Connect a pre-provisioned **Lakebase** (Postgres) source; bring in the market-research PDF | **Lakeflow Connect**, Volumes |
| **2** | **Data Discovery** | Explore your data three ways; fix missing metadata; access it via a business domain | **Unity Catalog, Genie One, Domains** |
| **3** | **Transform Data** | Build **silver** & **gold** tables with the medallion architecture; schedule a daily refresh | **Lakeflow Designer**, Jobs |
| **4** | **Business KPIs** | Define shared KPIs (revenue, profit, cost, marketing ROI) once, for everyone | **Metric Views**, Genie Code |
| **5** | **Decision Making** | Ask business questions; **forecast** with `ai_forecast()`, catch a bad Data-Science forecast, combine with the external PDF | **Genie Spaces**, **`ai_forecast()`** |
| **6** | **Visualizing Data** | Build daily dashboards (revenue, operating margin, top-5) two ways | **AI/BI Dashboards**, Genie Code |
| **7** | **Clean Up** | Remove every resource the labs created and reset the workspace | UC `DROP`, SDK, UI steps |

Each notebook ends with a ✅ checklist and a preview of the next lab, so you always
know where you are in the journey.

---

## 🚀 Getting started

1. **Clone this repo into your Databricks workspace.**
   In Databricks: **Workspace → (your user) → ⋮ → Create → Git folder**, and paste:
   ```
   https://github.com/nikita-bubentsov_data/data-camp-for-business
   ```
2. **Open `labs/Lab 0 - Setup.ipynb`** inside Databricks and attach **Serverless**
   compute (or any Unity-Catalog-enabled cluster).
3. **Run Lab 0 top to bottom.** It checks your permissions and runs a single
   deployment script that creates the catalog, schemas, volume, bronze tables, and
   the Lakebase instance.
4. **Do the labs in order** (0 → 6). Each builds on the previous one.

> 💡 New to Databricks notebooks? Just click a cell and press **Shift+Enter** to run
> it. Read the markdown above each code cell first — it explains what's about to happen.

---

## ✅ Prerequisites & permissions

These labs are written so a **non-admin business user** can complete them. **Lab 0
runs an automated permission check** and, for anything missing, prints exact copy-paste
SQL for your workspace admin (you don't have to figure it out yourself).

At a glance you'll need:

- Access to a Databricks workspace with **Unity Catalog** enabled
- Ability to **attach to Serverless** (or a UC-enabled cluster) and use a **SQL Warehouse**
- Permission to **create a catalog** *or* have an admin pre-create `retail_corp` and
  grant you ownership
- **Genie / AI-BI** and **Lakeflow** features enabled (workspace toggles)
- *(Optional)* **Lakebase / Database Instances** enabled for Lab 1's ingestion source

If a feature isn't enabled, every lab has a **graceful fallback** so you can still
learn the concept and complete the work. See the full permission table in Lab 0.

---

## 📁 Repository structure

```
data-camp-for-business/
├── README.md                     ← you are here
├── labs/                         ← the 7 guided lab notebooks (run in order)
│   ├── Lab 0 - Setup.ipynb
│   ├── Lab 1 - Data Ingestion.ipynb
│   ├── Lab 2 - Data Discovery.ipynb
│   ├── Lab 3 - Transform Data.ipynb
│   ├── Lab 4 - Business KPIs.ipynb
│   ├── Lab 5 - Decision Making.ipynb
│   ├── Lab 6 - Visualizing Data.ipynb
│   └── Lab 7 - Clean Up.ipynb
├── setup/                        ← shared config + automation (used by the labs)
│   ├── config.py                 ← ONE place to change catalog/schema names
│   ├── check_permissions.py      ← read-only permission auditor (prints TO-DOs)
│   ├── deploy_all.py             ← single idempotent deployment script
│   ├── generate_seed_data.py     ← regenerates the bronze CSVs (deterministic)
│   └── build_lab*.py             ← notebook generators (maintainers only)
├── data/
│   └── bronze/                   ← seed CSVs loaded into bronze in Lab 0
│       ├── dim_product.csv
│       ├── dim_customer.csv
│       ├── fact_orders.csv
│       ├── fact_order_items.csv
│       └── fact_marketing_campaigns.csv
└── assets/
    └── market_research/
        ├── Databricks_Retail_Market_Research.pdf   ← download in Lab 0, use in Lab 5
        └── build_pdf.py                            ← regenerates the PDF
```

---

## 🗃️ The data model

Your "operational" data (in Lakebase / bronze) is a small retail star schema:

| Table | Grain | Description |
|-------|-------|-------------|
| `dim_product` | 1 row / product | 18 merch SKUs across 5 categories |
| `dim_customer` | 1 row / customer | 1,800 e-commerce customers |
| `fact_orders` | 1 row / order | ~17.5K order headers (18 months of history) |
| `fact_order_items` | 1 row / line item | ~29K order lines |
| `fact_marketing_campaigns` | 1 row / campaign / month | 72 campaigns with spend & attributed revenue |
| `fact_sales_forecast` | 1 row / category / month | 15 forecast rows "from the Data Science team" — **deliberately full of anomalies** so Lab 5 teaches you to *validate* a forecast, not trust it blindly |

The five merch categories: **Outerwear**, **T-Shirts & Tops**, **Headwear**,
**Accessories**, **Drinkware**. Part of the fun of the labs is discovering that the
"best" category to promote depends entirely on *which* metric you trust — which is
exactly why the KPI and Genie labs matter.

> All data is **synthetic and deterministic** (seeded), so every learner sees the
> same numbers and the labs' validation checks always pass. Regenerate it any time
> with `python3 setup/generate_seed_data.py`.

---

## 🔧 For maintainers

- **Change catalog/schema names** in one place: `setup/config.py`.
- **Regenerate the seed data:** `python3 setup/generate_seed_data.py` (writes
  `data/bronze/*.csv`).
- **Regenerate the market-research PDF:** `python3 assets/market_research/build_pdf.py`.
- **Regenerate the notebooks:** `for n in 0 1 2 3 4 5 6; do python3 setup/build_lab$n.py; done`.
  The notebook *content* lives in the `setup/build_lab*.py` generators, which emit
  valid `.ipynb` JSON via `setup/nbbuild.py`. Edit the generator, not the `.ipynb`.

---

## 📚 Credits & references

- Metric-view patterns adapted from *Databricks Dashboard In A Day — Lab 2: Data
  Modelling.*
- Built as hands-on enablement for business users at a Databricks customer.

All figures, companies, and the market-research brief are **fictional**, created for
instructional use only.
