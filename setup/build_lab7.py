#!/usr/bin/env python3
"""Builds labs/Lab 7 - Clean Up.ipynb"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nbbuild import md, code, write_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cells = [
md("""# Lab 7 — Clean Up 🧹

### Databricks Data Camp for Business Users 🛍️

This lab **removes everything the labs created** and returns your workspace to its
original state. Use it when you've finished the training, or when you're resetting
the environment for the next learner.

> # ⚠️ STOP AND READ THIS FIRST
>
> **Running this lab is destructive and irreversible.** It will:
> - **Delete the entire `retail_corp` catalog** — every bronze, silver, and gold
>   table, every view, the Volume, and all uploaded files (including the PDF copy).
> - **Delete the Lakebase instance** `retail-corp-lakebase`.
> - **Delete the daily refresh Job** `retail_corp_gold_daily_refresh`.
>
> **All your progress across Labs 0–6 will be gone.** The metric views, the
> forecasts, the KPIs — everything. There is **no undo**.
>
> If you want to keep any results, **export or screenshot them before continuing.**
>
> A few assets can't be safely deleted from here (Genie Space, dashboards, the
> Lakeflow pipeline, the domain, the Git folder). This lab gives you **manual UI
> steps** for those at the end.

⏱️ *Estimated time: 10 minutes.*"""),

md("""## 7.0 — Load config"""),

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
print("This lab will PERMANENTLY DELETE the following:")
print("  • Catalog (and everything in it):", cfg["CATALOG"])
print("  • Lakebase instance:             ", cfg["LAKEBASE_INSTANCE"])
print("  • Daily Job:                     ", cfg["GOLD_JOB_NAME"])"""),

md("""## 7.1 — Confirm you really want to do this

As a safety gate, you must **explicitly opt in** by setting `CONFIRM_CLEANUP = True`
in the next cell. While it's `False` (the default), every deletion cell below will
**skip** and simply tell you what it *would* have done — so you can read through the
whole lab safely first.

When you're certain, change it to `True` and run the cells in order."""),

code("""# 🔒 SAFETY GATE — leave as False to preview; set True to actually delete.
CONFIRM_CLEANUP = False

if CONFIRM_CLEANUP:
    print("⚠️  CONFIRM_CLEANUP = True — deletion cells below WILL remove resources.")
else:
    print("🛡️  CONFIRM_CLEANUP = False — this is a DRY RUN. Nothing will be deleted.")
    print("    Read through the lab, then set CONFIRM_CLEANUP = True when ready.")"""),

md("""## 7.2 — Delete the daily refresh Job

Removes the scheduled Job created in Lab 3 (`retail_corp_gold_daily_refresh`) so it
stops running. (If you scheduled the Lakeflow *pipeline* directly instead, see the
manual steps in 7.6.)"""),

code("""job_name = cfg["GOLD_JOB_NAME"]
try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    found = list(w.jobs.list(name=job_name))
    if not found:
        print(f"• No Job named '{job_name}' found — nothing to delete.")
    elif not CONFIRM_CLEANUP:
        print(f"[dry run] Would delete Job '{job_name}' "
              f"(job_id={found[0].job_id}). Set CONFIRM_CLEANUP=True to delete.")
    else:
        for j in found:
            w.jobs.delete(job_id=j.job_id)
            print(f"✓ Deleted Job '{job_name}' (job_id={j.job_id}).")
except Exception as e:
    print("! Could not delete the Job automatically:", str(e)[:180])
    print("  → Manual: left nav → Jobs & Pipelines → find the job → ⋮ → Delete.")"""),

md("""## 7.3 — Delete the Lakebase instance

Removes the managed Postgres instance provisioned in Lab 0
(`retail-corp-lakebase`)."""),

code("""inst_name = cfg["LAKEBASE_INSTANCE"]
try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    # Does it exist?
    exists = False
    try:
        w.database.get_database_instance(name=inst_name)
        exists = True
    except Exception:
        exists = False

    if not exists:
        print(f"• No Lakebase instance named '{inst_name}' found — nothing to delete.")
    elif not CONFIRM_CLEANUP:
        print(f"[dry run] Would delete Lakebase instance '{inst_name}'. "
              f"Set CONFIRM_CLEANUP=True to delete.")
    else:
        # purge=True removes it fully; API name may vary slightly by SDK version.
        try:
            w.database.delete_database_instance(name=inst_name, purge=True)
        except TypeError:
            w.database.delete_database_instance(name=inst_name)
        print(f"✓ Deleted Lakebase instance '{inst_name}'.")
except Exception as e:
    print("! Could not delete the Lakebase instance automatically:", str(e)[:180])
    print("  → Manual: left nav → Compute → Database Instances (or Lakebase) →")
    print(f"    select '{inst_name}' → Delete.")"""),

md("""## 7.4 — Drop the catalog (this removes ALL tables, views, and the Volume)

This is the big one. Dropping the catalog with `CASCADE` removes **every** schema
(`bronze`, `silver`, `gold`), **every** table and view (including your metric views
and forecasts), and the **Volume** with all uploaded files (CSVs and the PDF copy).

> 💣 After this cell runs with `CONFIRM_CLEANUP = True`, `retail_corp` and all its
> contents are gone."""),

code("""catalog = cfg["CATALOG"]
# Show what's about to be destroyed, for a last look.
try:
    schemas = [r[0] for r in spark.sql(f"SHOW SCHEMAS IN {catalog}").collect()]
    print(f"Catalog '{catalog}' currently contains schemas: {schemas}")
    for s in schemas:
        if s == "information_schema":
            continue
        try:
            tbls = spark.sql(f"SHOW TABLES IN {catalog}.{s}").collect()
            print(f"  {s}: {len(tbls)} tables/views")
        except Exception:
            pass
except Exception as e:
    print(f"• Catalog '{catalog}' not found or already removed ({str(e)[:80]}).")"""),

code("""catalog = cfg["CATALOG"]
if not CONFIRM_CLEANUP:
    print(f"[dry run] Would run:  DROP CATALOG IF EXISTS {catalog} CASCADE")
    print("          Set CONFIRM_CLEANUP=True to actually drop the catalog.")
else:
    try:
        spark.sql(f"DROP CATALOG IF EXISTS {catalog} CASCADE")
        print(f"✓ Dropped catalog '{catalog}' and everything inside it.")
    except Exception as e:
        print("! Could not drop the catalog:", str(e)[:180])
        print("  → You may lack DROP permission. Ask an admin to run:")
        print(f"        DROP CATALOG IF EXISTS {catalog} CASCADE;")"""),

md("""## 7.5 — Verify the programmatic cleanup

Confirms the catalog is gone. (The Lakebase instance and Job were handled above.)"""),

code("""catalog = cfg["CATALOG"]
try:
    remaining = spark.sql(f"SHOW CATALOGS LIKE '{catalog}'").count()
    if remaining == 0:
        print(f"✓ Catalog '{catalog}' is gone.")
    else:
        if CONFIRM_CLEANUP:
            print(f"! Catalog '{catalog}' still exists — check the error in 7.4.")
        else:
            print(f"• Catalog '{catalog}' still exists (expected — this was a dry run).")
except Exception as e:
    print("Check inconclusive:", str(e)[:120])"""),

md("""## 7.6 — Manual clean-up (things that can't be deleted from here)

A few assets you created in the UI aren't tied to the catalog and can't be safely
removed from this notebook. Delete them by hand:

1. **Genie Space** (Lab 5)
   - Left nav → **Genie** → open **`Retail Corp — Category Decision`** → **⋮ /
     Settings → Delete**. Also removes the PDF you attached to it.

2. **AI/BI Dashboards** (Lab 6)
   - Left nav → **Dashboards** → delete **`Retail Corp — Daily KPIs`** and
     **`Retail Corp — Daily KPIs (Genie)`** → **⋮ → Move to Trash / Delete**.

3. **Lakeflow pipeline** (Lab 3)
   - Left nav → **Jobs & Pipelines** → find **`retail_corp_medallion`** →
     **⋮ → Delete**. (If you scheduled the pipeline directly, this also removes that
     schedule.)

4. **Data domain** (Lab 2)
   - **Catalog → Governance / Domains** → open **`Retail Sales & Marketing`** →
     remove assigned assets → **Delete domain**. *(If you only tagged the schema
     instead of creating a formal domain, dropping the catalog in 7.4 already cleared
     the tags.)*

5. **Lakeflow Connect ingestion pipeline** (Lab 1)
   - If you created **`retail_corp_bronze_ingest`** via the UI, delete it under
     **Data Ingestion / Jobs & Pipelines** as well.

6. **This Git folder / repo clone** (optional)
   - Left nav → **Workspace** → find your **`data-camp-for-business`** Git folder →
     **⋮ → Delete** if you no longer need the notebooks."""),

md("""## 7.7 — Local secrets reminder (outside Databricks)

This applies to the **local machine / repo** where you first set up the GitHub
connection — not the Databricks workspace:

- If you saved a GitHub token in a local `.env` / `.git-credentials`, and you're done
  with the project, consider **revoking that token** in GitHub
  (**Settings → Developer settings → Personal access tokens**) and deleting the
  local files. This is good hygiene for any credential you no longer need.

*(There's nothing to run here — this is just a reminder.)*"""),

md("""## ✅ Lab 7 complete — environment reset

If you ran the cells with `CONFIRM_CLEANUP = True`:
- ✅ Daily **Job** deleted
- ✅ **Lakebase** instance deleted
- ✅ **Catalog** `retail_corp` dropped (all tables, views, metric views, Volume, files)
- ✅ Manual UI assets removed per 7.6

Your workspace is back to its pre-lab state. 🧹

> 🔁 **Want to run the training again?** Just re-open **Lab 0 — Setup** and run it
> top to bottom. The single deploy script rebuilds everything from scratch.
>
> Thanks for taking Databricks Retail Corp. from "we don't use Databricks" to a
> fully data-driven organization — and for cleaning up after yourself. 👋""")
]

out = os.path.join(ROOT, "labs", "Lab 7 - Clean Up.ipynb")
write_notebook(out, cells)
print("Wrote", out, "with", len(cells), "cells")
