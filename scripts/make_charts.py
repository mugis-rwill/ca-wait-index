"""
make_charts.py -- TASK 4. The charts.

Three chart specs, as briefed:
  1. P90 by province, 2025, hip and knee, ordered   (the headline)
  2. Six-year P90 trend, all provinces
  3. One chart per surviving pair, P50 and P90 side by side

No chart shows a residual, a fitted value, or a quadrant. Every chart is a
direct plot of a published CIHI figure.

Chart-form choices, and why:

- CHART 1 is an ordered horizontal bar chart, one panel per procedure. Ordering
  is the point of the chart, so the bars are sorted by the value they encode.
  Hip and knee get separate panels because their orderings differ -- a reader
  must not infer a single national ranking.

- CHART 2 is small multiples, not ten lines on one axis. Ten series exceeds any
  categorical palette that stays colourblind-safe, and ten lines on one axis is
  unreadable regardless. Each province gets its own panel on a SHARED y-scale so
  panels are comparable, with the national range ghosted behind for context.

- CHART 3 is a dumbbell: a dot at P50, a dot at P90, joined by a line. The
  LENGTH OF THAT LINE IS THE TAIL -- the distance between the typical patient
  and the unlucky one. That is the entire angle of this work, so it is encoded
  as length rather than left to the reader to subtract.

This script only reshapes already-published numbers into a drawing payload. It
computes no statistics.

Output: output/charts.html
"""

import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "output")

ABBR = {
    "British Columbia": "BC", "Alberta": "AB", "Saskatchewan": "SK",
    "Manitoba": "MB", "Ontario": "ON", "Quebec": "QC",
    "New Brunswick": "NB", "Nova Scotia": "NS",
    "Prince Edward Island": "PE", "Newfoundland and Labrador": "NL",
}


def build_payload():
    t = pd.read_csv(os.path.join(OUT, "master_table.csv"))
    pairs = pd.read_csv(os.path.join(OUT, "matched_pairs.csv"))

    # ---- Chart 1: 2025 P90, ordered, per procedure
    headline = {}
    for proc in ("Hip", "Knee"):
        d = t[(t.procedure == proc) & (t.year == 2025)].sort_values(
            "p90_wait_days", ascending=False)
        headline[proc] = [{
            "province": r.province, "abbr": ABBR[r.province],
            "p90": r.p90_wait_days, "p50": r.p50_wait_days,
            "volume": int(r.volume), "benchmark": round(r.pct_meeting_benchmark, 1),
            "rows": r.cihi_source_rows,
        } for r in d.itertuples()]

    # ---- Chart 2: six-year P90 trend, per province, both procedures
    trend = []
    for prov in sorted(t.province.unique()):
        entry = {"province": prov, "abbr": ABBR[prov], "series": {}}
        for proc in ("Hip", "Knee"):
            d = t[(t.province == prov) & (t.procedure == proc)].sort_values("year")
            entry["series"][proc] = [
                {"year": int(r.year), "p90": r.p90_wait_days,
                 "p50": r.p50_wait_days, "volume": int(r.volume)}
                for r in d.itertuples()
            ]
        trend.append(entry)
    # Order panels by 2025 hip P90 so the panel grid reads worst-to-best,
    # matching chart 1 rather than fighting it.
    order = {r["province"]: i for i, r in enumerate(headline["Hip"])}
    trend.sort(key=lambda e: order.get(e["province"], 99))

    # ---- Chart 3: one per surviving pair
    pair_charts = []
    for (proc, pair), g in pairs.groupby(["procedure", "pair"]):
        a, b = pair.split(" / ")
        years = []
        for r in g.sort_values("year").itertuples():
            years.append({
                "year": int(r.year),
                "a": {"prov": a, "abbr": ABBR[a], "p50": r.p50_a, "p90": r.p90_a,
                      "volume": r.volume_a, "benchmark": r.pct_benchmark_a},
                "b": {"prov": b, "abbr": ABBR[b], "p50": r.p50_b, "p90": r.p90_b,
                      "volume": r.volume_b, "benchmark": r.pct_benchmark_b},
                "volume_gap_pct": r.volume_gap_pct,
                "p90_diff": r.p90_diff_a_minus_b,
                "direction": r.direction_p90,
            })
        pair_charts.append({
            "pair": pair, "procedure": proc,
            "province_a": a, "province_b": b,
            "abbr_a": ABBR[a], "abbr_b": ABBR[b],
            "years": years, "n_years": len(years),
        })
    # Sort by procedure then pair name -- NOT by gap size. Ordering charts by
    # effect size is how a reader gets led to the striking one.
    pair_charts.sort(key=lambda c: (c["procedure"], c["pair"]))

    return {
        "headline": headline,
        "trend": trend,
        "pairs": pair_charts,
        "meta": {
            "window": "April–September",
            "years": [2020, 2025],
            "n_pairs": len(pair_charts),
            "n_pair_years": len(pairs),
            "p90_max": float(t.p90_wait_days.max()),
        },
    }


def main():
    payload = build_payload()
    tpl_path = os.path.join(HERE, "charts_template.html")
    with open(tpl_path) as fh:
        html = fh.read()
    html = html.replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    out_path = os.path.join(OUT, "charts.html")
    with open(out_path, "w") as fh:
        fh.write(html)
    data_path = os.path.join(OUT, "charts_data.json")
    with open(data_path, "w") as fh:
        json.dump(payload, fh, indent=1)
    print(f"charts -> {out_path}  ({len(html):,} bytes)")
    print(f"  data -> {data_path}")
    print(f"  headline: {len(payload['headline']['Hip'])} provinces x 2 procedures")
    print(f"  trend   : {len(payload['trend'])} province panels")
    print(f"  pairs   : {len(payload['pairs'])} pair charts, "
          f"{payload['meta']['n_pair_years']} pair-years")


if __name__ == "__main__":
    main()
