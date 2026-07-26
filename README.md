# CanRoute — Provincial Diagnostic

A capacity/demand diagnostic for hip & knee replacement wait times across
Canadian provinces (2021–2025), built from real CIHI wait-time data and
StatCan population data. This is the lightweight, static-site half of the
broader CanRoute project (cross-provincial patient routing); it's kept
deliberately separate from any live routing app — just an offline pipeline
that produces JSON, and a static site that renders it.

## Architecture

```
raw_data/  →  scripts/ (ingest + compute)  →  output/*.json  →  site/ (renders only)
```

The frontend never computes statistics itself — regression, residuals, tail
flags, quadrant zones, and chart geometry are all computed once in
`scripts/compute.py` and shipped to the browser as data.

## What each part does

- **`scripts/ingest_provincial.py`** — parses CIHI's "Wait Times for Priority
  Procedures" workbook (provincial rows for Hip/Knee Replacement) and the
  StatCan 65+ population table.
- **`scripts/compute.py`** — turns a cleaned (capacity, demand, wait50,
  wait90, volume) table into the full frontend-ready payload: a linear
  regression of wait time on utilization, residuals, P90 tail flags, a
  capacity/demand quadrant zone, and precomputed chart pixel geometry.
- **`scripts/run_provincial.py`** — the real, working pipeline. For each
  province/year:
  - **capacity** = surgical volume per 100k of that province's 65+ population
  - **demand** = year-over-year growth rate of that same 65+ population
    (a real, independent demand-pressure signal, since CIHI has no
    referral/waitlist field to use directly)
  - **`pctBenchmark`** = CIHI's "% meeting benchmark" is carried through as a
    secondary stress signal in the tooltip, not folded into either axis.

  The first available year (2020) has no prior-year population baseline, so
  it's skipped rather than assigned a fabricated growth rate — output covers
  **2021–2025**.

  It also builds a **regional drill-down** from CIHI's own health-region
  breakdown (`hip_regional.json` / `knee_regional.json`, one payload per
  year/province). StatCan has no sub-provincial population data, so this
  view can't reuse the per-capita/population-growth definitions above:
  **capacity** = raw regional surgical volume, **demand** = `100 - %
  meeting benchmark` (both real CIHI numbers, unnormalized). Output covers
  **2020–2025** since it doesn't depend on the population-growth baseline.
- **`site/`** — a single static HTML/JS/CSS dashboard (no build step) with a
  hip/knee toggle, year tabs, and per-province selection (highlights the
  province's dot, its zone card, and shows a P50/P90 trend sparkline).
  Clicking a province swaps the main chart into that province's CIHI health
  regions (different axis definitions, see above); clicking it again
  returns to the provincial view.

## Running the pipeline

```bash
pip install -r scripts/requirements.txt
cd scripts
python3 run_provincial.py \
  --xlsx ../raw_data/wait-times-priority-procedures-in-canada-2008-2025-data-tables-en.xlsx \
  --out ../output
```

This writes `output/hip_provincial.json`, `output/knee_provincial.json`, and
their regional counterparts `output/hip_regional.json` /
`output/knee_regional.json`. The StatCan population CSV defaults to
whatever matches `raw_data/*Population*.csv`; pass `--population` to
override.

## Viewing the site

The page fetches JSON via relative `fetch()`, so it needs to be served over
HTTP, not opened as a `file://` URL:

```bash
python3 -m http.server 8000   # from the repo root
# then open http://localhost:8000/site/index.html
```

## Status

- **Provincial pipeline (CIHI, `run_provincial.py`)** — working, real data,
  no placeholders.
- **Hospital-level pipeline (BC, `run_all.py`)** — not built yet. It expects
  a `scripts/ingest_bc.py` module (real per-hospital COMPLETED/WAITING
  capacity/demand, no placeholder needed) and a BC Ministry of Health
  Surgical Wait Times workbook, neither of which exists in `raw_data/` yet.
- `output/sample_output.json` / `computed_output.json` are leftover
  synthetic-data artifacts from an earlier prototype iteration, kept for
  reference but not used by the current site.
