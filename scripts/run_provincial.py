"""
run_provincial.py — end to end for the real CIHI national workbook: produces
hip_provincial.json and knee_provincial.json, one entry per available year.

CIHI's table has no referral/waitlist field, so demand is derived from two
real, independent signals instead of faked as a copy of capacity:

    capacity = volume (surgeries completed) per 100k of the province's
               65+ population that year — a real, population-normalized
               throughput rate.
    demand   = year-over-year growth rate of that same 65+ population — a
               real demand-pressure signal independent of current volume.

The first CIHI year has no prior-year population baseline, so it's skipped
rather than assigned a fabricated growth rate (see population_growth() in
ingest_provincial.py). CIHI's "% meeting benchmark" metric is carried
through as pct_benchmark on each record as a secondary, real stress signal.

Usage:
    python run_provincial.py --xlsx path/to/cihi_workbook.xlsx --population path/to/pop.csv --out ../data
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from ingest_provincial import load_raw, clean, to_wide, PROCEDURES, load_population, population_growth
from compute import compute_year

ROOT = Path(__file__).resolve().parents[1]


def default_population_csv() -> str:
    matches = sorted((ROOT / "raw_data").glob("*Population*.csv"))
    if not matches:
        raise FileNotFoundError("No StatCan population CSV found in raw_data/ — pass --population explicitly")
    return str(matches[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", required=True)
    parser.add_argument("--population", default=None, help="StatCan 65+ population CSV (defaults to the file in raw_data/)")
    parser.add_argument("--out", default="../data")
    args = parser.parse_args()

    print(f"Loading {args.xlsx} ...")
    raw = load_raw(args.xlsx)
    cleaned = clean(raw)
    cleaned_regional = clean(raw, level="Regional")

    population_csv = args.population or default_population_csv()
    print(f"Loading population {population_csv} ...")
    pop_df = load_population(population_csv)
    growth_df = population_growth(pop_df)
    growth_lookup = growth_df.set_index(["province", "year"])["growth_pct"].to_dict()
    population_lookup = pop_df.set_index(["province", "year"])["population"].to_dict()

    all_years = sorted(y for y in cleaned["year"].dropna().unique() if 2020 <= y <= 2025)
    growth_years = sorted(growth_df["year"].unique())
    print(f"Years found in range 2020-2025: {all_years}")
    print(f"Years with a population-growth baseline: {growth_years}")
    skipped_years = sorted(set(all_years) - set(growth_years))
    if skipped_years:
        print(f"Skipping {skipped_years}: no prior-year population baseline to compute demand from")
    years = [y for y in all_years if y in growth_years]
    if not years:
        print("No years with both CIHI data and a population-growth baseline were found.")

    for procedure in PROCEDURES:
        key = "hip" if "Hip" in procedure and "Fracture" not in procedure else "knee"
        print(f"\nProcessing {procedure} ...")
        by_year = {}
        proc_df = cleaned[cleaned["Indicator"].astype(str).str.strip() == procedure]

        for year in years:
            wide = to_wide(proc_df, year)
            if wide.empty:
                print(f"  {year}: no data, skipping")
                continue
            records = []
            for _, row in wide.iterrows():
                if pd.isna(row["volume"]) or pd.isna(row["wait50"]) or pd.isna(row["wait90"]):
                    continue
                province = row["province"]
                pop_key = (province, year)
                if pop_key not in growth_lookup or pop_key not in population_lookup:
                    continue
                population = population_lookup[pop_key]
                growth_pct = growth_lookup[pop_key]
                pct_benchmark = row.get("pct_benchmark")
                records.append({
                    "name": province,
                    "capacity": float(row["volume"]) / population * 100_000,
                    "demand": float(growth_pct),
                    "wait50": float(row["wait50"]),
                    "wait90": float(row["wait90"]),
                    "volume": float(row["volume"]),
                    "population65Plus": population,
                    "pctBenchmark": None if pd.isna(pct_benchmark) else float(pct_benchmark),
                })
            if not records:
                print(f"  {year}: no usable rows after cleaning, skipping")
                continue
            title = f"CanRoute — Provincial Diagnostic — {procedure} — {year}"
            payload = compute_year(records, title)
            if payload is None:
                continue
            payload["meta"]["demand_is_placeholder"] = False
            payload["meta"]["dataSource"] = (
                "CIHI Wait Times for Priority Procedures in Canada — Data Tables, joined with "
                "StatCan Table 17-10-0005-01 (65+ population). Capacity = volume per 100k (65+); "
                "demand = year-over-year growth rate of the 65+ population."
            )
            by_year[str(int(year))] = payload
            print(f"  {year}: {payload['summary']['hospitalsShown']} provinces")

        out_path = f"{args.out}/{key}_provincial.json"
        with open(out_path, "w") as f:
            json.dump({"procedure": procedure, "years": by_year}, f, indent=2)
        print(f"Wrote {out_path}")

        # Regional drill-down: CIHI's health-region breakdown, one payload per
        # (year, province). No sub-provincial population data exists, so this
        # can't use the same per-capita capacity / population-growth demand
        # as the provincial view — capacity is raw volume and demand is the
        # benchmark-miss rate instead (both real CIHI signals, no fabrication).
        regional_by_year = {}
        proc_df_regional = cleaned_regional[cleaned_regional["Indicator"].astype(str).str.strip() == procedure]
        for year in all_years:
            wide = to_wide(proc_df_regional, year, by_region=True)
            if wide.empty:
                continue
            provinces_payload = {}
            for province, grp in wide.groupby("province"):
                records = []
                for _, row in grp.iterrows():
                    if pd.isna(row["volume"]) or pd.isna(row["wait50"]) or pd.isna(row["wait90"]) or pd.isna(row["pct_benchmark"]):
                        continue
                    records.append({
                        "name": row["region"],
                        "capacity": float(row["volume"]),
                        "demand": float(100 - row["pct_benchmark"]),
                        "wait50": float(row["wait50"]),
                        "wait90": float(row["wait90"]),
                        "volume": float(row["volume"]),
                        "pctBenchmark": float(row["pct_benchmark"]),
                    })
                if not records:
                    continue
                title = f"CanRoute — Regional Diagnostic — {procedure} — {province} — {year}"
                payload = compute_year(records, title)
                if payload is None:
                    continue
                payload["meta"]["demand_is_placeholder"] = False
                payload["meta"]["dataSource"] = (
                    "CIHI Wait Times for Priority Procedures in Canada — Data Tables (Regional level). "
                    "Capacity = raw surgical volume for the region (no sub-provincial population data "
                    "exists to normalize it per capita); demand = 100 - % meeting benchmark "
                    "(CIHI's own timeliness signal, real per region)."
                )
                provinces_payload[province] = payload
            if provinces_payload:
                regional_by_year[str(int(year))] = provinces_payload

        regional_out_path = f"{args.out}/{key}_regional.json"
        with open(regional_out_path, "w") as f:
            json.dump({"procedure": procedure, "years": regional_by_year}, f, indent=2)
        print(f"Wrote {regional_out_path}")


if __name__ == "__main__":
    sys.exit(main())
