<!--
---
title: "P2R-06a: T_A v2 design repairs"
description: "Amend P2R-06: repair the nine PR #6 review findings, bind Don's 2026-10-16 design decisions (component sSFR view, directional half-widths, high-redshift binning, joint mass-SFR candidate pair, partition exposure record), and refresh the review surface"
author: "Claude (coordinator)"
date: "2026-10-16"
version: "1.2"
status: "Queued, GPT pre-run review complete; named builder dispatch pending"
amends: "/opt/agents/repos/spec/2026-10/2026-10-05-cosmos2025-spec-p2r-06-ta-v2-design.md"
tags:
  - type: specification
  - domain: [feature-engineering, sed-fitting]
  - tech: [python, postgresql]
related_documents:
  - "[Parent spec P2R-06](/opt/agents/repos/spec/2026-10/2026-10-05-cosmos2025-spec-p2r-06-ta-v2-design.md)"
  - "[Repository instructions](/opt/agents/repos/cosmos2025-anomalies/AGENTS.md)"
  - "[P2R-06 review surface](/opt/agents/repos/cosmos2025-anomalies/docs/research/ta-v2-design/review.md)"
  - "[P2R-06 worklog](/opt/agents/repos/cosmos2025-anomalies/work-logs/worklog-2026-10-05-p2r06-ta-v2-design.md)"
---
-->

# Spec P2R-06a: T_A v2 design repairs

Repo mode, amendment of P2R-06. Gates A1.1 to A1.9. Parent PR #6 (radioastronomyio/cosmos2025-anomalies) merged on 2026-10-16 under Don's separate closeout instruction. Executes on a new branch `task/p2r06a-ta-v2-design-repairs` from the merged `main`; closeout opens one amendment PR referencing PR #6. Builder: the occupant Don names at dispatch (Kilo / GLM-5.3 built P2R-06). Independent scientific review of the repaired PR: GPT (Codex), which must not also hold the builder seat. The PR review bots rerun on push.

Authority: Don approved writing this spec on 2026-10-16 at 17:44 EDT ("Write it, GPT will review before running. Approved, execute."), Action Registry `recdrZoPWx6IaizkN`. GPT-6 completed pre-run review on 2026-10-16 under Don's instruction, "Standard review. Make any reasonable changes before execution." Version 1.1 incorporated that review; version 1.2 only reconciles the lifecycle after the separately instructed parent merge. A named builder dispatch remains the execution boundary. This review does not assign GPT the builder seat. Merging the amendment PR, answering the TA2 questions, P2R-07 dispatch, the MetaMCP cutover and the upstream report are outside this unit.

Parent-closeout authority, Don on 2026-10-16: "This repo needs its branch closed out and back on main so the spec can run. Approved, execute. The PR is still open it appears also." Codex / GPT-6 performed that separately instructed merge. Parent merge commit: `156cb9eee863a9fabd14e9f828991042fbe59d4b`; reviewed regression baseline: `d4bc1a240c0b6b874e875164896e5a5791af69c8`. The nine review findings remain repair obligations, and the design remains proposed, not adopted. The closeout worklog is `/opt/agents/repos/work-logs/2026-10-16-cosmos2025-worklog-00-p2r06-branch-closeout.md` (ML01-local central record).

Downstream: P2R-07 (development-only fitting) does not dispatch until Don answers TA2-Q01 to TA2-Q08 on the repaired review surface.

---

## 1. Objective

The PR #6 contract, validator and review surface are repaired so that each executable rule has a discriminating check, and scientific limitations or future execution promises are identified separately from what the validator proves. Each of the nine review findings (section 9) has a fixture or mutation that is shown to fail on the d4bc1a2 behaviour and pass on the repaired one. The five design decisions of 2026-10-16 are bound into the contract as `proposed_not_adopted` material: a component-built, non-rankable sSFR view with a separately named LePhare non-additivity context field; LePhare directional half-widths selected by the sign of the conditionally centered residual; a C1 binning rule with an explicit high-redshift boundary and tested support limits; a joint mass-SFR candidate pair alongside the marginal surfaces repaired by A1.2 and A1.3; and a partition exposure record with a development-only query rule. The review surface states what validation actually proves, adds closed questions TA2-Q07 and TA2-Q08, and no newly computed catalog fit, ranking or formal holdout evaluation appears in the diff. The exposure log necessarily carries the already-reported full-catalog summaries from Appendix A.

---

## 2. Why this exists

PR #6 reported 28/28 synthetic cases and 9/9 mutations caught while its contract and validator disagreed in at least nine places (Greptile review 5417842122 and Codex review 5417892132, both on head `d4bc1a2`). Two examples are reproducible from the branch. FX-06a asserts `delta_ssfr_100_dex == delta_sfr_100_dex - delta_mass_dex` while its own expected values are 0.69897 and 0.19897. A type-1 source with valid masses receives a finite `residual_mass_dex` although the population contract makes it audit-only. This is the failure class "contract stated, never enforced": the validator saw happy paths and a short mutation list, and nothing compared each stated rule against behaviour. The danger is silent. A false identity or a leaked population types cleanly, validates cleanly, and would enter a candidate ranking.

Coordinator queries on 2026-10-16 sized the findings on real data (Appendix A). Those reported measurements scoped this repair. They are prior findings, not newly frozen inputs or parameter bounds. Mathematical identities, inherited domain constants and explicitly declared synthetic expectations retain their stated roles.

The parent spec has ten defects, and they are the author's (Claude, coordinator), not the executor's. Section 8 lists them for the defect register.

**This unit writes no database object, fits nothing to the catalog, computes no new real-data residual, ranking or formal holdout evaluation, and changes no sealed P2R-05 artefact. Synthetic computation and transcription of historical exposure evidence are permitted.**

---

## 3. Inheritance and changes

P2R-06 sections 3, 4, 5.3, 5.4, 7 and 8 carry over unless changed here.

- **Lifecycle skills by absolute path.** The runner does not register skills; read and follow `/opt/agents/repos/local-agent-skills/skills/spec-startup/SKILL.md` before A1.1 and `/opt/agents/repos/local-agent-skills/skills/spec-closeout/SKILL.md` at A1.9. The P2R-06 worklog records that neither skill "exists in this execution environment"; both exist at these paths. Startup preflight runs on the clean merged `main` and creates the amendment branch under the repository convention.
- **Branch and PR.** Startup verifies a clean checkout on `main`, that PR #6 is merged at `156cb9eee863a9fabd14e9f828991042fbe59d4b`, and that local `main` and `origin/main` equal that merge commit. Confirm the reviewed regression baseline `d4bc1a240c0b6b874e875164896e5a5791af69c8` is an ancestor and that `docs/research/ta-v2-design/`, `src/inspection/validate_ta_v2_design.py` and `tests/test_ta_v2_design_contract.py` match that baseline. Then create `task/p2r06a-ta-v2-design-repairs` from `main`; commits land there and closeout pushes only that branch and opens one amendment PR linking PR #6. The branch uses the existing P2R series/slug convention without creating an issue just to allocate a number. Unexpected intervening work or an existing amendment branch stops startup for reconciliation; do not reset or overwrite it. No merge, no force-push, no push or direct edits to `main`. Preserve the parent branch.
- **Database reads, narrowed.** By default this unit reads nothing from the database. The single permitted read is the optional development-only support count in A1.5, under its stated constraints, through the read-only analyst access recorded in `AGENTS.md`. Read-only session/role checks solely needed to establish the optional count's analyst boundary are also allowed; they return no source estimates. Skip the optional count if that boundary cannot be established. Any other source-data read is a stop condition.

---

## 4. Execution environment

| Item | Value |
|---|---|
| Executor requirement | box-required on ML01 (repository, pinned local evidence, optional analyst read in A1.5) |
| Agent runtime | Named by Don at dispatch |
| Reasoning effort | High for A1.3, A1.4, A1.5 and A1.7 |
| Attended | GPT reviews this spec before dispatch. The run does not pause; Don reviews the repaired PR and answers the TA2 questions afterwards |
| Toolchain | Repository contract per `AGENTS.md`; pytest via `/opt/agents/venv` as recorded in the P2R-06 worklog |

Effects: repository documents, a pure validator and tests, lifecycle records, and the expressly authorized amendment-branch push and new amendment PR. Reversal is a subsequent reviewed revert, preserving history. A schema change, data mutation, credential use beyond read-only analyst access, external write other than that branch/PR publication, scientific release or provenance refresh is a stop condition.

---

## 5. Scope

### 5.1 Pre-existing (do not create)

The P2R-06 deliverables at `d4bc1a2` under `docs/research/ta-v2-design/`, `src/inspection/validate_ta_v2_design.py` and `tests/test_ta_v2_design_contract.py`; the P2R-06 worklog; the in-repo archived parent spec at `spec/2026-10/2026-10-05-cosmos2025-spec-p2r-06-ta-v2-design.md`; the frozen P2R-05 partitions in `analysis.specz_p2r05_splits` (12 development, 4 validation, 4 holdout tiles).

### 5.2 Modify

- `docs/research/ta-v2-design/`: `feature-contract.yaml` (version to `0.2.0-proposed`), `input-contract.md`, `input-identity.json`, `scientific-design.md`, `evaluation-protocol.md`, `fixtures.json`, `validation-results.json`, `review.md`, `README.md`.
- `docs/research/ta-v2-design/exposure-log.md` (new).
- `src/inspection/validate_ta_v2_design.py`, `tests/test_ta_v2_design_contract.py`.
- Interior indexes the docs pass touches: `src/inspection/README.md`, `tests/README.md`, `docs/research/README.md`, `docs/README.md`, `spec/README.md`, `spec/2026-10/README.md`, `work-logs/README.md`. These indexes may describe the amended package; no unrelated roadmap revision is authorized.
- `work-logs/worklog-2026-10-05-p2r06a-ta-v2-design-repairs.md` (new).
- In `work-logs/worklog-2026-10-05-p2r06-ta-v2-design.md`, only the frontmatter `status` value and the summary-table status cell, which still read in-progress although the unit closed. Justify the correction in the amendment worklog.
- At closeout, per `spec-closeout`: this spec's in-repo archive copy under `spec/2026-10/`, the central archive move, the central registry row, and the defect-register rows from section 8 in `/opt/agents/repos/spec/spec-defect-register.md`. Allocate register IDs at append time; SD/RV identifiers here are local references, not global register IDs.
- `staging/2026-10-16-p2r06a-execution/` for temporary regression baselines, outputs and an interior README, all ML01-local and gitignored. Preserve scratch artifacts; do not delete them. Durable worklog checkpoints include the evidence inline, not only staging links.

### 5.3 Do not touch

- `docs/project-state.md`. The coordinator-reported slope reversal (Appendix B) is recorded in the exposure log and the design rationale as a labelled prior finding. Promoting it to a frozen input is Don's decision.
- The parent worklog's gate records and seal. An amendment does not reopen its parent's execution record; only the stale status field is corrected.
- Repository-root `README.md`, `ROADMAP.md` and `src/README.md`. Their retired super-anomaly and multi-axis selection language is real drift, queued as a separate documentation unit so this repair does not widen.
- Everything P2R-06 section 5.4 lists.

---

## 6. Gates

Each gate ends in one commit referencing its gate ID (`A1.n`) with the `spec-closeout` trailer block, and a worklog checkpoint stating its evidence inline. Every repaired executable rule gets a discriminating fixture or mutation; scientific limitations and future execution promises are documented as such, not claimed to be machine-proved. For R1 to R9, preserve the old validator, contract and required inputs from the reviewed starting commit in a scratch copy. Run an assertion on its actual old behaviour, then on the repair, recording expected and observed values and exit codes. A missing newly introduced API or an import failure is not evidence of the old defect. A thin assertion adapter may observe old outputs but may not implement the repair. New capabilities absent from the old contract, such as joint scores, instead require an independent numerical oracle and a deliberately wrong variant rejected for its intended reason. Do not mutate the live checkout to obtain a baseline or invoke a baseline command that overwrites committed evidence.

### A1.1 Exposure record and query rule

Create `docs/research/ta-v2-design/exposure-log.md` with three sections.

1. **Pre-partition diagnostics.** Record the May report and frozen project-state inputs, and Appendix B separately as coordinator-reported history. Predating the partitions does not prove exact overlap with today's holdout sources, particularly across the v1/v1.1 boundary. Record available source/version/date locators and unknown coverage explicitly; do not rerun the diagnostics or infer per-tile membership. Historical observations can still have influenced design, so an untouched-holdout claim is not available.
2. **2026-10-16 coordinator queries.** Transcribe Appendix A's SQL and results verbatim, retaining the administrator-role redaction. Label these as coordinator-reported executions, not independently rerun evidence. CQ1 to CQ6 have no partition exclusion and the coordinator reports all-tile coverage; CQ8 establishes the whole partition sizes, not the number of qualifying holdout sources in each earlier query. In particular, 160,158 is the full holdout partition, not the CQ2/CQ5 eligible holdout denominator. State which design change each query motivated. CQ2 used 758,304 single-code sources; CQ5 used 634,845 sources under its distinct both-code predicates. Their broad `> -99`/positivity filters are not the exact repaired contract's domain/state predicates. CQ6's zero counts do not establish absence of missing or non-finite quantiles. Do not reinterpret these counts as exact contract eligibility or rerun the queries.
3. **Prospective rule.** Exploratory queries by coordinators, reviewers and executors that compute any T_A contract output (including context) or combine estimates from both codes use development only. Bind the join by `catalog_id` and the exact inherited `run_id` from `input-identity.json`, plus `analysis.specz_p2r05_splits.assigned_split = 'development'`; do not join unqualified runs or accept missing assignments. This is the default for exploration and fitting. A later named implementation may evaluate already-frozen choices on validation, and a separately authorized one-time final evaluation may use holdout, strictly under the S5 protocol. Neither exception authorizes new exploratory choices or fitting on those partitions. Covariate-only and single-code validity counts that influence design are logged; they do not waive this unit's A1.5-only source-read boundary.

Link this record from `evaluation-protocol.md`. State that design was informed by full-catalog summaries containing holdout information. No designated one-time evaluation of a frozen T_A model has yet run; do not claim that no outcome-derived holdout information was seen. Future parameters are fitted on development only. Keep the partitions and disclose that the eventual holdout assessment is not an untouched test of feature-family selection. TA2-Q08 asks Don to accept this qualified claim, not to restore an unseen-holdout status.

**Validation:**

- [ ] Each Appendix A SQL block and reported result is reproduced byte-for-byte; evidence labels and qualifications are separate text. Record a comparison of both SQL and result text, not SQL alone.
- [ ] Query-specific populations remain distinct from CQ8's partition totals and from the repaired eligibility contract.
- [ ] The prospective rule names the exact join/run/split requirements and permits only separately authorized, protocol-bound validation/final evaluation exceptions.
- [ ] No protocol or review claim asserts an unexposed holdout or zero historical outcome-derived exposure.
- [ ] No query was executed in this gate.

### A1.2 Population gating and SFR scale states (R2, R3, R8)

- **R3.** The `POP-MASS` predicate in `feature-contract.yaml` carries the conditions `input-contract.md` already states for it: CIGALE mass error present and nonnegative. A validator check compares the two artefacts' `POP-MASS` conditions so they cannot drift apart again.
- **R8 and the analogous SFR path.** Mass residuals/scores require `POP-MASS`; each SFR residual/score requires its own `POP-SFR-T`, independently of mass membership. Non-members receive NULL with `not_in_population`. Every joint output additionally requires the relevant intersection (A1.7). Raw deltas remain audit outputs where their point-domain states permit them. A single eligibility decision drives the population flag and its downstream gates; the evaluator may not ignore the declared predicate.
- **R2.** Both SFR scale machines run, their states and reasons are emitted, and each score requires population membership, point comparability and valid directional scale. The 0.3 relative-error limit is inclusive. Check finite inputs and complete quantile ordering `l68 <= med <= u68`; `u68 >= l68` alone is insufficient. Declare precedence: population/domain guards first, then scale/uncertainty guards, then arithmetic. A zero residual does not bypass these guards.

Fixtures: type 0 with valid masses and NULL CIGALE mass error, and the same with a negative error, are outside `POP-MASS` with finite raw delta and NULL residual and score; type 1, type 2 and unknown type with valid masses give the same pattern with reason `not_in_population`; CIGALE SFR relative error 0.31 gives the declared out-of-domain scale state and a NULL score, 0.29 gives a finite score; reversed quantiles, a median outside ordered endpoints, and non-finite uncertainty give NULL scores with reasons. Test type-1/2/unknown SFR sources, the exactly-0.3 boundary, and independence of mass-only and each SFR population.

**Validation:**

- [ ] Each defect-revealing fixture fails against `d4bc1a2` and passes after repair; already-correct boundary controls pass on both. Record both runs and distinguish the roles.
- [ ] Mutations caught with their intended reasons: error clause removed from `POP-MASS`; population gate removed from residual emission; SFR score gated on point state only; SFR population gate removed; the two artefacts' `POP-MASS` conditions made to disagree; median-containment check removed.
- [ ] `delta_mass_dex` stays bit-identical on finite, point-domain-valid audit controls. New non-finite/domain-invalid cases must fail closed; retaining a defective old numeric value is not an invariant.

### A1.3 Directional LePhare half-widths (R9; decision 2)

Replace `sigma_mass_lp_dex` and `sigma_sfr_lp_dex` with lower and upper half-widths, `*_lp_lo_dex = med - l68` and `*_lp_hi_dex = u68 - med`. The width entering a normalized score is selected by the sign of that quantity's **conditionally centered residual**, never the raw delta: a positive residual (LePhare above its expected value) uses the lower half-width, a negative residual uses the upper, and an exactly zero residual gives score zero only after population, point and uncertainty validity are established. For zero residual, both widths must be strictly positive; otherwise emit `degenerate_quantile_width` and NULL. For nonzero residual, the selected width must be strictly positive; an unselected zero width is allowed if complete quantile ordering still holds. Missing, negative or non-finite widths never produce a score. Raw deltas and eligible residuals remain available when only the scale is unsupported. CIGALE stays on the existing first-order approximation inside the 0.3 relative-error domain. State that the `sigma_sys_*` determination rule (1.4826 times the MAD of residual over scale equals 1 on development) uses the directional scale. Its declared parameter domain is finite and nonnegative. The repaired contract must state a deterministic solve/tolerance policy and the unsupported result when no admissible solution exists; it must not silently fabricate a negative floor or restore the historical constants. Synthetic no-solution and zero-spread cases exercise that policy. This unit fits no real-data floor, and these proposed scale details remain under TA2-Q02.

Fixtures: an asymmetric posterior (lower 0.05, upper 0.30) scored with a positive and with a negative residual, each using its correct side; a raw delta and centered residual of opposite sign (delta -0.10, expected -0.21, residual +0.11), where the side follows the residual; a zero-width selected side giving NULL with reason, and a zero-width unselected side leaving the score finite. Add zero residual with valid widths (zero score), zero residual with missing/reversed/zero widths (NULL), and a median outside otherwise ordered endpoints (NULL).

Appendix A reports zero zero-width/reversed-quantile counts under CQ6's 634,845-source proxy selection; that query did not count missing quantiles or establish exact amended eligibility. The guard is fail-closed protection, not a correction for observed data.

**Validation:**

- [ ] Asymmetric-score and wrong-side assertions demonstrate the old symmetric behaviour numerically. New width fields have explicit expected values, and their mutations fail for the intended reason; baseline API absence is not the discriminator.
- [ ] Mutations caught: symmetric average restored; side chosen by raw delta; zero-width guard removed.

### A1.4 sSFR component view and non-additivity context (R1; decision 1)

- `delta_ssfr_T_dex := (lephare.sfr_med - lephare.mass_med) - (log10(cigale.sfr_T) - log10(cigale.mass))`, equal to `delta_sfr_T_dex - delta_mass_dex` by construction. Kind `derived_view`, `rankable: false`, emitted only when both parent raw-delta states permit. Its domain depends on the component fields, not native `lephare.ssfr_med`. Missing or invalid native sSFR can null the context field without nulling this component view. `score_ssfr_T` remains NULL with explicit `unsupported_correlated_errors` state/reason; it is never a ranking input.
- New `ctx_lp_ssfr_nonadditivity_dex := lephare.ssfr_med - (lephare.sfr_med - lephare.mass_med)` when all three are point-valid. `context_only`; never a predictor or ranking input. Its description calls it a difference between LePhare summary estimators. Its interpretation guard states that it does not establish posterior bimodality, a degenerate fit or a physical cause.
- `lephare.ssfr_med` appears in no rankable or raw-disagreement formula.
- Validator rule: every output declaring an `algebraic_coupling` is checked numerically on every fixture where both sides are defined, absolute tolerance 1e-12 on full-precision computations, not on rounded prose values. A failing declared identity is a validation failure.

Fixtures: FX-06a rewritten with its existing inputs, expecting `delta_ssfr_100_dex = 0.5 - log10(2)` and `ctx_lp_ssfr_nonadditivity_dex = 0.5`; a case where native `ssfr_med` equals the component value, expecting context 0. Test absent and out-of-domain native sSFR with valid components, expecting the component delta to survive and the context to be NULL. Use a deterministic mathematical counterexample to the implication "non-additivity proves bimodality": independent Exp(1) variables X and Z with Y = X + Z have joint density exp(-Y) on 0 <= X <= Y, a unimodal log-concave distribution. Median(X) = median(Y-X) = log(2); median(Y) solves exp(-m)*(1+m) = 1/2. The non-additivity is 2*log(2)-m, about -0.29205. Quantization is optional and must have separately checked effects; merely seeding an unspecified skewed sample does not prove unimodality or a >0.2 gap. Label this as a synthetic illustration, not a model of LePhare's posterior.

Appendix A query CQ2 sized the native gap: mean -0.015 dex; 29,190 of 758,304 type-0 sources exceed 0.1 dex in absolute value, 7,795 exceed 0.3 and 1,693 exceed 1.

**Validation:**

- [ ] The rewritten FX-06a passes at full precision. The original native-sSFR formula on the unchanged record violates the coupling numerically; the repaired component formula agrees to tolerance. Both timescales and native-sSFR-independent eligibility are tested.
- [ ] Mutations caught: native `ssfr_med` reinserted into `delta_ssfr_T_dex`; a scratch contract declaring a false coupling; `ctx_lp_ssfr_nonadditivity_dex` marked rankable.

### A1.5 C1 binning and center support (R7; decision 3)

- **Binning rule.** Redshift edges are development-tile quantile edges with a forced edge at z = 5.5 inserted, declared as `kind: declared_domain` with its rationale (the coordinator-reported mass-slope reversal, Appendix B). Retain the declared six redshift quantile bins and five magnitude quantile bins before inserting the edge. Use deterministic linear-interpolation quantiles, collapse duplicate edges, and record effective bin counts. Insert 5.5 only when strictly inside the development support interval; do not extend the hull or manufacture empty support beyond it. Bins are left-closed/right-open except the final endpoint is included; z = 5.5 belongs to the upper bin. No resulting cell straddles 5.5. Missing/non-finite covariates are unsupported. Additional fixed edges require a later named change, not builder discretion. Appendix B describes a trend against mean mass, not the permitted brightness covariate; the forced boundary is an approved proposal, not evidence of a physical discontinuity or guaranteed adequate resolution.
- **Optional support evidence.** One development-only count under the exact repaired `POP-MASS` point/error predicates, in fixed redshift-magnitude support-audit bins declared before the query. These are not fitted quantile cells: calculating real-data quantile edges remains outside this unit. Join source IDs to `catalog_id`, bind the exact inherited `run_id` and `assigned_split = 'development'`, and reject unknown/duplicate assignments. Mass/error columns appear only inside single-code validity predicates; no SFR selection, cross-code arithmetic, estimates, averages or quantiles are returned. Record SQL, role/session read-only verification and counts in the exposure log. The read must not influence new bin edges or thresholds here. Skip it if the analyst boundary is unavailable; actual fitted-cell support remains unknown until P2R-07 whether or not this optional count runs.
- **Support enforcement.** The evaluator applies `center_min_cell_support` to support counts: a cell at or above it gives `cell`; otherwise a z-only cell at or above it gives `z_fallback`; otherwise `global_fallback`; covariates outside the development edges give `out_of_hull` with the existing global-center fallback. Count unique eligible source IDs at each level; duplicated rows do not manufacture support. Record both the requested cell and fallback used. Global fallback does not preserve local high-redshift structure, and no test or review may claim otherwise.
- **Synthetic construction.** The validator gains a pure function that builds edges (quantile plus forced), cell medians, support counts and fallbacks from synthetic fixture rows only. It enforces fit-request partition/duplicate guards on those rows, reads declared contract parameters rather than hardcoded mirrors, and has no database path.

Fixtures: support boundary (cell 200 gives `cell`, 199 gives `z_fallback`, z-only 199 gives `global_fallback`); a synthetic slope reversal in which delta depends on magnitude with opposite slope above z = 5.5 and the quantile top bin spans roughly z 3 to 8. With the forced edge, on-trend synthetic sources above 5.5 have absolute residuals below a declared tolerance; without it, their residuals carry a magnitude-dependent offset above that tolerance. Declare tolerance and adequate per-cell support before building the demonstration. Separately test a sparse high-redshift case that falls back and retains a known bias, duplicate quantile edges, z exactly 5.5, the maximum endpoint, and development support lying wholly on one side of 5.5.

**Validation:**

- [ ] Mutations caught: support counts ignored; forced edge removed.
- [ ] The support-boundary fixture fails against `d4bc1a2` (which uses any present cell) and passes after repair.
- [ ] If the optional query ran, its text and counts are in the exposure log and it satisfies every listed constraint by inspection recorded in the worklog.

### A1.6 Partition and identity fail-closed (R4, R5, R6)

- **R4.** Every fitted row needs an explicit, valid `development` assignment. Missing assignments reject as `unassigned_partition`; unknown labels, conflicting assignments and duplicate training IDs reject. Apply this guard to every synthetic center, scale and covariance fitter, not only a detached demonstration request.
- **R5.** `authorizing_spec` entries reference the in-repo archive copy by repository-relative path (`spec/2026-10/2026-10-05-cosmos2025-spec-p2r-06-ta-v2-design.md`) with its SHA-256. A missing file fails as `identity_missing:authorizing_spec`; a digest mismatch fails as `identity_mismatch:authorizing_spec`. No skip path exists. Required parent and amendment identities are an explicit manifest set at closeout, with schema validation: deleting an entry or its digest must fail as well. Resolve paths against the repository root, not the working directory; no search-order fallback. The central archive path is provenance only. The amendment becomes required at A1.9 once its archive copy exists; record that transition explicitly so final validation cannot silently revert to parent-only checking.
- **R6.** Record the actual interpreter and argument vector, resolve the script from the repository root, and provide a shell-safe rendering. The reproduction test executes that argument vector with `--results` redirected to a distinct scratch file, never the committed results file. Compare exit code, case/mutation outcomes, input hashes and semantic payload; exclude only generation time and the explicitly different output path/command representation. Never execute unparsed arbitrary result text through a shell.

**Validation:**

- [ ] New fixture FX-P5 (training ID with no assignment) is rejected.
- [ ] Against `d4bc1a2`, a scratch identity whose spec path does not exist passes, demonstrating R5. After repair it fails with `identity_missing`, and a one-byte change to the referenced copy fails with `identity_mismatch`.
- [ ] The recorded command re-executes into a different scratch output with the same semantic results; committed result bytes stay unchanged. Missing/altered files and deleted required manifest entries each fail; a non-root working directory still resolves identities correctly.

### A1.7 Joint mass-SFR candidate pair (decision 4)

For each SFR timescale T, add two `proposed_not_adopted` candidate surfaces:

- `joint_residual_distance_T`: `sqrt(r^T C_b,T^-1 r)` with `r = (residual_mass_dex, residual_sfr_T_dex)` and `C_b,T` a robust covariance of the eligible development residual vectors for timescale T, using the declared redshift-brightness cells and support hierarchy. This is dimensionless: residuals are in dex and covariance entries in dex squared. It is a covariance-normalized distance computed from unstandardized residuals, not a distance in dex or a replacement for the magnitude of a marginal residual.
- `score_joint_T`: `sqrt(z^T R_b,T^-1 z)`, with `z_k = r_k / tau_k`, and `R_b,T` a correlation matrix estimated on eligible standardized development residuals, with unit diagonal. This is distinct from the full covariance `C_b,T`; do not silently substitute one for the other. The denominator uses A1.3 directional widths and the declared CIGALE/systematic terms. It is an exploratory scale convention, not a known measurement-error covariance. Unit diagonal does not assert that the empirical variance of every z component is one. Cross-code and within-code mass-SFR correlations remain unknown.

Requirements:

- **Complete proposed estimator.** Before the fit-fixture implementation, declare one deterministic robust covariance procedure with objective, centering convention, tuning constants, minimum support, fallback hierarchy, degeneracy behavior, seed/tie rules if applicable, and exact construction of C and R. A family name or library default is insufficient. A1.7 authorizes choosing and documenting this proposal on synthetic evidence, not fitting or adopting it. Explicitly distinguish covariance centering from the fixed residual origin in the distance formula; do not introduce an undisclosed second conditional mean. Test the fitter on synthetic rows, not only hand-supplied matrices. Its estimates must actually feed the score evaluator.
- **Numerical guards.** Propose a finite clamp with `0 < joint_rho_clamp < 1` and a numerical-conditioning rationale. The illustrative 0.8-correlation examples are kernel checks on the stated matrices, not a requirement to choose a guard value that makes them pass unchanged. Also test the complete estimator/regularizer/scorer path against the exact effective matrix under the proposed guard. Define any eigenvalue floor on the dimensionless correlation matrix and reconstruct C using its positive marginal scales; do not apply an unexplained absolute floor to dex-squared values. Record pre/post regularization and flags. Such regularization can change rankings and remains a proposal under TA2-Q07, even when motivated numerically. Non-finite matrices, absent/zero marginal spread, insufficient global support or failed estimation produce explicit unsupported states, not invented covariance. The clamp test asserts the exact declared post-clamp value, not mere finiteness.
- **Domain and fit population.** The unstandardized distance requires `POP-MASS` intersected with `POP-SFR-T`, both residuals, and a supported covariance. The standardized score additionally requires both valid directional scales. Fit their covariance/correlation on their respective development-only populations, counted separately for each timescale; never borrow mass-only support counts or require both SFR timescales. Out-of-domain scale nulls the standardized score but may leave the unstandardized distance valid. Emit per-timescale state/reason, support count and fallback, covariance-model identity, inherited center/scale identities and regularization flag. Invalid or missing SFR nulls both relevant joint outputs without nulling a valid mass marginal.
- Interpretation guard: no chi-square, p-value, significance or probability label.
- **Centers and coexistence.** Reuse the selected C0/C1 mass center and the parent's S0 per-timescale SFR center. Conditional covariance does not authorize adding a conditional SFR mean. The declared cell grid remains fixed by the development-only binning rule even when C0 supplies the mass center. Marginal surfaces remain exactly as repaired by A1.2/A1.3; adding joint outputs must not change them. No combined ranker, maximum, union, quota, selection budget, low-correlation veto or automatic disable is defined in this unit.
- Protocol: add both surfaces for each timescale to the declared comparison set as candidates requiring later adoption, not automatic candidate-selection channels. Separate the criteria into mathematical correctness (synthetic), stability (development tile jackknife) and usefulness (validation-tile description of what a joint surface adds beyond the marginal surfaces, including its composition by support state, quantile and floor conditions and coverage). No criterion may reward elliptical distance by construction. Fully specify the descriptive stability/usefulness summaries and comparison set before any later validation data are read. For any top-K overlap description, K and tie handling must be fixed in the approved future protocol, not chosen after viewing rankings; no budget or quota is adopted here. Tile jackknife estimates are development-only, and absent spectroscopic survey labels cannot become a requirement for the non-spectroscopic sample. State limitations and evidence against adoption for Don's review, without inventing automatic thresholds.
- The raw full-catalog correlation in Appendix A (CQ5, r about -0.30, uncentered, censored regime included) is neither a parameter nor a bound for anything in the contract. The protocol says so.

Fixtures (expected values checked independently by two reviewers on 2026-10-16):

1. Correlation 0.8, unit scales: (3.0, 3.0) gives 3.162; (2.2, -2.2) gives 6.957. The off-pattern source outranks the on-pattern one.
2. Correlation 0: (2.5, 2.5) gives 3.536; (3.4, 0) gives 3.400. The surface is emitted; no veto applies.
3. Mixture covariance [[3.4, -2.5], [-2.5, 3.4]]: C at (4, -4) gives 2.329; D at (3, 3) gives 4.472. Recorded as a known limitation. The same fixture asserts that C's marginal magnitudes (4) exceed D's (3), so the marginal surfaces retain C above D.
4. Clamp: a supported cell with local correlation 0.9999, and a sparse cell falling back to a global correlation also set beyond the clamp. Both are clamped, finite and carry the recorded state. A sparse-cell case with only the local value extreme does not test the clamp, because the fallback replaces it.
5. Censored/non-comparable SFR and non-`POP-MASS` sources null both joint outputs with reasons. Out-of-domain scale nulls only `score_joint_T` if the residual distance is otherwise supported. Test valid instantaneous/invalid 100-Myr SFR and the reverse, zero covariance spread, absent model support, duplicate fitting rows, and missing/held-out partition assignments.
6. Pooled-correlation demonstrations: two bins with internal correlation 0 and centers (1, -1) and (-1, 1) give a strongly negative pooled correlation; a core with correlation -0.7 mixed with uncorrelated noise gives a pooled magnitude well below 0.7. Specify means, component variances and mixture weights and derive the expected pooled moments analytically; for equal zero-mean component variances and a 50/50 mixture of correlations -0.7 and 0, the pooled correlation is -0.35, not -0.30.

**Validation:**

- [ ] All six fixture families pass; use full-precision independent formula/moment oracles and 1e-3 only for the rounded numerical examples above. Fitter fixtures separately check a known core, contamination response, support fallback and degeneracy; documentation does not claim that one example proves robustness for arbitrary mixtures.
- [ ] Mutations caught: a low-correlation veto (fixture 2); a covariance fit request containing a validation-assigned row (partition guard); marginal outputs removed or altered when joint outputs are present; joint output emitted for a non-`POP-MASS` source; clamp removed (fixture 4, exact effective-correlation assertion); full covariance replaced by unit-diagonal correlation; actual covariance-fitting guard bypassed; native SFR-timescale populations incorrectly intersected.

### A1.8 Naming restraint and declared limitations

- Output names and `description` fields contain none of "bimodal", "multimodal", "secure redshift", "true anomaly" or "significance". `interpretation_guard` fields, which state what an output does not establish, are exempt. A structural check enforces this.
- `scientific-design.md` and `review.md` add these declared limitations. T_A is conditional on LePhare's redshift. A confident catastrophic photo-z can produce large T_A at low T_z, so low T_z does not establish a correct redshift; spec-z under the S5 conditions is the diagnostic for that. A fitted joint covariance can absorb a real rare population (A1.7 fixture 3).

**Validation:**

- [ ] Mutation caught: the phrase "bimodality flag" inserted into a `description` field.
- [ ] Both documents separately state shared-redshift dependence, lack of a low-T_z redshift guarantee, covariance masking, and inability to infer bimodality from median non-additivity. Each claim is checked in context, not by counting phrases.

### A1.9 Review surface, results and closeout

`review.md`:

- Design identity updated: contract `0.2.0-proposed`, counts from the regenerated results, P2R-06a authority.
- A response table mapping each of the eleven PR #6 review comments to R1 to R9, the change made, and the discriminating fixture or mutation ID.
- Claims corrected: remove statements that the validator enforced rules it did not enforce at `d4bc1a2`, and state what the repaired validation covers and does not.
- Findings TA2-F01 to F12 revised where they changed, plus new findings with evidence for the five decisions. The forced z = 5.5 edge is labelled as resting on a coordinator-reported prior finding not reproduced in this unit.
- TA2-Q01 to Q06 retain their IDs and existing unanswered state, with any necessary wording changes shown in a change table. No approved S5 question or answer is edited. Add:

| ID | Closed approval question |
|---|---|
| TA2-Q07 | Approve the joint mass-SFR candidate pair as declared comparison candidates alongside the repaired marginal surfaces, with any selection budget or quota left to a separate decision? |
| TA2-Q08 | Accept the documented design-stage exposure and the qualified future holdout claim, with development-only exploration/fitting, separately authorized protocol-bound validation/final evaluation, and no reroll? |

Closeout follows `AGENTS.md` and `/opt/agents/repos/local-agent-skills/skills/spec-closeout/SKILL.md`. Archive this spec to the central `spec/2026-10/` and the in-repo `spec/2026-10/` byte-identically; add its identity entry to `input-identity.json`; then regenerate `validation-results.json`. The reviewed queue spec is frozen for execution; archive bytes must match its startup digest. Do not rewrite this spec to make implementation pass. Final validation requires the parent and amendment manifest entries. Source-manifest and P2R-05 identity values are compared unchanged, never refreshed. Push only `task/p2r06a-ta-v2-design-repairs` and open one amendment PR against `main`, linking merged PR #6 and listing A1.1 to A1.9 and the R1 to R9 mapping. Do not merge. Seal the amendment worklog with per-gate SHAs. Append the registry row and record the section 8 parent defects and section 8.1 pre-run amendment defects in the central defect register, with its required pre-image capture and normal ID allocation. The parent-worklog status-only correction is the explicit exception to the lifecycle's closed-parent rule; its gates, seal and registry row stay unchanged. In the amendment worklog record exact commit hashes from git; do not claim its own containing commit hash inside that same commit.

**Validation:**

- [ ] One commit per gate A1.1 to A1.9 on `task/p2r06a-ta-v2-design-repairs`, each with the trailer block; branch pushed; exactly one amendment PR open and unmerged, linking merged PR #6.
- [ ] Run all applicable pure/offline tests; inspect collection/fixtures first so no install, network, database or sealed-product writer can run. Record any excluded integration checks and their reason. All required synthetic checks pass; the validator exits 0 on the repaired contract and nonzero, with the intended reason, on every mutation named in this spec; results record command, input and contract hashes and exit codes.
- [ ] Each of R1 to R9 has worklog evidence of a fixture or mutation failing on `d4bc1a2`, using meaningful behaviour assertions. An absent new API does not count; new capabilities use independent oracles and deliberate wrong variants.
- [ ] `git diff --name-only d4bc1a2..HEAD` contains only this amendment's section 5.2 allowlist, with its field-level restrictions enforced. The broader parent list grants no new edit permission here; in particular, project-state and frozen parent-spec bytes stay unchanged.
- [ ] The in-repo and central archive copies of this spec have identical SHA-256, and `input-identity.json` verifies both authorizing specs with no skip path.
- [ ] The registry row's `model` equals the `Model:` trailer, and the defect register records the ten parent entries and the six section 8.1 pre-run entries with correct attribution and no duplicated global IDs.
- [ ] The handoff names TA2-Q01 to Q08 and states that P2R-07, fitting, installation and publication await separate approval.

---

## 7. Constraints

- **Do not fit, rank or read outcomes.** Every center, covariance and score newly computed in this unit uses synthetic rows. Historical real-data values appear only as labelled exposure evidence, never as fitted parameters or fixture inputs.
- **Do not rerun Appendix A or compute any full-catalog statistic.** The exposure is recorded once; repeating it widens it.
- **Do not add a selection budget, quota, scientific adoption/rejection threshold or low-correlation veto.** These selection policies were proposed in review and deliberately left out. Domain, partition, identity and numerical-invalidity rejection guards remain required. Choosing a new selection policy is a scientific decision Don has not made; numerical/domain guards are the explicitly permitted proposals above.
- **Do not promote coordinator observations into frozen facts or parameter bounds.** Their evidence status stays explicit; the raw -0.30 correlation bounds nothing. This does not withdraw inherited frozen inputs, declared mathematical/domain constants, the approved proposed 5.5 boundary, or synthetic oracle values.
- **Do not repair the repository-root README or ROADMAP drift here.** It is real, and it is a separate unit.
- **Never delete, never merge, never force-push.** Retired content moves to `recycle-bin/` with worklog justification, per `AGENTS.md`.

---

## 8. Spec defects (author's)

These P2R-06 defects are attributed to its author (Claude, coordinator). Record them at closeout.

| ID | Defect | Class | Surfaced as |
|---|---|---|---|
| SD-1 | Declared algebraic relationships were not required to be numerically enforced | Contract stated, never enforced | R1 |
| SD-2 | The mutation list omitted scale-state bypass and population-gate removal | Detector, not discriminator | R2, R8 |
| SD-3 | The partition discriminator covered held-out IDs but not unassigned IDs | Domain unenumerated | R4 |
| SD-4 | Identities were to be compared by content, but closeout moved the authorizing spec and absence was not required to fail | Lifecycle ordering; fail-open | R5 |
| SD-5 | Results had to record the command, not show that it re-executes | Detector, not discriminator | R6 |
| SD-6 | Minimum support was required in the contract with no fallback discriminator | Contract stated, never enforced | R7 |
| SD-7 | "Keep asymmetric information where supported" carried no validation | Contract stated, never enforced | R9 |
| SD-8 | No consistency check between input-contract population conditions and feature-contract predicates | Contract stated, never enforced | R3 |
| SD-9 | The design lacked a way to record non-frozen coordinator history, assess bin-resolution limitations and disclose pre-partition/coordinator exposure; the slope reversal was not an omitted approved frozen input | Missing requirement | A1.5, A1.1 |
| SD-10 | Lifecycle skills were named without absolute `SKILL.md` paths, and the executor could not locate them | Missing requirement | P2R-06 worklog lifecycle note |

---

### 8.1 Pre-run defects in this amendment, corrected in v1.1

GPT-6 found these in the unexecuted v1.0 amendment during Don's 2026-10-16 review. They are amendment-authoring defects, not builder failures. Register them separately from SD-1 to SD-10 at closeout, pointing to this v1.1 correction record and the preserved preimage digest `5c8a8f3e77aac559128419d3e0ec62fda34d6577cb72f9a88590ee279755d96d`.

| Local ID | Defect and correction | Class | Gates |
|---|---|---|---|
| RV-1 | Blanket development-only wording contradicted planned validation; old wording denied prior outcome-derived exposure and conflated whole-partition counts with query membership. Preserve protocol-bound exceptions and qualify historical coverage. | Contradictory boundary; unsupported evidence claim | A1.1 |
| RV-2 | Zero residual bypassed uncertainty guards; complete quantile order, SFR population gating and native-sSFR-independent component eligibility were missing. Define precedence and discriminating cases. | Domain unenumerated | A1.2-A1.4 |
| RV-3 | All fixtures were required to fail on the baseline, including already-correct controls and absent new interfaces; rounded values conflicted with strict equality. Separate regression controls/new capabilities, and use independent full-precision oracles. | Unverifiable validation | A1.2-A1.7 |
| RV-4 | Quantile construction, forced-edge endpoints and fallback behavior were underspecified; optional counts could require forbidden real-data bin fitting. Define deterministic bins and fixed support-audit counts. | Missing requirement; scope contradiction | A1.5 |
| RV-5 | Joint covariance/correlation definitions, per-timescale support, scale-only failures and effective-clamp assertions were ambiguous; estimator requirements did not require an exercised fit path. Specify each surface and its domain, fit evidence and regularization semantics. | Contract stated, never enforced | A1.7 |
| RV-6 | Closeout omitted indexes, widened the allowlist back to the parent's, permitted incomplete identity manifests and could replay output over committed evidence. Enumerate exact surfaces, required identities and scratch-only reproduction. | Lifecycle ordering; fail-open | A1.6, A1.9 |

The review changes no SQL or reported-result text in Appendix A and does not authenticate the registry record or independently rerun coordinator measurements. The spec author supplied those authority/evidence records; Don's current instruction authorizes this pre-execution revision only.

---

## 9. Review findings

| ID | Finding on `d4bc1a2` | Raised by | Coordinator sizing | Gate |
|---|---|---|---|---|
| R1 | Declared sSFR identity is false; FX-06a contradicts it | Greptile P1, Codex P2 | CQ2: 29,190 type-0 sources with native gap above 0.1 dex | A1.4 |
| R2 | SFR scores ignore the scale state | Greptile P1, Codex P1 | Not sized | A1.2 |
| R3 | `POP-MASS` omits CIGALE mass-error validity | Greptile P1 | CQ1: 0 of 634,845 affected | A1.2 |
| R4 | Fit-request IDs with no assignment pass | Greptile P2 | Synthetic only | A1.6 |
| R5 | A missing authorizing spec skips verification | Greptile P2 | Live on ML01: the recorded path is absent after closeout's archive move | A1.6 |
| R6 | The recorded command points under `docs/src/` | Greptile P2 | Present in `validation-results.json` | A1.6 |
| R7 | The C1 support rule is untested | Greptile P2 | Not sized | A1.5 |
| R8 | Non-`POP-MASS` sources receive residuals and scores | Codex P2 | CQ1: 8,927 non-type-0 sources with both masses valid | A1.2 |
| R9 | Symmetric LePhare widths discard direction | Codex P2 | CQ6: no zero-width sides | A1.3 |

---

## 10. Execution order

1. A1.1 exposure record (it fixes what every later claim may say)
2. A1.2 population gating and SFR scale states
3. A1.3 directional half-widths
4. A1.4 sSFR component view
5. A1.5 binning and support
6. A1.6 partition and identity
7. A1.7 joint candidate pair (depends on A1.2, A1.3 and A1.5)
8. A1.8 naming and limitations
9. A1.9 review surface and closeout

---

## 11. Executor freedom

As P2R-06 section 8, plus: one fully specified proposed robust covariance procedure and regularization within A1.7's bounds, and fixture/test organization. These are proposals for TA2-Q07, not adopted scientific policy. Additional fixed high-redshift edges are excluded from this unit. Predeclare proposed estimator details before exercising them; do not adjust them to force a desired synthetic ranking. The executor does not choose adoption thresholds, quotas, vetoes or any real-data fit.

---

## Notes

Raised in the 2026-10-16 review round among Don, Claude, GPT and Gemini (Argon). Gemini's proposals for a low-correlation veto, candidate quotas, fixed trimming cutoffs and stability limits were not adopted; GPT's objections to them are recorded in the TA2-Q07 framing rather than resolved here. Separate units queued behind this one, none of which this unit may perform: the MetaMCP cutover (the coordinator's connection still runs under an administrator role), the repository-root README and ROADMAP revision for the September 1 retirement of super-anomaly selection, and a read-only T_z I/O profiling spec for the PDF(z) pickle.

---

## Appendix A: 2026-10-16 coordinator queries (CQ1 to CQ8)

Executed by Claude through MetaMCP on `cosmos2025_v11`, under an administrator role (read-only by the MCP's query validator, not by database role; cutover pending), on 2026-10-16 between about 16:00 and 17:55 EDT, in this order. None carries a partition predicate, so CQ1 to CQ6 covered all 20 tiles. Queries rejected by the MCP validator before execution, and one connection reset, returned no data and are omitted.

**CQ1.** POP-MASS error validity and non-type-0 counts. Motivated: demoting R3 to a consistency defect; sizing R8.

```sql
SELECT count(*) FILTER (WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0) AS t0_both_mass,
       count(*) FILTER (WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0 AND c.mass_err IS NULL) AS t0_mass_no_err,
       count(*) FILTER (WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0 AND c.mass_err < 0) AS t0_mass_neg_err,
       count(*) FILTER (WHERE c.mass <= 0) AS cig_mass_nonpos,
       count(*) FILTER (WHERE l.type <> 0 AND l.mass_med > -99 AND c.mass > 0) AS non_t0_both_mass
FROM source.lephare l JOIN source.cigale c USING (id)
```

Result: t0_both_mass 634845; t0_mass_no_err 0; t0_mass_neg_err 0; cig_mass_nonpos 10; non_t0_both_mass 8927.

**CQ2.** LePhare internal sSFR non-additivity (single code; now a contract context output, so in scope of the A1.1 rule). Motivated: decision 1.

```sql
SELECT count(*) AS n,
       avg(l.ssfr_med - l.sfr_med + l.mass_med) AS mean_gap,
       min(l.ssfr_med - l.sfr_med + l.mass_med) AS min_gap,
       max(l.ssfr_med - l.sfr_med + l.mass_med) AS max_gap,
       count(*) FILTER (WHERE l.ssfr_med - l.sfr_med + l.mass_med > 0.1 OR l.ssfr_med - l.sfr_med + l.mass_med < -0.1) AS n_gt_0p1,
       count(*) FILTER (WHERE l.ssfr_med - l.sfr_med + l.mass_med > 0.3 OR l.ssfr_med - l.sfr_med + l.mass_med < -0.3) AS n_gt_0p3,
       count(*) FILTER (WHERE l.ssfr_med - l.sfr_med + l.mass_med > 1.0 OR l.ssfr_med - l.sfr_med + l.mass_med < -1.0) AS n_gt_1
FROM source.lephare l
WHERE l.type = 0 AND l.mass_med > -99 AND l.sfr_med > -99 AND l.ssfr_med > -99
```

Result: n 758304; mean_gap -0.014821081650630638; min_gap -9.786629999999999; max_gap 0.6097099999999993; n_gt_0p1 29190; n_gt_0p3 7795; n_gt_1 1693.

**CQ3.** Redshift tail counts in the eligible mass population (covariate). Motivated: decision 3.

```sql
SELECT count(*) AS n,
       count(*) FILTER (WHERE l.zpdf_med > 3) AS z_gt_3,
       count(*) FILTER (WHERE l.zpdf_med > 4) AS z_gt_4,
       count(*) FILTER (WHERE l.zpdf_med > 5.5) AS z_gt_5p5
FROM source.lephare l JOIN source.cigale c USING (id)
WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0
```

Result: n 634845; z_gt_3 84987; z_gt_4 48348; z_gt_5p5 14535.

**CQ4.** Mean mass disagreement by redshift band (both codes in one expression). Motivated: decision 3 and context for an external review prompt.

```sql
SELECT CASE WHEN l.zpdf_med < 1 THEN 'a_z<1' WHEN l.zpdf_med < 3 THEN 'b_1-3' WHEN l.zpdf_med < 5.5 THEN 'c_3-5.5' ELSE 'd_>5.5' END AS zband,
       count(*) AS n,
       avg(l.mass_med - log(c.mass)) AS mean_delta,
       count(*) FILTER (WHERE l.mass_med - log(c.mass) < 0) AS n_cigale_heavier
FROM source.lephare l JOIN source.cigale c USING (id)
WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0 AND l.zpdf_med > -99
GROUP BY 1 ORDER BY 1
```

Result: a_z<1: n 269343, mean_delta -0.22115061968651317, n_cigale_heavier 249694. b_1-3: n 280508, -0.19862994052347577, 261400. c_3-5.5: n 70459, -0.2329780864428954, 67117. d_>5.5: n 14535, -0.22515061379263632, 13312.

**CQ5.** Mass and SFR (100 Myr) disagreement moments (both codes in one expression). Motivated: decision 4.

```sql
SELECT current_database() AS db, current_user AS usr, count(*) AS n,
       avg(l.mass_med - log(c.mass)) AS mx,
       avg(l.sfr_med - log(c.sfr_100myr)) AS my,
       avg((l.mass_med - log(c.mass)) * (l.mass_med - log(c.mass))) AS mxx,
       avg((l.sfr_med - log(c.sfr_100myr)) * (l.sfr_med - log(c.sfr_100myr))) AS myy,
       avg((l.mass_med - log(c.mass)) * (l.sfr_med - log(c.sfr_100myr))) AS mxy
FROM source.lephare l JOIN source.cigale c USING (id)
WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0 AND l.sfr_med > -99 AND c.sfr_100myr > 0
```

Result: db cosmos2025_v11; usr (administrator role, name withheld from this record); n 634845; mx -0.2126040622179253; my 0.07966464083861906; mxx 0.07514243165144985; myy 0.2059919964282771; mxy -0.040510298296032046. Derived by the coordinator: standard deviations 0.173 dex (mass) and 0.447 dex (SFR), correlation about -0.305. Uncentered, with the censored-SFR regime included.

**CQ6.** LePhare zero-width and reversed quantiles in the eligible mass population (single code). Motivated: sizing the A1.3 guard.

```sql
SELECT count(*) AS n,
       count(*) FILTER (WHERE l.mass_l68 = l.mass_med OR l.mass_u68 = l.mass_med) AS mass_zero_side,
       count(*) FILTER (WHERE l.mass_l68 > l.mass_med OR l.mass_u68 < l.mass_med) AS mass_reversed,
       count(*) FILTER (WHERE l.sfr_med > -99 AND (l.sfr_l68 = l.sfr_med OR l.sfr_u68 = l.sfr_med)) AS sfr_zero_side,
       count(*) FILTER (WHERE l.sfr_med > -99 AND (l.sfr_l68 > l.sfr_med OR l.sfr_u68 < l.sfr_med)) AS sfr_reversed
FROM source.lephare l JOIN source.cigale c USING (id)
WHERE l.type = 0 AND l.mass_med > -99 AND c.mass > 0
```

Result: n 634845; mass_zero_side 0; mass_reversed 0; sfr_zero_side 0; sfr_reversed 0.

**CQ7.** Partition table columns (metadata). Motivated: naming the A1.1 rule.

```sql
SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'analysis' AND table_name = 'specz_p2r05_splits' ORDER BY ordinal_position
```

Result: run_id text; catalog_id bigint; native_tile text; assigned_split text; split_version text; split_salt text; valid_tile_domain_member boolean; unassigned boolean.

**CQ8.** Partition sizes (metadata, no estimates). Motivated: stating holdout coverage.

```sql
SELECT s.assigned_split, count(*) AS n, count(DISTINCT s.native_tile) AS tiles FROM analysis.specz_p2r05_splits s GROUP BY 1 ORDER BY 1
```

Result: development 476137 (12 tiles); holdout 160158 (4 tiles); validation 147721 (4 tiles).

---

## Appendix B: Coordinator-reported pre-partition diagnostics (not reproduced)

Both sessions predate the P2R-05 partition freeze (2026-09-21/22). That chronology alone does not establish source-level or tile-level overlap with the current holdout, especially for the historical v1 baseline. Their influence on design is disclosed and their exact overlap remains unverified. Neither result is in `docs/project-state.md`; retain them as coordinator-reported findings, not additional frozen inputs, and do not reproduce them.

- **2026-07-10, v1 `cosmos2025` baseline (before the v1.1 mirror).** A conditional median Delta log M surface over 6 by 6 redshift and mean-mass bins ranged from about -0.07 to -0.34 dex, with the mass trend reversing above z of about 5.5. The top 1,000 sources by absolute `t_sfr_100` were 75.5% LePhare-quiescent. LePhare sSFR non-additivity had median 0.002 dex and absolute value below 0.02 for 70.6% of sources, with its tail concentrated in quiescent sources.
- **2026-09-01.** Means over the same plane confirmed a mass-slope reversal, not a sign reversal: every cell was negative (CIGALE heavier). The ~0.24 dex headline offset is a weighted average dominated by 227,632 sources at z below 1 and mean log mass below 8.5; at mean log mass above 9.5 and z below 2 the offset was about 0.05 dex. Those means compared LePhare `mass_med` with the CIGALE posterior mean.
