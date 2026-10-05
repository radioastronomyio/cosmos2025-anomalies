<!--
---
title: "P2R-05 Review Document: Spectroscopic Association and Eligibility Product"
description: "Human review surface for the mechanically sealed P2R-05 product: policy rendering, full sample accounting, sensitivity results, limitations, stable findings S5-F01 onward, and the five pending acceptance questions"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-22"
version: "1.1"
status: "Active - Awaiting Operator Adoption Review"
tags:
  - type: research
  - domain: astronomy
  - domain: spectroscopy
  - domain: data-engineering
related_documents:
  - "[Spec-z Science Dispositions](../specz-science-dispositions.md)"
  - "[Spec-z Linkage Evidence](../specz-linkage-evidence.md)"
  - "[Coverage Baseline](coverage-baseline.md)"
  - "[Frozen Tile Map](tile-map.md)"
  - "[Gate 5.3 Evidence](evidence-5-3.md)"
---
-->

# P2R-05 Review: Spectroscopic Association and Eligibility Product

This document is written for a reader who has not followed the execution.
Everything claimed here resolves to verified evidence with a reproduction
command; nothing was copied forward from a prior document without
reproduction. The product is **mechanically complete and sealed** and
**pending scientific adoption**: every table row carries
`pending_scientific_adoption`, and the five acceptance questions at the end
are unanswered.

## Product identity

| Field | Value |
|---|---|
| Database / schema | `cosmos2025_v11.analysis` |
| Run id | `1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c` |
| Policy | `p2r05-specz-policy-v1` (`configs/specz_science_policy_v1.yaml`, semantic digest in the run row) |
| Approved spec | v1.0, SHA-256 `7f481111ad826dd80b01106eeec71bfdaf0f5c649c0cc79b8661a0087af2757b` |
| Input snapshot | manifest SHA-256 `06b19654fc715106ba1f788b52e084df1e94043343517f2b8a49fd44abfff7a4` |
| Rows | measurements 482,579; sources 784,016; splits 784,016 |
| Mechanical seal | 2026-09-22T10:21:25Z; evidence in the run row |

Reproduce the core verification:

```
python -B src/features/specz_science/check_installed_product.py \
    --mode post-seal \
    --run-id 1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c
python src/features/specz_science/check_installed_independent.py
```

The post-seal command verifies the seal, run identity and installed content
against sealed metadata using SELECT-only analyst access. The historical
`--mode pre-seal` check requires an unsealed candidate and compares against
staging artifacts; it is expected to reject this sealed run. Neither mode
changes the seal or answers the pending adoption questions.

Full enumerations live in the installed tables under the run id above;
this document links figures to `analysis.specz_p2r05_<table>` columns
rather than pasting 784k rows.

## Policy as executed (compact rendering)

- **Association (P-01):** compilation rows associate solely through
  `id_cosmos25 = photometry_primary.id`; the native `-999` identifier is an
  explicit no-association state. Every `_all` measurement is audited; every
  catalog source receives a summary. Population A (`_all` only, all
  Priority 0 on this hold) is retained with no preferred redshift and is
  ineligible for both secure-use populations; no entry was promoted and no
  neighbour destination inferred.
- **Quality (P-02):** `numeric_valid_z` = non-null, finite, strictly
  positive. Recognized measured flags {1,2,3,4,9,11,12,13,14,19} with base
  confidences 50/80/95/97/85 and the +10 broad-line offset. A secure
  measurement requires flag in {3,4,13,14}, confidence in [95,100]
  consistent with that mapping, and numeric-valid z.
- **Preferred entry (P-03):** among a source's numeric-valid `_unique`
  entries, the highest valid confidence in [0,100]; ties broken by
  ascending `id_specz` (bookkeeping, not evidence of correctness); the
  value is copied, never averaged.
- **Conflict (P-04):** absolute pairwise difference > 0.005 is conflict.
  `unique_numeric_conflict` (numeric-valid `_unique` pairs) and
  `secure_all_conflict` (secure `_all` pairs) each veto both secure-use
  populations; `other_measurement_disagreement` is audit-only. Fewer than
  two qualifying entries means *not assessable*, not corroboration; a
  single secure preferred entry may be used, labelled singly supported.
- **Routing (P-05):** `lephare.type` is a photometric classification, not
  spectroscopic truth. Type 1 vetoes both populations. Primary galaxy
  eligibility = secure preferred + no veto + type 0 + no broad-line
  evidence + valid split. Separate validation = same quality gates, types
  {0,2}, and broad-line or photometric-QSO evidence, with distinct labels
  for the two evidences. The two booleans are mutually exclusive by
  construction.
- **Partitions (P-06):** SHA-256 tile ranking under the frozen salt;
  4 holdout / 4 validation / 12 development tiles; zero unassigned
  production sources; no rebalancing.
- **Diagnostics (P-07):** the pre-photometric-type mask, survey/confidence
  and photometric/spatial coverage, and exactly three sensitivity
  variants. No residual performance, fitted correction, or outcome metric
  was computed.
- **Upstream report (P-08):** prepared locally, not sent.
- **Adoption (P-09):** nothing is adopted by this document.

## Full sample accounting

Denominator throughout: 784,016 photometric catalog sources.

| Stage (predicate) | Sources | Fraction |
|---|---:|---:|
| Reached through `_all` association | 46,039 | 5.87% |
| Reached through `_unique` | 45,007 | 5.74% |
| Population A (`_all` only) | 1,032 | 0.13% |
| With a preferred `_unique` entry (numeric-valid) | 37,722 | 4.81% |
| With a secure preferred entry (P-02) | 20,100 | 2.56% |
| Vetoed by a P-04 flag (among all sources) | 722 | 0.09% |
| Qualified before photometric type (secure, unvetoed, valid tile) | 19,419 | 2.48% |
| **Primary galaxy eligible** | **18,402** | 2.35% |
| **Separate validation eligible** | **668** | 0.09% |

Primary-galaxy eligibility by partition: development 11,269, holdout
3,938, validation 3,195. Separate validation by partition: development
389, holdout 150, validation 129. Within the separate-validation
population, 259 members carry spectroscopic broad-line evidence and 409
are photometric-QSO-only; the labels remain distinct in the product
(`broad_line_reported`, `photometric_qso`). Of the 18,402 primary-galaxy
members, 10,652 are singly supported and 7,750 multiply supported.

State accounting closes exactly: 18,402 + 668 + 722 + 349 (LePHARE type 1
routed out) + 763,875 (no secure preferred) = 784,016. Overlapping
exclusion reasons and their counts are in
[`coverage-baseline.md`](coverage-baseline.md); reasons are retained per
source in `exclusion_reasons`, never collapsed.


Among the 20,100 secure-preferred sources, 681 have either P-04 veto;
19,419 remain qualified before photometric type. The 722 catalog-wide veto
count also includes 41 without a secure preferred entry. Secure-preferred
corroboration is 11,183 singly supported, 8,263 multiply supported and 654
conflicting, summing to 20,100. Corroboration describes secure `_all`
measurements; its conflicting category is not the union of both P-04 vetoes.

## Sensitivity summary

| Variant | Primary galaxy | Net change | Separate validation | Net change |
|---|---:|---:|---:|---:|
| Baseline | 18,402 | — | 668 | — |
| Confidence floor 97 | 14,738 | -3,664 | 598 | -70 |
| Absolute tolerance 0.001 | 16,992 | -1,410 | 480 | -188 |
| Normalized 0.005 | 18,567 | +165 | 760 | +92 |

All membership-change reasons are enumerated in
[`coverage-baseline.md`](coverage-baseline.md): the confidence floor's
losses are entries with confidence in [95,97) and its gains are vetoes
dissolved when one member of a conflicting secure pair drops below the
floor; the tighter absolute tolerance only adds vetoes; the normalized
rule only dissolves vetoes at these redshifts. These are diagnostic
alternatives; the approved baseline is unchanged and no variant was
selected.

## Limitations

- **Selection on LePHARE classification.** Primary-membership conditions
  on the photometric pipeline whose behavior a later unit may evaluate. Of
  the 19,419 otherwise-qualified sources, 349 carry LePHARE type 1 and are
  excluded, and 259 of the type-0/type-2 members carry broad-line
  evidence routing them out of primary use. The pre-type broad-line total
  is 261, including two type-1 sources already counted among the 349 excluded. Performance claims made on
  these populations apply to the selected LePHARE-classified samples and
  cannot establish unconditional performance across stellar/QSO
  classification failures or the full spectroscopic population. A passing
  cross-tab does not show excluded stars or QSOs were misclassified.
- **Spectroscopic representativeness.** 5.87 percent source coverage,
  survey-imbalanced (survey 38 alone contributes 184,275 of 420,362
  numeric-valid entries). Stratification diagnostics do not make
  spectroscopy representative of unobserved photometric populations.
- **Spatial partitions limit, but do not eliminate, leakage.** Tile
  blocking reduces one route; blended sources, upstream calibration, and
  survey systematics can still cross partitions.
- **Held-out records were read to build and check eligibility.** Their
  downstream prediction errors remain unevaluated; no outcome metric was
  computed.
- **A secure spec-z tests photo-z behavior, not mass truth.** It cannot
  establish which stellar-mass estimate is correct or explain mass
  disagreement; CIGALE redshifts are fixed to LePHARE solutions in the
  published methodology and no independent CIGALE photo-z exists.

## Findings

Each finding carries a statement, evidence locator, reproduction command,
and a closed question where a decision is required. Numbers below were
reproduced by this run from the captured snapshot, not carried from prior
documents.

**S5-F01 — The corrected association path is exact and complete for this
product.** All 482,579 audited measurements carry association status;
92,359 non-sentinel rows resolve to 46,039 catalog sources with zero
unresolved non-sentinel identifiers. Evidence: `analysis.specz_p2r05_measurements`
(`association_status`, `resolved_catalog_id`); independent check in
`check_installed_independent.py`. *Closed question: none; F-01/F-02 of the
P2R-04 surface are confirmed on this hold.*

**S5-F02 — Population A is a structural zero and stays unpromoted.** 1,032
sources over 1,559 entries, every entry Priority 0; no preferred redshift;
ineligible for both populations. Evidence: `specz_p2r05_sources.population_a`,
`preferred_id_specz IS NULL`; reproduction: gate 5.3 reductions
(`python src/features/specz_science/verify.py`). *Closed question: D-01 is
disposed by the approved policy; promotion of any demoted measurement
remains per-entry review, not an automated rule.*

**S5-F03 — Preferred-entry selection is deterministic and tie-broken by
bookkeeping only.** 37,722 sources have a numeric-valid preferred entry;
54 preferred selections were ties broken by ascending `id_specz`; tie
lists are carried (`preferred_tied_ids`). Evidence:
`specz_p2r05_sources.preferred_*`. *Closed question: none for construction;
S5-Q02 decides whether this baseline is adopted for calibration use.*

**S5-F04 — Conflict vetoes flag 722 sources catalog-wide, including
681 of the 20,100 secure-preferred sources.** Secure alternatives dominate
over shipped disagreements: 671 sources catalog-wide carry a
secure `_all` conflict (including 649 with a single `_unique` entry —
detectable only through the `_all` audit), 57 carry `_unique` numeric
conflicts (6 overlap). Evidence: `specz_p2r05_sources` flags and
`conflict_witnesses`; reproduction: `check_installed_independent.py`. *Closed
question: the policy deliberately treats shipped-representative
disagreement more conservatively than low-quality demoted discrepancies;
S5-Q02/Q03 confirm or revise that choice.*

**S5-F05 — The quality mapping is internally exact on this hold.** Every
one of the 272,909 flag-domain/confidence-range entries matches the
documented flag/confidence mapping; no unrecognized flag reaches
confidence 95 (flag 5 sits at 90; 6/10 at -99; -3 appears in `_all` only).
Evidence: gate 5.3 evidence document; `specz_p2r05_measurements.flag_confidence_mapping_consistent`.
*Closed question: any future threshold below 95 must reconsider flag 5
explicitly, per the approved policy.*

**S5-F06 — Photometric-type routing removes 349 otherwise-qualified
stellar sources and re-routes 259 type-0/type-2 broad-line members.**
The pre-type broad-line total of 261 also includes two type-1 sources
excluded with the stellar classification. The pre-photometric-type
diagnostic cross-tab (19,419 sources) reconciles
exactly with the final booleans; it changes no eligibility. Evidence:
`coverage-baseline.md`; `specz_p2r05_sources.classification_label`,
`broad_line_reported`. *Closed question: S5-Q02/Q03; the excluded-star
count is documentation of selection, not evidence of misclassification.*

**S5-F07: Sensitivity is material; confidence changes membership in both
directions.** The confidence floor loses 3,877 primary members and gains
213 through dissolved vetoes, for a net loss of 3,664. The separate population
loses 109 and gains 39, for a net loss of 70. The tighter absolute tolerance
only loses members (1,410 primary, 188 separate); the normalized rule only
gains members on this hold (165 primary, 92 separate). Evidence:
`coverage-baseline.md` sensitivity tables. *Closed
question: S5-Q02 decides whether the 0.005 absolute baseline stands.*

**S5-F08 — Partitions are frozen, complete, and unbalanced by design.**
Zero unassigned sources; 4/4/12 tiles; no survey or outcome rebalancing.
Evidence: `tile-map.md`; `specz_p2r05_splits`. *Closed question: S5-Q04.*

**S5-F09 — Process finding: the run identity initially hashed diagnostic
modules.** A gate 5.7 diagnostics edit moved the run id of built
products; the identity was corrected to build-affecting modules and the
unsealed product was rebuilt once within the destructive-rebuild budget
(1 of 2 used). Attribution: implementation defect in this unit's canonical
module, not a spec defect; caught before any seal. Evidence: seal record
`recovery_history` in the run row. *Closed question: none.*

**S5-F10 — The upstream incompatibility is confirmed and reportable.**
The catalog's `id_specz_khostovan25` does not resolve against the held
DR1.1 compilation (24,364/37,219 coincidental resolutions; field-scale
geometry, median 4,054.3415558937 arcsec on the documented all-links
basis; value range consistent with an earlier release's renumbering,
which remains an unconfirmed hypothesis). Evidence:
[`upstream-report-draft.md`](upstream-report-draft.md). *Closed question:
S5-Q05.*

## Evidence errata (2026-10-04)

These corrections repair reporting and verification instructions. They do not
change the policy, installed product, seal, adoption state, or S5 questions.
Evidence is retained in `staging/2026-10-04-astra-p2r05-errata/` and indexed in
[the errata worklog](../../../work-logs/worklog-2026-10-04-p2r05-errata.md).

| Finding | Previous statement | Correction and reason |
|---|---|---|
| AR-F01 | Current verification command expected an unsealed candidate | Use explicit post-seal mode and the pinned run ID; the prior state predicate rejects a correctly sealed product |
| AR-F03 | Sensitivity was “one-sided per dimension” | Confidence 97 loses 3,877 primary / 109 separate and gains 213 / 39 as vetoes dissolve; net counts concealed membership changes in both directions |
| AR-F04 | 261 type-0/type-2 broad-line members rerouted | 259 eligible broad-line members (71 type 0 + 188 type 2); two further broad-line sources are type 1 and excluded, yielding 261 before type routing |
| AR-F04 | Catalog-wide veto/support figures could be read as secure-preferred attrition | 681 vetoed among 20,100 secure-preferred versus 722 catalog-wide; secure-preferred corroboration is 11,183 / 8,263 / 654 singly / multiply / conflicting |
| AR-F02 | Raw variant headline fields were zero despite nonzero membership changes | Gate 1 repaired the two counters; all three totals now reproduce the independently reconstructed table without changing eligibility predicates |

`gate1-sensitivity-comparison.json` checks totals and gains/losses against the
independent reconstruction. `gate3-document-counts.json` records the exact
SELECT queries for denominator and type/broad-line counts. All five acceptance
questions below remain byte-identical to the pre-errata document.

## Acceptance questions (all pending)

- **S5-Q01:** Accept the mechanically verified association and
  preferred-entry product as a reproducible input for subsequent approved
  work?
- **S5-Q02:** Adopt the baseline primary galaxy eligibility policy for the
  declared spectroscopic calibration/validation use, given its exclusions
  and sensitivity?
- **S5-Q03:** Adopt the separately labelled broad-line/photometric-QSO
  validation population for its declared diagnostic use?
- **S5-Q04:** Accept the frozen partitions and documented
  coverage/independence limitations for a subsequent modelling spec?
- **S5-Q05:** Authorize sending the prepared upstream incompatibility
  report through an operator-chosen channel?

No answer is filled by the executor. A mechanically successful run can
recommend declining any of these; the sensitivity table above is the
material input to S5-Q02, and the limitations section bounds S5-Q01/Q03/Q04.
The upstream draft is local and unsent pending S5-Q05.
