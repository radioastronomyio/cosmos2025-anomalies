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
| Status | In progress |
| Gate | A1.2 geometry correction |
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
