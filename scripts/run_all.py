"""
run_all.py — end to end: read the raw BC workbook, produce hip.json and
knee.json, each containing every available fiscal year.

Usage:
    python run_all.py --xlsx path/to/workbook.xlsx --out ../data
"""

import argparse
import json
import sys

from ingest_bc import load_raw, clean, to_yearly, FISCAL_TO_YEAR
from compute import compute_year

PROCEDURES = {
    "hip": "Hip Replacement",
    "knee": "Knee Replacement",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", required=True, help="Path to the BC surgical wait times workbook")
    parser.add_argument("--out", default="../data", help="Output directory for hip.json / knee.json")
    args = parser.parse_args()

    print(f"Loading {args.xlsx} ...")
    raw = load_raw(args.xlsx)

    years = sorted(set(FISCAL_TO_YEAR.values()))

    for key, procedure_name in PROCEDURES.items():
        print(f"\nProcessing {procedure_name} ...")
        cleaned = clean(raw, procedure_name)
        by_year = {}
        for year in years:
            yearly = to_yearly(cleaned, year)
            if yearly.empty:
                print(f"  {year}: no data, skipping")
                continue
            records = yearly.to_dict(orient="records")
            title = f"CanRoute \u2014 Hospital Diagnostic \u2014 {procedure_name} \u2014 FY{year}/{str(year+1)[-2:]}"
            payload = compute_year(records, title)
            if payload is None:
                print(f"  {year}: no usable rows after cleaning, skipping")
                continue
            by_year[str(year)] = payload
            print(f"  {year}: {payload['summary']['hospitalsShown']} hospitals")

        out_path = f"{args.out}/{key}.json"
        with open(out_path, "w") as f:
            json.dump({"procedure": procedure_name, "years": by_year}, f, indent=2)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    sys.exit(main())
