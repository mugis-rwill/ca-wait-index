"""
make_pairs_doc.py -- a readable rendering of the TASK 3 results.

Same numbers as output/matched_pairs.xlsx, laid out to be read rather than
filtered. The rule is stated first, above any result, so a reader meets the
criterion before the numbers it selected.

Output: output/matched_pairs.html
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


def main():
    pairs = pd.read_csv(os.path.join(OUT, "matched_pairs.csv"))
    summary = pd.read_csv(os.path.join(OUT, "matched_pairs_summary.csv"))
    detail = pd.read_csv(os.path.join(OUT, "pair_year_detail.csv"))

    pairs["abbr_a"] = pairs.province_a.map(ABBR)
    pairs["abbr_b"] = pairs.province_b.map(ABBR)
    detail["abbr_a"] = detail.pair.str.split(" / ").str[0].map(ABBR)
    detail["abbr_b"] = detail.pair.str.split(" / ").str[1].map(ABBR)

    payload = {
        "pairs": json.loads(pairs.to_json(orient="records")),
        "summary": json.loads(summary.to_json(orient="records")),
        "detail": json.loads(detail.to_json(orient="records")),
        "meta": {
            "n_pair_years": int(len(pairs)),
            "n_pairs": int(summary.shape[0]),
            "possible": 540,
            "max_gap": float(pairs.p90_diff_a_minus_b.abs().max()),
            "min_gap": float(pairs.p90_diff_a_minus_b.abs().min()),
            "median_gap": float(pairs.p90_diff_a_minus_b.abs().median()),
        },
    }

    with open(os.path.join(HERE, "pairs_doc_template.html")) as fh:
        html = fh.read()
    html = html.replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    path = os.path.join(OUT, "matched_pairs.html")
    with open(path, "w") as fh:
        fh.write(html)
    print(f"pairs doc -> {path} ({len(html):,} bytes)")
    data_path = os.path.join(OUT, "pairs_doc_data.json")
    with open(data_path, "w") as fh:
        json.dump(payload, fh, indent=1)
    print(f"  data -> {data_path}")
    print(f"  {payload['meta']['n_pair_years']} pair-years, "
          f"{payload['meta']['n_pairs']} distinct pairs")


if __name__ == "__main__":
    main()
