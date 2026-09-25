<!--
---
title: "Gate 5.7 Coverage, Attrition, and Sensitivity Evidence"
description: "Baseline coverage with explicit predicates and denominators, source attrition and conflict provenance, the pre-photometric-type diagnostic, and the three fixed sensitivity comparisons for the P2R-05 product"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-22"
version: "1.0"
status: "Active"
tags:
  - type: research
  - domain: astronomy
  - domain: spectroscopy
  - domain: data-engineering
related_documents:
  - "[P2R-05 README](README.md)"
  - "[Frozen Tile Map](tile-map.md)"
---
-->

# Gate 5.7: Coverage, Attrition, and Sensitivity Evidence

Reproduction commands (repository root):

```
python src/features/specz_science/coverage.py
python src/features/specz_science/check_installed_independent.py
doppler run --project ml01 --config dev -- \
    python src/features/specz_science/negative_controls.py
```

Product identity of record: run
`1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c` in
`cosmos2025_v11.analysis` (full content digests in the run row and in
`staging/derived/specz-p2r05/products/finalize-summary.json`).

## Source accounting (denominator: 784,016 catalog sources)

Mutually exclusive summary states under the approved baseline:

| State | Predicate | Sources |
|---|---|---:|
| primary_galaxy | secure preferred entry, no veto, valid split, LePHARE type 0, no broad-line evidence | 18,402 |
| separate_validation | secure preferred, no veto, valid split, type in {0,2}, broad-line reported or photometric QSO | 668 |
| conflict_vetoed | either P-04 veto flag set (evaluated before routing) | 722 |
| no_secure_preferred | not vetoed and preferred entry absent or not secure | 763,875 |
| classification_routed_out | secure, unvetoed, valid split, routed out by type (all LePHARE type 1) | 349 |
| **Total** | | **784,016** |

Within the 668 separate-validation members the distinct labels stay
distinguishable: 259 carry spectroscopic broad-line evidence (71 type 0,
188 type 2) and 409 are photometric-QSO-only (LePHARE type 2 without a
broad-line report). No member is called a confirmed AGN on this evidence.

Overlapping exclusion reasons (a source may carry several; these are not
additive attrition): no_association 737,977; no_broad_line_or_qso 777,901
(this is the dominant reason because nearly all catalog sources have no
spectroscopy at all); photometric_type_stellar 17,374;
preferred_flag_not_in_secure_domain 17,622; no_numeric_valid_unique 7,285;
population_a_no_unique 1,032; secure_all_conflict 671;
unique_numeric_conflict 57; broad_line_evidence_present 426.

Attrition with explicit denominators: of 46,039 sources reached through
`_all`, 45,007 carry `_unique` entries; 20,100 carry a secure preferred
`_unique` entry (P-02/P-03 predicates over distinct sources); 722 are
vetoed by P-04; 18,402 and 668 finalize into the two secure-use
populations after P-05 routing and the P-06 split gate. Of the 20,100
secure-preferred sources, 11,490 are singly supported and 8,357 multiply
supported (agreement among secure `_all` measurements); 671 carry
conflicting secure alternatives.

## Pre-photometric-type diagnostic (P-07)

`spectroscopy_qualified_before_photometric_type` (resolved association,
secure preferred `_unique` entry, neither veto, valid tile): **19,419**,
reproducing the authoring prior. Cross-tabulation by observed LePHARE type
and broad-line reporting:

| LePHARE type | broad_line_reported | no_broad_line_report | Total |
|---|---:|---:|---:|
| 0 | 71 | 18,402 | 18,473 |
| 1 | 2 | 347 | 349 |
| 2 | 188 | 409 | 597 |
| missing/other | 0 | 0 | 0 |
| **Total** | **261** | **19,158** | **19,419** |

This is exclusion accounting. It cannot change either eligibility boolean,
is not an adopted sample, and does not establish that excluded stars or
QSOs were misclassified: primary-membership claims are conditioned on the
selected LePHARE-classified population.

## Entry-level distributions (denominator: audited `_all` entries)

Numeric-valid entries: 420,362 of 482,579. Survey distribution over those
entries is dominated by a few programs (top survey ids by entry count: 38
with 184,275, 37 with 83,230, 39 with 45,578, 115 with 27,430), i.e.
survey imbalance is material. Confidence distribution over numeric-valid
entries: 97 (258,018), 95 (14,891), plus 85, 80, 50, 0, 90, and -99
categories all present; flag distribution includes every observed category
including unrecognized values (full per-category tables in
`coverage-5-7.json`). These are descriptive of the compilation's
selection, not of the photometric catalog: spectroscopy coverage is
46,039/784,016 = 5.87 percent of sources, and no claim of
representativeness over unobserved photometric populations is made.

## Photometric and spatial coverage

Tile coverage: all 20 documented labels present; per-tile source counts
and partition assignments in the tracked tile map. Partition source
totals: development 476,137, validation 147,721, holdout 160,158,
unassigned 0.

F444W magnitude and F150W-F277W color are reported for the full catalog,
the primary-galaxy population, and the separate-validation population,
with native-missing, non-finite, underflow/overflow, and
`color_not_evaluated_display_domain` bins retained separately (bin edges
declared in the policy configuration; the display domain is a derived
diagnostic rule, not a claim that outside values are source sentinels —
two finite unfit magnitudes cannot manufacture an ordinary color here).
Full-catalog native-missing inputs: 25,255 sources for F444W magnitude
and 30,856 for the color pair; per-population tables are in
`coverage-5-7.json`; for example the primary-galaxy color distribution
concentrates in [0,1) with 13,948 of 18,402 members and 5 members carry
native-missing inputs.

## Sensitivity variants (three fixed, no winner chosen)

Each variant changes exactly its declared dimension, retains baseline
preferred-row ordering, and shares the frozen partitions:

| Variant | Changed dimension | Primary galaxy | vs baseline | Separate validation | vs baseline |
|---|---|---:|---|---:|---|
| Baseline | — | 18,402 | — | 668 | — |
| min_confidence_97 | confidence floor 95→97 | 14,738 | -3,664 net (-3,877 lost, +213 gained) | 598 | -70 (-109 lost, +39 gained) |
| abs_threshold_0p001 | absolute tolerance 0.005→0.001 | 16,992 | -1,410 (all losses) | 480 | -188 (all losses) |
| normalized_0p005 | pairwise d = abs(z_i-z_j)/(1+min(z_i,z_j)) > 0.005 | 18,567 | +165 (all gains) | 760 | +92 (all gains) |

Membership-change reasons: every min_confidence_97 loss is
`preferred_entry_left_secure_domain` (confidence in [95,97)); every gain is
`conflict_veto_resolved_under_variant` (one member of a conflicting secure
pair drops below the stricter floor, dissolving the secure pair). Every
abs_threshold_0p001 change is `new_conflict_veto`. Every normalized_0p005
change is `conflict_veto_resolved_under_variant` (normalized disagreement
falls at/below the threshold at the redshifts involved). These are
diagnostic alternatives, not parallel adopted samples.

## Independent verification and negative controls

- `check_installed_independent.py`: 784,016 source rows and 482,579
  measurement rows verified against independent restatements from the
  captured native input — preferred entries and values, conflict flags,
  association statuses and resolved ids, secure predicates, split
  assignments, both eligibility booleans, and full exclusion-reason sets.
- `negative_controls.py` (guarded scratch databases, real artifacts, one
  tamper each): removing an exclusion category, altering a source
  association, promoting a population-A entry to preferred, erasing a
  secure conflict, switching a tied preferred entry, and moving a source
  between splits are each caught on the intended invariant
  (`negative-controls-5-7.json` records the exact catch per control).
- No photo-z residual, stellar-mass tension, SFR ranking, fitted
  correction, anomaly score, or held-out outcome performance was computed
  anywhere in this unit.
