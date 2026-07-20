#!/usr/bin/env python3
"""
Databricks-branded ONE-PAGER (promotional overview) for the
"Data Camp for Business Users" engagement.

Reuses the zero-dependency PDF engine from the market-research builder so it runs
anywhere (no WeasyPrint / system libs needed). Produces a polished, brand-styled
PDF suitable for sharing with customers.

Run:  python3 assets/onepager/build_onepager.py
Out:  Databricks_Data_Camp_One_Pager.pdf
"""

import os
import sys

# Reuse the PDF engine (class PDF + palette) from the market-research builder.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "assets", "market_research"))
import build_pdf  # noqa: E402
from build_pdf import PDF, RED, DARK, GREEN, GREY, BLACK  # noqa: E402

# Tighten spacing for a dense SINGLE-PAGE layout. These module globals are read by
# the engine's methods at call time, so overriding them here affects only this run
# (each builder process imports build_pdf fresh — the market-research PDF is untouched).
build_pdf.LINE = 12.5
build_pdf.TOP_Y = 752
build_pdf.BOTTOM_Y = 40


class OnePager(PDF):
    """PDF subclass with compact heading spacing so everything fits on one page."""

    def h2(self, s):
        self.y -= 6
        self.text(build_pdf.MARGIN_X, self.y, s, 13, bold=True, color=DARK)
        self.y -= 4
        self.hline(build_pdf.MARGIN_X, build_pdf.PAGE_W - build_pdf.MARGIN_X,
                   self.y, RED, 1.4)
        self.y -= 12

    def bullet(self, s, size=10):
        # Flush bullet: text left-edge aligns with body paragraphs (MARGIN_X);
        # the red marker sits in the gutter just left of the margin. Line spacing
        # and trailing gap match para(), so bullet blocks read like the scenario.
        MX = build_pdf.MARGIN_X
        LINE = build_pdf.LINE
        lines = build_pdf.wrap(s, size, build_pdf.PAGE_W - 2 * MX)
        for i, ln in enumerate(lines):
            self._ensure(LINE)
            if i == 0:
                self.text(MX - 12, self.y, "•", size, color=RED)
            self.text(MX, self.y, ln, size, color=BLACK)
            self.y -= LINE
        self.y -= 4  # same trailing gap as para(gap=4)


def render():
    p = OnePager()
    p.y = build_pdf.TOP_Y  # honor the tightened top margin

    # ---- Masthead ----
    p.h1("Databricks Data Camp")
    p.text(build_pdf.MARGIN_X, p.y, "FOR BUSINESS USERS", 11, bold=True, color=RED)
    p.y -= 13
    p.para("A hands-on, story-driven lab series that turns business analysts into a "
           "self-service data team — from raw data to a governed, data-driven decision "
           "on the Databricks Platform. Some SQL helps; no engineering background needed.",
           size=10, gap=4)

    # ---- The scenario ----
    p.h2("The scenario that carries the journey")
    p.para("Participants become the new CEO of \"Databricks Retail Corp.\" — a merch shop "
           "that has never used Databricks on its own data. Their mission: decide which "
           "product category to promote next quarter, backed by real evidence (sales, a "
           "forecast, marketing ROI, external research). Every lab advances that decision, "
           "so skills land in a business context people remember.", size=10, gap=4)

    # ---- Format ----
    p.h2("The format")
    p.bullet("8 self-paced labs as guided Databricks notebooks — run in order.", size=10)
    p.bullet("UI-first & business-friendly: click-through Databricks UI; code only where "
             "there's no UI path (clearly marked optional).", size=10)
    p.bullet("One-click setup: a single deploy script provisions everything; automated "
             "permission & prerequisite checks flag exactly what's needed.", size=10)
    p.bullet("Safe & repeatable: synthetic data, graceful fallbacks, and a clean-up lab "
             "that resets the environment for the next cohort.", size=10)
    p.bullet("Delivery: self-guided, instructor-led, or hackathon warm-up — approx. "
             "half a day end to end.", size=10)
    p.bullet("Who it's for: business analysts, operations & finance teams, and any "
             "data-curious business user who knows a little SQL. Ideal as an onboarding "
             "accelerator, a pre-hackathon primer, or a proof-of-value that lands the "
             "lakehouse story with a non-technical audience.", size=10)

    # ---- The labs ----
    p.h2("What participants build (the 8 labs)")
    p.table(
        ["Lab", "What they do", "Databricks capability"],
        [
            ["0 · Setup", "Deploy assets, check permissions & previews", "Unity Catalog"],
            ["1 · Ingest", "Connect the operational source system", "Lakeflow Connect, Lakebase"],
            ["2 · Discover", "Explore & document data three ways", "Unity Catalog, Genie, Domains"],
            ["3 · Transform", "Build clean silver & gold tables", "Lakeflow Designer, medallion"],
            ["4 · KPIs", "Define shared metrics once, for all", "Metric Views"],
            ["5 · Decide", "Ask questions, forecast, weigh evidence", "Genie Spaces, ai_forecast()"],
            ["6 · Visualize", "Track the decision on live dashboards", "AI/BI Dashboards"],
            ["7 · Clean up", "Reset the workspace for the next run", "Governed lifecycle"],
        ],
        [15, 44, 30],
    )

    # ---- Outcomes ----
    p.h2("What your team walks away able to do")
    p.bullet("Find & trust data with Unity Catalog, Genie, and business domains.", size=10)
    p.bullet("Turn raw tables into business-ready KPIs with a visual, no-code pipeline.", size=10)
    p.bullet("Define revenue, profit, cost & marketing ROI once — one source of truth "
             "every dashboard and Genie answer shares.", size=10)
    p.bullet("Ask questions in plain English, forecast next quarter, and validate a "
             "hand-off instead of trusting it blindly.", size=10)
    p.bullet("Build & share AI/BI dashboards the whole company tracks daily.", size=10)

    p.spacer(4)
    p.footer_note("Databricks Data Camp for Business Users  |  Hands-on enablement by "
                  "Databricks Field Engineering. \"Databricks Retail Corp.\" and all figures "
                  "are fictional, for instructional use only.")

    out = os.path.join(HERE, "Databricks_Data_Camp_One_Pager.pdf")
    p.build(out)
    print("Wrote", out)


if __name__ == "__main__":
    render()
