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

## 🧭 What you'll build (the 8 labs)

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
   deployment script that creates the catalog, schemas, and Volume, and provisions +
   seeds the **Lakebase** source instance. (Bronze starts empty — you fill it in
   Lab 1 with Lakeflow Connect.)
4. **Do the labs in order** (0 → 7). Each builds on the previous one.

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
- **Lakebase / Database Instances** enabled — the operational source Lab 0 seeds and
  Lab 1 ingests from

If an *optional* feature isn't enabled, most labs have a **graceful fallback** so you
can still learn the concept. Lakebase is **required** — it's the source of truth the
whole pipeline is built from. See the full permission table in Lab 0.

---

## 📄 More detail

For the **full permission reference, the data model, the repository layout, and
maintainer notes**, see **[SETUP.md](SETUP.md)**.
