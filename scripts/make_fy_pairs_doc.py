"""
make_fy_pairs_doc.py -- charts for the fiscal-year matched pairs (Task 3, redone
on 12-month data).

One chart per surviving pair. Each chart puts four measures side by side for the
two provinces:

    volume | procedures per 100,000 aged 65+ | P50 days | P90 days

Why four panels and not one. The four measures have different units, so they
cannot share an axis -- a single scale carrying cases and days at once would be
a dual-axis chart, which is the most reliable way to mislead a reader. Each
measure gets its own panel and its own zero-based scale, and each panel is
captioned twice: the percentage difference between the two provinces, computed
the same way the matching rule computes it (|a-b| / max(a,b)), AND the same
difference in that measure's own units -- cases, cases per 100,000, or days.

Both are given because neither is sufficient alone. A percentage is what makes
measures with different units comparable to each other, but it hides scale: 13%
apart on a 90th percentile is 48 days of someone's life, and 13% apart on a
median is 26. Days are what a payer's cost is denominated in, so days are
printed next to every percentage rather than left for the reader to work out.

What the layout is built to show: the volume panel is the matching rule made
visible -- the two bars are the same length, by construction. Every panel to its
right is what varies once volume is held still. The per-100k panel is there
because equal case counts do not mean equal throughput: Prince Edward Island and
Newfoundland report almost the same number of knee replacements in 2020FY, but
PEI's 65+ population is a quarter the size, so its rate is 3.8x higher.

Output: output/matched_pairs_fy.html
"""

import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "output")

ABBR = {
    "British Columbia": "BC", "Alberta": "AB", "Saskatchewan": "SK",
    "Manitoba": "MB", "Ontario": "ON", "Quebec": "QC", "New Brunswick": "NB",
    "Nova Scotia": "NS", "Prince Edward Island": "PE",
    "Newfoundland and Labrador": "NL",
}


def pct_apart(a, b):
    """The rule's own difference measure, reused for every panel."""
    hi = max(abs(a), abs(b))
    return round(abs(a - b) / hi * 100, 1) if hi else 0.0


def main():
    fy = pd.read_csv(os.path.join(OUT, "master_table_fy.csv"))
    pairs = pd.read_csv(os.path.join(OUT, "matched_pairs_fy.csv"))
    aprsep = pd.read_csv(os.path.join(OUT, "matched_pairs.csv"))

    key = fy.set_index(["province", "procedure", "year"])
    charts = []
    for r in pairs.itertuples():
        a = key.loc[(r.province_a, r.procedure, r.year)]
        b = key.loc[(r.province_b, r.procedure, r.year)]
        measures = [
            {"label": "Volume", "unit": "cases", "diff_unit": "cases",
             "a": float(a.volume), "b": float(b.volume)},
            {"label": "Per 100k aged 65+", "unit": "cases per 100,000",
             "diff_unit": "per 100k",
             "a": float(a.procedures_per_100k_65plus),
             "b": float(b.procedures_per_100k_65plus)},
            {"label": "Median wait", "unit": "days", "diff_unit": "days",
             "a": float(a.p50_wait_days), "b": float(b.p50_wait_days)},
            {"label": "90th percentile", "unit": "days", "diff_unit": "days",
             "a": float(a.p90_wait_days), "b": float(b.p90_wait_days)},
        ]
        for m in measures:
            m["pct"] = pct_apart(m["a"], m["b"])
            # The gap in the measure's own units, printed beside the percentage.
            m["absdiff"] = round(abs(m["a"] - m["b"]), 1)
            lo = min(m["a"], m["b"])
            m["ratio"] = round(max(m["a"], m["b"]) / lo, 2) if lo else None
        charts.append({
            "pair": r.pair, "procedure": r.procedure, "year": int(r.year),
            "a": {"prov": r.province_a, "abbr": ABBR[r.province_a],
                  "pop": int(a.pop_65plus), "bench": round(float(a.pct_meeting_benchmark), 1)},
            "b": {"prov": r.province_b, "abbr": ABBR[r.province_b],
                  "pop": int(b.pop_65plus), "bench": round(float(b.pct_meeting_benchmark), 1)},
            "measures": measures,
            "direction": r.direction_p90,
            "p90_gap": abs(float(r.p90_diff_a_minus_b)),
            "p50_gap": abs(float(r.p50_diff_a_minus_b)),
            "rate_ratio": round(
                max(a.procedures_per_100k_65plus, b.procedures_per_100k_65plus)
                / min(a.procedures_per_100k_65plus, b.procedures_per_100k_65plus), 2),
            "rows_a": a.cihi_source_rows, "rows_b": b.cihi_source_rows,
        })
    # Ordered by procedure then pair name. Not by any gap.
    charts.sort(key=lambda c: (c["procedure"], c["pair"]))

    ak = set(zip(aprsep.procedure, aprsep.pair, aprsep.year))
    fk = set(zip(pairs.procedure, pairs.pair, pairs.year))
    payload = {
        "charts": charts,
        "table": json.loads(pairs.to_json(orient="records")),
        "meta": {
            "n": len(pairs), "possible": 450, "n_years": 5,
            "both": sorted(f"{p} {n} {y}" for p, n, y in (ak & fk)),
            "fy_only": sorted(f"{p} {n} {y}" for p, n, y in (fk - ak)),
            "n_aprsep": len(ak),
            "min_gap": float(pairs.p90_diff_a_minus_b.abs().min()),
            "max_gap": float(pairs.p90_diff_a_minus_b.abs().max()),
            "median_gap": float(pairs.p90_diff_a_minus_b.abs().median()),
        },
    }

    with open(os.path.join(HERE, "fy_pairs_template.html")) as fh:
        html = fh.read()
    html = html.replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    path = os.path.join(OUT, "matched_pairs_fy.html")
    with open(path, "w") as fh:
        fh.write(html)
    print(f"fy pairs doc -> {path} ({len(html):,} bytes)")
    data_path = os.path.join(OUT, "fy_pairs_data.json")
    with open(data_path, "w") as fh:
        json.dump(payload, fh, indent=1)
    print(f"  data -> {data_path}")
    print(f"  {len(charts)} pair charts")


if __name__ == "__main__":
    main()
