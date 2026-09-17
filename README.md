# CliniDashboard

This is a capacity/demand comparison tool for hip & knee replacement wait times across
Canadian provinces (2020–2025), built from real CIHI wait-time data and
StatCan population data. This repo has scripts that ingests raw data and calculates the capacity & demand metrics for each province and saves them as JSON files, then uses Javascript to render it.

## Architecture

```
raw_data/                       two files, and nothing else is read
  wait-times-...-2008-2025.xlsx   CIHI Table 1
  statcan_65plus_bands_provincial.csv

        |
        v
scripts/build_master_table.py   --window aprsep | fy
        |
        +--> output/master_table[_fy].csv               the audit trail (tracked)
        |    output/master_table[_fy].{xlsx,json}        convenience copies (ignored)
        |
        +--> scripts/matched_pairs.py      -> the Task 3 rule
        +--> scripts/make_benchmark_doc.py -> index.html          (the site)
        +--> scripts/make_charts.py        -> output/charts.html
        +--> scripts/make_pairs_doc.py     -> output/matched_pairs.html
        +--> scripts/make_fy_pairs_doc.py  -> output/matched_pairs_fy.html
```

Nothing computes at page load. Each generator embeds its data in the HTML it
writes, so the pages need no `fetch()` and work from `file://`.

Rebuild everything with one command:

```bash
pip install -r scripts/requirements.txt
python3 scripts/build_all.py          # 9 steps, in dependency order
python3 scripts/build_all.py --list   # show them without running
```

Every step is deterministic — running twice produces byte-identical files, so a
non-empty `git diff` after a rebuild means an input or a script changed, never
the build. (The `.xlsx` copies are the exception — `openpyxl` stamps the current
time into them — which is one reason they are gitignored rather than tracked.)

## What each part does

- **`scripts/build_master_table.py`** — reads the two raw files into one row per
  province / procedure / year. `--window aprsep` gives April–September 2020–2025
  (120 rows); `--window fy` gives the 12-month fiscal year 2020–2024 (98 rows,
  because Newfoundland published no 2024FY figures). Both windows come from this
  one code path so they cannot drift. Every output row carries
  `cihi_source_rows`, the Table 1 row numbers behind it.
- **`scripts/matched_pairs.py`** — applies the Task 3 matching rule, stated in
  the module docstring before any result. `--tag _fy` runs it on the other
  window.
- **`scripts/make_benchmark_doc.py`** + **`scripts/benchmark_template.html`** —
  **the site.** Writes `index.html` and, from the same source, the skeleton-less
  `output/benchmark_view.html` (gitignored; for publishing as an Artifact).
  **Edit the template, never `index.html`** — the next build overwrites it.
- **`scripts/make_charts.py`**, **`make_pairs_doc.py`**, **`make_fy_pairs_doc.py`**
  and their `*_template.html` files — the three sibling pages.
- **`scripts/make_local_index.py`** — writes `deliverables.html`, a local
  contents page listing every generated file with the command that produces it.
  Untracked, because it links almost entirely to gitignored files.
- **`scripts/build_all.py`** — sequences all of the above. The three index
  steps always run; the six sibling steps run only when their script is present
  and are skipped, with a note, when it is not — so a fresh clone builds the
  site without error.
- **`docs/`** — the written deliverables: the reporting-window and provenance
  findings, and the limitations page.

### What is tracked, and what is not

Tracked: `raw_data/`, `docs/`, `README.md`, `index.html`, and — as the audit
trail behind the published figures — exactly the two files the index generator
reads: `output/master_table.csv` and `output/master_table_fy.csv`. In
`scripts/`, only what `index.html` depends on: `build_master_table.py`,
`make_benchmark_doc.py`, `benchmark_template.html`, `build_all.py` and
`requirements.txt`. A clean export of the tracked files rebuilds `index.html`
byte-for-byte; that is the test the tracked set was cut against.

`index.html` also embeds the CIHI Table 1 row numbers behind every figure
(`cihi_source_rows`), so the page is auditable on its own without the separate
source tabs.

Gitignored: the matched-pairs and charts pages, **the scripts and templates that
make them** (`matched_pairs.py`, `make_charts.py`, `make_pairs_doc.py`,
`make_fy_pairs_doc.py`, `make_local_index.py` and their `*_template.html`), and
their data. They are separate work products, not part of the site. They remain
on disk here and `build_all.py` runs them when present; on a machine without
them the site still builds. Open `deliverables.html` to browse them locally.

Also gitignored, from the index step itself: the `.json` and `.xlsx` copies of
the master tables, the `sources*` provenance tabs, `benchmark_view.html` (the
skeleton-less form of the page, for publishing as an Artifact) and
`benchmark_data.json` (the payload embedded in both pages). All are regenerated
by the build and read by nothing that is tracked.

Also gitignored: **`_archive/`**. It holds the previous pooled-panel regression
(`panel.py`, `regional_panel.py` and helpers) and the previous front page
(`script.js`, `panel.css`, `style.css`, `trendlines.*`), plus the inputs and
outputs only those used. Nothing current reads any of it. It is on disk rather
than deleted because **those files were staged but never committed**, so `git`
has no copy to restore. `rm -rf _archive` purges it. See `_archive/README.md`.

Measures used throughout:

- **capacity** = surgical volume per 100k of the 65+ population
- **demand** = see "Which demand variable" below — `share65` between provinces,
  `share75` within one
- **pctBenchmark** = CIHI's "% meeting benchmark", carried through as a
  secondary signal rather than folded into an axis

### Why the window is 2020 onward

The brief asks for 2020–2025, and the data agrees that is the right place to
start. CIHI's workbook reaches back to 2008 with complete coverage from 2010,
but the pre-COVID and post-COVID eras behave as different systems: rank
correlation of province means between 2010–2019 and 2020–2025 is **+0.10**.
Nova Scotia ran 207 days pre-COVID, the slowest in Canada, and 168 after, the
second fastest — the only province to reverse. A series spanning both averages
two regimes and describes neither.

(That check was run against the archived panel model; see
`_archive/pipeline/panel.py`. It is reported here because the conclusion still
governs which years the current tables cover, not because the model does.)

### Reporting period — the one that bites

CIHI's `Data year` is **April–September** unless suffixed `FY` (12-month fiscal
year) or `Q3Q4` (October–March), so a bare `2025` is a *half-year* count. The
2024 rows confirm it: Apr–Sep plus Q3Q4 equals FY exactly (Ontario 11,515 +
11,757 = 23,272).

`build_master_table.py` matches the period string **exactly** —
`{year}{suffix}` — and never the leading four digits. Taking `int("2025FY"[:4])`
collapses three different periods into one integer and leaves the choice between
them to row order, which is how an earlier pipeline landed on April–September by
luck rather than by rule; the first time `2025FY` is published, that approach
silently doubles Ontario's volume with no error raised.

The two windows are never mixed. A 6-month count beside a 12-month one is not a
comparison, and April–September is the only window present in all six years,
because `2025FY` did not exist when the workbook was published. See
`docs/TASK1_window_and_provenance.md` for the full finding, including the test of
CIHI's claim that the 6-month window represents the full year.

## The descriptive track

`build_master_table.py`, `matched_pairs.py` and the three page generators are a
separate line of work from the panel model above, and share none of its code.
They read the CIHI workbook and the StatCan population file directly and fit
nothing. See `docs/` for the window-and-provenance findings and the limitations
page.

```bash
cd scripts
python3 build_master_table.py                    # 120 rows, Apr-Sep 2020-2025
python3 build_master_table.py --window fy        #  98 rows, fiscal 2020-2024
python3 matched_pairs.py                         # the matching rule, Apr-Sep
python3 matched_pairs.py --table ../output/master_table_fy.csv --tag _fy
python3 make_benchmark_doc.py                    # -> ../index.html
python3 make_pairs_doc.py ; python3 make_fy_pairs_doc.py
```

Every row of `output/master_table*.csv` carries a `cihi_source_rows` column with
the Table 1 row numbers behind it, so any published figure can be traced to the
workbook in a few seconds.

## Status

- **Front page (`index.html`)** — the benchmark view; generated, current.
- **Pipeline** — working, real data, no placeholders, deterministic.
- **Previous regression work** — moved to `_archive/`, read by nothing.
