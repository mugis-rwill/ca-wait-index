# Canada Hip & Knee replacement Wait-times Index

This is a comparison index for hip & knee replacement wait times across
Canadian provinces for years 2020–2025. It's built from real CIHI wait-time data and
StatCan population data. This repo consists of scripts that ingests the raw CIHI data and uses them to calculate the capacity & demand metrics for each province and saves them as JSON files, which then are rendered using Javascript.

## The Architecture

```
raw_data/                       two unedited raw data files,
  wait-times-...-2008-2025.xlsx   CIHI Table 1
  statcan_65plus_bands_provincial.csv

        |
        v
scripts/build_master_table.py   --window aprsep | fy
        |
        +--> output/master_table[_fy].csv               the audit trail (tracked)
        |
        +--> scripts/make_benchmark_doc.py -> index.html          (the site)
```

Nothing computes at page load. Each generator embeds its data in the HTML it
writes, so the pages need no `fetch()` and work from `file://`.

How to rebuild everything in one command:

```bash
pip install -r scripts/requirements.txt
python3 scripts/build_all.py          # 3 steps, in order of dependency
python3 scripts/build_all.py --list   # list all of them without running
```

Every step is deterministic meaning that running twice produces byte-identical files, so a
non-empty `git diff` after a rebuild means an input or a script changed, never
the build.

## What each part does

- **`scripts/build_master_table.py`** — reads the two raw files into one row per
  province / procedure / year. `--window aprsep` gives April–September 2020–2025
  (120 rows); `--window fy` gives the 12-month fiscal year 2020–2024 (98 rows,
  because Newfoundland published no 2024FY figures). Both windows come from this
  one code path so they cannot drift. Every output row carries
  `cihi_source_rows`, the Table 1 row numbers behind it.
- **`scripts/make_benchmark_doc.py`** + **`scripts/benchmark_template.html`** —
  **the site.** Writes `index.html` from the two master tables.
  **Edit the template, never `index.html`** — the next build overwrites it.
- **`scripts/build_all.py`** — sequences the three steps above: both master
  tables, then the page.
- **`docs/`** — the written findings: the reporting-window and provenance
  analysis, and the limitations page.

## What the page shows

Each province-year is a vertical segment from its **median wait (P50)** to its
**90th-percentile wait (P90)**, drawn against one horizontal line at the
**182-day benchmark** CIHI states for hip and knee replacement (6 months). Where
a segment sits relative to that line is the point: entirely below it, the
province clears the benchmark for at least 90% of patients; starting above it,
the province misses for more than half.

Figures on the page, all taken or computed directly from CIHI's published
numbers — nothing is modelled:

| Figure | Definition |
|---|---|
| P50, P90 | CIHI's reported 50th and 90th percentile waits, in days |
| % meeting benchmark | CIHI's reported share treated within 182 days |
| Missed cases | volume × (100 − % meeting benchmark) / 100 — the percentage turned into people |
| Tail ratio | P90 ÷ 182 — how many times the benchmark the slowest tenth waits |
| Volume | CIHI's reported case count for the window |
| Rate | volume per 100,000 population aged 65+ (StatCan) |

Volume is shown on a **separate strip beneath the chart**, on its own zero-based
scale. Two vertical scales on one frame let the
author decide, by choosing the scales, whether a reader sees a relationship —
and volume barely predicts the tail here, so the reader must not be nudged into
seeing one.

The page also shows the benchmark threshold that each province's own three
published numbers imply (interpolating between P50 and P90 to the reported
benchmark share). This is a diagnostic to justify where the line sits, not a
published figure; the per-province values are shown so the assumption can be
checked.

## Reporting period — the one that bites

CIHI's `Data year` is **April–September** unless suffixed `FY` (12-month fiscal
year) or `Q3Q4` (October–March), so a bare `2025` is a *half-year* count. The
2024 rows confirm it: Apr–Sep plus Q3Q4 equals FY exactly (Ontario 11,515 +
11,757 = 23,272).

`build_master_table.py` matches the period string **exactly** — `{year}{suffix}`
— never the leading four digits, which would collapse three different periods
into one.

The two windows are never mixed. A 6-month count beside a 12-month one is not a
comparison, so the page toggles between them and the rate label changes with the
window — only the fiscal-year rate is an annual one. April–September is the only
window present in all six years, because `2025FY` did not exist when the
workbook was published.

## Why the window is 2020 onward

CIHI's workbook reaches back to 2008 with complete coverage from 2010, but the
pre-COVID and post-COVID periods behave as different systems: the ranking of
provinces by median wait is nearly unrelated across the two eras. A series
spanning both would average two regimes and describe neither. See `docs/` for
the evidence.

## Provenance

Every row of `output/master_table*.csv` carries a `cihi_source_rows` column with
the Table 1 row numbers behind it, and `index.html` embeds the same row numbers
for every figure it draws. Any published number can be traced to the workbook in
a few seconds without running any code.

## Viewing the site

`index.html` is self-contained and works from `file://` — open it directly, or
serve the repo root with `python3 -m http.server 8000`.
