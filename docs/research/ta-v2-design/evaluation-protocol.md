<!--
---
title: "T_A v2 Evaluation Protocol"
description: "Preregistered development, validation, and holdout plan for a future T_A v2 implementation: split-use rules, declared model choices, strata, sensitivity plan, clustered uncertainty, and support policy (gate 6.4)"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-10-05"
version: "1.0"
status: "Active - proposed, pending approval"
tags:
  - type: specification
  - domain: astronomy
  - domain: data-science
  - domain: spectroscopy
related_documents:
  - "[Feature Contract](feature-contract.yaml)"
  - "[Input Contract](input-contract.md)"
  - "[Review Surface](review.md)"
---
-->

# T_A v2 Evaluation Protocol (Gate 6.4)

Preregistered before any implementation, fitting, or outcome computation.
**No outcome metric is computed in this unit**, and nothing below may be
read as a result. The design-stage data exposure that precedes this
protocol is disclosed in [exposure-log.md](exposure-log.md) (P2R-06a gate
A1.1): design was informed by full-catalog summaries containing holdout
information, so the eventual holdout assessment below is **not an
untouched test of feature-family selection**, and no claim in this
protocol asserts an unexposed holdout or zero historical outcome-derived
exposure. Future parameters are fitted on development only. This protocol
distinguishes two surfaces that must never share a denominator:

1. **Non-spectroscopic disagreement characterization** (POP-MASS,
   POP-SFR-*): cross-code behaviour over the photometric catalog.
2. **Redshift diagnostics** (POP-SPECZ-PRIMARY, POP-SPECZ-SEPARATE):
   photo-z behaviour assessment under the adopted P2R-05 mask.

A secure spec-z can assess a photo-z relationship; it cannot decide which
stellar mass or SFR is true, establish a causal source of mass tension, or
independently validate both codes' shared redshift assumptions (CIGALE
redshifts are fixed to LePhare solutions in the published methodology).
Spectroscopy availability is never a denominator or feature of surface 1.

## 1. Split use (S5-Q04 conditions, binding)

The frozen P2R-05 partitions (`analysis.specz_p2r05_splits.assigned_split`,
run `1e604a81...`; tile map digest `c6406d37...`; 4 holdout tiles A1, A7,
B3, B7 / 4 validation A3, A10, B1, B5 / 12 development) are reused as the
evaluation split.

| Split | Permitted use | Forbidden use |
|---|---|---|
| development | preprocessing, center fitting (C0/C1 parameters), scale determination (`sigma_sys_*`), support definitions, hyperparameters, bin edges | any outcome claim |
| validation | comparison among **declared** choices only (section 2); tie-breaks fixed in writing before any outcome is seen | new choices invented after seeing outcomes |
| holdout | one evaluation, once, after the contract and artifact identities below are frozen | rerolling, rebalancing, row-random fallback, second attempts |

Enforced synthetically by the gate 6.3 validator (fit requests FX-P1..P4:
validation/holdout IDs in a fit request rejected; one source cannot sit in
two partitions or as duplicate training rows; mutation M3 caught).

## 2. Declared model choices (the complete comparison set)

The implementation unit may compare exactly:

- mass center: `C0-constant` vs `C1-conditional-binned-median`
  (covariates, binning, support rule, and extrapolation as declared in
  feature-contract.yaml `centers.mass_center`; no other covariate set);
- SFR centers: `S0-constant` per timecale;
- scales: the declared quadrature with `sigma_sys_*` set by the
  robust-spread rule on development residuals;
- joint mass-SFR candidate pair (P2R-06a A1.7, decision 4): for each
  timescale T, `joint_residual_distance_T` (fitted winsorized covariance
  `C_b,T`) and `score_joint_T` (fitted correlation `R_b,T` on
  standardized residuals), both under the
  `winsorized-median-covariance-v1` estimator with the
  `joint_rho_clamp` regularization — **declared comparison candidates
  requiring later adoption (TA2-Q07), not automatic candidate-selection
  channels**. No combined ranker, maximum, union, quota, selection
  budget, low-correlation veto or automatic disable exists, and none may
  be added without a new approval. The marginal surfaces (A1.2/A1.3)
  are unchanged by the pair's presence. The raw full-catalog
  correlation in exposure-log CQ5 (about -0.30, uncentered, censored
  regime included) is neither a parameter nor a bound for anything in
  this protocol;
- state-machine constants (`sfr_floor_k = 1.0`, approximation domain 0.3,
  log-domain bounds): **not** choices — they are contract constants whose
  alteration is an approval question (TA2-Q02/Q03), not a tuned
  hyperparameter.

Tie-break rule (fixed now, before any outcome): if validation cannot
separate C0 from C1 under the predeclared comparison metric, select
**C0-constant** (the simpler model). If validation separates them, select
by the predeclared metric on development-conditioned residuals only. The
predeclared comparison metric for centers is the development-fitted,
robust-spread-normalized median absolute residual on validation-tile
POP-MASS members, reported with tile- and survey-clustered uncertainty;
no ranking-based metric enters model choice.

## 3. What is fitted, where

| Quantity | Fitted on | Carried identity |
|---|---|---|
| C0/C1 center parameters (edges, cell values, constants) | development only | `center_model_id` |
| `sigma_sys_mass_dex`, `sigma_sys_sfr_inst_dex`, `sigma_sys_sfr_100_dex` | development only | `scale_model_id` |
| score computation | nothing fitted | contract formulas |
| state machines and domain constants | nothing fitted | contract version |

No observed residual, ranking, or holdout outcome feeds back into any of
these (gate 6.2 constraint, enforced by design: the validator rejects
held-out fit IDs synthetically and the contract forbids outcome-dependent
covariates).

## 4. Strata (descriptive reporting, both surfaces)

Reported for every population and split: redshift (`zpdf_med` bins),
magnitude (`mag_auto_f444w` bins), colour (F150W−F277W, following the
P2R-05 coverage practice with native-missing and non-finite bins kept
separate), survey (spectroscopic compilation survey id, spec-z surfaces
only), and support stratum (cell / z_fallback / global_fallback /
out_of_hull; point_comparable / floor / nonpositive / missing /
invalid for SFR paths). Strata describe composition; they never redefine a
population.

## 5. Sensitivity plan (S5-Q02 conditions)

The three frozen one-factor P2R-05 variants — confidence floor 97
(14,738 primary), absolute tolerance 0.001 (16,992), normalized 0.005
(18,567) against the baseline 18,402 — are **predeclared** and reported
with every redshift-diagnostic result. They are never used to choose a
threshold, a center, a scale, or a favourable holdout outcome. The 0.005
absolute baseline is retained.

## 6. Uncertainty plan

- Clustered uncertainty by tile and survey for every reported aggregate;
  the four holdout tiles (A1, A7, B3, B7) are acknowledged as the entire
  holdout cluster set — no claim may treat holdout sources as independent
  draws beyond those clusters.
- Independence from upstream spectroscopic calibration is **unestablished**
  and stated wherever a spec-z-stratified number appears (P2R-05
  limitation, carried forward).
- `score_mass` / `score_sfr_*` are normalized residuals, not calibrated
  significances; any significance language requires a new approval.

## 7. Support policy

Lack of support yields an explicit unsupported claim or stratum, never
weighted extrapolation presented as coverage. Specifically: center cells
below the 200-member support shrink (z_fallback → global) with
`center_support` emitted; SFR paths that are not `point_comparable` stay
unscored with reasons; `score_ssfr_*` stays `unsupported_correlated_errors`;
the `upper_limit_supported` state stays unreachable pending bound
semantics and Don's reduced-scope decision (TA2-Q03).

## 8. Separate labelled diagnostics (S5-Q03 conditions)

POP-SPECZ-SEPARATE is reported only with its own denominator, split by
`broad_line_reported` (with evidence strength: secure broad-line
measurement vs tentative-only) and `photometric_qso` labels kept distinct.
The 16 tentative-only broad-line cases (review.md of P2R-05, S5-Q03 SQL
and result) are listed explicitly in any report that touches that
population. No member of this population enters primary fitting or mass
modelling by default.

## 9. Descriptive vs model-affecting comparisons

| Comparison | Class |
|---|---|
| Stratum composition (section 4) | descriptive only |
| Sensitivity variants (section 5) | descriptive only |
| Separate-labelled diagnostics (section 8) | descriptive only |
| C0 vs C1 center selection (section 2) | **model-affecting** (development fit, validation selection, holdout once) |
| Joint candidate pair adoption (sections 2, 10) | **approval-gated** (TA2-Q07); criteria predeclared, no automatic selection |
| `sigma_sys_*` determination | **model-affecting** (development only) |
| Any state-machine constant | approval-gated, never tuned |

## 10. Joint-candidate evaluation criteria (predeclared, A1.7)

The joint mass-SFR pair is evaluated on three separated criteria, fully
specified here before any validation data are read:

1. **Mathematical correctness (synthetic).** Proven by the gate-A1.7
   kernel checks, estimator fit checks, and evaluator fixtures; already
   green in `validation-results.json`.
2. **Stability (development tile jackknife).** For each timescale, the
   development tiles are dropped one at a time; the reported summaries
   are the per-tile changes in the fitted cell correlations, the count
   of cells crossing the clamp or falling to a fallback level, and the
   fraction of development sources whose support level changes. Tile
   jackknife estimates are development-only.
3. **Usefulness (validation-tile description).** On validation tiles,
   the joint surfaces are described compositionally: what the pair adds
   beyond the marginal surfaces, including composition by support state,
   quantile, and floor conditions, and coverage (the fraction of
   POP-MASS ∩ POP-SFR-T members with a finite surface). Description
   only; no selection occurs at this level.

No criterion may reward elliptical distance by construction. For any
top-K overlap description between joint and marginal rankings, K and the
tie handling (lexicographic by catalog_id) are fixed in the approved
future protocol before any ranking is viewed; no budget or quota is
adopted here. Absent spectroscopic survey labels cannot become a
requirement for the non-spectroscopic sample. Evidence against adoption
(covariance masking of rare populations living along the fitted major
axis — fixture KERNEL-3; pooled-correlation distortion — POOLED-1/2) is
stated for Don's review rather than resolved by an automatic threshold.

## 11. Holdout freeze checklist (before the single holdout evaluation)

1. This protocol and feature-contract.yaml bytes frozen (SHA-256 recorded).
2. `center_model_id` and `scale_model_id` selected on development and
   validation per sections 1–2, identities recorded.
3. Fixture suite green; validator exit 0.
4. All strata and sensitivity reports for development and validation
   published inside the implementation unit's evidence.
5. Holdout tiles read once, for the predeclared metric set only; results
   published as-is, including unsupported strata.

## 12. Non-goals

No production calibration, database installation, candidate list, release,
or upstream contact occurs under this protocol; each is a separate named
approval. Nothing in this protocol authorizes treating a spec-z as mass
truth or pooling POP-SPECZ-SEPARATE into primary fitting.
