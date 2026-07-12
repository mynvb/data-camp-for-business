#!/usr/bin/env python3
"""
Deterministic seed-data generator for Databricks Retail Corp.

Produces the BRONZE-layer CSVs that get loaded into the pre-provisioned Lakebase
(Postgres) instance in Lab 0/Lab 1. Everything is seeded (random.seed) so the
data is identical on every run and across all learners — the labs' validation
SQL and the "promote Outerwear" narrative depend on stable numbers.

Data model (bronze):
  dim_product              product catalog (5 categories of Databricks merch)
  dim_customer             e-commerce customers
  fact_orders              order headers (one row per order)
  fact_order_items         order line items (one row per product per order)
  fact_marketing_campaigns monthly marketing campaigns per category

Narrative baked into the numbers (so the labs reach a data-driven decision):
  * T-Shirts & Tops  -> highest UNIT volume, but thin-ish margin. A volume play.
  * Outerwear        -> fastest revenue GROWTH, highest MARGIN, best marketing
                        ROI, strong Q4 seasonality. The profit play. WINNER.
  * Accessories      -> high volume, lowest margin. A traffic driver.
  * Headwear         -> mid volume, decent margin, gift seasonality.
  * Drinkware        -> steady, gift seasonality.

Run:  python3 setup/generate_seed_data.py
Out:  data/bronze/*.csv  +  data/bronze/_summary.txt
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "bronze")
os.makedirs(OUT, exist_ok=True)

START = date(2024, 1, 1)
END = date(2025, 6, 30)          # 18 months of history (good for forecasting)
N_CUSTOMERS = 1800

# -------------------------------------------------------------------------
# Product catalog — Databricks-branded merch across 5 categories
# (product_name, category, subcategory, list_price, unit_cost)
# -------------------------------------------------------------------------
PRODUCTS = [
    # Outerwear — high price, high margin, the growth story
    ("Databricks Classic Hoodie",      "Outerwear",        "Hoodie",      65.00, 29.00),
    ("Delta Lake Zip-Up Hoodie",       "Outerwear",        "Hoodie",      72.00, 33.00),
    ("Lakehouse Fleece Jacket",        "Outerwear",        "Jacket",      95.00, 44.00),
    ("Spark Bomber Jacket",            "Outerwear",        "Jacket",     110.00, 53.00),
    # T-Shirts & Tops — high volume, thinner margin
    ("Databricks Logo Tee",            "T-Shirts & Tops",  "T-Shirt",     28.00,  9.00),
    ("Powered by Spark Tee",           "T-Shirts & Tops",  "T-Shirt",     30.00, 10.00),
    ("Unity Catalog Long-Sleeve",      "T-Shirts & Tops",  "Long-Sleeve", 38.00, 14.00),
    ("MLflow Performance Polo",        "T-Shirts & Tops",  "Polo",        45.00, 18.00),
    # Headwear
    ("Databricks Dad Cap",             "Headwear",         "Cap",         26.00,  9.00),
    ("Delta Knit Beanie",              "Headwear",         "Beanie",      24.00,  8.00),
    ("Lakehouse Snapback",             "Headwear",         "Cap",         30.00, 11.00),
    # Accessories — high volume, lowest margin
    ("Databricks Crew Socks",          "Accessories",      "Socks",       14.00,  4.50),
    ("Spark Sticker Pack",             "Accessories",      "Stickers",     8.00,  1.50),
    ("Databricks Canvas Tote",         "Accessories",      "Bag",         18.00,  6.00),
    ("Lakehouse Laptop Sleeve",        "Accessories",      "Bag",         32.00, 12.00),
    # Drinkware
    ("Databricks Steel Water Bottle",  "Drinkware",        "Bottle",      28.00,  9.00),
    ("Delta Ceramic Mug",              "Drinkware",        "Mug",         16.00,  5.00),
    ("Spark Travel Tumbler",           "Drinkware",        "Tumbler",     34.00, 12.00),
]

# Category-level demand behaviour --------------------------------------------
# base_weight     : relative popularity (drives volume share)
# monthly_growth  : compounding trend per month over the 18-month window
# season[m]       : multiplier by calendar month 1..12 (Q4 gifting, winter, etc.)
CAT = {
    "Outerwear": {
        "base_weight": 1.00, "monthly_growth": 0.055,
        "season": {1: 1.25, 2: 1.15, 3: 0.95, 4: 0.80, 5: 0.70, 6: 0.65,
                   7: 0.65, 8: 0.75, 9: 0.95, 10: 1.20, 11: 1.45, 12: 1.55},
    },
    "T-Shirts & Tops": {
        "base_weight": 1.85, "monthly_growth": 0.004,
        "season": {1: 0.90, 2: 0.90, 3: 1.00, 4: 1.10, 5: 1.20, 6: 1.25,
                   7: 1.25, 8: 1.15, 9: 1.00, 10: 0.95, 11: 0.90, 12: 0.90},
    },
    "Headwear": {
        "base_weight": 0.85, "monthly_growth": 0.020,
        "season": {1: 0.95, 2: 0.95, 3: 1.00, 4: 1.05, 5: 1.05, 6: 1.05,
                   7: 1.05, 8: 1.05, 9: 1.00, 10: 1.10, 11: 1.25, 12: 1.30},
    },
    "Accessories": {
        "base_weight": 1.55, "monthly_growth": 0.005,
        "season": {1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00, 6: 1.00,
                   7: 1.00, 8: 1.00, 9: 1.00, 10: 1.05, 11: 1.10, 12: 1.15},
    },
    "Drinkware": {
        "base_weight": 0.80, "monthly_growth": 0.012,
        "season": {1: 1.05, 2: 0.95, 3: 0.95, 4: 0.95, 5: 0.95, 6: 0.95,
                   7: 0.95, 8: 0.95, 9: 1.00, 10: 1.10, 11: 1.20, 12: 1.25},
    },
}

CHANNELS = ["Web", "Web", "Web", "Mobile App", "Mobile App", "Marketplace"]
REGIONS = [
    ("AMER", "United States"), ("AMER", "United States"), ("AMER", "Canada"),
    ("EMEA", "United Kingdom"), ("EMEA", "Germany"), ("EMEA", "France"),
    ("APAC", "Australia"), ("APAC", "India"), ("APAC", "Japan"),
]
SEGMENTS = ["Consumer", "Consumer", "Consumer", "Developer", "Enterprise Gift"]
FIRST = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie",
         "Avery", "Quinn", "Devon", "Skyler", "Reese", "Cameron", "Rowan",
         "Priya", "Wei", "Yuki", "Liam", "Noah", "Emma", "Olivia", "Sofia"]
LAST = ["Chen", "Patel", "Garcia", "Smith", "Muller", "Dubois", "Tanaka",
        "Kim", "Nguyen", "Johnson", "Brown", "Silva", "Rossi", "Kowalski",
        "Andersson", "Okafor", "Haddad", "Ivanov", "Costa", "Nakamura"]


def months_between(d):
    return (d.year - START.year) * 12 + (d.month - START.month)


def weekday_factor(d):
    # slightly higher volume mid-week, lower on weekends for B2B-ish merch store
    return [1.05, 1.08, 1.10, 1.08, 1.02, 0.85, 0.80][d.weekday()]


# -------------------------------------------------------------------------
# 1) dim_product
# -------------------------------------------------------------------------
products = []
for i, (name, cat, sub, price, cost) in enumerate(PRODUCTS, start=1):
    products.append({
        "product_id": 1000 + i,
        "product_name": name,
        "category": cat,
        "subcategory": sub,
        "list_price": f"{price:.2f}",
        "unit_cost": f"{cost:.2f}",
        "launch_date": (START - timedelta(days=random.randint(120, 600))).isoformat(),
        "is_active": "true",
    })

# per-product weight within its category (some hero SKUs)
prod_weight = {}
for p in products:
    prod_weight[p["product_id"]] = random.uniform(0.7, 1.4)

with open(os.path.join(OUT, "dim_product.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(products[0].keys()))
    w.writeheader()
    w.writerows(products)

# -------------------------------------------------------------------------
# 2) dim_customer
# -------------------------------------------------------------------------
customers = []
for cid in range(1, N_CUSTOMERS + 1):
    region, country = random.choice(REGIONS)
    fn = random.choice(FIRST)
    ln = random.choice(LAST)
    signup = START - timedelta(days=random.randint(0, 900))
    customers.append({
        "customer_id": 5000 + cid,
        "first_name": fn,
        "last_name": ln,
        "email": f"{fn.lower()}.{ln.lower()}{cid}@example.com",
        "region": region,
        "country": country,
        "customer_segment": random.choice(SEGMENTS),
        "signup_date": signup.isoformat(),
    })

with open(os.path.join(OUT, "dim_customer.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(customers[0].keys()))
    w.writeheader()
    w.writerows(customers)

customer_ids = [c["customer_id"] for c in customers]
prod_by_cat = {}
for p in products:
    prod_by_cat.setdefault(p["category"], []).append(p)
price_lookup = {p["product_id"]: float(p["list_price"]) for p in products}


def category_weight(cat, d):
    c = CAT[cat]
    m = months_between(d)
    trend = (1 + c["monthly_growth"]) ** m
    return c["base_weight"] * trend * c["season"][d.month]


# -------------------------------------------------------------------------
# 3) fact_orders + 4) fact_order_items
# -------------------------------------------------------------------------
orders = []
items = []
order_id = 90000
item_id = 700000

# campaign discount windows: category is "on promo" in certain months -> deeper
# discounts + more orders. Kept mild so it doesn't overwhelm the organic trend.
promo_windows = {
    "Outerwear": {(2024, 11), (2024, 12), (2025, 3)},
    "T-Shirts & Tops": {(2024, 6), (2024, 7), (2025, 5)},
    "Headwear": {(2024, 12), (2025, 4)},
    "Accessories": {(2024, 11), (2025, 1)},
    "Drinkware": {(2024, 12), (2025, 2)},
}

d = START
base_daily = 22
while d <= END:
    m = months_between(d)
    overall_trend = 1 + 0.9 * (m / 17.0)     # store grows ~1.9x over 18 months
    n_orders = base_daily * overall_trend * weekday_factor(d) * random.uniform(0.80, 1.20)
    n_orders = max(1, int(round(n_orders)))

    # precompute today's category weights
    cw = {cat: category_weight(cat, d) for cat in CAT}
    cats = list(cw.keys())

    for _ in range(n_orders):
        order_id += 1
        cust = random.choice(customer_ids)
        channel = random.choice(CHANNELS)
        n_lines = random.choices([1, 2, 3, 4], weights=[52, 30, 13, 5])[0]
        order_gross = 0.0

        picked = set()
        for _ln in range(n_lines):
            # choose category by today's weights
            cat = random.choices(cats, weights=[cw[c] for c in cats])[0]
            pool = prod_by_cat[cat]
            prod = random.choices(pool, weights=[prod_weight[p["product_id"]] for p in pool])[0]
            pid = prod["product_id"]
            if pid in picked:
                continue
            picked.add(pid)

            qty = random.choices([1, 2, 3], weights=[75, 20, 5])[0]
            list_price = price_lookup[pid]

            on_promo = (d.year, d.month) in promo_windows.get(cat, set())
            if on_promo:
                disc_pct = random.choice([0.10, 0.15, 0.20, 0.25])
            else:
                disc_pct = random.choices([0.0, 0.05, 0.10], weights=[70, 20, 10])[0]
            unit_price = round(list_price * (1 - disc_pct), 2)
            discount_amt = round((list_price - unit_price) * qty, 2)

            item_id += 1
            items.append({
                "order_item_id": item_id,
                "order_id": order_id,
                "product_id": pid,
                "quantity": qty,
                "unit_price": f"{unit_price:.2f}",
                "discount_amount": f"{discount_amt:.2f}",
            })
            order_gross += unit_price * qty

        status = random.choices(["COMPLETED", "COMPLETED", "COMPLETED", "RETURNED", "CANCELLED"],
                                weights=[80, 8, 6, 4, 2])[0]
        shipping = 0.0 if order_gross >= 75 else round(random.choice([4.99, 6.99, 8.99]), 2)
        orders.append({
            "order_id": order_id,
            "customer_id": cust,
            "order_date": d.isoformat(),
            "order_ts": f"{d.isoformat()} {random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}",
            "channel": channel,
            "order_status": status,
            "shipping_cost": f"{shipping:.2f}",
        })
    d += timedelta(days=1)

with open(os.path.join(OUT, "fact_orders.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(orders[0].keys()))
    w.writeheader()
    w.writerows(orders)

with open(os.path.join(OUT, "fact_order_items.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(items[0].keys()))
    w.writeheader()
    w.writerows(items)

# -------------------------------------------------------------------------
# 5) fact_marketing_campaigns  (monthly per category)
# -------------------------------------------------------------------------
# ROI is engineered: Outerwear best, Accessories worst. attributed_revenue is a
# realistic multiple of spend (roas) with noise, so a Marketing-ROI metric view
# = SUM(attributed_revenue)/SUM(spend) ranks Outerwear #1.
CAMPAIGN_ROAS = {          # attributed revenue per $1 spend (before noise)
    "Outerwear": 4.6,
    "Headwear": 3.4,
    "Drinkware": 3.0,
    "T-Shirts & Tops": 2.6,
    "Accessories": 1.8,
}
CAMPAIGN_CHANNELS = ["Paid Search", "Paid Social", "Email", "Display"]
campaigns = []
camp_id = 300
# iterate month by month
cur = date(START.year, START.month, 1)
while cur <= END:
    ym = (cur.year, cur.month)
    for cat in CAT:
        # not every category runs every month; heroes run more often
        run_prob = 0.9 if cat in ("Outerwear", "T-Shirts & Tops", "Accessories") else 0.7
        if ym in promo_windows.get(cat, set()):
            run_prob = 1.0
        if random.random() > run_prob:
            continue
        camp_id += 1
        channel = random.choice(CAMPAIGN_CHANNELS)
        boosted = ym in promo_windows.get(cat, set())
        spend = round(random.uniform(1500, 6000) * (1.6 if boosted else 1.0), 2)
        roas = CAMPAIGN_ROAS[cat] * random.uniform(0.85, 1.15)
        attributed = round(spend * roas, 2)
        impressions = int(spend * random.uniform(180, 320))
        ctr = random.uniform(0.008, 0.025)
        clicks = int(impressions * ctr)
        conv_rate = random.uniform(0.02, 0.06)
        conversions = max(1, int(clicks * conv_rate))
        last_day = (date(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1) - timedelta(days=1))
        campaigns.append({
            "campaign_id": camp_id,
            "campaign_name": f"{cat.split(' ')[0]} {cur.strftime('%b %Y')} {channel}",
            "category": cat,
            "channel": channel,
            "start_date": cur.isoformat(),
            "end_date": last_day.isoformat(),
            "spend_usd": f"{spend:.2f}",
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "attributed_revenue_usd": f"{attributed:.2f}",
        })
    # advance one month
    cur = date(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)

with open(os.path.join(OUT, "fact_marketing_campaigns.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(campaigns[0].keys()))
    w.writeheader()
    w.writerows(campaigns)

# -------------------------------------------------------------------------
# 6) fact_sales_forecast  — "provided by the Data Science team"
# -------------------------------------------------------------------------
# TEACHING DEVICE (Lab 5): these are DELIBERATELY BAD forecasts full of strange
# outliers, so learners who also generate a forecast with the ai_forecast() SQL
# function will SEE the discrepancy and learn to distrust a black-box hand-off.
#
# For context, actual recent (2025-Q2) monthly revenue is roughly:
#   Outerwear ~47K   T-Shirts ~25K   Headwear ~10K   Accessories ~9K   Drinkware ~8K
#
# The DS team's forecast (below) contradicts reality in obvious ways:
#   * Outerwear (our best category) predicted to COLLAPSE toward ~5K.
#   * Headwear predicted to EXPLODE ~8x to ~80K (implausible).
#   * Accessories predicted NEGATIVE revenue (impossible).
#   * Drinkware predicted flat but with a huge uncertainty band.
#   * Values are suspiciously round and the confidence intervals are nonsensical
#     (e.g. lower bound above the point forecast).
# Forecast horizon: the 3 months AFTER the data ends (2025-07, -08, -09).
forecast_rows = []
fc_id = 8000
# (category, [month1, month2, month3] point forecasts, note)
DS_FORECAST = {
    # our proven winner, absurdly forecast to crater:
    "Outerwear":        [6000.0, 5200.0, 4800.0],
    # mid category forecast to 8x overnight:
    "Headwear":         [72000.0, 81000.0, 90000.0],
    # impossible negative revenue:
    "Accessories":      [-1500.0, -800.0, -2000.0],
    # roughly plausible level but paired with broken confidence bounds:
    "Drinkware":        [8000.0, 8000.0, 8000.0],
    # flat/stale: same number 3x, ignores T-shirts' real growth:
    "T-Shirts & Tops":  [20000.0, 20000.0, 20000.0],
}
FC_MONTHS = ["2025-07-01", "2025-08-01", "2025-09-01"]
for cat, points in DS_FORECAST.items():
    for i, (mstart, pt) in enumerate(zip(FC_MONTHS, points)):
        # Intentionally broken/odd confidence intervals:
        if cat == "Accessories":
            lo, hi = pt - 500, pt + 500          # negative band
        elif cat == "Drinkware":
            lo, hi = pt - 40000, pt + 40000      # absurdly wide (±40K on an 8K point)
        elif cat == "Headwear":
            lo, hi = pt + 5000, pt + 15000       # lower bound ABOVE the point (broken)
        else:
            lo, hi = pt * 0.95, pt * 1.05        # suspiciously tight
        fc_id += 1
        forecast_rows.append({
            "forecast_id": fc_id,
            "category": cat,
            "forecast_month": mstart,
            "forecast_revenue_usd": f"{pt:.2f}",
            "lower_bound_usd": f"{lo:.2f}",
            "upper_bound_usd": f"{hi:.2f}",
            "model_name": "ds_prophet_v1",
            "generated_by": "data_science_team",
            "generated_date": "2025-06-28",
        })

with open(os.path.join(OUT, "fact_sales_forecast.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(forecast_rows[0].keys()))
    w.writeheader()
    w.writerows(forecast_rows)

# -------------------------------------------------------------------------
# Summary (also used to sanity-check the narrative)
# -------------------------------------------------------------------------
from collections import defaultdict

rev = defaultdict(float)
profit = defaultdict(float)
units = defaultdict(int)
rev_first = defaultdict(float)   # first 3 months
rev_last = defaultdict(float)    # last 3 months
cat_by_pid = {p["product_id"]: p["category"] for p in products}
cost_by_pid = {p["product_id"]: float(p["unit_cost"]) for p in products}
order_date = {o["order_id"]: o["order_date"] for o in orders}
order_status = {o["order_id"]: o["order_status"] for o in orders}

for it in items:
    oid = it["order_id"]
    if order_status[oid] in ("CANCELLED",):
        continue
    cat = cat_by_pid[it["product_id"]]
    q = int(it["quantity"])
    line_rev = float(it["unit_price"]) * q
    line_profit = (float(it["unit_price"]) - cost_by_pid[it["product_id"]]) * q
    rev[cat] += line_rev
    profit[cat] += line_profit
    units[cat] += q
    od = order_date[oid]
    if od <= "2024-03-31":
        rev_first[cat] += line_rev
    if od >= "2025-04-01":
        rev_last[cat] += line_rev

spend = defaultdict(float)
attrib = defaultdict(float)
for c in campaigns:
    spend[c["category"]] += float(c["spend_usd"])
    attrib[c["category"]] += float(c["attributed_revenue_usd"])

lines = []
lines.append(f"Rows: products={len(products)} customers={len(customers)} "
             f"orders={len(orders)} order_items={len(items)} campaigns={len(campaigns)} "
             f"ds_forecasts={len(forecast_rows)}")
lines.append("")
hdr = f"{'Category':<18}{'Revenue':>13}{'Profit':>13}{'Margin%':>9}{'Units':>9}{'Growth%':>9}{'MktROI':>8}"
lines.append(hdr)
lines.append("-" * len(hdr))
for cat in sorted(rev, key=lambda k: -rev[k]):
    margin = 100 * profit[cat] / rev[cat] if rev[cat] else 0
    growth = 100 * (rev_last[cat] / rev_first[cat] - 1) if rev_first[cat] else 0
    roi = attrib[cat] / spend[cat] if spend[cat] else 0
    lines.append(f"{cat:<18}{rev[cat]:>13,.0f}{profit[cat]:>13,.0f}{margin:>8.1f}%"
                 f"{units[cat]:>9,}{growth:>8.0f}%{roi:>8.1f}x")

summary = "\n".join(lines)
with open(os.path.join(OUT, "_summary.txt"), "w") as f:
    f.write(summary + "\n")
print(summary)
print("\nWrote CSVs to", OUT)
