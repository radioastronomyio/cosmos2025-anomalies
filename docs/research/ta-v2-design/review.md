<!--
---
title: "T_A v2 Design Review"
description: "Review surface for the proposed T_A v2 design contract: P2R-06 deliverable as repaired by P2R-06a (nine PR #6 findings, five design decisions), with the closed approval questions TA2-Q01 through TA2-Q08 for Don"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-10-16"
version: "2.0"
status: "Active - proposed, pending approval"
tags:
  - type: review
  - domain: astronomy
  - domain: sed-fitting
  - domain: feature-engineering
related_documents:
  - "[T_A v2 README](README.md)"
  - "[Input Contract](input-contract.md)"
  - "[Feature Contract](feature-contract.yaml)"
  - "[Evaluation Protocol](evaluation-protocol.md)"
  - "[Exposure Log](exposure-log.md)"
  - "[P2R-05 Review and S5 answers](../specz-science-p2r05/review.md)"
---
-->

# T_A v2 Design Review (P2R-06 gate 6.4, repaired by P2R-06a gate A1.9)

This is the human review surface for the T_A v2 design unit. The proposed
contract is **complete and mechanically validated; nothing is adopted**.
The closed questions at the end are for Don. They are not answered by this
document or its executor, and no answer is implied by the quality of the
engineering. A later implementation unit dispatches only after Don accepts
this review surface.

## Design identity

| Field | Value |
|---|---|
| Proposal | `ta-v2-feature-contract` v0.2.0-proposed (`docs/research/ta-v2-design/feature-contract.yaml`) |
| Validation | P2R-06a A1.9 regenerated run: 71/71 synthetic cases, 5/5 fit requests, 3/3 joint fit requests, 3/3 sigma_sys solve checks, 1/1 mathematical counterexamples, 1/1 binning demonstrations, 5/5 joint kernel checks, 5/5 joint estimator checks, 34/34 mutation controls caught, exit 0 (`validation-results.json`) |
| Authority | P2R-06 v1.0 (Action Registry `rec4acLZWCuN1tJk9`, 2026-10-05); parent PR #6 merged 2026-10-16 at `156cb9eee863a9fabd14e9f828991042fbe59d4b` under Don's separate closeout instruction; amendment P2R-06a v1.2 (Action Registry `recdrZoPWx6IaizkN`, 2026-10-16 17:44 EDT; GPT-6 pre-run review incorporated in v1.1) |
| Repaired baseline | All nine PR #6 review findings (R1-R9, Greptile review 5417842122 and Codex review 5417892132 on head `d4bc1a2`) demonstrated on the old behaviour and repaired; per-finding evidence in the P2R-06a worklog |
| Bound decisions | S5-Q01..Q05 as recorded 2026-10-05 (input-contract section 2); Don's five 2026-10-16 design decisions bound as `proposed_not_adopted` material |
| Read boundary | SELECT-only analyst access; the single A1.5 development-only support count is disclosed in the exposure log; no writes; no manifest refresh; frozen inputs not re-derived |
| Status of every scientific choice | `proposed_not_adopted` |

## What the d4bc1a2 claims got wrong, and what validation now covers

The P2R-06 review surface stated the contract was "mechanically validated"
while the validator and the contract disagreed in at least nine places
(two reproducible from the branch: the declared sSFR identity was
numerically false on the validator's own FX-06a outputs by 0.5 dex, and
type-1 sources received finite population-conditioned residuals although
the contract made them audit-only). The validator saw happy paths and a
short mutation list; nothing compared each stated rule against behaviour.
Those statements are withdrawn. The repaired validation enforces, with a
discriminating fixture or mutation for each executable rule: population
gating (FX-R3/R8 family), SFR scale states with complete quantile
containment (FX-R2 family), directional half-widths (FX-R9 family), the
algebraic couplings numerically at 1e-12 (FX-R1 family, M19/M20), support
hierarchies on unique-source counts (FX-R7 family, M22), the partition
and identity manifest fail-closed behaviour (FX-P5, M24/M25), the
recorded command's re-executability (test), the joint estimator and its
clamp (FX-J family, CLAMP-A/G, M26-M33), and the naming restraint (M34).

What validation still does **not** cover, stated as such rather than
claimed: no real-data fit, ranking, holdout evaluation, or scientific
adoption of any kind has occurred; the coordinator-reported prior
findings behind the forced z = 5.5 edge were not reproduced in this unit;
the robust covariance estimator's behaviour on arbitrary mixtures is not
proven by the synthetic examples; and the eventual holdout assessment is
not an untouched test of feature-family selection (exposure-log.md).

## PR #6 review comments → findings → repairs

| # | Review comment (source) | Finding | Change made | Discriminating evidence |
|---|---|---|---|---|
| 1 | Declared sSFR identity is false (Greptile P1) | R1 | Component-built `derived_view`, coupling enforced at 1e-12 | FX-06a rewritten (0.5 - log10 2); adapter old-gap 0.5 dex; M19 |
| 2 | sSFR identity contradicts fixture (Codex P2) | R1 | same | FX-R1a-d; M20 false coupling |
| 3 | SFR scores ignore the scale state (Greptile P1) | R2 | SFR scale machines evaluated; guards declared and enforced | FX-R2a-g; M12, M15 |
| 4 | SFR scores ignore the scale state (Codex P1) | R2 | same | FX-R2a score NULL at rel-err 0.31; boundary 0.30 finite |
| 5 | POP-MASS omits CIGALE mass-error validity (Greptile P1) | R3 | Predicate completed; cross-artefact consistency check | FX-R3a/b; M10, M14 |
| 6 | Fit-request IDs with no assignment pass (Greptile P2) | R4 | Shared partition guard on every fitter | FX-P5; adapter old-acceptance |
| 7 | Missing authorizing spec skips verification (Greptile P2) | R5 | Root-resolved manifest, no skip path, required-set check | M24/M25; scratch-identity tests |
| 8 | Recorded command points under docs/src/ (Greptile P2) | R6 | Interpreter/argv recorded from repo root; re-execution test | test_recorded_command_reexecutes_semantically |
| 9 | C1 support rule untested (Greptile P2) | R7 | Support counts enforced with fallback hierarchy; synthetic construction | FX-R7a-j; DEMO-SLOPE; M22, M23 |
| 10 | Non-POP-MASS sources receive residuals and scores (Codex P2) | R8 | Population gates on residuals and scores with reasons | FX-R8a-e; M11, M13 |
| 11 | Symmetric LePhare widths discard direction (Codex P2) | R9 | Directional half-widths selected by the conditionally centered residual | FX-R9a-i; M16-M18 |

## Findings

Each finding carries a statement, exact evidence, recommendation,
limitation, and the closed question it serves. Findings TA2-F01..F12 are
revised only where the amendment changed their subject; new findings
TA2-F13..F17 carry the five 2026-10-16 design decisions.

**TA2-F01 — The recorded S5 answers are on `main`, verified against the
binding table, and propagated without widening.** Evidence: input-contract
section 2 with exact review.md locators (Q01 line 321; Q02 323–337; Q03
339–376 incl. the 16 tentative-only cases and their SQL; Q04 378–385; Q05
387–392 at base `01f28ee`); interface inclusions/exclusions in section 3;
no run-status change and no adopted-state alias anywhere in the diff.
*Recommendation:* accept the binding as the reference for all downstream
interfaces. *Limitation:* the sealed rows retain
`pending_scientific_adoption`; that frozen value is not altered by anything
here. *Closed question: TA2-Q06.*

**TA2-F02 — Source semantics are fully inventoried; four semantics are
explicitly unsupported, and none is silently defaulted.** Evidence:
input-contract section 5 (32 fields by exact `source.table.column` with
dictionary line anchors 289–585 evidence): no documented censoring limits
anywhere (so `upper_limit_supported` is unreachable); CIGALE error shapes
undocumented; LePhare SFR timescale undocumented; no CIGALE sSFR column in
v1.1. Fixture FX-03c proves no rule may reference an undocumented bound
field. *Recommendation:* adopt the inventory as the semantic boundary.
*Limitation:* if upstream later documents bound semantics or an sSFR
column, a new approval is needed to activate them. *Closed question:
TA2-Q03.*

**TA2-F03 — The mass population no longer inherits SFR selection, and
membership now requires error validity.** Evidence: feature-contract
populations (`POP-MASS` predicate with the CIGALE mass-error conditions
and the input-contract echo checked by the validator); fixtures FX-04a/b/c
prove identical `delta_mass_dex` (0.0) under positive, zero, and NULL SFR,
and FX-04d proves a negative *log* SFR (linear 1e-3) is a valid point
comparison; FX-R3a/b prove NULL and negative errors fall outside POP-MASS
with the raw delta retained; CQ1 sized the exposure (0 of 634,845 affected
by error validity; 8,927 non-type-0 sources with both masses valid —
recorded context, not a frozen input). *Recommendation:* approve the
population structure. *Limitation:* `lephare.type = 0` remains an
explicit, recognized selection — claims stay conditional on the LePhare
classification. *Closed question: TA2-Q01.*

**TA2-F04 — Raw disagreement, conditional center, residual, score, support,
and model identity are separate outputs; a hidden universal shift is
structurally rejected; population gating now precedes everything.**
Evidence: feature-contract outputs block (`delta_mass_dex` with
`hidden_shift_guard`; `residual_mass_dex` with `population_gate: POP-MASS`;
`score_mass` with declared guards under `contract.guard_precedence`);
canonical formula identity plus mutation controls M6 (hidden 0.24 dex
shift) and M7 (reversed sign) both fail FX-01a; M11 removes the declared
population gate and fails structurally and behaviourally; FX-R8a-c prove
type-1/2/99 sources receive NULL residual and score with
`not_in_population`. *Recommendation:* approve the output separation,
residual-first ranking, and the population precedence. *Limitation:*
quadrature combination cannot represent correlated cross-code errors; the
score stays an exploratory normalized residual. *Closed question: TA2-Q01,
TA2-Q02.*

**TA2-F05 — The center family is bounded, covariate-restricted,
coupling-disclosed, and its binning rule is now fully specified and
enforced.** Evidence: feature-contract `centers.mass_center` (comparison
set C0/C1 only; permitted covariates `zpdf_med`, `mag_auto_f444w` plus
identified alternatives; forbidden covariates include every mass/SFR/sSFR
estimate, every chi-square field, spec-z fields, tile/survey identity, and
the target); the C1 entry carries `z_quantile_bins`/`mag_quantile_bins`,
the deterministic linear-interpolation `quantile_method`, the
`edge_conventions` (duplicate-edge collapse with effective-bin counts,
forced `forced_highz_edge` inserted only strictly inside the development
support, left-closed/right-open with the final endpoint included, z = 5.5
in the upper bin, missing/non-finite covariates unsupported), and
`support_enforcement: center_min_cell_support` over unique-source counts
with the requested cell recorded; FX-02a/b (cell-dependent residual,
unchanged raw delta), FX-02c1/c2, FX-02d (out-of-hull fallback), FX-R7a-c
(200 → cell, 199 → z_fallback, z-only 199 → global_fallback), FX-R7h/i
(z exactly 5.5 upper-bin; max endpoint included), FX-R7j (duplicate edges
collapse; support wholly below 5.5 inserts no edge); DEMO-SLOPE (with the
forced edge, on-trend residuals 0.0 ≤ 0.005; without it, 0.048 > 0.005);
M8/M9 (forbidden covariates), M22 (support counts ignored), M23 (forced
edge removed) all caught. *Recommendation:* approve C1 as recommended with
C0 retained. *Limitation:* bin resolution bounds how fast conditional
structure can be represented; out-of-hull sources get the global constant,
visibly; global fallback does not preserve local high-redshift structure.
*Closed question: TA2-Q02.*

**TA2-F06 — The SFR state contract is complete, honestly reduced, and now
scale-gated.** Evidence: feature-contract `sfr_100_point`/`sfr_inst_point`
carry all six required states with reasons; the scale machines now run and
emit their states with complete median containment and non-finite
rejection; FX-03a–d prove four distinguishable point paths; FX-R2a-g prove
out-of-domain (0.31), reversed-quantile, median-outside, missing, and
non-finite uncertainty cases all lose the score while eligible residuals
survive, with the inclusive 0.30/0.29 boundary controls passing throughout;
M2 (dropped censoring state) and M12/M15 (guards removed) caught. Because
no source metadata documents a one-sided bound, `upper_limit_supported`
is declared unreachable: censored paths stay unscored/context-only with no
epsilon replacement and no fabricated floor. *Recommendation:* accept the
reduced scope as the price of not inventing limits. *Limitation:* sources
near the positivity floor are retained unscored, so the SFR ranking covers
strictly fewer sources than a fabricated-floor design would claim to rank.
*Closed question: TA2-Q03.*

**TA2-F07 — sSFR is a component-built, non-rankable derived view whose
declared coupling is enforced numerically, and the LePhare non-additivity
is an honestly-guarded context field.** Evidence: `delta_ssfr_T_dex`
component formula satisfying `delta_ssfr_T_dex == delta_sfr_T_dex -
delta_mass_dex` by construction, checked at 1e-12 on every defined fixture
(R1: the d4bc1a2 formula violated its own declared coupling by 0.5 dex);
FX-06a rewritten (`0.5 - log10 2`), FX-R1a-d (inst timescale with nonzero
mass delta; native-sSFR-independent eligibility; context 0 / NULL cases);
`ctx_lp_ssfr_nonadditivity_dex` context-only with the MATH-1 deterministic
unimodal counterexample (non-additivity -0.29205262889677); M19/M20/M21
caught; `lephare.ssfr_med` appears in no rankable or delta formula.
*Recommendation:* approve the sSFR contract as a derived, non-independent,
non-rankable view plus context. *Limitation:* sSFR cannot confirm an
anomaly already present in the mass or SFR deltas; the context field does
not establish bimodality, a degenerate fit, or a physical cause; the CQ2
catalog sizing (29,190 of 758,304 above 0.1 dex) is recorded exposure
context, not a parameter. *Closed question: TA2-Q03.*

**TA2-F08 — The chi-square ratio is gone, and fit quality survives only as
separately named context.** Evidence: feature-contract fit-context block
(all `context_only`, never predictors, never ranked); FX-07a (passthrough
fidelity); M4 (quotient under a new name) caught; no dof recovery from
`nbfilt`; no independent-CIGALE-photo-z field exists or is invented.
*Recommendation:* approve the exclusion and retention. *Limitation:* a
cross-code fit-quality statistic remains possible only after separately
supported likelihood/normalization semantics and a new approval. *Closed
question: TA2-Q04.*

**TA2-F09 — Partition use is frozen and enforced fail-closed on every
synthetic fitter.** Evidence: feature-contract `partition_use` and
evaluation-protocol sections 1–3; FX-P1..P4 plus FX-P5 (unassigned ID
rejected) and FX-JP1..3 (duplicate, unassigned, and validation-assigned
covariance rows rejected); M3 caught; the shared `partition_guard` runs in
the center, solve, and covariance paths. The four holdout tiles are
acknowledged; uncertainty is clustered by tile and survey;
upstream-calibration independence is stated as unestablished.
*Recommendation:* approve for the future implementation. *Limitation:*
tile blocking reduces, does not eliminate, leakage. *Closed question:
TA2-Q05.*

**TA2-F10 — Identities are compared by content, root-resolved, and
fail-closed; the recorded command re-executes.** Evidence:
`input-identity.json` `authorizing_specs` manifest referencing the in-repo
archive copies by repository-relative path with SHA-256; a missing file
fails `identity_missing:authorizing_spec`, a digest mismatch fails
`identity_mismatch:authorizing_spec`, deleting a required entry fails
against the contract's `minimum_required_authorizing_specs`, and no skip
path exists (R5 was live on main: the d4bc1a2 recorded path was absent
after the parent closeout move); M5/M24/M25 and the scratch-identity
tests; the results record the actual interpreter and argv resolved from
the repository root, and the reproduction test re-executes them into a
scratch file with identical semantics (R6: the d4bc1a2 command pointed
under `docs/src/`, which does not exist). *Recommendation:* accept as the
provenance surface. *Limitation:* the gitignored adoption review remains
ML01-local evidence. *Closed question: TA2-Q01 (boundary acknowledgment).*

**TA2-F11 — The evaluation protocol is preregistered with no outcome
computed, the exposure history is disclosed, and the joint candidates
carry predeclared separated criteria.** Evidence: evaluation-protocol.md
(split-use table; declared comparison set including the joint candidate
pair as TA2-Q07 material; fixed tie-break; the three separated
joint-candidate criteria; descriptive vs model-affecting table; holdout
freeze checklist); exposure-log.md (pre-partition history with unknown
coverage; CQ1-CQ8 verbatim; prospective development-only rule; the single
A1.5 count); no metric, ranking, or holdout result exists anywhere in
this unit. *Recommendation:* approve as the protocol the implementation
unit must follow, with TA2-Q08 accepting the qualified holdout claim.
*Limitation:* design was informed by full-catalog summaries containing
holdout information, so the eventual holdout assessment is not an
untouched test of feature-family selection; protocol quality cannot
guarantee execution. *Closed question: TA2-Q05, TA2-Q08.*

**TA2-F12 — The frozen inputs each have a design response and a
discriminating failure case.** Evidence: scientific-design.md section 7
table maps the ~0.24 dex conditional offset, the censoring-dominated SFR
ranking, and the defective `chi2_ratio` to responses and to FX-01/FX-02,
FX-03/FX-04, and M4 respectively; none of the three inputs was re-derived
or re-voted. *Recommendation:* acknowledge the mapping. *Limitation:* the
responses are proposals until TA2-Q01..Q06 are answered. *Closed question:
TA2-Q01..Q06.*

**TA2-F13 — Decision 1 (component sSFR view) is bound as proposed
material.** Evidence: the derived view, its enforced coupling, and the
context field (TA2-F07); CQ2 sized the native gap (mean -0.015 dex) as
coordinator-reported context only. *Recommendation:* approve the component
view and the context field as declared. *Limitation:* the context is a
difference between LePhare summary estimators and establishes nothing
about posterior shape. *Closed question: TA2-Q03.*

**TA2-F14 — Decision 2 (directional half-widths) is bound as proposed
material.** Evidence: FX-R9a/b/i with independent oracles (0.891740157358414
on the 0.05 side versus the old symmetric 0.49567888926745); FX-R9c
(residual-driven side under an opposite-sign raw delta); the degenerate
and zero-residual rules; the declared sigma_sys solve policy with
SOLVE-1..3; M16-M18 caught. *Recommendation:* approve the directional
scale convention and the solve policy status. *Limitation:* the
sigma_sys determination remains under TA2-Q02 and no real-data floor is
fitted here; CQ6's zero counts do not establish absence of missing or
non-finite quantiles. *Closed question: TA2-Q02.*

**TA2-F15 — Decision 3 (high-redshift binning) is bound as proposed
material resting on a coordinator-reported prior finding not reproduced in
this unit.** Evidence: `forced_highz_edge = 5.5` as a `declared_domain`
constant whose rationale cites the 2026-07-10/2026-09-01 sessions
(exposure-log sections 1.2-1.3); DEMO-SLOPE (with edge: residuals ≤
0.005; without: 0.048); FX-R7h (z = 5.5 upper bin); FX-R7j (no insertion
when support lies wholly below); M23 caught. CQ3/CQ4 sized the tail
(14,535 type-0 eligible sources above z 5.5) as context. *Recommendation:*
approve the forced edge as a declared proposal. *Limitation:* the slope
reversal was observed against mean mass, not the permitted brightness
covariate; the boundary is not evidence of a physical discontinuity and
not a guarantee of adequate resolution; the A1.5 audit count shows the
[5.5,8) band is sparse in places (98 sources in m21-24), so per-cell
support at the boundary is an evaluation-time concern. *Closed question:
TA2-Q02.*

**TA2-F16 — Decision 4 (joint mass-SFR candidate pair) is bound as
proposed comparison-candidate material.** Evidence: the four surfaces
under `winsorized-median-covariance-v1` with the 0.95 clamp; kernel
checks with independent oracles (3.1622776601683795/6.957010852370437 at
correlation 0.8; 3.5355339059327378/3.4 at correlation 0 with no veto);
analytic pooled-moment demonstrations (-0.5; -0.35, not -0.30); estimator
checks (CORE rho exactly 0.5; CLAMP-A 0.9998 → exactly 0.95; DEGEN);
evaluator domain fixtures (population intersection, per-timescale
independence, scale-only failure, fallback, degeneracy); M26-M33 caught;
marginals unchanged. *Recommendation:* approve the pair as declared
comparison candidates alongside the repaired marginals, with any selection
budget or quota left to a separate decision (TA2-Q07). *Limitation:* a
fitted covariance can absorb a rare population along its major axis
(KERNEL-3); pooled correlations distort across heterogeneous bins
(POOLED-1/2); cross-code and within-code mass-SFR correlations remain
unknown; CQ5's raw correlation (about -0.30, uncentered, censored regime
included) is neither a parameter nor a bound. *Closed question: TA2-Q07.*

**TA2-F17 — Decision 5 (partition exposure record and development-only
query rule) is bound.** Evidence: exposure-log.md sections 1-4 (history
with unknown coverage; CQ1-CQ8 byte-for-byte with the population
distinctions; the prospective rule binding `catalog_id`, the inherited
`run_id`, and `assigned_split = 'development'`; the single A1.5 count
under the verified analyst role); the protocol links it and states the
qualified holdout claim. *Recommendation:* accept the record and the rule.
*Limitation:* the historical overlap with today's holdout is unverified,
so the disclosure is a qualification, not a restoration of an unseen
holdout. *Closed question: TA2-Q08.*

## Declared limitations (P2R-06a A1.8)

Stated separately from the findings above and mirrored in
scientific-design.md section 9; each is checked in context, not by
counting phrases.

1. **Shared-redshift dependence.** T_A is conditional on LePhare's
   redshift (CIGALE is fixed to LePhare solutions); no T_A output
   independently validates that redshift.
2. **No low-T_z redshift guarantee.** A confident catastrophic photo-z
   can produce a large T_A at low T_z; low T_z does not establish a
   correct redshift, and the diagnostic for catastrophic photo-z is
   spec-z under the S5 conditions (POP-SPECZ-PRIMARY), never a T_A
   threshold.
3. **Covariance masking.** A fitted joint covariance can absorb a real
   rare population living along its major axis (fixture KERNEL-3: larger
   marginals, smaller joint distance). The joint pair is a candidate
   surface with this limitation recorded.
4. **Median non-additivity is not bimodality.** The context field
   `ctx_lp_ssfr_nonadditivity_dex` does not establish posterior
   bimodality, a degenerate fit, or a physical cause; the deterministic
   unimodal counterexample MATH-1 (non-additivity about -0.292) proves a
   nonzero value can arise without any bimodality.

## Closed approval questions

These questions are put to Don. They are not answered here. TA2-Q01..Q06
retain their P2R-06 identities and remain unanswered; no approved S5
question or answer is edited. TA2-Q07 and TA2-Q08 are added by P2R-06a.

| ID | Closed approval question |
|---|---|
| TA2-Q01 | Approve the declared target population and the distinction between raw disagreement, conditional residual and anomaly score? |
| TA2-Q02 | Approve the specified center and scale procedures and uncertainty interpretation, without treating them as mass-truth calibration? |
| TA2-Q03 | Approve the SFR and sSFR state contract, including unscored or context-only handling where a valid censoring bound is unavailable? |
| TA2-Q04 | Approve exclusion of the chi-square ratio and retention of separately named fit-quality context only? |
| TA2-Q05 | Approve the split-use, support, sensitivity, uncertainty and one-time holdout protocol for the future implementation? |
| TA2-Q06 | Approve the spectroscopy interfaces as bound to the S5 answers, with no mass-truth interpretation or pooling of separate populations? |
| TA2-Q07 | Approve the joint mass-SFR candidate pair as declared comparison candidates alongside the repaired marginal surfaces, with any selection budget or quota left to a separate decision? |
| TA2-Q08 | Accept the documented design-stage exposure and the qualified future holdout claim, with development-only exploration/fitting, separately authorized protocol-bound validation/final evaluation, and no reroll? |

### Change table for existing questions (P2R-06a A1.9)

| ID | Wording change | Reason |
|---|---|---|
| TA2-Q01 | none | Population structure repaired in place (R3, R8); the question's subject is unchanged |
| TA2-Q02 | none | Centers/scales repaired in place (R7, R9); the question's subject is unchanged and now covers the directional scale and solve policy |
| TA2-Q03 | none | SFR machines repaired in place (R2); sSFR is now a component view (R1) within the same question's scope |
| TA2-Q04 | none | unchanged |
| TA2-Q05 | none | unchanged |
| TA2-Q06 | none | unchanged |

Each question resolves to concrete contract material and discriminating
evidence: TA2-Q01 → populations + mass outputs + FX-01/FX-04/FX-R3/FX-R8;
TA2-Q02 → `centers`/`scales` + FX-02 + FX-R7 + FX-R9 + SOLVE-1..3 + M6/M8;
TA2-Q03 → SFR machines + FX-03/FX-R2 + the sSFR component view + FX-06/FX-R1
+ M2 and the reduced-scope recommendation in TA2-F06; TA2-Q04 → fit-context
block + M4; TA2-Q05 → evaluation-protocol sections 1-12 + FX-P1..P5 +
FX-JP1..3; TA2-Q06 → input-contract section 2 + interface declarations;
TA2-Q07 → `joint_surfaces` + protocol section 10 + FX-J4..J7 + KERNEL/POOLED
+ CLAMP checks + M26-M33; TA2-Q08 → exposure-log.md + protocol preamble +
TA2-F17. None asks Don to approve an unspecified threshold or algorithm;
questions about new evidence (whether the catalog supplies usable
censoring bounds) are already resolved from source semantics and recorded
as unsupported (TA2-F02), and the three frozen facts are not put to a new
vote.

## Propagation guarantees

- The S5-Q03 population has no path into primary fitting (contract
  `specz_diagnostic_interfaces.separate_labelled_diagnostic.pooling:
  never`; populations table note).
- S5-Q05 has no dependency edge into scoring or any interface (traceability
  only; input-contract section 2 row Q05).
- The review can truthfully recommend **reduced SFR scope**: a mechanically
  complete design cannot silently broaden scientific authorization
  (TA2-F06).

## What answering "approve" would and would not authorize

Approval of TA2-Q01..Q06 authorizes a **later named implementation unit**
to materialize and validate T_A v2 under the approved contract, on
development data first, with its own reversible install boundary. It does
not authorize production calibration, database installation, candidate
publication, release, or upstream contact in this unit; each of those
remains a separate approval.
