<!--
---
title: "P2R-06: T_A v2 scientific design contract"
description: "Define reviewable mass-disagreement, SFR-censoring, fit-context and evaluation contracts from frozen inputs, bound to Don's 2026-10-05 S5 answers"
author: "Claude (coordinator), from the 2026-10-04 Codex/Astra draft"
date: "2026-10-05"
version: "1.0"
status: "Queued"
tags:
  - type: specification
  - domain: [feature-engineering, sed-fitting, spectroscopy]
  - tech: [python, postgresql]
related_documents:
  - "[Repository instructions](/opt/agents/repos/cosmos2025-anomalies/AGENTS.md)"
  - "[Frozen project inputs](/opt/agents/repos/cosmos2025-anomalies/docs/project-state.md)"
  - "[P2R-05 review and S5 answer record](/opt/agents/repos/cosmos2025-anomalies/docs/research/specz-science-p2r05/review.md)"
  - "[Coordinator log](/opt/agents/repos/work-logs/2026-10-04-cosmos2025-worklog-00-p2r05-adoption-coordination.md)"
---
-->

# Spec P2R-06: T_A v2 scientific design contract

Repo mode. Gates 6.1 to 6.5. Builder: GPT (Sol 6.1 unless Don names another) in the GPT Work COSMOS project. Review seat: Claude.

Authority: Don approved closing this spec on 2026-10-05 (Action Registry rec4acLZWCuN1tJk9; utterances 09:13 EDT "I dont see anything in your responses to veto." and 09:15 EDT "Approved to execute."). Dispatch is a separate act: Don pastes the dispatch prompt into the COSMOS project. A later T_A v2 implementation or calibration unit does not dispatch until Don accepts this unit's review surface. Database installation, production scores and release are outside this unit.

## 1. Objective

Deliver a complete proposed T_A v2 contract that distinguishes raw cross-code disagreement from conditional residuals, preserves SFR censoring and measurement states, excludes the invalid chi-square ratio, and declares the populations, uncertainty interpretation, partition use and validation protocol for a later implementation. Every proposed output has exact source fields, units, sign, domain, null and reason behaviour, provenance, and a discriminating synthetic example. A review document presents stable closed questions for Don. No observed T_A values are fitted or ranked, and the executor adopts no scientific policy.

## 2. Why this unit exists

`docs/project-state.md` (section 1, near line 55) supplies frozen design inputs, not hypotheses to diagnose again. Verify the text there; the summary below is the spec author's reading:

- A conditional cross-code mass offset of about 0.24 dex; the historical unconditional `t_mass` mean is -1.001 with a 0.1 dex mass floor.
- SFR rankings are dominated by censoring near the positivity boundary, even though the historical bulk `t_sfr_100` mean and std (0.302 / 0.980) look nominal.
- The historical `chi2_ratio` divides LePHARE `chi2_best` by CIGALE `chi2_red_best_fit`; their meanings and normalization are not commensurable.

Design around these inputs. Do not reopen their truth by repeating the May or July distributions, do not reinterpret an aggregate offset as a universal physical correction, and do not treat nominal bulk pull statistics as a validated tail-ranking distribution. Schema and semantic inspection for implementing a proposed contract is allowed; rerunning the frozen diagnostics is not.

P2R-05 supplies reproducible associations and selected redshifts, not independent stellar-mass measurements. The adoption review found strong magnitude and survey selection (the primary sample is 18,402 of 784,016 sources, 90.80% of it in F444W [15,24) against 12.22% of the catalog) and material eligibility sensitivity (14,738 / 16,992 / 18,567 primary under the three frozen variants against 18,402 at baseline).

## 3. Prerequisite and S5 binding

Prerequisite: Don's S5 answers are recorded in `docs/research/specz-science-p2r05/review.md` on `main` (the adoption-answers PR merged). If they are not on `main` at dispatch, stop at gate 6.1 and report.

Don's answers (2026-10-05, Action Registry rec4acLZWCuN1tJk9), to be verified against review.md at gate 6.1:

| S5 | Answer | Effect on this unit |
|---|---|---|
| Q01 | Adopt | Reference the exact P2R-05 run (1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c) and preferred-entry provenance in the optional redshift-diagnostic interface. |
| Q02 | Adopt with conditions: claims conditional on the frozen type-0, no-broad-line, secure-preferred, unvetoed selection; 0.005 absolute baseline kept with the three frozen variants predeclared and reported, never used to pick a threshold from held-out results; no stellar-mass or SFR truth interpretation; October 4 errata carried forward | Design a separately identified, conditional galaxy redshift diagnostic using the exact adopted mask, with the sensitivity variants and selection caveats built into the protocol. |
| Q03 | Adopt for separately reported diagnostics only; never pooled into primary fitting; evidence strength and photometric-QSO labels kept distinct; the 16 tentative-only broad-line cases reported explicitly | Design separate reporting by broad-line evidence strength and photometric-QSO label. No permission to include AGN or QSO objects in mass modelling by default. |
| Q04 | Adopt with conditions: development-only fitting, validation for declared choices, holdout once after the contract is fixed; clustered uncertainty by tile and survey; no rerolling or rebalancing; upstream-calibration independence stated as unestablished | Reuse the frozen source assignment as the evaluation split, with those conditions written into gate 6.4. |
| Q05 | Send the corrected upstream report; channel Don's choice | Traceability only. No dependency edge into this unit; this unit does not transmit anything. |

If the recorded answers differ from this table, the recorded answers govern; stop the affected lane and report the difference. Adoption does not authorize production calibration in this unit. Do not change the run status in `analysis.specz_p2r05_runs` or create an adopted-state alias; any operational state transition is a separate operator action.

## 4. Execution environment and lifecycle

Box-required on ML01 (source metadata and pinned local evidence). Repository toolchain and context-loading contract per `AGENTS.md`. Read-only analyst database access is the boundary; no administrator credentials. Unattended between reversible checkpoints; Don reviews the completed design before the next unit dispatches. Reasoning effort: high for gates 6.2 and 6.4.

Lifecycle: `AGENTS.md`'s work-spec procedure (task issue, branch `task/<n>-<slug>` off `main`, one commit per gate, one worklog) and the `spec-startup` / `spec-closeout` skills. Remote operations: Don directed on 2026-10-05 that GPT performs pushes and git operations ("GPT can do any pushes, merges, or git operations we need"). Closeout therefore pushes the task branch and opens one pull request. It does not merge. `AGENTS.md` lines 72 and 106 still say executors do no remote operations; record that conflict in the worklog for Don rather than editing `AGENTS.md`.

Effects: repository design documents, a pure contract validator, fixtures and lifecycle records. Reversal is branch reversal. There is no schema change, data mutation, service change, credential change, publication, external write or provenance refresh. Encountering one is a stop condition, not an additional gate.

## 5. Scope

### 5.1 Pre-existing; do not create

The verified v1.1 `source` mirror, sealed dictionary and raw manifest, read-only v1 baseline, the P2R-05 product, config and snapshot, analyst credential handoff, unit conventions, selected O1/O5 opportunities, and the three frozen T_A design inputs. Do not provision infrastructure, recapture a source snapshot, reconstruct spectroscopy, or create an adopted-state alias.

### 5.2 Modify

- `docs/research/ta-v2-design/README.md`: directory index and status.
- `docs/research/ta-v2-design/input-contract.md` and `input-identity.json`: S5 decision references, selected source metadata, inherited identities.
- `docs/research/ta-v2-design/feature-contract.yaml`: proposed fields, formulas, states and populations, each marked `proposed_not_adopted`.
- `docs/research/ta-v2-design/scientific-design.md`: rationale, alternatives and limits.
- `docs/research/ta-v2-design/evaluation-protocol.md`: preregistered development, validation and holdout plan and sensitivity plan.
- `docs/research/ta-v2-design/fixtures.json`, `validation-results.json` and `review.md`: discriminating synthetic cases, results and the review surface.
- `src/inspection/validate_ta_v2_design.py` and `tests/test_ta_v2_design_contract.py`: pure contract validation and synthetic-only tests. No live feature computation entry point.
- Interior indexes the docs pass touches: `src/inspection/README.md`, `tests/README.md`, `docs/research/README.md`, `docs/README.md`. A bounded `docs/project-state.md` entry may link the new design as pending approval without replacing its frozen facts.
- This spec's in-repo archive copy and `spec/` indexes, one worklog, the central registry row, and any spec-defect entry, per `AGENTS.md` and `spec-closeout`.

### 5.3 Reference, do not modify

`AGENTS.md`; documentation standards; `docs/project-state.md`; `docs/reference/unit-conventions.md`; `docs/research/science-opportunities.md`; `data/dictionary/columns-v11.csv`; `docs/reference/schema-v11.md`; `configs/data_paths.yaml`; the frozen raw manifest; the P2R-05 spec, policy, product, schema, review (including its S5 answer record and October 4 errata), tile-map and coverage documents and source modules; historical `src/features/compute_tension_scalars.py` and the May diagnostic report, for context only.

The independent adoption review is at `staging/2026-10-04-astra-p2r05-adoption/adoption-review.md` (ML01-local, gitignored). If the design cites it, record its SHA-256 at gate 6.1 and state every number used from it inline; do not cite it as the sole support for any claim.

Field anchors read on 2026-10-04 (verify; line numbers may move): LePHARE `mass_l68/mass_med/mass_u68` (dictionary lines 312-314), `sfr_l68/sfr_med/sfr_u68` (315-317); CIGALE `sfr_inst[_err]`, `sfr_100myr[_err]`, `mass[_err]` (526-531); CIGALE total and reduced chi-square (534-535). Unit labels alone do not distinguish log10 from linear; use the description and the unit-conventions document.

### 5.4 Do not touch

- Raw holdings, source tables, historical v1 tables, provenance pins: changing them destroys the fixed evidence boundary.
- P2R-05 tables, configs, builders, installer, sealer, snapshots and run status: the product is sealed and this is a dependent design unit. Existing defects become findings, not opportunistic repairs.
- Production tension formulas, the feature pipeline, consumer aliases, ranking tables, new analysis-schema objects: implementation starts only after design approval.
- MetaMCP, runtime infrastructure, credentials, external services, release mechanisms, upstream correspondence: separate operator boundaries.
- Archived specs, including P2R-05's and the errata spec.

## 6. Gates

Each gate ends in one commit referencing its gate number (with the `spec-closeout` trailer block) and a worklog checkpoint that states its evidence inline. Data semantics precede architecture. Independent work may continue after a stopped lane is recorded; dependent work must not assume its missing result.

### Gate 6.1: authority, source semantics and explicit populations

Produce the input contract and identity record. Bind the recorded S5 answers to section 3's table and declare which interfaces are included, excluded or blocked. Record the inherited policy, run, map and manifest identities without refreshing them. Inventory every proposed input field against the v1.1 dictionary and source descriptions: native quantity, unit, log or linear representation, uncertainty meaning, finite sentinel evidence, and availability of genuine censoring limits.

Define separate populations for: mass comparison; each SFR-timescale comparison; the adopted primary spectroscopy diagnostic; the separate labelled diagnostic; and audit-only or unscored sources. The mass population must not require both SFRs to be positive. Spectroscopy availability must not become the denominator of non-spectroscopic mass modelling. Any LePHARE classification or fit-quality gate is explicit and recognized as selection.

Validation:

- [ ] Every proposed input exists by exact `source.table.column` name, is bound to dictionary or source evidence, and has units, representation and a logical domain. Missing or ambiguous semantics produce an explicit `unsupported` state; no column relies on an inferred sentinel or implicit unit conversion.
- [ ] A table enumerates Q01 to Q05 with the recorded answer, scope consequence and exact locator in review.md on `main`. A recommendation cannot satisfy an `accepted` predicate.
- [ ] A synthetic source with valid masses and undefined or censored SFR enters the mass-only path and cannot enter an invalid SFR point-score path.
- [ ] The planned read set contains no v1 diagnostic rerun, no observed mass or SFR residual, no holdout outcome and no raw-manifest refresh. Any unavoidable violation stops the lane.
- [ ] Pins and identities are compared by content; an intentionally changed ID or digest in a scratch copy of the input contract is rejected, not overwritten.

### Gate 6.2: scientific feature contract and recommended design

Produce the machine-readable proposed contract and its explanation. For every output specify grain and key, exact source inputs, formula, sign, units, domain and validity, result state, null and reason codes, whether it may be ranked, and which data may fit its parameters. All scientific choices remain proposals for gate 6.4.

**Mass disagreement.** Preserve the raw signed quantity `delta_mass_dex = lephare.mass_med - log10(cigale.mass)` (positive means LePHARE is larger) and keep any centered residual distinct: `residual_mass_dex = delta_mass_dex - expected_delta(x)`. The frozen offset motivates a conditional expectation model; it is not a globally mandated subtraction, its magnitude does not fix a universal sign, and it is not a correction to true mass. Specify a recommended `expected_delta(x)` family, permitted covariates and transformations, fit objective, minimum support, regularization or binning, missing-input behaviour and extrapolation limits. The bounded comparison set is a development-only constant center and one declared conditional center; neither is fitted here. Do not use held-out residuals, spec-z availability or the target disagreement to define neighbourhoods or tune centering. If an individual mass estimate is a conditioning covariate, disclose the coupling and its synthetic failure modes.

Keep raw difference, conditional residual and any scale-normalized score distinct, retain raw and centered outputs together, and specify how rare deviations survive normalization. A proposed score documents estimator uncertainty and support and the effect of shared photometry, shared redshift assumptions and correlated errors. Do not call it a calibrated Gaussian significance or n-sigma without an approved validation argument.

LePHARE quantile widths and CIGALE linear errors are different summaries. Enumerate ordered-quantile, nonpositive mass or error, missing and large-relative-error cases. A first-order CIGALE log error `err/(value*ln(10))` needs a declared approximation domain and is not extrapolated to ill-constrained values. Do not infer a distribution from a mean and error without declaring the assumption. Keep asymmetric information where supported. The historical 0.1 dex mass and 0.2 dex SFR floors are context, not approved v2 constants; any new scale or floor needs a development-only determination rule and an approval question.

**SFR and sSFR.** Design distinct state and score paths for CIGALE instantaneous and 100 Myr SFR, and state the comparability limits of LePHARE's SFR summary. Required states at least: `point_comparable`, `upper_limit_supported`, `floor_or_censoring_suspected`, `nonpositive_log_undefined`, `missing`, `invalid_or_unsupported`, with explicit precedence and reasons. Do not equate every small positive value or zero with a measured upper limit; a positive posterior summary and its error are not evidence of a detection threshold, and a zero may be a meaningful native value whose logarithm is undefined. No epsilon replacement, positivity-only master sample, fabricated floor, or ranked point pull for an unbounded or unsupported censored case. Where source metadata establishes a real one-sided bound, define a bound-aware discrepancy with direction and units; where it does not, propose an unscored or context-only branch and ask Don whether that reduced scope is acceptable. Any sSFR quantity is derived only when both states permit it, with correlated uncertainty acknowledged, and is not an independent confirmation of the same anomaly.

**Fit-quality context.** Omit `chi2_ratio` from outputs and predictors. Retain separately named LePHARE total chi-square, CIGALE total chi-square and CIGALE reduced chi-square as context if needed. Do not recover degrees of freedom by guessing from `nbfilt` or introduce a raw-over-raw ratio as a substitute. A cross-code fit-quality statistic needs separately supported likelihood and normalization semantics and approval.

Validation:

- [ ] Every state in every feature has a complete domain, precedence rule and explicit output and reason; unsupported cases cannot default to a finite ranked value.
- [ ] Raw difference, expected center, centered residual, score, support flag and model or version identity are separate outputs. A universal 0.24 dex shift applied as a hidden mass correction is rejected by contract validation.
- [ ] The proposal specifies center and scale procedures but contains no fitted catalog coefficients or observed residual or ranking distribution; every illustrative number is labelled synthetic.
- [ ] Changing SFR between positive, zero and undefined leaves valid raw mass disagreement unchanged; censored or unsupported SFR cannot manufacture infinite or arbitrarily extreme ranked tension.
- [ ] No `chi2_ratio`, inferred degrees of freedom, independent-CIGALE-photo-z field or mass-truth label appears among permitted predictors or targets; renaming a forbidden ratio does not evade the dependency and formula check.
- [ ] Every scientific choice has a rationale, an identified alternative, a limitation and a linked approval question; none is marked accepted.

### Gate 6.3: executable synthetic contract checks

Build a pure validator and a compact fixture corpus. It may evaluate proposed algebra on synthetic records and inspect declared dependencies. It does not connect to a database or generate real catalog features. Fixtures cover unit and sign conversion, ordered and asymmetric quantiles, missing values and sentinels, zero and negative inputs, censoring states, insufficient support, out-of-domain covariates and partition-use rules.

Required discriminators:

- LePHARE log mass 10 against CIGALE linear mass 1e9 gives +1 dex; the explicit reverse definition gives the opposite sign; equal physical masses give zero; treating 1e9 as already logarithmic fails.
- The same discrepancy in two covariate cells with different proposed centers yields different residuals and an unchanged raw delta; a uniformly biased synthetic sample centers without erasing an injected isolated deviation; no real-data center is learned.
- A positive SFR, an exact zero, a documented upper limit and an unsupported floor follow four distinguishable paths; the last two do not inherit a point-score rank by default.
- Changing or removing SFR data cannot remove a valid mass-only record; a negative log SFR is not rejected by a linear positivity test.
- Validation or holdout IDs in a synthetic fit request are rejected; one source cannot appear in two partitions or as multiple independent training rows.
- Scratch-copy mutations that swap log and linear metadata, drop a censoring state or reason, allow a held-out fit ID, or reintroduce the chi-square quotient each fail their intended invariant.

Validation:

- [ ] The validator exits 0 on the complete contract with every expected synthetic result within its declared tolerance, and exits nonzero on each named mutation with the intended reason.
- [ ] Results record correct cases and negative controls with stable case IDs, expected and observed behaviour, command, input and contract hashes, and exit codes.
- [ ] No fixture is described as astrophysical validation, measured calibration, power estimate or real-data ranking.
- [ ] The validator has no database connection, no installer import and no catalog feature-generation mode.

### Gate 6.4: evaluation protocol and review surface

Create `evaluation-protocol.md` and `docs/research/ta-v2-design/review.md`. The protocol distinguishes non-spectroscopic disagreement characterization from the redshift diagnostics. A secure spec-z can assess a photo-z relationship; it cannot decide which stellar mass or SFR is true, establish a causal source of mass tension, or independently validate both codes' shared redshift assumptions.

Write Don's Q04 conditions in: preprocessing, center and scale fitting, support definitions and hyperparameters on development only; validation limited to declared choices with tie-breaks fixed before outcomes; contract and artifact identities frozen before a single holdout evaluation; no reroll or row-random fallback; survey and tile composition reported; clustered uncertainty with the four holdout tiles acknowledged; upstream-calibration dependence stated. Lack of support yields an explicit unsupported claim or stratum, not weighted extrapolation presented as coverage.

Write Don's Q02 and Q03 conditions in: the adopted primary mask, separate labels and denominators, redshift, magnitude, colour, survey and support strata, the three frozen one-factor sensitivity comparisons predeclared and never used to choose a favourable holdout result, and the 16 tentative-only broad-line cases reported explicitly. State which comparisons are descriptive and which can affect a future model decision. No outcome metrics are computed in this unit.

Each finding has an ID, one-line statement, exact file, field or fixture evidence, recommendation, limitation and closed question. At minimum:

| ID | Closed approval question |
|---|---|
| TA2-Q01 | Approve the declared target population and the distinction between raw disagreement, conditional residual and anomaly score? |
| TA2-Q02 | Approve the specified center and scale procedures and uncertainty interpretation, without treating them as mass-truth calibration? |
| TA2-Q03 | Approve the SFR and sSFR state contract, including unscored or context-only handling where a valid censoring bound is unavailable? |
| TA2-Q04 | Approve exclusion of the chi-square ratio and retention of separately named fit-quality context only? |
| TA2-Q05 | Approve the split-use, support, sensitivity, uncertainty and one-time holdout protocol for the future implementation? |
| TA2-Q06 | Approve the spectroscopy interfaces as bound to the S5 answers, with no mass-truth interpretation or pooling of separate populations? |

These questions are not answered by this spec or its executor. Questions about new evidence (for example whether the catalog supplies usable censoring bounds) are resolved from source semantics and recorded as supported or unsupported; the three frozen facts are not put to a new vote.

Validation:

- [ ] Every question resolves to a concrete contract or protocol section and discriminating evidence; none asks Don to approve an unspecified threshold or algorithm.
- [ ] Every frozen input maps to a design response and at least one failure case.
- [ ] S5 conditions propagate exactly; the Q03 population has no path into primary fitting, and Q05 has no dependency edge into scoring.
- [ ] Metrics, strata, model-choice rules and support thresholds are specified before fitting; holdout results are absent.
- [ ] The review can truthfully recommend reduced SFR scope; a mechanically complete design cannot silently broaden scientific authorization.
- [ ] Documentation has required frontmatter and interior README links and says proposed or pending; no adopted claim or release promise is introduced.

### Gate 6.5: closeout

Follow `AGENTS.md`'s work-spec contract and `spec-closeout`. Archive this spec into the in-repo `spec/2026-10/` and the central month folder per the repo's existing pattern. Push the task branch and open one pull request carrying `Closes #<n>` (section 4). Do not merge.

Validation:

- [ ] Branch `task/<n>-<slug>`, its base commit recorded; one commit per gate referencing its gate, each with the trailer block; the worklog states every validation result, stop condition and gate SHA inline.
- [ ] All changes lie within section 5.2; out-of-scope scientific or infrastructure files have no diff.
- [ ] Required checks pass; any stopped lane is explicit in review.md and its dependent deliverables are not presented as ready.
- [ ] One pull request, unmerged; the registry row's `model` equals the `Model:` trailer.
- [ ] The handoff names TA2-Q01 to Q06 and states that implementation, fitting, installation and publication await a later named approval.

## 7. Constraints and stop conditions

- **Do not change science in passing.** A tempting threshold, class exception or SFR floor belongs in the review contract. Any need to change sealed P2R-05 semantics stops that lane.
- **Do not recast the frozen diagnostics as tests.** They are inputs; reproducing them is out of scope.
- **Do not upgrade redshift truth into mass truth.** A deliverable that needs that assumption is rejected and surfaced.
- **Do not invent limits or likelihood equivalence.** Missing censoring, uncertainty or chi-square semantics lead to an unsupported branch or reduced scope; a numeric default would hide an unresolved choice.
- **Do not widen effects.** A database write, source re-export, upstream contact, calibration run, infrastructure change or provenance update is a stop condition; record the blocked lane and continue independent design work.
- **Do not claim independence from the tile map alone.** Narrow the claim or return it to Don.
- **Never delete; never merge.** Use the repository's preservation rules.

## 8. Executor freedom

The executor chooses document organization within the named artifacts, validator decomposition, helper names, fixture organization, and the read-only inspection strategy. It may recommend a fully specified design within the bounded alternatives and state unsupported cases. It may not adopt the design, fit it to the catalog, invent physical metadata, change the inherited product, substitute a different partition or eligibility policy, or widen the write boundary.

## 9. Execution order and end boundary

6.1 authority, identities, semantics and populations; 6.2 the proposed contract; 6.3 synthetic checks of its algebra, domains and failure behaviour; 6.4 the evaluation protocol and review surface; 6.5 closeout. The unit ends at Don's answers to TA2-Q01 to Q06. A later approved implementation unit materializes and validates T_A v2 under the contract Don approves, with its own reversible install boundary.
