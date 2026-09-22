<!--
---
title: "Phase 2 Restart Unit 5: Spectroscopic Association and Eligibility Product"
description: "Build and verify a reproducible source-level spectroscopy product, with explicit eligibility, conflict evidence, separate broad-line validation, and frozen source-level partitions, for human adoption review"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-09-21"
version: "1.0"
status: "Active - operator approved 2026-09-22; P-01 through P-09 frozen for execution"
tags:
  - type: specification
  - domain: astronomy
  - domain: spectroscopy
  - domain: data-engineering
  - tech: python
  - tech: postgresql
related_documents:
  - "[Repository instructions](/opt/agents/repos/cosmos2025-anomalies/AGENTS.md)"
  - "[Project state](/opt/agents/repos/cosmos2025-anomalies/docs/project-state.md)"
  - "[Corrected linkage evidence](/opt/agents/repos/cosmos2025-anomalies/docs/research/specz-linkage-evidence.md)"
  - "[Astronomy workload guidance](/opt/agents/repos/docs/workload-guidance/astronomy.md)"
  - "[Spec authoring contract](/opt/agents/repos/local-agent-skills/skills/spec-driven-prompt/SKILL.md)"
  - "[P2R-04](/opt/agents/repos/spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04-specz-linkage-correction.md)"
  - "[P2R-04b](/opt/agents/repos/spec/2026-08/2026-08-31-cosmos2025-spec-p2r-04b-seal-and-propagation-repair.md)"
---
-->

# Spec P2R-05: Spectroscopic Association and Eligibility Product

**Review state:** authoring is authorized. This version incorporates Claude review and author verification; it is not an executor dispatch. The operator has approved the end state, long-horizon execution structure, and separation of primary galaxy calibration from broad-line/AGN validation. The detailed defaults in P-01 through P-09 are author proposals for this review, not a claim that the operator individually approved them in the preceding discussion. Approval of a revised, named spec version freezes those defaults for execution.

**Mode:** repository work dispatched from the central queue. Target: `/opt/agents/repos/cosmos2025-anomalies`. Series identifier: P2R-05. Gates: 5.1 through 5.9. Follow the target's `AGENTS.md` work-spec contract and the local `spec-startup` and `spec-closeout` skills. The target's local-commit-only, operator-owned remote policy governs publication. This unit creates no issue or PR and performs no remote git operation.

**Dispatch prerequisites:** the operator approves the reviewed spec version and its policy defaults, with that approval durably recorded and the original D-01 through D-07 review surface linked to the approved decision contract before dispatch; direct ML01 authentication using the existing v1.1 analyst contract succeeds; bounded bootstrap access for the named derived objects is available. The operator resolved the HBA prerequisite on 2026-09-21; fresh ML01 analyst connections and effective source permissions were verified afterward (see the v0.3 access verification below). Repeat the direct-role preflight at execution time. Do not silently substitute an administrative runtime reader.

## Objective and stop boundary

Produce a mechanically verified, reproducible spectroscopy product in `cosmos2025_v11.analysis`, with one summary per photometric catalog source, measurement-level audit records, preferred reported redshifts distinct from calibration eligibility, complete reasons for exclusions, an independently identified broad-line/photometric-QSO validation population, immutable source-level development/validation/holdout assignments, and a review document tracing every acceptance claim to executable evidence. All products remain marked **pending scientific adoption**. Source mirrors, inherited provenance pins, and the historical v1 database remain unchanged.

The executor works continuously through construction, full processing, discriminating verification, diagnostics, documentation, and closeout. Gates are resumable checkpoints, not scheduled human reviews. The normal final HitL decides whether this product is fit for the declared downstream uses. Spectroscopic calibration or outcome evaluation in T_A/T_z does not begin in this unit. Non-spectroscopic mass-first work has an independent authorization boundary and is not blocked by this product's adoption decision.

## Why this exists

P2R-04 and its amendments established the corrected association path and repaired the evidence and its propagation. They deliberately left source-level science policy undecided. A shipped `_unique` row is neither proof of uniqueness per COSMOS2025 source nor proof that all other measurements agree. Conversely, positional proximity to a retained measurement does not establish the upstream deduplication relationship of a demoted measurement.

The next failure to prevent is a scientifically misleading product that passes structural checks. Examples include promoting a demoted measurement through a tie-break, treating a reproducible preferred row as truth, interpreting a mask flag as object classification, or fitting against a holdout whose outcomes were already inspected. Explicit rules and negative controls must distinguish these cases.

The information supplied to the executor is curated. Required reading below establishes the meanings and authority necessary for this task; it is not an invitation to absorb the entire project history or reopen the discovery strategy. Implementation freedom is broad after those meanings and decisions are fixed.

## Required understanding and context order

Run local `spec-startup` before deliverables and resolve its lifecycle companions from `/opt/agents/repos/local-agent-skills/skills/`. Read the workspace and target repository instruction files in their prescribed order. Read this spec in full. The following sources are mandatory at the indicated point; paths in the table are target-repository-relative unless explicitly qualified.

| When | Source and bounded reading | What the executor must understand |
|---|---|---|
| Startup | `AGENTS.md`, `README.md`, `docs/project-state.md` | Current release boundary, protected v1 baseline, runtime contract, and outstanding scientific adoption |
| Startup | Workspace `docs/workload-guidance/astronomy.md`, plus the environment references it requires | Applicable astronomy tools and host constraints; unrelated workload domains are not context for this task |
| Before 5.1 | `docs/research/specz-linkage-evidence.md`, findings F-01 through F-14 and D-01 through D-07 | Correct join, two different grains, recovery populations, historical diagnostic definitions, and previously deferred decisions |
| Before 5.1 | Pinned compilation root README, quality-flag section; compilation README, opening artifact/deduplication definitions | Flags, confidence mapping, and the meaning of `_all`, `_unique`, and Priority; no inferred measurement chronology |
| Before 5.1 | `configs/data_paths.yaml`; relevant rows of `data/dictionary/columns-v11.csv`; matching sections of `docs/reference/schema-v11.md` | Exact configured paths, physical field names, source meanings, units, and documented gaps |
| Before 5.1 | Relevant entries of `docs/reference/data-manifest-v1.1.csv` and `source.provenance` | Which existing pins identify the consumed inputs; recorded and observed identities must be compared |
| Before 5.2 | `REVIEW.md`; `src/etl/load_specz_all_v11.py`; `src/features/compute_tension_scalars.py`; their callers and applicable tests | The three narrow defects being repaired and the current error paths |
| Before 5.3 | The two corrected evidence generators and `tests/test_specz_linkage_evidence_regressions.py` | What the prior statistics actually compute and how the identifier and distribution regressions discriminate |
| Before 5.7 | `docs/research/science-opportunities.md`; `docs/reference/unit-conventions.md` | Intended later use and the limit of spectroscopy as mass validation; historical tension formulas are not requirements to implement here |
| Before docs and closeout | Applicable files in `docs/documentation-standards/`; local `spec-closeout` | Repository documentation conventions and the authoritative completion procedure |

Read additional code and narrow references when a declared gate depends on them; record consequential semantic discoveries with exact locators. Do not load unrelated domain guidance, the complete amendment chain, or speculative roadmap material as competing science authority. Historical specs are available for a specific unresolved lineage question, not as standing overrides of this successor's approved rules.

Required distinctions:

1. `Id_specz` identifies a compilation entry; `Id_COSMOS25` associates it with a catalog source. Neither is an array position. Use identifier lookup with uniqueness and membership checks.
2. Population A is present through `_all` but absent through `_unique`. Searching `_unique` can never return the same A source. The zero is structural and establishes no neighbour destination.
3. `_unique` is shipped upstream. In the held release it equals `_all` at Priority 1 across the native fields. This equality does not make it unique at COSMOS2025-source grain.
4. `_all` can expose disagreement for sources with only one `_unique` row. All qualifying measurements must participate in conflict diagnostics.
5. Confidence at least 95 includes broad-line flags 13/14. It is not synonymous with flags 3/4.
6. `photometry_primary.flag_star` describes overlap with a star mask. The sealed dictionary defines `lephare.type` as 0 galaxy, 1 star, 2 QSO. Use those meanings; never classify from a suggestive field name.
7. The source mirror preserves finite sentinels. Derived eligibility may reject values under the explicit policy without altering or relabelling their native values.
8. A secure spectroscopic redshift can test photo-z behavior. It does not establish which stellar-mass estimate is correct or prove a causal explanation for mass disagreement. The published COSMOS2025 methodology fixes CIGALE redshifts to LePHARE solutions; do not invent independent CIGALE photo-z estimates. The bounded upstream reference is [COSMOS2025 v1, section 8](https://arxiv.org/html/2506.03243v1#S8); this is methodological context, not authority to change the held v1.1 inputs.

`REVIEW.md` currently contradicts distinction 1 and understates the mirror count. It is a repair target, not an alternative join authority. Existing evidence recommendations also predate the additional `_all` audit and must not silently replace this spec's approved policy.

## Execution environment

| Item | Delta |
|---|---|
| Executor | Operator-selected **GLM53 full**, on ML01; use the operator's actual runtime configuration, with no model substitution |
| Required location | Box-required: pinned local holdings and the psql01 mirror |
| Toolchain | Target repository and astronomy workload contracts; shared ML01 Python environment |
| Attendance | No scheduled pauses during the run; final scientific adoption by the operator |
| Lifecycle | Local `spec-startup` and `spec-closeout`; target repository procedure governs conflicts |
| Review | Claude reviews this authored spec before dispatch. This is not authority for the executor to launch another model or incur review-service charges. |

Do not copy the selected executor label into attestation fields as a guessed runtime identity. Closeout reads the actual runtime facts as its skill requires.

## Policy contract for review

P-01 through P-09 are proposed defaults in this draft. Once the operator approves a named version for dispatch, they are frozen for that execution. The coordinator records that approval and its D-01 through D-07 dispositions before dispatch. The executor verifies and carries the supplied approval reference and approved spec digest into `docs/research/specz-science-dispositions.md`; it cannot manufacture an approval or settle an unfilled policy during the run. These dispositions authorize construction for the purposes explicitly stated here, while scientific adoption of the built product remains pending. Freeze the approved spec bytes at dispatch and retain that digest through unchanged archival; later science-policy changes require an approved amendment. Do not change the spec status during closeout in a way that invalidates the recorded approval identity.

### P-01: Association and population A (D-01, D-03)

Associate compilation rows solely through `id_cosmos25 = photometry_primary.id`. Carry the native identifier even when unmatched. A native `-999` identifier is an explicit no-association state. A different non-null identifier absent from the catalog is a contract discrepancy to investigate, not a licence to rematch coordinates.

Retain all `_all` measurements in the audit product. Population A has no preferred reported redshift from `_unique` and is ineligible for both primary calibration and the separate secure validation population. Preserve its entries, flags, confidence, coordinates, and review reasons. No Priority 0 entry is promoted, and no neighbour destination or upstream deduplication component is inferred.

All catalog sources receive a summary, including those without spectroscopy. This makes the photometric denominator explicit.

### P-02: Numeric validity and quality (D-04)

Define `numeric_valid_z` as non-null, finite, and strictly greater than zero. No arbitrary upper-redshift ceiling is introduced. Zero, negative values including -9, infinities, and missing values remain visible in the audit and fail this predicate.

Define recognized measured flags as `{1,2,3,4,9,11,12,13,14,19}`. Their base-flag confidence mapping is `1:50, 2:80, 3:95, 4:97, 9:85`, with the same mapping after subtracting 10 for the named broad-line flags. Flags 0/10 do not denote a measured redshift under this contract. Other flag values remain unclassified; do not assign them a physical interpretation from their sign.

Review verification across both held compilation surfaces found flag 5 at confidence 90 and flags 6/10 at -99; the remaining observed flags outside the recognized set carry confidence zero (including -3 in `_all` only). Flag 5 is the only unrecognized flag with positive confidence. No observed unrecognized flag reaches the baseline confidence threshold of 95. Reproduce that empirical bound at 5.3; it is not a universal property of the flag set. The secure predicate still requires an explicitly recognized flag and its consistent mapping. Any later policy lowering the threshold must reconsider flag 5 explicitly and must define its treatment if confidence 90 becomes eligible, including in a sensitivity variant. Do not infer flag 5's meaning or admit it automatically.

A `secure_measurement` has numeric-valid z, flag in `{3,4,13,14}`, confidence at least 95 and at most 100, and agreement with the documented flag/confidence mapping. A missing, out-of-domain, or inconsistent quality value prevents secure status and gets an explicit reason. It does not change the stored value or force the run to halt when this policy already covers the case.

Keep numeric availability, recognized measurement status, quality consistency, and secure status as separate predicates. The old `z > -90` rule is reproduced only as historical evidence.

### P-03: Preferred reported redshift (D-02)

For each source, candidates for `preferred_reported_z` are its numeric-valid `_unique` entries. Select the entry with highest valid confidence in the closed interval [0,100]; missing or out-of-domain confidence sorts below valid confidence. Break remaining ties by ascending `id_specz`. Record the tie and all tied entry IDs.

This tie-break is bookkeeping, not evidence that the selected measurement is more correct or newer. Do not infer recency from the identifier or survey number. The reported value is copied from the selected row, never averaged. An unusual flag can remain attached to a preferred reported value while preventing calibration eligibility. No candidates means a null preferred entry and redshift.

### P-04: Conflict policy (D-02)

Use a maximum pairwise absolute difference of **0.005** as the proposed conservative baseline. Equality is agreement; a larger difference is conflict. This is a selection rule for review, not a claim about a universal physical error scale.

Produce three independent flags:

- `unique_numeric_conflict`: at least two numeric-valid `_unique` entries differ by more than 0.005, irrespective of their confidence.
- `secure_all_conflict`: at least two secure measurements in `_all` differ by more than 0.005. A source with one `_unique` entry can have this flag.
- `other_measurement_disagreement`: a numeric-valid pair in `_all` differs by more than 0.005 and is not a pair of two secure measurements. This is retained for audit; by itself it does not veto eligibility.

Either of the first two flags vetoes both secure-use populations. Each flagged source includes witness entry IDs, raw z values, quality values, and the pairwise difference. Enumerate the compared population independently of the preferred-entry selector. With fewer than two qualifying entries, agreement is **not assessable** rather than a successful corroboration. An otherwise eligible single secure preferred entry can be used, labelled as singly supported.

The policy deliberately treats disagreements among multiple shipped representatives more conservatively than low-quality demoted alternatives. Measure that choice's effect; do not relax it to achieve a desired sample size.

### P-05: Galaxy, stellar, and broad-line handling (D-04)

Carry `lephare.type` as a photometric classification, not spectroscopic truth. Type 1 vetoes both secure-use populations. Null or unrecognized types receive an explicit classification-unknown exclusion. A disagreement between stellar classification and spectral evidence is retained for review without adjudication. This policy conditions primary membership on the output of the photometric pipeline whose redshift behavior a later unit may evaluate. Its performance claims therefore apply to the selected LePHARE-classified population; they cannot establish unconditional performance across stellar/QSO classification failures or the full spectroscopic population.

Define `broad_line_reported` when any associated numeric-valid `_all` measurement carries one of `{11,12,13,14,19}`. Preserve the confidence and entry IDs supporting that flag. It means a broad-line report exists, including tentative reports; it is not a complete AGN census. Define `photometric_qso` separately as `lephare.type = 2`.

**Primary galaxy calibration eligibility** requires all of:

- A secure preferred `_unique` entry and resolved source association.
- Neither veto conflict from P-04.
- `lephare.type = 0` and no `broad_line_reported` evidence.
- A valid frozen split assignment under P-06.

**Separate validation eligibility** uses the same association, preferred-quality, conflict, and split requirements, allows LePHARE type 0 or 2, and requires `broad_line_reported` or `photometric_qso`. Preserve distinct labels for spectroscopic broad-line evidence and photometric-QSO-only inclusion. Do not call every member a confirmed AGN. The two eligibility booleans are mutually exclusive.

Mask overlap, blending, magnitude, and photo-z validity are diagnostic context, not additional implicit sample cuts. Sources excluded from either secure-use population remain in the source summary with all applicable reasons.

### P-06: Frozen partitions (D-05)

Assign every catalog source before any fitting, tuning, or photo-z outcome analysis. Assignment depends only on its native tile and this fixed algorithm, not on spectroscopy availability, source quality, or the defective link column.

The valid tile domain is the documented twenty labels A1 through A10 and B1 through B10. For each label, compute SHA-256 over UTF-8 `cosmos2025-p2r05-spatial-v1|<tile>`, without a newline. Sort by the full hexadecimal digest, breaking any digest tie by the tile string. The first four labels are `holdout`, the next four `validation`, and the remaining twelve `development`. Publish the resulting tile map. These are 20/20/60 percent of tiles, not promises about source counts.

All sources in a tile inherit its assignment; all measurements inherit their source's assignment. Null or out-of-domain tiles are `unassigned` and fail secure-use eligibility. Record their counts without inventing a replacement tile.

Review verification found every catalog source carrying a non-null tile inside the documented twenty-label domain, so the expected production `unassigned` count is **zero**. A nonzero count halts partition completion for investigation. First distinguish an extraction, join, or assignment defect from a native source/domain discrepancy through an independent read; do not narrate source drift before excluding an implementation error. Repair an implementation defect within this contract and rerun its affected checks; a verified native discrepancy against the inherited identity invokes the blocked-signal contract. Synthetic invalid-tile fixtures must still produce the explicit `unassigned` state and a failing completion check. Test that source order, chunk size, and spectroscopy filtering do not alter assignments.

Survey and confidence balance are diagnostics, not a second assignment algorithm. Do not re-roll the salt or move tiles to improve balance or outcome metrics. Spatial blocking reduces one leakage route; it does not establish complete independence of blended sources, upstream calibration, or survey systematics. Record these limitations.

### P-07: Diagnostics and sensitivity without tuning

Publish eligibility counts, mutually exclusive summary states, overlapping reason counts, and coverage against the full catalog. Also produce a diagnostic `spectroscopy_qualified_before_photometric_type` mask: resolved association, secure preferred `_unique` entry, neither P-04 veto, and valid P-06 assignment, without the LePHARE-type or broad-line routing conditions. Cross-tabulate this mask by every observed LePHARE type (including missing/unknown) and `broad_line_reported`, and enumerate otherwise-qualified sources excluded by type. This is an exclusion-accounting diagnostic, not a new adopted sample, permission to remove the type veto, or evidence that photometric stellar labels are wrong. Distinguish entries from distinct sources in every denominator. Report survey/confidence distributions, tile coverage, LePHARE class, mask/blend context, and photometric coverage using the verified meanings of F444W magnitude and F150W-F277W color.

For magnitude summaries, retain native missing values and explicit underflow/overflow bins. Compute F150W-F277W color only when both magnitudes are finite and strictly between -10 and 50 AB; otherwise retain a separate `color_not_evaluated_display_domain` category, distinguishing native missing inputs. This deliberately broad plotting domain is a derived diagnostic rule, not a claim that every outside value is a source sentinel. In particular, two finite unfit magnitude values must not subtract to a plausible color and enter the ordinary color distribution. State the diagnostic bin definitions in the policy configuration before rendering the report. Bin edges may be chosen by the executor; they may not affect eligibility, preferred entries, partitions, or any model fit.

Produce exactly three sensitivity variants in addition to baseline, changing only the named dimension:

1. Minimum confidence 97, with the same flag-consistency rules and baseline conflict threshold.
2. Absolute conflict threshold 0.001, with baseline quality requirements.
3. Pairwise normalized conflict threshold 0.005, where `d = abs(z_i-z_j)/(1+min(z_i,z_j))` for positive finite pairs, with baseline quality requirements. Apply this comparison to each of the P-04 flags.

Variants recompute secure status and conflict flags consistently, retain the baseline preferred-row ordering, and share the frozen partitions. Report source-level membership changes and reasons. They are diagnostic alternatives, not parallel adopted samples or opportunities for the executor to choose a winner.

This unit computes no photo-z-versus-spec-z residual performance, no stellar-mass tension, no SFR ranking, no fitted correction, and no model selection. Held-out records are necessarily read to build and check their eligibility; their downstream prediction errors remain unevaluated. Selection diagnostics do not make spectroscopy representative of unobserved photometric populations.

### P-08: Upstream report (D-06)

Prepare a local, reproducible report of the incompatibility between the held photometric and compilation releases. Include exact release pins, the claimed correspondence, corrected query definitions, and the geometric discrepancy. Label renumbering as a hypothesis. Do not send the report, open an upstream issue, or contact anyone. The operator decides publication after review.

### P-09: Downstream use and adoption (D-07)

Every artifact and database run record identifies the policy version, inputs, code identity, and `pending_scientific_adoption` state. The product may be mechanically complete while adoption is pending. No consumer-facing alias implies approval, and no downstream spectroscopy calibration runs as a smoke test. The final review separately asks about primary galaxy use, separate validation use, sensitivity limitations, and release of the prepared upstream report.

## Prior observations to reproduce, not acceptance targets to manufacture

The following were observed in the authoring review of the checkout at `2f2c84e` and/or the sealed P2R-04 evidence. Exact agreement is expected for the same inputs and definitions. A disagreement first triggers independent recomputation and diagnosis. It cannot be explained away by changing the population or the expected value.

| Observation and definition | Prior |
|---|---:|
| Catalog / `_unique` / `_all` rows | 784,016 / 261,975 / 482,579 |
| Existing source provenance registrations | 12 |
| Native tiles: distinct documented labels / null or out-of-domain sources | 20 / 0 |
| Sources reached through `_unique` / `_all` | 45,007 / 46,039 |
| Population A sources / entries / nonzero-Priority entries | 1,032 / 1,559 / 0 |
| Population B sources / entries | 185 / 371 |
| B under finite `z > -90`: agreeing / disagreeing / one usable / zero usable | 75 / 57 / 48 / 5 |
| B under positive finite z, same absolute 0.005 tolerance | 72 / 57 / 49 / 7 |
| Disagreeing B groups with tied highest confidence, either preceding rule | 16 |
| Distinct `_unique` sources under `z > -90` / positive z / positive z and confidence >=95 | 39,165 / 37,722 / 20,100 |
| Corrected-path `_unique` entries with confidence >=95 and flags 13/14, without a z filter | 327 |
| `_unique`-reachable sources with >=2 positive finite, confidence >=95 entries in `_all`, without a flag filter | 8,939 |
| Same population spanning absolute z difference >0.005 | 656 |
| Of those, sources having exactly one `_unique` entry | 649 |
| Of those 649, sources whose Priority 1 entry meets the positive-z/confidence rule | 647 |

The last four rows are exploratory confidence-only counts. They are not predictions of P-02's stricter flag-consistent secure population. The 20,100 availability count is not an eligible-sample count. The defective-path median of 4,054.341555894 arcsec has an explicitly documented all-links coordinate basis in the corrected evidence; reuse its verified evidence, and independently reproduce it for the upstream report without changing that basis.

## Product and persistence contract

Freeze the semantic configuration as tracked `configs/specz_science_policy_v1.yaml`, with policy identifier `p2r05-specz-policy-v1`. Reject missing required policy fields, unexpected semantic keys, invalid domains, and a configuration that disagrees with the approved spec. No silent defaults or command-line overrides may change science policy. Storage paths and batch sizes are implementation configuration, separate from that policy's semantic digest.

The persistent outputs are four named tables in `cosmos2025_v11.analysis`:

| Relation | Grain and required content |
|---|---|
| `specz_p2r05_runs` | One record per content-addressed build; policy, input and code identities; canonical content digests; row counts; mechanical seal and pending-adoption status; operational timestamps separately |
| `specz_p2r05_measurements` | One row per `(run_id, id_specz)` in `_all`; all 32 native source fields preserved, association status, nullable resolved catalog ID, membership in `_unique`, numeric/quality predicates and reasons |
| `specz_p2r05_sources` | One row per `(run_id, catalog_id)` in the full catalog; preferred entry/z and tie provenance, entry counts, A/B membership, independent conflict flags and witness references, classification evidence, eligibility booleans, all exclusion reasons, and singly/multiply supported status |
| `specz_p2r05_splits` | One row per `(run_id, catalog_id)`; native tile, assigned partition, split version and salt identity |

The database schema must enforce the declared keys and relationships. Native columns in the measurement audit are copies, not repairs; derived fields are visibly separate. Conflict witnesses may be typed arrays or a structured field, but they must resolve to the exact audited entries and be independently reproducible. The executor chooses physical field names for unspecified derived fields and documents them in a separate derived schema contract. The sealed source dictionary is not extended for these derived products.

The run ID is derived deterministically from approved policy identity, consumed input content identities, and the implementation identity. Define canonical serialization before the build. It must distinguish nulls from finite sentinels, preserve relevant float values, use deterministic ordering, and exclude operational timestamps. Compute product content digests over the measurement, source, and split records; their metadata row in `specz_p2r05_runs` is outside those digest domains. Store content digests separately from container-file checksums. Implementation identity names the build-affecting code bytes and dependencies, not a future closeout commit. No output contains a requirement to record the hash of the commit or file containing that same record.

A repeat build of the same identity is verification-only and leaves the existing rows unchanged. Different identities may coexist. Do not overwrite a previous run, switch a general-purpose current-sample alias, or mark anything adopted. Foreign-key and eligibility assertions must hold on the complete installed result, not just in the local export.

Large local exports and resumable checkpoints live under configured `staging/derived/specz-p2r05/`. Durable evidence, exact commands, policy/contract files, input identities, content digests, and count summaries are tracked under `docs/research/specz-science-p2r05/`. Persist full source/measurement/split rows in the database; do not make an ignored staging JSON the only surviving evidence for an exclusion or conflict.

## Database authority and authentication

Runtime extraction and installed-product verification use the existing direct analyst handoff with connection-time read-only enforcement. Confirm the actual database, session/current principal, read-only settings, and needed SELECT privileges. A responsive connector alone does not establish this identity. Never log credential contents.

Administrative credentials supplied through the existing scoped Doppler contract are authorized for two bounded purposes: inherited verification/protected-v1 inventory under enforced read-only sessions, and bootstrap/installation of the four named analysis tables, schema creation if absent, their constraints/indexes/comments, and SELECT grants to the existing analyst role. The former preserves the existing verification contract and is not a substitute for proving direct analyst access. Source rows for this new science build are extracted through the analyst path into verified local artifacts before installation; the installer consumes those artifacts. This is a one-shot derived-product bootstrap, not authorization for an administrative analysis runtime.

At initial installation, a pre-existing `analysis` schema may be retained if ownership and privilege inspection support the operation. Existing unrelated objects are inventoried and untouched. A pre-existing same-named product relation must either match this contract and its run identities exactly or cause a stop before modification. Never drop or commandeer an object merely because its name matches.

The bootstrap may grant USAGE on the new analysis schema and SELECT on these four tables to the existing analyst role. It may not broaden source privileges, grant analyst writes, create credentials or roles, edit HBA, or change MetaMCP. Do not modify schema-wide default privileges as a convenience. Verify effective access after creation; do not assume owner-dependent defaults propagated.

Authenticated SQL failure and reversal tests use disposable databases under the repository's existing guarded scratch-prefix contract. Their creation, exact-resource cleanup, and synthetic fixtures are authorized. No production table is a fault-injection target. Protect v1 and all source schemas in both production and scratch-name guards.

## Scope

All unqualified paths below are target-repository-relative.

### Pre-existing, inspect rather than recreate

- Verified `cosmos2025_v11.source`, its twelve mirrors and provenance table; existing v1.1 analyst role and credential handoff.
- Immutable raw holdings, manifest, dictionary, source generators, and their reviewed pins.
- The corrected linkage evidence/generators and historical v1 tension products.
- Configured staging directories, which may need creation at their existing configured locations.

### Modify or create

- `REVIEW.md`: current join/grain/count guidance and distinction between source fidelity and derived eligibility.
- `src/features/compute_tension_scalars.py`: execution guard only; preserve scientific helpers and formulas.
- `src/etl/load_specz_all_v11.py`: uncertain-commit handling only, with corresponding tests. No production invocation of its load, provenance-registration, or comment-mutation modes.
- `src/features/specz_science/` (new): builders, policy validation, verification and installation interfaces; interior README. Module decomposition belongs to the executor.
- `configs/specz_science_policy_v1.yaml` (new); `configs/data_paths.yaml` and `configs/README.md` for new derived paths/contracts only. Preserve existing database defaults for the guarded historical runner.
- `tests/` for meaningful new tests and necessary integration of the new modules; `tests/README.md`. Existing checks may not be weakened to obtain green results.
- `docs/research/specz-science-dispositions.md` (approval/decision record, created during dispatch preparation if absent); `docs/research/specz-science-p2r05/` (new evidence, derived schema contract, review document, and local upstream-report draft, with README). Preserve pre-dispatch approval history.
- `docs/research/specz-linkage-evidence.md`: append a disposition pointer/status only, preserving historical figures, definitions, and the recorded amendment history.
- `AGENTS.md`, `README.md`, `docs/project-state.md`, `src/README.md`, `src/features/README.md`, `src/etl/README.md`, `docs/README.md`, `docs/research/README.md`, `work-logs/README.md`, and repository `spec/README.md` / month index for factual consequences of this unit only.
- Repository `work-logs/2026-09-21-cosmos2025-worklog-p2r-05-specz-science-surface.md`; bounded staging exports, blocked record, and decision record under `staging/derived/specz-p2r05/`; the repo recycle-bin and README for recovery of superseded untracked artifacts.
- Database: the four named `analysis.specz_p2r05_*` tables and their dependent indexes/constraints/comments, bounded grants described above, and exactly identified disposable scratch databases.
- Central spec's authorized archive move with approved bytes unchanged, its byte-identical repository archive copy and month README, and the lifecycle registry append. The central spec-defect register may receive append-only findings attributable to this run, with IDs allocated from its actual current state.

The final documentation pass may update an existing interior index directly containing an authorized changed path; it may not expand into unrelated documentation cleanup. No other central or peer repository content is a deliverable.

### Reference only

- Required context listed above, inherited source pins and semantic sources.
- Existing source-verification and scratch-test utilities, where their contracts fit; do not fork or casually change a sealed generator.
- `docs/phase2-tension-diagnostic-report.md` for the guard's historical target and later T_A context only.

### Do not touch, with reasons

- `cosmos2025` v1 database: irreplaceable historical baseline; no DDL or DML.
- `cosmos2025_v11.source`, including values, comments, ownership, ACLs, and provenance: inherited ground truth, not an analysis write target.
- Raw holdings, compilation checkout HEAD, source manifests, sealed dictionary, generated source DDL/conformance/schema docs, and their input seals: changing a pin would change the experiment. Read/verify only, including configured external semantic-source caches required by existing tests.
- HBA, MetaMCP, networking, Doppler configuration/secrets, shared software installations, other cluster services: outside this unit's authority. Their required state is checked before work.
- Scientific formulas and outputs of historical T_A; new T_A/T_z models, scores, mass corrections, or SFR filters: downstream scientific work needs its own approved contract.
- External messages, upstream issue creation, public release, DOI minting, remote git operations, and merges: operator-owned external actions.

## Reversal, validated work, and recovery latitude

Effects are ordinary repository edits, reversible derived-schema bootstrap, and rebuildable derived rows. No inherited provenance pin is replaced. New build metadata records new derived work without revising old provenance.

Before a mechanical seal, failed local exports may be replaced after preserving their diagnostic evidence. A failed database install rolls back its transaction. The down operation is tested on an authenticated scratch database and deletes only rows for this unit's unsealed run, then drops only newly created named objects that the startup/install ledger proves are unused and have no unrelated dependents. It does not cascade into unrelated objects. Remove a newly created schema only when proven empty; restore only grants this run added when no retained product depends on them.

The **mechanical seal** is declared at 5.7 after independent complete-product verification, installed content identity, and effective analyst access pass. Record the build identity, content digests, validation evidence, and gate commit. Scientific adoption is a separate state.

After the seal, an administrative, documentation, or verifier-code failure authorizes narrow repair and re-verification. It does not authorize destroying validated rows, reimporting source data, or repinning inputs. Commit uncertainty always preserves potentially committed work until an independent read classifies it as absent, complete and identical, or inconsistent. An inconsistent state is retained and reported; it is never silently deleted as cleanup.

**Destructive rebuild budget:** at most two removals/replacements of a fully materialized but unsealed candidate across this unit, counted cumulatively across differing failure signatures. Retained alternate build identities and transactional attempts that leave no persistent data are not destructive rebuilds. Record the cost, reason, and discarded validated scope of each destructive attempt. Sealed-product removal requires a new operator authorization regardless of remaining budget. Source reimports are never a recovery option in this unit.

The executor chooses module boundaries, batching, caching of verified intermediate results, diagnostic presentation, test organization, and the narrowest lawful recovery. It may correct its own implementation and verifier defects and resume at the earliest affected checkpoint. It may not reinterpret a failed scientific invariant or alter acceptance rules to preserve progress.

## Deliverables and matched validation

### Gate 5.1: Establish the executable contract and input identity

Complete startup, capture actual base identity, confirm the dispatch approval reference, and materialize the approved P-01 through P-09 policy and disposition record. Validate direct analyst access and installation authority before expensive work. Record source metadata, relevant native semantics, existing target objects/privileges, and hashes of the consumed input definitions. Capture a consistent read-only snapshot of the fields used by the build and its evidence; subsequent passes must refer to this same captured input identity.

**Validation:**

- [ ] Approval names this spec version and all policy defaults; no draft or blank scientific choice can enter execution.
- [ ] Actual database/principal/read-only facts and privileges are asserted; wrong database, admin-as-runtime-reader, and missing analyst SELECT fail preflight.
- [ ] Relevant source manifest/provenance pins agree with freshly checked consumed artifacts. Source hashes are compared, not merely displayed. Existing full-suite checks retain their broader source verification.
- [ ] Before-state records source relation definitions, constraints, comments, ACLs, counts and content identities, plus protected v1 identity; the implementation declares reproducible comparison methods and covers all source relations without writes.
- [ ] The approved policy, known source definitions, unsupported-quality handling, and split algorithm are machine-checked. Missing, extra, wrong-type, and out-of-domain policy values fail named tests.
- [ ] The approval/disposition record separates approved policy, empirical priors, and final adoption. It does not assert that earlier recommendations were already operator decisions.

### Gate 5.2: Remove the three known execution hazards

Correct `REVIEW.md` to state the actual join and grain, the current twelve-mirror boundary, and the difference between immutable source values and permissible derived rejection. Disable the historical feature runner's production entrypoint before any connection or write can occur. Preserve importable computation/report helpers for historical tests; this unit adds no override flag to run the destructive v1 pipeline.

Repair the measurement loader so exceptions before commit roll back without deleting unrelated work and a possibly successful commit is never followed by destructive cleanup. Demonstrate classification through an independent connection where applicable. The current source mirror is not reloaded or mutated to exercise this fix.

**Validation:**

- [ ] The historical CLI fails with an explanatory message before the connection factory is called; importing and exercising pure historical helpers still works.
- [ ] A fake/isolated commit that succeeds server-side then raises, including interruption, retains the installed table and data.
- [ ] An ordinary precommit failure rolls back; the handler performs no compensating production DROP after an uncertain commit.
- [ ] Scratch tests cover unknown/failed classification and existing-object protection, with observable retained values.
- [ ] Review instructions cannot endorse the defective catalog pointer or forbid the explicitly authorized derived eligibility layer.

### Gate 5.3: Reproduce and extend the decision evidence

Reproduce the prior table under its exact definitions using independent reductions or SQL over the captured source snapshot. Verify complete `_unique`/Priority-1 equality across native fields and the identifier lookup. Characterize A, B, and high-confidence `_all` disagreement among `_unique` singletons. Separately enumerate the proposed policy's stricter secure population and quality inconsistencies.

**Validation:**

- [ ] Each prior has a reproducible command/query, explicit surface, predicate, unit, and denominator. Discrepancies have independent recomputation and a supported disposition.
- [ ] Counts reconcile to enumerated IDs and entries; distributions include every observed category, including unknown and missing categories.
- [ ] A hostile fixture with unordered/non-contiguous IDs and colliding identifier values catches source/row-position confusion.
- [ ] A fixture with one `_unique` entry and a conflicting secure Priority 0 entry is detected by the `_all` audit.
- [ ] Population-A evidence explicitly identifies the structural zero and makes no nearest-neighbour ownership claim.

### Gate 5.4: Build the complete measurement and source products

Implement the policy and all required reasons over the complete snapshot. Build the four product contracts, leaving split-dependent eligibility unfinalized until 5.5. Persist native values separately from their derived interpretation. Encode reasons so the source summary is independently explainable from its entry records.

**Validation:**

- [ ] Exact equality of full catalog ID sets and source-summary keys; exact equality of `_all` entry sets and audit keys, including unmatched entries.
- [ ] Preferred values and tie lists match an independent implementation of P-03 for every source; no Priority 0 entry becomes preferred.
- [ ] Separate tests cover zero/one/multiple usable representatives, ties, invalid confidence, flags 0/10 and unknown flags, null/nonfinite/negative/zero z, and exact conflict-threshold boundaries.
- [ ] Conflicting high-confidence alternatives veto secure use even when the preferred entry is deterministic; a low-quality demoted discrepancy alone does not.
- [ ] Broad-line reporting, photometric QSO, stellar classification, and mask overlap remain distinct. Changing only `flag_star` cannot change object classification or secure eligibility. Finite out-of-display-domain magnitude pairs cannot manufacture an ordinary diagnostic color.
- [ ] An independent source reduction reproduces every conflict witness, quality predicate, and applicable exclusion reason. A subtly wrong preferred ID or missing witness fails verification.

### Gate 5.5: Freeze assignments and finalize eligibility

Produce the tile map and all source-level split records under P-06, then finalize both secure-use populations. Assignments precede all diagnostics that could motivate choosing a different split. Retain the map and canonical digest as a durable artifact.

**Validation:**

- [ ] Exact independent reproduction of the twenty-label tile map and all catalog-source assignments.
- [ ] Every repeated measurement follows its source; input reordering, batching, and changes in spectroscopy eligibility leave assignments unchanged.
- [ ] A source moved across partitions, a changed salt, and a duplicate assignment each fail independent verification.
- [ ] The native production tile-domain check and independent assignment reduction both produce zero `unassigned` sources. Injected null/out-of-domain tiles are visible, ineligible, and rejected by the completion check; there is no redistribution to balance surveys or sample sizes.
- [ ] Both secure-use booleans satisfy their full conjunctions and are mutually exclusive. Overlapping reasons are retained rather than collapsed into misleading additive counts.

### Gate 5.6: Install through bounded bootstrap and prove repeatability

Create/install the approved derived contracts from verified local artifacts. Use transactional installation and explicit run identity. Apply the bounded analyst read grants and independently reconnect through the real analyst path. Repeat the same build/installation request to prove identity-aware nonmutation.

**Validation:**

- [ ] Scratch up/down proof covers declared tables, keys, relationships, grants, protected-object guards, and commit uncertainty before persistent installation.
- [ ] A reconnecting analyst reads the exact installed products, with no effective write privileges; source and v1 rights are unchanged.
- [ ] Full installed row content and digests equal the verified local artifacts; counts alone do not pass.
- [ ] An identical rerun changes no rows, timestamps, grants, or adopted-status fields. A conflicting same-ID payload fails before modifying existing rows.
- [ ] Failures cannot leave a partially accepted run or promote `pending_scientific_adoption` to another state.

### Gate 5.7: Full verification, coverage, and mechanical seal

Run complete-product independent checks and the repository suite, then render baseline coverage, source attrition, conflict provenance and the three fixed sensitivity comparisons. Every figure carries its predicate and denominator. Verify protected source/v1 identities and inherited pins against 5.1. Declare the mechanical seal only after all these checks pass.

**Validation:**

- [ ] A separately expressed verifier reproduces full membership, preferred entries, reasons, and split identity from the captured native input; it does not call the builder's policy predicates or trust builder totals as its oracle.
- [ ] Negative controls remove a category, alter a source association, promote an A entry, erase a secure conflict, change a tied preferred entry, and move a source between splits; each is rejected on its intended invariant.
- [ ] Complete-row native-field fidelity holds for the measurement audit, including finite sentinels and SQL NULL. Derived content hashes recompute correctly.
- [ ] Full catalog accounting reconciles; entry and source denominators are explicit; broad-line-report and photometric-QSO-only subgroups remain distinguishable.
- [ ] All three sensitivity variants change only their declared dimension, preserve baseline ordering and partitions, and make no automatic adoption choice.
- [ ] Coverage includes survey/confidence imbalance and photometric/spatial gaps; no claim equates stratification with representativeness. The pre-photometric-type diagnostic independently reconciles every classification/broad-line subgroup and every otherwise-qualified type exclusion; it cannot change either adopted-policy eligibility boolean.
- [ ] No photo-z residuals, fitted corrections, anomaly scores, or held-out outcome performance are computed or published.
- [ ] Full existing pytest suite and new tests pass. Run from the shared environment under the existing credential wrapper where required. Include the expensive dictionary byte-identity and full-manifest checks once in final verification; do not silently deselect them or repeatedly reprofile without a new reason.
- [ ] Existing source generator check modes remain byte-identical and source conformance passes; source/v1 before-after invariance and protected-file hashes match.
- [ ] The seal records the input, policy, implementation and output identities, exact verification commands/results, elapsed time, peak RSS, and recovery history. It makes no scientific adoption claim.

### Gate 5.8: Deliver the human review document and upstream-report draft

Write `docs/research/specz-science-p2r05/review.md` for a reader who has not followed the execution. Include a compact policy rendering, full sample accounting, sensitivity results, limitations, and stable findings S5-F01 onward. Each finding carries a statement, exact evidence locator and reproduction command, and a closed question where a decision is required. Link full enumerations through their run/table/key identities.

The acceptance questions are:

- **S5-Q01:** Accept the mechanically verified association and preferred-entry product as a reproducible input for subsequent approved work?
- **S5-Q02:** Adopt the baseline primary galaxy eligibility policy for the declared spectroscopic calibration/validation use, given its exclusions and sensitivity?
- **S5-Q03:** Adopt the separately labelled broad-line/photometric-QSO validation population for its declared diagnostic use?
- **S5-Q04:** Accept the frozen partitions and documented coverage/independence limitations for a subsequent modelling spec?
- **S5-Q05:** Authorize sending the prepared upstream incompatibility report through an operator-chosen channel?

Every answer remains pending. A mechanically successful run can recommend declining a scientific adoption question. Describe implications without changing the approved baseline or choosing an alternative sensitivity policy.

**Validation:**

- [ ] Every acceptance claim resolves to verified evidence; no final statistic is copied from a prior without reproduction.
- [ ] All five questions are answerable from the delivered evidence, and no answer is filled by the executor. The limitations explicitly describe selection on LePHARE classification, give the independently measured number and makeup of otherwise-qualified exclusions, and restrict later validation claims to the selected population. A passing source-class cross-tab does not establish that excluded stars or QSOs were misclassified.
- [ ] The upstream draft reproduces the held-release mismatch and marks renumbering as unconfirmed; no external transmission occurred.
- [ ] Orientation docs distinguish completed construction from pending adoption, and the old disposition surface points to the new record without rewriting its historical findings.

### Gate 5.9: Close out the long-horizon run

Follow the target repository's work-spec contract and local `spec-closeout`. Resolve the skills from the local estate. Preserve per-gate checkpoints and the operator-interaction record, explicitly recording if none occurred. Record actual runtime and usage facts as available.

The central month archive is authoritative and the repository month archive carries a byte-identical copy, matching the established P2R-04 series convention. Archive under the month of this spec's filename. The target's operator-owned remote policy controls: deliver local commits for review without push, issue creation, PR creation, or merge.

**Validation:**

- [ ] Documentation and consistency passes find no unmet deliverable or unverified completion claim.
- [ ] Per-gate commits and worklog checkpoints exist; completed gates remain resumable and final product identities are recorded.
- [ ] Worklog, lifecycle registry append, archive copies and required indexes satisfy their authoritative contracts. A worklog need not contain the SHA of the commit containing that same worklog; capture final commit identity through the lifecycle's external record/final handoff without a self-reference requirement.
- [ ] Archive copies are byte-identical; the active central spec is absent only on clean closeout. Earlier archived specs and their worklog/registry seals are unchanged.
- [ ] Any spec defects are attributed honestly and appended to the current register without overwriting prior entries.
- [ ] The final handoff names the review document, product/run identity, local branch and commit, verification result, pending adoption questions, and any operator actions.

## Stop and blocked-signal contract

Stop when a required preflight fails, an approved semantic assumption is disproved, a required scientific choice is missing, scope must materially widen, recovery would destroy sealed work, or the cumulative destructive-rebuild budget is exhausted. Investigating and fixing an implementation defect within the approved contract does not itself require HitL.

Write `staging/derived/specz-p2r05/BLOCKED.md` with the gate, observed evidence, attempts, preserved work and identities, and the exact decision or authority required. Append the same material to the worklog and surface it through the executor's existing operator-visible session. No new messaging integration is assumed or authorized. Record operator questions and answers durably under the startup skill's interaction contract.

Use the lifecycle's blocked/partial path when required; leave the spec visible in the active queue. Do not edit the approved science rules mid-run, force a green seal, destroy validated work to simplify cleanup, or report implementation failure as a scientific finding. A substantive spec defect is corrected through an operator-approved amendment.

## Pre-dispatch review checklist

Claude and the operator should review the following against the actual implementation boundary before dispatch:

- [ ] P-01 through P-09 are deliberate choices: especially absolute versus normalized conflict, the treatment of low-quality `_unique` disagreements, tentative broad-line evidence, photometric classification gating, tie-breaking, and tile-level partitioning.
- [x] Direct analyst authentication and source read access were demonstrated on 2026-09-21 after the operator resolved the HBA gap; connection-time read-only enforcement was also verified. Repeat at execution preflight.
- [ ] Bounded installer access is available and its permitted actions match the named derived-object contract.
- [ ] Every required write, including ACL bootstrap, evidence, recovery and lifecycle closeout, is inside Modify; no required outcome depends on a forbidden action.
- [ ] Curated reading supplies each indispensable meaning, distinguishes observations from decisions, and does not make known-bad review prose an authority.
- [ ] Reversal is phased around the declared seal, preserves validated work, and has a cumulative cost/retry bound.
- [ ] The final full-suite cost is permitted by the run window. Intermediate testing can be focused; completion checks cannot be waived for convenience.
- [ ] The final HitL is scientific adoption of a completed product. There are no hidden scheduled approvals between mechanical gates.

## Notes on downstream scope

The result supplies reproducible spectroscopy association and eligibility, not a mass truth set. A later T_A spec must account for expected cross-code offsets, uncertainty conventions, and SFR censoring under its own approved rules. This unit's sample size or a favourable agreement plot cannot authorize that science implicitly.

## Draft review reconciliation (v0.2)

Claude independently reproduced the conflict-audit priors, positive-z population-B counts, recognized flag/confidence mapping, and twenty-label tile domain. The author's follow-up read-only checks confirmed the quality/domain findings. P-02 now states the observed unrecognized-flag bound precisely, including confidence-zero categories. P-06 and its gate validation require zero unassigned production sources and distinguish implementation error from source drift.

The review's LePHARE-classification concern is carried into P-05, a required pre-classification exclusion diagnostic in P-07, and the final limitations/verification. An author-side diagnostic under the proposed baseline found 19,419 spectroscopy-qualified sources before photometric-type routing: type 0 = 18,473, type 1 = 349, type 2 = 597. Broad-line-reported / no-broad-line-report counts were 71 / 18,402 for type 0, 2 / 347 for type 1, and 188 / 409 for type 2. These are additional priors for 5.3 to reproduce, not adopted counts or proof that any classification is wrong. The reduction uses P-02 secure quality, P-03 ordering, both P-04 vetoes, and the verified valid native tile domain.

The baseline absolute tolerance and photometric-type veto remain proposed science decisions. This revision changes neither. Direct analyst authentication still failed on HBA coverage during v0.2 review reconciliation. The subsequent operator repair and successful v0.3 verification below supersede that blocker; the execution-time reconnect proof remains required.


## Analyst access verification (v0.3)

The operator supplied the PGSQL01 HBA change and successful reload transcript. The new SCRAM rules name only database `cosmos2025_v11` and role `cosmos2025_v11_ro`, covering the existing administrator address ranges. Author-side checks from ML01 on 2026-09-21 at 08:55-08:56 UTC then used the configured analyst handoff directly, without administrative credentials or role impersonation. The observed path was `10.25.20.10` to `10.25.20.8:5432`; both `session_user` and `current_user` were `cosmos2025_v11_ro` in `cosmos2025_v11`.

The checks established:

- Actual SELECT succeeded on all 12 mirror tables and `source.provenance` (13 relations total). Catalog, `_unique`, `_all`, and provenance counts were 784,016 / 261,975 / 482,579 / 12.
- Effective table privileges denied INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, and TRIGGER on all 13 relations, with no effective ownership. Database CONNECT and source USAGE were granted; database CREATE and source CREATE were denied. The login role had no superuser, database-creation, role-creation, replication, or RLS-bypass attribute.
- Two fresh connections using the required connection-time `default_transaction_read_only=on` setting had distinct backend IDs 3002929 and 3002930. Each reported both default and active transaction read-only settings as `on` and successfully read the 12 provenance rows. Without that connection option, the observed default was `off`; effective source permissions already denied writes, and the runtime requirement for explicit read-only enforcement remains unchanged.
- The `analysis` schema did not yet exist. These checks close the source-access/HBA prerequisite; they do not claim that the four future analysis tables or their SELECT grants have been installed or verified. Gate 5.6 still requires its post-installation analyst reconnect proof.

This measured access state supersedes older pending-HBA statements in repository orientation/configuration comments. Refresh those statements with the orientation documentation in gate 5.8. The author performed only database reads during verification; the HBA modification and reload were the operator's work. P-01 through P-09 remain proposed, and v0.3 remains a draft awaiting operator policy approval.
