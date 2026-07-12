# Setup & Reference — Databricks Data Camp for Business Users

This file holds the **prerequisites, permissions, data model, repository layout, and
maintainer notes** for the labs. If you just want to *run* the training, start with
the [README](README.md) and open **Lab 0** — the automated checks there will tell you
exactly what (if anything) you're missing. This document is the deeper reference.

---

## ✅ Prerequisites & permissions

These labs are written so a **non-admin business user** can complete them. **Lab 0
runs an automated permission check** and, for anything missing, prints exact
copy-paste SQL for your workspace admin — you don't have to figure it out yourself.

### At a glance

- Access to a Databricks workspace with **Unity Catalog** enabled
- Ability to **attach to Serverless** (or a UC-enabled cluster) and use a **SQL Warehouse**
- Permission to **create a catalog** *or* have an admin pre-create `retail_corp` and
  grant you ownership
- **Genie / AI-BI** and **Lakeflow** features enabled (workspace toggles)
- *(Optional)* **Lakebase / Database Instances** enabled for Lab 1's ingestion source

If a feature isn't enabled, every lab has a **graceful fallback** so you can still
learn the concept and complete the work.

### Full permission reference

The automated check in Lab 0 (§0.3) tells you exactly which of these are missing —
this table is here for reference and to hand to an admin.

| # | Capability | Why it's needed | Lab |
|---|------------|-----------------|-----|
| 1 | **Attach to compute** (Serverless or a UC-enabled cluster) | Run any code | All |
| 2 | **Unity Catalog enabled** on the workspace | Governed tables, Genie, domains | All |
| 3 | **`CREATE CATALOG`** on the metastore *— OR —* an admin pre-creates `retail_corp` and grants you **ownership** | Create the project catalog | 0 |
| 4 | **`USE CATALOG`, `CREATE SCHEMA`, `CREATE TABLE`, `SELECT`, `MODIFY`** on the catalog | Build bronze/silver/gold tables | 0, 1, 3 |
| 5 | **`CREATE VOLUME`** (covered by schema-level `CREATE TABLE`) | Store CSVs + the PDF | 0, 1 |
| 6 | A **SQL Warehouse** you can use (Serverless recommended) | Genie, metric views, dashboards | 2, 4, 5, 6 |
| 7 | **Lakeflow / Declarative Pipelines** entitlement | Build the medallion pipeline | 3 |
| 8 | **Genie & AI/BI** enabled (Databricks Assistant) | Data discovery, Genie Spaces, dashboards | 2, 4, 5, 6 |
| 9 | **Lakebase / Database Instances** enabled *(optional)* | The "source system" for Lab 1 | 1 |

> ⚠️ **If you are NOT an admin:** you most likely have items 1–2 and can be granted
> 3–5 easily. Items 6–9 are workspace *features* an admin toggles once. The Lab 0
> checker prints copy-paste SQL your admin can run for the grant-based items.

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

## 📁 Repository structure

```
data-camp-for-business/
├── README.md                     ← start here: overview + story + how to run
├── SETUP.md                      ← you are here: prerequisites, data model, maintainer notes
├── labs/                         ← the 8 guided lab notebooks (run in order)
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
│   ├── nbbuild.py                ← ipynb builder helper (maintainers only)
│   └── build_lab*.py             ← notebook generators (maintainers only)
├── data/
│   └── bronze/                   ← seed CSVs loaded into bronze in Lab 0
│       ├── dim_product.csv
│       ├── dim_customer.csv
│       ├── fact_orders.csv
│       ├── fact_order_items.csv
│       ├── fact_marketing_campaigns.csv
│       └── fact_sales_forecast.csv
└── assets/
    ├── screenshot mock website.png                ← storefront mockup used in the README
    └── market_research/
        ├── Databricks_Retail_Market_Research.pdf  ← download in Lab 0, use in Lab 5
        └── build_pdf.py                            ← regenerates the PDF
```

---

## 🔧 For maintainers

- **Change catalog/schema names** in one place: `setup/config.py`.
- **Regenerate the seed data:** `python3 setup/generate_seed_data.py` (writes
  `data/bronze/*.csv`).
- **Regenerate the market-research PDF:** `python3 assets/market_research/build_pdf.py`.
- **Regenerate the notebooks:** `for n in 0 1 2 3 4 5 6 7; do python3 setup/build_lab$n.py; done`.
  The notebook *content* lives in the `setup/build_lab*.py` generators, which emit
  valid `.ipynb` JSON via `setup/nbbuild.py`. **Edit the generator, not the `.ipynb`.**

---

## 📚 Credits & references

- Metric-view patterns adapted from *Databricks Dashboard In A Day — Lab 2: Data
  Modelling.*
- Built as hands-on enablement for business users at a Databricks customer.

All figures, companies, and the market-research brief are **fictional**, created for
instructional use only.
