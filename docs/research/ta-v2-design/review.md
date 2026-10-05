<!--
---
title: "T_A v2 Design Review"
description: "Gate 6.4 review surface for the proposed T_A v2 design contract: findings with evidence and the closed approval questions TA2-Q01 through TA2-Q06 for Don"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-10-05"
version: "1.0"
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
  - "[P2R-05 Review and S5 answers](../specz-science-p2r05/review.md)"
---
-->

# T_A v2 Design Review (Gate 6.4)

This is the human review surface for the P2R-06 design unit. The proposed
T_A v2 contract is **complete and mechanically validated; nothing is
adopted**. The six closed questions at the end are for Don. They are not
answered by this spec, this document, or its executor, and no answer is
implied by the quality of the engineering. A later implementation unit
dispatches only after Don accepts this review surface.

## Design identity

| Field | Value |
|---|---|
| Proposal | `ta-v2-feature-contract` v0.1.0-proposed (`docs/research/ta-v2-design/feature-contract.yaml`) |
| Validation | gate 6.3 clean run: 28/28 synthetic cases, 4/4 fit requests, 9/9 mutation controls caught, exit 0 (`validation-results.json`) |
| Bound decisions | S5-Q01..Q05 as recorded 2026-10-05 (input-contract section 2) |
| Read boundary | SELECT-only analyst access; no writes; no manifest refresh; frozen inputs not re-derived |
| Status of every scientific choice | `proposed_not_adopted` |

## Findings

Each finding carries a statement, exact evidence, recommendation,
limitation, and the closed question it serves.

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

**TA2-F03 — The mass population no longer inherits SFR selection.**
Evidence: feature-contract populations (`POP-MASS` declares
`requires_sfr_state: false`); fixtures FX-04a/b/c prove identical
`delta_mass_dex` (0.0) under positive, zero, and NULL SFR, and FX-04d
proves a negative *log* SFR (linear 1e-3) is a valid point comparison,
not rejected by linear positivity. *Recommendation:* approve the population
structure. *Limitation:* `lephare.type = 0` remains an explicit,
recognized selection — claims stay conditional on the LePhare
classification. *Closed question: TA2-Q01.*

**TA2-F04 — Raw disagreement, conditional center, residual, score, support,
and model identity are separate outputs; a hidden universal shift is
structurally rejected.** Evidence: feature-contract outputs block
(`delta_mass_dex` with `hidden_shift_guard`; `expected_delta_mass_dex`;
`center_support`; `residual_mass_dex` as the primary ranking surface;
`score_mass` secondary with the not-a-calibrated-significance guard);
canonical formula identity plus mutation controls M6 (hidden 0.24 dex
shift) and M7 (reversed sign) both fail FX-01a. *Recommendation:* approve
the output separation and residual-first ranking. *Limitation:* quadrature
combination cannot represent correlated cross-code errors; the score stays
an exploratory normalized residual. *Closed question: TA2-Q01, TA2-Q02.*

**TA2-F05 — The center family is bounded, covariate-restricted, and
coupling-disclosed.** Evidence: feature-contract `centers.mass_center`
(comparison set C0/C1 only; permitted covariates `zpdf_med`,
`mag_auto_f444w` plus identified alternatives `zfinal` — excluded for its
documented 0-for-stars semantic and −99.0 candidate sentinel — and
`nbfilt`; forbidden covariates include every mass/SFR/sSFR estimate, every
chi-square field, spec-z fields, tile/survey identity, and the target);
FX-02a/b (cell-dependent residual, unchanged raw delta), FX-02c1/c2 (bias
centers without erasing an injected +4 dex deviation), FX-02d (out-of-hull
fallback); M8/M9 (forbidden covariates) caught. *Recommendation:* approve
C1 as recommended with C0 retained. *Limitation:* bin resolution bounds how
fast conditional structure can be represented; out-of-hull sources get the
global constant, visibly. *Closed question: TA2-Q02.*

**TA2-F06 — The SFR state contract is complete, and the honest consequence
is a reduced SFR scope that needs Don's explicit acceptance.** Evidence:
feature-contract `sfr_100_point`/`sfr_inst_point` carry all six required
states with reasons (`exact_zero_native_value` vs `negative_native_value`
split; `error_interval_spans_zero` for value ≤ k·err with k = 1.0 declared,
not fitted); FX-03a–d prove four distinguishable paths with the floor and
limit paths inheriting no point rank; M2 (dropped censoring state) caught.
Because no source metadata documents a one-sided bound, `upper_limit_supported`
is declared unreachable: censored paths stay unscored/context-only with no
epsilon replacement and no fabricated floor. *Recommendation:* accept the
reduced scope (unscored censored SFR) as the price of not inventing limits;
a bound-aware branch activates only under a later approval that supplies
real bound semantics. *Limitation:* sources near the positivity floor are
retained unscored, so the SFR ranking covers strictly fewer sources than a
fabricated-floor design would claim to rank. *Closed question: TA2-Q03.*

**TA2-F07 — sSFR disagreement is emitted with its algebraic coupling
declared and its score honestly unsupported.** Evidence: feature-contract
ssfr outputs (`delta_ssfr_T_dex == delta_sfr_T_dex − delta_mass_dex`
declared on the output; `not_independent_of_mass_and_sfr = true`;
`score_ssfr_T` = `unsupported_correlated_errors`, NULL, because the
CIGALE log sSFR error needs the unknown mass–SFR error correlation);
FX-06a (coupling verified numerically), FX-06b (raw delta emitted, score
NULL), FX-06c (parent-state gating). *Recommendation:* approve the sSFR
contract as a derived, non-independent view. *Limitation:* sSFR cannot
confirm an anomaly already present in the mass or SFR deltas.
*Closed question: TA2-Q03.*

**TA2-F08 — The chi-square ratio is gone, and fit quality survives only as
separately named context.** Evidence: feature-contract fit-context block
(`ctx_chi2_lephare_total`, `ctx_chi2_cigale_total`,
`ctx_chi2_cigale_reduced` sourced from `cigale.chi2_red_best_fit`, and
`ctx_nbfilt`; all `context_only`, never predictors, never ranked); FX-07a
(passthrough fidelity); M4 (quotient
under a new name) caught; no dof recovery from `nbfilt`; no
independent-CIGALE-photo-z field exists or is invented. *Recommendation:*
approve the exclusion and retention. *Limitation:* a cross-code
fit-quality statistic remains possible only after separately supported
likelihood/normalization semantics and a new approval. *Closed question:
TA2-Q04.*

**TA2-F09 — Partition use is frozen and synthetically enforced.**
Evidence: feature-contract `partition_use` and evaluation-protocol
sections 1–3; FX-P1 (validation/holdout ID in a fit request rejected),
FX-P2 (dual partition), FX-P3 (duplicate training rows) rejected, FX-P4
(clean development request accepted); M3 (rule removed) caught. The four
holdout tiles are acknowledged; uncertainty is clustered by tile and
survey; upstream-calibration independence is stated as unestablished.
*Recommendation:* approve for the future implementation. *Limitation:*
tile blocking reduces, does not eliminate, leakage. *Closed question:
TA2-Q05.*

**TA2-F10 — Identities are compared by content, never overwritten.**
Evidence: `input-identity.json` with tracked-file hashes (dictionary,
unit conventions, manifests, review, tile map, policy config), the
ML01-local adoption review hash with its three used numbers stated inline,
and cross-anchors into input-contract.md; mutation M5 and the scratch
identity test both rejected (`identity_content_mismatch` /
`identity_mismatch`). *Recommendation:* accept as the provenance surface.
*Limitation:* the gitignored adoption review remains ML01-local evidence.
*Closed question: TA2-Q01 (boundary acknowledgment).*

**TA2-F11 — The evaluation protocol is preregistered with no outcome
computed.** Evidence: evaluation-protocol.md (split-use table; declared
comparison set C0/C1 + S0 + robust-spread scales; fixed tie-break;
descriptive vs model-affecting table; holdout freeze checklist); no
metric, ranking, or holdout result exists anywhere in this unit.
*Recommendation:* approve as the protocol the implementation unit must
follow. *Limitation:* protocol quality cannot guarantee execution; the
implementation unit carries its own gates. *Closed question: TA2-Q05.*

**TA2-F12 — The frozen inputs each have a design response and a
discriminating failure case.** Evidence: scientific-design.md section 7
table maps the ~0.24 dex conditional offset, the censoring-dominated SFR
ranking, and the defective `chi2_ratio` to responses and to FX-01/FX-02,
FX-03/FX-04, and M4 respectively; none of the three inputs was re-derived
or re-voted. *Recommendation:* acknowledge the mapping. *Limitation:* the
responses are proposals until TA2-Q01..Q06 are answered.
*Closed question: TA2-Q01..Q06.*

## Closed approval questions

These questions are put to Don. They are not answered here.

| ID | Closed approval question |
|---|---|
| TA2-Q01 | Approve the declared target population and the distinction between raw disagreement, conditional residual and anomaly score? |
| TA2-Q02 | Approve the specified center and scale procedures and uncertainty interpretation, without treating them as mass-truth calibration? |
| TA2-Q03 | Approve the SFR and sSFR state contract, including unscored or context-only handling where a valid censoring bound is unavailable? |
| TA2-Q04 | Approve exclusion of the chi-square ratio and retention of separately named fit-quality context only? |
| TA2-Q05 | Approve the split-use, support, sensitivity, uncertainty and one-time holdout protocol for the future implementation? |
| TA2-Q06 | Approve the spectroscopy interfaces as bound to the S5 answers, with no mass-truth interpretation or pooling of separate populations? |

Each question resolves to concrete contract material and discriminating
evidence: TA2-Q01 → populations + mass outputs + FX-01/FX-04; TA2-Q02 →
`centers`/`scales` + FX-02 + M6/M8; TA2-Q03 → SFR/ssfr machines + FX-03/
FX-06 + M2 and the reduced-scope recommendation in TA2-F06; TA2-Q04 →
fit-context block + M4; TA2-Q05 → evaluation-protocol sections 1–10 +
FX-P1..P4; TA2-Q06 → input-contract section 2 + interface declarations.
None asks Don to approve an unspecified threshold or algorithm; questions
about new evidence (whether the catalog supplies usable censoring bounds)
are already resolved from source semantics and recorded as unsupported
(TA2-F02), and the three frozen facts are not put to a new vote.

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
