#!/usr/bin/env python3
"""
Pure-Python PDF generator (zero dependencies) for the Databricks Retail Corp.
market research brief used in Lab 5.

Produces a real, valid multi-page PDF using core PDF objects and the built-in
Helvetica font family. No third-party libraries required (works with the macOS
system Python), so the labs repo can regenerate the PDF anywhere.

Run:  python3 build_pdf.py
Out:  Databricks_Retail_Market_Research.pdf
"""

import os

# ----- Page geometry (US Letter, points) -----
PAGE_W, PAGE_H = 612, 792
MARGIN_X = 54
TOP_Y = 740
BOTTOM_Y = 60
LINE = 15  # default leading

# Databricks-ish palette (r,g,b 0-1)
RED = (1.0, 0.212, 0.129)
DARK = (0.106, 0.192, 0.224)
GREEN = (0.0, 0.663, 0.447)
GREY = (0.40, 0.44, 0.46)
BLACK = (0.10, 0.10, 0.10)


_UNI = {
    "—": "-",   # em dash
    "–": "-",   # en dash
    "‘": "'", "’": "'",   # smart single quotes
    "“": '"', "”": '"',   # smart double quotes
    "•": "\x95",  # bullet -> latin-1 bullet
    "…": "...",   # ellipsis
    "→": "->",    # right arrow
    "≠": "!=",
    " ": " ",
}


def _ascii(s):
    for k, v in _UNI.items():
        s = s.replace(k, v)
    return s


def esc(s):
    s = _ascii(s)
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


# Helvetica character widths (per 1000 units) — enough for wrapping accuracy.
_HELV = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667,
    "'": 191, '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333,
    '.': 278, '/': 278, '0': 556, '1': 556, '2': 556, '3': 556, '4': 556,
    '5': 556, '6': 556, '7': 556, '8': 556, '9': 556, ':': 278, ';': 278,
    '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015, 'A': 667, 'B': 667,
    'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722, 'I': 278,
    'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
    'X': 667, 'Y': 667, 'Z': 611, '[': 278, '\\': 278, ']': 278, '^': 469,
    '_': 556, '`': 333, 'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556,
    'f': 278, 'g': 556, 'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222,
    'm': 833, 'n': 556, 'o': 556, 'p': 556, 'q': 556, 'r': 333, 's': 500,
    't': 278, 'u': 556, 'v': 500, 'w': 722, 'x': 500, 'y': 500, 'z': 500,
    '{': 334, '|': 260, '}': 334, '~': 584,
}


def text_width(s, size, bold=False):
    # Bold is slightly wider; approximate with a small factor.
    factor = 1.03 if bold else 1.0
    total = sum(_HELV.get(ch, 556) for ch in s)
    return total / 1000.0 * size * factor


def wrap(text, size, max_w, bold=False):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if text_width(trial, size, bold) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


class PDF:
    def __init__(self):
        self.pages = []          # list of content-stream strings
        self.cur = []            # current page ops
        self.y = TOP_Y

    # --- low-level ---
    def _op(self, s):
        self.cur.append(s)

    def new_page(self):
        if self.cur:
            self.pages.append("\n".join(self.cur))
        self.cur = []
        self.y = TOP_Y

    def _ensure(self, needed):
        if self.y - needed < BOTTOM_Y:
            self.new_page()

    def set_fill(self, rgb):
        self._op(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg")

    def text(self, x, y, s, size, bold=False, color=BLACK):
        font = "F2" if bold else "F1"
        self.set_fill(color)
        self._op("BT")
        self._op(f"/{font} {size} Tf")
        self._op(f"1 0 0 1 {x:.1f} {y:.1f} Tm")
        self._op(f"({esc(s)}) Tj")
        self._op("ET")

    def rect(self, x, y, w, h, rgb):
        self.set_fill(rgb)
        self._op(f"{x:.1f} {y:.1f} {w:.1f} {h:.1f} re f")

    def hline(self, x1, x2, y, rgb, width=1.0):
        self._op(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} RG")
        self._op(f"{width} w")
        self._op(f"{x1:.1f} {y:.1f} m {x2:.1f} {y:.1f} l S")

    # --- high-level flow ---
    def h1(self, s):
        self._ensure(40)
        self.text(MARGIN_X, self.y, s, 22, bold=True, color=RED)
        self.y -= 26

    def subtitle(self, s):
        for ln in wrap(s, 9.5, PAGE_W - 2 * MARGIN_X):
            self._ensure(14)
            self.text(MARGIN_X, self.y, ln, 9.5, color=GREY)
            self.y -= 13
        self.y -= 6

    def h2(self, s):
        self._ensure(38)
        self.y -= 10
        self.text(MARGIN_X, self.y, s, 14.5, bold=True, color=DARK)
        self.y -= 6
        self.hline(MARGIN_X, PAGE_W - MARGIN_X, self.y, RED, 1.5)
        self.y -= 16

    def h3(self, s):
        self._ensure(24)
        self.y -= 4
        self.text(MARGIN_X, self.y, s, 11.5, bold=True, color=GREEN)
        self.y -= 16

    def para(self, s, size=10.5, color=BLACK, gap=6):
        for ln in wrap(s, size, PAGE_W - 2 * MARGIN_X):
            self._ensure(LINE)
            self.text(MARGIN_X, self.y, ln, size, color=color)
            self.y -= LINE
        self.y -= gap

    def bullet(self, s, size=10.5):
        indent = 16
        lines = wrap(s, size, PAGE_W - 2 * MARGIN_X - indent)
        for i, ln in enumerate(lines):
            self._ensure(LINE)
            if i == 0:
                self.text(MARGIN_X + 2, self.y, "•", size, color=RED)
            self.text(MARGIN_X + indent, self.y, ln, size, color=BLACK)
            self.y -= LINE
        self.y -= 2

    def callout(self, lines):
        # estimate height
        wrapped = []
        for (txt, bold) in lines:
            for ln in wrap(txt, 10, PAGE_W - 2 * MARGIN_X - 24):
                wrapped.append((ln, bold))
        h = 14 + len(wrapped) * 14
        self._ensure(h + 8)
        top = self.y + 6
        self.rect(MARGIN_X, top - h, PAGE_W - 2 * MARGIN_X, h, (1.0, 0.957, 0.945))
        self.rect(MARGIN_X, top - h, 4, h, RED)
        yy = top - 14
        for (ln, bold) in wrapped:
            self.text(MARGIN_X + 14, yy, ln, 10, bold=bold, color=BLACK)
            yy -= 14
        self.y = top - h - 10

    def table(self, headers, rows, widths):
        """Simple bordered table. widths are relative weights."""
        total_w = PAGE_W - 2 * MARGIN_X
        scale = total_w / sum(widths)
        colw = [w * scale for w in widths]
        size = 9.2
        row_h = 16

        def draw_header():
            self._ensure(row_h + 4)
            top = self.y
            self.rect(MARGIN_X, top - row_h, total_w, row_h, DARK)
            x = MARGIN_X
            for i, htxt in enumerate(headers):
                self.text(x + 4, top - 11.5, htxt, size, bold=True, color=(1, 1, 1))
                x += colw[i]
            self.y = top - row_h

        draw_header()
        for r in rows:
            # compute needed height (wrap each cell)
            cell_lines = []
            maxlines = 1
            for i, c in enumerate(r):
                wl = wrap(str(c), size, colw[i] - 8)
                cell_lines.append(wl)
                maxlines = max(maxlines, len(wl))
            rh = maxlines * 12 + 5
            if self.y - rh < BOTTOM_Y:
                self.new_page()
                draw_header()
            top = self.y
            # zebra
            self.rect(MARGIN_X, top - rh, total_w, rh, (0.957, 0.965, 0.969))
            x = MARGIN_X
            for i, wl in enumerate(cell_lines):
                yy = top - 11
                for ln in wl:
                    self.text(x + 4, yy, ln, size, color=BLACK)
                    yy -= 12
                x += colw[i]
            # borders
            self.hline(MARGIN_X, MARGIN_X + total_w, top - rh, (0.82, 0.84, 0.85), 0.5)
            self.y = top - rh
        self.y -= 10

    def spacer(self, h=6):
        self.y -= h

    def footer_note(self, s):
        self._ensure(30)
        self.y -= 6
        self.hline(MARGIN_X, PAGE_W - MARGIN_X, self.y, (0.82, 0.84, 0.85), 0.5)
        self.y -= 12
        for ln in wrap(s, 8.5, PAGE_W - 2 * MARGIN_X):
            self.text(MARGIN_X, self.y, ln, 8.5, color=GREY)
            self.y -= 11

    # --- output ---
    def build(self, path):
        self.new_page()  # flush last
        objs = []

        def add(body):
            objs.append(body)
            return len(objs)  # 1-based id

        # Fonts
        f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

        kids_ids = []
        content_ids = []
        for content in self.pages:
            data = content.encode("latin-1", "replace")
            cid = add(b"<< /Length %d >>\nstream\n" % len(data) + data + b"\nendstream")
            content_ids.append(cid)

        pages_id = len(objs) + 1 + len(self.pages)  # placeholder; fix below
        # We need page objects to reference Pages parent; create Pages first id.
        pages_obj_id = None

        # Reserve Pages object id
        pages_obj_id = add(b"PLACEHOLDER_PAGES")

        for cid in content_ids:
            pid = add(
                ("<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
                 "/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> "
                 "/Contents %d 0 R >>" % (pages_obj_id, PAGE_W, PAGE_H, f1, f2, cid)
                 ).encode("latin-1")
            )
            kids_ids.append(pid)

        kids = " ".join("%d 0 R" % k for k in kids_ids)
        objs[pages_obj_id - 1] = (
            "<< /Type /Pages /Count %d /Kids [%s] >>" % (len(kids_ids), kids)
        ).encode("latin-1")

        catalog_id = add(
            ("<< /Type /Catalog /Pages %d 0 R >>" % pages_obj_id).encode("latin-1")
        )

        # Serialize with xref
        out = bytearray()
        out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        offsets = [0] * (len(objs) + 1)
        for i, body in enumerate(objs, start=1):
            offsets[i] = len(out)
            out += ("%d 0 obj\n" % i).encode("latin-1")
            out += body if isinstance(body, (bytes, bytearray)) else body.encode("latin-1")
            out += b"\nendobj\n"
        xref_pos = len(out)
        n = len(objs) + 1
        out += ("xref\n0 %d\n" % n).encode("latin-1")
        out += b"0000000000 65535 f \n"
        for i in range(1, n):
            out += ("%010d 00000 n \n" % offsets[i]).encode("latin-1")
        out += ("trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (n, catalog_id, xref_pos)).encode("latin-1")

        with open(path, "wb") as fh:
            fh.write(out)
        return path


def render():
    p = PDF()
    p.h1("Databricks-Branded Apparel")
    p.subtitle("External Market Research Brief — Q4 Category Promotion Planning")
    p.subtitle("Prepared for: Databricks Retail Corp.  |  Prepared by: NorthStar Retail Insights (independent)  |  Reporting period: Trailing 4 quarters")

    p.callout([
        ("Purpose of this document:", True),
        ("This brief provides EXTERNAL market context to complement Databricks Retail", False),
        ("Corp.'s internal sales, forecast, and marketing data. Use it in Lab 5 to sanity-", False),
        ("check the category the internal numbers point to. Internal data tells you what", False),
        ("has sold; this brief tells you where the broader branded-apparel market is heading.", False),
    ])

    p.h2("1. Executive Summary")
    p.para("The branded developer- and tech-apparel market continues to grow, driven by hybrid-work casualization and the rise of \"conference merch\" as a wearable brand signal. Across the five categories Databricks Retail Corp. sells, growth is NOT evenly distributed. Outerwear (hoodies and jackets) shows the strongest combination of market growth, margin resilience, and repeat-purchase behavior, while accessories deliver volume but thin margins.")
    p.para("Headline finding: The Outerwear category (hoodies, zip-ups, jackets) is the standout opportunity for a Q4 promotion — it leads on projected market growth, has the highest customer willingness-to-pay, and peaks seasonally in Q4.")

    p.h2("2. Category Market Growth (Year-over-Year)")
    p.para("Projected market growth reflects the EXTERNAL branded-apparel market as a whole, not Databricks Retail Corp.'s own sales.")
    p.table(
        ["Category", "YoY Market Growth", "Projected Next-Qtr", "Market Maturity"],
        [
            ["Outerwear (hoodies, jackets)", "+18.4%", "+12.1%", "Growing"],
            ["T-Shirts & Tops", "+6.2%", "+4.0%", "Mature"],
            ["Headwear (caps, beanies)", "+9.8%", "+7.5%", "Growing"],
            ["Accessories (socks, bags)", "+4.1%", "+2.2%", "Saturated"],
            ["Drinkware (bottles, mugs)", "+5.5%", "+3.1%", "Mature"],
        ],
        [34, 22, 22, 22],
    )

    p.h2("3. Seasonality — Q4 Demand Index")
    p.para("An index of 100 represents an average quarter. Values above 100 indicate above-average Q4 demand (holiday gifting, colder weather, end-of-year conference season).")
    p.table(
        ["Category", "Q4 Demand Index", "Primary Q4 Driver"],
        [
            ["Outerwear", "142", "Colder weather + holiday gifting"],
            ["Headwear", "128", "Holiday gifting"],
            ["Drinkware", "119", "Corporate gifting"],
            ["T-Shirts & Tops", "94", "Off-season (warm-weather item)"],
            ["Accessories", "102", "Stocking-filler gifting"],
        ],
        [24, 22, 44],
    )

    p.h2("4. Willingness-to-Pay & Margin Signal")
    p.para("Survey of 2,100 tech-industry consumers who purchased branded apparel in the last 12 months. Willingness-to-pay reflects the perceived acceptable price for a premium-branded item in each category.")
    p.table(
        ["Category", "Avg. Willingness-to-Pay", "Premium Tolerance", "Typical Margin"],
        [
            ["Outerwear", "$68", "High", "52%"],
            ["Headwear", "$29", "Medium", "48%"],
            ["Drinkware", "$34", "Medium", "44%"],
            ["T-Shirts & Tops", "$31", "Medium", "46%"],
            ["Accessories", "$14", "Low", "33%"],
        ],
        [30, 28, 22, 20],
    )

    p.h2("5. Repeat-Purchase & Brand-Loyalty Behavior")
    p.bullet("Outerwear buyers have the highest 12-month repeat-purchase rate at 41% — a hoodie buyer often returns for a second color or a matching item.")
    p.bullet("Headwear repeat rate: 34%. Strong add-on / bundle attachment.")
    p.bullet("T-Shirts repeat rate: 29%. High volume but commoditized; price-sensitive.")
    p.bullet("Drinkware repeat rate: 22%. Largely one-time gifting purchases.")
    p.bullet("Accessories repeat rate: 19%. Impulse / low-consideration.")

    p.h2("6. Competitive & Channel Notes")
    p.bullet("Competing tech brands are expanding outerwear lines (premium hoodies, fleece-lined zip-ups) and reporting sell-through above forecast.")
    p.bullet("Accessories are increasingly used as free giveaways at events, depressing willingness-to-pay for paid accessory SKUs.")
    p.bullet("Social-media \"outfit\" posts featuring branded outerwear drive measurable organic reach; accessories rarely feature as a hero item.")

    p.h2("7. Recommendation for Databricks Retail Corp.")
    p.callout([
        ("External-market recommendation: prioritize Outerwear for the Q4 promotion.", True),
        ("- Highest projected market growth (+12.1% next quarter).", False),
        ("- Strongest Q4 seasonality (demand index 142).", False),
        ("- Highest willingness-to-pay ($68) and category margin (52%).", False),
        ("- Highest repeat-purchase rate (41%), improving customer lifetime value.", False),
    ])
    p.para("Note: This is the EXTERNAL-market view. Confirm it against Databricks Retail Corp.'s own sales numbers, forecast, and marketing ROI (Labs 3-5) before finalizing the decision. Where internal and external signals agree, confidence is high; where they diverge, investigate before committing budget.", size=10)

    p.footer_note("NorthStar Retail Insights  |  This document is synthetic training material created for the Databricks \"Data Camp for Business Users\" labs. All figures are fictional and for instructional use only.")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "Databricks_Retail_Market_Research.pdf")
    p.build(out_path)
    print("Wrote", out_path)


if __name__ == "__main__":
    render()
