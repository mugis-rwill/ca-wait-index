# Task 1 — Reporting window and provenance

**Source:** Canadian Institute for Health Information. *Wait Times for Priority
Procedures in Canada, 2008–2025 — Data Tables.* Ottawa, ON: CIHI; 2026.
File: `wait-times-priority-procedures-in-canada-2008-2025-data-tables-en.xlsx`.
Downloaded 2025-07-18. Sheets used: **Table 1** (data), **Instructions**,
**Methodology notes**.

---

## Q1. Is the April–September window PEI-only, or does it apply to all provinces?

**It applies to all provinces. There is no province-specific window.**

The window is a property of the `Data year` column, not of the province. CIHI
states it twice in the workbook:

- *Methodology notes*: "Since 2008, CIHI has reported on wait time data for
  procedures completed in April to September of each year... **Data year refers
  to the 6-month period of April to September, unless FY or Q3Q4 is indicated.**
  FY refers to the 12-month fiscal year (April to March) and Q3Q4 refers to the
  other 6-month period in the fiscal year, October to March."
- *Notes under Table 1* (row 20509): "Data year refers to the period April to
  September, unless FY or Q3Q4 is indicated."

Which windows exist in the hip/knee provincial rows:

| Data year | Window | Provinces carrying it |
|---|---|---|
| `2020`–`2025` (bare) | April–September | **all 10** |
| `2020FY`–`2024FY` | April–March (12 mo) | **all 10** |
| `2020Q3Q4`–`2024Q3Q4` | October–March | **all 10** |
| `2025FY`, `2025Q3Q4` | — | **none — not yet published** |

The extra FY and Q3Q4 periods were added during COVID-19 ("During the COVID-19
pandemic, extra data periods have been collected"). They are not a different
province reporting differently; they are additional periods collected from
everyone.

**Why 2025 is bare-year only:** the 2025 fiscal year had not closed when the
workbook was published, so only April–September 2025 exists. This is the
constraint that fixes the choice for Tasks 2–4: **April–September is the only
window available in all six years 2020–2025, so it is the window used
throughout.** Mixing a bare year with an FY year would compare a 6-month count
against a 12-month one.

### Checked, not assumed: is Apr–Sep representative of the full year?

CIHI says the 6-month window "is believed to be representative of the full
year." The FY and Q3Q4 rows let this be tested directly on the 98 province-year-
procedure cells where all three periods are published:

- **Volume.** April–September is **46.8%** of fiscal-year volume on average, but
  ranges from **29.3% to 61.5%**. It is not reliably half a year. Volume from
  this window must never be annualized by doubling.
- **Additivity.** Apr–Sep + Q3Q4 equals FY exactly in only **62 of 98** cells.
  The remainder differ, presumably through rounding or restatement.
- **P90.** The Apr–Sep P90 differs from the same cell's FY P90 by a median of
  **0.5 days** — but by **more than 30 days in 28 of 98 cells**, and by as much
  as **95 days** (Nova Scotia hip, 2020: 474 vs 569).

**What this does and does not affect.** It does *not* undermine a comparison
between two provinces in the same window and year — the window is held constant
on both sides, which is the whole point of the matching rule. It *does* mean no
figure here should be described as that province's annual wait time. Every
number in this work is an April–September figure and is labelled as one.

---

## Q2. Which provinces are collected independently by CIHI, and which self-report?

**All ten provinces self-report hip and knee replacement. None of it is
calculated independently by CIHI.**

*Instructions* sheet: "Wait times for hip fracture repair are calculated using
the Discharge Abstract Database (DAD) and National Ambulatory Care Reporting
System (NACRS) at the Canadian Institute for Health Information (CIHI). **For all
other procedures, aggregate wait time results are submitted to CIHI by
provincial ministries and agencies.**"

*Methodology notes*: "This product uses data provided by provinces in Canada,
except for the indicator Hip Fracture Repair Wait Times, which is calculated
using CIHI's administrative databases."

| Indicator | Provenance | Applies to |
|---|---|---|
| Hip Fracture Repair | CIHI-calculated (DAD + NACRS) | all provinces — **not used in this work** |
| **Hip Replacement** | **Provincial ministry/agency submission** | **all 10 provinces** |
| **Knee Replacement** | **Provincial ministry/agency submission** | **all 10 provinces** |

CIHI receives **aggregate results**, not case-level records. It does not
recompute the percentiles from raw data. This is the single most important fact
about the dataset, and it has three consequences carried through the rest of the
work:

1. **No confidence intervals are possible.** Percentiles arrive pre-computed.
   Without case-level data there is no sampling distribution to work from, and
   CIHI publishes no intervals of its own. None are manufactured here.
2. **The wait clock may not start at the same moment in every province.** What
   counts as the start of the wait (decision to treat, booking date, consult) is
   set by each province's own definition. CIHI harmonizes the reporting format,
   not the underlying measurement. This is the largest comparability risk in the
   data and it is **not resolvable from the published tables.**
3. **Provenance is uniform, so it cannot discriminate between provinces.** See
   below.

---

## Consequence for the Task 3 matching rule

The rule requires matched provinces to share a reporting window **and** a
provenance type. On this dataset both conditions are **uniform across all ten
provinces**: every hip/knee figure used is April–September, and every one is a
provincial ministry submission.

**Stated plainly before the rule is run: these two clauses exclude zero pairs.**
All 45 province pairs satisfy them by construction, and the binding constraint
is the ±5% volume criterion alone.

This is not a defect in the rule and the rule is not being loosened. The clauses
still do real work — they are what forces the use of bare-year rows only, and
they would bite immediately if hip fracture repair (CIHI-calculated) were added,
or if an FY row were mixed in. But the rule must not be described as though
window and provenance filtering removed candidate pairs here. They did not.
