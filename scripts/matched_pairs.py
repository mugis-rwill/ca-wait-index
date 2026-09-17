"""
matched_pairs.py -- TASK 3. The matching rule, applied exactly as written.

THE RULE, fixed before the results were seen:

  (1) Both provinces' volume within 5% of each other
  (2) Same procedure
  (3) Same year
  (4) Same reporting window
  (5) Same provenance type

TIE-BREAK ON (1). "Within 5% of each other" does not name a denominator, so one
is fixed here, in advance, and applied to every pair identically:

      | volume_a - volume_b |  /  max(volume_a, volume_b)  <=  0.05

max() is the strictest of the three candidate denominators (max < mean < min)
and is symmetric, so neither province is treated as the reference against which
the other is measured. The alternatives are reported at the bottom as a
sensitivity check ONLY -- the surviving set is the max() set, and it is not
revised after inspection.

ON (4) AND (5), STATED BEFORE THE RUN. Every hip/knee figure in this dataset is
April-September and every one is a provincial ministry submission (see Task 1).
Both clauses are therefore satisfied by all 45 province pairs and exclude none.
They are enforced in code anyway -- as equality tests on real columns, not as
assumptions -- so that they bite automatically if an FY row or a CIHI-calculated
indicator is ever added to the input.

NO POST-HOC FILTERING. Every pair the rule produces is reported, including
pairs whose wait-time gap is small or zero. The output is not sorted by gap size
and nothing is dropped for being uninteresting. That is the point of the task:
a rule that only ever surfaces the striking pair is not a rule.

A NOTE ON "EACH OF THE SIX YEARS". The task asks for the direction of the gap
in each of the six years. No pair clears the rule in all six -- volumes that
match in one year routinely diverge in the next -- so a second file,
pair_year_detail.csv, carries all six years for every surviving pair with a
`survives_rule` flag on each row. Rows where that flag is False did NOT pass the
volume test and must not be quoted as matched comparisons; they are there so the
direction of the gap can be read across the full window without implying the
rule was met.

Output: output/matched_pairs.xlsx  -- four tabs: The rule, Surviving pairs,
        Pair summary, Six-year detail
        output/matched_pairs.csv, output/matched_pairs_summary.csv,
        output/pair_year_detail.csv, output/matched_pairs.json
"""

import argparse
import itertools
import json
import os

import openpyxl
import openpyxl.styles
import openpyxl.utils
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

VOLUME_TOLERANCE = 0.05
DENOMINATOR = "max"          # fixed in advance; see module docstring


def volume_gap(a, b, denom=DENOMINATOR):
    """Relative volume difference between two provinces, symmetric in a and b."""
    hi, lo = max(a, b), min(a, b)
    base = {"max": hi, "min": lo, "mean": (a + b) / 2}[denom]
    return abs(a - b) / base


def find_pairs(df, denom=DENOMINATOR, tol=VOLUME_TOLERANCE):
    """
    Apply the rule to every province pair, in every procedure-year.

    Returns one row per surviving pair per year. Province order within a pair is
    alphabetical, so 'direction of the gap' is always read the same way and
    cannot flip between years by accident.
    """
    out = []
    for (proc, year), block in df.groupby(["procedure", "year"]):
        block = block.set_index("province")
        for a, b in itertools.combinations(sorted(block.index), 2):
            ra, rb = block.loc[a], block.loc[b]

            # (4) and (5): enforced, not assumed.
            if ra.reporting_window != rb.reporting_window:
                continue
            if ra.provenance_flag != rb.provenance_flag:
                continue

            # (1): the volume test.
            gap = volume_gap(ra.volume, rb.volume, denom)
            if gap > tol:
                continue

            p90_diff = ra.p90_wait_days - rb.p90_wait_days
            p50_diff = ra.p50_wait_days - rb.p50_wait_days
            if p90_diff > 0:
                direction = f"{a} slower"
            elif p90_diff < 0:
                direction = f"{b} slower"
            else:
                direction = "no gap"

            out.append({
                "pair": f"{a} / {b}",
                "procedure": proc,
                "year": year,
                "province_a": a,
                "province_b": b,
                "volume_a": int(ra.volume),
                "volume_b": int(rb.volume),
                "volume_gap_pct": round(gap * 100, 2),
                "p50_a": ra.p50_wait_days,
                "p50_b": rb.p50_wait_days,
                "p50_diff_a_minus_b": round(p50_diff, 1),
                "p90_a": ra.p90_wait_days,
                "p90_b": rb.p90_wait_days,
                "p90_diff_a_minus_b": round(p90_diff, 1),
                "pct_benchmark_a": round(ra.pct_meeting_benchmark, 1),
                "pct_benchmark_b": round(rb.pct_meeting_benchmark, 1),
                "pct_benchmark_diff_a_minus_b": round(
                    ra.pct_meeting_benchmark - rb.pct_meeting_benchmark, 1),
                "direction_p90": direction,
                "reporting_window": ra.reporting_window,
                "provenance_flag": ra.provenance_flag,
            })
    return pd.DataFrame(out)


def pair_year_detail(df, pairs, denom=DENOMINATOR, tol=VOLUME_TOLERANCE):
    """
    For every pair that survives at least once, the full six-year picture.

    `survives_rule` marks the years that actually passed the volume test. The
    other years are context only -- they are reported so the direction of the
    gap can be read across the window, and are flagged so they cannot be
    mistaken for matched comparisons.
    """
    out = []
    for (proc, pair), _ in pairs.groupby(["procedure", "pair"]):
        a, b = pair.split(" / ")
        for year in sorted(df.year.unique()):
            blk = df[(df.procedure == proc) & (df.year == year)].set_index("province")
            if a not in blk.index or b not in blk.index:
                continue
            ra, rb = blk.loc[a], blk.loc[b]
            gap = volume_gap(ra.volume, rb.volume, denom)
            p90d = ra.p90_wait_days - rb.p90_wait_days
            out.append({
                "procedure": proc, "pair": pair, "year": year,
                "survives_rule": bool(gap <= tol),
                "volume_a": int(ra.volume), "volume_b": int(rb.volume),
                "volume_gap_pct": round(gap * 100, 2),
                "p50_a": ra.p50_wait_days, "p50_b": rb.p50_wait_days,
                "p50_diff_a_minus_b": round(ra.p50_wait_days - rb.p50_wait_days, 1),
                "p90_a": ra.p90_wait_days, "p90_b": rb.p90_wait_days,
                "p90_diff_a_minus_b": round(p90d, 1),
                "pct_benchmark_a": round(ra.pct_meeting_benchmark, 1),
                "pct_benchmark_b": round(rb.pct_meeting_benchmark, 1),
                "direction_p90": (f"{a} slower" if p90d > 0 else
                                  f"{b} slower" if p90d < 0 else "no gap"),
            })
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser(description="Task 3: apply the matching rule.")
    ap.add_argument("--table", default=os.path.join(ROOT, "output", "master_table.csv"))
    ap.add_argument("--outdir", default=os.path.join(ROOT, "output"))
    ap.add_argument("--tag", default="",
                    help="suffix for output filenames, e.g. _fy. The rule itself "
                         "is identical across windows; only the input table changes.")
    args = ap.parse_args()

    df = pd.read_csv(args.table)
    pairs = find_pairs(df)

    n_prov = df.province.nunique()
    possible = n_prov * (n_prov - 1) // 2
    n_cells = df.groupby(["procedure", "year"]).ngroups
    n_years = df.year.nunique()

    # Sorted by pair and year for reading, NOT by gap size.
    pairs = pairs.sort_values(["procedure", "pair", "year"]).reset_index(drop=True)
    os.makedirs(args.outdir, exist_ok=True)
    csv_path = os.path.join(args.outdir, f"matched_pairs{args.tag}.csv")
    pairs.to_csv(csv_path, index=False)

    # A pair "survives in all six years" only if it clears the rule every year.
    survivors = (
        pairs.groupby(["procedure", "pair"])
        .agg(years_surviving=("year", "count"),
             years=("year", lambda s: ",".join(str(int(y)) for y in sorted(s))))
        .reset_index()
        .sort_values(["procedure", "pair"])
    )
    surv_path = os.path.join(args.outdir, f"matched_pairs_summary{args.tag}.csv")
    survivors.to_csv(surv_path, index=False)
    with open(os.path.join(args.outdir, f"matched_pairs_summary{args.tag}.json"), "w") as fh:
        json.dump(json.loads(survivors.to_json(orient="records")), fh, indent=1)

    detail = pair_year_detail(df, pairs)
    detail_path = os.path.join(args.outdir, f"pair_year_detail{args.tag}.csv")
    detail.to_csv(detail_path, index=False)
    with open(os.path.join(args.outdir, f"pair_year_detail{args.tag}.json"), "w") as fh:
        json.dump(json.loads(detail.to_json(orient="records")), fh, indent=1)

    print(f"Window: {df.reporting_window.iloc[0]}  ({df.year.min()}-{df.year.max()})")
    print(f"Possible province pairs per procedure-year: {possible}")
    print(f"Procedure-years examined: {n_cells}")
    print(f"Pair-years surviving the rule: {len(pairs)} of {possible * n_cells}")
    print(f"Distinct pairs appearing at least once: {len(survivors)}")
    print()
    print(f"Pairs surviving in ALL {n_years} years:")
    six = survivors[survivors.years_surviving == n_years]
    print(six.to_string(index=False) if len(six) else "  (none)")
    print()
    print("Sensitivity of the volume test to the denominator (NOT used to revise "
          "the result):")
    for d in ("max", "mean", "min"):
        print(f"  {d:5s}: {len(find_pairs(df, denom=d))} pair-years")

    with open(os.path.join(args.outdir, f"matched_pairs{args.tag}.json"), "w") as fh:
        json.dump({
            "rule": {
                "volume_tolerance": VOLUME_TOLERANCE,
                "denominator": DENOMINATOR,
                "formula": "abs(va - vb) / max(va, vb) <= 0.05",
                "also_required": ["same procedure", "same year",
                                  "same reporting window", "same provenance type"],
                "fixed_before_results": True,
            },
            "pairs": json.loads(pairs.to_json(orient="records")),
        }, fh, indent=1)
    # ---- workbook. The rule goes on the first tab, ahead of any result, so a
    # reader meets the criterion before the numbers it selected.
    rule_tab = pd.DataFrame([
        ("Rule", "Both provinces' volume within 5% of each other, same procedure, "
                 "same year, both using the same reporting window and same "
                 "provenance type."),
        ("Volume test", "abs(vol_a - vol_b) / max(vol_a, vol_b) <= 0.05"),
        ("Why max()", "The rule as written does not name a denominator. max() is the "
                      "strictest of the three candidates and is symmetric, so neither "
                      "province is the reference. Fixed before results were seen."),
        ("Denominator sensitivity", "; ".join(
            f"{d}: {len(find_pairs(df, denom=d))} pair-years" for d in ("max", "mean", "min"))),
        ("Reporting window", df.reporting_window.iloc[0]
            + f"; {df.year.min()}-{df.year.max()}, identical on both sides of every pair."),
        ("Provenance", "Provincial ministry/agency submission (aggregate) for all ten "
                       "provinces. CIHI calculates only Hip Fracture Repair itself, "
                       "which is not used here."),
        ("Window + provenance clauses", "Uniform across all provinces, so they exclude "
                                        "ZERO pairs. All 45 pairs satisfy them by "
                                        "construction; the volume test is the only "
                                        "binding constraint. Enforced in code anyway."),
        ("Post-hoc filtering", "None. Every pair the rule produced appears here, "
                               "including small and zero gaps. Rows are sorted by "
                               "procedure and pair name, never by gap size."),
        ("Pairs possible", f"{possible} per procedure-year x "
                           f"{n_cells} procedure-years = {possible * n_cells}"),
        ("Pair-years surviving", str(len(pairs))),
        ("Distinct pairs", str(len(survivors))),
        ("Surviving every year", (f"{int((survivors.years_surviving == n_years).sum())} "
                                  f"of {len(survivors)}. Volumes that match one year "
                                  "routinely diverge the next.")),
        ("Confidence intervals", "None. CIHI publishes aggregate percentiles submitted "
                                 "by provinces, not case-level data, and publishes no "
                                 "intervals of its own. None were manufactured."),
        ("Source", "CIHI Table 1, Wait times for priority procedures, by province and "
                   "Canada, 2008 to 2025. Downloaded 2025-07-18."),
    ], columns=["Item", "Statement"])

    xlsx_path = os.path.join(args.outdir, f"matched_pairs{args.tag}.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as xw:
        rule_tab.to_excel(xw, sheet_name="The rule", index=False)
        pairs.to_excel(xw, sheet_name="Surviving pairs", index=False)
        survivors.to_excel(xw, sheet_name="Pair summary", index=False)
        detail.to_excel(xw, sheet_name="Six-year detail", index=False)
        widths = {"The rule": (14, 96), "Surviving pairs": (10, 30),
                  "Pair summary": (10, 34), "Six-year detail": (10, 34)}
        for name, frame in (("The rule", rule_tab), ("Surviving pairs", pairs),
                            ("Pair summary", survivors), ("Six-year detail", detail)):
            ws = xw.sheets[name]
            ws.freeze_panes = "A2"
            lo, hi = widths[name]
            for idx, col in enumerate(frame.columns, start=1):
                longest = max([len(str(col))] + [len(str(v)) for v in frame[col]])
                letter = openpyxl.utils.get_column_letter(idx)
                ws.column_dimensions[letter].width = min(max(longest + 2, lo), hi)
            if name == "The rule":
                for row in ws.iter_rows(min_row=2, min_col=2, max_col=2):
                    row[0].alignment = openpyxl.styles.Alignment(
                        wrap_text=True, vertical="top")

    flips = []
    for (proc, pair), g in pairs.groupby(["procedure", "pair"]):
        dirs = set(g.direction_p90)
        if len(dirs) > 1:
            flips.append(f"  {proc} {pair}: {', '.join(sorted(dirs))}")
    print()
    print("Pairs where the direction of the P90 gap REVERSES across surviving years:")
    print("\n".join(flips) if flips else "  (none)")

    print(f"\n-> {xlsx_path}\n-> {csv_path}\n-> {surv_path}\n-> {detail_path}")


if __name__ == "__main__":
    main()
