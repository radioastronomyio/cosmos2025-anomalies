<!--
---
title: "T_A v2 Scientific Design"
description: "Rationale, identified alternatives, and limitations for every scientific choice in the proposed T_A v2 feature contract (gate 6.2)"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-10-05"
version: "1.0"
status: "Active - proposed, pending approval"
tags:
  - type: specification
  - domain: astronomy
  - domain: sed-fitting
  - domain: feature-engineering
related_documents:
  - "[Feature Contract](feature-contract.yaml)"
  - "[Input Contract](input-contract.md)"
  - "[Scientific Design alternatives and the review surface](review.md)"
---
-->

# T_A v2 Scientific Design (Gate 6.2)

Every choice below is `proposed_not_adopted` and carries: rationale,
identified alternative, limitation, and the approval question that disposes
it. Nothing is fitted here; no observed catalog residual, ranking, or
outcome appears anywhere in this unit.

## 1. Stance

The three frozen inputs are design drivers, not hypotheses to re-test:
(a) a ~0.24 dex conditional cross-code mass offset (unconditional historical
`t_mass` mean −1.001 with `sigma_sys_mass` 0.1 dex);
(b) SFR rankings dominated by censoring near the positivity boundary
(historical bulk `t_sfr_100` mean 0.302 / std 0.980 despite nominal bulk
statistics);
(c) the dimensionally incoherent historical `chi2_ratio`
(LePhare total χ² over CIGALE reduced χ²).
The design answers each input with a structural response and at least one
failure case (section 7); it never re-derives them.

## 2. Populations

**Rationale.** Mass disagreement is measurable whenever both mass summaries
are defined, regardless of SFR; SFR disagreement exists per timescale with
its own validity; spectroscopic populations serve redshift diagnostics only.
Separate populations prevent the historical failure where the analysis
sample silently required `sfr_inst > 0 AND sfr_100myr > 0` and thereby made
SFR censoring a hidden selection on the mass population.

**Identified alternative.** A single master analysis sample with NULL
features for undefined paths (the v1 structure). Rejected as primary because
it invites positivity-only master samples (a forbidden pattern) and hides
denominators.

**Limitation.** `lephare.type = 0` is itself a photometric classification by
the very pipeline being compared; every population claim is conditional on
that selection (mirroring the P2R-05 limitation). The type-1/2 and
unknown-type sources stay in POP-AUDIT, unscored, with reasons.

**Approval.** TA2-Q01.

## 3. Mass disagreement

### 3.1 Raw signed quantity

`delta_mass_dex = lephare.mass_med − log10(cigale.mass)`, positive = LePhare
larger. Sign convention follows `docs/reference/unit-conventions.md`
section 2. The raw delta is always retained and never silently centered;
the gate 6.3 validator's hidden-shift guard enforces byte-identity with the
formula on every fixture.

**Rationale.** A raw cross-code quantity is the only output not entangled
with modelling choices; every downstream claim can be audited against it.

**Identified alternative.** Centering inside the delta (a "corrected"
delta). Rejected: it would embed the ~0.24 dex input as a hidden universal
correction — the spec's rejected pattern — and erase the distinction
between disagreement and conditional residual.

**Limitation.** The two codes share photometry and redshift assumptions
(CIGALE fixed to LePhare solutions), so even a perfect residual model does
not isolate independent evidence.

**Approval.** TA2-Q01.

### 3.2 Conditional expectation model

Bounded comparison set: **C0** constant center (development-only median) and
**C1** binned conditional median over `(zpdf_med, mag_auto_f444w)` cells
with the declared support/shrinkage/extrapolation rules. Recommended: C1.

**Rationale.** The frozen offset is described as *conditional*; a constant
center cannot represent covariate structure, while a bounded, monotone,
median-based binned center is auditable, cheap, and shrinks to the global
constant where data are thin. Median (L1) limits contamination from the
heavy tails that are themselves the science target. Permitted covariates
(redshift, brightness) describe *where* the sources are, not *what either
code measured about mass*, so the center cannot absorb the signal it is
supposed to condition away. The historical 0.24 dex motivates this family;
it mandates no subtraction magnitude or sign.

**Identified alternatives.** (i) An individual mass estimate (either code)
as covariate: faster to fit, but it couples the center to the measured
disagreement — a source whose LePhARE mass is anomalous moves its own
center, and FX-02 demonstrates an injected isolated deviation being
absorbed; it remains an identified alternative, not the recommendation.
(ii) A smooth parametric regression (e.g. polynomial/spline on z and mag):
fewer parameters, but extrapolation behaviour and regularization choices
add unauditable leverage at the hull; binning makes support explicit.
(iii) No center at all (rank raw deltas): retained as C0's degenerate
limit; leaves the known conditional structure inside the ranking.

**Limitation.** Bin edges and cell values are development-tile quantities;
out-of-hull sources get the global constant with `center_support =
out_of_hull`, and a source whose true conditional offset varies faster than
the grid can hold residual structure. No held-out residual, spec-z
availability, or the target disagreement defines neighbourhoods or tunes
centering (spec gate 6.2); C1's grid uses only declared covariates and
development data.

**Approval.** TA2-Q02 (procedure approval; coefficients are fitted only in
the later implementation unit, on development only).

### 3.3 Residual, scale, and score

`residual_mass_dex = delta_mass_dex − expected_delta_mass_dex` is the
**primary proposed ranking surface**; `score_mass` — the residual over the
combined scale — is secondary.

**Rationale (ranking order).** Normalization can distort tails: a source
with an anomalously *large quoted error* would see its residual shrunk in
score space even when the raw disagreement is extreme. Ranking residual-
first guarantees rare deviations survive normalization; the score adds a
scale-aware view without controlling the ranking. Raw and centered outputs
are always emitted together with `center_model_id` and `center_support`, so
no consumer can mistake one for the other.

**Scales.** LePhare quantile half-width `(u68 − l68)/2` and the first-order
CIGALE dex error `err/(value·ln10)` are *different summaries* — an ordered
quantile interval versus a symmetric linear error of undocumented shape.
They are kept as separate outputs and combined only in the declared
quadrature score, with: nonpositive/missing error and mass cases enumerated
(`error_missing`, `error_negative`, `exact_zero_native_value`,
`negative_native_value`); ordered-quantile violations
(`quantile_order_violation`); and a declared approximation domain for the
first-order dex error (relative error ≤ 0.3) outside which the CIGALE
sigma is NULL with reason rather than extrapolated. No distribution is
inferred from a mean and an error: the score is explicitly *not* a
calibrated Gaussian significance or n-sigma; that would require an approved
validation argument (TA2-Q02). Asymmetric quantile information is retained
by emitting `l68`/`u68`-derived widths per quantity rather than a single
symmetrized number.

**Floors.** The historical 0.1 dex (mass) and 0.2 dex (SFR) systematics are
context, not v2 constants. The contract replaces them with a
development-only determination rule (robust spread of residual/scale = 1)
whose result is carried with `center_model_id`/`scale_model_id`; any new
floor value is an approval question, not a silent constant.

**Limitation.** Shared photometry and shared redshift assumptions correlate
the two codes' errors, so quadrature combination overstates independence;
the score is an exploratory normalized residual, and its uncertainty
interpretation is deliberately narrow. Sources whose CIGALE error is out of
the approximation domain keep their residual and ranking but lose the
score (`approximation_out_of_domain`) — support is visible, never silently
extrapolated.

**Approval.** TA2-Q02.

## 4. SFR and sSFR

### 4.1 State contract

Per-timescale state machines with first-match precedence:
`missing` → LePhare out-of-domain (`invalid_or_unsupported`) →
`nonpositive_log_undefined` (exact zero vs negative, distinct reasons) →
error missing/negative (`invalid_or_unsupported`) →
`floor_or_censoring_suspected` (`value <= sfr_floor_k × err`, k = 1.0) →
`upper_limit_supported` (declared unreachable) → `point_comparable`.

**Rationale.** The frozen censoring input says the historical ranking was
dominated by sources near the positivity floor. The response is not a
positivity gate but an explicit state machine: an exact zero is a meaningful
native value whose logarithm is undefined (`exact_zero_native_value`, no
epsilon replacement); a negative value likewise; a small positive value
whose quoted symmetric error reaches zero is ill-constrained in log space
and goes unscored with `error_interval_spans_zero`. This criterion is a
declared statistical property of the quoted summary — it is *not* a claim
that the value is a measured upper limit or that a detection threshold
exists.

**Identified alternative.** Epsilon substitution or a positivity-only
sample (both forbidden patterns); a Gaussian censored-likelihood pull
(requires likelihood semantics the source does not document).

**Limitation.** `sfr_floor_k` is a declared domain constant, not fitted;
TA2-Q03 explicitly includes it. LePhare's SFR summary has an undocumented
timescale, so both deltas carry `timescale_caveat_lephare` and are
definitional comparisons.

**Approval.** TA2-Q03.

### 4.2 Upper limits and reduced scope

No source metadata documents a one-sided bound anywhere in the v1.1
catalog, so `upper_limit_supported` is declared unreachable: where a real
bound existed, the contract would define a bound-aware discrepancy with
direction and units; here those paths are unscored/context-only. The review
surface truthfully recommends this reduced SFR scope and asks Don whether
it is acceptable (TA2-Q03); a mechanically complete design cannot silently
broaden scientific authorization.

### 4.3 sSFR

`delta_ssfr_T_dex` is emitted only when both parent states permit, with the
algebraic coupling `delta_ssfr = delta_sfr − delta_mass` declared on the
output and `not_independent_of_mass_and_sfr = true`: sSFR disagreement is
not an independent confirmation of the same anomaly. The CIGALE log sSFR
error needs the unknown mass–SFR error correlation, so `score_ssfr_T` is
`unsupported_correlated_errors` (NULL) on current evidence rather than an
independence assumption.

**Approval.** TA2-Q03.

## 5. Fit-quality context

`chi2_ratio` is omitted from outputs and predictors. LePhare total χ²,
CIGALE total χ², and CIGALE reduced χ² are retained as separately named,
individually meaningful context passthroughs — never predictors, never
ranked, never combined. Degrees of freedom are not recovered from `nbfilt`
(a filter count, not a dof census), and no raw-over-raw ratio substitutes
for the defective quotient: a cross-code fit-quality statistic needs
separately supported likelihood and normalization semantics plus its own
approval (TA2-Q04).

## 6. Spectroscopic interfaces (S5-bound)

The optional redshift-diagnostic interfaces bind to the S5 answers exactly
as recorded (input-contract section 2): the primary diagnostic uses the
adopted mask and preferred-entry provenance of run `1e604a81...` with all
claims conditional on the selection; the separate labelled diagnostic
reports broad-line strength and photometric-QSO labels distinctly (16
tentative-only cases explicit) and never pools into primary fitting; a
secure spec-z is never mass truth. Q05 has no dependency edge into scoring.

**Approval.** TA2-Q06.

## 7. Frozen inputs → design response → failure case

| Frozen input | Design response | Discriminating failure case (gate 6.3) |
|---|---|---|
| ~0.24 dex conditional mass offset; unconditional mean −1.001 | C0/C1 center family; residual/score separation; hidden-shift guard | FX-01/FX-02: a contract that bakes a constant into `delta_mass_dex` fails the formula-identity check; centers that absorb an injected isolated deviation fail FX-02 |
| SFR ranking dominated by positivity-floor censoring | explicit SFR state machine with `floor_or_censoring_suspected`, unscored censored paths, no epsilon, mass population decoupled from SFR | FX-03 (four distinguishable SFR paths; floor/limit paths cannot inherit a point rank) and FX-04 (mass output invariant under SFR changes) |
| dimensionally incoherent `chi2_ratio` | omission plus separately named context passthroughs; dependency check rejects any chi-square quotient under any name | FX-M4 mutation control reintroduces a quotient and must fail |

## 8. What this design does not do

It does not fit, adopt, calibrate, install, or publish anything; it does
not recompute the May/July diagnostics; it does not treat spec-z as mass
truth; it does not invent limits, likelihood equivalence, or an independent
CIGALE photo-z; and it does not widen the unit's write-free boundary. Every
authorization beyond this document's proposal status belongs to TA2-Q01
through TA2-Q06 or a later named approval.
