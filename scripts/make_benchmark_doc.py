"""
make_benchmark_doc.py -- DRAFT. Wait distributions against the benchmark line.

The chart: provinces across the x-axis, wait in days up the y-axis, and one
horizontal benchmark line running across all of them. Each province-year is a
vertical segment spanning its median to its 90th percentile, cut by the
benchmark line and coloured on either side of it. Where a segment starts and
ends relative to that line is the whole point -- a province whose entire segment
sits below the line clears the benchmark for at least 90% of patients; one whose
segment starts above it misses for more than half.

THE BENCHMARK VALUE IS STATED BY CIHI AND THEN CHECKED AGAINST THE DATA. CIHI
gives it as 6 months -- 182 days -- for hip and knee replacement. The workbook
never carries the threshold; it publishes only "% meeting benchmark". But P50,
P90 and % meeting benchmark are three points on one cumulative distribution --
the percentiles answer "given a share, what wait?" and the benchmark column
answers the inverse, "given a wait, what share?". Interpolating log-linearly
between (P50, 0.50) and (P90, 0.90) recovers the threshold each province's own
three published numbers imply. Across the 52 province-years where the benchmark
share falls strictly between those two percentiles, the implied threshold has a
median of 186.7 days and a coefficient of variation of 4.8%, and four provinces
land between 182.3 and 184.7, which corroborates the stated 6 months.

Run the same model backwards and it rules out the alternative: predicting each
province's published "% meeting benchmark" from its own P50 and P90 reproduces
CIHI's figure within 5 points in 100 of 120 province-years at 182 days (median
error 1.6 points), and in 0 of 120 at 112 days (median error 22.2 points).

That recovery is a DIAGNOSTIC, not a published figure: it depends on an
interpolation assumption. It is reported here to justify where the line sits,
and the per-province implied values are shown so the assumption can be checked
rather than taken on trust.

THE RATIO. Two are computed, because "how many surgeries should be done by the
benchmark time" can be read two ways and the draft should not silently pick one:

  tail_ratio      P90 / benchmark -- how many times the benchmark the unlucky
                  tenth actually waits. Saskatchewan hip 2025 = 2.47x.
  benchmark_share CIHI's published "% meeting benchmark" -- the share actually
                  done inside the threshold, and its complement in cases, which
                  is the count of patients who were not.

VOLUME IS A SECOND PANEL, NOT A SECOND AXIS. Volume shares the chart's x-axis on
a strip directly beneath it, on its own zero-based scale. It is deliberately not
plotted against a right-hand y-axis: two vertical scales on one frame let the
author decide, by choosing the scales, whether the reader sees a relationship.
Here that would be worse than merely sloppy -- the finding this work rests on is
that volume barely predicts the tail (hip throughput against P90 correlates at
-0.26 in 2025), so a reader must not be nudged into eyeballing a correlation the
data does not support. Vertical alignment lets the two be compared honestly:
same provinces, same order, same columns, two independent scales that are each
labelled.

The strip toggles between raw case volume and cases per 100,000 aged 65+,
because raw volume mostly measures how big a province is -- Ontario does 85x
Prince Edward Island's caseload and has 81x its 65+ population.

Two files are written from one source, so the hosted page and the published
artifact can never drift apart:

    output/benchmark_view.html   artifact form -- no document skeleton, because
                                 the Artifact runtime supplies <html>/<head>/<body>
    index.html                   standalone form -- the same content wrapped in a
                                 real document for serving over HTTP

The standalone wrapper adds only what the artifact runtime would otherwise have
provided: doctype, charset, viewport, a colour-scheme declaration and a zeroed
body margin. Everything visual still comes from the page's own <style> block.

Output: output/benchmark_view.html, index.html
"""

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "output")

# Days. CIHI states the hip/knee benchmark as "6 months" on its Wait Times for
# Priority Procedures in Canada, 2025 page. The data workbook never carries the
# figure, so it is corroborated against the published percentiles below.
#
# NOT 112 DAYS. That is the CATARACT SURGERY benchmark, from the same CIHI page
# ("cataract surgeries (69%) within the recommended 112 days"). Each priority
# procedure has its own: 112 days cataract, 28 days radiation therapy, 48 hours
# hip fracture repair, 6 months hip and knee replacement. Predicting each
# province's published "% meeting benchmark" from its own P50/P90 reproduces
# CIHI's figure within 5 points in 100 of 120 province-years at 182 days, and in
# 0 of 120 at 112 -- so the published data rules 112 out for these two
# procedures on its own.
BENCHMARK = 182
BENCHMARK_SOURCE = (
    "CIHI, Wait Times for Priority Procedures in Canada, 2025 - stated as "
    "6 months for hip and knee replacement"
)

ABBR = {
    "British Columbia": "BC", "Alberta": "AB", "Saskatchewan": "SK",
    "Manitoba": "MB", "Ontario": "ON", "Quebec": "QC", "New Brunswick": "NB",
    "Nova Scotia": "NS", "Prince Edward Island": "PE",
    "Newfoundland and Labrador": "NL",
}


def implied_threshold(df):
    """
    The benchmark threshold each province-year's own three numbers imply.

    Only rows whose benchmark share sits strictly between the 50th and 90th
    percentiles can be interpolated -- outside that range the two known points
    do not bracket the answer and the result would be an extrapolation.
    """
    d = df[(df.pct_meeting_benchmark > 50) & (df.pct_meeting_benchmark < 90)].copy()
    p = d.pct_meeting_benchmark / 100
    d["implied"] = np.exp(
        np.log(d.p50_wait_days)
        + (p - 0.5) / 0.4 * (np.log(d.p90_wait_days) - np.log(d.p50_wait_days))
    )
    return d


FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%93%8F"
    "%3C/text%3E%3C/svg%3E"
)

DESCRIPTION = (
    "Hip and knee replacement wait times in ten Canadian provinces, 2020-2025, "
    "plotted against the 182-day benchmark. Source: CIHI Table 1."
)


def as_document(artifact_html):
    """
    Wrap the artifact body in a real HTML document for hosting.

    The Artifact runtime injects a head and body around the published file; a web
    server does not. Splitting at the end of the page's own <style> block puts
    the title, font link and stylesheet in <head> and everything else in <body>,
    without touching a single rule -- so the hosted page renders identically to
    the artifact rather than being a second implementation of it.
    """
    marker = "</style>"
    cut = artifact_html.index(marker) + len(marker)
    head, body = artifact_html[:cut], artifact_html[cut:]
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="description" content="{DESCRIPTION}">\n'
        f'<link rel="icon" href="{FAVICON}">\n'
        # the two theme blocks in the page's own CSS key off prefers-color-scheme,
        # so declaring both here lets form controls and scrollbars follow suit
        "<style>:root{color-scheme:light dark}html,body{margin:0}"
        "img{max-width:100%}[hidden]{display:none!important}</style>\n"
        f"{head.strip()}\n</head>\n<body>\n{body.strip()}\n</body>\n</html>\n"
    )


def main():
    t = pd.read_csv(os.path.join(OUT, "master_table.csv"))

    rows = []
    for r in t.itertuples():
        rows.append({
            "province": r.province, "abbr": ABBR[r.province],
            "procedure": r.procedure, "year": int(r.year),
            "p50": float(r.p50_wait_days), "p90": float(r.p90_wait_days),
            "volume": int(r.volume),
            "rate": float(r.procedures_per_100k_65plus),
            "bench_pct": round(float(r.pct_meeting_benchmark), 1),
            # the two candidate ratios -- see module docstring
            "tail_ratio": round(float(r.p90_wait_days) / BENCHMARK, 2),
            "p50_ratio": round(float(r.p50_wait_days) / BENCHMARK, 2),
            # the percentage turned into people: exact arithmetic, no modelling
            "missed_cases": int(round(r.volume * (100 - r.pct_meeting_benchmark) / 100)),
            "rows": r.cihi_source_rows,
        })

    imp = implied_threshold(t)
    by_prov = (imp.groupby("province").implied
               .agg(["count", "median"]).round(1).reset_index())
    by_prov["abbr"] = by_prov.province.map(ABBR)

    payload = {
        "rows": rows,
        "benchmark": BENCHMARK,
        "benchmark_source": BENCHMARK_SOURCE,
        "provinces": [{"name": p, "abbr": ABBR[p]} for p in sorted(ABBR)],
        "years": sorted(t.year.unique().tolist()),
        "implied": {
            "median": round(float(imp.implied.median()), 1),
            "cv": round(float(imp.implied.std() / imp.implied.mean()), 3),
            "n": int(len(imp)),
            "by_province": json.loads(by_prov.to_json(orient="records")),
        },
    }

    with open(os.path.join(HERE, "benchmark_template.html")) as fh:
        html = fh.read()
    html = html.replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    path = os.path.join(OUT, "benchmark_view.html")
    with open(path, "w") as fh:
        fh.write(html)

    index_path = os.path.join(ROOT, "index.html")
    with open(index_path, "w") as fh:
        fh.write(as_document(html))

    print(f"benchmark view -> {path} ({len(html):,} bytes)")
    print(f"site index     -> {index_path}")
    data_path = os.path.join(OUT, "benchmark_data.json")
    with open(data_path, "w") as fh:
        json.dump(payload, fh, indent=1)
    print(f"  data -> {data_path}")
    print(f"  {len(rows)} province-years; benchmark drawn at {BENCHMARK} days")
    print(f"  implied threshold: median {payload['implied']['median']}d, "
          f"CV {payload['implied']['cv']}, n={payload['implied']['n']}")


if __name__ == "__main__":
    main()
