# Limitations

## What this is built from

Every number comes from one table: **Table 1, "Wait times for priority
procedures, by province and Canada, 2008 to 2025"**, in *Wait Times for Priority
Procedures in Canada, 2008–2025 — Data Tables* (Canadian Institute for Health
Information, Ottawa, 2026), downloaded 18 July 2025. Two procedures — **hip
replacement** and **knee replacement**. Six years, **2020 through 2025**. Ten
provinces; territories are excluded, as they are in CIHI's own provincial
reporting. That is 120 rows, and all 120 are complete.

The only other source is **Statistics Canada Table 17-10-0005-01, "Population
estimates on July 1, by age and gender"** (downloaded 10 September 2025), used
solely as the denominator for the per-100,000 rate. Recent years in that series
are postcensal and Statistics Canada revises them; the 2025 figure is
preliminary.

Every row of the master table carries the Table 1 row numbers it was built from,
so any figure can be checked against the source in a few seconds.

## This is a description, not an explanation

Nothing here is adjusted, modelled, or causal. The tables and charts report what
provinces submitted, arranged so it can be compared. **No claim is made that any
province's wait time is caused by its volume, its population, or its policy.**
Where two provinces differ, this work establishes that they differ — not why.
Readers who want a "why" will not find support for one here, and should not
infer it from the ordering of a chart.

## The rule, as it was written before we ran it

Two provinces form a matched pair when:

> Both provinces' volume is within 5% of each other, in the same procedure and
> the same year, with both using the same reporting window and the same
> provenance type.

"Within 5% of each other" does not name a denominator, so one was fixed in
advance — `|a−b| / max(a, b) ≤ 0.05`, the strictest of the candidates, symmetric
so that neither province is the reference. This was chosen before results were
seen and was not revised after. As it happens the choice was immaterial: max,
mean, and min denominators all yield the same 18 surviving pair-years.

**Every pair the rule produced is published**, including those with small gaps
and including the ones nobody would write about. Charts are ordered
alphabetically rather than by gap size. The smallest surviving gap is 37 days
and the largest 207; the widely-quoted Nova Scotia / Saskatchewan hip comparison
is 161 days, which is **seventh of eighteen**, not the largest.

## Comparability problems we know about

**The window is six months, not a year.** Every figure is April–September. CIHI
uses that window for timeliness and states it is "believed to be representative
of the full year." Where the fiscal-year rows exist, that belief is only
partly borne out: April–September is **46.8%** of fiscal-year volume on average
but ranges from **29.3% to 61.5%**, and the P90 measured on it differs from the
fiscal-year P90 by more than 30 days in **28 of 98** province-years, by as much
as 95. No figure here is annualized, and none should be described as a
province's annual wait time. The window is the same on both sides of every
comparison, so this does not distort the pairs — it limits what the pairs
generalize to.

**The window is not uniform across the available data, only across ours.** CIHI
also publishes fiscal-year and October–March rows for 2020–2024. We use none of
them, because 2025 has neither: the fiscal year had not closed at publication.
April–September is the only window present in all six years, so it is the only
one that permits a six-year series.

**Everything is self-reported.** CIHI calculates only one indicator itself — hip
fracture repair, from its own administrative databases — and that indicator is
not used here. Hip and knee replacement results are **aggregate figures
submitted by provincial ministries and agencies**. CIHI does not recompute them
from case-level records.

This has a consequence that no amount of care on our side can fix: **what starts
the clock may not be the same event in every province.** Whether the wait begins
at the decision to treat, at booking, or at some other point is set by each
province's own definition. CIHI harmonizes the reporting format, not the
underlying measurement. This is the largest comparability risk in the data, it
is not resolvable from the published tables, and a gap between two provinces may
in part reflect it.

**Provenance is uniform, so it filters nothing.** Because all ten provinces
self-report on the same window, the rule's window and provenance clauses are
satisfied by all 45 possible pairs and exclude none. They are enforced in code
anyway, and would take effect immediately if a CIHI-calculated indicator or a
fiscal-year row were added. But the rule should not be described as though those
clauses screened anything out here. They did not.

**No confidence intervals.** Because the percentiles arrive pre-computed and
CIHI publishes no intervals, there is no sampling distribution available to work
from. We publish none. A 141-case figure from Prince Edward Island and an
11,952-case figure from Ontario are printed with the same apparent authority,
and the small-province figures are inevitably less stable. Read them with that
in mind. We would rather say this than manufacture an interval that looks
rigorous and is not.

**Case mix is not controlled for, and could explain any gap here.** The data
carry no information on patient age, comorbidity, whether a procedure was a
primary or a revision, urgency, or how each province triages its queue. A
province with more complex patients, or one that books its most urgent cases
outside the measured pathway, can post a longer tail for reasons that have
nothing to do with how well its system runs. **Any observed gap, including the
matched-pair gaps, may be a case-mix difference.** Matching on volume does not
address this; it matches the size of the queue, not who is in it.

## Procedures performed is throughput, not capacity

The count of procedures is what a province *did*, not what it *could have done*.
It is bounded by operating-room time, staffing, and referral volume all at once,
and a low count cannot be read as a capacity ceiling any more than a high one can
be read as slack. For that reason it is reported **only as a rate** — procedures
per 100,000 population aged 65+ — and never as a capacity measure or an
efficiency score.

Two cautions on that rate. It is a **six-month rate**, because the numerator is a
six-month count; it must not be doubled. And the 65+ denominator is a
standardizing device, not a true population at risk: people under 65 receive
these procedures too, and are not in the denominator. The rate makes provinces
of different sizes and age structures comparable to each other. It is not the
share of any real population that had surgery.

In this data the rate has little to say about the tail. Across the ten provinces
in 2025, hip procedures per 100,000 aged 65+ and P90 correlate at **−0.26** — a
weak relationship in the expected direction and nothing more. Manitoba has the
highest throughput rate and the fourth-longest tail.

## One thing we removed

An earlier draft of this work used a regression that did not survive our own
diagnostics, and it was removed rather than reported.

## What we would still like and do not have

Case-level records, which would make real intervals and case-mix adjustment
possible; each province's written definition of when the wait clock starts; and
fiscal-year 2025 figures, which will allow the six-month window used here to be
checked against the full year for the most recent and most quoted year in the
series.
