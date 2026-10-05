<!--
---
title: "T_A v2 Input Contract"
description: "Gate 6.1 record: S5 decision binding, interface boundary, inherited identities, explicit populations, and the per-field source-semantics inventory for the proposed T_A v2 design"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-10-05"
version: "1.0"
status: "Active - proposed, pending approval"
tags:
  - type: specification
  - domain: astronomy
  - domain: sed-fitting
  - domain: spectroscopy
  - tech: python
  - tech: postgresql
related_documents:
  - "[T_A v2 README](README.md)"
  - "[P2R-05 Review and S5 answers](../specz-science-p2r05/review.md)"
  - "[Input Identity Record](input-identity.json)"
---
-->

# T_A v2 Input Contract (Gate 6.1)

Status: `proposed_not_adopted`. This record binds the frozen inputs and Don's
recorded S5 decisions to the proposed T_A v2 design boundary. It creates no
science, fits nothing, and changes nothing outside this directory.

## 1. Authority and prerequisite verification

- Authorizing spec: P2R-06 v1.0, SHA-256
  `04bb896050114207491603f7fc08971b59be274501454532e5c7ed6e5f42ecf0`
  (central queue file hashed at dispatch; archive copy lands at closeout).
- Operator authority: Don, Action Registry `rec4acLZWCuN1tJk9`, 2026-10-05
  utterances 09:13 EDT "I dont see anything in your responses to veto." and
  09:15 EDT "Approved to execute."
- Prerequisite check (spec section 3): Don's S5 answers **are recorded on
  `main`** in `docs/research/specz-science-p2r05/review.md` under
  "## Acceptance questions (answered 2026-10-05)" (line 308 at base commit
  `01f28ee`). Each recorded answer matches the spec's section 3 table
  verbatim in substance. The lane proceeds.

## 2. S5 binding table

| S5 | Recorded answer (review.md locator at base `01f28ee`) | Scope consequence for this unit |
|---|---|---|
| Q01 | **Adopt** (line 321) | The input contract references the exact P2R-05 run `1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c` and its preferred-entry provenance fields in the optional redshift-diagnostic interface only. |
| Q02 | **Adopt with conditions** (lines 323–337) | The conditional galaxy redshift diagnostic uses the exact adopted primary mask (`eligibility_primary_galaxy` under the frozen run). All claims are conditional on the type-0, no-broad-line, secure-preferred, unvetoed selection. The 0.005 absolute baseline is kept; the three frozen sensitivity variants (confidence 97; absolute 0.001; normalized 0.005) are predeclared and reported, never used to choose a threshold from held-out results. No stellar-mass or SFR truth interpretation attaches to spec-z eligibility. The October 4 errata are carried (review.md "Evidence errata (2026-10-04)", line 287). |
| Q03 | **Adopt for separately reported diagnostics only** (lines 339–376) | POP-SPECZ-SEPARATE is designed as separate reporting by broad-line evidence strength and photometric-QSO label, with the 16 tentative-only broad-line cases (reproduction SQL and result at review.md lines 347–376) reported explicitly. No path from this population into primary fitting. No AGN/QSO object enters mass modelling by default. |
| Q04 | **Adopt with conditions** (lines 378–385) | The frozen P2R-05 tile partitions (`analysis.specz_p2r05_splits.assigned_split`) are reused as the evaluation split. Preprocessing, centers, scales, supports and hyperparameters are fitted on development only; validation compares declared choices; holdout runs once after the contract is frozen; uncertainty is clustered by tile and survey; no rerolling or rebalancing; independence from upstream spectroscopic calibration is stated as unestablished. Written into gate 6.4. |
| Q05 | **Sending the corrected upstream report is authorized; channel is Don's choice** (lines 387–392) | Traceability only. No dependency edge enters this unit; this unit transmits nothing. |

Recorded answers govern. No run-status change in `analysis.specz_p2r05_runs`,
no adopted-state alias, no database transition: adoption authorizes downstream
design under the recorded conditions only (review.md lines 394–398).

## 3. Interface boundary

| Interface | State | Rule |
|---|---|---|
| `data/dictionary/columns-v11.csv` (tracked, sealed dictionary) | **Included (read-only)** | Sole field-semantics authority for source-mirror columns. |
| `docs/reference/unit-conventions.md` | **Included (read-only)** | Sole log10/linear conversion authority. SHA-256 `8a4d3a724ba435fe5668260e50be45c41f067214567a8723d27d004d3df9ca4a` equals the `semantic_note_source_sha256` pinned in the dictionary rows it annotates. |
| `cosmos2025_v11.source` mirror columns inventoried in section 5 | **Included (SELECT-only)** | Analyst role `cosmos2025_v11_ro` via the fixed `PGSQL01_COSMOS2025_V11_*` handoff names; connection-time read-only. Schema/semantic inspection for this contract only; no feature generation. |
| `cosmos2025_v11.analysis.specz_p2r05_*` (sealed product) | **Included (SELECT-only)** | Read through the same analyst path; never modified; run identity pinned to `1e604a81...`. |
| `cosmos2025.catalog` v1 baseline | **Excluded** | Historical evidence only. The May/July frozen inputs (section 6) already summarize it; no diagnostic is rerun against it. |
| Raw holdings `/mnt/nvme01/**`, PDFz pickle, SED archives | **Excluded** | No image-level or SED-level analysis; dictionary profiles are the semantic evidence; no manifest refresh. |
| Any database write, source re-export, calibration run, upstream contact, infrastructure change | **Blocked (stop condition)** | Encountering a need for one stops the lane and is recorded, per spec section 7. |

## 4. Inherited identities (recorded, not refreshed)

Recorded from tracked documents at base `01f28ee`; compared by content, never
regenerated. A mutated identity in any scratch copy of this contract is
rejected, not overwritten (enforced by the gate 6.3 validator).

| Identity | Value | Source of record |
|---|---|---|
| P2R-05 run id | `1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c` | review.md product-identity table |
| P2R-05 policy | `p2r05-specz-policy-v1`; config `configs/specz_science_policy_v1.yaml`, SHA-256 `fb6daa4fbbe6c61e8bfdc567147bf1317b99711926e10436014d768a6ae370ed` (tracked file hash; the run row's semantic digest is the authoritative in-database value and is not restated here) | review.md; dispositions record |
| P2R-05 authorizing spec | v1.0, SHA-256 `7f481111ad826dd80b01106eeec71bfdaf0f5c649c0cc79b8661a0087af2757b` | review.md; dispositions record |
| P2R-05 input snapshot manifest | SHA-256 `06b19654fc715106ba1f788b52e084df1e94043343517f2b8a49fd44abfff7a4` | review.md product-identity table |
| Frozen tile map (P-06) | canonical digest `c6406d37e32e4b5cfeb89fc91cda0eb9ed4abf0a192d8c5ab7e56fb893635937`; 4 holdout (A1, A7, B3, B7) / 4 validation (A3, A10, B1, B5) / 12 development tiles | `tile-map.md` |
| Sealed v1.1 dictionary | `data/dictionary/columns-v11.csv`, SHA-256 `324d3ea17b23a57223d84043559b8fa94c87c95c4710b3719f31358cd881e8b8` | tracked file hash at gate 6.1 |
| Raw v1.1 manifest (tracked layer) | `docs/reference/data-manifest-v1.1.md` SHA-256 `a0b3e31cd973317dfffd178d2cd841213a07a25e5565405911f2836133c3b139`; machine CSV SHA-256 `5941abbbcde4e27d706ec1a49456482cb779f9c77e6cf573b7313a0450ee4c7e` | tracked file hashes; raw-holding pins are **not** re-derived |
| Base commit | `main` at `01f28ee06383a4db9b44d8e6ef7125ea6ed722d9` | git |

Independent adoption review (ML01-local, gitignored):
`staging/2026-10-04-astra-p2r05-adoption/adoption-review.md`, SHA-256
`79d1fe50fab57625636474f0da184dccdd5b0444c39b6f027785fb78f1a90b72`. Numbers
used from it in this design, stated inline: the primary sample is 18,402 of
784,016 sources; 90.80% of the primary sample lies in F444W [15,24) against
12.22% of the catalog. Every such number is also carried by, or consistent
with, the tracked review surface (18,402 and 784,016 verbatim in review.md;
the magnitude-concentration figures summarize `coverage-baseline.md`'s
F444W-magnitude reporting, whose per-population tables are the tracked
authority); the adoption review is never the sole support for a claim.

## 5. Proposed input field inventory

Every proposed input exists by exact `source.table.column` name with
dictionary or source-description evidence. "Sentinel evidence" distinguishes
documented sentinels (none for these rows), profiler-flagged candidate
sentinels, and undocumented finite values. Only FITS masks and NaN are SQL
NULL in the mirror; finite sentinels remain source values.

### 5.1 Physical-parameter inputs

| # | Exact column | Native quantity | Unit / representation | Uncertainty meaning | Sentinel / NULL evidence | Censoring limits |
|---|---|---|---|---|---|---|
| 1 | `source.lephare.mass_med` | log stellar mass, median of the probability distribution (BC03 best-fit template) | `Msol`, **log10** (semantic note) | posterior quantile summary; `mass_l68`/`mass_u68` give the 68% interval | no documented or candidate sentinel; undocumented finite `-99.9` occurs 2,330× (profile top value); NaN 0 | none documented |
| 2 | `source.lephare.mass_l68` | lower 68% confidence limit | `Msol`, log10 | quantile | as row 1 (`-99.9` 2,330×) | none |
| 3 | `source.lephare.mass_u68` | upper 68% confidence limit | `Msol`, log10 | quantile | as row 1 | none |
| 4 | `source.lephare.sfr_med` | log SFR, median of PD | `Msol yr-1`, log10 | quantile (`sfr_l68/u68`) | `-99.9` 2,330×; NaN 0 | none |
| 5 | `source.lephare.sfr_l68` | lower 68% limit | `Msol yr-1`, log10 | quantile | as row 4 | none |
| 6 | `source.lephare.sfr_u68` | upper 68% limit | `Msol yr-1`, log10 | quantile | as row 4 | none |
| 7 | `source.lephare.ssfr_med` | log sSFR, median of PD | `yr-1`, log10 | quantile (`ssfr_l68/u68`) | `-99.9` 2,330×; NaN 0 | none |
| 8 | `source.lephare.ssfr_l68` | lower 68% limit | `yr-1`, log10 | quantile | as row 7 | none |
| 9 | `source.lephare.ssfr_u68` | upper 68% limit | `yr-1`, log10 | quantile | as row 7 | none |
| 10 | `source.cigale.mass` | stellar mass | `M_sol`, **linear** (semantic note) | symmetric linear error `mass_err` (shape undocumented) | NaN→NULL 139,661 (17.81%); finite negatives exist (profile min ≈ −1.52e12); no sentinel evidence | none documented |
| 11 | `source.cigale.mass_err` | error in stellar mass | `M_sol`, linear | symmetric 1σ-like summary; distribution shape undocumented | NaN→NULL 17.81%; min ≈ 1.25e-12 > 0; zeros not in top values but nonnegativity is not documented | none |
| 12 | `source.cigale.sfr_inst` | current SFR | `M_sol/yr`, linear | symmetric linear `sfr_inst_err` | NaN→NULL 17.81%; finite negatives (min ≈ −5,509.25); exact `0.0` occurs (26) | none documented |
| 13 | `source.cigale.sfr_inst_err` | error in current SFR | `M_sol/yr`, linear | as row 11 | min 0.0 (26 occurrences of 0.0 in top values) | none |
| 14 | `source.cigale.sfr_100myr` | SFR over last 100 Myr (lbt) | `M_sol/yr`, linear | symmetric linear `sfr_100myr_err` | NaN→NULL 17.81%; finite negatives (min ≈ −2,180.80); exact `0.0` occurs (26) | none documented |
| 15 | `source.cigale.sfr_100myr_err` | error in sfr_100myr | `M_sol/yr`, linear | as row 11 | min 0.0 | none |

Representation and conversion authority: rows 1–9 are log10 and rows 10–15
linear per `docs/reference/unit-conventions.md` section 1 and the dictionary
semantic notes; unit labels alone do not make the distinction (descriptions +
conventions do).

**Unsupported semantics declared at the input layer:**

- **No genuine censoring limits exist in the source metadata.** No row above
  carries a documented upper/lower limit, detection threshold, or
  censoring flag. A `upper_limit_supported` state is therefore unreachable
  on this catalog; any bound-aware branch stays unscored/context-only
  (gate 6.2; TA2-Q03 asks Don whether that reduced scope is acceptable).
- **CIGALE error distributions are shapeless summaries.** `*_err` values are
  documented only as "Error in X". The first-order dex error
  `err/(value·ln10)` is an approximation with a declared domain (gate 6.2),
  never a distributional claim.
- **LePhare SFR timescale is undefined in the source descriptions.** Both
  `sfr_med − log10(sfr_inst)` and `sfr_med − log10(sfr_100myr)` are
  definitional comparisons against a LePhare summary whose integration
  window is not documented as either CIGALE timescale.
- **No CIGALE sSFR column exists in v1.1.** The dictionary contains zero
  `ssfr` rows for `cigale` (the v1-era extraction-time `ssfr_cigale` is not
  a v1.1 field). Any sSFR quantity is derived under a declared algebraic
  coupling to the mass and SFR quantities (gate 6.2).

### 5.2 Fit-quality and classification context

| # | Exact column | Quantity | Evidence | Role in v2 |
|---|---|---|---|---|
| 16 | `source.lephare.chi2_best` | minimum χ² of the best-fit galaxy template (total; dof basis undocumented) | dictionary, verified | context output only; never a predictor or normalization |
| 17 | `source.cigale.chi2_best_fit` | χ² of the best-fit model (total) | dictionary, verified | context output only |
| 18 | `source.cigale.chi2_red_best_fit` | reduced χ² of the best-fit model (dof basis undocumented) | dictionary, verified | context output only |
| 19 | `source.lephare.nbfilt` | number of filters used in the LePhare fit | dictionary, verified | information-content context only; recovering dof from it is forbidden |
| 20 | `source.lephare.type` | LePhare classification {0 galaxy, 1 star, 2 qso} | dictionary, verified | explicit, recognized selection input |

The historical `chi2_ratio` (LePhare total over CIGALE reduced) is excluded
from outputs and predictors (gate 6.2); no raw-over-raw substitute and no
dof reconstruction from `nbfilt` enters any formula.

### 5.3 Covariates (proposed, development-only use)

| # | Exact column | Quantity | Evidence | Status |
|---|---|---|---|---|
| 21 | `source.lephare.zpdf_med` | photo-z, median of the zPDF | dictionary, verified; no candidate sentinel | recommended redshift covariate |
| 22 | `source.lephare.zfinal` | final photo-z estimate (median of likelihood for galaxies); **documented semantic**: set to 0 for stars and artifacts | dictionary, verified; candidate sentinel `-99.0` × 92,226 (11.76%) | identified alternative; excluded from the recommended set because of the documented zero semantic and the candidate sentinel |
| 23 | `source.photometry_primary.mag_auto_f444w` | AB auto magnitude, F444W | dictionary, verified (unit cell `unknown`; AB mag from description text) | brightness covariate/stratum context |

No individual mass or SFR estimate from either code is a permitted
centering covariate (coupling disclosure and the alternative that admits one
are in gate 6.2).

### 5.4 Spectroscopic diagnostic interface inputs (S5-bound)

| # | Exact column | Quantity | Source of record |
|---|---|---|---|
| 24 | `analysis.specz_p2r05_sources.run_id` | sealed run identity | derived schema contract |
| 25 | `analysis.specz_p2r05_sources.catalog_id` | join to `photometry_primary.id` | derived schema contract |
| 26 | `analysis.specz_p2r05_sources.eligibility_primary_galaxy` | adopted primary mask (Q02) | derived schema contract |
| 27 | `analysis.specz_p2r05_sources.eligibility_separate_validation` | separate labelled population (Q03) | derived schema contract |
| 28 | `analysis.specz_p2r05_sources.broad_line_reported` | broad-line evidence label | derived schema contract |
| 29 | `analysis.specz_p2r05_sources.photometric_qso` | photometric-QSO label | derived schema contract |
| 30 | `analysis.specz_p2r05_sources.preferred_reported_z` (+ `preferred_flag`, `preferred_confidence`, `preferred_entry_is_secure`, `preferred_tied_ids`) | preferred-entry redshift and provenance (Q01) | derived schema contract |
| 31 | `analysis.specz_p2r05_sources.classification_label` | carried photometric type label | derived schema contract |
| 32 | `analysis.specz_p2r05_splits.assigned_split` | frozen P-06 partition (Q04) | derived schema contract + tile map |

All 24–32 are SELECT-only, run-pinned to `1e604a81...`, and feed **only** the
redshift-diagnostic interfaces and the evaluation protocol; none is a
denominator for, or feature of, non-spectroscopic mass modelling.

## 6. Explicit populations

All population predicates are `proposed_not_adopted`. Populations are
grain-aligned at one row per `photometry_primary.id` and are **not**
nested: membership in one implies nothing about another unless stated.

| Population | Proposed predicate | Explicit notes |
|---|---|---|
| `POP-MASS` (mass comparison) | `lephare.type = 0` **and** `mass_med` state = `point_valid` **and** CIGALE mass state = `point_valid` (linear `mass` present, finite, > 0, error present and ≥ 0) | Requires **no** SFR state. Type 0 is an explicit, recognized LePhare-classification selection; sources of other types are audit-only. |
| `POP-SFR-INST` | `POP-MASS` inputs not required; `lephare.type = 0` and `sfr_med` = `point_valid` and `sfr_inst` path state = `point_comparable` | Per-timescale; independent of mass membership. |
| `POP-SFR-100` | same with the `sfr_100myr` path state = `point_comparable` | Per-timescale; a source may sit in exactly one, both, or neither SFR population. |
| `POP-SPECZ-PRIMARY` | `specz_p2r05_sources.eligibility_primary_galaxy IS TRUE` under run `1e604a81...` | Diagnostic interface only (Q02 mask). Never a denominator of non-spectroscopic mass modelling; conditional claims only. |
| `POP-SPECZ-SEPARATE` | `eligibility_separate_validation IS TRUE` under the same run | Separately reported by broad-line strength and photometric-QSO label; 16 tentative-only broad-line cases reported explicitly (Q03); no primary-fitting path. |
| `POP-AUDIT` | every catalog source not scored above | Retained unscored with reasons; includes type-1/2 sources, non-positive-mass sources, and all undefined/censored/unsupported states. |

Denominator rules: `POP-MASS`, `POP-SFR-*` denominators are their own
memberships over `lephare.type = 0` (selection reported, never hidden).
Spectroscopy availability never enters any non-spectroscopic population's
denominator. A synthetic source with valid masses and undefined or censored
SFR enters `POP-MASS` and no SFR population (fixture FX-03, gate 6.3).

## 7. Frozen design inputs (restated, not re-diagnosed)

From `docs/project-state.md` section 1, carried as frozen inputs: the
~0.24 dex conditional cross-code mass offset (historical unconditional
`t_mass` mean −1.001, `sigma_sys_mass` = 0.1 dex per the May report
`docs/phase2-tension-diagnostic-report.md`); the censoring-dominated SFR
tension ranking (analysis sample gated `sfr_inst > 0 AND sfr_100myr > 0`;
bulk `t_sfr_100` mean 0.302 / std 0.980 not a validated tail-ranking
distribution); the dimensionally incoherent historical `chi2_ratio`. None is
re-derived, re-voted, or treated as a test here.

## 8. Planned read set (gate 6.1 validation)

The planned reads for the entire unit are: the tracked repository documents
named in this contract; SELECT-only schema/semantic inspection of the
columns in section 5 where a live check is needed; and the sealed P2R-05
analysis tables under the pinned run. The read set contains **no** v1
diagnostic rerun, **no** observed mass or SFR residual computation, **no**
holdout outcome, and **no** raw-manifest refresh. Any unavoidable violation
of that set is a stop condition.

## 9. Identity handling rule

Pins and identities in this contract and in `input-identity.json` are
compared by content. If a scratch copy of this contract carries an
intentionally changed ID or digest, the validator (gate 6.3) rejects the
copy with a named reason; it never overwrites the recorded identity.
