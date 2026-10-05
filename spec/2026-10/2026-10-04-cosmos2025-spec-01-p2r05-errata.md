<!--
---
title: "P2R-05 evidence errata"
description: "Repair evidence code and reporting without changing the sealed spectroscopic product"
author: "Codex (builder); Don (scope authorization)"
date: "2026-10-04"
version: "1.0"
status: "Authorized"
tags:
  - type: specification
  - domain: [astronomy, documentation]
  - tech: [python, postgresql]
related_documents:
  - "../../AGENTS.md"
  - "../../staging/2026-10-04-astra-p2r05-adoption/adoption-review.md"
  - "../../spec/2026-09/2026-09-21-cosmos2025-spec-p2r-05-specz-science-surface.md"
---
-->

# P2R-05 evidence errata

Repo mode; gates 0 through 4. Authorization: Don's 2026-10-04 21:42 ET
“Yes” in the coordinator chat, as conveyed in this dispatch. Builder: Codex.
Independent review seat: Claude, handed off through Don after local completion;
this spec does not authorize a model invocation, contact, or paid review call.

## Objective

The sensitivity report counts both populations correctly, the installed-product
verifier distinguishes pre-seal from post-seal checks, and the three evidence
documents accurately report the existing measurements and their denominators.
All seven build-affecting implementation files, policy and frozen parent spec,
installed content, seal metadata, pending adoption state, and five S5 acceptance
questions remain unchanged. Five local gate commits and staged evidence make
the result independently reviewable by Claude and Don.

## Why this exists

AR-F01 through AR-F05 in the independent adoption review identify defects in
evidence code and prose. They do not authorize changing scientific selection,
building a replacement product, answering S5, or sending an upstream report.
The proposed counts must be checked against the held artifacts, not accepted
because this spec repeats them. This unit repairs implementations and reporting;
it neither amends nor reopens the frozen scientific design specification.

## Execution environment

ML01 required for held snapshots and SELECT-only analyst access. Use the shared
ML01 venv under the repository toolchain contract. Lifecycle: `spec-startup` and
`spec-closeout` in `/opt/agents/repos/local-agent-skills/skills/`; workload:
`/opt/agents/repos/docs/workload-guidance/astronomy.md`. Repository `AGENTS.md`
governs and the explicit dispatch overrides generic lifecycle publication.
The supplied authorization permits this unit to run without intermediate
operator approval until a stop condition or the final independent review.

## Scope

### Pre-existing

- Clean `main` at `f358b6d3e317edb0d95e21b612a59b6573c9e57f`.
- Sealed run `1e604a8131d3b26228818e39262f5137c5909efa9b31dfa3d772c413dcc67c4c`.
- Adoption staging evidence, especially `independent-sensitivity.json`,
  `identity-audit.json`, `selection-audit.json`, `supplemental-selects.json`,
  `upstream-geometry-audit.json`, and `upstream-release-pins.json`.

### Modify or create

- `src/features/specz_science/coverage.py` and `check_installed_product.py`.
- Focused new coverage/verifier tests in `tests/`.
- `docs/research/specz-science-p2r05/{review,coverage-baseline,upstream-report-draft}.md`.
- This staging directory: spec, README, checks, logs, review handoff and closeout.
- `work-logs/worklog-2026-10-04-p2r05-errata.md` and its interior index.
- Lifecycle closeout only: byte-identical repository archive copy of this new
  spec under `spec/2026-10/`, its README, parent index, and the registry entry
  required by AGENTS/spec-closeout. Retain the requested staged spec.

### Reference

Repository context loaded in AGENTS order; local documentation standards;
unit conventions; adopted analysis targets; parent P2R-05 spec and policy;
independent adoption review sections 7 and 8. Read existing evidence code,
manifest, run metadata and immutable native snapshots as needed.

### Do not touch

- `build`, `canonical`, `config`, `pipeline`, `policy`, `snapshot`, `splits`
  modules: their bytes are sealed implementation identity inputs.
- Policy configuration, frozen parent spec, parent worklog or registry record,
  sealed artifacts, tables and seal metadata: no provenance or policy changes.
- Adoption answers/state, source data, dependencies or environment installs.
- Previous adoption staging outputs, which remain independent evidence.
- Remote git and communications: no fetch, push, PR, merge, or upstream send.

## Deliverables and validation

Each gate ends with exactly one local commit referencing its number and a
checkpoint in the same worklog. Gate 4 includes closeout, with its commit
identified there as the commit carrying the checkpoint; staged closeout records
all five full SHAs after the last commit, following the parent worklog precedent.

### Gate 0: spec and branch

Write this spec before creating `task/p2r05-errata` off `main`. No issue number
was supplied and remote issue creation is forbidden; use the authorized slug
fallback. Capture clean starting tree/base, runtime, frozen file hashes and
existing seal metadata. Index staged artifacts and record authorization.

Validation: clean base and available venv verified; spec precedes branch;
protected file hashes recorded; no new scientific decisions or adopted values.
Commit the initial worklog and index; staging remains gitignored.

### Gate 1: accumulate sensitivity totals (AR-F02)

Populate both variant headline counts while retaining every selection predicate.

Validation: a synthetic regression fails on the original implementation and
passes after repair, discriminating primary from separate membership and testing
losses and gains. Full snapshot output with an explicit staging output path must
match all three variant counts and membership change counts in the independently
reconstructed JSON. Fresh run-ID recomputation from current seven module bytes
and recorded native input identities equals the pinned run; SELECT-only live
content digest checks match all three recorded and sealed hashes. Abort on drift.

### Gate 2: pre-seal and post-seal verifier (AR-F01)

Expose explicit modes. Pre-seal verifies an unsealed pending candidate and its
staging digest contract. Post-seal verifies a sealed pending product against the
seal evidence and run metadata, recomputes installed content, checks metadata
identity consistency and current implementation identity, and uses no DB writes.
Retain analyst capability checks and source-count checks. The post-seal mode
must accept an explicit run ID without requiring a mutable finalize summary.
Update the review's reproducibility command, retaining historical seal records.

Validation: tests accept valid pre/post cases and reject wrong seal state,
missing run, changed product data, seal content/identity drift and changed
implementation bytes. Observe the intended failure before implementation.
Run post-seal against the pinned live run, pre-seal against the same sealed run
as an expected negative control, and repeat the Gate 1 identity/content guard.
Prove the post-seal oracle is sealed metadata rather than staging digests.

### Gate 3: visible document errata (AR-F03, AR-F04)

Correct confidence sensitivity to describe 213 primary and 39 separate gains
from dissolved vetoes, alongside losses 3,877 and 109. Distinguish 261 pre-type
broad-line sources from 259 type-0/type-2 eligible sources and two excluded
type-1 sources. Distinguish 681 vetoes among 20,100 secure-preferred sources
from 722 catalog-wide vetoes; secure-preferred corroboration is
11,183 singly / 8,263 multiply / 654 conflicting. Each document has visible
errata identifying what changed and why.

Validation: fresh SELECT aggregate results support these counts; repaired
sensitivity output supports gains and losses; compare the entire S5 question
section against base byte for byte. No policy or adoption wording is changed.

### Gate 4: upstream draft and local closeout (AR-F05)

Implement the adoption review section 7's four corrections: explicit unique/all
lookup surfaces and 227 correct carried-source correspondences; zero stored
coordinate identity versus nonzero corrected-coordinate geometry; distinct
query descriptions; full source hashes, exact compilation checkout identity,
portable query definitions, counts and output-safe reproduction. Retain an
unconfirmed lineage hypothesis and respectful request; keep local and unsent.

Validation: execute the report's SELECT query definitions read-only, compare
results with independently audited geometry and full manifest pins. Check all
changed documentation, protected-file hashes, unchanged S5 section and local
five-commit history. Index evidence and a closed-question review surface for
Claude. Follow spec-closeout subject to the explicit local-only boundary.

## Review surface and end boundary

`README.md` in this staging directory indexes a `review-handoff.md` with pending
yes/no questions E-Q01 (count repair), E-Q02 (mode/identity checks), E-Q03
(numerical errata and unchanged S5), E-Q04 (accurate portable upstream draft),
E-Q05 (sealed identity and scope preserved). Each names evidence and related
AR finding. Claude reviews; Don owns disposition and any publication. Completion
of this unit neither grants adoption nor dispatches T_A v2.

## Constraints and executor freedom

Only SELECT database access. Do not invoke builder, installer, sealer, negative
controls that mutate databases, or broad test suites containing write fixtures.
Use no-bytecode Python, disabled pytest caches and focused in-memory tests;
all check output goes here. No deletion. Ordinary code/document changes are
reversible repository changes; there are no non-repository state effects other
than the required append-only lifecycle record and retained staging evidence.
Choose helper names, test decomposition and formatting freely; preserve all
scientific predicates, identity inputs, exact frozen counts and scope.

At any judgment boundary, irreversible action, blast-radius expansion,
invalidated material assumption, run-ID movement or need to rebuild: record
in the worklog and staged README and stop. Expected failing regression tests
and deliberately rejected verifier modes are validations, not stop events.
