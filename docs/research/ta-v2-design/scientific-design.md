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

**Scales.** LePhare 68% quantile intervals are generally asymmetric, so the
contract emits **directional half-widths** (`med - l68` and `u68 - med`)
and the width entering a normalized score is selected by the sign of the
conditionally centered residual (P2R-06a decision 2): a positive residual
uses the lower half-width, a negative residual the upper, and an exactly
zero residual gives score zero only after population, point and
uncertainty validity are established (both widths strictly positive,
else `degenerate_quantile_width`). Symmetrizing to `(u68 - l68)/2`
discards direction and is a caught mutation. The first-order CIGALE dex
error `err/(value·ln10)` is a *different summary* — a symmetric linear
error of undocumented shape — kept as a separate output and combined only
in the declared quadrature score, with: nonpositive/missing error and
mass cases enumerated (`error_missing`, `error_negative`,
`exact_zero_native_value`, `negative_native_value`); complete quantile
containment (`l68 <= med <= u68`, not merely `u68 >= l68`) plus a
non-finite rejection; and a declared approximation domain for the
first-order dex error (relative error <= 0.3, inclusive) outside which
the CIGALE sigma is NULL with reason rather than extrapolated. No
distribution is inferred from a mean and an error: the score is
explicitly *not* a calibrated Gaussian significance or n-sigma; that
would require an approved validation argument (TA2-Q02). The
`sigma_sys_*` determination rule (1.4826 × MAD of residual over the
**directional** combined scale equals 1 on development) carries a
declared finite-nonnegative domain and a deterministic bisection solve
policy with explicit `no_admissible_systematic_solution` and
`zero_residual_spread` unsupported results; a negative floor is never
fabricated and the historical 0.1/0.2 dex constants are not restored.
CQ6's zero zero-width/reversed counts do not establish absence of
missing or non-finite quantiles; the guards are fail-closed protection,
not a correction for observed data. These proposed scale details remain
under TA2-Q02; no real-data floor is fitted in this unit.

**Floors.** The historical 0.1 dex (mass) and 0.2 dex (SFR) systematics are
context, not v2 constants. The contract replaces them with a
development-only determination rule (robust spread of residual over the
directional scale = 1) whose result is carried with
`center_model_id`/`scale_model_id`; any new floor value is an approval
question, not a silent constant. The solve policy (bisection, declared
tolerances, explicit unsupported results) is part of the TA2-Q02 proposal;
when no admissible nonnegative solution exists the output is unsupported,
never a fabricated negative floor.

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

P2R-06a decision 1 (2026-10-16) rebuilt the sSFR surface as a
**component-built, non-rankable derived view**:
`delta_ssfr_T_dex = (lephare.sfr_med - lephare.mass_med) -
(log10(cigale.sfr_T) - log10(cigale.mass))`, equal to
`delta_sfr_T_dex - delta_mass_dex` **by construction**, and the validator
now enforces every declared `coupling_expr` numerically at absolute
tolerance 1e-12 on every fixture where both sides are defined (the
d4bc1a2 contract declared the coupling while its native-`ssfr_med`
formula violated it by 0.5 dex on its own FX-06a fixture — R1). The
view's domain depends on the component fields only, so missing or
out-of-domain native `lephare.ssfr_med` nulls the context without
nulling the view. `score_ssfr_T` stays NULL with
`unsupported_correlated_errors`: the CIGALE log sSFR error needs the
unknown mass-SFR error correlation, and no independence assumption is
fabricated. The native field survives only as
`ctx_lp_ssfr_nonadditivity_dex`, a context-only difference between
LePhare summary estimators whose interpretation guard states it does not
establish posterior bimodality, a degenerate fit, or a physical cause.
That guard is not prose alone: the deterministic counterexample MATH-1
(independent Exp(1) X and Z with Y = X + Z; joint density exp(-Y) on
0 <= X <= Y is unimodal and log-concave; median(X) = median(Y - X) =
ln 2; median(Y) solves exp(-m)(1+m) = 1/2 at m = 1.6783469900166605;
non-additivity 2*ln2 - m = -0.29205262889677) proves a nonzero median
non-additivity arises in a provably unimodal distribution, so a nonzero
value cannot be read as bimodal evidence. The CQ2 catalog sizing of the
native gap (mean -0.015 dex; 29,190 of 758,304 type-0 sources above
0.1 dex absolute) is recorded exposure context in the exposure log, not
a parameter here. `not_independent_of_mass_and_sfr = true` is retained:
sSFR disagreement is not an independent confirmation of the same
anomaly.

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

## 9. Declared limitations (P2R-06a A1.8)

Four limitations are declared here explicitly and separately in the
review surface; each is a property of the design, not a defect to fix in
passing.

1. **Shared-redshift dependence.** T_A is conditional on LePhare's
   redshift: CIGALE redshifts are fixed to LePhare solutions in the
   published methodology, so every disagreement surface inherits the
   photo-z it was handed. No T_A output independently validates that
   redshift.
2. **No low-T_z redshift guarantee.** A confident catastrophic photo-z
   can produce a large T_A at low T_z: the redshift-assessment tension
   and the mass/SFR disagreement tensions are different quantities, and
   a small redshift-assessment tension does not establish that the
   redshift is correct. The diagnostic for catastrophic photo-z is
   spectroscopic comparison under the S5 conditions (POP-SPECZ-PRIMARY),
   never a T_A threshold.
3. **Covariance masking.** A fitted joint covariance can absorb a real
   rare population living along its major axis: fixture KERNEL-3 shows a
   source with larger marginal magnitudes receiving a smaller joint
   distance than an off-axis source. The joint pair is a candidate
   surface with this limitation recorded, not a replacement for the
   marginals.
4. **Median non-additivity is not bimodality.** The LePhare
   non-additivity context is a difference between summary estimators; a
   deterministic unimodal (log-concave) construction produces a nonzero
   median non-additivity of about -0.292 (fixture MATH-1), so no nonzero
   value can be read as evidence of a bimodal posterior, a degenerate
   fit, or a physical cause.
