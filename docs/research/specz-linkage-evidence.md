<!--
---
title: "Spec-z Linkage Evidence"
description: "P2R-04 review surface: defective identifier, corrected join path, recovery populations, selection function, and the closed questions deferred to operator disposition"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.0"
status: "Active - Awaiting Operator Disposition"
tags:
  - type: research
  - domain: astronomy
  - domain: cosmos-web
  - domain: data-engineering
related_documents:
  - "[Spec P2R-04](../../spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md)"
  - "[ETL v2 Verification](etl-v2-verification.md)"
  - "[Schema v1.1](../reference/schema-v11.md)"
  - "[Spec-z Linkage Propagation Inventory](specz-linkage-propagation-inventory.md)"
  - "[P2R-04 Worklog](../../work-logs/2026-08-31-cosmos2025-worklog-p2r-04-specz-linkage-correction.md)"
---
-->

# Spec-z Linkage Evidence (P2R-04 Review Surface)

This is the human approval surface produced by spec P2R-04. It reports what
was measured, states every disposition the successor unit inherits as a
closed question with a recommendation, and decides none of them. Every number
below is reproducible from committed evidence commands against the pinned
sources and the sealed mirror; sources are cited per finding.

Evidence commands: corrected gate 4.1
`src/etl/verify_specz_linkage_v11.py` (SHA-256
`e55f2a44f4ec1dd89f5dae8ec89757afe972ddead288ead6f94d330625594466`),
corrected gate 4.7 `src/etl/characterize_specz_linkage_v11.py` (SHA-256
`83eb96b9c547d157fcb4a6313087477dc671ad7d324fd00ff6ff8d59d25aeb30`);
per-gate runtime evidence in the worklogs. Surfaces:
`source.photometry_primary` (784,016
rows), `source.specz_compilation_unique` (261,975 rows, galaxy level),
`source.specz_compilation_all` (482,579 rows, measurement level), and the two
pinned FITS artifacts
(`specz_compilation_COSMOS_DR1.1_unique.fits` SHA-256 `6ffd1145...`,
`specz_compilation_COSMOS_DR1.1_all.fits` SHA-256 `30675493...`).

Coordinate-basis convention: throughout this surface, an
"entry-to-catalog separation" uses the named compilation surface's
`ra_corrected/dec_corrected` against `photometry_primary.ra/dec` at that
entry's `Id_COSMOS25`. Every different source-entry pairing names both
coordinate surfaces inline.

---

## 1. Findings

Each finding carries a stable ID, a one-line statement, evidence with exact
numbers and their source, and a closed question.

### F-01 — The catalog link column does not address the held compilation's identifier namespace

`photometry_primary.id_specz_khostovan25` values do not resolve against the
DR1.1 compilation's `Id_specz` namespace except coincidentally.

Evidence (corrected gate 4.1 command, amendment worklog gate A1.2): 37,219
distinct non-sentinel (`!= -999`) values; 24,364 present in galaxy-level
`Id_specz`, 12,855 absent; stored range 223–165,312 against compilation
`Id_specz` range 1–487,666 (stored span 33.85% of the compilation range; 0
values exceed the compilation maximum). For the all-links population of
37,219 catalog sources, separations between `photometry_primary.ra/dec` and
the carried link's measurement-level
`specz_compilation_all.ra_corrected/dec_corrected` have median 4,054.34
arcsec, p90 5,956.72 arcsec, and max 9,085.02 arcsec. Separately, for the
24,364-link resolving subset, separations between
`photometry_primary.ra/dec` and the selected galaxy-level
`specz_compilation_unique.ra_corrected/dec_corrected` have median 4,245.57
arcsec, p90 6,061.36 arcsec, and max 9,085.02 arcsec. The compilation's own
crossmatch population of 92,359 measurement-level rows, using
`specz_compilation_all.ra_corrected/dec_corrected` against the catalog
`photometry_primary.ra/dec` named by `Id_COSMOS25`, has median 0.0840 arcsec
and max 0.9983 arcsec. The upstream description ("Unique ID of the source
corresponding to the Id_specz... -999 if no specz match",
`cosmosweb-dr1-detailed-column-descriptions.txt` section 1, line 36) is what
upstream said; the project records the non-resolution as a semantic note on
the dictionary row and as the live column comment, and the values are
mirrored as shipped with no repair.

**Closed question F-01-Q: Is `id_specz_khostovan25` unusable as a join key
against the held DR1.1 compilation? Yes** (measured; see F-03, F-04).

### F-02 — The compilation's own crossmatch into the catalog is exact

Stored `ra_COSMOS25`/`dec_COSMOS25` equal `photometry_primary.ra`/`dec` at
the row named by `Id_COSMOS25`.

Evidence (gate 4.1 command): separation distribution exactly 0.0 arcsec at
min/median/p90/p99/max over every row carrying a valid identifier and valid
coordinates — 92,359 of 482,579 measurement rows (390,220 excluded for the
-999 identifier sentinel; zero rows excluded for invalid coordinates after a
valid id) and 45,193 of 261,975 galaxy rows (216,782 sentinel-id exclusions).
A mutation test perturbing one stored coordinate by 0.5 arcsec in a scratch
copy reports 0.49977 arcsec, proving the zero is measured, not structural.

**Closed question F-02-Q: Is `Id_COSMOS25` the correct, exact join path from
the compilation into `photometry_primary`? Yes.**

### F-03 — The defective path's geometry is field-scale, not a crossmatch

Evidence (corrected gate 4.1 command, amendment worklog gate A1.2):

| Population and coordinate basis | n | min | median | p90 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|
| All links: catalog `photometry_primary.ra/dec` to carried measurement-level `specz_compilation_all.ra_corrected/dec_corrected` | 37,219 | 0.00490" | 4,054.34" | 5,956.72" | 7,219.43" | 9,085.02" |
| Resolving subset: catalog `photometry_primary.ra/dec` to selected galaxy-level `specz_compilation_unique.ra_corrected/dec_corrected` | 24,364 | 0.00604" | 4,245.57" | 6,061.36" | 7,379.07" | 9,085.02" |
| Compilation crossmatch: measurement-level `specz_compilation_all.ra_corrected/dec_corrected` to catalog `photometry_primary.ra/dec` named by `Id_COSMOS25` | 92,359 | 0.00013" | 0.0840" | 0.2322" | 0.6381" | 0.9983" |

The corrected all-links prior reproduction is recorded in F-06.

**Closed question F-03-Q: Do the two geometries describe one crossmatch and
one broken pointer rather than two crossmatches disagreeing about hard
cases? Yes.**

### F-04 — The stored values are range-incompatible with the held namespace

Evidence (gate 4.1 command): stored link range 223–165,312; compilation
measurement-level `Id_specz` range 1–487,666; 0 stored values exceed the
compilation maximum; the stored span covers 33.85% of the compilation's
identifier range, consistent with an earlier compilation release's
renumbering rather than a partial hold of the current one.

**Closed question F-04-Q: Can the stored values be mapped onto the held
namespace by any transformation we hold evidence for? No** (no artifact we
hold defines a mapping; inference is prohibited by the spec and by
AGENTS.md).

### F-05 — The galaxy-level artifact is the measurement-level rows at Priority = 1, as shipped

Evidence (gate 4.1 command): `Id_specz` unique at both levels (482,579/482,579
and 261,975/261,975); column sets identical (32 = live TFIELDS at both);
positional per-column value equality including mask and NaN equality between
the galaxy table and the measurement rows at `Priority = 1`. The
deduplication rule (highest quality flag; ties to the most recent redshift)
is the compilation's own definition at the pinned checkout
`specz_compilation/README.md`, List of Surveys section (SHA-256 `43992cf6...`).
Both artifacts are shipped upstream; neither is derived in this repository.

**Closed question F-05-Q: Is the galaxy-level table a shipped product rather
than something this repository may rederive? Yes.**

### F-06: The defective-path median prior reproduces on its stated basis

The investigation prior is the all-links defective-path median. For all
37,219 catalog sources carrying non-sentinel links, the corrected gate 4.1
command pairs each source's `photometry_primary.ra/dec` with its carried
measurement-level `specz_compilation_all.ra_corrected/dec_corrected` entry.
That population reproduces the prior at 4,054.34 arcsec to two decimals. An
independent dictionary association and spherical-law-of-cosines calculation
returns 4,054.341555895 arcsec, only 1.44e-09 arcsec from the primary result
of 4,054.341555894 arcsec. The earlier claim that the prior's basis was
unreconstructible was wrong.

**Closed question F-06-Q: Does the all-links reproduction agree with the
investigation prior and preserve the conclusion of F-03? Yes.**

### F-07 — Process finding: the P2R-03 verification surface could not regenerate post-extension (repaired)

Extending the sealed dictionary invalidated five pinned input seals of the
Gate 3.13 compiler, and two of its tests asserted the retired active-queue
spec path (broken since the closeout archive move, pre-existing). Repaired
in gate 4.2 without touching the sealed document: the four regenerated inputs
fall back to P2R-03-committed bytes at ref `e65242a` through an injectable,
seal-checked provider; the compiler module source remains mechanically
offline (worklog gate 4.2).

**Closed question F-07-Q: Is `docs/research/etl-v2-verification.md`
byte-unchanged and still reproducible from pinned bytes? Yes.**

### F-08 — Recovery population A and the neighbour-promotion hypothesis

Population A: catalog sources with measurement-level `Id_COSMOS25` entries
but no galaxy-level entry.

Evidence (corrected gate 4.7 command, full per-source enumeration in the run's JSON
output): 1,032 sources over 1,559 entries; every entry carries `Priority = 0`
(verified, not assumed). Entries per source: 716×1, 213×2, 58×3, 22×4, 13×5,
1×6, 4×7, 1×10, 2×11, 2×12. Entry-to-catalog separation: median 0.130", p90
0.380", max 0.982" for the 1,559 measurement-level entries, using
`specz_compilation_all.ra_corrected/dec_corrected` against the catalog
`photometry_primary.ra/dec` named by `Id_COSMOS25`. These are real
sub-arcsecond matches. Confidence values across entries: 0→415, 50→387,
80→303, 85→80, 95→157, 97→217; flags: 4→211, 0→399,
1→383, 2→303, 3→156, 9→80, others ≤14.

The representative search takes one nearest `Priority = 1` entry per
population-A source by measurement-level
`specz_compilation_all.ra_corrected/dec_corrected` separation, then applies
each radius to that same pairwise candidate:

| Radius | Names same catalog source | Names other catalog source | No candidate within radius | Population-A sources |
|---:|---:|---:|---:|---:|
| 3" | 0 | 535 | 497 | 1,032 |
| 5" | 0 | 694 | 338 | 1,032 |
| 10" | 0 | 956 | 76 | 1,032 |

The 5-arcsec 694 / 338 split is not stable across the tested radii. At 5
arcsec, **all 694 representatives name a different catalog source** and none
names the same source. For those 694 pairs, the entry-to-representative
separation using the two measurement-level
`specz_compilation_all.ra_corrected/dec_corrected` positions has median
0.873" and max 4.977". For the same 694 pairs, the population-A catalog
source `photometry_primary.ra/dec` to the representative-named destination
catalog source `photometry_primary.ra/dec` separation has median 1.167", p90
4.143", and max 5.756". This is pairwise nearest-candidate classification
only. It constructs no connected components, is not transitive across A-B
and B-C proximity chains, and has no multi-member component count.

**Closed question F-08-Q: Does the representative-destination measurement
establish a radius-stable recovery classification? No.** At 5 arcsec, all
694 representatives name another catalog source, but the other-source and
no-candidate counts move materially at 3 and 10 arcsec. The evidence does not
establish a selection rule or the destination of sources without a candidate
inside a tested radius.

### F-09 — Recovery population B and redshift disagreement

Population B: catalog sources named by more than one galaxy-level entry.

Evidence (gate 4.7 command): 185 sources over 371 entries (184 pairs, 1
triple). Entry-to-catalog separation median 0.202", max 0.977". Sentinel
redshifts excluded by the explicit rule finite `specz > -90`: 58 entries.
132 groups carry ≥2 usable redshifts; 75 agree within |Δz| ≤ 0.005; median
max-|Δz| 0.0028, p90 0.832, max 4.105. Survey mix spans 40 survey IDs
(37→45, 61→54, 38→42, 31→37, 42→28 entries lead). Full per-source tables
(entry redshifts, flags, confidences, surveys, separations) are in the gate
4.7 enumeration.

**Closed question F-09-Q: Do multiply-named galaxy sources carry material
redshift disagreement? Yes** — 57 of 132 comparable groups exceed
|Δz| = 0.005, with a tail to Δz = 4.1.

### F-10 — The defective column is quality-conditioned (selection function)

Evidence (corrected gate 4.7 command): of 37,219 flagged catalog sources,
24,364 have a non-sentinel defective link that resolves to galaxy-level
`Id_specz`, and 12,855 do not. The tables count galaxy-level entries attached
through `Id_COSMOS25` to each flagged-source population, not catalog sources.

| Galaxy-level attached-entry confidence bucket | Resolving-source population, n=21,700 entries | Non-resolving-source population, n=12,610 entries |
|---:|---:|---:|
| 0 | 3,778 | 1,743 |
| 50 | 2,719 | 1,484 |
| 80 | 3,167 | 1,845 |
| 85 | 632 | 590 |
| 95 | 2,711 | 1,033 |
| 97 | 8,693 | 5,915 |
| Bucket sum / stated total / independent count | 21,700 / 21,700 / 21,700 | 12,610 / 12,610 / 12,610 |

| Galaxy-level attached-entry flag bucket | Resolving-source population, n=21,700 entries | Non-resolving-source population, n=12,610 entries |
|---:|---:|---:|
| -99 | 3 | 19 |
| -2 | 1 | 0 |
| -1 | 383 | 358 |
| 0 | 3,391 | 1,366 |
| 1 | 2,715 | 1,482 |
| 2 | 3,160 | 1,845 |
| 3 | 2,688 | 1,027 |
| 4 | 8,549 | 5,782 |
| 9 | 623 | 587 |
| 11 | 4 | 2 |
| 12 | 7 | 0 |
| 13 | 23 | 6 |
| 14 | 144 | 133 |
| 19 | 9 | 3 |
| Bucket sum / stated total / independent count | 21,700 / 21,700 / 21,700 | 12,610 / 12,610 / 12,610 |

All four distributions reconcile. Flagged sources with no corrected-path
galaxy-level entry at all number 2,760 in the resolving population and 302 in
the non-resolving population. Any sample built on the defective column is
therefore conditioned on spectroscopic quality in a way nothing in the
catalog signals.

**Closed question F-10-Q: Does resolution under the defective column correlate
with the compilation's own quality fields? Yes, measurably** (distributions
above; for example, the non-resolving population carries proportionally more
flag-9 and confidence-85 entries and fewer confidence-95 entries relative to
its size).

### F-11 — Precision and recall of the defective column as a boolean flag

Evidence (gate 4.7 command; every figure names its denominator's surface):

| Surface (positive = source reachable via `Id_COSMOS25`) | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| Galaxy level (`specz_compilation_unique`, 45,007 positives) | 34,157 | 3,062 | 10,850 | 735,947 | 0.9177 | 0.7589 |
| Measurement level (`specz_compilation_all`, 46,039 positives) | 34,841 | 2,378 | 11,198 | 735,599 | 0.9361 | 0.7568 |

**Closed question F-11-Q: Would a sample drawn through the defective column
miss roughly a quarter of the true spectroscopic surface while silently
mislabeling thousands more? Yes.**

### F-12 — Usable spectroscopic availability through the corrected path

Evidence (gate 4.7 command; rule stated: finite `specz > -90`, no confidence
threshold applied): 39,165 galaxy-level sources carry a usable redshift; by
the compilation's own confidence value: 97→16,498, 95→4,201, 85→1,358,
80→7,430, 50→9,021, 0→732, -99→1 (values are not additive across rows: a
source may carry entries at several values; the table counts distinct
sources per value). Multiplicity: galaxy level 44,822×1, 184×2, 1×3;
measurement level 25,430 singletons through one source with 25 entries.

**Closed question F-12-Q: Does the corrected path supply a characterized,
threshold-free spectroscopic surface for the successor unit? Yes.**

### F-13 — Mirror state at completion of P2R-04

`cosmos2025_v11.source` holds thirteen relations (twelve mirrors plus
`provenance`), zero views, zero materialized views; `specz_compilation_all`
loaded under the P2R-03 null contract (482,579 rows, `Id_specz` primary key
from the gate 4.1 uniqueness proof, 32 columns with generated comments,
analyst SELECT verified effective, dual-hash provenance row, 640,000
seeded row-column comparisons reconciled with zero mismatches);
`specz_compilation_unique` renamed with identical count/digest/comments;
`photometry_primary` changed only in the authorized `id_specz_khostovan25`
column comment; no `analysis` schema exists (worklog gates 4.3–4.7).

**Closed question F-13-Q: Is the mirror a lossless, annotated, policy-free
representation of both compilation artifacts? Yes.**

### F-14: Process finding: the P2R-04 executor explained a firing prior instead of debugging it

The P2R-04 gate 4.1 prior check fired on the defective-path median. The
P2R-04 executor then authored the explanatory F-06 finding instead of
debugging the generator that produced the disagreement. The spec's
discriminator worked; the executor failed to follow it. The corrected
practice is that a firing scientific check remains a defect report until the
quantity is independently recomputed and its stated population and
coordinate basis are reproduced.

**Closed question F-14-Q: Must a firing scientific check remain open until
an independent recomputation resolves it? Yes.**

---

## 2. Deferred dispositions (closed questions for the operator)

Each item is a question with a recommendation. None is decided by this unit,
and no selection rule exists anywhere in the repository or database.

**D-01 — Recovery population A selection rule.** Should a catalog source
with only `Priority = 0` entries receive a spectroscopic redshift, and under
what entry-quality conditions? The pairwise nearest-`Priority = 1`
classification is radius-sensitive: at 3, 5, and 10 arcsec, respectively,
the 1,032 sources split as 0 / 535 / 497, 0 / 694 / 338, and 0 / 956 / 76 for
same-source / other-source / no-candidate classifications. These radii
compare the population-A and candidate `Priority = 1` measurement-level
`specz_compilation_all.ra_corrected/dec_corrected` positions. The 5-arcsec
split is not stable. This pairwise calculation constructs no connected
components, is not transitive, and has no multi-member component count.
*Recommendation: exclude population A from the primary spectroscopic sample
and retain it as a documented recovery list; promotion of any demoted
measurement is a scientific selection and should require per-entry review
(confidence/flag/separation), noting the radius sensitivity and the 338
sources with no representative within 5 arcsec.*

**D-02 — Recovery population B resolution rule.** When a catalog source
carries multiple galaxy-level entries, which redshift (if any) applies?
*Recommendation: accept only agreeing groups (e.g. within the tolerance this
surface reports), take the highest-confidence entry with an explicit
disagreement flag otherwise, and never silently average; 57 of 132
comparable groups currently disagree beyond |Δz| = 0.005.*

**D-03 — Spectroscopic sample surface.** Which mirror defines the
spectroscopic sample? *Recommendation: `specz_compilation_unique` (galaxy
level) as the primary surface, with `specz_compilation_all` reserved for
audit of deduplication decisions and population-A/B review.*

**D-04 — Confidence threshold.** What `Confidence_level`/flag threshold, if
any, defines a secure redshift? *Recommendation: report threshold-free
science products where feasible; if a threshold is required for calibration,
treat 95 (flag 3/4) as the candidate cut and record its selection function
explicitly — F-12's per-value table exists so this is a choice, not a
default.*

**D-05 — Calibration and held-out validation split.** How should the split
be drawn given the selection function in F-10/F-11? *Recommendation:
stratify by confidence value and survey before any linkage-based filtering,
hold out by catalog region where feasible, and document that any
defective-column conditioning is excluded by construction.*

**D-06 — Upstream defect report.** Should the `id_specz_khostovan25`
non-resolution be reported to the COSMOS-Web team? *Recommendation: yes —
the column's upstream description claims a correspondence the held DR1.1
compilation does not honor, and upstream can explain the earlier-release
renumbering hypothesis we cannot test.*

**D-07 — T_A v2 spectroscopic unblock.** May T_A v2 use spectroscopy for
calibration/validation before D-01–D-05 are disposed? *Recommendation: no;
T_A v2 may proceed in parallel on non-spectroscopic axes only, per the spec's
execution boundary.*

---

## 3. What this surface does not contain

No selection rule has been applied anywhere in the repository or database;
no view, materialized join, or spectroscopic sample exists; no
`Priority = 0` entry has been promoted; no confidence threshold has been
applied to any figure except where a distribution is itself the report; the
defective column's values are mirrored as shipped and annotated, never
repaired; and the `analysis` schema remains uncreated.

---

## Appendix A: Gate 4.1 prior observations versus corrected values

Source: corrected gate 4.1 command output, amendment worklog gate A1.2.
Agreements state both numbers. F-06 records the corrected reproduction of
the defective-path prior.

| Observation | Prior | Observed | Agreement |
|---|---:|---:|---|
| Non-sentinel link values, all distinct | 37,219 | 37,219 (distinct == count) | Yes |
| Resolving by galaxy-level `Id_specz` | 24,364 | 24,364 | Yes |
| Not resolving | 12,855 | 12,855 | Yes |
| Stored link value range | 223–165,312 | 223–165,312 | Yes |
| Compilation `Id_specz` range (measurement level) | 1–487,666 | 1–487,666 | Yes |
| Measurement rows; galaxy rows | 482,579; 261,975 | 482,579; 261,975 | Yes |
| Galaxy set == measurement `Priority = 1` | full equality | full row-and-column equality (F-05) | Yes |
| `ra/dec_COSMOS25` vs mirror at that id | zero, all rows | zero at min/median/p90/p99/max, both surfaces (F-02) | Yes |
| Compilation crossmatch separation | median 0.084", ceiling 0.998" | median 0.0840", max 0.9983" (measurement-level n=92,359; `specz_compilation_all.ra_corrected/dec_corrected` to catalog `photometry_primary.ra/dec` named by `Id_COSMOS25`) | Yes |
| Defective-path separation median | 4,054.34" | 4,054.34" (all-links n=37,219; catalog `photometry_primary.ra/dec` to measurement-level `specz_compilation_all.ra_corrected/dec_corrected`) | Yes (F-06) |
| Distinct sources, galaxy level | 45,007 | 45,007 | Yes |
| Distinct sources, measurement level | 46,039 | 46,039 | Yes |
| Usable-redshift sources, galaxy level | 39,165 | 39,165 (rule: finite `specz > -90`) | Yes |
| Flagged sources absent from galaxy surface | 3,062 | 3,062 | Yes |
| Flagged sources absent from measurement surface | 2,378 | 2,378 | Yes |
| Multiply-named sources, galaxy level | 185 groups / 371 rows | 185 / 371 | Yes |
