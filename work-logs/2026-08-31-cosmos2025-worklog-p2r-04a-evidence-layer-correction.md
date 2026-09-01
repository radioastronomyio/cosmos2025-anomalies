<!--
---
title: "Worklog: P2R-04A Evidence-Layer Correction"
description: "RED regression coverage for the P2R-04 evidence-layer defects"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-31"
version: "1.0"
status: "in-progress"
tags:
  - type: worklog
  - domain: testing
  - domain: spectroscopy
related_documents:
  - "docs/research/specz-linkage-evidence.md"
---
-->

# Worklog: P2R-04A Evidence-Layer Correction

## Summary

| Attribute | Value |
|-----------|-------|
| Status | Complete through A1.4 |
| Gate | A1.4 corrected evidence review surface |
| Branch | `task/4-specz-linkage-correction` |
| Base | `04b42e16faacbd2388979d9c608d54db26118a50` |

Objective: establish deterministic regression tests for the P2R-04 evidence
layer before changing either generator.

## Gate checkpoints

### Gate A1.1: Reproduce both evidence defects

Added in-memory regression fixtures for the Gate 4.1 verifier and Gate 4.7
characterizer. D1 is attributed to executor deviation: the verifier uses
catalog identifier arithmetic when it must find the catalog source carrying
the stored link. D2 is attributed to executor deviation: the rendered
confidence distribution does not establish complete category coverage or a
reconciled population total. Focused RED command and output are recorded
after execution. No generator, report, database object, or parent worklog was
changed.

Focused RED command:

```bash
pytest tests/test_specz_linkage_evidence_regressions.py -v
```

Observed result: `4 failed in 0.40s`, intentionally. D1 reports `link 20
must pair with stored-link carrier catalog source 10 (ra=0.0), not catalog
source 20 (ra=10.0)` and observes `36000.0 == 0.0`; its row-permutation
fixture changes the defective-path result from 36,000 to 108,000 arcsec. D2
reports that observed category `85` is absent from rendered `{50, 97}` and
that its bucket total `2` does not equal rendered stated total `3`. The
separately present assertion confirms rendered stated total `3` equals the
independently counted population `3`.

### Gate A1.2: Correct defective-path geometry

Repaired only the Gate 4.1 verifier's catalog-to-compilation association.
The primary helper selects catalog rows by stored non-sentinel link position,
then associates each carried value with `Id_specz`; it does not use a stored
link as a catalog identifier. The generator now reports the all-links
population (37,219, measurement-level corrected coordinates) separately from
the resolving subset (24,364, selected-measurement corrected coordinates).
`PRIORS.defective_median` is labeled and checked on the all-links population.

The independent all-links cross-check maps `Id_specz` through a dictionary
and uses a clamped spherical law of cosines. Its pre-stated 0.01 arcsec
tolerance exceeds double-precision rounding at the roughly one-degree median
by several orders while remaining small against the measured geometry.

Focused RED evidence, retained from this gate's start:

```bash
pytest tests/test_specz_linkage_evidence_regressions.py -v -k 'defective_path'
```

Result: `2 failed, 2 deselected in 0.39s`; direct pairing reported 36,000
arcsec instead of 0.0, and row permutation changed it to 108,000 arcsec.

Focused GREEN command:

```bash
pytest tests/test_specz_linkage_evidence_regressions.py -v -k 'defective_path'
```

Result: `2 passed, 2 deselected in 0.40s`. The combined file reports `2
passed, 2 failed in 0.39s`; the remaining intentional D2 failures are the
missing confidence category 85 and bucket sum 2 against stated total 3.

Live evidence used the one approved transport:

```bash
doppler run --project ml01 --config dev -- python src/etl/verify_specz_linkage_v11.py
```

Both manifest-pinned FITS artifacts matched SHA-256 and byte count. The sole
session reported database `cosmos2025_v11`, current/session user
`clusteradmin_pg01`, and both `default_transaction_read_only` and
`transaction_read_only` as `on`. It created or changed no database object.
All 20 prior checks passed. The all-links geometry was n=37,219, min
0.004896, median 4054.341556, p90 5956.722682, p99 7219.432634, max
9085.018894 arcsec. The resolving subset was n=24,364, min 0.006039, median
4245.566999, p90 6061.358157, p99 7379.066450, max 9085.018894 arcsec. The
independent median was 4054.341555895 arcsec, 1.44e-09 arcsec from the primary
route. The untouched compilation-crossmatch control retained n=92,359,
median 0.084048, max 0.998335 arcsec.

The deselected broader command ran with both D2 tests omitted and returned
`431 passed, 5 failed, 8 errors, 2 deselected`. Its five failures and eight
errors all halt at the frozen semantic-source hash for this verifier:
`46a7b827...` is sealed, while this repair observes `45b983eb...`.
`test_default_check_reproduces_tracked_dictionary_byte_identical` confirms
that the failure occurs before source profiling. Refreshing the dictionary
and conformance seal is outside the A1.2 allowed surface and was not done.

#### Fix Round 1: Guard at two decimal places

`PRIORS.defective_median` now fixes the all-links value at 4054.34 arcsec and
the generator compares `round(all_link_stats["median"], 2)`. The new D1
fixture sets its sole carrier at 4054.346 arcsec and asserts the resulting
prior check is `observed=4054.35`, `prior=4054.34`, and `agreement=False`.
The prior integer rounding produced the expected RED value 4054.0; after the
fix, the focused command reported `3 passed, 2 deselected in 0.40s`.

The live read-only command reported `defective_median: 4054.34 | 4054.34 |
True`. The database session was `cosmos2025_v11` as `clusteradmin_pg01` for
both current and session user, with `default_transaction_read_only=on` and
`transaction_read_only=on`.

Control proof: the exact `04b42e1` verifier bytes and the current verifier
were each run against the pinned FITS inputs and live source mirror through
read-only Doppler sessions. Their `geometry.compilation_crossmatch`
subdocuments were serialized with sorted keys, ASCII encoding, and compact
separators. Both produced SHA-256
`9a22f4b61bc3214875b0e0377aa3c2d2b068830b69956c58a5aeaff6de085cdc`; equality
is true. The historical comparison session separately recorded the same
database identity and both read-only settings as `on`. No control calculation
or tracked seal artifact changed.

### Gate A1.3: Correct distributions and add radius sensitivity

The characterizer now renders data-derived confidence and flag distributions
for the resolving and non-resolving attached-entry populations. Each reports
its scope, bucket sum, stated attached-entry total, independent entry count,
and reconciliation status. The live confidence totals were 21,700 resolving
and 12,610 non-resolving; confidence 85 appears in both at 632 and 590,
respectively. All four distributions reconciled.

Population A now computes one nearest `Priority=1` candidate per source and
classifies it at three radii. The source totals reconcile at each radius:
3 arcsec has 0 same, 535 other, and 497 none; 5 arcsec has 0 same, 694 other,
and 338 none; 10 arcsec has 0 same, 956 other, and 76 none. The 5-arcsec
694 / 338 split is therefore not stable. This is pairwise nearest-candidate
matching, not connected-component construction, so A-B and B-C proximity
does not form a transitive group.

The approved live command was:

```bash
doppler run --project ml01 --config dev -- \
  python src/etl/characterize_specz_linkage_v11.py
```

It opened two read-only sessions, one for source evidence and one for
post-state observation. Both reported `cosmos2025_v11` with current/session
user `clusteradmin_pg01`, `default_transaction_read_only=on`, and
`transaction_read_only=on`. Post-state evidence was zero source views, zero
source materialized views, no `analysis` schema, 12 provenance rows, and zero
rows written by the script. No database object changed.

Focused regression result:

```bash
pytest tests/test_specz_linkage_evidence_regressions.py -v
```

Result: `7 passed in 0.41s`. The D2 baseline began `3 passed, 2 failed` for
the missing 85 category and unreconciled total. The extended RED suite was
`3 passed, 4 failed`, then GREEN after implementation.

The established suite ran with only the required frozen check deselected:

```bash
pytest -k 'not test_default_check_reproduces_tracked_dictionary_byte_identical'
```

Result: `436 passed, 4 failed, 8 errors, 1 deselected in 124.57s`. All listed
failures and errors halt at the unchanged frozen semantic-source mismatch for
`specz_linkage_gate41` (expected `46a7b827...`, observed `2db4890d...`) before
their subject assertions. The seal, dictionary, generated artifacts, and
verifier were not modified. Full evidence and self-review are in
`.superpowers/sdd/2026-08-31-cosmos2025-spec-p2r-04a-evidence-layer-correction/task-3-report.md`.

### Gate A1.4: Correct the evidence review surface

Corrected `docs/research/specz-linkage-evidence.md` from the committed A1.2
and A1.3 evidence without opening a database session. F-01 and F-03 now keep
the all-links population of 37,219 sources on
`specz_compilation_all.ra_corrected/dec_corrected` separate from the 24,364
resolving links on `specz_compilation_unique.ra_corrected/dec_corrected`.
F-06 closes positively at the reproduced all-links median of 4,054.34 arcsec
and states that the earlier non-reconstructibility claim was wrong. The
surface's evidence-command hashes and corresponding F-06 appendix row now
identify the corrected committed sources and result.

F-08 reports the population-A split at 3, 5, and 10 arcsec as 0 / 535 / 497,
0 / 694 / 338, and 0 / 956 / 76 for same-source / other-source / no-candidate
classifications. It states that the 5-arcsec split is not stable and that the
method is pairwise, non-transitive, and constructs no connected components.
D-01 carries the same sensitivity evidence without deciding a selection
rule. F-10 lists every observed confidence and flag bucket for the resolving
and non-resolving galaxy-level attached-entry populations. Confidence and
flag tables each reconcile bucket sums, stated totals, and independent counts
at 21,700 and 12,610 entries.

Added F-14 as the stable process finding. It attributes the failure to the
P2R-04 executor, who explained the firing prior in F-06 instead of debugging
the generator. The corrected practice treats a firing scientific check as a
defect report until an independent recomputation reproduces the population
and coordinate basis. The finding says that the spec's discriminator worked;
it does not blame the spec.

Deterministic finding-block extraction against `04b42e1` reported only F-01,
F-03, F-06, F-08, F-10, and new F-14 as changed. F-02, F-04, F-05, F-07,
F-09, F-11, F-12, and F-13 were byte-identical. The superseded-number scan of
the changed findings, added-line em-dash scan, and new policy-decision scan
passed. A local evidence-to-surface check parsed the YAML frontmatter and
Markdown, matched the geometry, distribution, reconciliation, radius, and
topology values to the two gitignored evidence JSON files, and passed.

Focused regression command:

```bash
/opt/agents/venv/bin/pytest -q \
  tests/test_specz_linkage_evidence_regressions.py
```

Result: `7 passed in 0.41s`. `git diff --check` passed. This documentation
gate opened no database session and changed no database object.
