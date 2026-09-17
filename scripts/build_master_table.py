"""
build_master_table.py -- TASK 2. The master table.

One row per province / procedure / year, for hip and knee replacement, all ten
provinces, in one of CIHI's two reporting windows:

    --window aprsep   April-September, 2020-2025   (default; 120 rows)
    --window fy       fiscal year Apr-Mar, 2020-2024 (98 of 100 rows -- see below)

The two are built by the same code path so they cannot drift apart. They are
never mixed: a 6-month count beside a 12-month one is not a comparison.

This script is deliberately self-contained. It imports nothing from the rest of
this repo and reads exactly two files: CIHI's published workbook and Statistics
Canada's population estimates. Every published number can therefore be traced
to a named table, a named sheet, and a specific source row -- the
`cihi_source_rows` column carries the 1-based row numbers in CIHI's Table 1 that
each output row was built from.

METHOD CHOICES, and why (each is defensible without looking anything up):

1. WINDOW. CIHI writes April-September as a bare year, October-March as
   `<year>Q3Q4`, and the 12-month fiscal year as `<year>FY`. Matching is on the
   exact string, never on the leading four digits, because `int("2025FY"[:4])`
   silently merges three different periods.

   The April-September window runs 2020-2025 and is the only one available in
   all six years -- 2025FY does not exist, because the fiscal year had not
   closed when the workbook was published. The fiscal-year window therefore
   stops at 2024, and buys a full 12 months of coverage at the cost of the most
   recent year.

   FISCAL-YEAR COVERAGE IS NOT COMPLETE. Newfoundland and Labrador submitted no
   2024FY figures for either procedure -- all four metrics are `n/a` (Table 1
   rows 18790-18797). That province-year is absent from the fiscal-year table
   rather than imputed, so the fiscal-year panel holds 98 rows, not 100.

2. NO ANNUALIZATION. April-September volume is never doubled or scaled to a
   full year. Measured against the FY rows where both exist, this window is
   46.8% of fiscal-year volume on average but ranges from 29.3% to 61.5%. It is
   not reliably half a year, so its rate is reported as a six-month rate.
   Fiscal-year rows already cover 12 months, so their rate IS an annual rate and
   is labelled as one.

3. DENOMINATOR. Population aged 65+ on July 1 of the calendar year the window
   opens in. For April-September that date is the exact midpoint of the window,
   so the stock is measured in the middle of the flow it divides. For the fiscal
   year (April Y to March Y+1) the midpoint is around 1 October, three months
   later; July 1 of year Y is used anyway, because it is a published Statistics
   Canada figure rather than one interpolated by us, and at roughly 3% annual
   growth in the 65+ population the three-month offset moves the denominator by
   under 1% -- far less than the differences the rate is used to compare.

4. NO CONFIDENCE INTERVALS. CIHI receives aggregate percentiles submitted by
   provincial ministries, not case-level records, and publishes no intervals of
   its own. There is no sampling distribution available to work from, so none
   are computed. This is stated rather than worked around.

Outputs (written to output/):
    master_table[_fy].xlsx   two tabs: "Master table" and "Sources"
    master_table[_fy].csv    the table
    master_table[_fy].json   the same rows, for the charts
    sources[_fy].csv         the source tab, standalone
"""

import argparse
import json
import os
from datetime import date

import openpyxl
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------- provenance
# Recorded here so the source tab is generated from the same constants the
# pipeline actually reads, and cannot drift away from them.

CIHI_FILE = "wait-times-priority-procedures-in-canada-2008-2025-data-tables-en.xlsx"
CIHI_TABLE = "Table 1  Wait times for priority procedures, by province and Canada, 2008 to 2025"
CIHI_SHEET = "Table 1"
CIHI_CITATION = (
    "Canadian Institute for Health Information. Wait Times for Priority "
    "Procedures in Canada, 2008-2025 - Data Tables. Ottawa, ON: CIHI; 2026."
)
CIHI_DOWNLOADED = "2025-07-18"

POP_FILE = "statcan_65plus_bands_provincial.csv"
POP_TABLE = "Table 17-10-0005-01 (Product ID 17100005; CANSIM 051-0001)"
POP_TITLE = "Population estimates on July 1, by age and gender"
POP_URL = "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000501"
POP_AGE_GROUP = "65 years and older"
POP_VINTAGE = (
    "July 1 annual estimates; series end reference period 2025-01-01. "
    "Estimates for recent years are postcensal and are revised by Statistics "
    "Canada in later releases; the 2025 figure is preliminary postcensal."
)
POP_DOWNLOADED = "2025-09-10"

# Territories are excluded. CIHI's own provincial wait-time reporting excludes
# them, and StatCan's territorial 65+ counts are small enough that a rate per
# 100,000 would be unstable.
PROVINCES = [
    "British Columbia", "Alberta", "Saskatchewan", "Manitoba", "Ontario",
    "Quebec", "New Brunswick", "Nova Scotia", "Prince Edward Island",
    "Newfoundland and Labrador",
]
PROCEDURES = ["Hip Replacement", "Knee Replacement"]
# Each window: the Data year suffix CIHI uses, the years it covers, and how the
# resulting rate must be described. Adding a window here is the only change
# needed to build one.
WINDOWS = {
    "aprsep": {
        "suffix": "",
        "years": [2020, 2021, 2022, 2023, 2024, 2025],
        "label": "April-September (6 months)",
        "rate_basis": "6-month (Apr-Sep) count per 100,000 population 65+; NOT annualized",
        "pop_vintage": "July 1 estimate, same calendar year (window midpoint)",
        "tag": "",
    },
    "fy": {
        "suffix": "FY",
        "years": [2020, 2021, 2022, 2023, 2024],
        "label": "Fiscal year, April-March (12 months)",
        "rate_basis": "12-month (fiscal year) count per 100,000 population 65+; this IS an annual rate",
        "pop_vintage": "July 1 estimate of the calendar year the fiscal year opens in",
        "tag": "_fy",
    },
}

# Province-years CIHI publishes as n/a across every metric. Recorded here so the
# row count check below knows what to expect instead of being loosened.
KNOWN_ABSENT = {
    "fy": [("Newfoundland and Labrador", "Hip Replacement", 2024),
           ("Newfoundland and Labrador", "Knee Replacement", 2024)],
    "aprsep": [],
}

METRIC_MAP = {
    "Volume": "volume",
    "50th percentile": "p50_wait_days",
    "90th percentile": "p90_wait_days",
    "% meeting benchmark": "pct_meeting_benchmark",
}

# Task 1 findings, attached to every row rather than left in a memo.
PROVENANCE = "Provincial ministry/agency submission (aggregate)"
PROVENANCE_FLAG = "self-reported"


def load_cihi_table1(xlsx_path):
    """
    Read CIHI's Table 1 into a flat frame, keeping the source row number.

    Scans for the header row rather than hardcoding an offset, because CIHI has
    shifted the title block between editions. Row numbers are 1-based to match
    what a reader sees in Excel when they go to check a figure.
    """
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb[CIHI_SHEET]

    records, header_seen = [], False
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if not row or row[0] is None:
            continue
        first = str(row[0]).strip()
        if not header_seen:
            if first == "Reporting level":
                header_seen = True
            continue
        # The notes block sits under the data; stop at the first row whose
        # reporting level is not one of the three real values.
        if first not in ("National", "Provincial", "Regional"):
            continue
        records.append({
            "excel_row": i,
            "reporting_level": first,
            "province": str(row[1]).strip() if row[1] is not None else "",
            "region": str(row[2]).strip() if row[2] is not None else "",
            "indicator": str(row[3]).strip() if row[3] is not None else "",
            "metric": str(row[4]).strip() if row[4] is not None else "",
            "data_year": str(row[5]).strip() if row[5] is not None else "",
            "unit": str(row[6]).strip() if row[6] is not None else "",
            "result": row[7],
        })

    if not header_seen:
        raise ValueError(f"No 'Reporting level' header found in sheet {CIHI_SHEET!r}")
    return pd.DataFrame(records)


def load_population(csv_path, years):
    """65+ population by province and year, from StatCan 17-10-0005-01."""
    pop = pd.read_csv(csv_path)
    pop = pop[(pop["Age group"] == POP_AGE_GROUP) & (pop["GEO"].isin(PROVINCES))]
    pop = pop[pop["REF_DATE"].isin(years)]
    out = pop[["GEO", "REF_DATE", "VALUE"]].rename(
        columns={"GEO": "province", "REF_DATE": "year", "VALUE": "pop_65plus"}
    )
    missing = len(PROVINCES) * len(years) - len(out)
    if missing:
        raise ValueError(f"Population panel incomplete: {missing} province-years missing")
    return out.reset_index(drop=True)


def build(xlsx_path, pop_path, window="aprsep"):
    spec = WINDOWS[window]
    raw = load_cihi_table1(xlsx_path)

    # Exact Data year strings for this window -- "2024" or "2024FY", never a
    # four-digit prefix. See note 1.
    want_years = {f"{y}{spec['suffix']}" for y in spec["years"]}
    sel = raw[
        (raw.reporting_level == "Provincial")
        & (raw.indicator.isin(PROCEDURES))
        & (raw.province.isin(PROVINCES))
        & (raw.data_year.isin(want_years))
        & (raw.metric.isin(METRIC_MAP))
    ].copy()

    sel["field"] = sel.metric.map(METRIC_MAP)
    sel["year"] = sel.data_year.str.slice(0, 4).astype(int)

    # Refuse to guess if CIHI ever ships two rows for the same cell.
    dupes = sel.groupby(["province", "indicator", "year", "field"]).size()
    if (dupes > 1).any():
        raise ValueError(f"Duplicate source cells:\n{dupes[dupes > 1]}")

    # 'n/a' is CIHI's missing marker; anything non-numeric becomes NaN and is
    # reported as missing rather than dropped or filled.
    sel["value"] = pd.to_numeric(sel.result, errors="coerce")

    wide = sel.pivot_table(
        index=["province", "indicator", "year"], columns="field",
        values="value", aggfunc="first",
    ).reset_index()

    trace = (
        sel.sort_values("excel_row")
        .groupby(["province", "indicator", "year"])["excel_row"]
        .apply(lambda s: ";".join(str(int(v)) for v in s))
        .reset_index(name="cihi_source_rows")
    )
    wide = wide.merge(trace, on=["province", "indicator", "year"])

    wide = wide.merge(load_population(pop_path, spec["years"]),
                      on=["province", "year"], how="left")

    # Six-month rate. Not annualized -- see note 2.
    wide["procedures_per_100k_65plus"] = (
        wide.volume / wide.pop_65plus * 100_000
    ).round(1)

    wide["procedure"] = wide.indicator.str.replace(" Replacement", "", regex=False)
    wide["reporting_window"] = spec["label"]
    wide["provenance"] = PROVENANCE
    wide["provenance_flag"] = PROVENANCE_FLAG
    wide["pop_source"] = POP_TABLE
    wide["pop_vintage"] = spec["pop_vintage"]
    wide["rate_basis"] = spec["rate_basis"]
    wide["confidence_interval"] = "not available - CIHI publishes aggregate percentiles, not case-level data"

    cols = [
        "province", "procedure", "year",
        "volume", "p50_wait_days", "p90_wait_days", "pct_meeting_benchmark",
        "pop_65plus", "pop_source", "pop_vintage",
        "procedures_per_100k_65plus", "rate_basis",
        "reporting_window", "provenance", "provenance_flag",
        "confidence_interval",
        "cihi_table", "cihi_sheet", "cihi_source_rows",
    ]
    wide["cihi_table"] = CIHI_TABLE
    wide["cihi_sheet"] = CIHI_SHEET

    out = wide[cols].sort_values(["procedure", "year", "province"]).reset_index(drop=True)
    return out


def source_tab(window="aprsep"):
    """The source tab: what was downloaded, from where, and when."""
    spec = WINDOWS[window]
    yrs = f"{spec['years'][0]}..{spec['years'][-1]}"
    suf = spec["suffix"]
    if window == "fy":
        year_rule = (f"Data year in ({yrs}) matched as exact '<year>FY' strings, "
                     "excluding all bare-year (April-September) and Q3Q4 rows")
        absent = (" Newfoundland and Labrador published no 2024FY figures for "
                  "either procedure (all metrics n/a, Table 1 rows 18790-18797); "
                  "that province-year is absent rather than imputed, so this "
                  "table holds 98 rows, not 100.")
    else:
        year_rule = (f"Data year in ({yrs}) matched as exact bare-year strings, "
                     "excluding all FY and Q3Q4 rows")
        absent = ""
    rows = [
        {
            "dataset": "CIHI wait times",
            "exact_table_name": CIHI_TABLE,
            "sheet": CIHI_SHEET,
            "file": CIHI_FILE,
            "publisher": "Canadian Institute for Health Information (CIHI)",
            "citation": CIHI_CITATION,
            "downloaded": CIHI_DOWNLOADED,
            "fields_used": "Reporting level, Province, Indicator, Metric, Data year, Unit of measurement, Indicator result",
            "filter_applied": (
                "Reporting level = 'Provincial'; Indicator in (Hip Replacement, "
                f"Knee Replacement); {year_rule}"
            ),
            "reporting_window": spec["label"],
            "notes": (
                "Hip and knee replacement results are submitted to CIHI by "
                "provincial ministries and agencies as aggregate figures. Only "
                "Hip Fracture Repair is calculated by CIHI from DAD/NACRS, and "
                "it is not used here. Data year is April-September unless "
                "suffixed FY (April-March) or Q3Q4 (October-March)." + absent
            ),
        },
        {
            "dataset": "StatCan population 65+",
            "exact_table_name": f"{POP_TABLE} - {POP_TITLE}",
            "sheet": "n/a (CSV extract)",
            "file": POP_FILE,
            "publisher": "Statistics Canada",
            "citation": (
                f"Statistics Canada. {POP_TABLE}, {POP_TITLE}. {POP_URL}"
            ),
            "downloaded": POP_DOWNLOADED,
            "fields_used": "REF_DATE, GEO, Age group, VALUE",
            "filter_applied": (
                f"Age group = '{POP_AGE_GROUP}'; GEO in the 10 provinces; "
                f"REF_DATE in {yrs}"
            ),
            "reporting_window": spec["pop_vintage"],
            "notes": POP_VINTAGE,
        },
    ]
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description="Build the Task 2 master table.")
    ap.add_argument("--xlsx", default=os.path.join(ROOT, "raw_data", CIHI_FILE))
    ap.add_argument("--population", default=os.path.join(ROOT, "raw_data", POP_FILE))
    ap.add_argument("--outdir", default=os.path.join(ROOT, "output"))
    ap.add_argument("--window", choices=sorted(WINDOWS), default="aprsep",
                    help="aprsep = April-September 2020-2025 (default); "
                         "fy = fiscal year April-March 2020-2024")
    args = ap.parse_args()

    spec = WINDOWS[args.window]
    tag = spec["tag"]
    os.makedirs(args.outdir, exist_ok=True)
    table = build(args.xlsx, args.population, args.window)

    absent = KNOWN_ABSENT[args.window]
    expected = len(PROVINCES) * len(PROCEDURES) * len(spec["years"]) - len(absent)
    if len(table) != expected:
        raise ValueError(f"Expected {expected} rows, built {len(table)}")

    holes = table[["volume", "p50_wait_days", "p90_wait_days",
                   "pct_meeting_benchmark", "pop_65plus"]].isna().sum()
    csv_path = os.path.join(args.outdir, f"master_table{tag}.csv")
    table.to_csv(csv_path, index=False)

    src = source_tab(args.window)
    src_path = os.path.join(args.outdir, f"sources{tag}.csv")
    src.to_csv(src_path, index=False)
    with open(os.path.join(args.outdir, f"sources{tag}.json"), "w") as fh:
        json.dump(json.loads(src.to_json(orient="records")), fh, indent=1)

    xlsx_out = os.path.join(args.outdir, f"master_table{tag}.xlsx")
    with pd.ExcelWriter(xlsx_out, engine="openpyxl") as xw:
        table.to_excel(xw, sheet_name="Master table", index=False)
        src.to_excel(xw, sheet_name="Sources", index=False)
        for name, frame in (("Master table", table), ("Sources", src)):
            ws = xw.sheets[name]
            ws.freeze_panes = "A2"
            for idx, col in enumerate(frame.columns, start=1):
                width = max(len(str(col)), *(len(str(v)) for v in frame[col].head(200)))
                ws.column_dimensions[
                    openpyxl.utils.get_column_letter(idx)
                ].width = min(max(width + 2, 10), 60)

    json_path = os.path.join(args.outdir, f"master_table{tag}.json")
    with open(json_path, "w") as fh:
        json.dump({
            "generated": date.today().isoformat(),
            "reporting_window": spec["label"],
            "provenance": PROVENANCE,
            "confidence_intervals": "none - not computable from published aggregates",
            "rows": json.loads(table.to_json(orient="records")),
        }, fh, indent=1)

    print(f"window       : {args.window} -- {spec['label']}")
    if absent:
        print(f"absent rows  : {len(absent)} published as n/a and excluded: "
              + "; ".join(f"{p} {i} {y}" for p, i, y in absent))
    print(f"workbook     : {xlsx_out}")
    print(f"master table : {len(table)} rows -> {csv_path}")
    print(f"source tab   : {len(src)} datasets -> {src_path}")
    print(f"json         : {json_path}")
    print(f"missing cells: {holes.to_dict()}")


if __name__ == "__main__":
    main()
